# from IPython import get_ipython
# get_ipython().magic('reset -sf')


import matplotlib as mpl
import matplotlib.pyplot as plt
import sys
from os.path import exists
from scipy.stats import sem
from scipy import stats
from scipy.optimize import curve_fit
import os
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

# from aem import app
os.environ['MPLCONFIGDIR'] = "/var/www/html/Python"
# os.environ['MPLCONFIGDIR'] = "/Users/apack/Downloads/Testarea/Python" # < -------- M A N U A L (otherwise comment out)
os.chdir(os.path.dirname(os.path.realpath(__file__)))

# import statistics
# from scipy.interpolate import CubicSpline
# from scipy.optimize import curve_fit

# Import data of a single measurement
if len(sys.argv) == 3:
    folder = "../Results/" + str(sys.argv[1]) + "/"
    polynomial = str(sys.argv[2])
else:
    sys.argv.append("220701_021845_NBS19")  # < -------- M A N U A L
    sys.argv.append("2")
    folder = "../Results/" + str(sys.argv[1]) + "/"
    print(folder)
    polynomial = str(sys.argv[2])

samID = str(sys.argv[1])

strFiles = []
for file in os.listdir(folder):
    if file.endswith(".str"):
        strFiles.append(file)
strFiles.sort()

# Pattern for the measurement, default is Ref Sam Ref Sam […] Ref
pattern = ["Dummy", "Ref", "Sam", "Ref", "Sam", "Ref", "Sam", "Ref", "Sam", "Ref", "Sam", "Ref", "Sam", "Ref", "Sam", "Ref", "Sam", "Ref", "Sam", "Ref", "Sam", "Ref", "Sam", "Ref"]

i = 0
for file in strFiles:
    baseName = file[:-4]
    df1 = pd.read_csv(folder + baseName + ".str", names=["Time(abs)", "I627", "I628", "I626", "CO2"], delimiter=" ", skiprows=1, index_col=False)
    if i == 0:
        startTime = df1['Time(abs)'][0]
    # All the other data
    df2 = pd.read_csv(folder + baseName + ".stc", delimiter=",", skiprows=1)
    # Combine data from the two files (*.str, *.stc) into one file
    df = pd.concat([df1, df2], axis=1, join="inner")
    df['Type'] = pattern[i]
    # df['Cycle'] = i
    df['Time(rel)'] = df['Time(abs)'] - startTime
    # Now filter Δ'17O data using the z-Method
    df['d17Otmp'] = ((df['I627'] / df['I626']) / np.mean(df['I627'] / df['I626']) - 1) * 1000
    df['d18Otmp'] = ((df['I628'] / df['I626']) / np.mean(df['I628'] / df['I626']) - 1) * 1000
    df['Dp17Otmp'] = (1000 * np.log(df['d17Otmp'] / 1000 + 1) - 0.528 * 1000 * np.log(df['d18Otmp'] / 1000 + 1)) * 1000
    df['z_score'] = stats.zscore(df['Dp17Otmp'])
    df['Cycle'] = i
    if i == 0:
        dfAll = df
    else:
        dfAll = dfAll.append(df, ignore_index=True)
    i = i + 1

# dfAll['Cycle'] = df['Cycle']
dfAll['d17O'] = ((dfAll['I627'] / dfAll['I626']) / np.mean(dfAll['I627'] / dfAll['I626']) - 1) * 1000
dfAll['d18O'] = ((dfAll['I628'] / dfAll['I626']) / np.mean(dfAll['I628'] / dfAll['I626']) - 1) * 1000
dfAll['Dp17O'] = (1000 * np.log(dfAll['d17O'] / 1000 + 1) - 0.528 * 1000 * np.log(dfAll['d18O'] / 1000 + 1)) * 1000

# Export all data into an Excel file
dfAll.to_excel(folder + "allData.xlsx")

# Plot the rawdata
width = 6
height = 20
plt.rcParams["figure.figsize"] = (width, height)
plt.rcParams.update({'font.size': 6})

mpl.rcParams['axes.prop_cycle'] = mpl.cycler(color=["#4053d3", "#ddb310", "#b51d14", "#cacaca"])

df = dfAll
# Now select data using the z-score (3sigma criterion)
df = df.loc[df['z_score'].abs() <= 3]
dfOutliers = df.loc[df['z_score'].abs() > 3]
nOutliers = dfOutliers.shape[0]
# Get data from the logfile (T and humidity)
if(exists(folder + "logFile.csv")):
    dfLogFile = pd.read_csv(folder + "logFile.csv")
    # exclude lines that have no data in the 6th column, this is backwards compatible
    dfLogFile = dfLogFile[dfLogFile.percentageX.notnull()]
    # print( dfLogFile )

