<?php
    echo "Starting the evaluateData.php script<br>";
    if ( isset( $_POST['sampleName']) )
    {
        $sampleName = explode( "/", $_POST['sampleName'] ); // Results/220226_084003_bottleCO2
        $sampleName = $sampleName[1];
        $polynomial = $_POST['polynomial']; // 0…3, 100 for standard bracketing
        $userName = urlencode( $_POST['userName'] );
    }
    else
    {
        $sampleName = $_GET['sampleName']; // Give sample name via URL
        $polynomial = $_GET['polynomial']; // 0…3, 100 for standard bracketing
        $userName = $_POST['userName'];
    }
    if( $userName == "" )
    {
        $userName = "Dummy_Dummy";
    }

    // Execute shell command
    if( fnmatch('*refill*',$sampleName) )
    {
        // exec("sudo find . -type d -name "$sampleName" -exec rm -rf {} \;")
        console.log("This was a refill, there will be no data processing.");
        exit();
    }
    else
    {
        $cmd = "/usr/bin/python3 Python/processRawDataFiles.py " . $sampleName . " " . $polynomial . " 2>&1";
    }
    $cmd = "/usr/bin/python3 Python/processRawDataFiles.py " . $sampleName . " " . $polynomial . " 2>&1";
    $result = shell_exec( $cmd );
    echo $result;

    // Hello Andreas, I had to comment out the lines below

    // echo "<hr>";
    // // There might be an error message before the result string. That needs to be removed first
    // // Check if there is a ". 2" in the string
    // if( strpos( $result, PHP_EOL) )
    // {
    //     echo "Ist was davor " . strpos( $result, PHP_EOL);
    //     $result = substr( $result, strpos($result, PHP_EOL) );
    // }
    // echo "<hr>";
    // echo $result; // 220412_053915_refGas 14.232 28.045 -101.2 3.5

    echo "<br>";
    echo "The python program has evaluated the data<br />";

    // That does not work
    $resultArray = explode(" ",$result);
    // Now upload the data to the Isolabor server
    // Only upload if data make sense
    if( trim( $resultArray[1] ) != "(most" )
    {
        $url = "http://192.168.1.1/isotope/addTildasData.php?sampleName=" . $sampleName . "&d17O=" . trim($resultArray[1]) . "&d18O=" . trim($resultArray[2]) . "&CapD17O=" . trim($resultArray[3]) . "&CapD17OError=" . trim($resultArray[4]) . "&d17Oreference=" . trim($resultArray[5]) . "&d18Oreference=" . trim($resultArray[6]) . "&pCO2Ref=" . trim($resultArray[8]) . "&pCO2Sam=" . trim($resultArray[9]) . "&PCellRef=" . trim($resultArray[10]) . "&PCellSam=" . trim($resultArray[11]). "&userName=" . trim($userName);
        echo "$url<br>";
        $page = file_get_contents($url);
        echo $page;
        echo "<br />";
        echo "Data have been uploaded to the database.<br />";
        
        if( is_dir( "/mnt/isolaborserver_web/isotope/MeasurementFiles/$sampleName" ) === FALSE )
        {
            // Create folder on Isolaborserver
            exec("mkdir /mnt/isolaborserver_web/isotope/MeasurementFiles/$sampleName");
            // logfile.csv *.stc *.str from TILDAS xlsx and png svg from Python
            // Now copy all measurement files to the isolaborserver
            exec("cp Results/$sampleName/* /mnt/isolaborserver_web/isotope/MeasurementFiles/$sampleName");
            echo "Data copied to Isolaborserver<br />";
        }
        else
        {
            // Only copy the updated files if the folder exists
            exec("cp Results/$sampleName/allData.xlsx /mnt/isolaborserver_web/isotope/MeasurementFiles/$sampleName");
            exec("cp Results/$sampleName/bracketingResults.xlsx /mnt/isolaborserver_web/isotope/MeasurementFiles/$sampleName");
            exec("cp Results/$sampleName/*.png /mnt/isolaborserver_web/isotope/MeasurementFiles/$sampleName");
            exec("cp Results/$sampleName/*.svg /mnt/isolaborserver_web/isotope/MeasurementFiles/$sampleName");
            echo "Folder existed, files and data were updated on Isolaborserver<br />";
        }
        exec("zip -j $sampleName.zip Results/$sampleName/*"); // creates ZIP archive of all data
        exec("cp $sampleName.zip /mnt/isolaborserver_web/isotope/MeasurementFiles/$sampleName");

        // delete local files to save space
        exec("rm $sampleName.zip");
        exec("rm Results/$sampleName/*.svg");
        exec("rm Results/$sampleName/*.png");
        exec("rm Results/$sampleName/bracketingResults.xlsx");


    }
?>
