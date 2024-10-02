from pymemcache.client import base
import time
import serial
import datetime
import ujson

# Arduino serial communication
try:
    arduino = serial.Serial('/dev/ttyACM0', baudrate=115200, timeout=0.2)
    print(" ✓ Connection to Arduino established")
    time.sleep(1)
except serial.SerialException:
    print(" x Connection to Arduino could not be established. Stopping the script.")
    quit()

# Edwards pressure gauge serial communication
# NOTE: There are two USB serial ports conneted: USB1 and USB0
#       Here we test which is the Edwards. The other one has to be the TILDAS.
MAX_ATTEMPTS = 10
EXPECTED_MESSAGE_LENGTH = 9
try:
    # Connect to 'something' over USB1
    EDWARDS_PORT = '/dev/ttyUSB1'
    edwards_gauge = serial.Serial(EDWARDS_PORT, baudrate=9600, timeout=0)
    time.sleep(2)
    attempts = 1
    success = False
    while attempts < MAX_ATTEMPTS and success is False:
        # Send a query and listen for a response
        edwards_gauge.write(bytes('?GA1\r', 'utf-8'))
        try:
            test_message = edwards_gauge.readline().decode('utf-8')
        except UnicodeDecodeError:
            test_message = ""
        if len(test_message) == EXPECTED_MESSAGE_LENGTH:
            # The response was the expected length, so this is the Edwards gauge
            print(" ✓ Connection to Edwards gauge established over " + EDWARDS_PORT)
            TILDAS_PORT = '/dev/ttyUSB0'
            success = True
        else:
            time.sleep(1)
            print("    Trying to connect to the Edwards gauge. Attempt #" + str(attempts), end="\r")
            attempts += 1
    if success is False:
        EDWARDS_PORT = '/dev/ttyUSB0'
        edwards_gauge.close() # close previous connection
        # Connect to 'something' over USB0
        edwards_gauge = serial.Serial(EDWARDS_PORT, baudrate=9600, timeout=0)
        time.sleep(1)
        attempts = 0
        while attempts < MAX_ATTEMPTS and success is False:
            # Send a query and listen for a response
            edwards_gauge.write(bytes('?GA1\r', 'utf-8'))
            try:
                test_message = edwards_gauge.readline().decode('utf-8')
            except UnicodeDecodeError:
                test_message = ""
            if len(test_message) == EXPECTED_MESSAGE_LENGTH:
                print(" ✓ Connection to Edwards gauge established over " + EDWARDS_PORT)
                time.sleep(1)
                success = True
                TILDAS_PORT = '/dev/ttyUSB1'
            else:
                time.sleep(1)
                attempts += 1
        if success is False:
            print(" x Connection to Edwards gauge could not be established. Stopping the script.")
            arduino.close() # close open connections
            quit()
except FileNotFoundError:
    print(" x The Edwards gauge's USB cable is not plugged in. Stopping the script.")
    quit()

# Laser spectrometer serial communication
try:
    laser = serial.Serial(TILDAS_PORT, baudrate=57600, timeout=1)
    print(" ✓ Connection to TILDAS established over " + TILDAS_PORT)
    time.sleep(1)
except FileNotFoundError:
    print(" x The TILDAS's USB cable is not plugged in. Stopping the script.")
    arduino.close() # close open connections
    edwards_gauge.close() # close open connections
    quit()

# Set initial values, that are obviously fake
vacuum = '9.999'
arduinoStatus = ""
laserStatus = "0,0,0,0,0"
ArduinoError = 0

# Connect to the shared variable
m = base.Client(('127.0.0.1', 11211))
m.set('key2', "")

print("Transmitting to and recieving data from sendCommand.php...")

try:
    start_time_elapsed = time.time()
    start_time_speed = time.time()
    elapsed_time = 0
    while True:

        # Read the data stream from the laser spectrometer
        # NOTE: This data is only used by the inlet system to show the status of the measurements
        #       The final measurement results are evaluated using the .str and .stc files

        if( laser.inWaiting() > 10 ):
            # Read the serial output of the TILDAS if there is something to read (at least 11 bytes)
            try:
                laserStatus = laser.readline().decode('utf-8').strip()
                # print(laserStatus) # Show the raw serial output of the TILDAS in the Terminal - for debugging

                laserStatusArray = laserStatus.split(',')

                mr1 = str(round(float(laserStatusArray[1]) / 1000,3)) # 627
                mr2 = str(round(float(laserStatusArray[2]) / 1000,3)) # 628
                mr3 = str(round(float(laserStatusArray[3]) / 1000,3)) # 626
                mr4 = str(round(float(laserStatusArray[4]) / 1000,3)) # free-path CO2
                cellP = str(round(float(laserStatusArray[10]),3)) # cell pressure (Torr)

                laserStatus = cellP + ',' + mr1 + ',' + mr2 + ',' + mr3 + ',' + mr4
                # print(laserStatus) # Show laser status string in the Terminal - for debugging
            except (ValueError, UnicodeDecodeError, IndexError):
                # If the string is broken, just ignore it
                # This error could occur when starting the script
                laserStatus = "0,0,0,0,0"

        # Read the JSON string sent by the Arduino
        try:
            arduinoStatusNew = arduino.readline()
            arduinoStatusNew = arduinoStatusNew.decode('utf-8').strip()
            arduinoStatusNew = ujson.loads(arduinoStatusNew)
            # print(arduinoStatusNew) # Show the raw serial output of the Arduino in the Terminal - for debugging

            # Check if the JSON string is correct lenght
            if len(arduinoStatusNew) != 16:
                raise ValueError("Invalid number of values in the JSON string")

            # Check if some of the values make sense
            z_percentage = float(arduinoStatusNew.get('Z_percentage', 0))
            x_pressure = float(arduinoStatusNew.get('X_pressure', 0))
            y_pressure = float(arduinoStatusNew.get('Y_pressure', 0))
            if not (0 <= z_percentage <= 100 and -1 <= x_pressure <= 7 and -1 <= y_pressure <= 7):
                raise ValueError("Invalid values in the JSON string")

            # Convert JSON data to comma-separated string without keys
            arduinoStatus = ""
            arduinoStatus = ",".join(arduinoStatusNew.values())

        except (UnicodeDecodeError, TypeError, ValueError, ujson.JSONDecodeError):
            ArduinoError += 1
        
        # print(arduinoStatus) # Show the formatted serial output of the Arduino in the Terminal - for debugging

        # Read Edwards pressure gauge and temperature sensor every 5 seconds
        if(int(time.time()) % 5 == 0):
            try:
                edwards_gauge.write( bytes('?GA1\r','utf-8') )
                edwards_response = edwards_gauge.readline().decode('utf-8').strip()
                vacuum = str(round(float(edwards_response), 5))
            except (UnicodeDecodeError, ValueError):
                pass # broken response from the Edwards gauge -> do nothing


        # Create a status string from the information from Arduino, TILDAS, Edwards gauge, and room sensor and store it for PHP in the shared variable 'key'
        if( arduinoStatus != "" ):

            # Create the status string
            timeNow = datetime.datetime.now().strftime("%H:%M:%S")
            status = timeNow + ',' + arduinoStatus + ',' + laserStatus + ',' + vacuum

            # Set shared variable #1: this is what the sendCommand.php files recieves
            m.set('key', status)

            # print(status) # Show the status string in the Terminal - for debugging

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

except KeyboardInterrupt:
    m.close()
    edwards_gauge.close()
    arduino.close()
    # laser.close() # if you close the TILDAS's serial port you have to re-open it on the TILDAS's PC
    print("\nLoop stopped by user")