#!/usr/bin/env python
# -*- coding: utf-8 -*-
import serial
import time

outStr = ''
inStr = ''

ser = serial.Serial("/dev/ttyUSB0", 9600, timeout=2)
# if (ser.isOpen() == True):
#   ser.close()
#   print('Was open, is closed now before reopening.')
# ser.open()

# for i, a in enumerate(range(33, 126)):
#  outStr += chr(a)

# ser.write( bytes(outStr,'utf-8') )
# time.sleep(0.05)
inStr = ser.read(ser.inWaiting())

# print("Out-string:")
# print( bytes(outStr,'utf-8') )

print("In-string:")
print( inStr )

# if(inStr == outStr):
#   print ("Bingo!")
# else:
#   print ("Ooops!")
ser.close()




# #!/usr/bin/python3
# # from pymemcache.client import base
# 
# import time
# import serial
# import sys
# # import os
# import datetime
# port = '/dev/ttyUSB0'
# laserSpectrometer = serial.Serial(port,9600,timeout=3) # ,115200,timeout=3
# # This resets the Arduino, so this program needs to loop all time
# # without re-initializing the serial communication
# def write_read(cmd):
#     laserSpectrometer.write(bytes(cmd, 'utf-8')) # This could be a '?' to get the status
#     time.sleep(0.05) # Wait a bit
#     data = arduino.readline() # This now reads out the entire answer
#     return data
# 
# 
# # Connect to the shared variable
# # m = base.Client(('127.0.0.1', 11211))
# 
# # This is to wait until theArduino is ready and the status message shows up, it starts with an 'X'
# # while( write_read('?').decode('utf-8')[0:1] != 'X' ):
# #    msg = write_read('?').decode('utf-8')
#     # Here could be some action
#     # print( msg )
#     
# print("Starting main loop, contineously reading data from laser spectrometer")
# while( 2 > 1 ):
#     status = laserSpectrometer.readline()
#     # status = status.decode('utf-8')
#     # status = status[:-1]
#     if( status != "" ):
#         print('No signal')
#     else:
#         # status = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ',' + status[:-1]
#         # m.set('key', status)
#         print(status)
#     # value = m.get('key2').decode('UTF-8')
#     # if( value != "" ):
#     # arduino.write(bytes(value, 'utf-8')) # This could be a '?' to get the status
#     # time.sleep(0.05) # Wait a bit
#     # write_read(value).decode('utf-8')
#     # Set the key back to empty
#     # print("Command received",value)
#     # m.set('key2', "")
#     print('Send a Hallo')
#     laserSpectrometer.write(bytes('Hallo', 'utf-8')) # This could be a '?' to get the status
#     # time.sleep(0.05) # Wait a bit
#     # time.sleep(0.5)
# # clean up
# m.close()