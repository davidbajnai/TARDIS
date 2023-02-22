#!/usr/bin/python3
from pymemcache.client import base

# connect
m = base.Client(('127.0.0.1', 11211))

# get a value
value = m.get('key')
print("Value read:",value)

# set a value
# m.set('key', 'value from python')

# clean up
m.close()