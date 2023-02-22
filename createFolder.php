<?php
$sampleName = $_POST['sampleName'];
if( $sampleName != "" )
{
    // Create folder on the raspberry pi
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