# this script plots the TILDAS data and calculates the isotope ratios

# the script has to start with this, do not move these lines
import os
os.environ['MPLCONFIGDIR'] = "/var/www/html/Python"
os.chdir(os.path.dirname(os.path.realpath(__file__)))

# import modules
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

import sys
from os.path import exists
from scipy.stats import sem
from scipy import stats
from scipy.optimize import curve_fit
from datetime import datetime


import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')


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
measurement_date = datetime.strptime(samID[0:6], '%y%m%d')

strFiles = []
for file in os.listdir(folder):
    if file.endswith(".str"):
        strFiles.append(file)
strFiles.sort()

# Pattern for the measurement, default is Ref Sam Ref Sam […] Ref
if "air" in samID.lower():
    pattern = ["Dummy", "Dummy", "Dummy", "Ref", "Sam", "Ref", "Sam", "Ref", "Sam", "Ref", "Sam", "Ref", "Sam", "Ref", "Sam", "Ref", "Sam", "Ref", "Sam", "Ref", "Sam", "Ref", "Sam", "Ref", "Sam", "Ref", "Sam", "Ref", "Sam", "Ref", "Sam", "Ref", "Sam", "Ref", "Sam", "Ref", "Sam", "Ref", "Sam", "Ref", "Sam", "Ref", "Sam", "Ref","Sam", "Ref", "Sam", "Ref", "Sam", "Ref"]
else:
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
height = 18
plt.rcParams["figure.figsize"] = (width, height)
plt.rcParams.update({'font.size': 6})
plt.rcParams["legend.loc"] = "upper left"
#                                                      blue     yellow      red        grey    green
mpl.rcParams['axes.prop_cycle'] = mpl.cycler(color=["#4053d3", "#ddb310", "#b51d14", "#cacaca", "#00b25d"])

df = dfAll
# Now select data using the z-score (3sigma criterion)
nOutliers = df.loc[df['z_score'].abs() > 3].shape[0]
# df = df.loc[df['Cycle'] < 14] # filter for cycles
df = df.loc[df['z_score'].abs() <= 3]

# Get data from the logfile (temperature, humidity, bellow pressures)
if(exists(folder + "logFile.csv")):
    dfLogFile = pd.read_csv(folder + "logFile.csv")
    # exclude lines that have no data in the 6th column, this is backwards compatible
    if ('percentageX' in dfLogFile.columns):
        dfLogFile = dfLogFile[dfLogFile.percentageX.notnull()]

seconds = df['Time(rel)'].iat[-1]
seconds = seconds % (24 * 3600)
hour = seconds // 3600
seconds %= 3600
minutes = seconds // 60
seconds %= 60
measurement_duration = str("%d:%02d:%02d" % (hour, minutes, seconds))

if(exists(folder + "logFile.csv")):
    if(measurement_date > datetime(2022, 12, 5) ):
        x_logFile = dfLogFile['Time(abs)'] + 3600 - df['Time(abs)'][0]
    else:
        x_logFile = dfLogFile['Time(abs)'] + 7200 - df['Time(abs)'][0]

sample_col = "C0"
reference_col = "C2"
bracketing_col = "C1"
dummy_col = "C3"
data_colors = {'Dummy':'C3', 'Sam':'C0', 'Ref':'C2'}
cmap = LinearSegmentedColormap.from_list('custom_colors', ['C3','C2','C0'])
data_names = ['Dummy', 'Reference', 'Sample']

# Now plot measurement
pltsize = 10

# Subplot A: d18O vs time
ax1 = plt.subplot(pltsize, 1, 1)
x = df['Time(rel)']
y = df['d18O']
plt.text(0.99 , 0.98, 'A', size=14, horizontalalignment='right', verticalalignment='top', transform=ax1.transAxes)
scat = plt.scatter(x, y, marker =".", c = df.Type.astype('category').cat.codes, cmap=cmap)
plt.legend(handles=scat.legend_elements()[0], labels=data_names, markerscale = 0.5)
plt.ylabel("$\delta^{18}$O (‰, raw)")
plt.title(samID + "\nmeasurement duration: " + measurement_duration)

