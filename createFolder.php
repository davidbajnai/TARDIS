<?php

// This script is used to:
// create a folder on the RPi before each analysis to store the measurement files

date_default_timezone_set('CET');

$sampleName = $_POST['sampleName'];
$StartDate = $_POST['date']; // Date and time when measurement started in UNIX format & UTC timezone

$StartDate = DateTime::createFromFormat('U', $StartDate ) -> setTimezone(new DateTimeZone('CET'));

// Do not create a folder for bellow refill
if( $sampleName != ""  and str_contains($sampleName, "refill") === false)
{
    $folderName = date_format($StartDate, "ymd_His") . "_" . $sampleName;

    mkdir("Results/" . $folderName,0777);
    if( is_dir( "Results/" . $folderName ) )
    {
        echo "Results/" . $folderName;
    }
    else
    {
        echo "Error: could not create folder.";
    }
}
else
{
    echo "No folder created.";
}

// The echo response of this script is used as a folder name variable later on. Do not echo other messages!