<?php

// This script is used to:
// log the status (temp, bellow compression, vacuum, etc.) of the inlet system

$logFileName = $_POST['logFileName'];
$logDataJSON = json_decode(urldecode($_POST['logDataJSON']), true);

// Create the CSV file and write header row with keys if it doesnt exist yet
if (!file_exists($logFileName)) {
    $headerRow = implode(',', array_keys($logDataJSON)) . PHP_EOL;
    file_put_contents($logFileName, $headerRow);
}

// Append data to CSV file
$dataRow = implode(',', $logDataJSON) . PHP_EOL;
file_put_contents($logFileName, $dataRow, FILE_APPEND);

echo "Data written to logfile ($logFileName) at " . date("H:i:s");