# Subplot B: D17O vs time
ax7 = plt.subplot(pltsize, 1, 2, sharex=ax1)
x = df['Time(rel)']
y = df['Dp17O']
plt.text(0.99, 0.98, 'B', size=14, horizontalalignment='right', verticalalignment='top', transform=ax7.transAxes)
plt.scatter(x, y, marker=".", color = df['Type'].map(data_colors))
plt.ylabel("$\Delta^{17}$O (ppm, raw)")

# Subplot C: CO2 in cell vs time
ax3 = plt.subplot(pltsize, 1, 3, sharex=ax1)
x = df['Time(rel)']
y = df['I626'] / 1000
plt.scatter(x, y, marker=".", color = df['Type'].map(data_colors))
smpCO2 = df.loc[(df["Cycle"] > 0) & (df["Cycle"] % 2 == 0) ,['I626']].mean()/1000
smpCO2 = float(np.round(smpCO2, 1))
smpLab = str(smpCO2) + " ppm"
refCO2 = df.loc[(df["Cycle"] > 0) & (df["Cycle"] % 2 != 0) ,['I626']].mean()/1000
refCO2 = float(np.round(refCO2, 1))
refLab = str(refCO2) + " ppm"
plt.text(0.06 / width, 0.06 / height * 11, smpLab, size=8, color="C0", horizontalalignment='left', verticalalignment='bottom', transform=ax3.transAxes, bbox=dict(fc='white', ec="none", pad=2, alpha=0.5))
plt.text(0.06 / width, 0.17-0.06 / height * 11, refLab, size=8, color="C2", horizontalalignment='left', verticalalignment='bottom', transform=ax3.transAxes, bbox=dict(fc='white', ec="none", pad=2, alpha=0.5))
plt.text(0.99, 0.98, 'C', size=14, horizontalalignment='right', verticalalignment='top', transform=ax3.transAxes)
plt.ylabel("CO$_2$ (ppm, cell)")

# Subplot D: Cell pressure vs time
ax4 = plt.subplot(pltsize, 1, 4, sharex=ax1)
x = df['Time(rel)']
y = df[' Praw']
plt.scatter(x, y, marker=".",color = df['Type'].map(data_colors))
mean = df.loc[(df["Cycle"] > 0) ,[' Praw']].mean()
mean = float(np.round(mean, 3))
label = str(mean) + " Torr"
plt.text(0.06 / width, 0.06 / height * 11, label, size=8, color="black", horizontalalignment='left', verticalalignment='bottom', transform=ax4.transAxes, bbox=dict(fc='white', ec="none", pad=2, alpha=0.5))
plt.text(0.99, 0.98, 'D', size=14, horizontalalignment='right', verticalalignment='top', transform=ax4.transAxes)
plt.ylabel("Pressure (Torr, cell)")

# Subplot E: Cell temperature
ax6 = plt.subplot(pltsize, 1, 5, sharex=ax1)
x = df['Time(rel)']
y = df[' Traw'] - 273.15
plt.scatter(x, y, marker=".",color = df['Type'].map(data_colors))
plt.ylabel("Temperature (°C, cell)")
minty = np.round(np.mean(y), 3)
sdt = np.round(np.std(y), 3)
la = str(minty) + "±" + str(sdt) + " °C"
plt.text(0.06 / width, 0.06 / height * 11, la, size=8, color="black", horizontalalignment='left', verticalalignment='bottom', transform=ax6.transAxes, bbox=dict(fc='white', ec="none", pad=2,alpha=0.5))
plt.text(0.99, 0.98, 'E', size=14, horizontalalignment='right', verticalalignment='top', transform=ax6.transAxes)

# Subplot F: Coolant temperature and room temperature
ax5 = plt.subplot(pltsize, 1, 6, sharex=ax1)
x = df['Time(rel)']
y = df[' Tref'] - 273.15
plt.scatter(x, y, marker=".",color = df['Type'].map(data_colors))
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
    plt.text(1 - 0.06 / width, 0.06 / height * 11, la_2, size=8, color="C1", horizontalalignment='right', verticalalignment='bottom', transform=ax5.transAxes, bbox=dict(fc='white', ec="none", pad=2,alpha=0.5))
