/**
 * Display Preview and LED Rendering
 * Handles the LED matrix display preview, grid overlay, and LED dot rendering
 */

// Draw pixel grid lines on top of scaled image
function drawGrid(canvas, logicalWidth, logicalHeight, scale) {
    const show = document.getElementById('toggleGrid')?.checked;
    if (!canvas || !show) return;
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.strokeStyle = 'rgba(255,255,255,0.12)';
    ctx.lineWidth = 1;

    // Vertical lines
    for (let x = 0; x <= logicalWidth; x++) {
        const px = Math.floor(x * scale) + 0.5;
        ctx.beginPath();
        ctx.moveTo(px, 0);
        ctx.lineTo(px, logicalHeight * scale);
        ctx.stroke();
    }

    // Horizontal lines
    for (let y = 0; y <= logicalHeight; y++) {
        const py = Math.floor(y * scale) + 0.5;
        ctx.beginPath();
        ctx.moveTo(0, py);
        ctx.lineTo(logicalWidth * scale, py);
        ctx.stroke();
    }
}

// Update display preview with better scaling and error handling
function updateDisplayPreview(data) {
    const preview = document.getElementById('displayPreview');
    const stage = document.getElementById('previewStage');
    const img = document.getElementById('displayImage');
    const canvas = document.getElementById('gridOverlay');
    const ledCanvas = document.getElementById('ledCanvas');
    const placeholder = document.getElementById('displayPlaceholder');

    if (data.image) {
        // Show stage
        placeholder.style.display = 'none';
        stage.style.display = 'inline-block';

        // Current scale from slider
        const scale = parseInt(document.getElementById('scaleRange').value || '8');

        // Update image and meta label
        img.style.imageRendering = 'pixelated';
        img.onload = () => {
            // Ensure LED dot overlay samples after image is ready
            renderLedDots();
        };
        img.src = `data:image/png;base64,${data.image}`;
        const meta = document.getElementById('previewMeta');
        if (meta) {
            // Use config dimensions as fallback
            const configWidth = data.width || 128;
            const configHeight = data.height || 32;
            meta.textContent = `${configWidth} x ${configHeight} @ ${scale}x`;
        }

        // Once image loads, size the canvas to match
        const width = (data.width || 128) * scale;
        const height = (data.height || 32) * scale;
        img.style.width = width + 'px';
        img.style.height = height + 'px';
        ledCanvas.width = width;
        ledCanvas.height = height;
        canvas.width = width;
        canvas.height = height;
        drawGrid(canvas, data.width || 128, data.height || 32, scale);
        renderLedDots();
    } else {
        stage.style.display = 'none';
        placeholder.style.display = 'block';
        placeholder.innerHTML = `<div style="color: #666; font-size: 1.2rem;">
            <i class="fas fa-exclamation-triangle"></i>
            No display data available
        </div>`;
    }
}

function renderLedDots() {
    const ledCanvas = document.getElementById('ledCanvas');
    const img = document.getElementById('displayImage');
    const toggle = document.getElementById('toggleLedDots');
    if (!ledCanvas || !img || !toggle) return;
    const show = toggle.checked;
    ledCanvas.style.display = show ? 'block' : 'none';
    if (!show) return;

    const scale = parseInt(document.getElementById('scaleRange').value || '8');
    const fillPct = parseInt(document.getElementById('dotFillRange').value || '75');
    const dotRadius = Math.max(1, Math.floor((scale * fillPct) / 200)); // radius in px
    const ctx = ledCanvas.getContext('2d');
    ctx.clearRect(0, 0, ledCanvas.width, ledCanvas.height);

    // Clear previous overlay; do not forcibly black-out if sampling fails
    ctx.clearRect(0, 0, ledCanvas.width, ledCanvas.height);

    // Create an offscreen canvas to sample pixel colors
    const off = document.createElement('canvas');
    const logicalWidth = Math.floor(ledCanvas.width / scale);
    const logicalHeight = Math.floor(ledCanvas.height / scale);
    off.width = logicalWidth;
    off.height = logicalHeight;
    const offCtx = off.getContext('2d', { willReadFrequently: true });
    // Draw the current image scaled down to logical LEDs to sample colors
    try {
        offCtx.drawImage(img, 0, 0, logicalWidth, logicalHeight);
    } catch (_) { /* draw failures ignored */ }

    // Draw circular dots for each LED pixel
    let drawn = 0;
    for (let y = 0; y < logicalHeight; y++) {
        for (let x = 0; x < logicalWidth; x++) {
            const pixel = offCtx.getImageData(x, y, 1, 1).data;
            const r = pixel[0], g = pixel[1], b = pixel[2], a = pixel[3];
            // Skip fully black to reduce overdraw
            if (a === 0 || (r | g | b) === 0) continue;
            ctx.fillStyle = `rgb(${r},${g},${b})`;
            const cx = Math.floor(x * scale + scale / 2);
            const cy = Math.floor(y * scale + scale / 2);
            ctx.beginPath();
            ctx.arc(cx, cy, dotRadius, 0, Math.PI * 2);
            ctx.fill();
            drawn++;
        }
    }

    // If nothing was drawn (e.g., image not ready), hide overlay to show base image
    if (drawn === 0) {
        ledCanvas.style.display = 'none';
    }
}

