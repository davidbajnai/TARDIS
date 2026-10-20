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

The terminal-started Python process runs as root, so Apache needs permission to
run this one script as root. These instructions assume the Apache user is
`www-data` and the installation is `/var/www/html`.

Ensure the script is executable and owned by root:

```bash
sudo chown root:root /var/www/html/controller/shell/terminate.sh
sudo chmod 755 /var/www/html/controller/shell/terminate.sh
```

The script and its parent directories must not be writable by `www-data`, so the
web server cannot replace the command that is allowed to run as root.

Open a dedicated sudoers file:

```bash
sudo visudo -f /etc/sudoers.d/tardis-stop
```

Add this exact rule. The final `""` permits no command-line arguments:

```sudoers
www-data ALL=(root) NOPASSWD: /var/www/html/controller/shell/terminate.sh ""
```

Validate the configuration without executing STOP:

```bash
sudo visudo -c
sudo -u www-data sudo -n -l -- /var/www/html/controller/shell/terminate.sh
```

Keep pyserial available to the root `python3` used by the already-tested script.
PHP must allow `exec`. If configuration is missing, the button reports failure
and does not claim that the Arduino was reset.

Before a hardware test, put Z at 50%. After clicking STOP, verify that the Python
terminal exits, the Arduino restarts, the GUI reloads, and the warning appears.
Reset WD/BG manually in TDLWintel and restart `serialComm.py` before operating the
inlet again.