plt.text(0.06 / width, 0.06 / height * 11, la, size=8, color="black", horizontalalignment='left', verticalalignment='bottom', transform=ax5.transAxes, bbox=dict(fc='white', ec="none", pad=2,alpha=0.5))
plt.text(0.99, 0.98, 'F', size=14, horizontalalignment='right', verticalalignment='top', transform=ax5.transAxes)

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
        plt.text(0.06 / width, 0.17 - 0.06 / height * 8, laSP, size=8, color="C2", horizontalalignment='left', verticalalignment='bottom', transform=ax11.transAxes, bbox=dict(fc='white', ec="none", pad=2,alpha=0.5))
    plt.text(0.06 / width, 0.06 / height * 11, laby, size=8, color="C0", horizontalalignment='left', verticalalignment='bottom', transform=ax11.transAxes, bbox=dict(fc='white', ec="none", pad=2,alpha=0.5))
plt.text(0.99, 0.98, 'G', size=14, horizontalalignment='right', verticalalignment='top', transform=ax11.transAxes)

# Subplot J: Room humidity vs time
# ax9 = plt.subplot(pltsize, 1, 9, sharex=ax1)
# if 'RoomH' in dfLogFile.columns:
#     y = dfLogFile['RoomH']
#     plt.plot(x, y)
# plt.text(0.96, 1 - 0.06 / height * 8, 'J', size=14, horizontalalignment='left', verticalalignment='top', transform=ax9.transAxes)
# plt.ylabel("Humidity (%, room)")

# Subplot K: Room pressure vs time
# ax10 = plt.subplot(pltsize, 1, 10, sharex=ax1)
# if 'RoomP' in dfLogFile.columns:
#     y = dfLogFile['RoomP']
#     plt.plot(x, y)
# plt.text(0.96, 1 - 0.06 / height * 8, 'K', size=14, horizontalalignment='left', verticalalignment='top', transform=ax10.transAxes)
# plt.ylabel("Pressure (hPa, room)")

# Subplot H: Box humidity and room humidity
# ax12 = plt.subplot(pltsize, 1, 8, sharex=ax1)
# if (exists(folder + "logFile.csv")) and ('Humidity(room)' in dfLogFile.columns):
#     x = x_logFile
#     y = dfLogFile['Humidity(room)']
#     plt.plot(x, y)
#     plt.ylabel("Humidity (%, box)")
#     meany = np.round(np.mean(y), 2)
#     stdy = np.round(np.max(y)-np.min(y), 2)
#     laby = str(meany) + "%, " + "∆RH: " + str(stdy) + "%"
#     if 'RoomH' in dfLogFile.columns:
#         x = x_logFile
#         y = dfLogFile['RoomH']
#         ax12b = ax12.twinx()
#         ax12b.spines['right'].set_color('C1')
#         plt.plot(x, y, color="C1")
#         plt.ylabel("Humidity (%, room)")
#         meany_2 = np.round(np.mean(y), 2)
#         stdy_2 = np.round(np.max(y)-np.min(y), 2)
#         laby_2 = str(meany_2) + "%, " + "∆RH: " + str(stdy_2) + "%"
#         plt.text(1 - 0.06 / width, 0.06 / height * 11, laby_2, size=8, color="C1", horizontalalignment='right', verticalalignment='bottom', transform=ax12.transAxes, bbox=dict(fc='white', ec="none", pad=2))
#     plt.text(0.06 / width, 0.06 / height * 11, laby, size=8, color="C0", horizontalalignment='left', verticalalignment='bottom', transform=ax12.transAxes, bbox=dict(fc='white', ec="none", pad=2))
# plt.text(0.96, 1 - 0.06 / height * 8, 'H', size=14, horizontalalignment='left', verticalalignment='top', transform=ax12.transAxes)

# Subplot H: X (reference) bellow expansion and pressure
ax13 = plt.subplot(pltsize, 1, 8, sharex=ax1)
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
plt.text(0.99, 0.98, 'H', size=14, horizontalalignment='right', verticalalignment='top', transform=ax13.transAxes)

