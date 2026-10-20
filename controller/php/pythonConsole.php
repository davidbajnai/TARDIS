<?php

// Accept only dedicated console requests --------------------------------------

header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store');
ini_set('display_errors', '0');

function consoleResponse(int $status, array $response): void
{
    http_response_code($status);
    echo json_encode($response);
    exit;
}

$method = $_SERVER['REQUEST_METHOD'] ?? '';
if (!in_array($method, ['GET', 'POST'], true)) {
    header('Allow: GET, POST');
    consoleResponse(405, ['ok' => false, 'message' => 'Use GET or POST.']);
}
// A cross-origin form cannot supply this header. No command comes from input.
if (($_SERVER['HTTP_X_TARDIS_PYTHON'] ?? '') !== '1') {
    consoleResponse(403, ['ok' => false, 'message' => 'Invalid Python console request.']);
}

// Read the bounded RAM buffer without starting or stopping Python --------------

if ($method === 'GET') {
    $cache = new Memcached();
    $cache->setOption(Memcached::OPT_CONNECT_TIMEOUT, 1000);
    $cache->setOption(Memcached::OPT_RECV_TIMEOUT, 1000000);
    $cache->addServer('127.0.0.1', 11211);
    $value = $cache->get('tardis:python-console');
    $cache->quit();
    $state = is_string($value) ? json_decode($value, true) : null;
    if (!is_array($state) || !isset($state['updated_at']) ||
        (($state['running'] ?? false) && time() - $state['updated_at'] > 5)) {
        consoleResponse(503, ['ok' => false, 'message' =>
            'Live output is unavailable. Python may still be running; use STOP to stop it.']);
    }
    consoleResponse(200, $state);
}

// Start the fixed helper under the same request lock as STOP -------------------

ignore_user_abort(true);
set_time_limit(20);
$scriptPath = realpath(__DIR__ . '/../python/python_console.py');
if ($scriptPath === false || !is_readable($scriptPath)) {
    consoleResponse(500, ['ok' => false, 'message' => 'Python console helper is missing.']);
}
$lock = fopen(sys_get_temp_dir() . '/tardis-stop.lock', 'c');
if ($lock === false) {
    consoleResponse(500, ['ok' => false, 'message' => 'Could not open the start/stop lock.']);
}
if (!flock($lock, LOCK_EX | LOCK_NB)) {
    fclose($lock);
    consoleResponse(409, ['ok' => false, 'message' =>
        'A start or STOP request is running. Wait for it to finish.']);
}

// The helper detaches its output monitor and communication process. PHP waits
// only for launch acknowledgement. Both processes run as PHP's user; no sudo.
$output = [];
$exitCode = 1;
exec('python3 ' . escapeshellarg($scriptPath) . ' 2>&1', $output, $exitCode);
flock($lock, LOCK_UN);
fclose($lock);
$result = json_decode(implode("\n", $output), true);
if (!is_array($result) || !array_key_exists('ok', $result)) {
    consoleResponse(500, ['ok' => false, 'message' =>
        "The Python launcher failed:\n" . implode("\n", $output)]);
}
consoleResponse($exitCode === 0 && $result['ok'] ? 200 : 500, $result);
