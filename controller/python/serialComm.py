# >>>>>>>>>>>>>>>>>>>>>>>>>>>>> IMPORT PACKAGES <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

from pymemcache.client import base
import time
import serial
import serial.tools.list_ports
from datetime import datetime
import ujson
import threading
import csv
import os
import sys

# >>>>>>>>>>>>>>>>>>>>>>>>>>> SERIAL COMMUNICATION <<<<<<<<<<<<<<<<<<<<<<<<<<<<

# Get available devices connected to the computer
devices = {p.serial_number: p.device for p in serial.tools.list_ports.comports()}

# Assign the serial ports to the devices

try:
    TILDAS_PORT = devices["ETBQi19C116"]
    print(f" ✓ TILDAS is connected at {TILDAS_PORT}")
except KeyError:
    print(" x The TILDAS is not connected. Stopping the script.")
    sys.exit(1)

try:
    EDWARDS_PORT = devices["CHAAb131R01"]
    print(f" ✓ The Edwards gauge is connected at {EDWARDS_PORT}")
except KeyError:
    print(" x The Edwards gauge is not connected")
    sys.exit(1)

try:
    ARDUINO_PORT = devices["8503631363035151D102"]
    print(f" ✓ The Arduino is connected at {ARDUINO_PORT}")
except KeyError:
    print(" x The Arduino is not connected")
    sys.exit(1)
print("")

# Establish the serial connections

try:
    arduino = serial.Serial(ARDUINO_PORT, baudrate=115200, timeout=0.2)
    print(" ✓ Serial communication with the Arduino is established")
    time.sleep(1)
except serial.SerialException:
    print(" x Failed to establsih serial communication with the Arduino")
    sys.exit(1)

try:
    laser = serial.Serial(TILDAS_PORT, baudrate=57600, timeout=1)
    print(" ✓ Serial communication with the TILDAS established")
    time.sleep(1)
except serial.SerialException:
    print(" x Failed to establish serial communication with the TILDAS")
    sys.exit(1)

MAX_ATTEMPTS = 2
EXPECTED_MESSAGE_LENGTH = 9
try:
    edwards_gauge = serial.Serial(EDWARDS_PORT, baudrate=9600, timeout=1)
    time.sleep(2)
    for attempt in range(MAX_ATTEMPTS):
        edwards_gauge.write(b'?GA1\r')
        try:
            response = edwards_gauge.readline().decode('utf-8')
        except UnicodeDecodeError:
            response = ""
        if len(response) == EXPECTED_MESSAGE_LENGTH:
            print(" ✓ Serial communication with the Edwards gauge established")
            break
        time.sleep(1)
    else:
        raise serial.SerialException("Invalid response length")

except serial.SerialException:
    print(" x Failed to establish serial communication with the Edwards gauge")
    sys.exit(1)

# Connect to the shared variable
m = base.Client(('127.0.0.1', 11211))
m.set('key2', "")

# Serial connections are established
print("\nTransmitting to and recieving data from sendCommand.php...")


# >>>>>>>>>>>>>>>>>>>>>>>>>>>>> DEFINE LOOPS <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

""" NOTE
Reading the Edwards gauge has to be in a separate loop
othwerwise the it slows down the communication with the Arduino and TILDAS
"""

lock = threading.Lock()

def loop_1():

    # Initialize the global variable also used by loop_2
    global vacuum
    vacuum = "0.0000"

    while True:
        # Read Edwards pressure gauge and temperature sensor
        try:
            edwards_gauge.write( bytes('?GA1\r','utf-8') )
            edwards_response = edwards_gauge.readline().decode('utf-8').strip()
            vacuum_new = round(float(edwards_response), 4)
            if vacuum_new >= 0:
                with lock:
                    vacuum = str(vacuum_new)
            else:
                pass
        except (UnicodeDecodeError, ValueError):
            pass # broken response from the Edwards gauge -> do nothing