seconds = df['Time(rel)'].iat[-1]
seconds = seconds % (24 * 3600)
hour = seconds // 3600
seconds %= 3600
minutes = seconds // 60
seconds %= 60
measurementTime = str("%d:%02d:%02d" % (hour, minutes, seconds))
if(exists(folder + "logFile.csv")):
    x_logFile = dfLogFile['Time(abs)'] + 7200 - df['Time(abs)'][0]

# Now plot measurement
pltsize = 11

# Subplot A: d18O vs time
ax1 = plt.subplot(pltsize, 1, 1)
x = df['Time(rel)']
y = df['d18O']
plt.text(0.06 / width, 1 - 0.06 / height * 8, 'A', size=14, horizontalalignment='left', verticalalignment='top', transform=ax1.transAxes)
plt.scatter(x, y, marker=".")
plt.ylabel("$\delta^{18}$O (‰, raw)")
plt.title(samID + "\nmeasurement duration: " + measurementTime)

# Subplot B: D17O vs time
ax7 = plt.subplot(pltsize, 1, 2, sharex=ax1)
x = df['Time(rel)']
y = df['Dp17O']
plt.text(0.06 / width, 1 - 0.06 / height * 8, 'B', size=14, horizontalalignment='left', verticalalignment='top', transform=ax7.transAxes)
plt.scatter(x, y, marker=".")
plt.ylabel("$\Delta^{17}$O (ppm, raw)")

# Subplot B: free CO2 vs time
# ax2 = plt.subplot(pltsize, 1, 2, sharex=ax1)
# y = df['CO2'] / 1000
# plt.text(0.06 / width, 1 - 0.06 / height * 8, 'B', size=14, horizontalalignment='left', verticalalignment='top', transform=ax2.transAxes)
# plt.scatter(x, y, marker=".")
# plt.ylabel("CO$_2$ (free path, ppmv)")

# Subplot C: CO2 in cell vs time
ax3 = plt.subplot(pltsize, 1, 3, sharex=ax1)
x = df['Time(rel)']
y = df['I626'] / 1000
plt.text(0.06 / width, 1 - 0.06 / height * 8, 'C', size=14, horizontalalignment='left', verticalalignment='top', transform=ax3.transAxes)
plt.scatter(x, y, marker=".")
plt.ylabel("CO$_2$ (ppm, cell)")

# Subplot D: Cell pressure vs time
ax4 = plt.subplot(pltsize, 1, 4, sharex=ax1)
x = df['Time(rel)']
y = df[' Praw']
plt.text(0.06 / width, 1 - 0.06 / height * 8, 'D', size=14, horizontalalignment='left', verticalalignment='top', transform=ax4.transAxes)
plt.scatter(x, y, marker=".")
plt.ylabel("Pressure (Torr, cell)")

# Subplot E: Cell temperature
ax6 = plt.subplot(pltsize, 1, 5, sharex=ax1)
x = df['Time(rel)']
y = df[' Traw'] - 273.15
plt.scatter(x, y, marker=".")
plt.ylabel("Temperature (°C, cell)")
minty = np.round(np.mean(y), 3)
sdt = np.round(np.std(y), 3)
la = str(minty) + "±" + str(sdt) + " °C"
plt.text(0.06 / width, 0.06 / height * 11, la, size=8, color="C0", horizontalalignment='left', verticalalignment='bottom', transform=ax6.transAxes, bbox=dict(fc='white', ec="none", pad=2))
plt.text(0.06 / width, 1 - 0.06 / height * 8, 'E', size=14, horizontalalignment='left', verticalalignment='top', transform=ax6.transAxes)

# Subplot F: Coolant temperature and room temperature
ax5 = plt.subplot(pltsize, 1, 6, sharex=ax1)
x = df['Time(rel)']
y = df[' Tref'] - 273.15
plt.scatter(x, y, marker=".")
plt.ylabel("Temperature (°C, coolant)")
minty = np.round(np.mean(y), 3)
sdt = np.round(np.std(y), 3)
la = str(minty) + "±" + str(sdt) + " °C"
if (exists(folder + "logFile.csv")) and ('RoomT' in dfLogFile.columns):
    ax5b = ax5.twinx()
    ax5b.spines['right'].set_color('C1')
    x = x_logFile
    y = dfLogFile['RoomT']
    plt.plot(x, y, color="C1")
    plt.ylabel("Temperature (°C, room)")
    minty_2 = np.round(np.mean(y), 3)
    sdt_2 = np.round(np.std(y), 3)
    la_2 = str(minty_2) + "±" + str(sdt_2) + " °C"
    plt.text(1-0.06 / width, 0.06 / height * 11, la_2, size=8, color="C1", horizontalalignment='right', verticalalignment='bottom', transform=ax5.transAxes, bbox=dict(fc='white', ec="none", pad=2))
