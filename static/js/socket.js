/**
 * Socket.IO Connection Management
 * Handles real-time communication with the server
 */

// Fallback polling when websocket is disconnected
let __previewPollTimer = null;

function initializeSocket() {
    socket = io({
        path: '/socket.io',
        transports: ['websocket', 'polling'],
        reconnection: true,
        reconnectionAttempts: Infinity,
        reconnectionDelay: 1000,
        reconnectionDelayMax: 10000
    });
    
    socket.on('connect', function() {
        updateConnectionStatus(true);
        showNotification('Connected to LED Matrix', 'success');
        stopPreviewPolling();
    });
    
    socket.on('disconnect', function() {
        updateConnectionStatus(false);
        showNotification('Disconnected from LED Matrix', 'error');
        // Try to reconnect with exponential backoff
        let attempt = 0;
        const retry = () => {
            attempt++;
            const delay = Math.min(30000, 1000 * Math.pow(2, attempt));
            setTimeout(() => {
                if (socket.connected) return;
                socket.connect();
            }, delay);
        };
        retry();
        startPreviewPolling();
    });
    
    socket.on('connect_error', function(_err) {
        updateConnectionStatus(false);
        startPreviewPolling();
    });
    
    socket.on('display_update', function(data) {
        updateDisplayPreview(data);
    });
    
    socket.on('ondemand_error', function(data) {
        showNotification(`On-demand error: ${data.error}`, 'error');
        refreshOnDemandStatus();
    });
}

function updateConnectionStatus(connected) {
    const status = document.getElementById('connectionStatus');
    if (connected) {
        status.className = 'connection-status connected';
        status.innerHTML = '<i class="fas fa-wifi"></i> Connected';
    } else {
        status.className = 'connection-status disconnected';
        status.innerHTML = '<i class="fas fa-wifi"></i> Disconnected';
    }
}

function startPreviewPolling() {
    if (__previewPollTimer) return;
    __previewPollTimer = setInterval(fetchCurrentDisplayOnce, 1000);
}

function stopPreviewPolling() {
    if (__previewPollTimer) clearInterval(__previewPollTimer);
    __previewPollTimer = null;
}

async function fetchCurrentDisplayOnce() {
    try {
        const res = await fetch('/api/display/current');
        const data = await res.json();
        if (data && data.image) updateDisplayPreview(data);
    } catch (_) {}
}

