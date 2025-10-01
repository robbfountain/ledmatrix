/**
 * News Manager
 * Handles news feed configuration and management
 */

async function loadNewsManagerData() {
    try {
        const response = await fetch('/news_manager/status');
        const data = await response.json();
        
        if (data.status === 'success') {
            newsManagerData = data.data;
            updateNewsManagerUI();
        } else {
            console.error('Error loading news manager data:', data.message);
        }
    } catch (error) {
        console.error('Error loading news manager data:', error);
    }
}

function updateNewsManagerUI() {
    document.getElementById('news_enabled').checked = newsManagerData.enabled || false;
    document.getElementById('headlines_per_feed').value = newsManagerData.headlines_per_feed || 2;
    document.getElementById('rotation_enabled').checked = newsManagerData.rotation_enabled !== false;
    
    // Populate available feeds
    const feedsGrid = document.getElementById('news_feeds_grid');
    feedsGrid.innerHTML = '';
    
    if (newsManagerData.available_feeds) {
        newsManagerData.available_feeds.forEach(feed => {
            const isEnabled = newsManagerData.enabled_feeds.includes(feed);
            const feedDiv = document.createElement('div');
            feedDiv.className = 'checkbox-item';
            feedDiv.innerHTML = `
                <label>
                    <input type="checkbox" name="news_feed" value="${feed}" ${isEnabled ? 'checked' : ''}>
                    ${feed}
                </label>
            `;
            feedsGrid.appendChild(feedDiv);
        });
    }
    
    updateCustomFeedsList();
    updateNewsStatus();
}

function updateCustomFeedsList() {
    const customFeedsList = document.getElementById('custom_feeds_list');
    customFeedsList.innerHTML = '';
    
    if (newsManagerData.custom_feeds) {
        Object.entries(newsManagerData.custom_feeds).forEach(([name, url]) => {
            const feedDiv = document.createElement('div');
            feedDiv.style.cssText = 'margin: 10px 0; padding: 10px; border: 1px solid #ccc; border-radius: 4px; background: white;';
            feedDiv.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div><strong>${name}</strong>: ${url}</div>
                    <button type="button" onclick="removeCustomFeed('${name}')" 
                            style="background: #ff4444; color: white; border: none; padding: 4px 8px; border-radius: 3px; cursor: pointer;">Remove</button>
                </div>
            `;
            customFeedsList.appendChild(feedDiv);
        });
    }
}

function updateNewsStatus() {
    const statusDiv = document.getElementById('news_status');
    const enabledFeeds = newsManagerData.enabled_feeds || [];
    
    statusDiv.innerHTML = `
        <h4>Current Status</h4>
        <p><strong>Enabled:</strong> ${newsManagerData.enabled ? 'Yes' : 'No'}</p>
        <p><strong>Active Feeds:</strong> ${enabledFeeds.join(', ') || 'None'}</p>
        <p><strong>Headlines per Feed:</strong> ${newsManagerData.headlines_per_feed || 2}</p>
        <p><strong>Total Custom Feeds:</strong> ${Object.keys(newsManagerData.custom_feeds || {}).length}</p>
        <p><strong>Rotation Enabled:</strong> ${newsManagerData.rotation_enabled !== false ? 'Yes' : 'No'}</p>
    `;
}

async function saveNewsSettings() {
    const enabledFeeds = Array.from(document.querySelectorAll('input[name="news_feed"]:checked'))
        .map(input => input.value);
    
    const headlinesPerFeed = parseInt(document.getElementById('headlines_per_feed').value);
    const enabled = document.getElementById('news_enabled').checked;
    
    try {
        await fetch('/news_manager/toggle', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ enabled: enabled })
        });
        
        const response = await fetch('/news_manager/update_feeds', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                enabled_feeds: enabledFeeds,
                headlines_per_feed: headlinesPerFeed
            })
        });
        
        const data = await response.json();
        showNotification(data.message, data.status);
        
        if (data.status === 'success') {
            loadNewsManagerData();
        }
    } catch (error) {
        showNotification('Error saving news settings: ' + error, 'error');
    }
}

async function addCustomFeed() {
    const name = document.getElementById('custom_feed_name').value.trim();
    const url = document.getElementById('custom_feed_url').value.trim();
    
    if (!name || !url) {
        showNotification('Please enter both feed name and URL', 'error');
        return;
    }
    
    try {
        const response = await fetch('/news_manager/add_custom_feed', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: name, url: url })
        });
        
        const data = await response.json();
        showNotification(data.message, data.status);
        
        if (data.status === 'success') {
            document.getElementById('custom_feed_name').value = '';
            document.getElementById('custom_feed_url').value = '';
            loadNewsManagerData();
        }
    } catch (error) {
        showNotification('Error adding custom feed: ' + error, 'error');
    }
}

async function removeCustomFeed(name) {
    if (!confirm(`Are you sure you want to remove the feed "${name}"?`)) {
        return;
    }
    
    try {
        const response = await fetch('/news_manager/remove_custom_feed', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: name })
        });
        
        const data = await response.json();
        showNotification(data.message, data.status);
        
        if (data.status === 'success') {
            loadNewsManagerData();
        }
    } catch (error) {
        showNotification('Error removing custom feed: ' + error, 'error');
    }
}

function refreshNewsStatus() {
    loadNewsManagerData();
    showNotification('News status refreshed', 'success');
}

async function saveNewsAdvancedSettings() {
    const payload = {
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
            text_color: hexToRgbArray(document.getElementById('news_text_color').value),
            separator_color: hexToRgbArray(document.getElementById('news_separator_color').value)
        }
    };
    await saveConfigJson(payload);
}

