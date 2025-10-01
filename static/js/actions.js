/**
 * System Actions
 * Handles system actions like restart, reboot, git pull, etc.
 */

async function systemAction(action) {
    if (action === 'reboot_system' && !confirm('Are you sure you want to reboot the system?')) {
        return;
    }
    if (action === 'migrate_config' && !confirm('This will migrate your configuration to add any new options with default values. A backup will be created automatically. Continue?')) {
        return;
    }
    
    try {
        const response = await fetch('/api/system/action', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: action })
        });
        const result = await response.json();
        showNotification(result.message, result.status);
    } catch (error) {
        showNotification('Error executing action: ' + error.message, 'error');
    }
}

async function runAction(actionName) {
    const outputElement = document.getElementById('action_output');
    if (outputElement) {
        outputElement.textContent = `Running ${actionName.replace(/_/g, ' ')}...`;
    }

    try {
        const response = await fetch('/run_action', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: actionName })
        });
        const data = await response.json();
        
        if (outputElement) {
            let outputText = `Status: ${data.status}\nMessage: ${data.message}\n`;
            if (data.stdout) outputText += `\n--- STDOUT ---\n${data.stdout}`;
            if (data.stderr) outputText += `\n--- STDERR ---\n${data.stderr}`;
            outputElement.textContent = outputText;
        }
        
        showNotification(data.message, data.status);
    } catch (error) {
        if (outputElement) {
            outputElement.textContent = `Error: ${error}`;
        }
        showNotification(`Error running action: ${error}`, 'error');
    }
}

function confirmShutdown() {
    if (!confirm('Are you sure you want to shut down the system? This will power off the Raspberry Pi.')) return;
    runAction('shutdown_system');
}

async function fetchLogs() {
    const logContent = document.getElementById('log-content');
    logContent.textContent = 'Loading logs...';

    try {
        const response = await fetch('/get_logs');
        const data = await response.json();
        
        if (data.status === 'success') {
            logContent.textContent = data.logs;
        } else {
            logContent.textContent = `Error loading logs: ${data.message}`;
        }
    } catch (error) {
        logContent.textContent = `Error loading logs: ${error}`;
    }
}

