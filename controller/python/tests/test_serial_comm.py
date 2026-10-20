# Imports ----------------------------------------------------------------------

import ast
from contextlib import redirect_stderr, redirect_stdout
import io
import math
from pathlib import Path
import queue
import re
import runpy
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from pymemcache.client import base
import serial
import serial.tools.list_ports
import ujson


# Test helpers -----------------------------------------------------------------

script_path = Path(__file__).resolve().parents[1] / "serialComm.py"
arduino_path = script_path.parents[1] / "arduino" / "Ardu" / "Ardu.ino"


def load_definitions():
    # The production script intentionally starts at top level. Load its actual
    # parsers/workers without running port discovery or opening any connections.
    tree = ast.parse(script_path.read_text())
    constant_names = {
        "arduino_status_keys", "arduino_move_statuses", "arduino_text_keys"
    }
    definitions = []
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom, ast.FunctionDef)):
            definitions.append(node)
        elif isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id in constant_names
            for target in node.targets
        ):
            definitions.append(node)
    namespace = {"__name__": "serial_comm_test"}
    exec(compile(ast.Module(body=definitions, type_ignores=[]), str(script_path),
                 "exec"), namespace)
    namespace.update(
        lock=threading.Lock(), stop_event=threading.Event(),
        worker_errors=queue.Queue(), vacuum="0.0000",
    )
    return namespace


def valid_arduino_status():
    return {
        "moveStatus": "-", "X_position": "50.00", "X_percentage": "50.0",
        "Y_position": "50.00", "Y_percentage": "50.0", "Z_position": "7980",
        "Z_percentage": "50.00", "X_pressure": "1.700", "Y_pressure": "1.700",
        "Z_pressure": "366.0", "valveArray": "01" * 16, "relayArray": "01",
        "boxHumidity": "45.00", "boxTemperature": "32.5000",
        "boxSetpoint": "32.50", "fanSpeed": "50.00", "D_pressure": "0.0",
        "arduinoSpeed": "12",
    }


def encode_status(status):
    return ujson.dumps(status).encode('utf-8') + b'\r\n'


def laser_line(pressure="40.1236"):
    return f"0,123456.7,23456.7,345678.9,4567.8,0,0,0,0,0,{pressure}\r\n".encode()


class EndOfInput(Exception):
    pass


def run_communication_iterations(namespace, arduino_lines, laser_lines,
                                 commands=None):
    arduino_port = Mock()
    arduino_port.readline.side_effect = [*arduino_lines, EndOfInput()]
    arduino_port.write.side_effect = len
    laser_port = Mock(in_waiting=20)
    laser_port.readline.side_effect = [*laser_lines, b'']
    cache = Mock()
    cache.get.side_effect = commands or [None] * len(arduino_lines)
    namespace.update(arduino=arduino_port, laser=laser_port, m=cache)
    with redirect_stdout(io.StringIO()):
        try:
            namespace['loop_2']()
        except EndOfInput:
            pass
    return arduino_port, cache


def published_statuses(cache):
    return [ujson.loads(call.args[1]) for call in cache.set.call_args_list
            if call.args[0] == 'key']


# Parsing and compatibility tests ----------------------------------------------

