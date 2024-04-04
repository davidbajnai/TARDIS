# version 3.0.9000

## Hardware
* Replaced the Raspberry Pi 4 with a mini computer running Ubuntu
* Removed the room temperature and humidity sensors

## Software
* Restructured the html folder to follow the model–view–controller pattern
* Updated the evaluateData.php to use SSH to transfer files
* Arduino now sends status as a JSON string
* Writing the logFile is done using a JSON string
* Removed room temperature and room humidity values from front panel and logFile
* Relative humidity is shown on the front panel
* Additional minor improvments and bug fixes
