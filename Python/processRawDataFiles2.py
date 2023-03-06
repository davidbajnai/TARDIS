# this script plots the TILDAS data and calculates the isotope ratios

# the script has to start with this, do not move these lines
import os
os.environ['MPLCONFIGDIR'] = "/var/www/html/Python"
os.chdir(os.path.dirname(os.path.realpath(__file__)))

# import modules
import matplotlib as mpl
from scipy.stats import t
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
samID = str(sys.argv[1])
folder = "../Results/" + samID + "/"
polynomial = str(sys.argv[2])
measurement_date = datetime.strptime(samID[0:6], '%y%m%d')

strFiles = []
for file in os.listdir(folder):
    if file.endswith(".str"):
        strFiles.append(file)
strFiles.sort()

# Pattern for the measurement. Air measurements start with 3 dummies.
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

# If a cycle is skipped, we can adjust the cycle numbers here, e.g., 230118_084902_heavyVsRef
# If all is good, leave it commented out.
# dfAll.loc[dfAll['Cycle'] > 3, 'Cycle'] +=1

dfAll['d17O'] = ((dfAll['I627'] / dfAll['I626']) / np.mean(dfAll['I627'] / dfAll['I626']) - 1) * 1000
dfAll['d18O'] = ((dfAll['I628'] / dfAll['I626']) / np.mean(dfAll['I628'] / dfAll['I626']) - 1) * 1000
dfAll['Dp17O'] = (1000 * np.log(dfAll['d17O'] / 1000 + 1) - 0.528 * 1000 * np.log(dfAll['d18O'] / 1000 + 1)) * 1000

# Export all data into an Excel file
dfAll.to_excel(folder + "allData.xlsx")

# Now select data using the z-score (3sigma criterion)
# The excel file includes all data, but only the filtered data is used for the calculationsand plots
df = dfAll
nOutliers = df.loc[df['z_score'].abs() > 3].shape[0] # number of outliers
df = df.loc[df['z_score'].abs() <= 3]

dfLogFile = pd.read_csv(folder + "logFile.csv")

