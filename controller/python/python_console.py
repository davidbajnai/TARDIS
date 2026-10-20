# Imports ----------------------------------------------------------------------

import codecs
import fcntl
import json
import os
from pathlib import Path
import re
import select
import signal
import subprocess
import sys
import tempfile
import time

from pymemcache.client import base


# Configuration ----------------------------------------------------------------

script_path = Path(__file__).resolve().with_name("serialComm.py")
console_key = "tardis:python-console"
output_limit = 16384


# Process identification --------------------------------------------------------

def python_script_argument(arguments):
    # Match the executed script, including python3 -u, never a later argument.
    index = 1
    while index < len(arguments):
        argument = arguments[index]
        if argument in ("-", "-c", "-m") or argument.startswith(("-c", "-m")):
            return None
        if argument == "--":
            return arguments[index + 1] if index + 1 < len(arguments) else None
        if argument in ("-W", "-X", "--check-hash-based-pycs"):
            index += 2
        elif argument.startswith("-"):
            index += 1
        else:
            return argument
    return None


def find_serial_processes():
    process_ids = []
    for process_dir in Path("/proc").iterdir():
        if not process_dir.name.isdigit():
            continue
        try:
            arguments = [os.fsdecode(argument) for argument in
                         (process_dir / "cmdline").read_bytes().split(b"\0")
                         if argument]
            if not arguments or not re.fullmatch(
                r"python(?:\d+(?:\.\d+)*)?", Path(arguments[0]).name
            ):
                continue
            argument = python_script_argument(arguments)
            if argument is None or Path(argument).name != script_path.name:
                continue
            candidate = Path(argument)
            if not candidate.is_absolute():
                candidate = (process_dir / "cwd").resolve() / candidate
            if candidate.resolve() == script_path:
                process_ids.append(int(process_dir.name))
        except FileNotFoundError:
            continue  # The process exited during the scan.
    return process_ids


# Bounded terminal display -----------------------------------------------------

class TerminalBuffer:
    def __init__(self):
        self.history = ""
        self.line = ""
        self.cursor = 0

    def append(self, text):
        for character in text:
            if character == "\r":
                # serialComm.py redraws its speed/error line every second.
                self.cursor = 0
            elif character == "\n":
                self.history = (self.history + self.line + "\n")[-output_limit:]
                self.line = ""
                self.cursor = 0
            else:
                self.line = (self.line[:self.cursor] + character
                             + self.line[self.cursor + 1:])
                self.cursor += 1
                if len(self.line) > output_limit:
                    self.line = self.line[-output_limit:]
                    self.cursor = min(self.cursor, output_limit)

    def text(self):
        return (self.history + self.line)[-output_limit:]


def cache_client():
    return base.Client(("127.0.0.1", 11211), connect_timeout=1, timeout=1)


def publish_console(cache, state, terminal, running):
    state.update(output=terminal.text(), running=running, updated_at=time.time())
    try:
        cache.set(console_key, json.dumps(state), expire=30 if running else 300,
                  noreply=False)
    except Exception:
        # A failed display update must not stop draining the child's pipe.
        # The GUI detects a stale/missing snapshot; later updates can recover.
        cache.close()


# Detached output monitor ------------------------------------------------------

