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
edwards = serial.Serial('/dev/ttyUSB1', baudrate=9600, timeout=1)
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
time.sleep(2)
# This is to wait until the Arduino is ready and the status message shows up, it starts with an 'X'

print("Starting continuously reading data from Arduino.")

i = 0
while( 2 > 1 ):
    # Read laser spectrometer data
    if( laser.inWaiting() > 10 ):
        laserStatus = laser.readline()
        laserStatus = laserStatus.decode('utf-8')
        # print(laserStatus)
        laserStatus = laserStatus[:-1]
        laserStatusArray = laserStatus.split(',')
        mr1 = laserStatusArray[1]
        mr2 = laserStatusArray[2]
        mr3 = laserStatusArray[3]
        mr4 = laserStatusArray[4]
        mr5 = laserStatusArray[5]
        mr6 = laserStatusArray[6]
        mr7 = laserStatusArray[7]
        mr8 = laserStatusArray[8]
        pressure = laserStatusArray[10]
        tempr = laserStatusArray[9]

    # Read Arduino data
    status = arduino.readline()
    # print(status) # Show the raw serial output of the Arduino in the Terminal - for debugging
    status = status.decode('utf-8')
    status = status[:-1]

    # Read Edwards pressure gauge and temperature sensor every 10 cycles
    if(i == 10):

        edwards.write( bytes('?GA1\r','utf-8') )
        edwardsGauge = edwards.readline().decode('utf-8')
        # A little formatting is necessary because the string is sometimes broken
        if len(edwardsGauge) == 9:
            vacuum = str(edwardsGauge)[:-1]
        
        # room temperature from sensor
        sensor.get_sensor_data()
        roomT = '{:05.3f}'.format(sensor.data.temperature)
        roomH = '{:05.3f}'.format(sensor.data.humidity)
        roomP = '{:05.3f}'.format(sensor.data.pressure)
        
        time.sleep(0.05)
        i = 0

    # Create a status string from the information from Arduino, TILDAS, and Edwards gauge and store it for PHP in the shared variable 'key'
    if( status != "" ):
        status = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ',' + status[:-1]
        m.set('key', status + ',' + pressure[:-1] + ',' + mr1 + ',' + mr2 + ',' + mr3 + ',' + mr4 + ',' + tempr + ',' + vacuum  + ',' + str(roomT)+ ',' + str(roomH) + ',' + str(roomP))
        # Show status string in terminal - for debugging
        # print(status + ',' + pressure[:-1] + ',' + mr1 + ',' + mr2 + ',' + mr3 + ',' + mr4 + ',' + tempr + ',' + vacuum + ',' + str(roomT) + ',' + str(roomH) + ',' + str(roomP))
        time.sleep(0.05)

    # Receive commands for Arduino from PHP via shared variable 'key2'
    value = m.get('key2').decode('UTF-8')
    if( value != "" ):
        arduino.write( bytes(value, 'utf-8') )
        # print(value) # Show command in the terminal - for debugging
        m.set('key2', "")
        time.sleep(0.05)

    i = i + 1