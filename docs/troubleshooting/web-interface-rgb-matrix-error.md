# Troubleshooting: Web Interface RGB Matrix Initialization Error

**Date**: October 6, 2025  
**Issue**: Web interface crashes when pressing on-demand sports buttons (e.g., MLB "upcoming")  
**Severity**: Critical - Web service unable to start properly

---

## Symptom

When pressing the "upcoming" button under the Sports tab (MLB section) in the web interface, the following error appears immediately and the service stops:

```
INFO:src.display_manager:Initializing RGB Matrix with settings: rows=32, cols=64, chain_length=2, parallel=1, hardware_mapping=b'regular'
Need root. You are configured to use the hardware pulse generator for
	smooth color rendering, however the necessary hardware
	registers can't be accessed because you probably don't run
	with root permissions or privileges have been dropped.
	So you either have to run as root (e.g. using sudo) or
	supply the --led-no-hardware-pulse command-line flag.

	Exiting; run as root or with --led-no-hardware-pulse
```

---

## Initial Hypothesis (Incorrect)

At first, this appeared to be a simple permissions issue where the web interface wasn't running with root privileges. However, investigation revealed a more complex problem.

---

## Investigation Process

### Step 1: Check Service Status

```bash
sudo systemctl status ledmatrix-web
```

**Finding**: Service was in a crash-loop, repeatedly failing and restarting every 10 seconds.

### Step 2: Review Service Configuration

```bash
cat /home/ledpi/LEDMatrix/ledmatrix-web.service
```

**Finding**: Service was correctly configured to run as `User=root`, so permissions should have been adequate.

### Step 3: Check Service Logs

```bash
sudo journalctl -u ledmatrix-web.service -n 50 --no-pager
```

**Critical Discovery**: The real error was hidden in the logs:

```
Oct 06 09:32:46 ledpi ledmatrix-web[158664]: Installing rgbmatrix module...
Oct 06 09:32:46 ledpi ledmatrix-web[158664]: Failed to install dependencies: Command '['/usr/bin/python3', '-m', 'pip', 'install', '--break-system-packages', '-e', '/home/ledpi/LEDMatrix/rpi-rgb-led-matrix-master/bindings/python']' returned non-zero exit status 2.
Oct 06 09:32:46 ledpi ledmatrix-web[158664]: Failed to install dependencies. Exiting.
Oct 06 09:32:46 ledpi systemd[1]: ledmatrix-web.service: Main process exited, code=exited, status=1/FAILURE
```

The web service was **failing to start entirely** because it couldn't install the `rgbmatrix` Python module during initialization.

### Step 4: Attempt Manual Installation

```bash
sudo /usr/bin/python3 -m pip install --break-system-packages -e rpi-rgb-led-matrix-master/bindings/python
```

**Error Output**:
```
ERROR: Exception:
...
AssertionError: Egg-link does not match installed location of rgbmatrix (at /home/ledpi/LEDMatrix/rpi-rgb-led-matrix-master/bindings/python)
```

**Root Cause Identified**: The `rgbmatrix` module had a **corrupted installation** with mismatched egg-link files, preventing pip from reinstalling or uninstalling it.

---

## Root Causes

1. **Corrupted Python Package**: The `rgbmatrix` module had a broken egg-link at `/usr/local/lib/python3.11/dist-packages/rgbmatrix.egg-link` that pointed to an incorrect or inconsistent location.

2. **Service Startup Failure**: The `start_web_conditionally.py` script attempts to install dependencies on every startup, including the rgbmatrix module. When this fails, the entire service crashes.

3. **Secondary Issue**: After fixing the rgbmatrix installation, encountered a new error where Flask-SocketIO refused to run with Werkzeug in production mode without explicit permission.

---

## Resolution Steps

### Fix 1: Remove Corrupted rgbmatrix Installation

**Step 1**: Locate the corrupted egg-link file:
```bash
sudo find /usr/local/lib/python3.11 -name "rgbmatrix*" 2>/dev/null
```

**Output**:
```
/usr/local/lib/python3.11/dist-packages/rgbmatrix.egg-link
```

**Step 2**: Remove the corrupted egg-link files:
```bash
sudo rm /usr/local/lib/python3.11/dist-packages/rgbmatrix.egg-link
sudo rm -f /usr/local/lib/python3.11/dist-packages/easy-install.pth
```

**Step 3**: Rebuild and reinstall the rgbmatrix module from source:
```bash
cd /home/ledpi/LEDMatrix/rpi-rgb-led-matrix-master/bindings/python
sudo /usr/bin/python3 setup.py build
sudo /usr/bin/python3 -m pip install --break-system-packages -e .
```

**Expected Output**:
```
Successfully installed rgbmatrix-0.0.1
```

### Fix 2: Allow Werkzeug in Production Mode

**Issue**: Flask-SocketIO now enforces a production guard when running with Werkzeug (threading mode).

**Solution**: Add `allow_unsafe_werkzeug=True` parameter to the `socketio.run()` call.

**File**: `/home/ledpi/LEDMatrix/web_interface_v2.py`

**Change** (around line 1674):
```python
# Before:
socketio.run(
    app,
    host='0.0.0.0',
    port=5001,
    debug=False,
    use_reloader=False
)

# After:
socketio.run(
    app,
    host='0.0.0.0',
    port=5001,
    debug=False,
    use_reloader=False,
    allow_unsafe_werkzeug=True
)
```

