<?php

// Accept only the dedicated STOP request ---------------------------------------

header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store');
ini_set('display_errors', '0');

function stopResponse(int $status, bool $ok, string $message): void
{
    http_response_code($status);
    echo json_encode(['ok' => $ok, 'message' => $message]);
    exit;
}

if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') {
    header('Allow: POST');
    stopResponse(405, false, 'STOP requires a POST request.');
}
// A cross-origin form cannot supply this header. No command comes from input.
if (($_SERVER['HTTP_X_TARDIS_STOP'] ?? '') !== '1') {
    stopResponse(403, false, 'Invalid STOP request.');
}

// Execute the fixed reset script -----------------------------------------------

ignore_user_abort(true);
set_time_limit(30);
$scriptPath = realpath(__DIR__ . '/../shell/terminate.sh');
if ($scriptPath === false || !is_executable($scriptPath)) {
    stopResponse(500, false, 'STOP script is missing or is not executable.');
}

// Prevent overlapping reset requests from multiple tabs.
$lock = fopen(sys_get_temp_dir() . '/tardis-stop.lock', 'c');
if ($lock === false) {
    stopResponse(500, false, 'Could not create the STOP lock.');
}
if (!flock($lock, LOCK_EX | LOCK_NB)) {
    fclose($lock);
    stopResponse(409, false, 'A STOP request is already running. Wait for it to finish.');
}

// Run as Apache's user, which must also own serialComm.py and have serial access.
// See shell/STOP_SETUP.md; no privilege elevation is performed here.
$output = [];
$exitCode = 1;
exec(escapeshellarg($scriptPath) . ' 2>&1', $output, $exitCode);
flock($lock, LOCK_UN);
fclose($lock);

if ($exitCode !== 0) {
    error_log('TARDIS STOP failed: ' . implode("\n", $output));
    stopResponse(
        500,
        false,
        "STOP failed; the Arduino reset is not confirmed.\n" . implode("\n", $output)
    );
}

stopResponse(200, true, 'serialComm.py stopped and the Arduino reset pulse was sent.');
