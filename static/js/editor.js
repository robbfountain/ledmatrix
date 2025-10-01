/**
 * Display Editor
 * Handles the visual display editor for creating custom layouts
 */

function initializeEditor() {
    // Initialize drag and drop for editor elements
    const paletteItems = document.querySelectorAll('.palette-item');
    paletteItems.forEach(item => {
        item.addEventListener('dragstart', function(e) {
            e.dataTransfer.setData('text/plain', this.dataset.type);
        });
    });

    // Make display preview a drop zone
    const preview = document.getElementById('displayPreview');
    preview.addEventListener('dragover', function(e) {
        e.preventDefault();
    });
    
    preview.addEventListener('drop', function(e) {
        e.preventDefault();
        const elementType = e.dataTransfer.getData('text/plain');
        const rect = preview.getBoundingClientRect();
        const scaleInput = document.getElementById('scaleRange');
        const scale = scaleInput ? parseInt(scaleInput.value || '8') : 8;
        const x = Math.floor((e.clientX - rect.left) / scale);
        const y = Math.floor((e.clientY - rect.top) / scale);
        
        addElement(elementType, x, y);
    });
}

function addElement(type, x, y) {
    const element = {
        id: Date.now(),
        type: type,
        x: x,
        y: y,
        properties: getDefaultProperties(type, x, y)
    };
    
    currentElements.push(element);
    updatePreview();
    selectElement(element);
}

function getDefaultProperties(type, baseX, baseY) {
    switch (type) {
        case 'text':
            return {
                text: 'Sample Text',
                color: [255, 255, 255],
                font_size: 'normal'
            };
        case 'weather_icon':
            return {
                condition: 'sunny',
                size: 16
            };
        case 'rectangle':
            return {
                width: 20,
                height: 10,
                color: [255, 255, 255]
            };
        case 'line':
            return {
                x2: (baseX || 0) + 20,
                y2: baseY || 0,
                color: [255, 255, 255]
            };
        default:
            return {};
    }
}

async function updatePreview() {
    if (!editorMode) return;
    
    try {
        const response = await fetch('/api/editor/preview', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                elements: currentElements
            })
        });
        const result = await response.json();
        if (result.status !== 'success') {
            showNotification(result.message, 'error');
        }
    } catch (error) {
        showNotification('Error updating preview: ' + error.message, 'error');
    }
}

function selectElement(element) {
    selectedElement = element;
    updatePropertiesPanel();
}

function updatePropertiesPanel() {
    const panel = document.getElementById('elementProperties');
    if (!selectedElement) {
        panel.innerHTML = '<p>Select an element to edit its properties</p>';
        return;
    }

    let html = `<h5>${selectedElement.type.toUpperCase()} Properties</h5>`;
    html += `<div class="form-group">
                <label>X Position</label>
                <input type="number" class="form-control" value="${selectedElement.x}" 
                       onchange="updateElementProperty('x', parseInt(this.value))">
             </div>`;
    html += `<div class="form-group">
                <label>Y Position</label>
                <input type="number" class="form-control" value="${selectedElement.y}" 
                       onchange="updateElementProperty('y', parseInt(this.value))">
             </div>`;

    // Add type-specific properties
    if (selectedElement.type === 'text') {
        html += `<div class="form-group">
                    <label>Text</label>
                    <input type="text" class="form-control" value="${selectedElement.properties.text}" 
                           onchange="updateElementProperty('properties.text', this.value)">
                 </div>`;
    }

    panel.innerHTML = html;
}

function updateElementProperty(path, value) {
    if (!selectedElement) return;
    
    const keys = path.split('.');
    let obj = selectedElement;
    
    for (let i = 0; i < keys.length - 1; i++) {
        if (!obj[keys[i]]) obj[keys[i]] = {};
        obj = obj[keys[i]];
    }
    
    obj[keys[keys.length - 1]] = value;
    updatePreview();
}

function clearEditor() {
    currentElements = [];
    selectedElement = null;
    updatePreview();
    updatePropertiesPanel();
}

async function saveLayout() {
    try {
        const response = await fetch('/api/config/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                type: 'layout',
                data: {
                    elements: currentElements,
                    timestamp: Date.now()
                }
            })
        });
        const result = await response.json();
        showNotification(result.message, result.status);
    } catch (error) {
        showNotification('Error saving layout: ' + error.message, 'error');
    }
}

async function loadLayout() {
    try {
        const res = await fetch('/api/editor/layouts');
        const data = await res.json();
        if (data.status === 'success' && data.data && data.data.elements) {
            currentElements = data.data.elements;
            selectedElement = null;
            updatePreview();
            updatePropertiesPanel();
            showNotification('Layout loaded', 'success');
        } else {
            showNotification('No saved layout found', 'warning');
        }
    } catch (err) {
        showNotification('Error loading layout: ' + err, 'error');
    }
}

