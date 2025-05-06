"""
This script is used to reprocess samples in the Results folder.
It filters samples either based on defined measurement dates
or based on a list of sample names from a .CSV file.
The sample names can be filtered to exclude certain patterns.
"""

# >>>>>>>>>>>>>>>>>>>>>>>>>>>>> IMPORT PACKAGES <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
import os
import pandas as pd
import re
from datetime import datetime
from tqdm import tqdm
import subprocess

# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> SETTINGS <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
############ EDIT HERE ############
# Filter samples based on measurement date
afterDate = datetime(2025, 5, 5, 20)
beforeDate = datetime(2025, 10, 29)
# Create a dataframe from the subfolder names in the Results folder
folders = os.listdir('/var/www/html/data/Results')
folders = pd.DataFrame(folders, columns=["column"]).astype('str')

# Alternatively read a list of sample names from a .CSV file
# folders = pd.read_csv("/var/www/html/controller/python/filesToReprocess.csv",
#                       usecols=[0], header=None, names=["column"], dtype=str)

# Make the dataframe workable
results = folders.column.str.split("_", n=2, expand=True)
results.columns = ["Date", "Time", "SampleName"]
results["RealDate"] = results["Date"] + results["Time"]
results["RealDate"] = pd.to_datetime(results["RealDate"], format='%y%m%d%H%M%S')
results = results.astype({'Date': 'int'})
resultsFiltered = results[results.RealDate >= afterDate]  # measured after
resultsFiltered = resultsFiltered[resultsFiltered.RealDate <= beforeDate]  # measured before
resultsFiltered = resultsFiltered.sort_values(by=["RealDate"])

############ EDIT HERE ############
# Filter sample names according to measurement date
# resultsFiltered = resultsFiltered[resultsFiltered["SampleName"].str.contains("DH11")]  # includes
resultsFiltered = resultsFiltered[~resultsFiltered["SampleName"].str.contains("test")]  # doesn't include
resultsFiltered = resultsFiltered[~resultsFiltered["SampleName"].str.contains("Air")]  # doesn't include
resultsFiltered = resultsFiltered[~resultsFiltered["SampleName"].str.contains("air")]  # doesn't include
resultsFiltered = resultsFiltered[~resultsFiltered["SampleName"].str.contains("scaling")]  # doesn't include


# Add bracketing reprocess PHP link to the dataframe
resultsFiltered["SampleID"] = resultsFiltered["Date"].astype("str") + "_" + resultsFiltered["Time"] + "_" + resultsFiltered["SampleName"]
resultsFiltered["Link"] = "http://localhost/controller/php/evaluateData.php?sampleName=" + resultsFiltered["Date"].astype("str") + "_" + resultsFiltered["Time"] + "_" + resultsFiltered["SampleName"]
resultsFiltered["Success"] = ""

# Calculate how long the reprocess would take and ask permission to proceed
for index, row in resultsFiltered.iterrows():
    print(str(row["Date"]) + "_" + row["Time"] + "_" + row["SampleName"])
number_of_samples = len(resultsFiltered)
print(f"Let's reprocess {number_of_samples} samples! This monumental work will take ca. {(number_of_samples*16.47/60):.0f} minutes.")
proceed = input("Do you wish to proceed (Y)?")

# This is the reprocess loop
if proceed.lower() == "y":
    try:
        print("Fine! Starting reprocessing. I will work hard while you are sipping coffee...")
        total = len(resultsFiltered)
        for index, row in tqdm(resultsFiltered.iterrows(), total=total):

            tqdm.write(f"Currently working on {row['SampleID']}")

            # Run the PHP script to copy files
            subprocess.run(["php", "/var/www/html/controller/php/copyFiles.php", row["SampleID"]])
            subprocess.run(["/var/www/html/controller/shell/deleteFiles.sh", row["SampleID"]])

            curl_command = ["curl", "-x", "", row["Link"]]
            completed_process = subprocess.run(curl_command, capture_output=True, text=True)
            page_source = completed_process.stdout

            if re.search(r"'dfAll' is not defined", page_source):
                resultsFiltered.at[index, "Success"] = "__Empty folder__"
            elif re.search(r"Traceback", page_source):
                resultsFiltered.at[index, "Success"] = "___Py Problem___"
            elif re.search(r"Discard", page_source):
                resultsFiltered.at[index, "Success"] = "___Discarded____"
            else:
                resultsFiltered.at[index, "Success"] = "_______OK_______"

            # Append the row to CSV
            resultsFiltered.loc[[index], ["SampleID", "Success", "Link"]].to_csv(
                '/var/www/html/controller/python/recentlyReprocessedFiles.csv',
                index=False, header=False, mode="a"
            )

        print("Finished reprocessing. I'm exhausted.")

    except KeyboardInterrupt:
        print("\nFine, I will stop now. I love wasting my time.")

else:
    print("Alright, I am not going to do anything.")