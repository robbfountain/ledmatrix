/**
 * Utility Functions
 * Helper functions for notifications, color conversion, and common operations
 */

// Show notification to user
function showNotification(message, type) {
    const notification = document.getElementById('notification');
    notification.textContent = message;
    notification.className = `notification ${type} show`;
    
    setTimeout(() => {
        notification.classList.remove('show');
    }, 3000);
}

// Convert hex color to RGB array
function hexToRgbArray(hex) {
    const m = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return m ? [parseInt(m[1], 16), parseInt(m[2], 16), parseInt(m[3], 16)] : [255, 255, 255];
}

// Convert RGB array to hex color
function rgbToHex(arr) {
    const [r, g, b] = arr || [255, 255, 255];
    const toHex = v => ('0' + Math.max(0, Math.min(255, v)).toString(16)).slice(-2);
    return `#${toHex(r)}${toHex(g)}${toHex(b)}`;
}

// Create FormData from object
function makeFormData(obj) {
    const fd = new FormData();
    Object.entries(obj).forEach(([k, v]) => fd.append(k, v));
    return fd;
}

// Update brightness display value
function updateBrightnessDisplay(value) {
    document.getElementById('brightness-value').textContent = value;
}

// Generic JSON save using existing endpoint
async function saveConfigJson(fragment) {
    try {
        const response = await fetch('/save_config', {
            method: 'POST',
            body: makeFormData({
                config_type: 'main',
                config_data: JSON.stringify(fragment)
            })
        });
        const result = await response.json();
        showNotification(result.message || 'Saved', result.status || 'success');
    } catch (error) {
        showNotification('Error saving configuration: ' + error, 'error');
    }
}

// JSON validation and formatting
function formatJson(elementId) {
    const textarea = document.getElementById(elementId);
    const jsonText = textarea.value;
    
    try {
        const parsed = JSON.parse(jsonText);
        const formatted = JSON.stringify(parsed, null, 4);
        textarea.value = formatted;
        
        textarea.classList.remove('error');
        textarea.classList.add('valid');
        
        showNotification('JSON formatted successfully!', 'success');
    } catch (error) {
        showNotification(`Cannot format invalid JSON: ${error.message}`, 'error');
        textarea.classList.remove('valid');
        textarea.classList.add('error');
    }
}

function validateJson(textareaId, validationId) {
    const textarea = document.getElementById(textareaId);
    const validationDiv = document.getElementById(validationId);
    const jsonText = textarea.value;
    
    validationDiv.innerHTML = '';
    validationDiv.className = 'json-validation';
    validationDiv.style.display = 'block';
    
    const statusId = validationId.replace('-validation', '-status');
    const statusElement = document.getElementById(statusId);
    
    try {
        const parsed = JSON.parse(jsonText);
        
        validationDiv.className = 'json-validation success';
        if (statusElement) {
            statusElement.textContent = 'VALID';
            statusElement.className = 'json-status valid';
        }
        validationDiv.innerHTML = `
            <div><strong>✅ JSON is valid!</strong></div>
            <div>✓ Valid JSON syntax<br>✓ Proper structure<br>✓ No obvious issues detected</div>
        `;
        
    } catch (error) {
        validationDiv.className = 'json-validation error';
        if (statusElement) {
            statusElement.textContent = 'INVALID';
            statusElement.className = 'json-status error';
        }
        
        validationDiv.innerHTML = `
            <div><strong>❌ Invalid JSON syntax</strong></div>
            <div><strong>Error:</strong> ${error.message}</div>
        `;
    }
}

async function saveRawJson(configType) {
    const textareaId = configType === 'main' ? 'main-config-json' : 'secrets-config-json';
    const textarea = document.getElementById(textareaId);
    const jsonText = textarea.value;
    
    try {
        JSON.parse(jsonText);
    } catch (error) {
        showNotification(`Invalid JSON format: ${error.message}`, 'error');
        return;
    }
    
    const configName = configType === 'main' ? 'Main Configuration' : 'Secrets Configuration';
    if (!confirm(`Are you sure you want to save changes to the ${configName}?`)) {
        return;
    }
    
    try {
        const response = await fetch('/save_raw_json', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                config_type: configType,
                config_data: jsonText
            })
        });
        const data = await response.json();
        showNotification(data.message, data.status);
    } catch (error) {
        showNotification(`Error saving configuration: ${error}`, 'error');
    }
}

