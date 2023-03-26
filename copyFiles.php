<?php

// This script is used to:
// copy the measurement files (.stc and .str) from the TILDAS to the RPi

function getFiles($dir)
{
    return array_values(array_filter(scandir($dir), function ($file) {
        global $dir;
        return !is_dir("{$dir}/{$file}");
    }));
}

date_default_timezone_set('Europe/Berlin');

$folderName = $_POST['folderName']; // Something like Results/230306_112345_sampleName
$StartDate = $_POST['date']; // Date and time when measurement started in UNIX format & UTC timezone

// Do not evaluate data for refills
if (str_contains($folderName, "folder") === true) {
    echo ("This was a refill, there are no files to copy");
    exit();
}

// Convert the measurment start date time UNIX date string to a DateTime object in CET timezone. 
$StartDate = DateTime::createFromFormat('U', $StartDate)->setTimezone(new DateTimeZone('CET'));
echo "Search files created after: " . date_format($StartDate, 'ymd_His' . "\n");

$path = '/mnt/TILDAS-CS-132/Data';
$files = getFiles($path);

foreach ($files as $file) {
    if ($file[0] == "2" && $file[6] == "_" && $file[13] == "." && (substr($file, -3) == "str" || substr($file, -3) == "stc") && DateTimeImmutable::createFromFormat('ymd_His', substr($file, 0, 13)) > $StartDate) {
        exec("cp /mnt/TILDAS-CS-132/Data/$file $folderName/$file");
    }
}

echo "Files successfully copied to local folder.";