// Initialize display controls
function initializeDisplayControls() {
    // UI controls for grid & scale
    const scaleRange = document.getElementById('scaleRange');
    const scaleValue = document.getElementById('scaleValue');
    const toggleGrid = document.getElementById('toggleGrid');
    const gridCanvas = document.getElementById('gridOverlay');

    if (scaleRange && scaleValue) {
        scaleRange.addEventListener('input', () => {
            scaleValue.textContent = `${scaleRange.value}x`;
            // Repaint grid at new scale using latest known dimensions
            fetch('/api/display/current')
                .then(r => r.json())
                .then(data => {
                    if (!data || !data.width || !data.height) return;
                    // Resize image and canvas
                    const img = document.getElementById('displayImage');
                    const scale = parseInt(scaleRange.value || '8');
                    img.style.width = `${data.width * scale}px`;
                    img.style.height = `${data.height * scale}px`;
                    gridCanvas.width = data.width * scale;
                    gridCanvas.height = data.height * scale;
                    drawGrid(gridCanvas, data.width, data.height, scale);
                    renderLedDots();
                })
                .catch(() => {});
        });
    }

    if (toggleGrid && gridCanvas) {
        toggleGrid.addEventListener('change', () => {
            gridCanvas.style.display = toggleGrid.checked ? 'block' : 'none';
            if (toggleGrid.checked) {
                // Redraw grid with current size
                fetch('/api/display/current')
                    .then(r => r.json())
                    .then(data => {
                        if (!data || !data.width || !data.height) return;
                        const scale = parseInt((document.getElementById('scaleRange')?.value) || '8');
                        drawGrid(gridCanvas, data.width, data.height, scale);
                    })
                    .catch(() => {});
            }
        });
        // default hidden
        gridCanvas.style.display = 'none';
    }

    // LED dot mode controls
    const toggleLedDots = document.getElementById('toggleLedDots');
    const dotFillRange = document.getElementById('dotFillRange');
    const dotFillValue = document.getElementById('dotFillValue');
    if (dotFillRange && dotFillValue) {
        dotFillRange.addEventListener('input', () => {
            dotFillValue.textContent = `${dotFillRange.value}%`;
            renderLedDots();
        });
    }
    if (toggleLedDots) {
        toggleLedDots.addEventListener('change', renderLedDots);
        // Ensure dot mode is rendered on load if enabled by default
        if (toggleLedDots.checked) {
            setTimeout(renderLedDots, 200);
        }
    }
}

// Display control functions
async function startDisplay() {
    await runAction('start_display');
}

async function stopDisplay() {
    await runAction('stop_display');
}

async function toggleEditorMode() {
    try {
        const response = await fetch('/api/editor/toggle', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        const result = await response.json();
        showNotification(result.message, result.status);
        
        if (result.status === 'success') {
            editorMode = result.editor_mode;
            location.reload(); // Reload to update UI
        }
    } catch (error) {
        showNotification('Error toggling editor mode: ' + error.message, 'error');
    }
}

async function takeScreenshot() {
    try {
        const response = await fetch('/api/display/current');
        const data = await response.json();
        
        if (data.image) {
            // Create download link
            const link = document.createElement('a');
            link.href = 'data:image/png;base64,' + data.image;
            link.download = 'led_matrix_screenshot_' + new Date().getTime() + '.png';
            link.click();
            showNotification('Screenshot saved', 'success');
        } else {
            showNotification('No display data available', 'warning');
        }
    } catch (error) {
        showNotification('Error taking screenshot: ' + error.message, 'error');
    }
}