# Subplot J: Y (sample) bellow expansion and pressure
ax14 = plt.subplot(pltsize, 1, 9, sharex=ax1)
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
plt.text(0.99, 0.98, 'I', size=14, horizontalalignment='right', verticalalignment='top', transform=ax14.transAxes)

# Subplot K: Z bellow
ax15 = plt.subplot(pltsize, 1, 10, sharex=ax1)
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
plt.text(0.99, 0.98, 'J', size=14, horizontalalignment='right', verticalalignment='top', transform=ax15.transAxes)

ax15.set_xlabel("Relative time (s)")
plt.tight_layout()
plt.savefig(folder + "rawData.svg")
plt.savefig(folder + "rawData.png", dpi=300)


############################## Fit data ##############################
######################################################################

# Fit the ref and sam data with the same a1, a2, a3 and only different intercepts r0, s0
# Modified after https://stackoverflow.com/questions/51482486/python-global-fitting-for-data-sets-of-different-sizes

# Plot properties
height = 11.69
width = 6
plt.rcParams["figure.figsize"] = (width, height)
plt.rcParams["legend.loc"] = "upper left"
plt.figure(0)
plt.rcParams.update({'font.size': 6})

# Reference gas composition: D'17O = -100 ppm
d18ORS = 28.048
d17ORS = 14.611 + 0.010  # D'17O = -90 ppm
Dp17ORS = 1000 * np.log(d17ORS / 1000 + 1) - 0.528 * 1000 * np.log(d18ORS / 1000 + 1)

dfRef = df.loc[df['Type'] == "Ref"]
dfSam = df.loc[df['Type'] == "Sam"]
dfDummy = df.loc[df['Type'] == "Dummy"]

########## Fit für d17O ##########
ax1 = plt.subplot(3, 1, 1)
plt.text(0.99, 0.99, 'A', size=14, horizontalalignment='right', verticalalignment='top', transform=ax1.transAxes)

xDummy = df.loc[df['Type'] == "Dummy"]["Time(rel)"]
d17ODummyRaw = ((dfDummy['I627']/dfDummy['I626'])/np.mean(df['I627']/df['I626']) - 1) * 1000
d18ODummyRaw = ((dfDummy['I628']/dfDummy['I626'])/np.mean(df['I628']/df['I626']) - 1) * 1000
yDummy = d17ODummyRaw
plt.scatter(xDummy, yDummy, color=dummy_col, marker=".", label="Dummy", zorder = 4)

xRef = df.loc[df['Type'] == "Ref"]["Time(rel)"]
d17ORefRaw = ((dfRef['I627']/dfRef['I626'])/np.mean(df['I627']/df['I626']) - 1) * 1000
d18ORefRaw = ((dfRef['I628']/dfRef['I626'])/np.mean(df['I628']/df['I626']) - 1) * 1000
yRef = d17ORefRaw
plt.scatter(xRef, yRef, color=reference_col, marker=".", label="Reference", zorder = 3)

xSam = dfSam['Time(rel)']
d17O = ((dfSam['I627']/dfSam['I626'])/np.mean(df['I627']/df['I626']) - 1) * 1000
d18O = ((dfSam['I628']/dfSam['I626'])/np.mean(df['I628']/df['I626']) - 1) * 1000
ySam = d17O
plt.scatter(xSam, ySam, color=sample_col, marker=".", label="Sample", zorder = 2)

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
        return r0 + a1 * data + a2 * data * data # second order polynomial data calculated for bracketing resutls too
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
        return s0 + a1 * data + a2 * data * data # second order polynomial data calculated for bracketing resutls too
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

if polynomial != "100":
    plt.plot(xFitData, y_fit_1, color=reference_col, zorder = -1)
    plt.plot(xFitData, y_fit_2, color=sample_col, zorder = -1)

# Sample-standard bracketing for d17O
bracketingResults = []
bracketingCycles = []

if "air" in samID.lower():
    dfm = df.loc[df['Cycle'] > 2] # starting from cycle 3 (0,1,2 are dummies)
    cy = 4 # the number of the first proper reference cycle
