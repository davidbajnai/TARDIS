<?php

// This script is used to:
// receive the status array from the serialComm.py
// and send commands to the TILDAS and the Arduino

// Function to send command to TILDAS
// via TCP daemon
function sendCommandViaRelay(string $command): string
{
    $s = @stream_socket_client("tcp://127.0.0.1:23456", $e, $r, 1);
    if ($s === false) {
        return false;
    }
    fwrite($s, $command);
    fflush($s);
    $resp = fgets($s, 512);
    fclose($s);
    return $resp ?: false;
}

// Get the status array from the serialComm.py via shared variable "key"
// The status array is then "echoed" to frontPanel.php via AJAX
$m = new Memcached();
$m->addServer('127.0.0.1', 11211);
$value = $m->get('key');
echo $value;

// Check if a command was sent from the frontPanel.php
if ($_POST['cmd'] != "") {
    if ($_POST['cmd'] == "TWD1") {

        // Send the TILDAS commands to start the data acquisition
        sendCommandViaRelay("amass1\r\namwd1\r\n");
    } else if ($_POST['cmd'] == "TWD0") {

        // Send the TILDAS commands to stop the data acquisition
        sendCommandViaRelay("amass0\r\namwd0\r\nbdfits1\r\n");
    } else if ($_POST['cmd'] == "BG0") {

        // Send the TILDAS commands to suspend background fitting
        sendCommandViaRelay("bdfits1\r\n");
    } else if ($_POST['cmd'] == "BG1") {

        // Send the TILDAS command to enable background fitting
        sendCommandViaRelay("bdfits0\r\n");
    } else {

        // Commands sent to the Arduino to open valves, compress bellows etc. via Python serial communication
        $m->set('key2', $_POST['cmd']);
        usleep(100000);
    }
}
// clean up
$m->quit();

