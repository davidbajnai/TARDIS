<?php

// This script is used to:
// evaluation data and send the results to the isolabor server

date_default_timezone_set('Europe/Berlin');

if (isset($_POST['sampleName'])) {
    if (str_contains($_POST['sampleName'], "folder") === true) {
        echo ("This was a refill, there will be no data processing.");
        exit();
    }
    $sampleName = explode("/", $_POST['sampleName']); // Results/220226_084003_sampleName
    $sampleName = $sampleName[1];
    $polynomial = $_POST['polynomial']; // 0…3, 100 for standard bracketing
    $userName = urlencode($_POST['userName']);
    echo "Parameters are recieved from JavaScript<br><br>";
} else {
    $sampleName = $_GET['sampleName']; // Give sample name via URL
    $polynomial = $_GET['polynomial']; // 0…3, 100 for standard bracketing
    $userName = $_POST['userName'];
    echo "Parameters are recieved via URL<br><br>";
}

// Start the timer
$start_time = microtime(true);

$cmd = "python3 ../python/evaluateData.py " . $sampleName . " " . $polynomial . " 2>&1";
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
        "userName" => trim($userName ?? 'David Bajnai')
    );

    // Convert data to JSON format
    $jsonData = json_encode($postData);
    $encodedData = urlencode($jsonData);

    // URL to send the data
    $uploadUrl = "http://10.132.1.101/controller/php/dataInputTILDAS.php";

    $finalUrl = $uploadUrl . "?jsonstring=" . $encodedData;

    $response = file_get_contents($finalUrl);

    echo $response;


    // Upload files to server.
    echo "<br><br>Uploading files to server...<br>";

    // Open ftp server
    include_once('../config/.config.php');

    $filesToUpload = array(
        "FitPlot.png",
        "bracketingResults.png",
        "rawData.png",
        "$sampleName.zip"
    );

    $localDirectory = "/var/www/html/data/Results/" . $sampleName;
    $remoteDirectory = "/var/www/html/data";

    $connection = ssh2_connect($server_IP);
    if (!$connection) {
        die("Failed to connect to the SSH server.\n");
    }

    // Authenticate with the SSH server
    if (!ssh2_auth_password($connection, $username, $password)) {
        die("Failed to authenticate with the SSH server.\n");
    }

    // Initialize SFTP subsystem
    $sftp = ssh2_sftp($connection);
    if (!$sftp) {
        die("Failed to initialize SFTP subsystem.\n");
    }

    foreach ($filesToUpload as $fileName) {
        $localFilePath = "$localDirectory/$fileName";
        $remoteFilePath = "$remoteDirectory/$fileName";

        // Upload the file via SFTP
        $stream = fopen("ssh2.sftp://$sftp$remoteFilePath", 'w');
        if (!$stream) {
            echo "Failed to open remote file for writing: $remoteFilePath\n";
            continue;
        }

        $data = file_get_contents($localFilePath);
        if ($data === false) {
            echo "Failed to read local file: $localFilePath\n";
            fclose($stream);
            continue;
        }

        $bytesWritten = fwrite($stream, $data);
        fclose($stream);

        if ($bytesWritten === false) {
            echo "Failed to write data to remote file: $remoteFilePath\n";
            continue;
        }

        echo "File uploaded successfully: $fileName</br>";
    }

    // Delete some of the local files to save space on the Raspberry
    exec("rm /var/www/html/data/Results/$sampleName/$sampleName.zip");
    // exec("rm Results/$sampleName/*.png");
    exec("rm /var/www/html/data/Results/$sampleName/bracketingResults.xlsx");
}
