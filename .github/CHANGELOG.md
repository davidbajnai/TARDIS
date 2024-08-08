# version 3.0.9000

## Hardware
* Replaced the Raspberry Pi 4 with a mini computer running Ubuntu.
    - This change did not significantly enhance performance but did improve security and the reliability of the hard drive.
* Removed the room temperature and humidity sensors

## Software
* Restructured the html folder to follow the model–view–controller pattern
* Updated the evaluateData.php to use SSH to transfer files
* Arduino now sends seonsor status as a JSON string
* Writing the logFile is done using a JSON string
* Removed room temperature and room humidity values from front panel and logFile
* Relative humidity is shown on the front panel
* Additional minor improvements and bug fixes
* Background fitting suspended before evacuating the cell (2024-08-08, BD)
