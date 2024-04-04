<?php

// This script is used to:
// evaluation data and send the results to the isolabor server

date_default_timezone_set('Europe/Berlin');

if (isset($_POST['sampleName'])) {
    $sampleName = urldecode($_POST['sampleName']); 
    $userName = urldecode($_POST['userName']);
    echo "Parameters are recieved from JavaScript<br><br>";
} else {
    $sampleName = urldecode($_GET['sampleName']);
    $userName = urldecode($GET['userName']);
    echo "Parameters are recieved via URL<br><br>";
}

// Import necessary data 
include_once('../config/.config.php');

// Start the timer
$start_time = microtime(true);

$cmd = "python3 ../python/evaluateData.py " . $sampleName . " " . " 2>&1";
$result = shell_exec($cmd); // isotope ratios from the evaluation script

// Stop the timer
$end_time = microtime(true);
$duration = $end_time - $start_time;

echo "Data evalauted in " . round($duration, 2) . " seconds:<br/>";
echo $result . "<br>";

$resultArray = explode(" ", $result);

// Now upload the data to the Isolabor server
if (trim($resultArray[1]) != "(most") // Only upload if data make sense
{
    
    // Upload data to database

    echo "<br>Uploading results to the database...<br>";

    // Create a ZIP archive of all data and upload that too the isolaborserver
    exec("cd /var/www/html/data/Results/$sampleName/ && zip -j $sampleName.zip *");

    // Set additional POST fields
    $postData = array(
        "sampleName" => $sampleName ?? '',
        "d17O" => trim($resultArray[1] ?? ''),
        "d18O" => trim($resultArray[2] ?? ''),
        "d18OError" => trim($resultArray[3] ?? ''),
        "CapD17O" => trim($resultArray[4] ?? ''),
        "CapD17OError" => trim($resultArray[5] ?? ''),
        "d17Oreference" => trim($resultArray[6] ?? ''),
        "d18Oreference" => trim($resultArray[7] ?? ''),
        "pCO2Ref" => trim($resultArray[8] ?? ''),
        "pCO2Sam" => trim($resultArray[9] ?? ''),
        "PCellRef" => trim($resultArray[10] ?? ''),
        "PCellSam" => trim($resultArray[11] ?? ''),
        "userName" => trim($userName ?? 'Bajnai')
    );

    // Convert data to JSON format
    $encodedData = urlencode(json_encode($postData));

    // URL to send the data
    $uploadURL = "http://". $server_IP . "/controller/php/dataInputTILDAS.php" . "?jsonstring=" . $encodedData;

    $response = file_get_contents($uploadURL);

    echo $response;


    // Upload files to server.
    echo "<br><br>Uploading files to server...<br>";

    $filesToUpload = array(
        "FitPlot.png",
        "bracketingResults.png",
        "rawData.png",
        "$sampleName.zip"
    );

    $localDirectory = "/var/www/html/data/Results/" . $sampleName;
    $remoteDirectory = "/var/www/html/data/measurementFiles/" . $sampleName;

    $connection = ssh2_connect($server_IP);
    if (!$connection) {
        die("Failed to connect to the SSH server.</br>");
    }

    // Authenticate with the SSH server
    if (!ssh2_auth_password($connection, $server_user, $server_passwd)) {
        die("Failed to authenticate with the SSH server.</br>");
    }

    // Initialize SFTP subsystem
    $sftp = ssh2_sftp($connection);
    if (!$sftp) {
        die("Failed to initialize SFTP subsystem.</br>");
    }

    // Check if remote directory exists
    $stat = ssh2_sftp_stat($sftp, $remoteDirectory);
    if ($stat !== false && $stat['mode'] & 0040000) {
        echo "Remote directory exists.</br>";
    } else {
        // Create remote directory if it doesn't exist
        if (!ssh2_sftp_mkdir($sftp, $remoteDirectory)) {
            die("Failed to create remote directory.</br>");
        }
        echo "Remote directory created.</br>";
    }

    foreach ($filesToUpload as $fileName) {

        $localFilePath = "$localDirectory/$fileName";
        $remoteFilePath = "$remoteDirectory/$fileName";

        // Upload the file via SFTP
        $stream = fopen($localFilePath, 'r');
        if (!$stream) {
            echo "Failed to open local file for reading: $localFilePath</br>";
            continue;
        }

        $upload = ssh2_scp_send($connection, $localFilePath, $remoteFilePath, 0644);

        if (!$upload) {
            echo "Failed to upload file: $localFilePath</br>";
        } else {
            echo "File uploaded successfully: $localFilePath</br>";
        }

        fclose($stream);
    }

    // Delete some of the local files to save space on the Raspberry
    exec("rm /var/www/html/data/Results/$sampleName/$sampleName.zip");
    // exec("rm Results/$sampleName/*.png");
    exec("rm /var/www/html/data/Results/$sampleName/bracketingResults.xlsx");
}
