<?php

// This script is used to:
// create a folder on the RPi before each analysis to store the measurement files

$sampleName = $_POST['sampleName'];

// Do not create a folder for bellow refill
if( $sampleName != "" and strpos($sampleName,"refill") === false)
{
    $folderName = date(y) . date(m) . date(d) . "_" . date(H) . date(i) . date(s) . "_" . $sampleName;
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