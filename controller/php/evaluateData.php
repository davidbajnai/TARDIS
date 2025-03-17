<?php

// This script is used to:
// evaluation data and send the results to the isolabor server

error_reporting(E_ALL);
ini_set('display_errors', 1);
date_default_timezone_set('Europe/Berlin');
$timestamp = time();
$DateTimeAdded = date("Y-m-d H:i:s", $timestamp);

if (isset($_POST['sampleName'])) {
    $sampleName = urldecode($_POST['sampleName']); 
    $userName = urldecode($_POST['userName']);
    echo "Parameters are recieved from JavaScript<br><br>";
} else {
    $sampleName = urldecode($_GET['sampleName']);
    // $userName = urldecode($GET['userName']);
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

$postData = json_decode($result, true);

// Check if decoding was successful
if ($postData === null && json_last_error() !== JSON_ERROR_NONE) {
    die('<br>Error decoding JSON from Python script.');
} else {

    echo "<br>Uploading results to the database...<br>";

    // Add some extra variables to the array
    $userName_json = !empty($userName) ? $userName : 'David Bajnai';
    $postData['Analyst'] = trim($userName_json);
    $postData['SampleType'] = "CO2";
    $postData['Method'] = "IR absorption";
    $postData['MassSpectrometer'] = "TILDAS";
    $postData['DateTimeAdded'] = $DateTimeAdded;

    $encodedData = urlencode(json_encode($postData));

    // URL to send the data
    $uploadURL = "https://isolabor.geo.uni-goettingen.de/controller/php/dataInputTILDAS.php?jsonstring=" . $encodedData;

    // Create a stream context to disable SSL verification
    $context = stream_context_create([
        "ssl" => [
            "verify_peer" => false,
            "verify_peer_name" => false,
        ]
    ]);
    
    $response = file_get_contents($uploadURL, false, $context);
    
    echo $response;


    echo "<br><br>Uploading files to server...<br>";

    // Get the sample name
    $sampleName = $postData['SampleName'];

    // Get the local directory
    $localDirectory = "/var/www/html/data/Results/" . $sampleName;

    // Copy SPE files from the TILDAS PC to the local directory
    $csvFile = $localDirectory . "/list_of_SPE_files.csv";
    $localSPEDirectory = $localDirectory . "/SPE_files";
    if (file_exists($csvFile) && !is_dir($localSPEDirectory)) {
        mkdir($localSPEDirectory, 0777, true);
        $csv = fopen($csvFile, "r");
        $speFiles = array();
        while (($row = fgetcsv($csv)) !== false) {
            if (!empty($row) && is_array($row) && isset($row[0])) { 
                $speFiles[] = trim($row[0]); 
            }
        }
        fclose($csv);

        if (!is_dir('/mnt/TILDAS_PC')) {
            echo("<br><span style='color:red;'>TILDAS PC not mounted</span><br>");
            } else {
            $speFiles = array_diff($speFiles, array(''));
            foreach ($speFiles as $speFile) {
                $localFilePath = $localDirectory . "/SPE_files/" . basename($speFile);
                if (file_exists($speFile)) {
                    exec("cp " . escapeshellarg($speFile) . " " . escapeshellarg($localFilePath));
                } else {
                    echo "<br>File not found: $speFile";
                }
            }
        }
        exec("rm " . $csvFile);
    } elseif (is_dir($localSPEDirectory) && count(scandir($localSPEDirectory)) > 2) {
        echo("<br>SPE files already there<br>");
    } else {
        echo("<br><span style='color:red;'>SPE files not copied</span><br>");
    }

    // Clean up
    exec("rm " . $csvFile);
    if (count(scandir($localSPEDirectory)) <= 2){
        rmdir($localSPEDirectory);
    }

    echo "</br>";

    // Create a ZIP archive of all files and upload that too the isolaborserver
    exec("cd /var/www/html/data/Results/$sampleName/ && zip -j $sampleName.zip *");

    $filesToUpload = array(
        "FitPlot.png",
        "rawData.png",
        "$sampleName.zip"
    );

    $remoteDirectory = "/var/www/html/data/measurementFiles/" . $sampleName;

    $connection = ssh2_connect($server_IP);
    if (!$connection) {
        die("<span style='color:red;'>Failed to connect to the SSH server</span></br>");
    }

    // Authenticate with the SSH server
    if (!ssh2_auth_password($connection, $server_user, $server_passwd)) {
        die("<span style='color:red;'>Failed to authenticate with the SSH server</span></br>");
    }

    // Initialize SFTP subsystem
    $sftp = ssh2_sftp($connection);
    if (!$sftp) {
        die("<span style='color:red;'>Failed to initialize SFTP subsystem</span></br>");
    }

    // Check if remote directory exists
    $stat = ssh2_sftp_stat($sftp, $remoteDirectory);
    if ($stat !== false && $stat['mode'] & 0040000) {
        echo "Remote directory exists</br>";
    } else {
        // Create remote directory if it doesn't exist
        if (!ssh2_sftp_mkdir($sftp, $remoteDirectory)) {
            die("<span style='color:red;'>Failed to create remote directory</span></br>");
        }
        echo "Remote directory created.</br>";
    }

    foreach ($filesToUpload as $fileName) {

        $localFilePath = "$localDirectory/$fileName";
        $remoteFilePath = "$remoteDirectory/$fileName";

        // Upload the file via SFTP
        $stream = fopen($localFilePath, 'r');
        if (!$stream) {
            echo "<span style='color:red;'>Failed to open local file for reading: $localFilePath</span></br>";
            continue;
        }

        $upload = ssh2_scp_send($connection, $localFilePath, $remoteFilePath, 0777);

        if (!$upload) {
            echo "<span style='color:red;'>Failed to upload file: $localFilePath</span></br>";
        } else {
            echo "File uploaded successfully: $localFilePath</br>";
        }

        fclose($stream);
    }

    // Delete some of the local files to save space on the Raspberry
    exec("rm /var/www/html/data/Results/$sampleName/$sampleName.zip");
}
