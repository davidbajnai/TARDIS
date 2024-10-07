# This script plots the TILDAS data and calculates the isotope ratios

#################################################################
######################## Import libraries #######################
#################################################################
import os
os.environ['MPLCONFIGDIR'] = "/var/www/html/controller/python"
os.chdir(os.path.dirname(os.path.realpath(__file__)))
from os.path import exists

import warnings
warnings.filterwarnings('ignore')

import sys
import json
import numpy as np
import pandas as pd

from datetime import datetime

from scipy import stats
from scipy.stats import sem

from matplotlib.colors import LinearSegmentedColormap
import matplotlib.pyplot as plt
import matplotlib as mpl

#################################################################
####################### Figure parameters #######################
#################################################################

plt.rcParams.update({'font.size': 6})
plt.rcParams["legend.loc"] = "upper left"
plt.rcParams["savefig.dpi"] = 300
plt.rcParams["savefig.bbox"] = "tight"
plt.rcParams['savefig.transparent'] = False
plt.rcParams['mathtext.default'] = 'regular'

#################################################################
####################### Define functions ########################
#################################################################

def prime(delta):
    return 1000 * np.log(delta/1000 + 1)


def unprime(deltaprime):
    return (np.exp(deltaprime/1000) - 1) * 1000


def Dp17O(d17O, d18O):
    return (prime(d17O) - 0.528 * prime(d18O)) * 1000


#################################################################
####################### Import TILDAS data ######################
#################################################################

# Import measurement info
samID = str(sys.argv[1])  # Something like 230118_084902_heavyVsRef
folder = os.path.join("/var/www/html/data/Results/", samID)

# Calculate the start time of the measurement.
# The TILDAS and the loglife use Mac time, which is the number of seconds since 1904-01-01
measurementStarted = int(datetime.strptime(samID[0:13], '%y%m%d_%H%M%S').timestamp()-datetime(1904, 1, 1).timestamp())
dateTimeMeasured = str(datetime.strptime(samID[:6] + samID[7:13], "%y%m%d%H%M%S").strftime("%Y-%m-%d %H:%M:%S"))

strFiles = []
for file in os.listdir(folder):
    if file.endswith(".str"):
        strFiles.append(file)
strFiles.sort()

# Pattern for the measurements
if "air" in samID.lower():
    # Air measurements start with two Ref dummies (cy 0 and 3) and two air dummies (cy 1, 3 and, 4)
    pattern = ["Dummy"] * 5 + ["Ref", "Sam"] * 20
else:
    # Regular measurements start with a single Ref dummy (cy 0)
    pattern = ["Dummy"] + ["Ref", "Sam"] * 20

# Read all data files and combine them into one dataframe
i = 0
for file in strFiles:
    baseName = file[:-4]
    # The .str files contain the isotopologue mixing ratios
    dfstr = pd.read_csv(os.path.join(folder, baseName + ".str"), names=["Time(abs)", "I627", "I628", "I626", "CO2"], delimiter=" ", skiprows=1, index_col=False)
    
    # The .stc files contain the cell temperature, pressure, etc. data
    dfstc = pd.read_csv(os.path.join(folder, baseName + ".stc"), delimiter=",", skiprows=1)
    dfstc.columns = dfstc.columns.str.strip()
    
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
        dfAll = pd.concat([dfAll, df], ignore_index=True)
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
df.to_excel(os.path.join(folder, "allData.xlsx"), index=False)

# Get the list of the SPI files and copy the list into a CSV file
if "SPEFile" in df.columns:
    df["SPEFile"] = df["SPEFile"].str.replace(r'C:\\TDLWintel', '/mnt/TILDAS_PC', regex=True).str.replace(r'\\', '/', regex=True)
    df["SPEFile"].dropna().to_csv(os.path.join(folder, "list_of_SPE_files.csv"), index=False, header=False)

#################################################################
################### Read and reformat logfile ###################
#################################################################

# Necessary to maintain compatibility with the old logfiles