# Calculate the measurement duration
seconds = df['Time(rel)'].iat[-1]
measurement_duration = str("%d:%02d:%02d" % (seconds % (24 * 3600) // 3600, seconds % 3600 // 60, seconds % 3600 % 60))

# Time shift between TILDAS data and the logfile data

x_logFile = dfLogFile["dateTime"] - startTime


############################## Raw data ##############################
######################################################################

# Plot parameters
width = 6
height = 18
plt.rcParams["figure.figsize"] = (width, height)
plt.rcParams.update({'font.size': 6})
plt.rcParams["legend.loc"] = "upper left"
# from http://tsitsul.in/blog/coloropt/                blue     yellow      red        grey    green
mpl.rcParams['axes.prop_cycle'] = mpl.cycler(color=["#4053d3", "#ddb310", "#b51d14", "#cacaca", "#00b25d"])

colSample = "C0"
colReference = "C2"
colBracketing = "C1"
colDummy = "C3"
data_colors = {'Dummy':'C3', 'Sam':'C0', 'Ref':'C2'}
cmap = LinearSegmentedColormap.from_list('custom_colors', ['C3','C2','C0'])
data_names = ['Dummy', 'Reference', 'Sample']

pltsize = 10 # Number of subplots

# Subplot A: d18O vs time
ax1 = plt.subplot(pltsize, 1, 1)
x = df['Time(rel)']
y = df['d18O']
scat = plt.scatter(x, y, marker = ".", c = df.Type.astype('category').cat.codes, cmap=cmap)
plt.text(0.99 , 0.98, 'A', size = 14, ha = 'right', va = 'top', transform = ax1.transAxes)
plt.legend(handles=scat.legend_elements()[0], labels=data_names, markerscale = 0.5)
plt.ylabel("$\delta^{18}$O (‰, raw)")
plt.title(samID + "\nmeasurement duration: " + measurement_duration)

# Subplot B: D17O vs time
ax2 = plt.subplot(pltsize, 1, 2, sharex=ax1)
x = df['Time(rel)']
y = df['Dp17O']
plt.scatter(x, y, marker=".", color = df['Type'].map(data_colors))
plt.ylabel("$\Delta^{\prime 17}$O (ppm, raw)")
plt.text(0.99, 0.98, 'B', size = 14, ha = 'right', va = 'top', transform=ax2.transAxes)

# Subplot C: CO2 in cell vs time
ax3 = plt.subplot(pltsize, 1, 3, sharex=ax1)
x = df['Time(rel)']
y = df['I626'] / 1000
plt.scatter(x, y, marker=".", color = df['Type'].map(data_colors))
pCO2Sam = df.loc[(df["Cycle"] > 0) & (df["Cycle"] % 2 == 0) ,['I626']].mean()/1000
pCO2Sam = float(np.round(pCO2Sam, 1))
smpLab = str(pCO2Sam) + " ppm"
pCO2Ref = df.loc[(df["Cycle"] > 0) & (df["Cycle"] % 2 != 0) ,['I626']].mean()/1000
pCO2Ref = float(np.round(pCO2Ref, 1))
refLab = str(pCO2Ref) + " ppm"
plt.text(0.01, 0.02, smpLab, size = 8, color = colSample, ha = 'left', va = 'bottom', transform = ax3.transAxes, bbox = dict(fc = 'white', ec = "none", pad = 1, alpha = 0.5))
plt.text(0.01, 0.12, refLab, size = 8, color = colReference, ha = 'left', va = 'bottom', transform = ax3.transAxes, bbox = dict(fc = 'white', ec = "none", pad = 1, alpha = 0.5))
plt.ylabel("$\mathit{p}$CO$_2$ (ppm, cell)")
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
if (exists(folder + "logFile.csv")) and ('roomTemperature' in dfLogFile.columns):
    ax5b = ax6.twinx()
    ax5b.spines['right'].set_color('C1')
    x = x_logFile
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
    x = x_logFile
    y = dfLogFile['boxTemperature']
    plt.plot(x, y)
    plt.ylabel("Temperature (°C, box)")
    mean = np.round(np.mean(y), 3)
    std = np.round(np.std(y), 3)
    labelTemp = str(mean) + "±" + str(std) + " °C"
    if 'boxSetpoint' in dfLogFile.columns:
        x = x_logFile
        y = dfLogFile['boxSetpoint']
        plt.plot(x, y, color="C2")
        labelSP = str("SP: ") + str(dfLogFile['boxSetpoint'].iat[0]) + " °C"
    if 'fanSpeed' in dfLogFile.columns:
        ax7b = ax7.twinx()
        ax7b.spines['right'].set_color('C1')
        x = x_logFile
        y = dfLogFile['fanSpeed']
        plt.plot(x, y, color="C1")
        plt.ylabel("Fan speed (%)")
        plt.text(0.01, 0.11, labelSP, size = 8, color = "C2", ha = 'left', va = 'bottom', transform = ax7.transAxes, bbox=dict(fc = 'white', ec = "none", pad = 1, alpha=0.5))
    plt.text(0.01, 0.02, labelTemp, size = 8, color = "C0", ha = 'left', va = 'bottom', transform = ax7.transAxes, bbox=dict(fc = 'white', ec = "none", pad = 1, alpha=0.5))
plt.text(0.99, 0.98, 'G', size=14, ha = 'right', va = 'top', transform = ax7.transAxes)

# Subplot H: X (reference) bellow expansion and pressure
ax8 = plt.subplot(pltsize, 1, 8, sharex=ax1)
if (exists(folder + "logFile.csv")) and ('pressureX' in dfLogFile.columns):
    x = x_logFile
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
    x = x_logFile
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
x = x_logFile
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
plt.savefig(folder + "rawData.svg")
plt.savefig(folder + "rawData.png", dpi = 300)


############################## Fit data ##############################
######################################################################

# Fit the ref and sam data with the same a1, a2, a3 and only different intercepts r0, s0
# Modified after https://stackoverflow.com/questions/51482486/python-global-fitting-for-data-sets-of-different-sizes
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

# Plot properties
height = 11.69
width = 6
plt.rcParams["figure.figsize"] = (width, height)
plt.rcParams["legend.loc"] = "upper left"
plt.figure(0)
plt.rcParams.update({'font.size': 6})

# Reference gas composition
d18OReference = 28.048
d17OReference = 14.621  # D'17O = -90 ppm
Dp17OReference = 1000 * np.log(d17OReference / 1000 + 1) - 0.528 * 1000 * np.log(d18OReference / 1000 + 1)

# Make separate dataframes for Dummy, Reference, and Sample
dfRef = df.loc[df['Type'] == "Ref"]
dfSam = df.loc[df['Type'] == "Sam"]
dfDummy = df.loc[df['Type'] == "Dummy"]


########## Fit for d17O ##########
ax1 = plt.subplot(3, 1, 1)
plt.text(0.99, 0.99, 'A', size = 14, ha = 'right', va = 'top', transform = ax1.transAxes)

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

# Polynomial fit calculations
y1 = np.array(df.loc[df['Type'] == "Ref"]['d17O'])
y2 = np.array(df.loc[df['Type'] == "Sam"]['d17O'])
comboY = np.append(y1, y2)

x1 = np.array(xRef)
x2 = np.array(xSam)
comboX = np.append(x1, x2)

# Quality control
if len(y1) != len(x1):
    raise(Exception('Unequal x1 and y1 data length'))
if len(y2) != len(x2):
    raise(Exception('Unequal x2 and y2 data length'))

# Some initial parameter values
initialParameters = np.array([1, 0, 0, 0, 0])

# curve fit the combined data to the combined function
fittedParameters, pcov = curve_fit(combinedFunction, comboX, comboY, initialParameters)

# values for display of fitted function
r0, s0, a1, a2, a3 = fittedParameters

xFitData = np.arange(min(dfRef['Time(rel)']), max(dfRef['Time(rel)']))

y_fit_1 = function1(xFitData, r0, s0, a1, a2, a3)  # first data set, first equation
y_fit_2 = function2(xFitData, r0, s0, a1, a2, a3)  # second data set, second equation

# Calculate the alpha (Sam / Ref) value
a17Poly = (y_fit_2[0] + 1000) / (y_fit_1[0] + 1000)
d17OPolyRaw = (a17Poly - 1) * 1000

# Only plot polynomial data if we need it
if polynomial != "100":
    plt.plot(xFitData, y_fit_1, color = colReference, zorder = -1)
    plt.plot(xFitData, y_fit_2, color = colSample, zorder = -1)

# Bracketing calculations
bracketingResults = []
bracketingCycles = []

if "air" in samID.lower():
    dfm = df.loc[df['Cycle'] > 2] # starting from cycle 3 (0,1,2 are dummies)
    cy = 4 # the number of the first proper reference cycle
else:
    dfm = df.loc[df['Cycle'] > 0] # starting from cycle 1 (0 is a dummy)
    cy = 2 # the number of the first proper reference cycle

dfm = dfm.groupby(['Cycle'])['Time(rel)',"d17O","d18O","Dp17O"].mean()
plt.scatter(dfm.iloc[:,0], dfm.iloc[:,1], marker = "*", s = 20, c = colBracketing, label = "Cycle avg", zorder = 5)

while cy < df['Cycle'].max():
    if (cy % 2) == 0:

        # Previous (reference) cycle
        x1 = df.loc[df['Cycle'] == cy - 1]["Time(rel)"].mean()
        y1 = df.loc[df['Cycle'] == cy - 1]["d17O"].mean()
        y1error = sem(df.loc[df['Cycle'] == cy - 1]["d17O"])

        # Following (reference) cycle
        x2 = df.loc[df['Cycle'] == cy + 1]["Time(rel)"].mean()
        y2 = df.loc[df['Cycle'] == cy + 1]["d17O"].mean()
        y2error = sem(df.loc[df['Cycle'] == cy + 1]["d17O"])

        # Interpolation based on the neighbouring reference cycles
        m = (y2 - y1) / (x2 - x1)
        b = y1 - m * x1

        # Values for the sample cycle
        xs = df.loc[df['Cycle'] == cy]["Time(rel)"].mean()
        ys = df.loc[df['Cycle'] == cy]["d17O"].mean()
        ysRef = m * xs + b
        
        a17Bracketing = (ys + 1000) / (ysRef + 1000)
        d17OBracketing = (d17OReference + 1000 ) * a17Bracketing - 1000
        bracketingResults.append(d17OBracketing)
        bracketingCycles.append(cy)
        
        # Only plot bracketing data if we need it
        if polynomial == "100":
            plt.plot([x1, x2], [y1, y2], linestyle = 'dotted', color = colBracketing, linewidth=1.2, dash_capstyle = "round", zorder = 5)
            plt.plot([xs, xs], [ys, ysRef], color = colBracketing, linewidth = 1.2, zorder = 5)
    cy = cy + 1

# We create the dfBracketingResults dataframe here
dfBracketingResults = pd.DataFrame(bracketingCycles, columns = ["Cycle"])
dfBracketingResults['d17O'] = bracketingResults

plt.ylabel("$\delta^{17}$O (‰, raw)")
plt.legend()

########## Fit für d18O ##########
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

# Polynomial fit calculations
y1 = np.array(df.loc[df['Type'] == "Ref"]['d18O'])
y2 = np.array(df.loc[df['Type'] == "Sam"]['d18O'])
comboY = np.append(y1, y2)

x1 = np.array(xRef)
x2 = np.array(xSam)
comboX = np.append(x1, x2)

# Quality control
if len(y1) != len(x1):
    raise(Exception('Unequal x1 and y1 data length'))
if len(y2) != len(x2):
    raise(Exception('Unequal x2 and y2 data length'))

# Some initial parameter values
initialParameters = np.array([1.0, 1.0, 1.0, 1.0, 1.0])

# curve fit the combined data to the combined function
fittedParameters, pcov = curve_fit(combinedFunction, comboX, comboY, initialParameters)

# values for display of fitted function
r0, s0, a1, a2, a3 = fittedParameters

y_fit_1 = function1(xFitData, r0, s0, a1, a2, a3)  # first data set, first equation
y_fit_2 = function2(xFitData, r0, s0, a1, a2, a3)  # second data set, second equation

# Calculate the alpha (Sam / Ref) value
a18Poly = (y_fit_2[0] + 1000) / (y_fit_1[0] + 1000)
d18OPolyRaw = (a18Poly - 1) * 1000

if polynomial != "100":
    plt.plot(xFitData, y_fit_1, color=colReference, zorder = -1)
    plt.plot(xFitData, y_fit_2, color=colSample, zorder = -1)

# Bracketing calculations
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
        y1 = df.loc[df['Cycle'] == cy - 1]["d18O"].mean()
        y1error = sem(df.loc[df['Cycle'] == cy-1]["d18O"])

        # Following (reference) cycle
        x2 = df.loc[df['Cycle'] == cy + 1]["Time(rel)"].mean()
        y2 = df.loc[df['Cycle'] == cy + 1]["d18O"].mean()
        y2error = sem(df.loc[df['Cycle'] == cy + 1]["d18O"])

        # Interpolation based on the neighbouring reference cycles
        m = (y2 - y1) / (x2 - x1)
        b = y1 - m * x1

        # Values for the sample cycle
        xs = df.loc[df['Cycle'] == cy]["Time(rel)"].mean()
        ys = df.loc[df['Cycle'] == cy]["d18O"].mean()
        ysRef = m * xs + b
        
        a18Bracketing = (ys + 1000) / (ysRef + 1000)
        d18OBracketing = (d18OReference + 1000 ) * a18Bracketing - 1000
        bracketingResults.append(d18OBracketing)

        # Only plot bracketing data if we need it
        if polynomial == "100":
            plt.plot([x1, x2], [y1, y2], linestyle = 'dotted', color = colBracketing, linewidth = 1.2, dash_capstyle = "round", zorder = 5)
            plt.plot([xs, xs], [ys, ysRef], color = colBracketing, linewidth = 1.2, zorder = 5)
    cy = cy + 1

dfBracketingResults['d18O'] = bracketingResults

plt.ylabel("$\delta^{18}$O (‰, raw)")
plt.legend()

##### Fit für D'17O ####
ax3 = plt.subplot(3, 1, 3)
plt.text(0.99, 0.99, 'C', size = 14, ha = 'right', va = 'top', transform = ax3.transAxes)

# Values referenced to the standard
d17ODummy = d17ODummyRaw + d17OReference + 1/1000 * d17ODummyRaw * d17OReference
d18ODummy = d18ODummyRaw + d18OReference + 1/1000 * d18ODummyRaw * d18OReference
yDummy = (1000 * np.log(d17ODummy/1000+1) - 0.528 * 1000 * np.log(d18ODummy/1000+1)) * 1000
plt.scatter(xDummy, yDummy, color = colDummy, marker = ".", label = "Dummy")

d17ORef = d17ORefRaw + d17OReference + 1/1000 * d17ORefRaw * d17OReference
d18ORef = d18ORefRaw + d18OReference + 1/1000 * d18ORefRaw * d18OReference
yRef = (1000 * np.log(d17ORef/1000+1) - 0.528 * 1000 * np.log(d18ORef/1000+1)) * 1000
plt.scatter(xRef, yRef, color = colReference, marker = ".", label = "Reference")

d17OSam = d17OSamRaw + d17OReference + 1/1000 * d17OSamRaw * d17OReference
d18OSam = d18OSamRaw + d18OReference + 1/1000 * d18OSamRaw * d18OReference
ySam = (1000 * np.log(d17OSam/1000+1) - 0.528 * 1000 * np.log(d18OSam/1000+1)) * 1000
plt.scatter(xSam, ySam, color = colSample, marker = ".", label = "Sample")

# Polynomial fit calculations
y1 = np.array(yRef)
y2 = np.array(ySam)
comboY = np.append(y1, y2)

x1 = np.array(xRef)
x2 = np.array(xSam)
comboX = np.append(x1, x2)

# Quality check
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
    plt.plot(xFitData, y_fit_1, color=colReference, zorder = -1)
    plt.plot(xFitData, y_fit_2, color=colSample, zorder = -1)

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

# Sample-standard bracketing
bracketingResults = []
bracketingTime = []
bracketingYs = []

plt.scatter(dfm.iloc[:,0], dfm.iloc[:,3]+ Dp17OReference * 1000, marker = "*", s = 20, c=colBracketing, label = "Cycle avg", zorder = 5)

if "air" in samID.lower():
    cy = 4
else:
    cy = 2

while cy < df['Cycle'].max():
    if (cy % 2) == 0:

        # Previous (reference) cycle
        x1 = df.loc[df['Cycle'] == cy - 1]["Time(rel)"].mean()
        y1 = df.loc[df['Cycle'] == cy - 1]["Dp17O"].mean() + Dp17OReference * 1000
        y1error = sem(df.loc[df['Cycle'] == cy - 1]["Dp17O"])

        # Following (reference) cycle
        x2 = df.loc[df['Cycle'] == cy + 1]["Time(rel)"].mean()
        y2 = df.loc[df['Cycle'] == cy + 1]["Dp17O"].mean() + Dp17OReference * 1000
        y2error = sem(df.loc[df['Cycle'] == cy + 1]["Dp17O"])

        # Interpolation based on the neighbouring reference cycles
        m = (y2 - y1) / (x2 - x1)
        b = y1 - m * x1

        # Values for the sample cycle
        xs = df.loc[df['Cycle'] == cy]["Time(rel)"].mean()
        ys = df.loc[df['Cycle'] == cy]["Dp17O"].mean() + Dp17OReference * 1000
        ysRef = m * xs + b

        bracketingCycles.append(cy)
        bracketingResults.append(ys - ysRef + Dp17OReference * 1000)
        bracketingTime.append(xs)
        bracketingYs.append(ys)

        if polynomial == "100":
            plt.plot([x1, x2], [y1, y2], linestyle = 'dotted', color = colBracketing, linewidth = 1.2, dash_capstyle = "round", zorder = 5)
            plt.plot([xs, xs], [ys, ysRef], color = colBracketing, linewidth = 1.2, zorder = 5)
    cy = cy + 1

dfBracketingResults['Dp17O'] = bracketingResults

# Drop rows where something is missing, This occurs when a cycle is skipped, e.g., 230118_084902_heavyVsRef
dfBracketingResults = dfBracketingResults.dropna()

# Outlier test based on a modified z-score
# Calculate modified z-score based on Iglewicz and Hoaglin 1993
median = np.median(dfBracketingResults['Dp17O'])
diff = (dfBracketingResults['Dp17O'] - median)
mad = np.median(np.absolute(diff))
modified_z_score = 0.6745 * diff / mad
dfBracketingResults['z_score'] = stats.zscore(dfBracketingResults['Dp17O']) # just for information
dfBracketingResults['IH_score'] = modified_z_score

# Mark outlier cycles on the plot
outlierPlot = pd.DataFrame(bracketingTime, columns = ["Time"])
outlierPlot['D17O'] = bracketingYs
outlierPlot['IH_score'] = modified_z_score
nIHOutliers = outlierPlot.loc[outlierPlot['IH_score'].abs() >= 5].shape[0]
outlierPlot = outlierPlot.loc[outlierPlot['IH_score'].abs() >= 5]

OutLab = "No outliers"
if nIHOutliers > 0 and polynomial == "100":
    OutLab = "Outlier (N: " + str(nIHOutliers) +")"
    plt.scatter(outlierPlot['Time'],  outlierPlot['D17O'], marker = "*", s = 20, c = "C4", label = OutLab, zorder = 6)
    if nIHOutliers == 1 :
        OutLab = str(nIHOutliers) + " outlier cycle"
    else:
        OutLab = str(nIHOutliers) + " outlier cycles"

# Export bracketing data to a file, including outliers
dfBracketingResults.to_excel(excel_writer=folder + "bracketingResults.xlsx", header = True, index = False)

# Final bracketing results, excluding outliers
dfBracketingResults = dfBracketingResults.loc[dfBracketingResults['IH_score'].abs() < 5]
d18O_SRB = round(np.mean(dfBracketingResults['d18O']),3)
d17O_SRB = round(np.mean(dfBracketingResults['d17O']),3)
D17Op_SRB = round(np.mean(dfBracketingResults['Dp17O']),1)
D17Op_SRB_error = round(sem(dfBracketingResults['Dp17O']),1)

# Final polynomial results
d17OPolyFinal = round(d17OPolyRaw + d17OReference + 1/1000 * d17OPolyRaw * d17OReference, 3)
d18OPolyFinal = round(d18OPolyRaw + d18OReference + 1/1000 * d18OPolyRaw * d18OReference, 3)
Dp17OPolyFinal = round((1000 * np.log(d17OPolyFinal / 1000 + 1) - 0.528 * 1000 * np.log(d18OPolyFinal / 1000 + 1)) * 1000, 1)

# Write evaluated data into the figure title
first_line = samID # + "  " + measurement_date.strftime("%m/%d/%Y")
if polynomial == "100":
    second_line = str("\n" + "Results from bracketing: " + "$\delta{}^{17}$O: "+ str(d17O_SRB) + "‰, $\delta{}^{18}$O: " + str(d18O_SRB) + "‰, $\Delta{}^{\prime 17}$O: " + str(D17Op_SRB) + " ± " + str(D17Op_SRB_error) + " ppm, " + OutLab)
else:
    second_line = str("\n" + "Results from " +polynomial+ "nd order polynomial fit: " + "$\delta{}^{17}$O: "+ str(d17OPolyFinal) + "‰, $\delta{}^{18}$O: " + str(d18OPolyFinal) + "‰, $\Delta{}^{\prime 17}$O: " + str(Dp17OPolyFinal) + " ± " + str(round(Dp17OPolyErr, 1)) +" ppm")
third_line = str("\n(Reference gas: " +"$\delta{}^{17}$O: "+ str(d17OReference) + "‰, " + "$\delta{}^{18}$O: " + str(d18OReference) + "‰, " + "$\Delta{}^{\prime 17}$O: " + str(round(Dp17OReference*1000,1)) + " ppm)")
plt.title(first_line + second_line + third_line)
plt.ylabel("$\Delta^{\prime 17}$O (ppm)")
plt.xlabel("Relative time (s)")
plt.legend()

plt.tight_layout()
plt.savefig(str(folder + "FitPlot.svg"))
plt.savefig(str(folder +  "FitPlot.png"), dpi = 300)

##### Bracketing trend ####
if (polynomial == "100"):
    plt.rcParams["figure.figsize"] = (6, 3)
    plt.rcParams["legend.loc"] = "upper left"
    plt.rcParams.update({'font.size': 6})
    plt.figure(2)

    plt.scatter(dfBracketingResults['Cycle']/2, dfBracketingResults['Dp17O'], marker = "*", s = 20, c=colSample, label = "Cycle avg", zorder = 5)
    plt.plot(dfBracketingResults['Cycle']/2, dfBracketingResults['Dp17O'], color = colSample, linewidth = 1)
    plt.axhline(D17Op_SRB, c = colBracketing, zorder = -1, linewidth = 1.2, label = "mean")
    plt.axhline(D17Op_SRB-D17Op_SRB_error, c = colBracketing,linestyle = 'dotted', dash_capstyle = "round", zorder = -1,linewidth = 1.2, label = "sem")
    plt.axhline(D17Op_SRB+D17Op_SRB_error, c = colBracketing, linestyle = 'dotted', dash_capstyle = "round", zorder = -1,linewidth = 1.2)
    # plt.axhline(D17Op_SRB-D17Op_SRB_error*t.ppf(q=1-(1-0.68)/2, df = np.max(dfBracketingResults['Cycle']/2) ), c = "#cacaca",linestyle = 'dotted', dash_capstyle = "round", zorder = -1,linewidth = 1.2)
    # plt.axhline(D17Op_SRB+D17Op_SRB_error*t.ppf(q=1-(1-0.68)/2, df = np.max(dfBracketingResults['Cycle']/2) ), c = "#cacaca",linestyle = 'dotted', dash_capstyle = "round", zorder = -1,linewidth = 1.2)
    plt.ylabel("$\Delta^{\prime 17}$O (ppm)")
    plt.xlabel("Sample cycle")
    plt.xticks([1,2,3,4,5,6,7,8,9,10])
    plt.legend()
    plt.tight_layout()
    plt.savefig(str(folder + "bracketingResults.svg"))
    plt.savefig(str(folder +  "bracketingResults.png"), dpi = 300)


# Print out the values. This is what the evaluateData.php reads out
if polynomial != '100':
    print(sys.argv[1], d17OPolyFinal, d18OPolyFinal, Dp17OPolyFinal, Dp17OPolyErr, d17OReference, d18OReference, polynomial, pCO2Ref, pCO2Sam, PCellRef, PCellSam)
else:
    print(sys.argv[1], d17O_SRB, d18O_SRB, D17Op_SRB, D17Op_SRB_error, d17OReference, d18OReference, polynomial, pCO2Ref, pCO2Sam, PCellRef, PCellSam)
