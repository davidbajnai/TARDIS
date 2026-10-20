# Imports ----------------------------------------------------------------------

import csv
from datetime import datetime
import math
from pathlib import Path
import queue
import sys
import threading
import time
import traceback

from pymemcache.client import base
import serial
import serial.tools.list_ports
import ujson


# Status definitions -----------------------------------------------------------

# These names and their string values are the existing Arduino/PHP/GUI contract.
arduino_status_keys = (
    "moveStatus", "X_position", "X_percentage", "Y_position", "Y_percentage",
    "Z_position", "Z_percentage", "X_pressure", "Y_pressure", "Z_pressure",
    "valveArray", "relayArray", "boxHumidity", "boxTemperature", "boxSetpoint",
    "fanSpeed", "D_pressure", "arduinoSpeed",
)
arduino_move_statuses = {
    "-", "MX", "MY", "MZ", "PX", "PY", "EX", "EY", "SN", "RS", "WK",
}
arduino_text_keys = {"moveStatus", "valveArray", "relayArray"}


# Status parsing ---------------------------------------------------------------

def finite_number(value):
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("Non-finite sensor value")
    return number


def to_ppm(value):
    return round(finite_number(value) / 1000, 3)


def parse_laser_status(raw_line):
    # Preserve the existing acceptance of complete CSV responses on timeout.
    # Confirm TILDAS framing before requiring a particular line terminator.
    fields = raw_line.decode('utf-8').strip().split(',')
    if len(fields) < 11:
        raise ValueError("Incomplete TILDAS status fields")

    # Build a replacement only after every required field has been validated.
    return {
        "chi_627": to_ppm(fields[1]),
        "chi_628": to_ppm(fields[2]),
        "chi_626": to_ppm(fields[3]),
        "free_path_CO2": to_ppm(fields[4]),
        "cellPressure": round(finite_number(fields[10]), 3),
    }


def parse_arduino_status(raw_line):
    if not raw_line.endswith(b'\n'):
        raise ValueError("Incomplete Arduino status line")
    status = ujson.loads(raw_line.decode('utf-8').strip())
    if not isinstance(status, dict) or set(status) != set(arduino_status_keys):
        raise ValueError("Unexpected Arduino status keys or object type")
    if not all(isinstance(value, str) for value in status.values()):
        raise ValueError("Arduino status values must be strings")
    if status["moveStatus"] not in arduino_move_statuses:
        raise ValueError("Unexpected Arduino moveStatus")
    for key, length in (("valveArray", 32), ("relayArray", 2)):
        if len(status[key]) != length or set(status[key]) - {"0", "1"}:
            raise ValueError(f"Invalid {key}")

    numbers = {
        key: finite_number(value)
        for key, value in status.items() if key not in arduino_text_keys
    }
    # Retain the existing pressure/position bounds; potentiometer values may
    # legitimately extend beyond 0-100%, so do not add new limits to them.
    if not (0 <= numbers["Z_percentage"] <= 100
            and -1 <= numbers["X_pressure"] <= 7
            and -1 <= numbers["Y_pressure"] <= 7):
        raise ValueError("Arduino pressure or position outside existing bounds")

    # Return the original strings, including all trailing zeroes and precision.
    return status


# Device workers ---------------------------------------------------------------

def loop_1():
    global vacuum

    # Reading the Edwards gauge separately keeps its response time out of the
    # Arduino/TILDAS loop. I/O failures propagate to the worker supervisor.
    while not stop_event.is_set():
        try:
            edwards_gauge.write(b'?GA1\r')
            edwards_response = edwards_gauge.readline().decode('utf-8').strip()
            vacuum_new = round(finite_number(edwards_response), 4)
            if vacuum_new >= 0:
                with lock:
                    vacuum = str(vacuum_new)
        except (UnicodeDecodeError, ValueError):
            # Keep the last valid reading if the gauge sends malformed data.
            pass

        stop_event.wait(0.1)


