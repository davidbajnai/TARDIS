import os
from datetime import datetime
import pandas as pd

# Specify the global measurement interval here
afterDate = datetime(2021,11,18,11)
beforeDate = datetime(2023,11,1,1)

# Specify the sample names to export here
samples = ["MVCH","MB1551"]

# Create a dataframe from the subfolder names in the Results folder
folders = os.listdir('/var/www/html/Results/')
folders = pd.DataFrame(folders, columns = ["FolderName"]).astype('str')

# Make the dataframe workable
folders[["Date", "Time", "SampleName"]] = folders.FolderName.str.split("_", n = 2, expand = True)
folders["DateTime"] = folders["Date"] + ", " + folders["Time"]
folders["DateTime"] = pd.to_datetime(folders["DateTime"], format = '%y%m%d, %H%M%S')
folders = folders.drop(["Date","Time"], axis=1)

# Filter sample names according to measurement date
folders = folders[folders.DateTime >= afterDate] # measured after
folders = folders[folders.DateTime <= beforeDate] # measured before
folders = folders[folders["SampleName"].str.contains('|'.join(samples))] # includes

# for index, row in folders.iterrows():
listFolders = " ".join(folders.FolderName)
# print(listFolders)

os.system("zip -r supplementary " + listFolders)