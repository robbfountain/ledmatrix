/**
 * State Management
 * Global variables and state management for the application
 */

// Global state variables
let socket;
let currentConfig = {};
let editorMode = false;
let currentElements = [];
let selectedElement = null;
let newsManagerData = {};

// Initialize state from server data
function initializeState() {
    const serverDataEl = document.getElementById('serverData');
    const serverData = serverDataEl ? JSON.parse(serverDataEl.textContent) : { main_config: {}, editor_mode: false };
    currentConfig = serverData.main_config || {};
    editorMode = !!serverData.editor_mode;
}

// Function to refresh the current config from the server
async function refreshCurrentConfig() {
    try {
        const response = await fetch('/api/config/main');
        if (response.ok) {
            const configData = await response.json();
            currentConfig = configData;
        }
    } catch (error) {
        console.warn('Failed to refresh current config:', error);
    }
}

// On-demand mode status
async function refreshOnDemandStatus() {
    try {
        const res = await fetch('/api/ondemand/status');
        const data = await res.json();
        if (data && data.on_demand) {
            const s = data.on_demand;
            const el = document.getElementById('ondemand-status');
            if (el) { 
                el.textContent = `On-Demand: ${s.running && s.mode ? s.mode : 'None'}`; 
            }
        }
    } catch (e) { 
        /* ignore */ 
    }
}

async function startOnDemand(mode) {
    try {
        const res = await fetch('/api/ondemand/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mode })
        });
        const data = await res.json();
        if (data.status === 'success') {
            showNotification(data.message || 'On-demand started successfully', 'success');
        } else {
            showNotification(data.message || 'Failed to start on-demand', 'error');
        }
        refreshOnDemandStatus();
    } catch (err) {
        showNotification('Error starting on-demand: ' + err, 'error');
    }
}

async function stopOnDemand() {
    try {
        const res = await fetch('/api/ondemand/stop', { method: 'POST' });
        const data = await res.json();
        showNotification(data.message || 'On-Demand stopped', data.status || 'success');
        refreshOnDemandStatus();
    } catch (err) {
        showNotification('Error stopping on-demand: ' + err, 'error');
    }
}

// System stats update
async function updateSystemStats() {
    try {
        const response = await fetch('/api/system/status');
        const stats = await response.json();
        
        // Update stats in the overview tab if they exist
        const cpuUsage = document.querySelector('.stat-card .stat-value');
        if (cpuUsage) {
            document.querySelectorAll('.stat-card .stat-value')[0].textContent = stats.cpu_percent + '%';
            document.querySelectorAll('.stat-card .stat-value')[1].textContent = stats.memory_used_percent + '%';
            document.querySelectorAll('.stat-card .stat-value')[2].textContent = stats.cpu_temp + '°C';
            document.querySelectorAll('.stat-card .stat-value')[5].textContent = stats.disk_used_percent + '%';
        }
        refreshOnDemandStatus();
    } catch (error) {
        console.error('Error updating system stats:', error);
    }
}

async function updateApiMetrics() {
    try {
        const res = await fetch('/api/metrics');
        const data = await res.json();
        if (data.status !== 'success') return;
        const el = document.getElementById('api-metrics');
        const w = Math.round((data.window_seconds || 86400) / 3600);
        const f = data.forecast || {};
        const u = data.used || {};
        el.innerHTML = `
            <div><strong>Window:</strong> ${w} hours</div>
            <div><strong>Weather:</strong> ${u.weather || 0} used / ${f.weather || 0} forecast</div>
            <div><strong>Stocks:</strong> ${u.stocks || 0} used / ${f.stocks || 0} forecast</div>
            <div><strong>Sports:</strong> ${u.sports || 0} used / ${f.sports || 0} forecast</div>
            <div><strong>News:</strong> ${u.news || 0} used / ${f.news || 0} forecast</div>
            <div><strong>Odds:</strong> ${u.odds || 0} used / ${f.odds || 0} forecast</div>
            <div><strong>Music:</strong> ${u.music || 0} used / ${f.music || 0} forecast</div>
            <div><strong>YouTube:</strong> ${u.youtube || 0} used / ${f.youtube || 0} forecast</div>
        `;
    } catch (e) {
        // ignore
    }
}