plt.text(0.06 / width, 0.06 / height * 11, la, size=8, color="C0", horizontalalignment='left', verticalalignment='bottom', transform=ax5.transAxes, bbox=dict(fc='white', ec="none", pad=2))
plt.text(0.06 / width, 1 - 0.06 / height * 8, 'F', size=14, horizontalalignment='left', verticalalignment='top', transform=ax5.transAxes)

# # Subplot I: Room temperature vs time
# ax8 = plt.subplot(pltsize, 1, 8, sharex=ax1)
# if 'RoomT' in dfLogFile.columns:
#     y = dfLogFile['RoomT']
#     plt.plot(x, y)
# plt.text(0.06 / width, 1 - 0.06 / height * 8, 'I', size=14, horizontalalignment='left', verticalalignment='top', transform=ax8.transAxes)
# plt.ylabel("Temperature (°C, room)")

# Subplot G: Box temperature vs time
ax11 = plt.subplot(pltsize, 1, 7, sharex=ax1)
if (exists(folder + "logFile.csv")) and ('Temperature(room)' in dfLogFile.columns):
    x = x_logFile
    y = dfLogFile['Temperature(room)']
    plt.plot(x, y)
    plt.ylabel("Temperature (°C, box)")
    meany = np.round(np.mean(y), 3)
    stdy = np.round(np.std(y), 3)
    laby = str(meany) + "±" + str(stdy) + " °C"
    if 'TargetT(box)' in dfLogFile.columns:
        x = x_logFile
        y = dfLogFile['TargetT(box)']
        plt.plot(x, y, color="C2")
        laSP = str("SP: ") + str(dfLogFile['TargetT(box)'].iat[0]) + " °C"
    if 'fanSpeed' in dfLogFile.columns:
        ax11b = ax11.twinx()
        ax11b.spines['right'].set_color('C1')
        x = x_logFile
        y = dfLogFile['fanSpeed']
        plt.plot(x, y, color="C1")
        plt.ylabel("Fan speed (%)")
        plt.text(0.06 / width, 0.15 - 0.06 / height * 8, laSP, size=8, color="C2", horizontalalignment='left', verticalalignment='bottom', transform=ax11.transAxes, bbox=dict(fc='white', ec="none", pad=2))
    plt.text(0.06 / width, 0.06 / height * 11, laby, size=8, color="C0", horizontalalignment='left', verticalalignment='bottom', transform=ax11.transAxes, bbox=dict(fc='white', ec="none", pad=2))
plt.text(0.06 / width, 1 - 0.06 / height * 11, 'G', size=14, horizontalalignment='left', verticalalignment='top', transform=ax11.transAxes)

# Subplot J: Room humidity vs time
# ax9 = plt.subplot(pltsize, 1, 9, sharex=ax1)
# if 'RoomH' in dfLogFile.columns:
#     y = dfLogFile['RoomH']
#     plt.plot(x, y)
# plt.text(0.06 / width, 1 - 0.06 / height * 8, 'J', size=14, horizontalalignment='left', verticalalignment='top', transform=ax9.transAxes)
# plt.ylabel("Humidity (%, room)")

# Subplot K: Room pressure vs time
# ax10 = plt.subplot(pltsize, 1, 10, sharex=ax1)
# if 'RoomP' in dfLogFile.columns:
#     y = dfLogFile['RoomP']
#     plt.plot(x, y)
# plt.text(0.06 / width, 1 - 0.06 / height * 8, 'K', size=14, horizontalalignment='left', verticalalignment='top', transform=ax10.transAxes)
# plt.ylabel("Pressure (hPa, room)")

# Subplot H: Box humidity and room humidity
ax12 = plt.subplot(pltsize, 1, 8, sharex=ax1)
if (exists(folder + "logFile.csv")) and ('Humidity(room)' in dfLogFile.columns):
    x = x_logFile
    y = dfLogFile['Humidity(room)']
    plt.plot(x, y)
    plt.ylabel("Humidity (%, box)")
    meany = np.round(np.mean(y), 2)
    stdy = np.round(np.max(y)-np.min(y), 2)
    laby = str(meany) + "%, " + "∆RH: " + str(stdy) + "%"
    if 'RoomH' in dfLogFile.columns:
        x = x_logFile
        y = dfLogFile['RoomH']
        ax12b = ax12.twinx()
        ax12b.spines['right'].set_color('C1')
        plt.plot(x, y, color="C1")
        plt.ylabel("Humidity (%, room)")
        meany_2 = np.round(np.mean(y), 2)
        stdy_2 = np.round(np.max(y)-np.min(y), 2)
        laby_2 = str(meany_2) + "%, " + "∆RH: " + str(stdy_2) + "%"
        plt.text(1 - 0.06 / width, 0.06 / height * 11, laby_2, size=8, color="C1", horizontalalignment='right', verticalalignment='bottom', transform=ax12.transAxes, bbox=dict(fc='white', ec="none", pad=2))
    plt.text(0.06 / width, 0.06 / height * 11, laby, size=8, color="C0", horizontalalignment='left', verticalalignment='bottom', transform=ax12.transAxes, bbox=dict(fc='white', ec="none", pad=2))
