<?php

// This script is used to:
// copy the measurement files (.stc and .str) from the TILDAS to the RPi

function getFiles($dir)
{
    return array_values(array_filter(scandir($dir), function ($file) {
        return !is_dir("{$dir}/{$file}");
    }));
}

date_default_timezone_set('Europe/Berlin');


if (isset($_POST['folderName'])) {
    // Something like data/Results/240404_114556_heavyVsRef
    $folderName = urldecode($_POST['folderName']);
    // Date and time when measurement started in UNIX format & UTC timezone
    $timeMeasurementStarted = $_POST['timeMeasurementStarted'];
} else {
    $folderName = urldecode($_GET['folderName']); 
    $timeMeasurementStarted = $_GET['timeMeasurementStarted'];
}

echo "Starting copying files to " . $folderName . "</br>";

// Convert the measurment start date time UNIX date string to a DateTime object in CET timezone. 
$timeMeasurementStarted = DateTime::createFromFormat('U', $timeMeasurementStarted)->setTimezone(new DateTimeZone('CET'));
echo "Search files created after: " . date_format($timeMeasurementStarted, 'Y-m-d H:i:s') . "</br>";

if (count(scandir('/mnt/TILDAS_PC')) <= 2) {
    echo "TILDAS PC not mounted.\n";
    exit();
}

$files = getFiles('/mnt/TILDAS_PC/Data');

if (empty($files)) {
    echo "No matching files found.";
} else {
    foreach ($files as $file) {
        if ($file[0] == "2" && $file[6] == "_" && $file[13] == "." && (substr($file, -3) == "str" || substr($file, -3) == "stc") && DateTimeImmutable::createFromFormat('ymd_His', substr($file, 0, 13)) > $timeMeasurementStarted) {
            exec("cp /mnt/TILDAS_PC/Data/$file ../../$folderName/$file");
        }
    }
    echo "Files successfully copied to local folder!";
}