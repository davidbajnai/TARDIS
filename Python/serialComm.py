from pymemcache.client import base
import time
import serial
import bme680
import datetime
import re
from alive_progress import alive_bar

# Arduino serial communication
try:
    arduino = serial.Serial('/dev/ttyACM0', baudrate=115200, timeout=1)
    print(" ✓ Connection to Arduino established")
    time.sleep(2)
except serial.SerialException:
    print(" x Connection to Arduino could not be established. Stopping the script.")
    quit()

# Laser spectrometer serial communication
try:
    laser = serial.Serial('/dev/ttyUSB0', baudrate=57600, timeout=1)
    print(" ✓ Connection to TILDAS established over /dev/ttyUSB0")
    time.sleep(2)
except serial.SerialException:
    laser = serial.Serial('/dev/ttyUSB1', baudrate=57600, timeout=1)
    print(" ✓ Connection to TILDAS established over /dev/ttyUSB1")
    time.sleep(2)
if laser is None:
    print(" x Failed to establish connection to TILDAS. Stopping the script.")
    quit()


# Edwards pressure gauge serial communication (can also be ttyUSB0)
try:
    edwards = serial.Serial('/dev/ttyUSB1', baudrate=9600, timeout=0.05) # a longer timeout stalls the script
    print(" ✓ Connection to Edwards gauge established over /dev/ttyUSB1")
    time.sleep(2)
except serial.SerialException:
    edwards = serial.Serial('/dev/ttyUSB0', baudrate=9600, timeout=0.05) # a longer timeout stalls the script
    print(" ✓ Connection to Edwards gauge established over /dev/ttyUSB0")
    time.sleep(2)
if edwards is None:
    print(" x Failed to establish connection to Edwards gauge. Stopping the script.")
    quit()

# Initialize the breakout sensors
try:
    sensor = bme680.BME680(bme680.I2C_ADDR_PRIMARY)
    print(" ✓ Connection to room temperature sensor established over I2C")
    time.sleep(2)
except IOError:
    print(" x Connection to room temperature sensor failed. Stopping the script.")
    quit()

# Set initial values, that are obviously fake
vacuum = '9.999'
arduinoStatus = ""
roomT = 1
roomH = 1

# Connect to the shared variable
m = base.Client(('127.0.0.1', 11211))
m.set('key2', "")

print("Transmitting to and recieving data from sendCommand.php...")

i = 0
with alive_bar(i, bar=False, monitor=False, spinner=False) as bar:
    try:
        while True:

            # Read the data stream from the laser spectrometer
            # NOTE: This data is only used by the inlet system to show the status of the measurements
            #       The final measurement results are evaluated using the .str and .stc files

            if( laser.inWaiting() > 10 ):
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
                # This error could occur when starting the script
                time.sleep(0.05)
                arduinoStatusNew = arduino.readline().decode('utf-8').strip()
            
            # print(arduinoStatus) # Show the raw serial output of the Arduino in the Terminal - for debugging

            # Check if we have a complete string using a regular expression
            pattern = re.compile(r'^-?[A-Z]{0,}[,][-]?\d+\.\d{2}[,][-]?\d+\.\d{1}[,][-]?\d+\.\d{2}[,][-]?\d+\.\d{1}[,][-]?\d+[,][-]?\d+\.\d{2}[,][A][,][-]?\d+\.\d{3}[,][-]?\d+\.\d{3}[,][-]?\d+\.\d{1}[,][B][,]\d{32}[,]\d{2,3}\.\d{2}[,]\d{2,3}\.\d{3}[,]\d{2}\.\d{2}[,](?:0|[1-9]\d?|100)$')
            if re.match(pattern, arduinoStatusNew):
                arduinoStatus = arduinoStatusNew
            # print(arduinoStatus) # Show the modified status string in the Terminal - for debugging

            # Read Edwards pressure gauge and temperature sensor every 10 cycles
            if(i == 10):

                edwards.write( bytes('?GA1\r','utf-8') )
                edwardsGauge = edwards.readline().decode('utf-8')
                # A little formatting is necessary because the string is sometimes broken
                if len(edwardsGauge) == 9:
                    vacuum = str(round(float(edwardsGauge), 4))
                
                # room temperature from sensor
                try:
                    sensor.get_sensor_data()
                    roomT = '{:05.2f}'.format(sensor.data.temperature)
                    roomH = '{:05.2f}'.format(sensor.data.humidity)
                except (OSError, RuntimeError, ZeroDivisionError):
                    # Dont break the loop if the sensor is disconnected
                    roomT = 1
                    roomH = 1
                
                i = 0

                time.sleep(0.05)

            # Create a status string from the information from Arduino, TILDAS, Edwards gauge, and room sensor and store it for PHP in the shared variable 'key'
            if( arduinoStatus != "" ):

                # Create the status string
                timeNow = datetime.datetime.now().strftime("%H:%M:%S")
                status = timeNow + ',' + arduinoStatus + ',' + laserStatus + ',' + vacuum + ',' + str(roomH)+ ',' + str(roomT)

                # Set shared variable: this is what the sendCommand.php files recieves
                m.set('key', status)

                # print(status) # Show the status string in the Terminal - for debugging

                time.sleep(0.05)

            # Receive commands for Arduino from PHP via shared variable 'key2'
            value = m.get('key2').decode('UTF-8')
            if( value != "" ):
                arduino.write( bytes(value, 'utf-8') )
                arduino.flush()
                # print(value) # Show command in the terminal - for debugging
                m.set('key2', "")

            # Clean up the shared variables
            m.close()

            i = i + 1
            bar()
    except KeyboardInterrupt:
        m.close()
        print("Loop stopped by user")