plt.text(0.06 / width, 1 - 0.06 / height * 8, 'H', size=14, horizontalalignment='left', verticalalignment='top', transform=ax12.transAxes)

# Subplot I: X (reference) bellow expansion and pressure
ax13 = plt.subplot(pltsize, 1, 9, sharex=ax1)
if (exists(folder + "logFile.csv")) and ('pressureX' in dfLogFile.columns):
    x = x_logFile
    y = dfLogFile['pressureX']
    plt.plot(x, y)
    plt.ylabel("X (ref.) bellow pressure (mbar)")
    ax13b = ax13.twinx()
    ax13b.spines['right'].set_color('C1')
    y = dfLogFile['percentageX']
    plt.plot(x, y, color="C1")
    plt.ylabel("X (ref.) bellow expansion (%)")
    plt.text(0.06 / width, 1 - 0.06 / height * 8, 'I', size=14, horizontalalignment='left', verticalalignment='top', transform=ax13.transAxes)

# Subplot J: Y (sample) bellow expansion and pressure
ax14 = plt.subplot(pltsize, 1, 10, sharex=ax1)
if (exists(folder + "logFile.csv")) and ('pressureY' in dfLogFile.columns):
    x = x_logFile
    y = dfLogFile['pressureY']
    plt.plot(x, y, label="Y (Reference)")
    plt.ylabel("Y (sam.) bellow pressure (mbar)")
    ax14b = ax14.twinx()
    ax14b.spines['right'].set_color('C1')
    y = dfLogFile['percentageY']
    plt.plot(x, y, color="C1")
    plt.ylabel("Y (sam.) bellow expansion (%)")
    plt.text(0.06 / width, 1 - 0.06 / height * 8, 'J', size=14, horizontalalignment='left', verticalalignment='top', transform=ax14.transAxes)

# Subplot K: Z bellow
ax15 = plt.subplot(pltsize, 1, 11, sharex=ax1)
if 'pressureA' in dfLogFile.columns:
    x = x_logFile
    y = dfLogFile['pressureA']
    plt.plot(x, y)
    plt.ylabel("A pressure (mbar)")
    ax15b = ax15.twinx()
    ax15b.spines['right'].set_color('C1')
    y = dfLogFile['percentageZ']
    plt.plot(x, y, color="C1")
    plt.ylabel("Z bellow expansion (%)")
    plt.text(0.06 / width, 1 - 0.06 / height * 8, 'K', size=14, horizontalalignment='left', verticalalignment='top', transform=ax15.transAxes)

plt.xlabel("Relative time (s)")
plt.tight_layout()
plt.savefig(folder + "rawData.svg")
plt.savefig(folder + "rawData.png", dpi=300)
# plt.show()


# Now fit the data ####################################################################################
height = 15
width = 6
plt.rcParams["figure.figsize"] = (width, height)
plt.rcParams["legend.loc"] = "upper left"
plt.figure(0)
plt.rcParams.update({'font.size': 6})

# Fit data
# Fit the ref and sam data with the same a1, a2, a3 and only different intercepts r0, s0
# Modified after https://stackoverflow.com/questions/51482486/python-global-fitting-for-data-sets-of-different-sizes
# Reference gas data

# Reference gas composition: D'17O = -100 ppm
d18ORS = 28.048
d17ORS = 14.611 + 0.010  # D'17O = -90 ppm

dfRef = df.loc[df['Type'] == "Ref"]
dfSam = df.loc[df['Type'] == "Sam"]
dfDummy = df.loc[df['Type'] == "Dummy"]

# Fit für d17O ###############################################################################################
ax1 = plt.subplot(3, 1, 1)

xDummy = df.loc[df['Type'] == "Dummy"]["Time(rel)"]
d17ODummyRaw = ((dfDummy['I627']/dfDummy['I626'])/np.mean(df['I627']/df['I626']) - 1) * 1000
d18ODummyRaw = ((dfDummy['I628']/dfDummy['I626'])/np.mean(df['I628']/df['I626']) - 1) * 1000
yDummy = d17ODummyRaw
plt.scatter(xDummy, yDummy, color="#cacaca", marker=".", label="Dummy (ref.) CO$_2$")