else:
    dfm = df.loc[df['Cycle'] > 0] # starting from cycle 1 (0 is a dummy)
    cy = 2 # the number of the first proper reference cycle

dfm = dfm.groupby(['Cycle'])['Time(rel)',"d17O","d18O","Dp17O"].mean()
plt.scatter(dfm.iloc[:,0], dfm.iloc[:,1], marker = "*", s = 20, c=bracketing_col, label="Cycle avg", zorder = 5)

while cy < df['Cycle'].max():
    if (cy % 2) == 0:
        x1 = df.loc[df['Cycle'] == cy - 1]["Time(rel)"].mean()

        # For d17O
        y1 = df.loc[df['Cycle'] == cy - 1]["d17O"].mean()
        y1error = sem(df.loc[df['Cycle'] == cy-1]["d17O"])
        x2 = df.loc[df['Cycle'] == cy + 1]["Time(rel)"].mean()
        y2 = df.loc[df['Cycle'] == cy + 1]["d17O"].mean()
        y2error = sem(df.loc[df['Cycle'] == cy + 1]["d17O"])

        # For the interpolation
        m = (y2 - y1) / (x2 - x1)
        b = y1 - m * x1
        xs = df.loc[df['Cycle'] == cy]["Time(rel)"].mean()
        ys = df.loc[df['Cycle'] == cy]["d17O"].mean()
        ysRef = m * xs + b
        
        bracketingAlpha17 = (ys + 1000) / (ysRef + 1000)
        bracketingd17O = (d17ORS + 1000 ) * bracketingAlpha17 - 1000
        bracketingResults.append(bracketingd17O)
        bracketingCycles.append(cy)
        
        if polynomial == "100":
            plt.plot([x1, x2], [y1, y2], linestyle='dotted', color=bracketing_col, linewidth=1.2, dash_capstyle = "round", zorder = 5)
            plt.plot([xs, xs], [ys, ysRef], color=bracketing_col, linewidth=1.2, zorder = 5)
    cy = cy + 1

# We create the dfBracketingResults dataframe here
dfBracketingResults = pd.DataFrame(bracketingCycles, columns = ["Cycle"])
dfBracketingResults['d17O'] = bracketingResults

plt.ylabel("$\delta^{17}$O (‰)")

# plt.title("$1000\,\ln{ α_\mathrm{Sam-Ref}^{17} }$ = " + str(round(1000 * np.log(α17SR), 3)))

plt.legend()



########## Fit für d18O ##########
ax1 = plt.subplot(3, 1, 2)
plt.text(0.99, 0.99, 'B', size=14, horizontalalignment='right', verticalalignment='top', transform=ax1.transAxes)

xDummy = df.loc[df['Type'] == "Dummy"]["Time(rel)"]
d17ODummyRaw = ((dfDummy['I627']/dfDummy['I626'])/np.mean(df['I627']/df['I626']) - 1) * 1000
d18ODummyRaw = ((dfDummy['I628']/dfDummy['I626'])/np.mean(df['I628']/df['I626']) - 1) * 1000
yDummy = d18ODummyRaw
plt.scatter(xDummy, yDummy, color=dummy_col, marker=".", label="Dummy", zorder = 4)

xRef = df.loc[df['Type'] == "Ref"]["Time(rel)"]
d17ORefRaw = ((dfRef['I627']/dfRef['I626'])/np.mean(df['I627']/df['I626']) - 1) * 1000
d18ORefRaw = ((dfRef['I628']/dfRef['I626'])/np.mean(df['I628']/df['I626']) - 1) * 1000
yRef = d18ORefRaw
plt.scatter(xRef, yRef, color=reference_col, marker=".", label="Reference", zorder = 3)

xSam = dfSam['Time(rel)']
d17O = ((dfSam['I627']/dfSam['I626'])/np.mean(df['I627']/df['I626']) - 1) * 1000
d18O = ((dfSam['I628']/dfSam['I626'])/np.mean(df['I628']/df['I626']) - 1) * 1000
ySam = d18O
plt.scatter(xSam, ySam, color=sample_col, marker=".", label="Sample", zorder = 2)

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

