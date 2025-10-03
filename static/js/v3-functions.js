// Additional JavaScript functions for index_v3.html
// Ported from index_v2.html

let currentElements = [];
let selectedElement = null;
let newsManagerData = {};

async function refreshCurrentConfig() {
    try {
        const response = await fetch('/api/config/main');
        if (response.ok) {
            currentConfig = await response.json();
        }
    } catch (error) {
        console.warn('Failed to refresh current config:', error);
    }
}

async function refreshOnDemandStatus(){
    try{
        const res = await fetch('/api/ondemand/status');
        const data = await res.json();
        if(data && data.on_demand){
            const s = data.on_demand;
            const el = document.getElementById('ondemand-status');
            if(el){ el.textContent = `On-Demand: ${s.running && s.mode ? s.mode : 'None'}`; }
        }
    }catch(e){ }
}

async function startOnDemand(mode){
    try{
        const res = await fetch('/api/ondemand/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mode })
        });
        const data = await res.json();
        showNotification(data.message || (data.status === 'success' ? 'Started' : 'Failed'), data.status || 'info');
        refreshOnDemandStatus();
    }catch(err){
        showNotification('Error: ' + err, 'error');
    }
}

async function stopOnDemand(){
    try{
        const res = await fetch('/api/ondemand/stop', { method: 'POST' });
        const data = await res.json();
        showNotification(data.message || 'Stopped', data.status || 'success');
        refreshOnDemandStatus();
    }catch(err){
        showNotification('Error: ' + err, 'error');
    }
}

async function updateApiMetrics(){
    try {
        const res = await fetch('/api/metrics');
        const data = await res.json();
        if (data.status !== 'success') return;
        const el = document.getElementById('api-metrics');
        const w = Math.round((data.window_seconds || 86400) / 3600);
        const f = data.forecast || {};
        const u = data.used || {};
        
        // Update window display
        const windowEl = document.getElementById('api-window');
        if (windowEl) windowEl.textContent = `${w}h`;
        
        // Calculate total
        const totalUsed = (u.weather || 0) + (u.stocks || 0) + (u.sports || 0) + (u.news || 0);
        const totalForecast = (f.weather || 0) + (f.stocks || 0) + (f.sports || 0) + (f.news || 0);
        
        el.innerHTML = `
            <div class="bg-gray-50 rounded-lg p-4 text-center">
                <div class="text-3xl font-bold text-secondary">${u.weather || 0}/${f.weather || 0}</div>
                <div class="text-sm text-gray-600 mt-1">Weather</div>
            </div>
            <div class="bg-gray-50 rounded-lg p-4 text-center">
                <div class="text-3xl font-bold text-secondary">${u.stocks || 0}/${f.stocks || 0}</div>
                <div class="text-sm text-gray-600 mt-1">Stocks</div>
            </div>
            <div class="bg-gray-50 rounded-lg p-4 text-center">
                <div class="text-3xl font-bold text-secondary">${u.sports || 0}/${f.sports || 0}</div>
                <div class="text-sm text-gray-600 mt-1">Sports</div>
            </div>
            <div class="bg-gray-50 rounded-lg p-4 text-center">
                <div class="text-3xl font-bold text-secondary">${u.news || 0}/${f.news || 0}</div>
                <div class="text-sm text-gray-600 mt-1">News</div>
            </div>
            <div class="bg-gray-50 rounded-lg p-4 text-center">
                <div class="text-3xl font-bold text-secondary">${totalUsed}/${totalForecast}</div>
                <div class="text-sm text-gray-600 mt-1">Total</div>
            </div>
        `;
    } catch (e) { }
}

async function updateSystemStats() {
    try {
        await fetch('/api/system/status');
        refreshOnDemandStatus();
    } catch (error) {
        console.error('Error updating system stats:', error);
    }
}

function updateBrightnessDisplay(value) {
    const el = document.getElementById('brightness-value');
    if (el) el.textContent = value;
}

// Note: drawGrid, renderLedDots, updateDisplayPreview, toggleEditorMode, takeScreenshot 
// are defined inline in the HTML due to Jinja2 template variables

