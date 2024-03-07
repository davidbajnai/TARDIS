<?php

// This script is used to:
// log the status (temp, bellow compression, vacuum, etc.) of the inlet system

// Set CET or CEST timezone as appropriate (CET is used in winter, CEST in summer)
date_default_timezone_set('Europe/Berlin');


$sampleName = $_POST['sampleName'];
$logData = $_POST['logData']; // Comma separated string
$folderName = $_POST['folderName'];

$fileName = "../../". $folderName . "/logFile.csv";

// Do not log data for refills
if (str_contains($sampleName, "refill")) {
    exit();
}

// Create a logfile if it doesnt exist yet
if (file_exists($fileName) === false) {
    // Name the header row
    file_put_contents($fileName, "sampleName,Time(abs),boxTemperature,boxSetpoint,boxHumidity,percentageX,percentageY,percentageZ,pressureX,pressureY,pressureA,vacuum,fanSpeed\n", FILE_APPEND  | LOCK_EX);
}

// Add data to the logfile
foreach ($logData as $row) {
    file_put_contents($fileName, $sampleName . "," . trim(implode(",", $row)) . "\n", FILE_APPEND  | LOCK_EX);
}

echo "Data written to logfile ($fileName) at " . date("H:i:s");