dfLogFile = pd.read_csv(os.path.join(folder, "logFile.csv"))

# Drop empty columns and rows with missing values
dfLogFile = dfLogFile.dropna(how='all', axis=1)
dfLogFile = dfLogFile.dropna(how='any', axis=0)

# Rename the columns
new_column_names = {
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
    "pressureA": "pressureZ",
    "edwards": "vacuum",
    "fanSpeed": "fanSpeed",
    "RoomT": "roomTemperature",
    "RoomH": "roomHumidity",
    "RoomP": "roomPressure"
}
dfLogFile = dfLogFile.rename(columns=new_column_names)

if 'Time(rel)' not in dfLogFile.columns:
    # Calculate the relative time used for plotting
    dfLogFile["Time(rel)"] = dfLogFile["Time(abs)"] - measurementStarted

    # Compensate for summer time / winter time, if necessary
    # A mismatch between TILDAS and logFile data can remain if the clocks were not synchronized
    if (dfLogFile["Time(rel)"].iat[0] < -3000):
        dfLogFile["Time(rel)"] = dfLogFile["Time(rel)"] + 3600

# Determine the pressure unit (Torr is used after 2025-09-01)
if "Time(abs)" in dfLogFile.columns:
    time0 = datetime.fromtimestamp(dfLogFile["Time(abs)"].iat[0]-2082844800-3600)
    if time0 > datetime(2025, 9, 1):
        pressure_unit = "Torr"
    else:
        pressure_unit = "mbar"

# overwrite the original CSV file with the updated version
dfLogFile.to_csv(os.path.join(folder, "logFile.csv"), index=False)

