<?php
    // This files loads the appropriate method .csv file from the Methods folder
    // The method .csv file has to be present in the Methods folder

    /* Get the name of the uploaded file */
    $filename = $_POST['methodFileName'];

    /* Choose where to save the uploaded file */
    $location = "./Methods/" . $filename;

    /* Save the uploaded file to the local filesystem */
    $file = fopen($location, "r");
    $col1_array = [];
    $col2_array = [];
    $col3_array = [];
    $row = 1;
    if (($handle = $file) !== FALSE) {
        while (($data = fgetcsv($handle, 1000, ",")) !== FALSE) {
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
        fclose($handle);
    }
    echo implode(",", $col1_array );
    echo "|";
    echo implode(",", $col2_array );
    echo "|";
    echo implode(",", $col3_array );
?>