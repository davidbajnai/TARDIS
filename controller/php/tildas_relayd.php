<?php
declare(strict_types=1);

include_once("/var/www/html/controller/config/.config.php");

/*
  Minimal TILDAS relay daemon
  - persistent TCP connection to $TILDAS_IP:12345
  - local listener on 127.0.0.1:23456
  - supports multi-line commands with CRLF
  - write-only protocol to Windows
*/

if (!isset($TILDAS_IP) || trim($TILDAS_IP) === "") {
    fwrite(STDERR, "ERROR: \$TILDAS_IP not set in config\n");
    exit(1);
}

$WINDOWS_IP   = trim($TILDAS_IP);
$WINDOWS_PORT = 12345;

$LISTEN_IP    = "127.0.0.1";
$LISTEN_PORT  = 23456;

$windows = null;

/* connect to Windows if not connected */
function connectWindows(): bool
{
    global $windows, $WINDOWS_IP, $WINDOWS_PORT;

    if (is_resource($windows)) {
        return true;
    }

    $windows = @stream_socket_client(
        "tcp://{$WINDOWS_IP}:{$WINDOWS_PORT}",
        $errno,
        $errstr,
        2
    );

    if ($windows === false) {
        $windows = null;
        return false;
    }

    // do NOT set read timeout, we never read
    return true;
}

/* reset Windows connection */
function resetWindows(): void
{
    global $windows;
    if (is_resource($windows)) {
        @fclose($windows);
    }
    $windows = null;
}

/* start local server */
$server = @stream_socket_server(
    "tcp://{$LISTEN_IP}:{$LISTEN_PORT}",
    $errno,
    $errstr
);

if ($server === false) {
    fwrite(STDERR, "ERROR: cannot listen: {$errstr}\n");
    exit(1);
}

fwrite(STDERR, "TILDAS relay running, Windows {$WINDOWS_IP}:{$WINDOWS_PORT}\n");

while (true) {
    $client = @stream_socket_accept($server, -1);
    if ($client === false) {
        continue;
    }

    stream_set_timeout($client, 2);

    /* read full payload from client */
    $payload = "";

    while (!feof($client)) {
        $line = fgets($client, 4096);
        if ($line === false) {
            break;
        }
        $payload .= $line;
    }

    if ($payload === "") {
        fclose($client);
        continue;
    }

    if (!connectWindows()) {
        fwrite($client, "ERROR\n");
        fclose($client);
        sleep(1);
        continue;
    }

    $written = fwrite($windows, $payload);
    fflush($windows);

    if ($written === false || $written === 0) {
        resetWindows();
        fwrite($client, "ERROR\n");
        fclose($client);
        continue;
    }

    /* ACK client, do NOT read from Windows */
    fwrite($client, "OK\n");
    fflush($client);
    fclose($client);
}
