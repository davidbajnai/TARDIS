# version 3.0.9000

## Hardware
* Replaced the Raspberry Pi 4 with a mini computer running Ubuntu
    - This change did not significantly enhance performance but did improve security and the reliability of the hard drive
* Removed the room temperature and humidity sensors
* Optimized the tubing to reduce dead volume
* Exchanged the PID controlled fans

## Software
* Restructured the html folder to follow the model–view–controller pattern
* Optimized the evaluateData.py script
    - Removed redundant calcualtions
    - New variables are now calculated and exported, including cell temperature and some uncertainties
    - Removed the `bracketingResults.png` file. The bracketing results are now included in the `FitPlot.png` file.
    - The evaluated data is now exported as a JSON string
* Updated the evaluateData.php
    - It now uses SSH to transfer files
    - The data is sent to the server as a JSON string
    - The script copies the SPE files from the TILDAS PC to the server
* Updated the Arduino code
    - The Arduino now sends the sensor status as a JSON string
    - Minor perfromance improvements
    - From 2024-09-24 on, all pressure values are exported as Torr
* Writing the logFile is done using a JSON string
* Removed room temperature and room humidity values from front panel and logFile
* Relative humidity is shown on the front panel
* Additional minor improvements and bug fixes
* Background fitting suspended before evacuating the cell (2024-08-08, BD)
