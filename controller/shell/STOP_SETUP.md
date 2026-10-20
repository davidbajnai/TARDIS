# GUI Start PY and STOP buttons

The yellow Start PY button calls `controller/php/pythonConsole.php`. Its Python
helper, `controller/python/python_console.py`, launches `serialComm.py` as the
web-server user with unbuffered output. A detached helper drains stdout/stderr
even after the popup or browser closes. Start PY reopens an existing GUI session
and refuses to launch another copy when a terminal-started copy is found.

The popup refreshes about once per second. It shows up to 16,384 characters held
in the existing Memcached service under the separate `tardis:python-console` key;
no terminal output logfile is written. Carriage returns redraw the speed/error
line. Output expires five minutes after Python exits. Missing or stale output is
reported as unavailable, not as proof that Python has stopped. The empty
`/tmp/tardis-python-console.lock` file coordinates GUI launches; it is not a log.

Start and STOP share a request lock. No start is queued during a reset. Do not
also start Python manually while a GUI launch is in progress. Neither button
changes the communication JSON, command formats, or sequence logic.

The red STOP button calls `controller/php/terminate.php`, which runs
`controller/shell/terminate.sh`. On success, the browser reloads the GUI and shows
the Z-position and manual TILDAS WD/BG reset warning again.

The STOP request is independent of `moveStatus`. Existing synchronous requests
can delay handling the click. No sequence variables, pending commands, or
existing request timings are changed by the button handler; the page reload
reinitializes the GUI after the reset succeeds. Failure leaves the page in place
and displays the error.

## Linux setup

The PHP endpoints run their scripts directly as the web server's user, without
`sudo`. That user must also own the running `serialComm.py` process and have
access to the serial devices. An ordinary Apache worker cannot stop a process
owned by root.

These instructions assume PHP runs as `www-data` and the installation is
`/var/www/html`. If PHP-FPM uses a different account, use that account throughout.
Run the setup commands below in the Linux root terminal already used to start
Python. They require administrator access once; the GUI buttons do not.

First put Z at 50% and stop the existing root-owned `serialComm.py` with Ctrl+C
in its terminal. Do not start a second copy alongside it.

Check which group owns the serial devices:

```bash
ls -l /dev/ttyS0 /dev/ttyACM* /dev/ttyUSB*
```

On a typical Debian/Ubuntu installation this is `dialout`. If the listing
confirms that group, grant access and restart Apache so its workers receive
the updated group membership:

```bash
usermod -aG dialout www-data
chmod 755 /var/www/html/controller/shell/terminate.sh
systemctl restart apache2
```

If PHP runs through PHP-FPM, restart that PHP-FPM service too. If a device has
a different owning group, grant access through its actual device group instead.

For normal operation, click Start PY. Confirm the successful connection messages
and updating speed/error line in its popup before operating the inlet. Opening
the Arduino connection can reset it, so Z must be at 50% before starting.

For troubleshooting from an ordinary terminal:

```bash
python3 /var/www/html/controller/python/serialComm.py
```

Stop that copy with Ctrl+C. It belongs to the terminal user, so GUI STOP cannot
stop it if PHP runs as a different user. To troubleshoot with PHP's ownership,
use the following instead, from a **root terminal**:

```bash
runuser -u www-data -- python3 /var/www/html/controller/python/serialComm.py
```

`runuser` is only for switching accounts from a root terminal; it is not called
by either button. This manual launch remains attached to the terminal.

To stop a background copy and reset the Arduino from a terminal, run:

```bash
/var/www/html/controller/shell/terminate.sh
```

Run this as the process owner or root. In particular, an ordinary `david`
terminal cannot stop GUI-started Python owned by `www-data`; use GUI STOP or a
root terminal. Keep Z at 50% and reset WD/BG manually afterwards.

The `python3` environment used by that account must provide `pyserial`,
`pymemcache`, and `ujson`. PHP must allow `exec`. No sudoers rule is needed;
if the previous dedicated STOP rule was installed, it can be removed.

## Check on the Linux inlet computer

With Z at 50% and no measurement running, click Start PY and check the connection
messages followed by the updating speed/error line. Close the popup, confirm the
GUI still updates, and reopen it with Start PY; the process PID should remain
the same. Then click STOP: Python should exit, the Arduino should reset, and the
GUI should reload with the warning. Reset WD/BG manually in TDLWintel and use
Start PY to restart communication before operating the inlet again. A failed
Python startup should leave its error/traceback visible in the popup.
