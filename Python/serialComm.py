from pymemcache.client import base
import time
import serial
import bme680
import datetime

# Arduino serial communication
arduino = serial.Serial('/dev/ttyACM0', baudrate=115200, timeout=1)
# Laser spectrometer serial communication (can also be ttyUSB1)
laser = serial.Serial('/dev/ttyUSB0', baudrate=57600, timeout=1)
# Edwards pressure gauge serial communication (can also be ttyUSB0)
edwards = serial.Serial('/dev/ttyUSB1', baudrate=9600, timeout=0.05) # a longer timeout stalls the script
# Initialize the breakout sensors
sensor = bme680.BME680(bme680.I2C_ADDR_PRIMARY)

# Set initial values, that are obviously fake
edwardsGauge = '1.00E+40'
vacuum = '1.00E+40'
roomT = 1
roomH = 1
roomP = 1

# Connect to the shared variable
m = base.Client(('127.0.0.1', 11211))
m.set('key2', "")

arduino.readline()
time.sleep(2) # This is to wait until the Arduino is ready and the status message shows up

print("Starting continuously reading data from Arduino.")

i = 0
while( 2 > 1 ):
    # Read laser spectrometer data
    if( laser.inWaiting() > 10 ):
        laserStatus = laser.readline().decode('utf-8')
        # print(laserStatus) # Show the raw serial output of the TILDAS in the Terminal - for debugging
        laserStatus = laserStatus[:-1] # Remove the line break from the end of the string
        # print(laserStatus) # Show the raw serial output of the TILDAS in the Terminal - for debugging

        laserStatusArray = laserStatus.split(',')

        mr1 = laserStatusArray[1] # 627
        mr2 = laserStatusArray[2] # 628
        mr3 = laserStatusArray[3] # 626
        mr4 = laserStatusArray[4] # free-path CO2
        cellT = laserStatusArray[9] # cell temperature
        cellP = laserStatusArray[10] # cell pressure (Torr)

        laserStatus = cellP[:-1] + ',' + mr1 + ',' + mr2 + ',' + mr3 + ',' + mr4 + ',' + cellT
        # print(laserStatus) # Show laser status string in the Terminal - for debugging

        # These are not used
        # mr5 = laserStatusArray[5]
        # mr6 = laserStatusArray[6]
        # mr7 = laserStatusArray[7]
        # mr8 = laserStatusArray[8]

    # Read Arduino data
    arduinoStatus = arduino.readline()
    # print(arduinoStatus) # Show the raw serial output of the Arduino in the Terminal - for debugging
    arduinoStatus = arduinoStatus.decode('utf-8')
    arduinoStatus = arduinoStatus[:-1] # Remove the line break from the end of the string
    # print(arduinoStatus) # Show the status string in the Terminal - for debugging

    # Read Edwards pressure gauge and temperature sensor every 10 cycles
    if(i == 10):

        edwards.write( bytes('?GA1\r','utf-8') )
        edwardsGauge = edwards.readline().decode('utf-8')
        # A little formatting is necessary because the string is sometimes broken
        if len(edwardsGauge) == 9:
            vacuum = str(edwardsGauge)[:-1]
        
        # room temperature from sensor
        sensor.get_sensor_data()
        roomT = '{:05.2f}'.format(sensor.data.temperature)
        roomH = '{:05.2f}'.format(sensor.data.humidity)
        
        time.sleep(0.05)
        i = 0

    # Create a status string from the information from Arduino, TILDAS, Edwards gauge, and room sensor and store it for PHP in the shared variable 'key'
    if( arduinoStatus != "" ):

        # Create the status string
        timeNow = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status = timeNow + ',' + arduinoStatus[:-1] + ',' + laserStatus + ',' + vacuum + ',' + str(roomT)+ ',' + str(roomH)

        # Set shared variable: this is what the sendCommand.php files recieves
        m.set('key', status)

        # print(status) # Show the status string in the Terminal - for debugging

        time.sleep(0.05)

    # Receive commands for Arduino from PHP via shared variable 'key2'
    value = m.get('key2').decode('UTF-8')
    if( value != "" ):
        arduino.write( bytes(value, 'utf-8') )
        # print(value) # Show command in the terminal - for debugging
        m.set('key2', "")
        time.sleep(0.05)

    i = i + 1

    # Clean up the shared variables
    m.close()