# some initial parameter values
initialParameters = np.array([1.0, 1.0, 1.0, 1.0, 1.0])

# curve fit the combined data to the combined function
fittedParameters, pcov = curve_fit(combinedFunction, comboX, comboY, initialParameters)

# values for display of fitted function
r0, s0, a1, a2, a3 = fittedParameters

y_fit_1 = function1(xFitData, r0, s0, a1, a2, a3)  # first data set, first equation
y_fit_2 = function2(xFitData, r0, s0, a1, a2, a3)  # second data set, second equation

α18SR = (y_fit_2[0] + 1000) / (y_fit_1[0] + 1000)

if polynomial != "100":
    plt.plot(xFitData, y_fit_1, color=reference_col, zorder=-1)
    plt.plot(xFitData, y_fit_2, color=sample_col, zorder=-1)

# Sample-standard bracketing for d18O
bracketingResults = []

plt.scatter(dfm.iloc[:,0], dfm.iloc[:,2], marker = "*", s = 20, c=bracketing_col, label="Cycle avg", zorder = 5)

if "air" in samID.lower():
    cy = 4
else:
    cy = 2

while cy < df['Cycle'].max():
    if (cy % 2) == 0:

        x1 = df.loc[df['Cycle'] == cy - 1]["Time(rel)"].mean()

        y1 = df.loc[df['Cycle'] == cy - 1]["d18O"].mean()
        y1error = sem(df.loc[df['Cycle'] == cy-1]["d18O"])
        x2 = df.loc[df['Cycle'] == cy + 1]["Time(rel)"].mean()
        y2 = df.loc[df['Cycle'] == cy + 1]["d18O"].mean()
        y2error = sem(df.loc[df['Cycle'] == cy + 1]["d18O"])

        # For the interpolation
        m = (y2 - y1) / (x2 - x1)
        b = y1 - m * x1
        xs = df.loc[df['Cycle'] == cy]["Time(rel)"].mean()
        ys = df.loc[df['Cycle'] == cy]["d18O"].mean()
        ysRef = m * xs + b
        
        bracketingAlpha18 = (ys + 1000) / (ysRef + 1000)
        bracketingd18O = (d18ORS + 1000 ) * bracketingAlpha18 - 1000
        bracketingResults.append(bracketingd18O)

        if polynomial == "100":
            plt.plot([x1, x2], [y1, y2], linestyle='dotted', color=bracketing_col, linewidth=1.2, dash_capstyle = "round", zorder = 5)
            plt.plot([xs, xs], [ys, ysRef],color=bracketing_col, linewidth=1.2, zorder = 5)
        # plt.scatter(xs, ysRef, color=reference_col, marker = (5,1), zorder = 5)
    cy = cy + 1

dfBracketingResults['d18O'] = bracketingResults

plt.ylabel("$\delta^{18}$O (‰)")

# plt.title("$1000\,\ln{ α_\mathrm{Sam-Ref}^{18} }$ = " + str(round(1000 * np.log(α18SR), 3)))

plt.legend()

# Now we have

d17OSR = (α17SR - 1) * 1000
d18OSR = (α18SR - 1) * 1000

d17OSS = round(d17OSR + d17ORS + 1/1000 * d17OSR * d17ORS, 3)
d18OSS = round(d18OSR + d18ORS + 1/1000 * d18OSR * d18ORS, 3)
Dp17OSS = round((1000 * np.log(d17OSS / 1000 + 1) - 0.528 * 1000 * np.log(d18OSS / 1000 + 1)) * 1000, 1)


##### Fit für D'17O ####
ax1 = plt.subplot(3, 1, 3)
plt.text(0.99, 0.99, 'C', size=14, horizontalalignment='right', verticalalignment='top', transform=ax1.transAxes)

