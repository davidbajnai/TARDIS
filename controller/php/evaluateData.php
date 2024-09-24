<?php

// This script is used to:
// evaluation data and send the results to the isolabor server

date_default_timezone_set('Europe/Berlin');
$timestamp = time();
$DateTimeAdded = date("Y-m-d H:i:s", $timestamp);

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
    $uploadURL = "http://". $server_IP . "/controller/php/dataInputTILDAS.php" . "?jsonstring=" . $encodedData;

    $response = file_get_contents($uploadURL);

    echo $response;


    echo "<br><br>Uploading files to server...<br>";

    // Get the sample name
    $sampleName = $postData['SampleName'];

    // Get the local directory
    $localDirectory = "/var/www/html/data/Results/" . $sampleName;

    // Copy SPE files from the TILDAS PC to the local directory
    $csvFile = $localDirectory . "/list_of_SPE_files.csv";
    $localSPEDirectory = $localDirectory . "/SPE_files";
    if (!is_dir($localSPEDirectory) && file_exists($csvFile)) {
        mkdir($localSPEDirectory, 0777, true);

        $csv = fopen($csvFile, "r");
        $speFiles = array();
        while (!feof($csv)) {
            $speFiles[] = fgetcsv($csv)[0];
        }
        fclose($csv);

        exec("rm " . $csvFile);

        if (count(scandir('/mnt/TILDAS_PC')) <= 2) {
            echo("<br>TILDAS PC not mounted.<br>");
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
    } else {
        echo("<br>SPE files not copied<br>");
    }
    echo "</br>";

    // Create a ZIP archive of all files and upload that too the isolaborserver
    exec("cd /var/www/html/data/Results/$sampleName/ && zip -j $sampleName.zip *");

    $filesToUpload = array(
        "FitPlot.png",
        // "bracketingResults.png",
        "rawData.png",
        "$sampleName.zip"
    );

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
