#!/usr/bin/env bash

# Stop the terminal-started serialComm.py, then reset the Arduino Mega.
# Run as the same user who started serialComm.py, with access to its USB port.
# Before running, put the Z bellow at 50%: the firmware assumes this on restart.

set -euo pipefail

# Locate the paired communication script ----------------------------------------

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
exec python3 - "$script_dir/../python/serialComm.py" <<'PY'
# Imports ----------------------------------------------------------------------

import os
from pathlib import Path
import re
import signal
import sys
import time

try:
    import serial
    import serial.tools.list_ports
except ImportError:
    sys.exit("pyserial is required; use the Python environment for serialComm.py.")


# Process identification --------------------------------------------------------

script_path = Path(sys.argv[1]).resolve()
arduino_serial_number = "8503631363035151D102"


def find_serial_processes():
    process_ids = []
    for process_dir in Path("/proc").iterdir():
        if not process_dir.name.isdigit():
            continue
        try:
            arguments = [
                os.fsdecode(argument)
                for argument in (process_dir / "cmdline").read_bytes().split(b"\0")
                if argument
            ]
            if not arguments or not re.fullmatch(
                r"python(?:\d+(?:\.\d+)*)?", Path(arguments[0]).name
            ):
                continue
            # Match the script argument, including relative paths and spaces.
            # Do not match Python -c/-m commands mentioning the filename.
            if "-c" in arguments or "-m" in arguments:
                continue
            for argument in arguments[1:]:
                if Path(argument).name != script_path.name:
                    continue
                candidate = Path(argument)
                if not candidate.is_absolute():
                    candidate = (process_dir / "cwd").resolve() / candidate
                if candidate.resolve() == script_path:
                    process_ids.append(int(process_dir.name))
                    break
        except FileNotFoundError:
            # A process can exit between listing /proc and reading its files.
            continue
    return process_ids


# Stop communication and reset the Mega -----------------------------------------

try:
    if not sys.platform.startswith("linux"):
        raise RuntimeError("This script must run on the Linux inlet computer.")
    if not script_path.is_file():
        raise RuntimeError(f"Communication script not found: {script_path}")

    ports = [
        port.device for port in serial.tools.list_ports.comports()
        if port.serial_number == arduino_serial_number
    ]
    if len(ports) != 1:
        raise RuntimeError("Expected exactly one connected inlet Arduino Mega.")

    print("Reminder: Z must be at 50% before an Arduino restart.", flush=True)
    process_ids = find_serial_processes()
    for process_id in process_ids:
        print(f"Stopping serialComm.py (PID {process_id})...", flush=True)
        try:
            # This invokes the script's KeyboardInterrupt/finally cleanup.
            os.kill(process_id, signal.SIGINT)
        except ProcessLookupError:
            pass

    deadline = time.monotonic() + 15
    while find_serial_processes():
        if time.monotonic() >= deadline:
            raise RuntimeError(
                "serialComm.py did not stop within 15 seconds; Arduino not reset."
            )
        time.sleep(0.1)
    print("serialComm.py stopped." if process_ids else "serialComm.py is not running.")

    # Mega 2560 auto-reset is triggered by asserting the USB DTR line.
    # Configure before opening; no inlet commands or firmware changes are needed.
    with serial.Serial(port=None, baudrate=115200, timeout=1, exclusive=True) as board:
        board.dtr = False
        board.port = ports[0]
        board.open()
        time.sleep(0.1)
        board.dtr = True
        time.sleep(2)
    print(f"Arduino reset pulse sent on {ports[0]}. serialComm.py remains stopped.")
except (OSError, RuntimeError, serial.SerialException) as error:
    sys.exit(f"Terminate failed: {error}")
PY