xDummy = df.loc[df['Type'] == "Dummy"]["Time(rel)"]
d17ODummyRaw = ((dfDummy['I627']/dfDummy['I626'])/np.mean(df['I627']/df['I626']) - 1) * 1000
d18ODummyRaw = ((dfDummy['I628']/dfDummy['I626'])/np.mean(df['I628']/df['I626']) - 1) * 1000
yDummy = (1000 * np.log(d17ODummyRaw/1000+1) - 0.528 * 1000 * np.log(d18ODummyRaw/1000+1)) * 1000
plt.scatter(xDummy, yDummy, color=dummy_col, marker=".", label="Dummy")

xRef = dfRef['Time(rel)']
d17O = ((dfRef['I627']/dfRef['I626'])/np.mean(df['I627']/df['I626']) - 1) * 1000
d17O = d17O + d17ORS + 1/1000 * d17O * d17ORS
d18O = ((dfRef['I628']/dfRef['I626'])/np.mean(df['I628']/df['I626']) - 1) * 1000
d18O = d18O + d18ORS + 1/1000 * d18O * d18ORS
yRef = (1000 * np.log(d17O/1000+1) - 0.528 * 1000 * np.log(d18O/1000+1)) * 1000
plt.scatter(xRef, yRef, color=reference_col, marker=".", label="Reference")

xSam = dfSam['Time(rel)']
d17O = ((dfSam['I627']/dfSam['I626'])/np.mean(df['I627']/df['I626']) - 1) * 1000
d17O = d17O + d17ORS + 1/1000 * d17O * d17ORS
d18O = ((dfSam['I628']/dfSam['I626'])/np.mean(df['I628']/df['I626']) - 1) * 1000
d18O = d18O + d18ORS + 1/1000 * d18O * d18ORS
ySam = (1000 * np.log(d17O/1000+1) - 0.528 * 1000 * np.log(d18O/1000+1)) * 1000
plt.scatter(xSam, ySam, color=sample_col, marker=".", label="Sample")

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

y_fit_1 = function1(xFitData, r0, s0, a1, a2, a3)  # first data set, first equation
y_fit_2 = function2(xFitData, r0, s0, a1, a2, a3)  # second data set, second equation

if polynomial != "100":
    plt.plot(xFitData, y_fit_1, color=reference_col, zorder = -1)
    plt.plot(xFitData, y_fit_2, color=sample_col, zorder = -1)

# Calculate the errors
# Reference
x = x1
y = y1
yfit = function1(x, r0, s0, a1, a2, a3)
diff = y-yfit
sd1 = np.std(diff) / np.sqrt(len(diff))
# Sample
x = x2
y = y2
yfit = function2(x, r0, s0, a1, a2, a3)
diff = y-yfit
sd2 = np.std(diff) / np.sqrt(len(diff))


# Sample-standard bracketing
bracketingResults = []
bracketingTime = []
bracketingYs = []

plt.scatter(dfm.iloc[:,0], dfm.iloc[:,3]+ Dp17ORS * 1000, marker = "*",s = 20, c=bracketing_col, label="Cycle avg", zorder = 5)

if "air" in samID.lower():
    cy = 4
else:
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

        # For the interpolation
        m = (y2 - y1) / (x2 - x1)
        b = y1 - m * x1
        xs = df.loc[df['Cycle'] == cy]["Time(rel)"].mean()
        ys = df.loc[df['Cycle'] == cy]["Dp17O"].mean() + Dp17ORS * 1000
        ysRef = m * xs + b
        bracketingCycles.append(cy)
        bracketingResults.append(ys - ysRef + Dp17ORS * 1000)
        bracketingTime.append(xs)
        bracketingYs.append(ys)

        if polynomial == "100":
            plt.plot([x1, x2], [y1, y2], linestyle='dotted', color=bracketing_col, linewidth=1.2, dash_capstyle = "round", zorder = 5)
            plt.plot([xs, xs], [ys, ysRef], color=bracketing_col, linewidth = 1.2, zorder = 5)
        # plt.scatter(xs, ysRef, color=reference_col, marker = (5,1), zorder = 5)
    cy = cy + 1

dfBracketingResults['D17O'] = bracketingResults
dfBracketingResults['z_score'] = stats.zscore(dfBracketingResults['D17O'])