class StatusParsingTests(unittest.TestCase):
    def test_all_current_arduino_keys_and_statuses_match(self):
        namespace = load_definitions()
        source = arduino_path.read_text()
        self.assertEqual(
            tuple(re.findall(r'doc\["([^"]+)"\]', source)),
            namespace['arduino_status_keys'],
        )
        emitted_statuses = set(re.findall(r'sendStatus\("([^"]+)"\)', source))
        emitted_statuses.update(re.findall(r'wait\(\d+, "([^"]+)"\)', source))
        self.assertEqual(emitted_statuses, namespace['arduino_move_statuses'])
        for move_status in emitted_statuses:
            status = valid_arduino_status()
            status['moveStatus'] = move_status
            self.assertEqual(namespace['parse_arduino_status'](encode_status(status)),
                             status)

    def test_invalid_arduino_frames_are_rejected(self):
        namespace = load_definitions()
        valid = valid_arduino_status()
        invalid_values = [
            [], list(range(18)), None, "unexpected", 1,
            {str(index): "0" for index in range(18)},
            {key: value for key, value in valid.items() if key != 'fanSpeed'},
            {**valid, 'unexpected': '0'},
            {**valid, 'moveStatus': 'finished'},
            {**valid, 'valveArray': '0' * 31},
            {**valid, 'valveArray': '0' * 31 + 'X'},
            {**valid, 'relayArray': '012'},
            {**valid, 'relayArray': '0X'},
            {**valid, 'Z_percentage': '-0.1'},
            {**valid, 'Z_percentage': '100.1'},
            {**valid, 'X_pressure': '-1.001'},
            {**valid, 'Y_pressure': '7.001'},
        ]
        numeric_keys = set(valid) - namespace['arduino_text_keys']
        for key in numeric_keys:
            for value in ('nan', 'inf', '-inf', '1e999', '', 'bad', None, 0, True):
                invalid_values.append({**valid, key: value})
        frames = [encode_status(value) for value in invalid_values]
        frames.extend([b'', b'{', b'{}\n', b'\xff\n', encode_status(valid).rstrip()])
        for frame in frames:
            with self.subTest(frame=frame):
                with self.assertRaises((ValueError, UnicodeDecodeError)):
                    namespace['parse_arduino_status'](frame)

    def test_existing_bounds_and_potentiometer_values_remain_accepted(self):
        namespace = load_definitions()
        for pressure in ('-1.000', '7.000'):
            for percentage in ('0.00', '100.00'):
                status = valid_arduino_status()
                status.update(X_pressure=pressure, Y_pressure=pressure,
                              Z_percentage=percentage, X_percentage='-2.0',
                              Y_percentage='103.0')
                self.assertEqual(namespace['parse_arduino_status'](encode_status(status)),
                                 status)

    def test_laser_conversion_and_extra_fields_remain_compatible(self):
        namespace = load_definitions()
        expected = {
            'chi_627': 123.457, 'chi_628': 23.457, 'chi_626': 345.679,
            'free_path_CO2': 4.568, 'cellPressure': 40.124,
        }
        self.assertEqual(namespace['parse_laser_status'](laser_line()), expected)
        self.assertEqual(namespace['parse_laser_status'](
            laser_line().rstrip() + b',extra\n'), expected)

    def test_laser_line_endings_remain_compatible(self):
        namespace = load_definitions()
        expected = namespace['parse_laser_status'](laser_line())
        for ending in (b'', b'\r', b'\n', b'\r\n'):
            self.assertEqual(namespace['parse_laser_status'](
                laser_line().rstrip() + ending), expected)

    def test_invalid_laser_frames_are_rejected(self):
        namespace = load_definitions()
        frames = [b'', b'bad,not-a-number,0,0\n', b'\xff\n']
        for index in (1, 2, 3, 4, 10):
            for value in ('bad', 'nan', 'inf', '-inf', '1e999'):
                fields = laser_line().decode().strip().split(',')
                fields[index] = value
                frames.append((','.join(fields) + '\n').encode())
        for frame in frames:
            with self.subTest(frame=frame):
                with self.assertRaises((ValueError, UnicodeDecodeError)):
                    namespace['parse_laser_status'](frame)


# Communication and supervision tests ------------------------------------------