def loop_2():
    arduino_errors = 0
    arduino_status = dict.fromkeys(arduino_status_keys, "")
    arduino_status["moveStatus"] = "Error"
    laser_status = {
        "cellPressure": 0,
        "chi_627": 0,
        "chi_628": 0,
        "chi_626": 0,
        "free_path_CO2": 0,
    }
    start_time_elapsed = time.monotonic()
    start_time_speed = start_time_elapsed
    elapsed_time = 0
    last_status_print = start_time_elapsed
    temperature_log = Path("/var/www/html/data/Logfiles") / (
        f"tempControl{datetime.now().strftime('_%y%m%d_%H%M%S')}.csv"
    )

    while not stop_event.is_set():
        # TILDAS serial data supplies the display and pressure/mixing-ratio
        # adjustment. Measurement evaluation still uses the .str/.stc files.
        if laser.in_waiting > 10:
            try:
                laser_status = parse_laser_status(laser.readline())
            except (UnicodeDecodeError, ValueError):
                # Assignment occurs only if the complete replacement is valid.
                pass

        try:
            arduino_status_new = parse_arduino_status(arduino.readline())

            # Optional temperature logging for PID tuning (disabled as before).
            # if elapsed_time < 2700:
            #     write_header = not temperature_log.exists()
            #     with temperature_log.open('a', newline='') as log_file:
            #         writer = csv.writer(log_file)
            #         if write_header:
            #             writer.writerow([
            #                 "Time", "boxTemperature", "boxSetpoint", "fanSpeed"
            #             ])
            #         writer.writerow([
            #             datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            #             arduino_status_new['boxTemperature'],
            #             arduino_status_new['boxSetpoint'],
            #             arduino_status_new['fanSpeed'],
            #         ])

            arduino_status = arduino_status_new
        except (UnicodeDecodeError, ValueError):
            arduino_errors += 1

        if stop_event.is_set():
            break

        # Preserve the current shared status schema and last-valid-data policy.
        # Freshness tracking and command acknowledgements need a coordinated
        # change with PHP/JavaScript and are not inferred from this timestamp.
        if arduino_status["moveStatus"] != "Error":
            status_dict = {
                "time": datetime.now().strftime("%H:%M:%S"),
                **arduino_status,
                **laser_status,
            }
            with lock:
                status_dict["vacuum"] = vacuum
            m.set('key', ujson.dumps(status_dict))

        # Preserve the existing command bytes and key2 handoff for this stage.
        # An absent cache key is normal after eviction/restart, not a command.
        raw_command = m.get('key2')
        if stop_event.is_set():
            break
        value = raw_command.decode('utf-8') if raw_command is not None else ""
        if value != "":
            command_bytes = value.encode('utf-8')
            bytes_written = arduino.write(command_bytes)
            if bytes_written != len(command_bytes):
                # Delivery is uncertain: stop visibly rather than retrying a
                # potentially executed operation without acknowledgement IDs.
                raise OSError("Incomplete Arduino command write; not retried")
            arduino.flush()
            m.set('key2', "")

        now = time.monotonic()
        elapsed_time = now - start_time_elapsed
        days, remainder = divmod(int(elapsed_time), 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        time_taken = now - start_time_speed
        speed = 1 / time_taken if time_taken > 0 else 0

        if now - last_status_print >= 1:
            print(
                f"  Elapsed: {days:.0f} d, {hours:.0f} h, {minutes:.0f} m, "
                f"{seconds:.0f} s | Speed: {speed:.1f}Hz | "
                f"Arduino errors: {arduino_errors:.0f}      ", end="\r"
            )
            last_status_print = now
        start_time_speed = now


# Worker supervision -----------------------------------------------------------

def run_worker(worker):
    try:
        worker()
        if not stop_event.is_set():
            raise RuntimeError("Communication worker exited unexpectedly")
    except Exception as error:
        # Failures must not leave only one worker running and an apparently
        # healthy process. Do not reconnect or replay commands automatically.
        worker_errors.put((threading.current_thread().name, error))
        stop_event.set()


# Serial connections and startup -----------------------------------------------

lock = threading.Lock()
stop_event = threading.Event()
worker_errors = queue.Queue()
vacuum = "0.0000"  # Initialize before either worker can publish a status.
arduino = None
laser = None
edwards_gauge = None
m = None
threads = []
exit_code = 0

try:
    devices = {port.serial_number: port.device
               for port in serial.tools.list_ports.comports()}
    tildas_port = "/dev/ttyS0"
    edwards_port = devices.get("CHAAb131R01")
    arduino_port = devices.get("8503631363035151D102")
    if edwards_port is None:
        raise RuntimeError("The Edwards gauge is not connected")
    print(f" ✓ The Edwards gauge is connected at {edwards_port}")
    if arduino_port is None:
        raise RuntimeError("The Arduino is not connected")
    print(f" ✓ The Arduino is connected at {arduino_port}\n")

    # Keep the existing read timeouts and baud rates. Bound writes and cache
    # access so I/O failures can reach the supervisor instead of hanging.
    arduino = serial.Serial(
        arduino_port, baudrate=115200, timeout=0.2, write_timeout=1
    )
    print(" ✓ Serial communication with the Arduino is established")
    time.sleep(1)

    laser = serial.Serial(tildas_port, baudrate=56000, timeout=1)
    print(" ✓ Serial communication with the TILDAS established")
    time.sleep(1)

    edwards_gauge = serial.Serial(
        edwards_port, baudrate=9600, timeout=1, write_timeout=1
    )
    time.sleep(2)
    max_attempts = 2
    expected_message_length = 9
    for attempt in range(max_attempts):
        edwards_gauge.write(b'?GA1\r')
        try:
            response = edwards_gauge.readline().decode('utf-8')
        except UnicodeDecodeError:
            response = ""
        if len(response) == expected_message_length:
            print(" ✓ Serial communication with the Edwards gauge established")
            break
        time.sleep(1)
    else:
        raise serial.SerialException("Invalid Edwards response length")

    m = base.Client(('127.0.0.1', 11211), connect_timeout=1, timeout=1)
    m.set('key2', "")
    print("\nTransmitting to and receiving data from sendCommand.php...")

    threads = [
        threading.Thread(
            target=run_worker, args=(loop_1,), name="Edwards", daemon=True
        ),
        threading.Thread(
            target=run_worker, args=(loop_2,), name="Arduino/TILDAS", daemon=True
        ),
    ]
    for thread in threads:
        thread.start()
    stop_event.wait()
except KeyboardInterrupt:
    print("\nThreads stopped by user")
except Exception as error:
    exit_code = 1
    print(f"\n x Communication stopped: {error}", file=sys.stderr)
    traceback.print_exception(type(error), error, error.__traceback__)
finally:
    stop_event.set()
    for thread in threads:
        if thread.ident is not None:
            thread.join(timeout=3)
            if thread.is_alive():
                exit_code = 1
                print(f"\n x {thread.name} worker did not stop", file=sys.stderr)

    while not worker_errors.empty():
        worker_name, error = worker_errors.get_nowait()
        exit_code = 1
        print(f"\n x {worker_name} communication failed: {error}", file=sys.stderr)
        traceback.print_exception(type(error), error, error.__traceback__)

    for connection in (edwards_gauge, laser, arduino, m):
        if connection is not None:
            try:
                connection.close()
            except Exception as error:
                exit_code = 1
                print(f"\n x Connection cleanup failed: {error}", file=sys.stderr)

sys.exit(exit_code)