async function systemAction(action) {
    if (action === 'reboot_system' && !confirm('Are you sure you want to reboot?')) return;
    if (action === 'migrate_config' && !confirm('Migrate config? A backup will be created.')) return;
    try {
        const response = await fetch('/api/system/action', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({action: action})
        });
        const result = await response.json();
        showNotification(result.message, result.status);
    } catch (error) {
        showNotification('Error: ' + error.message, 'error');
    }
}

async function runAction(actionName) {
    const outputElement = document.getElementById('action_output');
    if (outputElement) outputElement.textContent = `Running ${actionName.replace(/_/g, ' ')}...`;
    try {
        const response = await fetch('/run_action', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: actionName })
        });
        const data = await response.json();
        let outputText = `Status: ${data.status}\nMessage: ${data.message}\n`;
        if (data.stdout) outputText += `\n--- STDOUT ---\n${data.stdout}`;
        if (data.stderr) outputText += `\n--- STDERR ---\n${data.stderr}`;
        if (outputElement) outputElement.textContent = outputText;
        showNotification(data.message, data.status);
    } catch (error) {
        if (outputElement) outputElement.textContent = `Error: ${error}`;
        showNotification(`Error: ${error}`, 'error');
    }
}

function confirmShutdown(){
    if (!confirm('Are you sure you want to shut down the system?')) return;
    runAction('shutdown_system');
}

async function fetchLogs() {
    const logContent = document.getElementById('log-content');
    logContent.textContent = 'Loading logs...';
    try {
        const response = await fetch('/get_logs');
        const data = await response.json();
        logContent.textContent = data.status === 'success' ? data.logs : `Error: ${data.message}`;
    } catch (error) {
        logContent.textContent = `Error: ${error}`;
    }
}

// Helper functions
function hexToRgbArray(hex){
    const m = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return m ? [parseInt(m[1],16), parseInt(m[2],16), parseInt(m[3],16)] : [255,255,255];
}

function rgbToHex(arr){
    const [r,g,b] = arr || [255,255,255];
    const toHex = v => ('0' + Math.max(0, Math.min(255, v)).toString(16)).slice(-2);
    return `#${toHex(r)}${toHex(g)}${toHex(b)}`;
}

async function saveConfigJson(fragment){
    try {
        const response = await fetch('/save_config', {
            method: 'POST',
            body: makeFormData({ config_type: 'main', config_data: JSON.stringify(fragment) })
        });
        const result = await response.json();
        showNotification(result.message || 'Saved', result.status || 'success');
    } catch (error) {
        showNotification('Error saving: ' + error, 'error');
    }
}

function makeFormData(obj){
    const fd = new FormData();
    Object.entries(obj).forEach(([k,v]) => fd.append(k, v));
    return fd;
}

// JSON functions
function formatJson(elementId) {
    const textarea = document.getElementById(elementId);
    try {
        const parsed = JSON.parse(textarea.value);
        textarea.value = JSON.stringify(parsed, null, 4);
        showNotification('JSON formatted successfully!', 'success');
    } catch (error) {
        showNotification(`Cannot format invalid JSON: ${error.message}`, 'error');
    }
}

function validateJson(textareaId, validationId) {
    const textarea = document.getElementById(textareaId);
    const validationDiv = document.getElementById(validationId);
    validationDiv.classList.remove('hidden');
    const statusElement = document.getElementById(validationId.replace('-validation', '-status'));
    try {
        JSON.parse(textarea.value);
        validationDiv.className = 'mt-2 p-3 rounded-lg text-sm bg-green-50 border border-green-200 text-green-800';
        if (statusElement) {
            statusElement.textContent = 'VALID';
            statusElement.className = 'absolute top-3 right-3 px-2 py-1 rounded text-xs font-bold text-white bg-success';
        }
        validationDiv.innerHTML = '<div><strong>✅ JSON is valid!</strong></div>';
    } catch (error) {
        validationDiv.className = 'mt-2 p-3 rounded-lg text-sm bg-red-50 border border-red-200 text-red-800';
        if (statusElement) {
            statusElement.textContent = 'INVALID';
            statusElement.className = 'absolute top-3 right-3 px-2 py-1 rounded text-xs font-bold text-white bg-accent';
        }
        validationDiv.innerHTML = `<div><strong>❌ Invalid JSON</strong></div><div>${error.message}</div>`;
    }
}

