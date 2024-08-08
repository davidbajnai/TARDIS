<?php

    // This script is used to:
    // receive the status array from the serialComm.py
    // and send commands to the TILDAS and the Arduino

    include_once("../config/.config.php");

    // Function to send command to TILDAS
    function sendCommandViaTCP($command, $IP) {

        $socket = fsockopen($IP, 12345, $errno, $errstr, 1);
        sleep(1);
        if ($socket) {
            fwrite($socket, $command);
            sleep(2);
            fclose($socket);
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
            sendCommandViaTCP("amass1\r\namwd1\r\n", $TILDAS_IP);

        } else if( $_POST['cmd'] == "TWD0" ) {

            // Send the TILDAS commands to stop the data acquisition
            sendCommandViaTCP("amass0\r\namwd0\r\n", $TILDAS_IP);
        

        } else if( $_POST['cmd'] == "BG0" ) {

            // Send the TILDAS commands to suspend background fitting
            sendCommandViaTCP("bdfits1\r\n", $TILDAS_IP);
        

        } else if( $_POST['cmd'] == "BG1" ) {

            // Send the TILDAS command to enable background fitting
            sendCommandViaTCP("bdfits0\r\n", $TILDAS_IP);

        } else {
            
            // Commands sent to the Arduino to open valves, compress bellows etc. via Python serial communication
            $m->set('key2', $_POST['cmd']);
            usleep(100000);
        }
    }
    // clean up
    $m->quit();