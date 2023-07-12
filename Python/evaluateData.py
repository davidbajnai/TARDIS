# This script plots the TILDAS data and calculates the isotope ratios

# Import libraries
import os
os.environ['MPLCONFIGDIR'] = "/var/www/html/Python"
os.chdir(os.path.dirname(os.path.realpath(__file__)))

import warnings
import numpy as np
import pandas as pd
from datetime import datetime
from scipy.optimize import curve_fit
from scipy import stats
from scipy.stats import sem
from os.path import exists
import sys
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.pyplot as plt
from scipy.stats import t
import matplotlib as mpl
warnings.filterwarnings('ignore')

#################################################################
####################### Define functions ########################
#################################################################

def prime(delta):
    return 1000 * np.log(delta/1000 + 1)


def unprime(deltaprime):
    return (np.exp(deltaprime/1000) - 1) * 1000


def Dp17O(d17O, d18O):
    return (prime(d17O) - 0.528 * prime(d18O)) * 1000  # Value in ppm


# These are the functions used for the "smooth fit" method
# Reference and sample data are fitted with the same a1, a2, a3 but different intercepts: r0, s0
# Modified after https://stackoverflow.com/questions/51482486/python-global-fitting-for-data-sets-of-different-sizes
def function1(data, r0, s0, a1, a2, a3):
    if polynomial == "3":
        return r0 + a1 * data + a2 * data * data + a3 * data * data * data
    if polynomial == "2":
        return r0 + a1 * data + a2 * data * data
    if polynomial == "1":
        return r0 + a1 * data
    if polynomial == "0":
        return r0


def function2(data, r0, s0, a1, a2, a3):
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


#################################################################
####################### Import TILDAS data ######################
#################################################################

# Import measurement info
samID = str(sys.argv[1])  # Something like 230118_084902_heavyVsRef
folder = "../Results/" + samID + "/"
polynomial = str(sys.argv[2])  # String

# Calculate the start time of the measurement.
# The TILDAS and the loglife use Mac time, which is the number of seconds since 1904-01-01
measurementStarted = int(datetime.strptime(samID[0:13], '%y%m%d_%H%M%S').timestamp()-datetime(1904, 1, 1).timestamp())

strFiles = []
for file in os.listdir(folder):
    if file.endswith(".str"):
        strFiles.append(file)
strFiles.sort()

# Pattern for the measurements
if "air" in samID.lower():
    # Air measurements start with two Ref dummy (cy 0 and 1) and a sample dummy (cy 2)
    pattern = ["Dummy", "Dummy", "Dummy",
               "Ref", "Sam", "Ref", "Sam", "Ref", "Sam", "Ref", "Sam", "Ref", "Sam", "Ref", "Sam", "Ref", "Sam", "Ref", "Sam", "Ref", "Sam", "Ref","Sam", "Ref"]
else:
    # Regular measurements start with a single Ref dummy (cy 0)
    pattern = ["Dummy",
               "Ref", "Sam", "Ref", "Sam", "Ref", "Sam", "Ref", "Sam", "Ref", "Sam", "Ref", "Sam", "Ref", "Sam", "Ref", "Sam", "Ref", "Sam", "Ref", "Sam", "Ref"]

# Read all data files and combine them into one dataframe
i = 0
for file in strFiles:
    baseName = file[:-4]

    # The .str files contain the isotopologue mixing ratios
    dfstr = pd.read_csv(folder + baseName + ".str", names=["Time(abs)", "I627", "I628", "I626", "CO2"], delimiter=" ", skiprows=1, index_col=False)
    
    # The .stc files contain the cell temperature, pressure, etc. data
    dfstc = pd.read_csv(folder + baseName + ".stc", delimiter=",", skiprows=1)
    
    # Combine data from the two files
    df = pd.concat([dfstr, dfstc], axis=1, join="inner")
    
    df['Time(rel)'] = df['Time(abs)'] - measurementStarted
    df['Type'] = pattern[i]
    df['Cycle'] = i
    df['d17O_cy'] = ((df['I627'] / df['I626']) / np.mean(df['I627'] / df['I626']) - 1) * 1000
    df['d18O_cy'] = ((df['I628'] / df['I626']) / np.mean(df['I628'] / df['I626']) - 1) * 1000
    df['Dp17O_cy'] = Dp17O(df['d17O_cy'], df['d18O_cy'])
    df['z_score'] = stats.zscore(df['Dp17O_cy'])
    if i == 0:
        dfAll = df
    else:
        dfAll = dfAll.append(df, ignore_index=True)
    i = i + 1
df = dfAll

# Calculate the isotope ratios normalized to all data avarege
df["d17O_raw"] = ((df['I627'] / df['I626']) / np.mean(df['I627'] / df['I626']) - 1) * 1000
df["d18O_raw"] = ((df['I628'] / df['I626']) / np.mean(df['I628'] / df['I626']) - 1) * 1000
df["Dp17O_raw"] = Dp17O(df["d17O_raw"], df["d18O_raw"])

# Compensate for summer time / winter time, if necessary
if (df["Time(rel)"].iat[0] > 3500):
    df["Time(rel)"] = df["Time(rel)"] - 3600

# Export all data into an Excel file
df.to_excel(folder + "allData.xlsx", index=False)

