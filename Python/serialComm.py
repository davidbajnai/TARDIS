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
# edwardsGauge = '1.00E+40'
vacuum = '9.999'
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

    # Read the data stream from the laser spectrometer
    # NOTE: This data is only used by the inlet system to show the status of the measurements
    #       The final measurement results are evaluated using the .str and .stc files

    if( laser.inWaiting() > 10 ):
        laserStatus = laser.readline().decode('utf-8')
        laserStatus = laserStatus[:-1] # Remove the line break from the end of the string
        # print(laserStatus) # Show the raw serial output of the TILDAS in the Terminal - for debugging

        laserStatusArray = laserStatus.split(',')

        mr1 = str(round(float(laserStatusArray[1]) / 1000,1)) # 627
        mr2 = str(round(float(laserStatusArray[2]) / 1000,1)) # 628
        mr3 = str(round(float(laserStatusArray[3]) / 1000,1)) # 626
        mr4 = str(round(float(laserStatusArray[4]) / 1000,1)) # free-path CO2
        # cellT = laserStatusArray[9] # cell temperature
        # cellP = laserStatusArray[10] # cell pressure (Torr)
        cellP = str(round(float(laserStatusArray[10]),3)) # cell pressure (Torr)

        laserStatus = cellP + ',' + mr1 + ',' + mr2 + ',' + mr3 + ',' + mr4
        # print(laserStatus) # Show laser status string in the Terminal - for debugging

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
            vacuum = str(round(float(edwardsGauge), 4))
        
        # room temperature from sensor
        sensor.get_sensor_data()
        roomT = '{:05.2f}'.format(sensor.data.temperature)
        roomH = '{:05.2f}'.format(sensor.data.humidity)
        
        i = 0

        time.sleep(0.05)

    # Create a status string from the information from Arduino, TILDAS, Edwards gauge, and room sensor and store it for PHP in the shared variable 'key'
    if( arduinoStatus != "" ):

        # Create the status string
        timeNow = datetime.datetime.now().strftime("%H:%M:%S")
        status = timeNow + ',' + arduinoStatus[:-1] + ',' + laserStatus + ',' + vacuum + ',' + str(roomT)+ ',' + str(roomH)

        # Set shared variable: this is what the sendCommand.php files recieves
        m.set('key', status)

        print(status) # Show the status string in the Terminal - for debugging

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