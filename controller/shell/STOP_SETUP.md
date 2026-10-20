# GUI STOP button

The red STOP button calls `controller/php/terminate.php`, which runs
`controller/shell/terminate.sh`. On success, the browser reloads the GUI and shows
the Z-position and manual TILDAS WD/BG reset warning again.

The STOP request is independent of `moveStatus`. Existing synchronous requests
can delay handling the click. No sequence variables, pending commands, or
existing request timings are changed by the button handler; the page reload
reinitializes the GUI after the reset succeeds. Failure leaves the page in place
and displays the error.

## Linux setup

The PHP endpoint runs the script directly as the web server's user, without
`sudo`. That user must also own the running `serialComm.py` process and have
access to the serial devices. An ordinary Apache worker cannot stop a process
owned by root.

These instructions assume PHP runs as `www-data` and the installation is
`/var/www/html`. If PHP-FPM uses a different account, use that account throughout.
Run the setup commands below in the Linux root terminal already used to start
Python. They require administrator access once; the STOP button does not.

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

Start Python in the terminal as the same user as PHP:

```bash
runuser -u www-data -- python3 /var/www/html/controller/python/serialComm.py
```

Use this launch command for subsequent runs as well. `runuser` is invoked from
the root terminal to switch to the unprivileged account; it is not called by the
button. Python remains attached to the terminal.

The `python3` environment used by that account must provide `pyserial`,
`pymemcache`, and `ujson`. PHP must allow `exec`. No sudoers rule is needed;
if the previous dedicated STOP rule was installed, it can be removed.

Before a hardware test, put Z at 50%. After clicking STOP, verify that the Python
terminal exits, the Arduino restarts, the GUI reloads, and the warning appears.
Reset WD/BG manually in TDLWintel and restart `serialComm.py` before operating the
inlet again.