# Now filter data using the z-score (3-sigma criterion)
# The excel file includes all data, but only filtered data is used for the calculations and plots
df = df.loc[df['z_score'].abs() <= 3]

#################################################################
################### Read and reformat logfile ###################
#################################################################

# Necessary to maintain compatibility with the old logfiles

dfLogFile = pd.read_csv(folder + "logFile.csv")

# Reprocess old logfiles
if 'Time(rel)' not in dfLogFile.columns:

    # Remove any rows that are missing a value
    dfLogFile = dfLogFile.dropna(how='any')

    # Rename the columns
    new_columns = {
        "SampleName": "sampleName",
        "dateTime": "Time(abs)",
        "Temperature(room)": "boxTemperature",
        "TargetT(box)": "boxSetpoint",
        "Humidity(room)": "boxHumidity",
        "percentageX": "percentageX",
        "percentageY": "percentageY",
        "percentageZ": "percentageZ",
        "pressureX": "pressureX",
        "pressureY": "pressureY",
        "pressureA": "pressureA",
        "edwards": "vacuum",
        "fanSpeed": "fanSpeed",
        "RoomT": "roomTemperature",
        "RoomH": "roomHumidity",
        "RoomP": "roomPressure"
    }
    dfLogFile = dfLogFile.rename(columns=new_columns)

    # Assign placeholder values for any missing columns
    for col in ["sampleName", "Time(abs)", "boxTemperature", "boxSetpoint", "boxHumidity", "percentageX", "percentageY", "percentageZ", "pressureX", "pressureY", "pressureA", "vacuum", "fanSpeed", "roomTemperature", "roomHumidity"]:
        if col not in dfLogFile.columns:
            dfLogFile = dfLogFile.assign(**{col: np.nan})

    # Calculate the relative time used for plotting
    dfLogFile["Time(rel)"] = dfLogFile["Time(abs)"] - measurementStarted

    # Compensate for summer time / winter time, if necessary
    # A mismatch between TILDAS and logFile data can remain if the clocks were not synchronized
    if (dfLogFile["Time(rel)"].iat[0] < -3000):
        dfLogFile["Time(rel)"] = dfLogFile["Time(rel)"] + 3600

    # overwrite the original CSV file with the updated DataFrame
    dfLogFile.to_csv(folder + "logFile.csv", index=False)

