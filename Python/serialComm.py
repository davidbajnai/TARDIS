from pymemcache.client import base
import time
import serial
import bme680
import datetime
import re

# Arduino serial communication
try:
    arduino = serial.Serial('/dev/ttyACM0', baudrate=115200, timeout=0.5)
    print(" ✓ Connection to Arduino established")
    time.sleep(1)
except serial.SerialException:
    print(" x Connection to Arduino could not be established. Stopping the script.")
    quit()

# Edwards pressure gauge serial communication
# NOTE: There are two USB serial ports conneted to the rPi: USB1 and USB0
#       Here we test which is the Edwards. The other one has to be the TILDAS.
MAX_ATTEMPTS = 10
EXPECTED_MESSAGE_LENGTH = 9
try:
    # Connect to 'something' over USB1
    edwards_gauge = serial.Serial('/dev/ttyUSB0', baudrate=9600, timeout=0.05)
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
            print(" ✓ Connection to Edwards gauge established over /dev/ttyUSB0")
            TILDAS_PORT = '/dev/ttyUSB1'
            success = True
        else:
            time.sleep(1)
            print("    Trying to connect to the Edwards gauge. Attempt #" + str(attempts), end="\r")
            attempts += 1
    if success is False:
        edwards_gauge.close() # close previous connection
        # Connect to 'something' over USB0
        edwards_gauge = serial.Serial('/dev/ttyUSB1', baudrate=9600, timeout=0.05)
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
                print(" ✓ Connection to Edwards gauge established over /dev/ttyUSB1")
                time.sleep(1)
                success = True
                TILDAS_PORT = '/dev/ttyUSB0'
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

# Initialize the breakout sensors
try:
    sensor = bme680.BME680(bme680.I2C_ADDR_PRIMARY)
    print(" ✓ Connection to room temperature sensor established over I2C")
    time.sleep(1)
except IOError:
    print(" x Connection to room temperature sensor failed. Stopping the script.")
    quit()

# Set initial values, that are obviously fake
vacuum = '9.999'
arduinoStatus = ""
laserStatus = "0,0,0,0,0"
roomT = 1
roomH = 1
ArduinoError = 0

# Connect to the shared variable
m = base.Client(('127.0.0.1', 11211))
m.set('key2', "")

print("Transmitting to and recieving data from sendCommand.php...")

try:
    start_time = time.time()
    loops = 1
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

        # Read Arduino data
        try:
            arduinoStatusNew = arduino.readline().decode('utf-8').strip()
        except UnicodeDecodeError:
            # Try to read the status string again if it failed the first time
            time.sleep(0.05)
            arduinoStatusNew = arduino.readline().decode('utf-8').strip()
        
        # print(arduinoStatus) # Show the raw serial output of the Arduino in the Terminal - for debugging

        # Check if we have a complete string using a regular expression
        pattern = re.compile(r'^-?[A-Z]{0,}[,][-]?\d+\.\d{2}[,][-]?\d+\.\d{1}[,][-]?\d+\.\d{2}[,][-]?\d+\.\d{1}[,][-]?\d+[,][-]?\d+\.\d{2}[,][A][,][-]?\d+\.\d{3}[,][-]?\d+\.\d{3}[,][-]?\d+\.\d{1}[,][B][,]\d{32}[,]\d{2}[,]\d{2,3}\.\d{2}[,]\d{2,3}\.\d{3}[,]\d{2}\.\d{2}[,](?:0|[1-9]\d?|100)$')
        if re.match(pattern, arduinoStatusNew):
            arduinoStatus = arduinoStatusNew
        else:
            ArduinoError += 1
            
        # Read Edwards pressure gauge and temperature sensor every 10 cycles
        if(loops % 10 == 0):

            edwards_gauge.write( bytes('?GA1\r','utf-8') )
            try:
                edwards_response = edwards_gauge.readline().decode('utf-8')
            except UnicodeDecodeError:
                edwards_response = "1.00E-04 "
            # A little formatting is necessary because the string is sometimes broken
            if len(edwards_response) == EXPECTED_MESSAGE_LENGTH:
                vacuum = str(round(float(edwards_response), 4))
            
            # room temperature from sensor
            try:
                sensor.get_sensor_data()
                roomT = '{:05.2f}'.format(sensor.data.temperature)
                roomH = '{:05.2f}'.format(sensor.data.humidity)
            except (OSError, RuntimeError, ZeroDivisionError):
                # Dont break the loop if the sensor is disconnected
                roomT = 1
                roomH = 1

            time.sleep(0.05)

        # Create a status string from the information from Arduino, TILDAS, Edwards gauge, and room sensor and store it for PHP in the shared variable 'key'
        if( arduinoStatus != "" ):

            # Create the status string
            timeNow = datetime.datetime.now().strftime("%H:%M:%S")
            status = timeNow + ',' + arduinoStatus + ',' + laserStatus + ',' + vacuum + ',' + str(roomH)+ ',' + str(roomT)

            # Set shared variable #1: this is what the sendCommand.php files recieves
            m.set('key', status)

            # print(status) # Show the status string in the Terminal - for debugging

            time.sleep(0.05)

        # Receive commands for Arduino from PHP via shared variable #2, defined in sendCommand.php
        value = m.get('key2').decode('UTF-8')
        if( value != "" ):
            arduino.write( bytes(value, 'utf-8') )
            arduino.flush()
            # print(value) # Show command in the terminal - for debugging
            m.set('key2', "")

        # Clean up the shared variables
        m.close()

        # Calculate and print the loop info
        elapsed_time = time.time() - start_time
        days, remainder = divmod(int(elapsed_time), 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)

        print("  Elapsed: {} d, {} h, {} m, {} s".format(int(days), int(hours), int(minutes), int(seconds)) + " | Speed: " + str(round(loops/elapsed_time,1)) + " Hz | Arduino errors: " + str(ArduinoError) + "   ", end="\r")
        loops += 1

except KeyboardInterrupt:
    m.close()
    edwards_gauge.close()
    arduino.close()
    # laser.close() # if you close the TILDAS's serial port you have to re-open it on the TILDAS's PC
    print("\nLoop stopped by user")