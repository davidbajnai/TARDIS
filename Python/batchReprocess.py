import os
import pandas as pd
import numpy as np
import re
from datetime import datetime
from alive_progress import alive_bar

from selenium import webdriver
driver = webdriver.Chrome()
driver.set_window_size(1700, 400)

############ EDIT HERE ############
# Filter samples based on measurement date
# afterDate = datetime(1946,12,18)
# beforeDate = datetime(2022,11,18,11) # since this, we measured multiple cycles for bracketing
afterDate = datetime(2022,11,28,15)
beforeDate = datetime(2022,12,18,11)

# Create a dataframe from the subfolder names in the Results folder
folders = os.listdir('/var/www/html/Results/')
folders = pd.DataFrame(folders, columns = ["column"]).astype('str')

# Make the dataframe workable
results = folders.column.str.split("_", n = 2, expand = True)
results.columns = ["Date", "Time", "SampleName"]
results["RealDate"] = results["Date"] + results["Time"]
# results.loc[:,["RealDate"]].to_csv('/var/www/html/recentlyReprocessedFiles.csv', index = False, header=False, mode = "a")
results["RealDate"] = pd.to_datetime(results["RealDate"], format = '%y%m%d%H%M%S')
results = results.astype({'Date':'int'})

############ EDIT HERE ############
# Filter sample names according to measurement date
resultsFiltered = results[results.RealDate >= afterDate] # measured after
resultsFiltered = resultsFiltered[resultsFiltered.RealDate <= beforeDate] # measured before
resultsFiltered = resultsFiltered[resultsFiltered["SampleName"].str.contains("SK-")] # includes
resultsFiltered = resultsFiltered[~resultsFiltered["SampleName"].str.contains("refill")] # doesn't include
resultsFiltered = resultsFiltered[~resultsFiltered["SampleName"].str.contains("test")] # doesn't include
resultsFiltered = resultsFiltered[~resultsFiltered["SampleName"].str.contains("Air")] # doesn't include
resultsFiltered = resultsFiltered.sort_values(by=["RealDate"])

# Determine the polynomial (2nd order or bracketing) based on measurement date
resultsFiltered["Polynomial"] = np.where(resultsFiltered["RealDate"]<datetime(2022,11,18,11),"2", "100")

# Add bracketing reprocess php link to the dataframe
resultsFiltered["SampleID"] = resultsFiltered["Date"].astype("str") + "_"+ resultsFiltered["Time"] + "_"+ resultsFiltered["SampleName"]
resultsFiltered["Link"] = "http://192.168.1.242/evaluateData.php?sampleName=" + resultsFiltered["Date"].astype("str") +"_"+ resultsFiltered["Time"] +"_"+ resultsFiltered["SampleName"] + "&polynomial=" + resultsFiltered["Polynomial"]
resultsFiltered["Success"] = ""

# Calculate thow lon the reprocess would take and ask whether to proceed
for index, row in resultsFiltered.iterrows():
        print(str(row["Date"])+"_"+ row["Time"] +"_"+ row["SampleName"])
print("Let's reprocess " + str(len(resultsFiltered)) + " samples. This monumental work will take ca. " + str( round(len(resultsFiltered)*47/60) ) + " minutes.")
proceed = input("Do you wish to proceed (Y)?")

# This is the reprocess loop
if proceed.lower() == "y":
    print("Fine! Starting reprocessing. I will work hard while you are sipping coffee...")
    total = round(len(resultsFiltered))
    with alive_bar(total, stats = False, spinner = None) as bar:
        for index, row in resultsFiltered.iterrows():

            driver.get(row["Link"]) # This waits until the page is loaded, i.e., the reprocess is complete

            if re.search(r"'dfAll' is not defined", driver.page_source):
                resultsFiltered.loc[index, "Success"] = "__Empty folder__"
            elif re.search(r"Traceback", driver.page_source):
                resultsFiltered.loc[index, "Success"] = "___Py Problem___"
            else:
                resultsFiltered.loc[index, "Success"] = "_______OK_______"
            bar()
    # Save the list of the reprocessed samples
    resultsFiltered.loc[:,["SampleID","Success","Link"]].to_csv('/var/www/html/recentlyReprocessedFiles.csv', index = False, header=False, mode = "a")
    print("Finished reprocessing. I'm exhausted.")
else:
    print("Alright, I am not going to do anything.")