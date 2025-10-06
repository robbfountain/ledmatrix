# Troubleshooting: Config File Permission Denied Error

**Date**: October 6, 2025  
**Issue**: Web interface shows "permission denied" when trying to save config/config.json  
**Severity**: Medium - Configuration changes cannot be saved through web interface

---

## Symptom

When attempting to save configuration changes through the web interface, users encounter a permission denied error:

```
Permission denied when saving config/config.json
```

This prevents users from updating settings, sports configurations, or display preferences through the web UI.

---

## Root Cause Analysis

### Step 1: Check File Permissions

```bash
ls -la config/config.json
```

**Typical Output**:
```
-rw-r--r-- 1 ledpi ledpi 19754 Oct  6 08:51 config/config.json
```

### Step 2: Check Service User

```bash
ps aux | grep web_interface_v2.py
```

**Finding**: The web service may be running as a different user than the file owner.

### Step 3: Check Service Configuration

```bash
cat /etc/systemd/system/ledmatrix-web.service
```

**Key Lines**:
```ini
[Service]
User=ledpi  # or User=root
```

---

## Root Causes

1. **User Mismatch**: The web service runs as one user (typically `root` or `daemon`) but the config file is owned by `ledpi`
2. **Insufficient Permissions**: The config file doesn't have write permissions for the user running the web service
3. **Service Configuration**: The systemd service may be configured to run as the wrong user

---

## Resolution Steps

### Solution 1: Fix Service User Configuration (Recommended)

**Step 1**: Update the service file to run as the correct user:

```bash
sudo nano /etc/systemd/system/ledmatrix-web.service
```

**Change**:
```ini
[Service]
User=ledpi  # Change from 'root' to 'ledpi'
WorkingDirectory=/home/ledpi/LEDMatrix
Environment=USE_THREADING=1
ExecStart=/usr/bin/python3 /home/ledpi/LEDMatrix/start_web_conditionally.py
Restart=on-failure
RestartSec=10
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=ledmatrix-web
```

**Step 2**: Reload systemd and restart the service:

```bash
sudo systemctl daemon-reload
sudo systemctl restart ledmatrix-web
```

**Step 3**: Verify the service is running as the correct user:

```bash
ps aux | grep web_interface_v2.py
```

**Expected Output**: Process should show `ledpi` as the user.

### Solution 2: Adjust File Permissions (Alternative)

If the service must run as root, ensure proper file permissions:

**Step 1**: Make the config file writable by the group:

```bash
chmod 664 config/config.json
```

**Step 2**: Add the web service user to the ledpi group:

```bash
sudo usermod -a -G ledpi [service-user]
```

### Solution 3: Temporary Fix (Not Recommended for Production)

**Warning**: This reduces security by making the file world-writable.

```bash
chmod 666 config/config.json
```

---

## Verification

### Check File Permissions

```bash
ls -la config/config.json
```

**Expected Output**:
```
-rw-rw-r-- 1 ledpi ledpi 19754 Oct  6 08:51 config/config.json
```

### Test Config Save

1. Navigate to the web interface: `http://[pi-ip]:5001`
2. Go to the Configuration section
3. Make a small change (e.g., adjust a setting)
4. Click "Save Configuration"
5. Verify the change was saved without errors

### Check Service Status

```bash
sudo systemctl status ledmatrix-web --no-pager
```

**Expected Output**:
```
● ledmatrix-web.service - LED Matrix Web Interface Service
     Loaded: loaded (/etc/systemd/system/ledmatrix-web.service; enabled; preset: enabled)
     Active: active (running)
```

---

## Prevention Measures

### 1. Consistent User Configuration

Ensure all services and files use consistent user ownership:

```bash
# Check ownership of key files
ls -la config/
ls -la src/
ls -la assets/
```

### 2. Service User Best Practices

- **Development**: Run services as `ledpi` user
- **Production**: Consider using a dedicated service user with appropriate permissions
- **Avoid**: Running services as `root` unless absolutely necessary

### 3. File Permission Monitoring

Create a simple script to check permissions:

```bash
#!/bin/bash
# check_permissions.sh
echo "Checking LED Matrix file permissions..."
ls -la config/config.json
ls -la config/
echo "Service status:"
ps aux | grep web_interface_v2.py | grep -v grep
```

### 4. Backup Configuration

Before making permission changes, always backup the config:

```bash
cp config/config.json config/config.json.backup.$(date +%Y%m%d_%H%M%S)
```

---

## Common Scenarios

### Scenario 1: Service Running as Root

**Problem**: Service runs as `root`, file owned by `ledpi`
**Solution**: Either change service to run as `ledpi` or give `root` write access

### Scenario 2: Service Running as Daemon

**Problem**: Service runs as `daemon` user (system user)
**Solution**: Change service configuration to use `ledpi` user

### Scenario 3: SELinux/AppArmor Restrictions

**Problem**: Security modules blocking file access
**Solution**: Check security module logs and adjust policies if needed

---

## Troubleshooting Checklist

If config save issues persist:

- [ ] Check file ownership: `ls -la config/config.json`
- [ ] Check service user: `ps aux | grep web_interface_v2.py`
- [ ] Verify service config: `cat /etc/systemd/system/ledmatrix-web.service`
- [ ] Check service logs: `sudo journalctl -u ledmatrix-web.service -n 20`
- [ ] Test manual file write: `sudo -u [service-user] touch config/test_write`
- [ ] Verify directory permissions: `ls -la config/`
- [ ] Check for file locks: `lsof config/config.json`
- [ ] Restart service: `sudo systemctl restart ledmatrix-web`

---

## Related Files

- **Config File**: `/home/ledpi/LEDMatrix/config/config.json`
- **Service File**: `/etc/systemd/system/ledmatrix-web.service`
- **Web Interface**: `/home/ledpi/LEDMatrix/web_interface_v2.py`
- **Startup Script**: `/home/ledpi/LEDMatrix/start_web_conditionally.py`

---

## Additional Resources

- [Systemd Service Configuration](https://www.freedesktop.org/software/systemd/man/systemd.service.html)
- [Linux File Permissions Guide](https://linuxize.com/post/linux-file-permissions/)
- [User and Group Management](https://ubuntu.com/server/docs/security-users)

---

## Summary

The permission denied error when saving configuration files is typically caused by a mismatch between the user running the web service and the owner of the configuration file. The recommended solution is to configure the systemd service to run as the same user who owns the project files (`ledpi`), ensuring consistent permissions across the system.

**Key Points**:
- Always check file ownership and service user configuration
- Use consistent user accounts across services and file ownership
- Test configuration changes after fixing permissions
- Keep backups of working configurations