# Calculate the measurement duration
seconds = dfLogFile["Time(rel)"].iat[-1]
measurement_duration = str("%d:%02d:%02d" % (seconds % (24 * 3600) // 3600, seconds % 3600 // 60, seconds % 3600 % 60))


#################################################################
###################### Figure 1 – Raw data ######################
#################################################################

# Plot parameters
width = 6
height = 18
pltsize = 10  # Number of subplots
plt.rcParams["figure.figsize"] = (width, height)
plt.rcParams.update({'font.size': 6})
plt.rcParams["legend.loc"] = "upper left"
# from http://tsitsul.in/blog/coloropt/                blue     yellow      red        grey    green
mpl.rcParams['axes.prop_cycle'] = mpl.cycler(color=["#4053d3", "#ddb310", "#b51d14", "#cacaca", "#00b25d"])

# Colors
colSample = "C0"
colReference = "C2"
colBracketing = "C1"
colDummy = "C3"
data_colors = {'Dummy': 'C3', 'Sam': 'C0', 'Ref': 'C2'}
cmap = LinearSegmentedColormap.from_list('custom_colors', ['C3', 'C2', 'C0'])
data_names = ['Dummy', 'Reference', 'Sample']

# Subplot A: d18O vs time
ax1 = plt.subplot(pltsize, 1, 1)
x = df["Time(rel)"]
y = df["d18O_raw"]
scat = plt.scatter(x, y, marker = ".", c = df.Type.astype('category').cat.codes, cmap=cmap)
plt.text(0.99 , 0.98, 'A', size = 14, ha = 'right', va = 'top', transform = ax1.transAxes)
plt.legend(handles=scat.legend_elements()[0], labels=data_names, markerscale = 0.5)
plt.ylabel("$\delta^{18}$O (‰, raw)")
plt.title(samID + "\nmeasurement duration: " + measurement_duration)

# Subplot B: D17O vs time
ax2 = plt.subplot(pltsize, 1, 2, sharex=ax1)
x = df['Time(rel)']
y = df['Dp17O_raw']
plt.scatter(x, y, marker=".", color = df['Type'].map(data_colors))
plt.ylabel("$\Delta^{\prime 17}$O (ppm, raw)")
plt.text(0.99, 0.98, 'B', size = 14, ha = 'right', va = 'top', transform=ax2.transAxes)

# Subplot C: CO2 in cell vs time
ax3 = plt.subplot(pltsize, 1, 3, sharex=ax1)
x = df['Time(rel)']
y = df['I626'] / 1000
plt.scatter(x, y, marker=".", color = df['Type'].map(data_colors))
if "air" in samID.lower():
    # Air measurements start with two Ref dummy (cy 0 and 1) and a sample dummy (cy 2)
    pCO2Sam = df.loc[(df["Cycle"] > 2) & (df["Cycle"] % 2 == 0) ,['I626']].mean()/1000
    pCO2Ref = df.loc[(df["Cycle"] > 1) & (df["Cycle"] % 2 != 0) ,['I626']].mean()/1000
else:
    # Regular measurements start with a single Ref dummy (cy 0)
    pCO2Sam = df.loc[(df["Cycle"] > 0) & (df["Cycle"] % 2 == 0) ,['I626']].mean()/1000
    pCO2Ref = df.loc[(df["Cycle"] > 0) & (df["Cycle"] % 2 != 0) ,['I626']].mean()/1000
pCO2Sam = float(np.round(pCO2Sam, 1))
smpLab = str(pCO2Sam) + " ppmv"
pCO2Ref = float(np.round(pCO2Ref, 1))
refLab = str(pCO2Ref) + " ppmv"
plt.text(0.01, 0.02, smpLab, size = 8, color = colSample, ha = 'left', va = 'bottom', transform = ax3.transAxes, bbox = dict(fc = 'white', ec = "none", pad = 1, alpha = 0.5))
plt.text(0.01, 0.12, refLab, size = 8, color = colReference, ha = 'left', va = 'bottom', transform = ax3.transAxes, bbox = dict(fc = 'white', ec = "none", pad = 1, alpha = 0.5))
plt.ylabel("$\mathit{p}$CO$_2$ (ppmv)")
plt.text(0.99, 0.98, 'C', size = 14, ha = 'right', va = 'top', transform = ax3.transAxes)

# Subplot D: Cell pressure vs time
ax4 = plt.subplot(pltsize, 1, 4, sharex = ax1)
x = df['Time(rel)']
y = df[' Praw']
plt.scatter(x, y, marker=".", color = df['Type'].map(data_colors))
PCellSam = df.loc[(df["Cycle"] > 0) & (df["Cycle"] % 2 == 0) ,[' Praw']].mean()
PCellSam = float(np.round(PCellSam, 3))
smpLab = str(PCellSam) + " Torr"
PCellRef = df.loc[(df["Cycle"] > 0) & (df["Cycle"] % 2 != 0) ,[' Praw']].mean()
PCellRef = float(np.round(PCellRef, 3))
refLab = str(PCellRef) + " Torr"
plt.text(0.01, 0.02, smpLab, size = 8, color = colSample, ha = 'left', va = 'bottom', transform = ax4.transAxes, bbox = dict(fc = 'white', ec = "none", pad = 1, alpha = 0.5))
plt.text(0.01, 0.12, refLab, size = 8, color = colReference, ha = 'left', va = 'bottom', transform = ax4.transAxes, bbox = dict(fc = 'white', ec = "none", pad = 1, alpha = 0.5))
plt.ylabel("Pressure (Torr, cell)")
plt.text(0.99, 0.98, 'D', size = 14, ha = 'right', va = 'top', transform = ax4.transAxes)

# Subplot E: Cell temperature
ax5 = plt.subplot(pltsize, 1, 5, sharex = ax1)
x = df['Time(rel)']
y = df[' Traw'] - 273.15
plt.scatter(x, y, marker=".",color = df['Type'].map(data_colors))
plt.ylabel("Temperature (°C, cell)")
minty = np.round(np.mean(y), 3)
sdt = np.round(np.std(y), 3)
la = str(minty) + "±" + str(sdt) + " °C"
plt.text(0.01, 0.02, la, size=8, color="black", ha = 'left', va = 'bottom', transform=ax5.transAxes, bbox=dict(fc='white', ec="none", pad=1,alpha=0.5))
plt.text(0.99, 0.98, 'E', size = 14, ha = 'right', va = 'top', transform = ax5.transAxes)

# Subplot F: Coolant temperature and room temperature
ax6 = plt.subplot(pltsize, 1, 6, sharex = ax1)
x = df['Time(rel)']
y = df[' Tref'] - 273.15
plt.scatter(x, y, marker=".",color = df['Type'].map(data_colors))
plt.ylabel("Temperature (°C, coolant)")
mean = np.round(np.mean(y), 3)
std = np.round(np.std(y), 3)
labelCoolantT = str(mean) + "±" + str(std) + " °C"
ax5b = ax6.twinx()
ax5b.spines['right'].set_color('C1')
x = dfLogFile["Time(rel)"]
y = dfLogFile['roomTemperature']
plt.plot(x, y, color = "C1")
plt.ylabel("Temperature (°C, room)")
mean = np.round(np.mean(y), 3)
std = np.round(np.std(y), 3)
labelRoomT = str(mean) + "±" + str(std) + " °C"
plt.text(1 - 0.01, 0.02, labelRoomT, size=8, color="C1", ha = 'right', va = 'bottom', transform = ax6.transAxes, bbox=dict(fc='white', ec="none", pad=1,alpha=0.5))
plt.text(0.01, 0.02, labelCoolantT, size=8, color="black", ha = 'left', va = 'bottom', transform = ax6.transAxes, bbox=dict(fc='white', ec="none", pad=1,alpha=0.5))
plt.text(0.99, 0.98, 'F', size = 14, ha ='right', va = 'top', transform = ax6.transAxes)

# Subplot G: Box temperature vs time
ax7 = plt.subplot(pltsize, 1, 7, sharex = ax1)
if (exists(folder + "logFile.csv")) and ('boxTemperature' in dfLogFile.columns):
    x = dfLogFile["Time(rel)"]
    y = dfLogFile['boxTemperature']
    plt.plot(x, y)
    plt.ylabel("Temperature (°C, box)")
    mean = np.round(np.mean(y), 3)
    std = np.round(np.std(y), 3)
    labelTemp = str(mean) + "±" + str(std) + " °C"
    if 'boxSetpoint' in dfLogFile.columns:
        x = dfLogFile["Time(rel)"]
        y = dfLogFile['boxSetpoint']
        plt.plot(x, y, color="C2")
        labelSP = str("SP: ") + str(dfLogFile['boxSetpoint'].iat[0]) + " °C"
    if 'fanSpeed' in dfLogFile.columns:
        ax7b = ax7.twinx()
        ax7b.spines['right'].set_color('C1')
        x = dfLogFile["Time(rel)"]
        y = dfLogFile['fanSpeed']
        plt.plot(x, y, color="C1")
        plt.ylabel("Fan speed (%)")
        plt.text(0.01, 0.11, labelSP, size = 8, color = "C2", ha = 'left', va = 'bottom', transform = ax7.transAxes, bbox=dict(fc = 'white', ec = "none", pad = 1, alpha=0.5))
    plt.text(0.01, 0.02, labelTemp, size = 8, color = "C0", ha = 'left', va = 'bottom', transform = ax7.transAxes, bbox=dict(fc = 'white', ec = "none", pad = 1, alpha=0.5))
plt.text(0.99, 0.98, 'G', size=14, ha = 'right', va = 'top', transform = ax7.transAxes)

# Subplot H: X (reference) bellow expansion and pressure
ax8 = plt.subplot(pltsize, 1, 8, sharex=ax1)
if (exists(folder + "logFile.csv")) and ('pressureX' in dfLogFile.columns):
    x = dfLogFile["Time(rel)"]
    y = dfLogFile['pressureX']
    plt.plot(x, y)
    plt.ylabel("X (ref.) bellow pressure (mbar)")
    ax8b = ax8.twinx()
    ax8b.spines['right'].set_color('C1')
    y = dfLogFile['percentageX']
    plt.plot(x, y, color="C1")
    plt.ylabel("X (ref.) bellow expansion (%)")
plt.text(0.99, 0.98, 'H', size = 14, ha = 'right', va = 'top', transform = ax8.transAxes)

# Subplot J: Y (sample) bellow expansion and pressure
ax9 = plt.subplot(pltsize, 1, 9, sharex=ax1)
if (exists(folder + "logFile.csv")) and ('pressureY' in dfLogFile.columns):
    x = dfLogFile["Time(rel)"]
    y = dfLogFile['pressureY']
    plt.plot(x, y, label="Y (Reference)")
    plt.ylabel("Y (sam.) bellow pressure (mbar)")
    ax9b = ax9.twinx()
    ax9b.spines['right'].set_color('C1')
    y = dfLogFile['percentageY']
    plt.plot(x, y, color="C1")
    plt.ylabel("Y (sam.) bellow expansion (%)")
plt.text(0.99, 0.98, 'I', size=14, ha = 'right', va = 'top', transform = ax9.transAxes)

# Subplot K: Z bellow
ax10 = plt.subplot(pltsize, 1, 10, sharex = ax1)
x = dfLogFile["Time(rel)"]
y = dfLogFile['pressureA']
plt.plot(x, y)
plt.ylabel("A pressure (mbar)")
ax10b = ax10.twinx()
ax10b.spines['right'].set_color('C1')
y = dfLogFile['percentageZ']
plt.plot(x, y, color = "C1")
plt.ylabel("Z bellow expansion (%)")
plt.text(0.99, 0.98, 'J', size = 14, ha = 'right', va = 'top', transform = ax10.transAxes)

ax10.set_xlabel("Relative time (s)")
plt.tight_layout()
# plt.savefig(folder + "rawData.svg")
plt.savefig(folder + "rawData.png", dpi = 300)


#################################################################
###################### Figure 2 – Fit data ######################
#################################################################

# Plot properties
width = 6
height = 2.5 * 3 + 1
plt.rcParams["figure.figsize"] = (width, height)
plt.rcParams["legend.loc"] = "upper left"
plt.figure(0)
plt.rcParams.update({'font.size': 6})

# Reference gas composition
d18OWorkingGas = 28.048
d17OWorkingGas = 14.621  # D'17O = -90 ppm
Dp17OWorkingGas = Dp17O(d17OWorkingGas, d18OWorkingGas) / 1000 # D'17O in permille

# Make separate dataframes for Dummy, Reference, and Sample
dfRef = df.loc[df['Type'] == "Ref"]
dfSam = df.loc[df['Type'] == "Sam"]
dfDummy = df.loc[df['Type'] == "Dummy"]

######################### Plot A – d17O #########################
ax1 = plt.subplot(3, 1, 1)
plt.text(0.99, 0.99, 'A', size = 14, ha = 'right', va = 'top', transform = ax1.transAxes)
plt.title(samID)

xDummy = df.loc[df['Type'] == "Dummy"]["Time(rel)"]
d17ODummyRaw = ((dfDummy['I627']/dfDummy['I626'])/np.mean(df['I627']/df['I626']) - 1) * 1000
yDummy = d17ODummyRaw
plt.scatter(xDummy, yDummy, color = colDummy, marker = ".", label = "Dummy", zorder = 4)

xRef = df.loc[df['Type'] == "Ref"]["Time(rel)"]
d17ORefRaw = ((dfRef['I627']/dfRef['I626'])/np.mean(df['I627']/df['I626']) - 1) * 1000
yRef = d17ORefRaw
plt.scatter(xRef, yRef, color = colReference, marker=".", label="Reference", zorder = 3)

xSam = dfSam['Time(rel)']
d17OSamRaw = ((dfSam['I627']/dfSam['I626'])/np.mean(df['I627']/df['I626']) - 1) * 1000
ySam = d17OSamRaw
plt.scatter(xSam, ySam, color = colSample, marker = ".", label = "Sample", zorder = 2)

# Calculate the delta values
if polynomial != "100":

    # Calculate and plot with the "smooth fit" approach

    y1 = np.array(df.loc[df['Type'] == "Ref"]["d17O_raw"])
    y2 = np.array(df.loc[df['Type'] == "Sam"]["d17O_raw"])
    comboY = np.append(y1, y2)

    x1 = np.array(xRef)
    x2 = np.array(xSam)
    comboX = np.append(x1, x2)

    if len(y1) != len(x1):
        raise(Exception('Unequal x1 and y1 data length'))
    if len(y2) != len(x2):
        raise(Exception('Unequal x2 and y2 data length'))

    # Fit the combined data to the combined function
    initialParameters = np.array([1, 1, 1, 1, 1])
    fittedParameters, pcov = curve_fit(combinedFunction, comboX, comboY, initialParameters)
    r0, s0, a1, a2, a3 = fittedParameters

    # xFit defined here, but used in subsequent smooth fit plots
    xFit = np.arange(min(dfRef['Time(rel)']), max(dfRef['Time(rel)']))

    yFit1 = function1(xFit, r0, s0, a1, a2, a3)  # first data set, first equation
    yFit2 = function2(xFit, r0, s0, a1, a2, a3)  # second data set, second equation

    # Calculate the alpha (Sam / Ref) value
    a17Poly = (yFit2[0] + 1000) / (yFit1[0] + 1000)
    d17OPolyRaw = (a17Poly - 1) * 1000

    plt.plot(xFit, yFit1, color = colReference, zorder = -1)
    plt.plot(xFit, yFit2, color = colSample, zorder = -1)
else:

    # Calculate and plot with the "bracketing" approach

    bracketingResults = []
    bracketingCycles = []
    bracketingTime = []
    bracketingpCO2 = []
    bracketingpCO2_mismatch = []

    # New dataframe without the dummy cycles
    if "air" in samID.lower():
        dfm = df.loc[df['Cycle'] > 2]
        cy = 4 # the number of the first proper reference cycle
    else:
        dfm = df.loc[df['Cycle'] > 0]
        cy = 2 # the number of the first proper reference cycle

    dfm = dfm.groupby(['Cycle'])['Time(rel)',"d17O_raw","d18O_raw","Dp17O_raw"].mean()
    plt.scatter(dfm.iloc[:,0], dfm.iloc[:,1], marker = "*", s = 20, c = colBracketing, label = "Cycle avg", zorder = 5)

    while cy < df['Cycle'].max():
        if (cy % 2) == 0:

            # Previous (reference) cycle
            x1 = df.loc[df['Cycle'] == cy - 1]["Time(rel)"].mean()
            y1 = df.loc[df['Cycle'] == cy - 1]["d17O_raw"].mean()
            y1error = sem(df.loc[df['Cycle'] == cy - 1]["d17O_raw"])

            # Following (reference) cycle
            x2 = df.loc[df['Cycle'] == cy + 1]["Time(rel)"].mean()
            y2 = df.loc[df['Cycle'] == cy + 1]["d17O_raw"].mean()
            y2error = sem(df.loc[df['Cycle'] == cy + 1]["d17O_raw"])

            # Interpolation based on the neighbouring reference cycles
            m = (y2 - y1) / (x2 - x1)
            b = y1 - m * x1

            # Values for the sample cycle
            xs = df.loc[df['Cycle'] == cy]["Time(rel)"].mean()
            ys = df.loc[df['Cycle'] == cy]["d17O_raw"].mean()
            ysRef = m * xs + b
            
            a17Bracketing = (ys + 1000) / (ysRef + 1000)
            d17OBracketing = (d17OWorkingGas + 1000 ) * a17Bracketing - 1000
            bracketingResults.append(d17OBracketing)
            bracketingCycles.append(cy)

            bracketingTime.append(xs)
            bracketingpCO2.append(df.loc[df['Cycle'] == cy]["I626"].mean()/1000)
            bracketingpCO2_mismatch.append((pCO2Ref - df.loc[df['Cycle'] == cy]["I626"].mean()/1000))

            # Only plot bracketing data if we need it
            if polynomial == "100":
                plt.plot([x1, x2], [y1, y2], linestyle = 'dotted', color = colBracketing, linewidth=1.2, dash_capstyle = "round", zorder = 5)
                plt.plot([xs, xs], [ys, ysRef], color = colBracketing, linewidth = 1.2, zorder = 5)
        cy = cy + 1

    # We create the dfBracketingResults dataframe here
    dfBracketingResults = pd.DataFrame(bracketingCycles, columns = ["Cycle"])
    dfBracketingResults['Time(rel)'] = bracketingTime
    dfBracketingResults['pCO2'] = bracketingpCO2
    dfBracketingResults['pCO2_mismatch'] = bracketingpCO2_mismatch
    dfBracketingResults['d17O'] = bracketingResults

plt.ylabel("$\delta^{17}$O (‰, raw)")
plt.legend()
ax1lim = ax1.get_xlim()

######################### Plot B – d18O #########################
ax2 = plt.subplot(3, 1, 2)
plt.text(0.99, 0.99, 'B', size = 14, ha = 'right', va = 'top', transform = ax2.transAxes)

d18ODummyRaw = ((dfDummy['I628']/dfDummy['I626'])/np.mean(df['I628']/df['I626']) - 1) * 1000
yDummy = d18ODummyRaw
plt.scatter(xDummy, yDummy, color = colDummy, marker = ".", label = "Dummy", zorder = 4)

d18ORefRaw = ((dfRef['I628']/dfRef['I626'])/np.mean(df['I628']/df['I626']) - 1) * 1000
yRef = d18ORefRaw
plt.scatter(xRef, yRef, color=colReference, marker=".", label="Reference", zorder = 3)

d18OSamRaw = ((dfSam['I628']/dfSam['I626'])/np.mean(df['I628']/df['I626']) - 1) * 1000
ySam = d18OSamRaw
plt.scatter(xSam, ySam, color = colSample, marker=".", label="Sample", zorder = 2)

# Calculate the delta values
if polynomial != "100":

    # Calculate and plot with the "smooth fit" approach

    y1 = np.array(df.loc[df['Type'] == "Ref"]["d18O_raw"])
    y2 = np.array(df.loc[df['Type'] == "Sam"]["d18O_raw"])
    comboY = np.append(y1, y2)

    x1 = np.array(xRef)
    x2 = np.array(xSam)
    comboX = np.append(x1, x2)

    if len(y1) != len(x1):
        raise(Exception('Unequal x1 and y1 data length'))
    if len(y2) != len(x2):
        raise(Exception('Unequal x2 and y2 data length'))

    # Fit the combined data to the combined function
    fittedParameters, pcov = curve_fit(combinedFunction, comboX, comboY, initialParameters)

    # values for display of fitted function
    r0, s0, a1, a2, a3 = fittedParameters

    # first data set, first equation
    yFit1 = function1(xFit, r0, s0, a1, a2, a3)
    # second data set, second equation
    yFit2 = function2(xFit, r0, s0, a1, a2, a3)

    # Calculate the errors for the reference
    fit1 = function1(x1, r0, s0, a1, a2, a3)
    diff1 = y1-fit1
    sd1 = np.std(diff1) / np.sqrt(len(diff1))

    # Calculate the errors for the sample
    fit2 = function2(x2, r0, s0, a1, a2, a3)
    diff2 = y2-fit2
    sd2 = np.std(diff2) / np.sqrt(len(diff2))

    # Calculate propagated errors
    d18OPolyErr = np.round(np.sqrt(sd1**2 + sd2**2), 3)

    # Calculate the alpha (Sam / Ref) value
    a18Poly = (yFit2[0] + 1000) / (yFit1[0] + 1000)
    d18OPolyRaw = (a18Poly - 1) * 1000

    plt.plot(xFit, yFit1, color=colReference, zorder = -1)
    plt.plot(xFit, yFit2, color=colSample, zorder = -1)
else:

    # Calculate and plot with the "bracketing" approach

    bracketingResults = []

    plt.scatter(dfm.iloc[:,0], dfm.iloc[:,2], marker = "*", s = 20, c = colBracketing, label = "Cycle avg", zorder = 5)

    if "air" in samID.lower():
        cy = 4
    else:
        cy = 2

    while cy < df['Cycle'].max():
        if (cy % 2) == 0:

            # Previous (reference) cycle
            x1 = df.loc[df['Cycle'] == cy - 1]["Time(rel)"].mean()
            y1 = df.loc[df['Cycle'] == cy - 1]["d18O_raw"].mean()
            y1error = sem(df.loc[df['Cycle'] == cy-1]["d18O_raw"])

            # Following (reference) cycle
            x2 = df.loc[df['Cycle'] == cy + 1]["Time(rel)"].mean()
            y2 = df.loc[df['Cycle'] == cy + 1]["d18O_raw"].mean()
            y2error = sem(df.loc[df['Cycle'] == cy + 1]["d18O_raw"])

            # Interpolation based on the neighbouring reference cycles
            m = (y2 - y1) / (x2 - x1)
            b = y1 - m * x1

            # Values for the sample cycle
            xs = df.loc[df['Cycle'] == cy]["Time(rel)"].mean()
            ys = df.loc[df['Cycle'] == cy]["d18O_raw"].mean()
            ysRef = m * xs + b
            
            a18Bracketing = (ys + 1000) / (ysRef + 1000)
            d18OBracketing = (d18OWorkingGas + 1000 ) * a18Bracketing - 1000
            bracketingResults.append(d18OBracketing)

            # Only plot bracketing data if we need it
            if polynomial == "100":
                plt.plot([x1, x2], [y1, y2], linestyle = 'dotted', color = colBracketing, linewidth = 1.2, dash_capstyle = "round", zorder = 5)
                plt.plot([xs, xs], [ys, ysRef], color = colBracketing, linewidth = 1.2, zorder = 5)
        cy = cy + 1

    dfBracketingResults['d18O'] = bracketingResults

plt.ylabel("$\delta^{18}$O (‰, raw)")
plt.legend()

######################## Plot C – Dp17O #########################
ax3 = plt.subplot(3, 1, 3)
plt.text(0.99, 0.99, 'C', size = 14, ha = 'right', va = 'top', transform = ax3.transAxes)

# Values referenced to the working gas
d17ODummy = d17ODummyRaw + d17OWorkingGas + 1/1000 * d17ODummyRaw * d17OWorkingGas
d18ODummy = d18ODummyRaw + d18OWorkingGas + 1/1000 * d18ODummyRaw * d18OWorkingGas
yDummy = (1000 * np.log(d17ODummy/1000+1) - 0.528 * 1000 * np.log(d18ODummy/1000+1)) * 1000
plt.scatter(xDummy, yDummy, color = colDummy, marker = ".", label = "Dummy")

d17ORef = d17ORefRaw + d17OWorkingGas + 1/1000 * d17ORefRaw * d17OWorkingGas
d18ORef = d18ORefRaw + d18OWorkingGas + 1/1000 * d18ORefRaw * d18OWorkingGas
yRef = (1000 * np.log(d17ORef/1000+1) - 0.528 * 1000 * np.log(d18ORef/1000+1)) * 1000
plt.scatter(xRef, yRef, color = colReference, marker = ".", label = "Reference")

d17OSam = d17OSamRaw + d17OWorkingGas + 1/1000 * d17OSamRaw * d17OWorkingGas
d18OSam = d18OSamRaw + d18OWorkingGas + 1/1000 * d18OSamRaw * d18OWorkingGas
ySam = (1000 * np.log(d17OSam/1000+1) - 0.528 * 1000 * np.log(d18OSam/1000+1)) * 1000
plt.scatter(xSam, ySam, color = colSample, marker = ".", label = "Sample")

# Calculate the Dp17O values
if polynomial != "100":

    # Calculate and plot with the "smooth fit" approach

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

    # curve fit the combined data to the combined function
    fittedParameters, pcov = curve_fit(combinedFunction, comboX, comboY, initialParameters)

    # values for display of fitted function
    r0, s0, a1, a2, a3 = fittedParameters

    y_fit_1 = function1(xFit, r0, s0, a1, a2, a3)  # first data set, first equation
    y_fit_2 = function2(xFit, r0, s0, a1, a2, a3)  # second data set, second equation

    plt.plot(xFit, y_fit_1, color=colReference, zorder = -1)
    plt.plot(xFit, y_fit_2, color=colSample, zorder = -1)

    # Calculate the errors for the reference
    x = x1
    y = y1
    yfit = function1(x, r0, s0, a1, a2, a3)
    diff = y-yfit
    sd1 = np.std(diff) / np.sqrt(len(diff))

    # Calculate the errors for the sample
    x = x2
    y = y2
    yfit = function2(x, r0, s0, a1, a2, a3)
    diff = y-yfit
    sd2 = np.std(diff) / np.sqrt(len(diff))

    # Calculate propagated errors
    Dp17OPolyErr = np.round(np.sqrt(sd1**2 + sd2**2),1)

    # Final polynomial results
    d17OPolyFinal = round(d17OPolyRaw + d17OWorkingGas + 1/1000 * d17OPolyRaw * d17OWorkingGas, 3)
    d18OPolyFinal = round(d18OPolyRaw + d18OWorkingGas + 1/1000 * d18OPolyRaw * d18OWorkingGas, 3)
    Dp17OPolyFinal = round((1000 * np.log(d17OPolyFinal / 1000 + 1) - 0.528 * 1000 * np.log(d18OPolyFinal / 1000 + 1)) * 1000, 1)
else:

    # Calculate and plot with the "bracketing" approach

    bracketingResults = []
    bracketingTime = []
    bracketingYs = []

    plt.scatter(dfm.iloc[:,0], dfm.iloc[:,3]+ Dp17OWorkingGas * 1000, marker = "*", s = 20, c=colBracketing, label = "Cycle avg", zorder = 5)

    if "air" in samID.lower():
        cy = 4
    else:
        cy = 2

    while cy < df['Cycle'].max():
        if (cy % 2) == 0:

            # Previous (reference) cycle
            x1 = df.loc[df['Cycle'] == cy - 1]["Time(rel)"].mean()
            y1 = df.loc[df['Cycle'] == cy - 1]["Dp17O_raw"].mean() + Dp17OWorkingGas * 1000
            y1error = sem(df.loc[df['Cycle'] == cy - 1]["Dp17O_raw"])

            # Following (reference) cycle
            x2 = df.loc[df['Cycle'] == cy + 1]["Time(rel)"].mean()
            y2 = df.loc[df['Cycle'] == cy + 1]["Dp17O_raw"].mean() + Dp17OWorkingGas * 1000
            y2error = sem(df.loc[df['Cycle'] == cy + 1]["Dp17O_raw"])

            # Interpolation based on the neighbouring reference cycles
            m = (y2 - y1) / (x2 - x1)
            b = y1 - m * x1

            # Values for the sample cycle
            xs = df.loc[df['Cycle'] == cy]["Time(rel)"].mean()
            ys = df.loc[df['Cycle'] == cy]["Dp17O_raw"].mean() + Dp17OWorkingGas * 1000
            ysRef = m * xs + b

            bracketingCycles.append(cy)
            bracketingResults.append(ys - ysRef + Dp17OWorkingGas * 1000)
            bracketingTime.append(xs)
            bracketingYs.append(ys)

            if polynomial == "100":
                plt.plot([x1, x2], [y1, y2], linestyle = 'dotted', color = colBracketing, linewidth = 1.2, dash_capstyle = "round", zorder = 5)
                plt.plot([xs, xs], [ys, ysRef], color = colBracketing, linewidth = 1.2, zorder = 5)
        cy = cy + 1

    dfBracketingResults['Dp17O'] = bracketingResults

    # Calculate modified z-score based on Iglewicz and Hoaglin 1993
    # median = np.median(dfBracketingResults['Dp17O'])
    # diff = (dfBracketingResults['Dp17O'] - median)
    # mad = np.median(np.absolute(diff))
    # modified_z_score = 0.6745 * diff / mad
    # dfBracketingResults['z_score'] = stats.zscore(dfBracketingResults['Dp17O'])
    # dfBracketingResults['IH_score'] = modified_z_score

    # Export bracketing data to a file, including outliers
    dfBracketingResults.to_excel(excel_writer=folder + "bracketingResults.xlsx", header = True, index = False)

    # Final bracketing results
    d18O_SRB = round(np.mean(dfBracketingResults['d18O']), 3)
    d18O_SRB_error = round(sem(dfBracketingResults['d18O']), 3)
    d17O_SRB = round(np.mean(dfBracketingResults['d17O']), 3)
    d17O_SRB_error = round(sem(dfBracketingResults['d17O']), 3)
    D17Op_SRB = round(np.mean(dfBracketingResults['Dp17O']), 1)
    D17Op_SRB_error = round(sem(dfBracketingResults['Dp17O']), 1)

# Write evaluated data into the figure title
workingGasInfo = str("\n(Reference gas: " + "$\delta{}^{17}$O: " + str(d17OWorkingGas) + "‰, " + "$\delta{}^{18}$O: " +
                     str(d18OWorkingGas) + "‰, " + "$\Delta{}^{\prime 17}$O: " + str(round(Dp17OWorkingGas*1000, 1)) + " ppm)")
if polynomial == "100":
    evaluatedData = str("Results from bracketing: " +
                        "$\delta{}^{17}$O: " + str(d17O_SRB) +
                        "‰, $\delta{}^{18}$O: " + str(d18O_SRB) + " ± " + str(d18O_SRB_error) +
                        "‰, $\Delta{}^{\prime 17}$O: " + str(D17Op_SRB) + " ± " + str(D17Op_SRB_error) + " ppm")
else:
    evaluatedData = str("Results from " + polynomial + "$^{nd}$ order polynomial fit: " +
                        "$\delta{}^{17}$O: " + str(d17OPolyFinal) +
                        "‰, $\delta{}^{18}$O: " + str(d18OPolyFinal) + " ± " + str(d18OPolyErr) + 
                        "‰, $\Delta{}^{\prime 17}$O: " + str(Dp17OPolyFinal) + " ± " + str(round(Dp17OPolyErr, 1)) + " ppm")
plt.title(evaluatedData + workingGasInfo)

plt.ylabel("$\Delta^{\prime 17}$O (ppm, raw)")
plt.xlabel("Relative time (s)")
plt.legend()

plt.tight_layout()
plt.savefig(str(folder + "FitPlot.png"), dpi = 300)

##### Plot backeting results ####
if (polynomial == "100"):
    plt.rcParams["figure.figsize"] = (6, 2.4)
    plt.rcParams["legend.loc"] = "upper left"
    plt.rcParams.update({'font.size': 6})
    plt.figure(2)

    plt.scatter(dfBracketingResults['Time(rel)'], dfBracketingResults['Dp17O'], marker = "*", s = 20, c=colSample, label = "Cycle avg", zorder = 5)
    plt.plot(dfBracketingResults['Time(rel)'], dfBracketingResults['Dp17O'], color = colSample, linewidth = 1)
    plt.axhline(D17Op_SRB, c=colBracketing, zorder=-1, linewidth=1.2, label="mean")
    plt.axhline(D17Op_SRB-D17Op_SRB_error, c=colBracketing, linestyle='dotted', dash_capstyle="round", zorder=-1, linewidth=1.2, label="sem")
    plt.axhline(D17Op_SRB+D17Op_SRB_error, c=colBracketing, linestyle='dotted', dash_capstyle="round", zorder=-1, linewidth=1.2)
    plt.ylabel("$\Delta^{\prime 17}$O (ppm)")
    plt.xlabel("Relative time (s)")
    plt.title(samID)
    plt.xlim(ax1lim)
    plt.legend()
    plt.tight_layout()
    plt.savefig(str(folder + "bracketingResults.png"), dpi=300)


# Print out the values. This is what the evaluateData.php reads out
if polynomial != '100':
    print(sys.argv[1], d17OPolyFinal, d18OPolyFinal, d18OPolyErr, Dp17OPolyFinal, Dp17OPolyErr, d17OWorkingGas, d18OWorkingGas, pCO2Ref, pCO2Sam, PCellRef, PCellSam)
else:
    print(sys.argv[1], d17O_SRB, d18O_SRB, d18O_SRB_error, D17Op_SRB, D17Op_SRB_error, d17OWorkingGas, d18OWorkingGas, pCO2Ref, pCO2Sam, PCellRef, PCellSam)
