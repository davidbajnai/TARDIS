# Imports ----------------------------------------------------------------------

import ast
import os
from pathlib import Path
import re
import signal
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock


# Load the embedded program without importing hardware dependencies -------------

shell_path = Path(__file__).resolve().parents[1] / "terminate.sh"
source = shell_path.read_text().split("<<'PY'\n", 1)[1].rsplit("\nPY", 1)[0]
program = ast.parse(source)
# Execute from the configuration assignments onward with mocked imports.
start = next(
    index for index, node in enumerate(program.body)
    if isinstance(node, ast.Assign)
)
program_code = compile(
    ast.Module(body=program.body[start:], type_ignores=[]), str(shell_path), "exec"
)
script_path = shell_path.parents[1] / "python" / "serialComm.py"


# Regression tests -------------------------------------------------------------

class TerminateTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.process_root = Path(self.temporary_directory.name)
        self.events = []
        self.stuck = False
        self.signal_denied = False
        self.elapsed = 0
        self.board = Mock()
        self.board.open.side_effect = lambda: self.events.append("open")
        self.board.__enter__ = Mock(return_value=self.board)
        self.board.__exit__ = Mock(return_value=False)
        self.serial = SimpleNamespace(
            Serial=Mock(return_value=self.board),
            SerialException=OSError,
            tools=SimpleNamespace(list_ports=SimpleNamespace(
                comports=lambda: [SimpleNamespace(
                    device="/dev/mock", serial_number="8503631363035151D102"
                )]
            )),
        )
        self.namespace = {
            "Path": self.map_path,
            "os": SimpleNamespace(
                fsdecode=os.fsdecode, getpid=lambda: 200, kill=self.send_signal
            ),
            "re": re,
            "signal": signal,
            "sys": SimpleNamespace(
                argv=["-", str(script_path)], platform="linux",
                exit=self.exit_program,
            ),
            "serial": self.serial,
            "time": SimpleNamespace(
                monotonic=lambda: self.elapsed, sleep=self.advance_time
            ),
            "print": Mock(),
        }

    def map_path(self, value):
        return self.process_root if str(value) == "/proc" else Path(value)

    def advance_time(self, seconds):
        self.elapsed += seconds

    def exit_program(self, message):
        raise SystemExit(message)

    def add_process(self, process_id, arguments):
        process_dir = self.process_root / str(process_id)
        process_dir.mkdir()
        (process_dir / "cmdline").write_bytes(
            b"\0".join(os.fsencode(argument) for argument in arguments) + b"\0"
        )
        (process_dir / "cwd").symlink_to(script_path.parent, target_is_directory=True)

    def send_signal(self, process_id, sent_signal):
        self.assertEqual(process_id, 100, "An unrelated process was signalled")
        self.assertEqual(sent_signal, signal.SIGINT)
        self.events.append("stop")
        if self.signal_denied:
            raise PermissionError("Permission denied")
        if not self.stuck:
            (self.process_root / str(process_id) / "cmdline").write_bytes(b"")

    def run_program(self):
        exec(program_code, self.namespace)

    def test_helper_is_not_signalled_and_reset_is_reached(self):
        self.add_process(100, ["python3", str(script_path)])
        self.add_process(200, ["python3", "-", str(script_path)])
        # Also exclude another stdin helper, independently of the PID guard.
        self.add_process(201, ["python3", "-", str(script_path)])
        self.run_program()
        self.assertEqual(self.events, ["stop", "open"])
        self.assertTrue(self.board.dtr)
        self.assertEqual(self.board.port, "/dev/mock")
        self.board.__exit__.assert_called_once()

    def test_current_pid_is_always_excluded(self):
        self.add_process(200, ["python3", str(script_path)])
        self.run_program()
        self.assertEqual(self.events, ["open"])

    def test_relative_script_path_and_interpreter_options(self):
        self.add_process(100, [
            "/venv/bin/python3.10", "-u", "-W", "default", "-X", "dev",
            "--", "serialComm.py",
        ])
        self.run_program()
        self.assertEqual(self.events, ["stop", "open"])

    def test_unrelated_commands_are_not_signalled(self):
        commands = [
            ["python3", "-c", "pass", str(script_path)],
            ["python3", "-mpackage", str(script_path)],
            ["python3", "other.py", str(script_path)],
            ["python3", "/unrelated/serialComm.py"],
            ["bash", str(script_path)],
        ]
        for process_id, arguments in enumerate(commands, start=300):
            self.add_process(process_id, arguments)
        self.run_program()
        self.assertEqual(self.events, ["open"])

    def test_no_running_script_still_resets_board(self):
        self.run_program()
        self.assertEqual(self.events, ["open"])

    def test_shutdown_timeout_prevents_reset(self):
        self.add_process(100, ["python3", str(script_path)])
        self.stuck = True
        with self.assertRaisesRegex(SystemExit, "did not stop"):
            self.run_program()
        self.serial.Serial.assert_not_called()

    def test_permission_failure_prevents_reset(self):
        self.add_process(100, ["python3", str(script_path)])
        self.signal_denied = True
        with self.assertRaisesRegex(SystemExit, "Permission denied"):
            self.run_program()
        self.serial.Serial.assert_not_called()

    def test_missing_board_prevents_shutdown(self):
        self.add_process(100, ["python3", str(script_path)])
        self.serial.tools.list_ports.comports = lambda: []
        with self.assertRaisesRegex(SystemExit, "exactly one"):
            self.run_program()
        self.assertEqual(self.events, [])


# Run tests --------------------------------------------------------------------

unittest.main()
