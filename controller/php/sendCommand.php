<?php

    // This script is used to:
    // receive the status array from the serialComm.py
    // and send commands to the TILDAS and the Arduino

    // Function to send command to TILDAS
    function sendCommandViaTCP($command) {

        // Get last modified date of the commands logfile on the TILDAS PC
        $oldFileTime = exec( "date -r /mnt/TILDAS-CS-132/Commands/comlog.dat" );
        $newFileTime = $oldFileTime;

        for ($attempts = 0; $attempts < 50; $attempts++) {
            // Compare the file timestamps to check if the TILDAS recieved the command
            // If the timestamp did not change, the command was not received: repeat the command
            if ($newFileTime == $oldFileTime) {
                $socket = @fsockopen('10.132.1.87', 12345, $errno, $errstr, 1);
                sleep(2);
                fwrite($socket, $command);
                sleep(2);
                fclose($socket);
                sleep(2);
                $newFileTime = exec( "date -r /mnt/TILDAS-CS-132/Commands/comlog.dat" );
            } else {
                break;
            }
        }
    }

    // Get the status array from the serialComm.py via shared variable "key"
    // The status array is then "echoed" to frontPanel.php via AJAX
    $m = new Memcached();
    $m->addServer('127.0.0.1', 11211);
    $value = $m->get('key');
    echo $value;

    // Check if a command was sent from the frontPanel.php
    if( $_POST['cmd'] != "" ) {
        if( $_POST['cmd'] == "TWD1" ) {
        
            // Send the TILDAS commands to start the data acquisition
            sendCommandViaTCP("amass1\r\namwd1\r\n");

        } else if( $_POST['cmd'] == "TWD0" ) {

            // Send the TILDAS commands to stop the data acquisition
            sendCommandViaTCP("amass0\r\namwd0\r\n");

        } else {
            
            // Commands sent to the Arduino to open valves, compress bellows etc. via Python serial communication
            $m->set('key2', $_POST['cmd']);
            usleep(100000);
        }
    }
    // clean up
    $m->quit();