xRef = df.loc[df['Type'] == "Ref"]["Time(rel)"]
d17ORefRaw = ((dfRef['I627']/dfRef['I626'])/np.mean(df['I627']/df['I626']) - 1) * 1000
d18ORefRaw = ((dfRef['I628']/dfRef['I626'])/np.mean(df['I628']/df['I626']) - 1) * 1000
yRef = d17ORefRaw
plt.scatter(xRef, yRef, color="#b51d14", marker=".", label="Reference CO$_2$")

xSam = dfSam['Time(rel)']
d17O = ((dfSam['I627']/dfSam['I626'])/np.mean(df['I627']/df['I626']) - 1) * 1000
d18O = ((dfSam['I628']/dfSam['I626'])/np.mean(df['I628']/df['I626']) - 1) * 1000
ySam = d17O
plt.scatter(xSam, ySam, color="#4053d3", marker=".", label="Sample CO$_2$")

y1 = np.array(df.loc[df['Type'] == "Ref"]['d17O'])
y2 = np.array(df.loc[df['Type'] == "Sam"]['d17O'])
comboY = np.append(y1, y2)

x1 = np.array(xRef)
x2 = np.array(xSam)
comboX = np.append(x1, x2)

if len(y1) != len(x1):
    raise(Exception('Unequal x1 and y1 data length'))
if len(y2) != len(x2):
    raise(Exception('Unequal x2 and y2 data length'))


def function1(data, r0, s0, a1, a2, a3):  # not all parameters are used here, a1, a2 are sha#b51d14
    if polynomial == "100":
        return r0 + a1 * data + a2 * data * data
    if polynomial == "3":
        return r0 + a1 * data + a2 * data * data + a3 * data * data * data
    if polynomial == "2":
        return r0 + a1 * data + a2 * data * data
    if polynomial == "1":
        return r0 + a1 * data
    if polynomial == "0":
        return r0


def function2(data, r0, s0, a1, a2, a3):  # not all parameters are used here, c is sha#b51d14
    if polynomial == "100":
        return s0 + a1 * data + a2 * data * data
    if polynomial == "3":
        return s0 + a1 * data + a2 * data * data + a3 * data * data * data
    if polynomial == "2":
        return s0 + a1 * data + a2 * data * data
    if polynomial == "1":
        return s0 + a1 * data
    if polynomial == "0":
        return s0


def combinedFunction(comboData, r0, s0, a1, a2, a3):
    # single data reference passed in, extract separate data
    extract1 = comboData[:len(x1)]  # first data
    extract2 = comboData[len(x1):]  # second data

    result1 = function1(extract1, r0, s0, a1, a2, a3)
    result2 = function2(extract2, r0, s0, a1, a2, a3)

    return np.append(result1, result2)


# some initial parameter values
initialParameters = np.array([1, 0, 0, 0, 0])

# curve fit the combined data to the combined function
fittedParameters, pcov = curve_fit(combinedFunction, comboX, comboY, initialParameters)

# values for display of fitted function
r0, s0, a1, a2, a3 = fittedParameters

xFitData = np.arange(min(dfRef['Time(rel)']), max(dfRef['Time(rel)']))

y_fit_1 = function1(xFitData, r0, s0, a1, a2, a3)  # first data set, first equation
y_fit_2 = function2(xFitData, r0, s0, a1, a2, a3)  # second data set, second equation

α17SR = (y_fit_2[0] + 1000) / (y_fit_1[0] + 1000)

plt.plot(xFitData, y_fit_1, color="#b51d14")
plt.plot(xFitData, y_fit_2, color="#4053d3")


plt.ylabel("$\delta^{17}$O (‰)")

plt.title("$1000\,\ln{ α_\mathrm{Sam-Ref}^{17} }$ = " + str(round(1000 * np.log(α17SR), 3)))

plt.legend()

# Fit für d18O ###############################################################################################
ax1 = plt.subplot(3, 1, 2)

xRef = df.loc[df['Type'] == "Ref"]["Time(rel)"]
d17ORefRaw = ((dfRef['I627']/dfRef['I626'])/np.mean(df['I627']/df['I626']) - 1) * 1000
d18ORefRaw = ((dfRef['I628']/dfRef['I626'])/np.mean(df['I628']/df['I626']) - 1) * 1000
yRef = d18ORefRaw
plt.scatter(xRef, yRef, color="#b51d14", marker=".", label="Reference CO$_2$")

xSam = dfSam['Time(rel)']
d17O = ((dfSam['I627']/dfSam['I626'])/np.mean(df['I627']/df['I626']) - 1) * 1000
d18O = ((dfSam['I628']/dfSam['I626'])/np.mean(df['I628']/df['I626']) - 1) * 1000
ySam = d18O
plt.scatter(xSam, ySam, color="#4053d3", marker=".", label="Sample CO$_2$")

