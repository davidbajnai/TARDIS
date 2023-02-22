# from IPython import get_ipython
# get_ipython().magic('reset -sf')

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import os
os.chdir( os.path.dirname(os.path.realpath(__file__)) )
# from scipy.signal import find_peaks
# import statistics
# from scipy.interpolate import CubicSpline
# from scipy.optimize import curve_fit

# Get current size
fig_size = plt.rcParams["figure.figsize"] 
# Set figure width to 12 and height to 9
fig_size[0] = 8
fig_size[1] = 6
plt.rcParams["figure.figsize"] = fig_size
plt.rcParams.update({'font.size': 14})

# Import data
folder = "/mnt/TILDAS-CS-132/Data/"
# Isotope data
# Day 1
# df1 = pd.read_csv("./" + folder + "/211215_193939.str", names=["Time(abs)", "I627", "I628", "I626","CO2"], delimiter=" ", skiprows=1, index_col=False)
# All the other data
# df2 = pd.read_csv("./" + folder + "/211215_193939.stc", delimiter=",", skiprows=1)
# Combine data from the two files (*.str, *.stc) into one file

print( folder )