async function saveRawJson(configType) {
    const textareaId = configType === 'main' ? 'main-config-json' : 'secrets-config-json';
    const textarea = document.getElementById(textareaId);
    try { JSON.parse(textarea.value); } catch (error) {
        showNotification(`Invalid JSON: ${error.message}`, 'error');
        return;
    }
    const configName = configType === 'main' ? 'Main Configuration' : 'Secrets Configuration';
    if (!confirm(`Save changes to ${configName}?`)) return;
    try {
        const response = await fetch('/save_raw_json', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ config_type: configType, config_data: textarea.value })
        });
        const data = await response.json();
        showNotification(data.message, data.status);
    } catch (error) {
        showNotification(`Error: ${error}`, 'error');
    }
}

// News Manager Functions
async function loadNewsManagerData() {
    try {
        const response = await fetch('/news_manager/status');
        const data = await response.json();
        if (data.status === 'success') {
            newsManagerData = data.data;
            updateNewsManagerUI();
        }
    } catch (error) {
        console.error('Error loading news manager:', error);
    }
}

function updateNewsManagerUI() {
    document.getElementById('news_enabled').checked = newsManagerData.enabled || false;
    document.getElementById('headlines_per_feed').value = newsManagerData.headlines_per_feed || 2;
    document.getElementById('rotation_enabled').checked = newsManagerData.rotation_enabled !== false;
    
    const feedsGrid = document.getElementById('news_feeds_grid');
    feedsGrid.innerHTML = '';
    if (newsManagerData.available_feeds) {
        newsManagerData.available_feeds.forEach(feed => {
            const isEnabled = newsManagerData.enabled_feeds.includes(feed);
            const feedDiv = document.createElement('div');
            feedDiv.className = 'bg-white border border-gray-300 rounded-lg p-2';
            feedDiv.innerHTML = `
                <label class="flex items-center cursor-pointer">
                    <input type="checkbox" name="news_feed" value="${feed}" ${isEnabled ? 'checked' : ''} class="mr-2">
                    <span class="text-sm">${feed}</span>
                </label>
            `;
            feedsGrid.appendChild(feedDiv);
        });
    }
    updateCustomFeedsList();
    updateNewsStatus();
}

function updateCustomFeedsList() {
    const list = document.getElementById('custom_feeds_list');
    list.innerHTML = '';
    if (newsManagerData.custom_feeds) {
        Object.entries(newsManagerData.custom_feeds).forEach(([name, url]) => {
            const div = document.createElement('div');
            div.className = 'flex justify-between items-center p-3 bg-white border border-gray-300 rounded-lg';
            div.innerHTML = `
                <div><strong class="font-semibold">${name}</strong>: <span class="text-sm text-gray-600">${url}</span></div>
                <button onclick="removeCustomFeed('${name}')" class="bg-red-500 hover:bg-red-600 text-white px-3 py-1 rounded text-sm">Remove</button>
            `;
            list.appendChild(div);
        });
    }
}

function updateNewsStatus() {
    const statusDiv = document.getElementById('news_status');
    const enabledFeeds = newsManagerData.enabled_feeds || [];
    statusDiv.innerHTML = `
        <h4 class="font-semibold text-gray-700 mb-2">Current Status</h4>
        <p class="text-sm"><strong>Enabled:</strong> ${newsManagerData.enabled ? 'Yes' : 'No'}</p>
        <p class="text-sm"><strong>Active Feeds:</strong> ${enabledFeeds.join(', ') || 'None'}</p>
        <p class="text-sm"><strong>Headlines per Feed:</strong> ${newsManagerData.headlines_per_feed || 2}</p>
        <p class="text-sm"><strong>Total Custom Feeds:</strong> ${Object.keys(newsManagerData.custom_feeds || {}).length}</p>
    `;
}

async function saveNewsSettings() {
    const enabledFeeds = Array.from(document.querySelectorAll('input[name="news_feed"]:checked')).map(i => i.value);
    const enabled = document.getElementById('news_enabled').checked;
    try {
        await fetch('/news_manager/toggle', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ enabled }) });
        const response = await fetch('/news_manager/update_feeds', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ enabled_feeds: enabledFeeds, headlines_per_feed: parseInt(document.getElementById('headlines_per_feed').value) })
        });
        const data = await response.json();
        showNotification(data.message, data.status);
        if (data.status === 'success') loadNewsManagerData();
    } catch (error) {
        showNotification('Error: ' + error, 'error');
    }
}