xDummy = df.loc[df['Type'] == "Dummy"]["Time(rel)"]
d17ODummyRaw = ((dfDummy['I627']/dfDummy['I626'])/np.mean(df['I627']/df['I626']) - 1) * 1000
d18ODummyRaw = ((dfDummy['I628']/dfDummy['I626'])/np.mean(df['I628']/df['I626']) - 1) * 1000
yDummy = d18ODummyRaw
plt.scatter(xDummy, yDummy, color="#cacaca", marker=".", label="Dummy (ref.) CO$_2$")

y1 = np.array(df.loc[df['Type'] == "Ref"]['d18O'])
y2 = np.array(df.loc[df['Type'] == "Sam"]['d18O'])
comboY = np.append(y1, y2)

x1 = np.array(xRef)
x2 = np.array(xSam)
comboX = np.append(x1, x2)

if len(y1) != len(x1):
    raise(Exception('Unequal x1 and y1 data length'))
if len(y2) != len(x2):
    raise(Exception('Unequal x2 and y2 data length'))

# def function1(data, r0, s0, a1, a2, a3): # not all parameters are used here, a1, a2 are sha#b51d14
#     return r0 + a1 * data + a2 * data * data + a3 * data * data * data

# def function2(data, r0, s0, a1, a2, a3): # not all parameters are used here, c is sha#b51d14
#     return s0 + a1 * data + a2 * data * data + a3 * data * data * data

# def combinedFunction(comboData, r0, s0, a1, a2, a3):
#     # single data reference passed in, extract separate data
#     extract1 = comboData[:len(x1)] # first data
#     extract2 = comboData[len(x1):] # second data

#     result1 = function1(extract1, r0, s0, a1, a2, a3)
#     result2 = function2(extract2, r0, s0, a1, a2, a3)

#     return np.append(result1, result2)

# some initial parameter values
initialParameters = np.array([1.0, 1.0, 1.0, 1.0, 1.0])

# curve fit the combined data to the combined function
fittedParameters, pcov = curve_fit(combinedFunction, comboX, comboY, initialParameters)

# values for display of fitted function
r0, s0, a1, a2, a3 = fittedParameters

# xFitData = np.arange(-400,1000)

y_fit_1 = function1(xFitData, r0, s0, a1, a2, a3)  # first data set, first equation
y_fit_2 = function2(xFitData, r0, s0, a1, a2, a3)  # second data set, second equation

α18SR = (y_fit_2[0] + 1000) / (y_fit_1[0] + 1000)

plt.plot(xFitData, y_fit_1, color="#b51d14")
plt.plot(xFitData, y_fit_2, color="#4053d3")

plt.ylabel("$\delta^{18}$O (‰)")

plt.title("$1000\,\ln{ α_\mathrm{Sam-Ref}^{18} }$ = " + str(round(1000 * np.log(α18SR), 3)))

plt.legend()

# Now we have

d17OSR = (α17SR - 1) * 1000
d18OSR = (α18SR - 1) * 1000

d17OSS = round(d17OSR + d17ORS + 1/1000 * d17OSR * d17ORS, 3)
d18OSS = round(d18OSR + d18ORS + 1/1000 * d18OSR * d18ORS, 3)
Dp17OSS = round((1000 * np.log(d17OSS / 1000 + 1) - 0.528 * 1000 * np.log(d18OSS / 1000 + 1)) * 1000, 1)

# Fit für D'17O

plt.subplot(3, 1, 3)

xRef = dfRef['Time(rel)']
d17O = ((dfRef['I627']/dfRef['I626'])/np.mean(df['I627']/df['I626']) - 1) * 1000
d17O = d17O + d17ORS + 1/1000 * d17O * d17ORS
d18O = ((dfRef['I628']/dfRef['I626'])/np.mean(df['I628']/df['I626']) - 1) * 1000
d18O = d18O + d18ORS + 1/1000 * d18O * d18ORS
yRef = (1000 * np.log(d17O/1000+1) - 0.528 * 1000 * np.log(d18O/1000+1)) * 1000
plt.scatter(xRef, yRef, color="#b51d14", marker=".", label="Reference CO$_2$")