### Fix 3: Restart the Web Service

```bash
sudo systemctl restart ledmatrix-web
```

---

## Verification

### Check Service Status
```bash
sudo systemctl status ledmatrix-web
```

**Expected Output**:
```
● ledmatrix-web.service - LED Matrix Web Interface Service
     Loaded: loaded (/etc/systemd/system/ledmatrix-web.service; enabled; preset: enabled)
     Active: active (running) since Mon 2025-10-06 09:35:52 EDT
```

### Verify Web Interface is Running
```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:5001/
```

**Expected Output**: `200`

### Check Process Owner
```bash
ps aux | grep "web_interface_v2.py" | grep -v grep
```

**Expected Output**: Process running as `root`

### Test in Browser

1. Navigate to `http://[your-pi-ip]:5001`
2. Go to the Sports tab → MLB section
3. Click the "upcoming" button
4. The display should show MLB upcoming games without crashing

---

## Why This Happened

1. **Pip Egg-Link Corruption**: The editable installation (`-e` flag) of the rgbmatrix module created an egg-link file. At some point, this link became invalid (possibly due to:
   - Moving the repository directory
   - Reinstalling Python
   - Interrupted pip installation
   - Manual file system changes)

2. **Service Design**: The `start_web_conditionally.py` script reinstalls dependencies on every service start. While this ensures dependencies are always up-to-date, it also means a corrupted package will prevent the service from starting entirely.

3. **Flask-SocketIO Update**: A recent update to Flask-SocketIO added stricter production safety checks, requiring explicit acknowledgment when using Werkzeug (the development server) in production.

---

## Prevention Measures

### 1. Monitor Service Startup
Set up monitoring for the ledmatrix-web service:

```bash
# Check service startup logs regularly
sudo journalctl -u ledmatrix-web.service --since "10 minutes ago"
```

### 2. Consider Using a Virtual Environment
While currently using `--break-system-packages`, consider creating a dedicated virtual environment for the LED Matrix project to isolate dependencies and avoid system-wide package corruption.

### 3. Improve Error Handling in Startup Script
Modify `start_web_conditionally.py` to:
- Log detailed error information
- Attempt recovery (e.g., remove corrupted packages before reinstalling)
- Send notifications when startup fails

### 4. Pin Python Package Versions
In `requirements_web_v2.txt`, consider pinning specific versions to avoid unexpected breaking changes:

```txt
flask-socketio==5.3.x  # Pin to specific version
```

---

## Related Issues

### Hardware Access Conflict
**Note**: The original error message about "need root" can also occur if:
- Both the main `ledmatrix` service AND the web interface's on-demand feature try to access the hardware simultaneously
- The on-demand feature should only be used when the main service is stopped

**Check main service status**:
```bash
sudo systemctl status ledmatrix
```

**If active, stop it before using on-demand features**:
```bash
sudo systemctl stop ledmatrix
```

### Configuration File Permission Issues
**Related**: If you encounter permission denied errors when saving configuration changes through the web interface, see:
- [Config File Permission Denied Troubleshooting](config-file-permission-denied.md)

This is a separate but related issue where the web service user doesn't have write permissions to `config/config.json`.

---

## Technical Details

### What is an Egg-Link?
An egg-link is a file created by pip when installing a package in "editable" mode (`pip install -e`). It contains the path to the package's source directory, allowing changes to the source code to be immediately reflected without reinstalling.

**Structure**:
```
/path/to/source/directory
.
```

### Why Did It Break?
The egg-link file contained a path that no longer matched the actual package location, causing pip to:
- Fail to uninstall the package (can't verify location)
- Fail to install over it (detects existing install but can't remove it)
- Enter a broken state where the package appears installed but isn't functional

### The Fix
By manually removing the egg-link and reinstalling from source, we:
1. Cleared the corrupted metadata
2. Rebuilt the C extensions (rgbmatrix has native code)
3. Created a fresh, valid egg-link

---

## Additional Resources

- [Flask-SocketIO Documentation](https://flask-socketio.readthedocs.io/)
- [rpi-rgb-led-matrix Library](https://github.com/hzeller/rpi-rgb-led-matrix)
- [Python Packaging User Guide - Editable Installs](https://pip.pypa.io/en/stable/topics/local-project-installs/#editable-installs)

---

## Troubleshooting Checklist

If this issue occurs again:

- [ ] Check service logs: `sudo journalctl -u ledmatrix-web.service -n 50`
- [ ] Verify rgbmatrix installation: `python3 -c "import rgbmatrix; print('OK')"`
- [ ] Check for egg-link files: `find /usr/local/lib -name "*.egg-link"`
- [ ] Test manual install: `sudo pip install --break-system-packages -e rpi-rgb-led-matrix-master/bindings/python`
- [ ] Verify web interface is running as root: `ps aux | grep web_interface`
- [ ] Ensure main ledmatrix service is stopped if using on-demand: `sudo systemctl stop ledmatrix`
- [ ] Check file permissions in assets directory: `ls -la assets/sports/`

---

## Summary

The issue was **not** primarily a permissions problem, despite the error message suggesting otherwise. The web service was failing to start entirely due to a corrupted Python package installation, which prevented the service from even reaching the point where it would initialize the LED matrix hardware.

**Key Lesson**: Always check service startup logs (`journalctl`) when a service isn't behaving as expected. The actual error may occur much earlier in the startup process than where symptoms manifest.

