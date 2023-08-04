<?php

// This script is used to:
// receives the status array from the serialComm.py
// and sends commands to the TILDAS and the Arduino

$m = new Memcached();
$m->addServer('127.0.0.1', 11211);
$value = $m->get('key');
echo $value; // This is the information received from Python serial communication

if( $_POST['cmd'] != "" )
{
    if( $_POST['cmd'] == "TWD1" )
    {
        // Send command via TCP
        // $socket = fsockopen('192.168.1.240', 12345, $errno, $errstr, 10);
        // if (!$socket) {
        //     // Handle connection error
        //     echo "Error: $errno - $errstr";
        // } else {
        //     // Send the message: "WD on" and "ASS on"
        //     fwrite($socket, "amass1\r\namwd1\r\n");
        //     // Close the connection
        //     fclose($socket);
        // }

        // get last modified date of the commands logfile on the TILDAS PC
        $oldFileTime = exec( "date -r /mnt/TILDAS-CS-132/Commands/comlog.dat" );

        // Copy command file in the mounted folder from the TILDAS instrument
        exec( "cp /mnt/TILDAS-CS-132/Commands/ComQue.xyz.StartWriting /mnt/TILDAS-CS-132/Commands/ComQue.xyz" );
        sleep(1); // Some delay

        // get last modified date of the commands logfile on the TILDAS PC
        $newFileTime = exec( "date -r /mnt/TILDAS-CS-132/Commands/comlog.dat" );

        // compare the file timestamps to check if the TILDAS recieved the command
        // if the command was not recieved, i.e., the timestamp did not change, repeat the command
        if( $newFileTime == $oldFileTime )
        {
            exec( "cp /mnt/TILDAS-CS-132/Commands/ComQue.xyz.StartWriting /mnt/TILDAS-CS-132/Commands/ComQue.xyz" );
        }
    }
    else if( $_POST['cmd'] == "TWD0" )
    {
        // Send command via TCP
        // $socket = fsockopen('192.168.1.240', 12345, $errno, $errstr, 10);
        // if (!$socket) {
        //     // Handle connection error
        //     echo "Error: $errno - $errstr";
        // } else {
        //     // Send the message: "WD off" and "ASS off"
        //     fwrite($socket, "amass0\r\namwd0\r\n");
        //     // Close the connection
        //     fclose($socket);
        // }

        // get last modified date of the commands logfile on the TILDAS PC
        $oldFileTime = exec( "date -r /mnt/TILDAS-CS-132/Commands/comlog.dat" );

        // Copy command file in the mounted folder from the TILDAS instrument
        exec( "cp /mnt/TILDAS-CS-132/Commands/ComQue.xyz.StopWriting /mnt/TILDAS-CS-132/Commands/ComQue.xyz" );
        sleep(1); // Some delay

        // get last modified date of the commands logfile on the TILDAS PC
        $newFileTime = exec( "date -r /mnt/TILDAS-CS-132/Commands/comlog.dat" );

        // compare the file timestamps to check if the TILDAS recieved the command
        // if the command was not recieved, i.e., the timestamp did not change, repeat the command
        if( $newFileTime == $oldFileTime )
        {
            exec( "cp /mnt/TILDAS-CS-132/Commands/ComQue.xyz.StopWriting /mnt/TILDAS-CS-132/Commands/ComQue.xyz" );
        }
    }
    else
    {
        // This is a command sent to Python serial communication
        $m->set('key2', $_POST['cmd']);
    }
}
// clean up
$m->quit();