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

$cmd = "/usr/bin/python3 Python/evaluateData.py " . $sampleName . " " . $polynomial . " 2>&1";
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
    // exec("cd /var/www/html/Results/$sampleName/ && zip -j $sampleName.zip *");
    // echo "<br />Data zipped.<br />";

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
    include_once('controller/config/.config.php');

    $filesToUpload = array(
        "FitPlot.png",
        "bracketingResults.png"
    );

    $localDirectory = "/var/www/html/Results/" . $sampleName;
    $remoteDirectory = "/var/www/html/data";

    foreach ($filesToUpload as $fileName) {
        $localFilePath = "$localDirectory/$fileName";
        $remoteFilePath = "$remoteDirectory/$fileName";
    
        // Construct the SCP command
  
        // Execute the SCP command
        exec("scp -P $port -i /home/pi/.ssh/id_rsa $localFilePath $username@$server:$remoteFilePath 2>&1", $output, $returnCode);
            
        if ($returnCode !== 0) {
            echo "Failed to upload file: $fileName<br>";
            echo "SCP command output: " . implode("\n", $output) . "<br>";
        } else {
            echo "File uploaded successfully: $fileName\n";
        }
    }

    // Delete some of the local files to save space on the Raspberry
    exec("rm Results/$sampleName/$sampleName.zip");
    // exec("rm Results/$sampleName/*.png");
    exec("rm Results/$sampleName/bracketingResults.xlsx");
}