class CommunicationTests(unittest.TestCase):
    def test_bad_frames_preserve_last_good_status_and_commands_continue(self):
        namespace = load_definitions()
        first = valid_arduino_status()
        first['moveStatus'] = 'MX'
        last = {**first, 'moveStatus': '-', 'X_position': '60.00'}
        arduino_port, cache = run_communication_iterations(
            namespace,
            [encode_status(first), encode_status(list(range(18))), encode_status(last)],
            [laser_line(), b'bad,not-a-number,0,0\n', laser_line('41.2345')],
            [b'V01O', None, b'BZ50.0'],
        )
        statuses = published_statuses(cache)
        self.assertEqual(len(statuses), 3)
        # The publication timestamp may cross a second boundary in this test.
        self.assertEqual(
            {key: value for key, value in statuses[1].items() if key != 'time'},
            {key: value for key, value in statuses[0].items() if key != 'time'},
        )
        self.assertEqual(statuses[2]['X_position'], '60.00')
        self.assertEqual(statuses[2]['moveStatus'], '-')
        self.assertEqual(statuses[2]['cellPressure'], 41.234)
        expected_keys = set(first) | {
            'time', 'vacuum', 'cellPressure', 'chi_627', 'chi_628', 'chi_626',
            'free_path_CO2',
        }
        for status in statuses:
            self.assertEqual(set(status), expected_keys)
            self.assertTrue(all(isinstance(status[key], str) for key in first))
            self.assertTrue(all(math.isfinite(status[key]) for key in (
                'cellPressure', 'chi_627', 'chi_628', 'chi_626', 'free_path_CO2')))
        self.assertEqual([call.args[0] for call in arduino_port.write.call_args_list],
                         [b'V01O', b'BZ50.0'])
        self.assertEqual(arduino_port.flush.call_count, 2)
        self.assertEqual([call.args for call in cache.set.call_args_list
                          if call.args[0] == 'key2'], [('key2', ''), ('key2', '')])

    def test_invalid_first_status_is_not_published(self):
        namespace = load_definitions()
        arduino_port, cache = run_communication_iterations(
            namespace, [b'broken\n'], [b'broken\n'], [b'V01C'],
        )
        self.assertEqual(published_statuses(cache), [])
        arduino_port.write.assert_called_once_with(b'V01C')

    def test_partial_write_stops_without_retry_or_clearing_command(self):
        namespace = load_definitions()
        arduino_port = Mock()
        arduino_port.readline.return_value = encode_status(valid_arduino_status())
        arduino_port.write.return_value = 2
        cache = Mock()
        cache.get.return_value = b'V01O'
        namespace.update(arduino=arduino_port, laser=Mock(in_waiting=0), m=cache)
        with self.assertRaisesRegex(OSError, 'Incomplete Arduino command write'):
            namespace['loop_2']()
        arduino_port.write.assert_called_once_with(b'V01O')
        arduino_port.flush.assert_not_called()
        self.assertFalse(any(call.args[0] == 'key2'
                             for call in cache.set.call_args_list))

    def test_worker_failure_stops_both_workers(self):
        namespace = load_definitions()
        worker = Mock(side_effect=serial.SerialException('device disconnected'))
        namespace['run_worker'](worker)
        self.assertTrue(namespace['stop_event'].is_set())
        name, error = namespace['worker_errors'].get_nowait()
        self.assertEqual(name, threading.current_thread().name)
        self.assertIsInstance(error, serial.SerialException)

    def test_unexpected_worker_return_is_reported(self):
        namespace = load_definitions()
        namespace['run_worker'](Mock())
        self.assertTrue(namespace['stop_event'].is_set())
        self.assertIsInstance(namespace['worker_errors'].get_nowait()[1], RuntimeError)

    def test_requested_worker_shutdown_is_not_reported_as_failure(self):
        namespace = load_definitions()
        namespace['stop_event'].set()
        namespace['run_worker'](Mock())
        self.assertTrue(namespace['worker_errors'].empty())

    def test_no_command_is_sent_after_shutdown_is_requested(self):
        namespace = load_definitions()
        arduino_port = Mock()
        arduino_port.readline.return_value = encode_status(valid_arduino_status())
        cache = Mock()
        def get_command(key):
            namespace['stop_event'].set()
            return b'V01O'
        cache.get.side_effect = get_command
        namespace.update(arduino=arduino_port, laser=Mock(in_waiting=0), m=cache)
        namespace['loop_2']()
        arduino_port.write.assert_not_called()

    def test_edwards_rejects_nonfinite_and_negative_readings(self):
        namespace = load_definitions()
        gauge = Mock()
        gauge.readline.side_effect = [b'1.23456\n', b'nan\n', b'inf\n', b'-1\n']
        namespace.update(edwards_gauge=gauge)
        with patch.object(namespace['stop_event'], 'wait',
                          side_effect=[False, False, False, EndOfInput()]):
            with self.assertRaises(EndOfInput):
                namespace['loop_1']()
        self.assertEqual(namespace['vacuum'], '1.2346')


# Full-script startup and shutdown tests ---------------------------------------

class ScriptLifecycleTests(unittest.TestCase):
    def test_disconnect_exits_nonzero_and_closes_every_connection(self):
        ports = [SimpleNamespace(serial_number='CHAAb131R01', device='/fake/edwards'),
                 SimpleNamespace(serial_number='8503631363035151D102', device='/fake/arduino')]
        arduino_port, laser_port, gauge, cache = Mock(), Mock(in_waiting=0), Mock(), Mock()
        arduino_port.readline.side_effect = serial.SerialException('test disconnect')
        gauge.readline.return_value = b'0.000000\n'
        output, errors = io.StringIO(), io.StringIO()
        with patch.object(serial.tools.list_ports, 'comports', return_value=ports), \
                patch.object(serial, 'Serial', side_effect=[arduino_port, laser_port, gauge]), \
                patch.object(base, 'Client', return_value=cache), \
                patch('time.sleep'), redirect_stdout(output), redirect_stderr(errors):
            with self.assertRaises(SystemExit) as result:
                runpy.run_path(str(script_path))
        self.assertEqual(result.exception.code, 1)
        self.assertIn('Arduino/TILDAS communication failed', errors.getvalue())
        self.assertIn('test disconnect', errors.getvalue())
        for connection in (arduino_port, laser_port, gauge, cache):
            connection.close.assert_called_once()
        arduino_port.write.assert_not_called()

    def test_startup_failure_closes_already_opened_port(self):
        ports = [SimpleNamespace(serial_number='CHAAb131R01', device='/fake/edwards'),
                 SimpleNamespace(serial_number='8503631363035151D102', device='/fake/arduino')]
        arduino_port = Mock()
        with patch.object(serial.tools.list_ports, 'comports', return_value=ports), \
                patch.object(serial, 'Serial', side_effect=[
                    arduino_port, serial.SerialException('laser unavailable')]), \
                patch('time.sleep'), redirect_stdout(io.StringIO()), \
                redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as result:
                runpy.run_path(str(script_path))
        self.assertEqual(result.exception.code, 1)
        arduino_port.close.assert_called_once()


# Run tests --------------------------------------------------------------------

unittest.main()