async function addCustomFeed() {
    const name = document.getElementById('custom_feed_name').value.trim();
    const url = document.getElementById('custom_feed_url').value.trim();
    if (!name || !url) { showNotification('Please enter both name and URL', 'error'); return; }
    try {
        const response = await fetch('/news_manager/add_custom_feed', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, url })
        });
        const data = await response.json();
        showNotification(data.message, data.status);
        if (data.status === 'success') {
            document.getElementById('custom_feed_name').value = '';
            document.getElementById('custom_feed_url').value = '';
            loadNewsManagerData();
        }
    } catch (error) {
        showNotification('Error: ' + error, 'error');
    }
}

async function removeCustomFeed(name) {
    if (!confirm(`Remove feed "${name}"?`)) return;
    try {
        const response = await fetch('/news_manager/remove_custom_feed', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name })
        });
        const data = await response.json();
        showNotification(data.message, data.status);
        if (data.status === 'success') loadNewsManagerData();
    } catch (error) {
        showNotification('Error: ' + error, 'error');
    }
}

function refreshNewsStatus() {
    loadNewsManagerData();
    showNotification('News status refreshed', 'success');
}

const initColor = (input) => {
    if (!input) return;
    try { const rgb = JSON.parse(input.dataset.rgb || '[255,255,255]'); input.value = rgbToHex(rgb); } catch {}
};

async function saveNewsAdvancedSettings(){
    const newsTextColor = document.getElementById('news_text_color');
    const newsSepColor = document.getElementById('news_separator_color');
    if (newsTextColor) initColor(newsTextColor);
    if (newsSepColor) initColor(newsSepColor);
    await saveConfigJson({
        news_manager: {
            update_interval: parseInt(document.getElementById('news_update_interval').value),
            scroll_speed: parseFloat(document.getElementById('news_scroll_speed').value),
            scroll_delay: parseFloat(document.getElementById('news_scroll_delay').value),
            rotation_threshold: parseInt(document.getElementById('news_rotation_threshold').value),
            dynamic_duration: document.getElementById('news_dynamic_duration').checked,
            min_duration: parseInt(document.getElementById('news_min_duration').value),
            max_duration: parseInt(document.getElementById('news_max_duration').value),
            duration_buffer: parseFloat(document.getElementById('news_duration_buffer').value),
            font_size: parseInt(document.getElementById('news_font_size').value),
            font_path: document.getElementById('news_font_path').value,
            text_color: hexToRgbArray(newsTextColor.value),
            separator_color: hexToRgbArray(newsSepColor.value)
        }
    });
}

