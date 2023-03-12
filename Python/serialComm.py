from pymemcache.client import base
import time
import serial
import bme680
import datetime
import re

# Arduino serial communication
try:
    arduino = serial.Serial('/dev/ttyACM0', baudrate=115200, timeout=1)
    print("Connection to Arduino established")
    time.sleep(2)
except serial.SerialException:
    print("Connection to Arduino could not be established. Stopping the script.")
    quit()

# Laser spectrometer serial communication
try:
    laser = serial.Serial('/dev/ttyUSB0', baudrate=57600, timeout=1)
    print("Connection to the TILDAS established over /dev/ttyUSB0")
    time.sleep(2)
except serial.SerialException:
    laser = serial.Serial('/dev/ttyUSB1', baudrate=57600, timeout=1)
    print("Connection to the TILDAS established over /dev/ttyUSB1")
    time.sleep(2)

# Edwards pressure gauge serial communication (can also be ttyUSB0)
try:
    edwards = serial.Serial('/dev/ttyUSB1', baudrate=9600, timeout=0.05) # a longer timeout stalls the script
    print("Connection to the Edwards gauge established over /dev/ttyUSB1")
    time.sleep(2)
except serial.SerialException:
    edwards = serial.Serial('/dev/ttyUSB0', baudrate=9600, timeout=0.05) # a longer timeout stalls the script
    print("Connection to the Edwards gauge established over /dev/ttyUSB0")
    time.sleep(2)

# Initialize the breakout sensors
sensor = bme680.BME680(bme680.I2C_ADDR_PRIMARY)

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
while( 2 > 1 ):

    # Read the data stream from the laser spectrometer
    # NOTE: This data is only used by the inlet system to show the status of the measurements
    #       The final measurement results are evaluated using the .str and .stc files

    if( laser.inWaiting() > 10 ):
        laserStatus = laser.readline().decode('utf-8').strip()
        # print(laserStatus) # Show the raw serial output of the TILDAS in the Terminal - for debugging

        laserStatusArray = laserStatus.split(',')

        mr1 = str(round(float(laserStatusArray[1]) / 1000,1)) # 627
        mr2 = str(round(float(laserStatusArray[2]) / 1000,1)) # 628
        mr3 = str(round(float(laserStatusArray[3]) / 1000,1)) # 626
        mr4 = str(round(float(laserStatusArray[4]) / 1000,1)) # free-path CO2
        cellP = str(round(float(laserStatusArray[10]),3)) # cell pressure (Torr)

        laserStatus = cellP + ',' + mr1 + ',' + mr2 + ',' + mr3 + ',' + mr4
        # print(laserStatus) # Show laser status string in the Terminal - for debugging

    # Read Arduino data
    arduinoStatusNew = arduino.readline().decode('utf-8').strip()
    # print(arduinoStatus) # Show the raw serial output of the Arduino in the Terminal - for debugging

    # Check if we have a complete string using a regular expression
    pattern = re.compile(r'^-?[A-Z]{0,}[,][-]?\d+\.\d{2}[,][-]?\d+\.\d{1}[,][-]?\d+\.\d{2}[,][-]?\d+\.\d{1}[,][-]?\d+[,][-]?\d+\.\d{2}[,][-]?\d+\.\d{3}[,][-]?\d+\.\d{3}[,][-]?\d+\.\d{1}[,][SW][,]\d{32}[,]\d{2,3}\.\d{2}[,]\d{2,3}\.\d{3}[,](?:0|[1-9]\d?|100)$')
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
            # Dont break the loop if the sensor does not respond
            sensor.get_sensor_data()
            roomT = '{:05.2f}'.format(sensor.data.temperature)
            roomH = '{:05.2f}'.format(sensor.data.humidity)
        except OSError:
            roomT = 1
            roomH = 1
        
        i = 0

        time.sleep(0.05)

    # Create a status string from the information from Arduino, TILDAS, Edwards gauge, and room sensor and store it for PHP in the shared variable 'key'
    if( arduinoStatus != "" ):

        # Create the status string
        timeNow = datetime.datetime.now().strftime("%H:%M:%S")
        status = timeNow + ',' + arduinoStatus + ',' + laserStatus + ',' + vacuum + ',' + str(roomT)+ ',' + str(roomH)

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

    i = i + 1

    # Clean up the shared variables
    m.close()