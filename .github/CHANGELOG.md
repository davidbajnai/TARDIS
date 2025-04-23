# version 3.0.9000

## Hardware
* Replaced the Raspberry Pi 4 with an Intel i5 computer running Ubuntu
    - This change did not significantly enhance performance but did improve security and the reliability of the hard drive
* Removed the room temperature and humidity sensors
* Optimized the tubing to reduce dead volume
* Exchanged the PID controlled fans
* Replaced the "A" Baratron with a mini-Baratron
* Added a new "D" pressure gauge
* The inlet system is connected with a KIEL device through a 1/8" capillary

## Software
* Restructured the html folder to follow the model–view–controller pattern
* All data transfers between the scripts and to the database are now performed using JSON strings.
* Changes to `evaluateData.py`:
    - Removed redundant calcualtions
    - New variables are now calculated and exported, including cell temperature and some uncertainties
    - Removed the `bracketingResults.png` file. The bracketing results are now included in the `FitPlot.png` file.
    - Information on mismatch in the analytical parameters is exported to the database
    - Measurement duration is calculated based on the total length of the TILDAS measurements instead based on the logfile
* Changes to `evaluateData.php`:
    - It now uses SSH to transfer files
    - The script copies the SPE files from the TILDAS PC to the server
* Changes to `serialComm.py`:
    - The script automatically detects the COM ports
* Changes to the Arduino code:
    - Perfromance improvements
    - From 2024-09-24 on, all pressure values are exported as Torr
* Various front panel updates
* Background fitting suspended before evacuating the cell