# Calculate the measurement duration
seconds = dfLogFile["Time(rel)"].iat[-1]
measurement_duration = str("%d:%02d:%02d" % (seconds % (24 * 3600) // 3600, seconds % 3600 // 60, seconds % 3600 % 60))


#################################################################
###################### Figure 1 – Raw data ######################
#################################################################

# Plot parameters
plt.rcParams["figure.figsize"] = (6, 18)
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

fig, (ax1, ax2, ax3, ax4, ax5, ax6, ax7, ax8, ax9, ax10) = plt.subplots(10, 1, sharex=True)
ax1.set_title(f"{samID}\nMeasurement duration: {measurement_duration}")

# Subplot A: d18O vs time
TILDAS_time = df["Time(rel)"]
y = df["d18O_raw"]
scat = ax1.scatter(TILDAS_time, y, marker = ".", c = df.Type.astype('category').cat.codes, cmap=cmap)
ax1.text(0.99, 0.98, 'A',
         size=14, ha='right', va='top', transform=ax1.transAxes,
         bbox=dict(fc='white', ec="none", pad=1, alpha=0.5))
ax1.legend(handles=scat.legend_elements()[0], labels=data_names, markerscale = 0.5)
ax1.set_ylabel("$\delta^{18}$O (‰, raw)")

# Subplot B: D17O vs time
y = df['Dp17O_raw']
ax2.scatter(TILDAS_time, y, marker=".", color = df['Type'].map(data_colors))
ax2.set_ylabel("$\Delta\prime^{17}$O (ppm, raw)")
ax2.text(0.99, 0.98, 'B',
         size=14, ha='right', va='top', transform=ax2.transAxes,
         bbox=dict(fc='white', ec="none", pad=1, alpha=0.5))

# Subplot C: mixing ratios (pCO2) vs time
pCO2 = df['I626'] / 1000
ax3.scatter(TILDAS_time, pCO2, marker=".", color = df['Type'].map(data_colors))

if "air" in samID.lower():
    # Air measurements start with two Ref dummy (cy 0 and 1) and a sample dummy (cy 2)
    pCO2Sam = df.loc[(df["Cycle"] > 2) & (df["Cycle"] % 2 == 0), ['I626']]/1000
    pCO2Ref = df.loc[(df["Cycle"] > 1) & (df["Cycle"] % 2 != 0), ['I626']]/1000
else:
    # Regular measurements start with a single Ref dummy (cy 0)
    pCO2Sam = df.loc[(df["Cycle"] > 0) & (df["Cycle"] % 2 == 0), ['I626']]/1000
    pCO2Ref = df.loc[(df["Cycle"] > 0) & (df["Cycle"] % 2 != 0), ['I626']]/1000

pCO2Sam_error = float(np.round(np.std(pCO2Sam), 1))
pCO2Sam = float(np.round(np.mean(pCO2Sam), 1))
pCO2Ref_error = float(np.round(np.std(pCO2Ref), 1))
pCO2Ref = float(np.round(np.mean(pCO2Ref), 1))

ax3.text(0.01, 0.02, f"{pCO2Sam}±{pCO2Sam_error} ppmv", size = 8, color = colSample, ha = 'left', va = 'bottom', transform = ax3.transAxes, bbox = dict(fc = 'white', ec = "none", pad = 1, alpha = 0.5))
ax3.text(0.01, 0.12, f"{pCO2Ref}±{pCO2Ref_error} ppmv", size = 8, color = colReference, ha = 'left', va = 'bottom', transform = ax3.transAxes, bbox = dict(fc = 'white', ec = "none", pad = 1, alpha = 0.5))
ax3.set_ylabel("$\mathit{p}$CO$_2$ (ppmv, cell)")
ax3.text(0.99, 0.98, 'C',
         size=14, ha='right', va='top', transform=ax3.transAxes,
         bbox=dict(fc='white', ec="none", pad=1, alpha=0.5))

# Subplot D: Cell pressure vs time
y = df['Praw']
ax4.scatter(TILDAS_time, y, marker=".", color = df['Type'].map(data_colors))
PCellSam = float(df.loc[(df["Cycle"] > 0) & (df["Cycle"] % 2 == 0), ['Praw']].mean().round(3))
PCellSam_error = float(df.loc[(df["Cycle"] > 0) & (df["Cycle"] % 2 == 0), ['Praw']].std().round(3))
PCellRef = float(df.loc[(df["Cycle"] > 0) & (df["Cycle"] % 2 != 0) ,['Praw']].mean().round(3))
PCellRef_error = float(df.loc[(df["Cycle"] > 0) & (df["Cycle"] % 2 != 0) ,['Praw']].std().round(3))
ax4.text(0.01, 0.02, f"{PCellSam}±{PCellSam_error} Torr", size = 8, color = colSample, ha = 'left', va = 'bottom', transform = ax4.transAxes, bbox = dict(fc = 'white', ec = "none", pad = 1, alpha = 0.5))
ax4.text(0.01, 0.12, f"{PCellRef}±{PCellRef_error} Torr", size = 8, color = colReference, ha = 'left', va = 'bottom', transform = ax4.transAxes, bbox = dict(fc = 'white', ec = "none", pad = 1, alpha = 0.5))
ax4.set_ylabel("Pressure (Torr, cell)")
ax4.text(0.99, 0.98, 'D',
         size=14, ha='right', va='top', transform=ax4.transAxes,
         bbox=dict(fc='white', ec="none", pad=1, alpha=0.5))

# Subplot E: Cell temperature
TCell = df['Traw'] - 273.15
ax5.scatter(TILDAS_time, TCell, marker=".",color = df['Type'].map(data_colors))
ax5.set_ylabel("Temperature (°C, cell)")
TCell_error = np.round(np.std(TCell), 3)
TCell = np.round(np.mean(TCell), 3)
ax5.text(0.01, 0.02, f"{TCell}±{TCell_error} °C", size=8, color="black", ha = 'left', va = 'bottom', transform=ax5.transAxes, bbox=dict(fc='white', ec="none", pad=1,alpha=0.5))
ax5.text(0.99, 0.98, 'E',
         size=14, ha='right', va='top', transform=ax5.transAxes,
         bbox=dict(fc='white', ec="none", pad=1, alpha=0.5))

# Subplot F: Coolant temperature and room temperature
TCoolant = df['Tref'] - 273.15
ax6.scatter(TILDAS_time, TCoolant, marker=".",color = df['Type'].map(data_colors))
ax6.set_ylabel("Temperature (°C, coolant)")
TCoolant_error = np.std(TCoolant)
TCoolant = np.mean(TCoolant)

if ('roomTemperature' in dfLogFile.columns):
    ax6b = ax6.twinx()
    ax6b.spines['right'].set_color('C1')
    x = dfLogFile["Time(rel)"]
    y = dfLogFile['roomTemperature']
    ax6b.plot(x, y, color = "C1")
    ax6b.set_ylabel("Temperature (°C, room)")
    mean = np.round(np.mean(y), 3)
    std = np.round(np.std(y), 3)
    labelRoomT = str(mean) + "±" + str(std) + " °C"
    ax6b.text(1 - 0.01, 0.02, labelRoomT, size=8, color="C1", ha = 'right', va = 'bottom', transform = ax6.transAxes, bbox=dict(fc='white', ec="none", pad=1,alpha=0.5))

ax6.text(0.01, 0.02, f"{TCoolant:.3f}±{TCoolant_error:.3f} °C", size=8, color="black", ha = 'left', va = 'bottom', transform = ax6.transAxes, bbox=dict(fc='white', ec="none", pad=1,alpha=0.5))
ax6.text(0.99, 0.98, 'F',
         size=14, ha='right', va='top', transform=ax6.transAxes,
         bbox=dict(fc='white', ec="none", pad=1, alpha=0.5))

# Subplot G: Box temperature vs time
if ('boxTemperature' in dfLogFile.columns):
    x = dfLogFile["Time(rel)"]
    y = dfLogFile['boxTemperature']
    ax7.plot(x, y, color="C0")
    ax7.set_ylabel("Temperature (°C, box)")
    mean = np.round(np.mean(y), 3)
    std = np.round(np.std(y), 3)
    labelTemp = str(mean) + "±" + str(std) + " °C"
    if ('boxSetpoint' in dfLogFile.columns):
        x = dfLogFile["Time(rel)"]
        y = dfLogFile['boxSetpoint']
        ax7.plot(x, y, color="C2")
        labelSP = str("SP: ") + str(dfLogFile['boxSetpoint'].iat[0]) + " °C"
    if ('fanSpeed' in dfLogFile.columns):
        ax7b = ax7.twinx()
        ax7b.spines['right'].set_color('C1')
        x = dfLogFile["Time(rel)"]
        y = dfLogFile['fanSpeed']
        ax7b.plot(x, y, color="C1")
        ax7b.set_ylabel("Fan speed (%)")
        ax7.text(0.01, 0.11, labelSP, size = 8, color = "C2", ha = 'left', va = 'bottom', transform = ax7.transAxes, bbox=dict(fc = 'white', ec = "none", pad = 1, alpha=0.5))
    ax7.text(0.01, 0.02, labelTemp, size = 8, color = "C0", ha = 'left', va = 'bottom', transform = ax7.transAxes, bbox=dict(fc = 'white', ec = "none", pad = 1, alpha=0.5))
ax7.text(0.99, 0.98, 'G',
         size=14, ha='right', va='top', transform=ax7.transAxes,
         bbox=dict(fc='white', ec="none", pad=1, alpha=0.5))

# Subplot H: X (reference) bellow expansion and pressure
if ('pressureX' in dfLogFile.columns):
    x = dfLogFile["Time(rel)"]
    y = dfLogFile['pressureX']
    ax8.plot(x, y)
    ax8.set_ylabel(f"Pressure ({pressure_unit}, X)")
    ax8b = ax8.twinx()
    ax8b.spines['right'].set_color('C1')
    y = dfLogFile['percentageX']
    ax8b.plot(x, y, color="C1")
    ax8b.set_ylabel("Bellow expansion (%, X)")
ax8.text(0.99, 0.98, 'H',
         size=14, ha='right', va='top',
         transform=ax8.transAxes, bbox=dict(fc='white', ec="none", pad=1, alpha=0.5))

# Subplot J: Y (sample) bellow expansion and pressure
if ('pressureY' in dfLogFile.columns):
    x = dfLogFile["Time(rel)"]
    y = dfLogFile['pressureY']
    ax9.plot(x, y)
    ax9.set_ylabel(f"Pressure ({pressure_unit}, Y)")
    ax9b = ax9.twinx()
    ax9b.spines['right'].set_color('C1')
    y = dfLogFile['percentageY']
    ax9b.plot(x, y, color="C1")
    ax9b.set_ylabel("Bellow expansion (%, Y)")
ax9.text(0.99, 0.98, 'I',
         size=14, ha='right', va='top',
         transform=ax9.transAxes, bbox=dict(fc='white', ec="none", pad=1, alpha=0.5))

# Subplot K: Z bellow
if all(col in dfLogFile.columns for col in ['pressureZ', 'percentageZ', 'Time(rel)']):
    x = dfLogFile["Time(rel)"]
    y = dfLogFile['pressureZ']
    ax10.plot(x, y)
    ax10.set_ylabel(f"Pressure ({pressure_unit}, Z)")
    ax10b = ax10.twinx()
    ax10b.spines['right'].set_color('C1')
    y = dfLogFile['percentageZ']
    ax10b.plot(x, y, color = "C1")
    ax10b.set_ylabel("Bellow expansion (%, Z)")
ax10.text(0.99, 0.98, 'J',
          size=14, ha='right', va='top',
          transform=ax10.transAxes, bbox=dict(fc='white', ec="none", pad=1, alpha=0.5))
ax10.set_xlabel("Relative time (s)")

plt.tight_layout()
plt.savefig(os.path.join(folder, "rawData.png"))


#################################################################
########################## Filter data ##########################
#################################################################

# Now filter data using the z-score (3-sigma criterion)
# The excel file includes all data, but only filtered data is used for the calculations and plots
df = df.loc[df['z_score'].abs() <= 3]

#################################################################
###################### Figure 2 – Fit data ######################
#################################################################

# Plot properties
plt.rcParams["figure.figsize"] = (6, 6)
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, sharex=True)


# Reference gas composition
d18OWorkingGas = 28.048
d17OWorkingGas = 14.621  # D'17O = -90 ppm
Dp17OWorkingGas = Dp17O(d17OWorkingGas, d18OWorkingGas)

# Make separate dataframes for Dummy, Reference, and Sample
dfRef = df.loc[df['Type'] == "Ref"]
dfSam = df.loc[df['Type'] == "Sam"]
dfDummy = df.loc[df['Type'] == "Dummy"]

######################### Plot A – d17O #########################

ax1.scatter(dfDummy["Time(rel)"], dfDummy["d17O_raw"],
            color=colDummy, marker=".", label="Dummy")

ax1.scatter(dfRef["Time(rel)"], dfRef["d17O_raw"],
            color=colReference, marker=".", label="Reference")

ax1.scatter(dfSam['Time(rel)'], dfSam["d17O_raw"],
            color=colSample, marker=".", label="Sample")

bracketingResults = []
bracketingCycles = []
bracketingTime = []

# New dataframe without the dummy cycles
if "air" in samID.lower():
    dfm = df.loc[df['Cycle'] > 2]
    cy = 4 # the number of the first proper reference cycle
else:
    dfm = df.loc[df['Cycle'] > 0]
    cy = 2 # the number of the first proper reference cycle

dfm = dfm.groupby(['Cycle'])[['Time(rel)', "d17O_raw", "d18O_raw", "Dp17O_raw"]].mean()
ax1.scatter(dfm.iloc[:, 0], dfm.iloc[:, 1],
            marker="*", s=20, c=colBracketing, label="Cycle avg")

while cy < df['Cycle'].max():
    if (cy % 2) == 0:

        # Previous (reference) cycle
        x1 = dfm.loc[cy - 1]["Time(rel)"]
        y1 = dfm.loc[cy - 1]["d17O_raw"]

        # Following (reference) cycle
        x2 = dfm.loc[cy + 1]["Time(rel)"]
        y2 = dfm.loc[cy + 1]["d17O_raw"]

        # Interpolation based on the neighbouring reference cycles
        m = (y2 - y1) / (x2 - x1)
        b = y1 - m * x1

        # Values for the sample cycle
        xs = dfm.loc[cy]["Time(rel)"]
        ys = dfm.loc[cy]["d17O_raw"]

        ysRef = m * xs + b

        a17Bracketing = (ys + 1000) / (ysRef + 1000)
        d17OBracketing = (d17OWorkingGas + 1000 ) * a17Bracketing - 1000
        bracketingResults.append(d17OBracketing)
        bracketingCycles.append(cy)

        bracketingTime.append(xs)

        ax1.plot([x1, x2], [y1, y2],
                 linestyle='dotted', color=colBracketing, linewidth=1.2, dash_capstyle="round")
        ax1.plot([xs, xs], [ys, ysRef],
                 color=colBracketing, linewidth=1.2)
    cy = cy + 1

# We create the dfBracketingResults dataframe here
dfBracketingResults = pd.DataFrame(bracketingCycles, columns = ["Cycle"])
dfBracketingResults['Time(rel)'] = bracketingTime
dfBracketingResults['d17O'] = bracketingResults

ax1.legend(loc="center left")
ax1.text(0.99, 0.99, 'A',
         size=14, ha='right', va='top', transform=ax1.transAxes,
         bbox=dict(fc='white', ec="none", pad=1, alpha=0.5))
ax1.set_ylabel("$\delta^{17}$O (‰, raw)")


######################### Plot B – d18O #########################

ax2.scatter(dfDummy["Time(rel)"], dfDummy["d18O_raw"],
            color=colDummy, marker=".", label="Dummy")

ax2.scatter(dfRef["Time(rel)"], dfRef["d18O_raw"],
            color=colReference, marker=".", label="Reference")

ax2.scatter(dfSam['Time(rel)'], dfSam["d18O_raw"],
            color=colSample, marker=".", label="Sample")

bracketingResults = []

ax2.scatter(dfm.iloc[:, 0], dfm.iloc[:, 2],
            marker="*", s=20, c=colBracketing, label="Cycle avg")

if "air" in samID.lower():
    cy = 4
else:
    cy = 2

while cy < df['Cycle'].max():
    if (cy % 2) == 0:

        # Previous (reference) cycle
        x1 = dfm.loc[cy - 1]["Time(rel)"]
        y1 = dfm.loc[cy - 1]["d18O_raw"]

        # Following (reference) cycle
        x2 = dfm.loc[cy + 1]["Time(rel)"]
        y2 = dfm.loc[cy + 1]["d18O_raw"]

        # Interpolation based on the neighbouring reference cycles
        m = (y2 - y1) / (x2 - x1)
        b = y1 - m * x1

        # Values for the sample cycle
        xs = dfm.loc[cy]["Time(rel)"]
        ys = dfm.loc[cy]["d18O_raw"]

        ysRef = m * xs + b
        
        a18Bracketing = (ys + 1000) / (ysRef + 1000)
        d18OBracketing = (d18OWorkingGas + 1000 ) * a18Bracketing - 1000
        bracketingResults.append(d18OBracketing)

        ax2.plot([x1, x2], [y1, y2],
                 linestyle='dotted', color=colBracketing, linewidth=1.2, dash_capstyle="round")
        ax2.plot([xs, xs], [ys, ysRef],
                 color=colBracketing, linewidth=1.2)
    cy = cy + 1

dfBracketingResults['d18O'] = bracketingResults

ax2.text(0.99, 0.99, 'B',
         size=14, ha='right', va='top', transform=ax2.transAxes,
         bbox=dict(fc='white', ec="none", pad=1, alpha=0.5))
ax2.set_ylabel("$\delta^{18}$O (‰, raw)")

######################## Plot C – Dp17O #########################

dfBracketingResults['Dp17O'] = Dp17O(dfBracketingResults['d17O'], dfBracketingResults['d18O'])

# Final bracketing results
d18O_SRB = round(np.mean(dfBracketingResults['d18O']), 3)
d18O_SRB_error = round(sem(dfBracketingResults['d18O']), 3)
d17O_SRB = round(np.mean(dfBracketingResults['d17O']), 3)
d17O_SRB_error = round(sem(dfBracketingResults['d17O']), 3)
D17Op_SRB = round(np.mean(dfBracketingResults['Dp17O']), 1)
D17Op_SRB_error = round(sem(dfBracketingResults['Dp17O']), 1)

ax3.scatter(dfBracketingResults['Time(rel)'], dfBracketingResults['Dp17O'],
            marker="*", s=20, c=colSample, label="Cycle avg", zorder=5)
ax3.plot(dfBracketingResults['Time(rel)'], dfBracketingResults['Dp17O'],
         color=colSample, linewidth=1)
ax3.axhline(D17Op_SRB,
            c=colBracketing, zorder=-1, linewidth=1.2, label="mean")
ax3.axhline(D17Op_SRB-D17Op_SRB_error,
            c=colBracketing, linestyle='dotted', dash_capstyle="round", zorder=-1, linewidth=1.2, label="sem")
ax3.axhline(D17Op_SRB+D17Op_SRB_error,
            c=colBracketing, linestyle='dotted', dash_capstyle="round", zorder=-1, linewidth=1.2)

# Write evaluated data into the figure title
ax1.set_title(f"{samID}\nEvaluated results: $\\delta^{{17}}$O = {d17O_SRB}±{d17O_SRB_error}‰, $\delta^{{18}}$O = {d18O_SRB}±{d18O_SRB_error}‰, $\\Delta\\prime^{{17}}$O = {D17Op_SRB}±{D17Op_SRB_error} ppm\nWorking reference gas: $\\delta^{{17}}$O = {d17OWorkingGas}‰, $\\delta^{{18}}$O = {d18OWorkingGas}‰, $\\Delta\\prime^{{17}}$O = {Dp17OWorkingGas:.1f} ppm")

ax3.legend()
ax3.text(0.99, 0.99, 'C',
         size=14, ha='right', va='top', transform=ax3.transAxes,
         bbox=dict(fc='white', ec="none", pad=1, alpha=0.5))
ax3.set_ylabel("$\Delta\prime^{17}$O (ppm, rel. working gas)")
ax3.set_xlabel("Relative time (s)")

plt.tight_layout()
plt.savefig(os.path.join(folder, "FitPlot.png"))

#####################################################################
# Send evaluated results to the PHP script
#####################################################################

output_data = {
    "SampleName": sys.argv[1],
    "dateTimeMeasured": dateTimeMeasured,
    "d17O": d17O_SRB,
    "d17OError": d17O_SRB_error,
    "d18O": d18O_SRB,
    "d18OError": d18O_SRB_error,
    "CapD17O": D17Op_SRB,
    "CapD17OError": D17Op_SRB_error,
    "d17Oreference": d17OWorkingGas,
    "d18Oreference": d18OWorkingGas,
    "pCO2Ref": pCO2Ref,
    "pCO2Ref_error": pCO2Ref_error,
    "pCO2Sam": pCO2Sam,
    "pCO2Sam_error": pCO2Sam_error,
    "PCellRef": PCellRef,
    "PCellRef_error": PCellRef_error,
    "PCellSam": PCellSam,
    "PCellSam_error": PCellSam_error,
    "TCell": TCell,
    "TCell_error": TCell_error,
}
print(json.dumps(output_data))