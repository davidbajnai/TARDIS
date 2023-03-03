<?php

// This script is used to:
// log the status (temp, bellow compression, vacuum, etc.) of the inlet system

$sampleName = $_POST['sampleName'];
$logData = $_POST['logData']; // Comma separated string
$folderName = $_POST['folderName'];

// Create a logfile if it doesnt exist yet
if( file_exists( $folderName . "/logFile.csv" ) === false )
{
    // Name the header row
    file_put_contents( $folderName . "/logFile.csv", "SampleName,Time(abs),Temperature(room),TargetT(box),Humidity(room),percentageX,percentageY,percentageZ,pressureX,pressureY,pressureA,edwards,fanSpeed,RoomT,RoomH,RoomP\n", FILE_APPEND  | LOCK_EX );
}

// Add data to the logfile
foreach ($logData as $row) {
    $rowLength = count($row);
    $desiredLength = 15;
    if( $rowLength === $desiredLength )
    {
        // echo "This row is 15 elements long, I will copy it into the logFile ";
        file_put_contents( $folderName . "/logFile.csv", $sampleName . "," . trim(implode(",",$row)) . "\n", FILE_APPEND  | LOCK_EX );
    }
}

echo "Data written to logfile.";