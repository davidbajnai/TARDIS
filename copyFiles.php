<?php

// This script is used:
// to copy the measurement files (.stc and .str) from the TILDAS to the RPi

function getFiles( $dir ){
    return array_values(array_filter(scandir($dir), function($file){
        global $dir;
        return !is_dir("{$dir}/{$file}");
    }));
}

$folderName = $_POST['folderName'];
$date = $_POST['date']; // This is the UNIX time, seconds since 1.1.1970 like 1645861203
$ymdSting = substr( $folderName, 8, 13);
echo $ymdSting;

$path = '/mnt/TILDAS-CS-132/Data';
$files = getFiles( $path );

foreach( $files as $file )
{
    if( $file[0] == "2" && $file[6] == "_" && $file[13] == "." && ( substr($file, -3) == "str" || substr($file, -3) == "stc" ) && substr( $file, 0, 13 ) > $ymdSting  )
    {
        exec("cp /mnt/TILDAS-CS-132/Data/$file $folderName/$file");
        // echo $file . " ...OK<br />";
    }
}

// echo "Files successfully copied to local folder.";