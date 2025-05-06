<?php
// This script is used to:
// copy the measurement files (.stc and .str) from the TILDAS to the RPi

function getFiles($dir)
{
    return array_values(array_filter(scandir($dir), function ($file) use ($dir) {
        return !is_dir("{$dir}/{$file}");
    }));
}

date_default_timezone_set('Europe/Berlin');

if (php_sapi_name() === 'cli') {
    $rawName = $argv[1]; // e.g., 250428_155550_heavyVsRef
    $_POST['folderName'] = $rawName;

    // Extract datetime from folder name (yymmdd_HHMMSS)
    if (preg_match('/(\d{6})_(\d{6})/', $rawName, $matches)) {
        $datetime = DateTime::createFromFormat('ymd_His', $matches[1] . '_' . $matches[2], new DateTimeZone('Europe/Berlin'));
        $_POST['timeMeasurementStarted'] = $datetime->getTimestamp();
    }
}

if (isset($_POST['folderName'])) {
    $folderName = basename(urldecode($_POST['folderName']));
    $timeMeasurementStarted = $_POST['timeMeasurementStarted'];
} else {
    $folderName = basename(urldecode($_GET['folderName']));
    $timeMeasurementStarted = $_GET['timeMeasurementStarted'];
}

echo "Starting copying files to " . $folderName . "</br>";

// Convert the measurment start date time UNIX date string to a DateTime object in CET timezone. 
$timeMeasurementStarted = DateTime::createFromFormat('U', $timeMeasurementStarted)->setTimezone(new DateTimeZone('Europe/Berlin'));
echo "Search files created after: " . date_format($timeMeasurementStarted, 'Y-m-d H:i:s') . "</br>";

if (count(scandir('/mnt/TILDAS_PC')) <= 2) {
    echo "The TILDAS PC not yet mounted you dummy. Let's correct this serious mistake... </br>";
    exec('sudo /var/www/html/controller/shell/mountTILDAS.sh', $output, $returnVar);
    
    if ($returnVar !== 0) {
        echo "Oh noo, mounting the TILDAS PC failed because: $returnVar\n";
        exit(1);
    }
}

$files = getFiles('/mnt/TILDAS_PC/Data');

if (empty($files)) {
    echo "No matching files found.";
} else {
    $copiedFiles = [];

    $baseDir = dirname(__FILE__);
    $destinationDir = $baseDir . "/../../data/Results/" . $folderName;

    if (!is_dir($destinationDir)) {
        echo "Destination folder does not exist: $destinationDir</br>";
    } else {
        foreach ($files as $file) {
            if (strlen($file) >= 14 &&
                $file[0] == "2" &&
                $file[6] == "_" &&
                $file[13] == "." &&
                (substr($file, -3) === "str" || substr($file, -3) === "stc")
            ) {
                $fileTimestamp = DateTimeImmutable::createFromFormat(
                    'ymd_His',
                    substr($file, 0, 13),
                    new DateTimeZone('Europe/Berlin')
                )->getTimestamp();
                
                if ($fileTimestamp > $timeMeasurementStarted->getTimestamp()) {
                    exec("cp /mnt/TILDAS_PC/Data/$file $destinationDir/$file");
                    $copiedFiles[] = $file;
                }
            }
        }

        if (!empty($copiedFiles)) {
            echo "Files successfully copied to local folder!</br>";
        } else {
            echo "No matching files were copied.";
        }
    }
}