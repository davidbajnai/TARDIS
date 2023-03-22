<?php

// This script is used to:
// log the status (temp, bellow compression, vacuum, etc.) of the inlet system

date_default_timezone_set('CET');

$sampleName = $_POST['sampleName'];
$logData = $_POST['logData']; // Comma separated string
$folderName = $_POST['folderName'];

// Do not log data for refills
if (str_contains($sampleName, "refill")) {
    exit();
}

// Create a logfile if it doesnt exist yet
if (file_exists($folderName . "/logFile.csv") === false) {
    // Name the header row
    file_put_contents($folderName . "/logFile.csv", "sampleName,Time(abs),boxTemperature,boxSetpoint,boxHumidity,percentageX,percentageY,percentageZ,pressureX,pressureY,pressureA,vacuum,fanSpeed,roomTemperature,roomHumidity\n", FILE_APPEND  | LOCK_EX);
}

// Add data to the logfile
foreach ($logData as $row) {
    file_put_contents($folderName . "/logFile.csv", $sampleName . "," . trim(implode(",", $row)) . "\n", FILE_APPEND  | LOCK_EX);
}

echo "Data written to logfile at " . date("H:i:s");