// Sports Configuration
async function refreshSportsConfig(){
    try {
        await refreshCurrentConfig();
        const cfg = currentConfig;
        const leaguePrefixes = {
            'nfl_scoreboard': 'nfl', 'mlb_scoreboard': 'mlb', 'milb_scoreboard': 'milb',
            'nhl_scoreboard': 'nhl', 'nba_scoreboard': 'nba', 'ncaa_fb_scoreboard': 'ncaa_fb',
            'ncaa_baseball_scoreboard': 'ncaa_baseball', 'ncaam_basketball_scoreboard': 'ncaam_basketball',
            'ncaam_hockey_scoreboard': 'ncaam_hockey', 'soccer_scoreboard': 'soccer'
        };
        const leagues = [
            { key: 'nfl_scoreboard', label: 'NFL' }, { key: 'mlb_scoreboard', label: 'MLB' },
            { key: 'milb_scoreboard', label: 'MiLB' }, { key: 'nhl_scoreboard', label: 'NHL' },
            { key: 'nba_scoreboard', label: 'NBA' }, { key: 'ncaa_fb_scoreboard', label: 'NCAA FB' },
            { key: 'ncaa_baseball_scoreboard', label: 'NCAA Baseball' },
            { key: 'ncaam_basketball_scoreboard', label: 'NCAAM Basketball' },
            { key: 'ncaam_hockey_scoreboard', label: 'NCAAM Hockey' },
            { key: 'soccer_scoreboard', label: 'Soccer' }
        ];
        const container = document.getElementById('sports-config');
        const html = leagues.map(l => {
            const sec = cfg[l.key] || {};
            const p = leaguePrefixes[l.key] || l.key;
            const fav = (sec.favorite_teams || []).join(', ');
            const displayModes = sec.display_modes || {};
            const liveModeEnabled = displayModes[`${p}_live`] ?? true;
            const recentModeEnabled = displayModes[`${p}_recent`] ?? true;
            const upcomingModeEnabled = displayModes[`${p}_upcoming`] ?? true;
            return `
                <div class="bg-gray-50 border border-gray-300 rounded-lg p-4">
                    <div class="flex justify-between items-center mb-3">
                        <label class="flex items-center cursor-pointer">
                            <input type="checkbox" data-league="${l.key}" class="sp-enabled mr-2" ${sec.enabled ? 'checked' : ''}>
                            <strong class="text-gray-800">${l.label}</strong>
                        </label>
                        <div class="flex gap-2">
                            <button type="button" onclick="startOnDemand('${p}_live')" class="bg-blue-500 hover:bg-blue-600 text-white px-2 py-1 rounded text-xs"><i class="fas fa-bolt mr-1"></i>Live</button>
                            <button type="button" onclick="startOnDemand('${p}_recent')" class="bg-blue-500 hover:bg-blue-600 text-white px-2 py-1 rounded text-xs"><i class="fas fa-bolt mr-1"></i>Recent</button>
                            <button type="button" onclick="startOnDemand('${p}_upcoming')" class="bg-blue-500 hover:bg-blue-600 text-white px-2 py-1 rounded text-xs"><i class="fas fa-bolt mr-1"></i>Upcoming</button>
                        </div>
                    </div>
                    <div class="space-y-2 mb-3">
                        <label class="flex items-center cursor-pointer bg-white border border-gray-200 rounded px-3 py-2 hover:border-gray-400 transition">
                            <input type="checkbox" data-league="${l.key}" class="sp-display-mode mr-2" data-mode="live" ${liveModeEnabled ? 'checked' : ''}>
                            <i class="fas fa-circle text-red-500 mr-2 text-xs"></i>
                            <span class="text-sm font-medium text-red-600">Live Mode</span>
                        </label>
                        <label class="flex items-center cursor-pointer bg-white border border-gray-200 rounded px-3 py-2 hover:border-gray-400 transition">
                            <input type="checkbox" data-league="${l.key}" class="sp-display-mode mr-2" data-mode="recent" ${recentModeEnabled ? 'checked' : ''}>
                            <i class="fas fa-history text-yellow-500 mr-2 text-xs"></i>
                            <span class="text-sm font-medium text-yellow-600">Recent Mode</span>
                        </label>
                        <label class="flex items-center cursor-pointer bg-white border border-gray-200 rounded px-3 py-2 hover:border-gray-400 transition">
                            <input type="checkbox" data-league="${l.key}" class="sp-display-mode mr-2" data-mode="upcoming" ${upcomingModeEnabled ? 'checked' : ''}>
                            <i class="fas fa-clock text-blue-500 mr-2 text-xs"></i>
                            <span class="text-sm font-medium text-blue-600">Upcoming Mode</span>
                        </label>
                    </div>
                    <div class="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                        <label class="flex items-center cursor-pointer">
                            <input type="checkbox" data-league="${l.key}" class="sp-live-priority mr-1" ${sec.live_priority ? 'checked' : ''}>
                            Live Priority
                        </label>
                        <label class="flex items-center cursor-pointer">
                            <input type="checkbox" data-league="${l.key}" class="sp-show-odds mr-1" ${sec.show_odds ? 'checked' : ''}>
                            Show Odds
                        </label>
                        <label class="flex items-center cursor-pointer">
                            <input type="checkbox" data-league="${l.key}" class="sp-favorites-only mr-1" ${sec.show_favorite_teams_only ? 'checked' : ''}>
                            Favorites Only
                        </label>
                        <div>
                            <input type="text" data-league="${l.key}" class="sp-favorites w-full px-2 py-1 border border-gray-300 rounded text-sm" value="${fav}" placeholder="DAL, NYY">
                            <p class="text-xs text-gray-500">Favorite teams</p>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
        container.innerHTML = html || 'No sports configuration found.';
    } catch (err) {
        document.getElementById('sports-config').innerHTML = '<div class="text-red-500">Failed to load sports configuration</div>';
    }
}

async function saveSportsConfig(){
    try {
        const leagues = document.querySelectorAll('.sp-enabled');
        const fragment = {};
        leagues.forEach(chk => {
            const key = chk.getAttribute('data-league');
            const leaguePrefixes = {
                'nfl_scoreboard': 'nfl', 'mlb_scoreboard': 'mlb', 'milb_scoreboard': 'milb',
                'nhl_scoreboard': 'nhl', 'nba_scoreboard': 'nba', 'ncaa_fb_scoreboard': 'ncaa_fb',
                'ncaa_baseball_scoreboard': 'ncaa_baseball', 'ncaam_basketball_scoreboard': 'ncaam_basketball',
                'soccer_scoreboard': 'soccer'
            };
            const p = leaguePrefixes[key] || key;
            const liveModeEnabled = document.querySelector(`.sp-display-mode[data-league="${key}"][data-mode="live"]`)?.checked || false;
            const recentModeEnabled = document.querySelector(`.sp-display-mode[data-league="${key}"][data-mode="recent"]`)?.checked || false;
            const upcomingModeEnabled = document.querySelector(`.sp-display-mode[data-league="${key}"][data-mode="upcoming"]`)?.checked || false;
            
            fragment[key] = {
                enabled: chk.checked,
                live_priority: document.querySelector(`.sp-live-priority[data-league="${key}"]`)?.checked || false,
                show_odds: document.querySelector(`.sp-show-odds[data-league="${key}"]`)?.checked || false,
                show_favorite_teams_only: document.querySelector(`.sp-favorites-only[data-league="${key}"]`)?.checked || false,
                favorite_teams: (document.querySelector(`.sp-favorites[data-league="${key}"]`)?.value || '').split(',').map(s => s.trim()).filter(Boolean),
                display_modes: {
                    [`${p}_live`]: liveModeEnabled,
                    [`${p}_recent`]: recentModeEnabled,
                    [`${p}_upcoming`]: upcomingModeEnabled
                }
            };
        });
        await saveConfigJson(fragment);
        showNotification('Sports configuration saved', 'success');
    } catch (err) {
        showNotification('Error: ' + err, 'error');
    }
}

// Editor Functions
function initializeEditor() {
    const items = document.querySelectorAll('[draggable="true"][data-type]');
    items.forEach(item => {
        item.addEventListener('dragstart', e => e.dataTransfer.setData('text/plain', item.dataset.type));
    });
    const preview = document.getElementById('displayPreview');
    preview.addEventListener('dragover', e => e.preventDefault());
    preview.addEventListener('drop', function(e) {
        e.preventDefault();
        const type = e.dataTransfer.getData('text/plain');
        const rect = preview.getBoundingClientRect();
        const scale = parseInt(document.getElementById('scaleRange').value || '8');
        addElement(type, Math.floor((e.clientX - rect.left) / scale), Math.floor((e.clientY - rect.top) / scale));
    });
}

function addElement(type, x, y) {
    currentElements.push({ id: Date.now(), type, x, y, properties: {} });
    updatePreview();
}

async function updatePreview() {
    if (!editorMode) return;
    try {
        await fetch('/api/editor/preview', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ elements: currentElements }) });
    } catch (error) {}
}

function clearEditor() {
    currentElements = [];
    selectedElement = null;
    updatePreview();
}

async function saveLayout() {
    try {
        const response = await fetch('/api/config/save', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ type: 'layout', data: { elements: currentElements, timestamp: Date.now() } })
        });
        const result = await response.json();
        showNotification(result.message, result.status);
    } catch (error) {
        showNotification('Error: ' + error.message, 'error');
    }
}

async function loadLayout(){
    try {
        const res = await fetch('/api/editor/layouts');
        const data = await res.json();
        if (data.status === 'success' && data.data?.elements) {
            currentElements = data.data.elements;
            selectedElement = null;
            updatePreview();
            showNotification('Layout loaded', 'success');
        } else {
            showNotification('No saved layout', 'warning');
        }
    } catch (err) {
        showNotification('Error: ' + err, 'error');
    }
}

