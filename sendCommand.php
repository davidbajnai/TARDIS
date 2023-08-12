<?php

// This script is used to:
// receive the status array from the serialComm.py
// and send commands to the TILDAS and the Arduino

// Define functions to send command to TILDAS
function sendCommandViaTCP($command) {
    $socket = fsockopen('192.168.1.240', 12345, $errno, $errstr, 1);
    usleep(250000);
    if ($socket) {
        fwrite($socket, $command);
    }
    usleep(250000);
    fclose($socket);
}

// Get the status array from the serialComm.py via shared variable "key"
// The status array is then "echoed" to frontPanel.php via AJAX
$m = new Memcached();
$m->addServer('127.0.0.1', 11211);
$value = $m->get('key');
echo $value;

// Check if a command was sent from the frontPanel.php
if( $_POST['cmd'] != "" )
{
    if( $_POST['cmd'] == "TWD1" )
    // the TWD1 command means that the user wants to start the measurement
    {
        // Get last modified date of the commands logfile on the TILDAS PC
        $oldFileTime = exec( "date -r /mnt/TILDAS-CS-132/Commands/comlog.dat" );

        sendCommandViaTCP("amass1\r\namwd1\r\n");

        // Get last modified date of the commands logfile on the TILDAS PC
        $newFileTime = exec( "date -r /mnt/TILDAS-CS-132/Commands/comlog.dat" );

        // Compare the file timestamps to check if the TILDAS recieved the command
        if( $newFileTime == $oldFileTime )
        // If the timestamp did not change, the command was not recieved: repeat the command
        {
            sendCommandViaTCP("amass1\r\namwd1\r\n");
        }
    }
    else if( $_POST['cmd'] == "TWD0" )
    // the TWD0 command means that the user wants to stop the measurement
    {
        // Get last modified date of the commands logfile on the TILDAS PC
        $oldFileTime = exec( "date -r /mnt/TILDAS-CS-132/Commands/comlog.dat" );

        sendCommandViaTCP("amass0\r\namwd0\r\n");

        // Get last modified date of the commands logfile on the TILDAS PC
        $newFileTime = exec( "date -r /mnt/TILDAS-CS-132/Commands/comlog.dat" );

        // Compare the file timestamps to check if the TILDAS recieved the command
        if( $newFileTime == $oldFileTime )
        // If the timestamp did not change, the command was not recieved: repeat the command
        {
            sendCommandViaTCP("amass1\r\namwd1\r\n");
        }
    }
    else
    // Commands sent to the Arduino to open valves, compress bellows etc.
    {
        // This is a command sent to Python serial communication
        $m->set('key2', $_POST['cmd']);
        usleep(100000);
    }
}
// clean up
$m->quit();