def monitor_output(lock_fd, ready_fd):
    cache = cache_client()
    terminal = TerminalBuffer()
    state = {"ok": True, "running": False, "pid": None, "exit_code": None}
    try:
        # Background shells may ignore SIGINT. Restore it before exec so Python
        # installs its normal KeyboardInterrupt handler for terminate.sh.
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        child = subprocess.Popen(
            [sys.executable, "-u", str(script_path)],
            cwd=script_path.parent, stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        state.update(pid=child.pid, running=True,
                     message="Python launched. Check the startup messages below.")
    except Exception as error:
        state.update(ok=False, message=f"Could not launch Python: {error}")
        os.write(ready_fd, json.dumps(state).encode("utf-8"))
        os.close(ready_fd)
        cache.close()
        os.close(lock_fd)
        return

    # Acknowledge only after the real child exists, while PHP still holds the
    # same request lock as STOP. The monitor owns no web-request output pipes.
    publish_console(cache, state, terminal, True)
    try:
        os.write(ready_fd, json.dumps({key: value for key, value in state.items()
                                    if key != "output"}).encode("utf-8"))
    except BrokenPipeError:
        pass  # A closed browser/request does not cancel communication.
    finally:
        os.close(ready_fd)

    decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")
    next_update = time.monotonic()
    try:
        while True:
            readable, _, _ = select.select([child.stdout], [], [], 0.25)
            if readable:
                chunk = os.read(child.stdout.fileno(), 4096)
                if not chunk:
                    break
                terminal.append(decoder.decode(chunk))
            if time.monotonic() >= next_update:
                publish_console(cache, state, terminal, True)
                next_update = time.monotonic() + 1
        terminal.append(decoder.decode(b"", final=True))
        state["exit_code"] = child.wait()
        state["message"] = f"Python stopped (exit code {state['exit_code']})."
        publish_console(cache, state, terminal, False)
    finally:
        child.stdout.close()
        cache.close()
        os.close(lock_fd)


# Launch or reopen the existing console ----------------------------------------

def start_communication():
    if not sys.platform.startswith("linux"):
        raise RuntimeError("Start PY must run on the Linux inlet computer.")
    if not script_path.is_file():
        raise RuntimeError(f"Communication script not found: {script_path}")

    # This empty lock file stores no terminal output. Keep the lock for the
    # monitor's lifetime, including startup and the child's shutdown cleanup.
    lock_path = Path(tempfile.gettempdir()) / "tardis-python-console.lock"
    with lock_path.open("a") as lock_file:
        try:
            fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return {"ok": True, "watch": True,
                    "message": "A GUI Python session already exists; reopening its output."}

        process_ids = find_serial_processes()
        if process_ids:
            return {"ok": True, "watch": False,
                    "message": "serialComm.py is already running (PID "
                               + ", ".join(map(str, process_ids))
                               + "). Its output remains in the terminal that started it."}

        cache = cache_client()
        try:
            # Fail before touching hardware if the console cannot be displayed.
            state = {"ok": True, "running": True, "pid": None, "output": "",
                     "message": "Starting Python...", "updated_at": time.time()}
            if not cache.set(console_key, json.dumps(state), expire=30,
                             noreply=False):
                raise RuntimeError("Could not initialize the in-memory console.")
        finally:
            cache.close()

        ready_read, ready_write = os.pipe()
        try:
            try:
                monitor = subprocess.Popen(
                    [sys.executable, str(Path(__file__).resolve()), "monitor",
                     str(lock_file.fileno()), str(ready_write)],
                    stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL, start_new_session=True,
                    pass_fds=(lock_file.fileno(), ready_write),
                )
            finally:
                os.close(ready_write)
            # The monitor only spawns the child before acknowledging; it does
            # not wait for serial devices. EOF also reports a failed monitor.
            response = os.read(ready_read, 4096)
            if not response:
                monitor.wait()
                raise RuntimeError("The Python output monitor could not start.")
            result = json.loads(response)
            result["watch"] = result["ok"]
            return result
        finally:
            os.close(ready_read)
        # Closing our lock fd leaves the inherited monitor lock held. Never
        # call LOCK_UN here: both descriptors share the same kernel lock.


# Entry point ------------------------------------------------------------------

if len(sys.argv) == 4 and sys.argv[1] == "monitor":
    monitor_output(int(sys.argv[2]), int(sys.argv[3]))
else:
    try:
        print(json.dumps(start_communication()))
    except Exception as error:
        print(json.dumps({"ok": False, "watch": False,
                          "message": f"Start PY failed: {error}"}))
        sys.exit(1)