# i = 0
# while i < len( intervalsRef ):
#     dfRefMean = df.loc[ (df['Time(rel)'] > intervalsRef[i][0]) & (df['Time(rel)'] < intervalsRef[i][1])]
#     xRefMean = dfRefMean['Time(rel)']
#     d17OMean = ( (dfRefMean['I627']/dfRefMean['I626'])/np.mean( df['I627']/df['I626'] ) - 1 ) * 1000
#     d17OMean = d17OMean + d17ORS + 1/1000 * d17OMean * d17ORS
#     d18OMean = ( (dfRefMean['I628']/dfRefMean['I626'])/np.mean( df['I628']/df['I626'] ) - 1 ) * 1000
#     d18OMean = d18OMean + d18ORS + 1/1000 * d18OMean * d18ORS
#     yRefMean = (1000 * np.log( d17OMean/1000+1 ) - 0.528 * 1000 * np.log( d18OMean/1000+1 )) * 1000
#     plt.errorbar(
#         np.mean(xRefMean),np.mean(yRefMean),
#         xerr=None,
#         yerr=np.std(yRefMean) / np.sqrt( len(xRefMean) ),
#         marker="o",
#         marke#b51d14gecolor="black",
#         color="#b51d14",
#         markersize=10,
#         zorder=100
#     )
#     i = i + 1

xSam = dfSam['Time(rel)']
d17O = ((dfSam['I627']/dfSam['I626'])/np.mean(df['I627']/df['I626']) - 1) * 1000
d17O = d17O + d17ORS + 1/1000 * d17O * d17ORS
d18O = ((dfSam['I628']/dfSam['I626'])/np.mean(df['I628']/df['I626']) - 1) * 1000
d18O = d18O + d18ORS + 1/1000 * d18O * d18ORS
ySam = (1000 * np.log(d17O/1000+1) - 0.528 * 1000 * np.log(d18O/1000+1)) * 1000
plt.scatter(xSam, ySam, color="#4053d3", marker=".", label="Sample CO$_2$")

xDummy = df.loc[df['Type'] == "Dummy"]["Time(rel)"]
d17ODummyRaw = ((dfDummy['I627']/dfDummy['I626'])/np.mean(df['I627']/df['I626']) - 1) * 1000
d18ODummyRaw = ((dfDummy['I628']/dfDummy['I626'])/np.mean(df['I628']/df['I626']) - 1) * 1000
yDummy = (1000 * np.log(d17ODummyRaw/1000+1) - 0.528 * 1000 * np.log(d18ODummyRaw/1000+1)) * 1000
plt.scatter(xDummy, yDummy, color="#cacaca", marker=".", label="Dummy (ref.) CO$_2$")

# Dp17Osample = np.mean( ySam )

# i = 0
# while i < len( intervalsSam ):
#     dfSamMean = df.loc[ (df['Time(rel)'] > intervalsSam[i][0]) & (df['Time(rel)'] < intervalsSam[i][1])]
#     xSamMean = dfSamMean['Time(rel)']
#     d17OMean = ( (dfSamMean['I627']/dfSamMean['I626'])/np.mean( df['I627']/df['I626'] ) - 1 ) * 1000
#     d17OMean = d17OMean + d17ORS + 1/1000 * d17OMean * d17ORS
#     d18OMean = ( (dfSamMean['I628']/dfSamMean['I626'])/np.mean( df['I628']/df['I626'] ) - 1 ) * 1000
#     d18OMean = d18OMean + d18ORS + 1/1000 * d18OMean * d18ORS
#     ySamMean = (1000 * np.log( d17OMean/1000+1 ) - 0.528 * 1000 * np.log( d18OMean/1000+1 )) * 1000
#     plt.errorbar(
#         np.mean(xSamMean),np.mean(ySamMean),
#         xerr=None,
#         yerr=np.std(ySamMean) / np.sqrt( len(xSamMean) ),
#         marker="o",
#         marke#b51d14gecolor="white",
#         color="#4053d3",
#         markersize=10,
#         zorder=100
#     )
#     i = i + 1

y1 = np.array(yRef)
y2 = np.array(ySam)
comboY = np.append(y1, y2)

x1 = np.array(xRef)
x2 = np.array(xSam)
comboX = np.append(x1, x2)

if len(y1) != len(x1):
    raise(Exception('Unequal x1 and y1 data length'))
if len(y2) != len(x2):
    raise(Exception('Unequal x2 and y2 data length'))

# some initial parameter values
initialParameters = np.array([1.0, 1.0, 1.0, 1.0, 0.0])

# curve fit the combined data to the combined function
fittedParameters, pcov = curve_fit(combinedFunction, comboX, comboY, initialParameters)

# values for display of fitted function
r0, s0, a1, a2, a3 = fittedParameters

# xFitData = np.arange(-400,1000)

y_fit_1 = function1(xFitData, r0, s0, a1, a2, a3)  # first data set, first equation
y_fit_2 = function2(xFitData, r0, s0, a1, a2, a3)  # second data set, second equation

plt.plot(xFitData, y_fit_1, color="#b51d14")
plt.plot(xFitData, y_fit_2, color="#4053d3")