# Here we calculate a modified z-score based on Iglewicz and Hoaglin 1993
median = np.median(dfBracketingResults['D17O'])
diff = (dfBracketingResults['D17O'] - median)
mad = np.median(np.absolute(diff))
modified_z_score = 0.6745 * diff / mad
dfBracketingResults['IH_score'] = modified_z_score

outlierPlot = pd.DataFrame(bracketingTime, columns = ["Time"])
outlierPlot['D17O'] = bracketingYs
outlierPlot['IH_score'] = modified_z_score
nIHOutliers = outlierPlot.loc[outlierPlot['IH_score'].abs() >= 5].shape[0]
outlierPlot = outlierPlot.loc[outlierPlot['IH_score'].abs() >= 5]

OutLab = "No outliers"

if nIHOutliers > 0 and polynomial == "100":
    OutLab = "Outlier (N: " + str(nIHOutliers) +")"
    plt.scatter(outlierPlot['Time'],  outlierPlot['D17O'], marker = "*", s = 20, c="C4", label=OutLab, zorder = 6)
    if nIHOutliers == 1 :
        OutLab = str(nIHOutliers) + " outlier"
    else:
        OutLab = str(nIHOutliers) + " outliers"

# Export bracketing data to a file, including outliers
dfBracketingResults.to_excel(excel_writer=folder + "bracketingResults.xlsx", header = True, index = False)

# Here are the bracketing results, excluding outliers
# Comment out this line to re-evaluate data including outliers
dfBracketingResults = dfBracketingResults.loc[dfBracketingResults['IH_score'].abs() < 5]

d18O_SRB = round(np.mean(dfBracketingResults['d18O']),3)
d17O_SRB = round(np.mean(dfBracketingResults['d17O']),3)
D17Op_SRB = round(np.mean(dfBracketingResults['D17O']),1)
D17Op_SRB_error = round(sem(dfBracketingResults['D17O']),1)


# Write evaluated data into the figure title

first_line = samID # + "  " + measurement_date.strftime("%m/%d/%Y")
if polynomial == "100":
    second_line = str("\n" + "Results from bracketing: " + "$\delta{}^{17}$O$_\mathrm{raw}$: "+ str(d17O_SRB) + "‰, $\delta{}^{18}$O$_\mathrm{raw}$: " + str(d18O_SRB) + "‰, $\Delta{}^{\prime 17}$O$_\mathrm{raw}$: " + str(D17Op_SRB) + " ± " + str(D17Op_SRB_error) + " ppm, " + OutLab)
else:
    second_line = str("\n" + "Results from " +polynomial+ "nd order polynomial fit: " + "$\delta{}^{17}$O$_\mathrm{raw}$: "+ str(d17OSS) + "‰, $\delta{}^{18}$O$_\mathrm{raw}$: " + str(d18OSS) + "‰, $\Delta{}^{\prime 17}$O$_\mathrm{raw}$: " + str(Dp17OSS) + " ± " + str(round(np.sqrt(sd1**2 + sd2**2), 1)) +" ppm")
third_line = str("\n(Reference gas: " +"$\delta{}^{17}$O: "+ str(d17ORS) + "‰, " + "$\delta{}^{18}$O: " + str(d18ORS) + "‰, " + "$\Delta{}^{\prime 17}$O: " + str(round(Dp17ORS*1000,1)) + " ppm)")
plt.title(first_line + second_line + third_line)

plt.ylabel("$\Delta^{\prime 17}$O (ppm)")
plt.xlabel("Relative time (s)")

plt.legend()

plt.tight_layout()
plt.savefig(str(folder + "FitPlot.svg"))
plt.savefig(str(folder +  "FitPlot.png"), dpi=300)


# Print out the values
# Hi Andreas, the reference and the sample pCO2 values are stored in the smpCO2 and refCO2 float variables, respectively.

if polynomial != '100':
    print(sys.argv[1], d17OSS, d18OSS, Dp17OSS, round(np.sqrt(sd1**2 + sd2**2), 1), d17ORS, d18ORS, polynomial)
else:
    print(sys.argv[1], d17O_SRB, d18O_SRB, D17Op_SRB, D17Op_SRB_error, d17ORS, d18ORS, polynomial)
