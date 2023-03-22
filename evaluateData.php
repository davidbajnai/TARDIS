<?php

// This script is used to:
// start the data evaluation and clean up

date_default_timezone_set('CET');

if (isset($_POST['sampleName'])) {
    if (str_contains($_POST['sampleName'], "folder") === true) {
        echo ("This was a refill, there will be no data processing.");
        exit();
    }
    $sampleName = explode("/", $_POST['sampleName']); // Results/220226_084003_sampleName
    $sampleName = $sampleName[1];
    $polynomial = $_POST['polynomial']; // 0…3, 100 for standard bracketing
    $userName = urlencode($_POST['userName']);
    echo "Parameters are recieved from JavaScript<br>";
} else {
    $sampleName = $_GET['sampleName']; // Give sample name via URL
    $polynomial = $_GET['polynomial']; // 0…3, 100 for standard bracketing
    $userName = $_POST['userName'];
    echo "Parameters are recieved via URL<br>";
}
if ($userName == "") {
    $userName = "Dummy_Dummy";
}

// Decide which evaluation script to use. This is necessary because a change in the logfile structure
$measurementDateTime = DateTimeImmutable::createFromFormat('ymd_His', substr( $sampleName, 0, 13));

$changeDate = new DateTime('2023-03-06 13:00:00');
if ($measurementDateTime < $changeDate) {
    echo "Based on the measurement date (" . date_format($measurementDateTime, 'Y-m-d H:i:s') . " < " . date_format($changeDate, 'Y-m-d H:i:s') . ") we use the historic python script (processRawDataFiles1.py) <br>";
    $cmd = "/usr/bin/python3 Python/processRawDataFiles1.py " . $sampleName . " " . $polynomial . " 2>&1";
    $result = shell_exec($cmd); // isotope ratios from the evaluation script
    echo $result . "<br>";
} else {
    echo "Based on the measurement date (" . date_format($measurementDateTime, 'Y-m-d H:i:s') . " > " . date_format($changeDate, 'Y-m-d H:i:s') . ") we use the newer python script (processRawDataFiles2.py) <br>";
    $cmd = "/usr/bin/python3 Python/processRawDataFiles2.py " . $sampleName . " " . $polynomial . " 2>&1";
    $result = shell_exec($cmd); // isotope ratios from the evaluation script
    echo $result . "<br>";
}

echo "The python program has evaluated the data<br />";

$resultArray = explode(" ", $result);

// Now upload the data to the Isolabor server
if (trim($resultArray[1]) != "(most") // Only upload if data make sense
{
    $url = "http://192.168.1.1/isotope/addTildasData.php?sampleName=" . $sampleName . "&d17O=" . trim($resultArray[1]) . "&d18O=" . trim($resultArray[2]) . "&CapD17O=" . trim($resultArray[3]) . "&CapD17OError=" . trim($resultArray[4]) . "&d17Oreference=" . trim($resultArray[5]) . "&d18Oreference=" . trim($resultArray[6]) . "&pCO2Ref=" . trim($resultArray[8]) . "&pCO2Sam=" . trim($resultArray[9]) . "&PCellRef=" . trim($resultArray[10]) . "&PCellSam=" . trim($resultArray[11]) . "&userName=" . trim($userName);
    echo "$url<br>";
    $page = file_get_contents($url);
    echo $page;
    echo "<br />";
    echo "Data have been uploaded to the database.<br />";

    if (is_dir("/mnt/isolaborserver_web/isotope/MeasurementFiles/$sampleName") === FALSE) {
        // Create folder on Isolaborserver
        exec("mkdir /mnt/isolaborserver_web/isotope/MeasurementFiles/$sampleName");

        // Now copy all measurement files to the isolaborserver
        exec("cp Results/$sampleName/* /mnt/isolaborserver_web/isotope/MeasurementFiles/$sampleName");
        echo "Data copied to Isolaborserver<br />";
    } else {
        // Only copy the updated files if the folder exists
        exec("cp Results/$sampleName/allData.xlsx /mnt/isolaborserver_web/isotope/MeasurementFiles/$sampleName");
        exec("cp Results/$sampleName/bracketingResults.xlsx /mnt/isolaborserver_web/isotope/MeasurementFiles/$sampleName");
        exec("cp Results/$sampleName/*.png /mnt/isolaborserver_web/isotope/MeasurementFiles/$sampleName");
        exec("cp Results/$sampleName/*.svg /mnt/isolaborserver_web/isotope/MeasurementFiles/$sampleName");
        echo "Folder existed, files and data were updated on Isolaborserver<br />";
    }

    // Create a ZIP archive of all data and upload that too the isolaborserver
    exec("zip -j $sampleName.zip Results/$sampleName/*");
    exec("cp $sampleName.zip /mnt/isolaborserver_web/isotope/MeasurementFiles/$sampleName");

    // Delete some of the local files to save space on the Raspberry
    exec("rm $sampleName.zip");
    exec("rm Results/$sampleName/*.svg");
    exec("rm Results/$sampleName/*.png");
    exec("rm Results/$sampleName/bracketingResults.xlsx");
}