<?php
    // Write command into the php -> python text file
    $cmd = $_POST['cmd'];
    $date = date('Y-m-d H:i:s');
    $cmdString = $date . "," . $cmd;
    $myfile = fopen("php2python.txt", "w") or die("Unable to open file php2python.txt!");
    fwrite($myfile, $cmdString);
    fclose($myfile);
    echo "Command $cmdString written to php2python.txt file.";
?>