def loop_2():

    # Initialize variables used in the loop
    ArduinoError = 0
    arduinoStatus = {
        "moveStatus": "Error",
        "X_position": "",
        "X_percentage": "",
        "Y_position": "",
        "Y_percentage": "",
        "Z_position": "",
        "Z_percentage": "",
        "X_pressure": "",
        "Y_pressure": "",
        "Z_pressure": "",
        "valveArray": "",
        "relayArray": "",
        "boxHumidity": "",
        "boxTemperature": "",
        "boxSetpoint": "",
        "fanSpeed": "",
        "D_pressure": "",
        "arduinoSpeed": "",
    }

    laserStatus = {
        "cellPressure": 0,
        "chi_627": 0,
        "chi_628": 0,
        "chi_626": 0,
        "free_path_CO2": 0
    }
    start_time_elapsed = time.time()
    start_time_speed = time.time()
    elapsed_time = 0
    temperature_log = os.path.join(
        "/var/www/html/data/Logfiles", f"tempControl{datetime.now().strftime('_%y%m%d_%H%M%S')}.csv")

    while True:

        """ NOTE
        Here we read the data stream from the TILDAS.
        This data is only used by the inlet system to show the status of the measurements,
        and to adjust the cell pressure, and the 626 mixing ratio.
        The measurement results are evaluated using the .str and .stc files.
        """

        if laser.in_waiting > 10:
            # Read the serial output of the TILDAS if there is something to read (at least 11 bytes)
            try:
                laserStatus = laser.readline().decode('utf-8').strip()
                # print(laserStatus) # Show the raw serial output of the TILDAS in the Terminal - for debugging

                laserStatusArray = laserStatus.split(',')

                def to_ppm(value):
                    return round(float(value) / 1000, 3)

                laserStatus = {
                    "chi_627": to_ppm(laserStatusArray[1]),
                    "chi_628": to_ppm(laserStatusArray[2]),
                    "chi_626": to_ppm(laserStatusArray[3]),
                    "free_path_CO2": to_ppm(laserStatusArray[4]),
                    "cellPressure": round(float(laserStatusArray[10]), 3)
                }
                # print(ujson.dumps(laserStatus, indent=2)) # Show laser status string in the Terminal - for debugging
            except (ValueError, UnicodeDecodeError, IndexError):
                # If the string is broken, just ignore it
                pass

        # Read the JSON string sent by the Arduino
        try:
            arduinoStatusNew = arduino.readline()
            arduinoStatusNew = arduinoStatusNew.decode('utf-8').strip()
            arduinoStatusNew = ujson.loads(arduinoStatusNew)
            # print(arduinoStatusNew) # Show the raw serial output of the Arduino in the Terminal - for debugging

            # Check if the JSON string is correct lenght
            if len(arduinoStatusNew) != 18:
                raise ValueError("Invalid number of values in the JSON string")

            # Check if some of the values make sense
            z_percentage = float(arduinoStatusNew.get('Z_percentage', 0))
            x_pressure = float(arduinoStatusNew.get('X_pressure', 0))
            y_pressure = float(arduinoStatusNew.get('Y_pressure', 0))
            if not (0 <= z_percentage <= 100 and -1 <= x_pressure <= 7 and -1 <= y_pressure <= 7):
                raise ValueError("Invalid values in the JSON string")

            # Save the temperatre control data to a CSV file for PID tuning
            # if elapsed_time < 2700:
            #     write_header = not os.path.exists(temperature_log)
            #     with open(temperature_log, mode='a', newline='') as file:
            #         writer = csv.writer(file)
            #         if write_header:
            #             writer.writerow(["Time", "boxTemperature", "boxSetpoint", "fanSpeed"])
            #         timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            #         box_temp = arduinoStatusNew.get('boxTemperature', '')
            #         fanspeed = arduinoStatusNew.get('fanSpeed', '')
            #         boxSetpoint = arduinoStatusNew.get('boxSetpoint', '')
            #         writer.writerow([timestamp, box_temp, boxSetpoint, fanspeed])

            arduinoStatus = arduinoStatusNew

        except (UnicodeDecodeError, TypeError, ValueError, ujson.JSONDecodeError):
            ArduinoError += 1
        
        # print(arduinoStatus) # Show the formatted serial output of the Arduino in the Terminal - for debugging

        # Create a status string from the information from Arduino, TILDAS, Edwards gauge, and room sensor and store it for PHP in the shared variable 'key'
        if arduinoStatus.get("moveStatus") != "Error":

            # Create the status string
            status_dict = {
                "time": datetime.now().strftime("%H:%M:%S"),
                "vacuum": vacuum,
                **arduinoStatus,
                **laserStatus
            }

            # Convert to JSON string
            status = ujson.dumps(status_dict)

            # Set shared variable #1: this is what the sendCommand.php files recieves
            m.set('key', status)

            # print(ujson.dumps(status, indent=2)) # Show the status string in the Terminal - for debugging
            # time.sleep(0.05)

        # Receive commands for Arduino from PHP via shared variable #2, defined in sendCommand.php
        value = m.get('key2').decode('UTF-8')
        if( value != "" ):
            arduino.write( bytes(value, 'utf-8') )
            arduino.flush()
            # print(value) # Show command in the terminal - for debugging
            m.set('key2', "")

        # Clean up the shared variables
        m.close()

        # Calculate the elapsed time since start
        elapsed_time = time.time() - start_time_elapsed
        days, remainder = divmod(int(elapsed_time), 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)

        # Calculate the speed
        time_taken = time.time() - start_time_speed
        speed = 1 / time_taken

        print(f"  Elapsed: {days:.0f} d, {hours:.0f} h, {minutes:.0f} m, {seconds:.0f} s | Speed: {speed:.1f}Hz | Arduino errors: {ArduinoError:.0f}      ", end="\r")
        start_time_speed = time.time()


# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>> THREADS <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

thread_1 = threading.Thread(target=loop_1, daemon=True)
thread_2 = threading.Thread(target=loop_2, daemon=True)
thread_1.start()
thread_2.start()

try:
    thread_1.join()
    thread_2.join()
except KeyboardInterrupt:
    print("\nThreads stopped by user")
finally:
    if edwards_gauge:
        edwards_gauge.close()
    if m:
        m.close()
    if arduino:
        arduino.close()