# plt.show()

# Calculate the errors
# Reference
x = x1
y = y1
yfit = function1(x, r0, s0, a1, a2, a3)
diff = y-yfit
sd1 = np.std(diff) / np.sqrt(len(diff))
# print(sd)
# plt.scatter(x,diff,color='#b51d14',label='reference')
# Sample
x = x2
y = y2
yfit = function2(x, r0, s0, a1, a2, a3)
diff = y-yfit
sd2 = np.std(diff) / np.sqrt(len(diff))
# print(sd)
# plt.scatter(x,diff,color='#4053d3',label='sample')


# plt.legend()
# plt.show()

Dp17ORS = 1000 * np.log(d17ORS / 1000 + 1) - 0.528 * 1000 * np.log(d18ORS / 1000 + 1)

# Now perform the sample standard bracketing ###################################


cy = 1
while cy <= df['Cycle'].max():
    x = df.loc[df['Cycle'] == cy]["Time(rel)"].mean()
    y = df.loc[df['Cycle'] == cy]["Dp17O"].mean() + Dp17ORS * 1000
    # yerror = sem( df.loc[df['Cycle'] == cy]["Dp17O"] )
    # if (cy % 2) == 0:
    #     # even -> sample
    #     color = 'blue',
    # else:
    #     color = 'red'
    plt.scatter(x, y, s=20, c="#ddb310", label=None)
    # plt.errorbar(
    #         x, y,
    #         xerr = None,
    #         yerr = None,
    #         color = color
    #         )
    cy = cy + 1

tmp = []
bracketingResults = []

cy = 2
while cy < df['Cycle'].max():
    if (cy % 2) == 0:
        x1 = df.loc[df['Cycle'] == cy - 1]["Time(rel)"].mean()
        # For Δ'17O
        y1 = df.loc[df['Cycle'] == cy - 1]["Dp17O"].mean() + Dp17ORS * 1000
        y1error = sem(df.loc[df['Cycle'] == cy-1]["Dp17O"])
        x2 = df.loc[df['Cycle'] == cy + 1]["Time(rel)"].mean()
        y2 = df.loc[df['Cycle'] == cy + 1]["Dp17O"].mean() + Dp17ORS * 1000
        y2error = sem(df.loc[df['Cycle'] == cy + 1]["Dp17O"])
        plt.plot([x1, x2], [y1, y2], color='#ddb310')
        # For the interpolation
        m = (y2 - y1) / (x2 - x1)
        b = y1 - m * x1
        xs = df.loc[df['Cycle'] == cy]["Time(rel)"].mean()
        ys = df.loc[df['Cycle'] == cy]["Dp17O"].mean() + Dp17ORS * 1000
        ysRef = m * xs + b
        tmp.append(ys - ysRef)
        bracketingResults.append(ys - ysRef)
        plt.plot(
            [xs, xs], [ys, ysRef],
            color="#ddb310",
            linewidth=1
        )
    cy = cy + 1

# Export bracketing data to file
dfBracketingResults = pd.DataFrame(bracketingResults)
dfBracketingResults.to_excel(excel_writer=folder + "bracketingResults.xlsx")

y = m * x + b

m = (y2 - y1) / (x2 - x1)
b = y1 - m * x1

plt.title(samID + "\n$\delta{}^{17}$O$_\mathrm{raw}$: " + str(d17OSS) + "‰, $\delta{}^{18}$O$_\mathrm{raw}$: " + str(d18OSS) + "‰, $\Delta{}^{\prime 17}$O$_\mathrm{0.528,\,raw}$ " + str(Dp17OSS) + " ± " + str(round(np.sqrt(sd1**2 + sd2**2), 1)) + " ppm\nReference gas: " + str(d17ORS) + "‰, " + str(d18ORS) + "‰, Polynomial: " + str(polynomial) + "\n Sample-Reference-Bracketing: " + str(round(np.mean(tmp) + Dp17ORS * 1000, 1)) + " ± " + str(round(sem(tmp), 1)) + " ppm")

plt.ylabel("$\Delta^{\prime 17}$O (ppm)")
plt.xlabel("Time (s)")

plt.legend()

plt.tight_layout()
plt.savefig(folder + "FitPlot.svg")
plt.savefig(folder + "FitPlot.png", dpi=300)

# Print out the folder name
if polynomial != '100':
    print(sys.argv[1], d17OSS, d18OSS, Dp17OSS, round(np.sqrt(sd1**2 + sd2**2), 1), d17ORS, d18ORS, polynomial)
else:
    print(sys.argv[1], d17OSS, d18OSS, round(np.mean(tmp) + Dp17ORS * 1000, 1), round(sem(tmp), 1), d17ORS, d18ORS, polynomial)
