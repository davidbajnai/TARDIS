<?php
    
// This script is used to:
// load a method CSV file

if (isset($_POST['methodFileName'])) {

    // Get the name of the uploaded file
    $filename = $_POST['methodFileName'];
    // The file should be here
    $location = "../../data//Methods/" . $filename;

} else if (isset($_FILES['file']['name'])) {

    // Get the name of the uploaded file
    $filename = $_FILES['file']['name'];

    // Validate uploaded file format
    $file_extension = pathinfo($filename, PATHINFO_EXTENSION);
    if ($file_extension !== 'csv') {
        error_log('Invalid file format. Only CSV files are allowed.');
        exit;
    }

    // Choose where to save the uploaded file
    $location = "../../data/Methods/" . $filename;

    // Save the uploaded file to the local filesystem
    if ( !move_uploaded_file($_FILES['file']['tmp_name'], $location) )
    { 
        error_log("Method file could not be saved to $location"); 
        exit;
    }

} else {
    error_log('No filename provided.');
    exit;
}

$col1_array = [];
$col2_array = [];
$col3_array = [];
$row = 1;

$file = fopen($location, "r");
if ( $file ) {

    while (($data = fgetcsv($file, 1000, ",")) !== FALSE) {
        $num = count($data);
        for ($c = 0; $c < $num; $c++) {
            if($c == 0)
            {
                $col1_array[] = $data[$c]; 
            }
            if($c == 1)
            {
                $col2_array[] = $data[$c]; 
            }
            if($c == 2)
            {
                $col3_array[] = $data[$c]; 
            }
        }
        $row++;
    }
    fclose($file);

} else {
    error_log('Unable to open method csv file.');
    exit;
}

echo implode(",", $col1_array );
echo "|";
echo implode(",", $col2_array );
echo "|";
echo implode(",", $col3_array );