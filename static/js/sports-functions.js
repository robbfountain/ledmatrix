/**
 * Sports Configuration
 * Handles sports league configuration and settings
 */

async function refreshSportsConfig() {
    try {
        // Refresh the current config to ensure we have the latest data
        await refreshCurrentConfig();
        const res = await fetch('/api/system/status');
        const stats = await res.json();
        // Build a minimal sports UI off current config
        const cfg = currentConfig;
        const leaguePrefixes = {
            'nfl_scoreboard': 'nfl',
            'mlb_scoreboard': 'mlb',
            'milb_scoreboard': 'milb',
            'nhl_scoreboard': 'nhl',
            'nba_scoreboard': 'nba',
            'ncaa_fb_scoreboard': 'ncaa_fb',
            'ncaa_baseball_scoreboard': 'ncaa_baseball',
            'ncaam_basketball_scoreboard': 'ncaam_basketball',
            'ncaam_hockey_scoreboard': 'ncaam_hockey',
            'soccer_scoreboard': 'soccer'
        };
        const leagues = [
            { key: 'nfl_scoreboard', label: 'NFL' },
            { key: 'mlb_scoreboard', label: 'MLB' },
            { key: 'milb_scoreboard', label: 'MiLB' },
            { key: 'nhl_scoreboard', label: 'NHL' },
            { key: 'nba_scoreboard', label: 'NBA' },
            { key: 'ncaa_fb_scoreboard', label: 'NCAA FB' },
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
            const recentToShow = sec.recent_games_to_show ?? 1;
            const upcomingToShow = sec.upcoming_games_to_show ?? 1;
            const liveUpd = sec.live_update_interval ?? 30;
            const recentUpd = sec.recent_update_interval ?? 3600;
            const upcomingUpd = sec.upcoming_update_interval ?? 3600;
            const displayModes = sec.display_modes || {};
            const liveModeEnabled = displayModes[`${p}_live`] ?? true;
            const recentModeEnabled = displayModes[`${p}_recent`] ?? true;
            const upcomingModeEnabled = displayModes[`${p}_upcoming`] ?? true;
            return `
                <div class="bg-white border border-gray-200 rounded-lg p-4 mb-4 shadow-sm">
                    <div class="flex justify-between items-center mb-4">
                        <label class="flex items-center gap-2">
                            <input type="checkbox" data-league="${l.key}" class="sp-enabled rounded border-gray-300 text-blue-600 focus:ring-blue-500" ${sec.enabled ? 'checked' : ''}>
                            <span class="font-semibold text-gray-800">${l.label}</span>
                        </label>
                        <div class="flex gap-2">
                            <button type="button" class="bg-blue-500 hover:bg-blue-600 text-white px-3 py-1.5 rounded text-sm transition" onclick="startOnDemand('${p}_live')"><i class="fas fa-bolt mr-1"></i>Live</button>
                            <button type="button" class="bg-blue-500 hover:bg-blue-600 text-white px-3 py-1.5 rounded text-sm transition" onclick="startOnDemand('${p}_recent')"><i class="fas fa-bolt mr-1"></i>Recent</button>
                            <button type="button" class="bg-blue-500 hover:bg-blue-600 text-white px-3 py-1.5 rounded text-sm transition" onclick="startOnDemand('${p}_upcoming')"><i class="fas fa-bolt mr-1"></i>Upcoming</button>
                            <button type="button" class="bg-gray-500 hover:bg-gray-600 text-white px-3 py-1.5 rounded text-sm transition" onclick="stopOnDemand()"><i class="fas fa-ban mr-1"></i>Stop</button>
                        </div>
                    </div>
                    <div class="mt-4">
                        <h4 class="text-md font-semibold text-gray-700 mb-3">
                            <i class="fas fa-toggle-on mr-2"></i>Display Modes
                        </h4>
                        <div class="space-y-2">
                            <label class="flex items-center gap-3 p-2 bg-gray-50 rounded border">
                                <input type="checkbox" data-league="${l.key}" class="sp-display-mode rounded border-gray-300 text-green-600 focus:ring-green-500" data-mode="live" ${liveModeEnabled ? 'checked' : ''}>
                                <i class="fas fa-circle text-green-500"></i>
                                <span class="text-sm font-medium text-gray-700">Live Mode</span>
                            </label>
                            <label class="flex items-center gap-3 p-2 bg-gray-50 rounded border">
                                <input type="checkbox" data-league="${l.key}" class="sp-display-mode rounded border-gray-300 text-blue-600 focus:ring-blue-500" data-mode="recent" ${recentModeEnabled ? 'checked' : ''}>
                                <i class="fas fa-history text-blue-500"></i>
                                <span class="text-sm font-medium text-gray-700">Recent Mode</span>
                            </label>
                            <label class="flex items-center gap-3 p-2 bg-gray-50 rounded border">
                                <input type="checkbox" data-league="${l.key}" class="sp-display-mode rounded border-gray-300 text-purple-600 focus:ring-purple-500" data-mode="upcoming" ${upcomingModeEnabled ? 'checked' : ''}>
                                <i class="fas fa-clock text-purple-500"></i>
                                <span class="text-sm font-medium text-gray-700">Upcoming Mode</span>
                            </label>
                        </div>
                    </div>
                    <div class="mt-4 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-1">Live Priority</label>
                            <input type="checkbox" data-league="${l.key}" class="sp-live-priority rounded border-gray-300 text-blue-600 focus:ring-blue-500" ${sec.live_priority ? 'checked' : ''}>
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-1">Show Odds</label>
                            <input type="checkbox" data-league="${l.key}" class="sp-show-odds rounded border-gray-300 text-blue-600 focus:ring-blue-500" ${sec.show_odds ? 'checked' : ''}>
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-1">Favorites Only</label>
                            <input type="checkbox" data-league="${l.key}" class="sp-favorites-only rounded border-gray-300 text-blue-600 focus:ring-blue-500" ${sec.show_favorite_teams_only ? 'checked' : ''}>
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-1">Test Mode</label>
                            <input type="checkbox" data-league="${l.key}" class="sp-test-mode rounded border-gray-300 text-orange-600 focus:ring-orange-500" ${sec.test_mode ? 'checked' : ''}>
                            <p class="text-xs text-gray-500 mt-1">Enable test mode for demo purposes</p>
                        </div>
                        <div class="md:col-span-2">
                            <label class="block text-sm font-medium text-gray-700 mb-1">Favorite Teams</label>
                            <input type="text" data-league="${l.key}" class="sp-favorites w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500" value="${fav}" placeholder="PHI, PSU">
                            <p class="text-xs text-gray-500 mt-1">Comma-separated abbreviations</p>
                        </div>
                    </div>
                    <div class="mt-4 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-1">Live Update Interval (sec)</label>
                            <input type="number" min="10" class="sp-live-update w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500" data-league="${l.key}" value="${liveUpd}">
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-1">Recent Update Interval (sec)</label>
                            <input type="number" min="60" class="sp-recent-update w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500" data-league="${l.key}" value="${recentUpd}">
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-1">Upcoming Update Interval (sec)</label>
                            <input type="number" min="60" class="sp-upcoming-update w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500" data-league="${l.key}" value="${upcomingUpd}">
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-1">Recent Games to Show</label>
                            <input type="number" min="0" class="sp-recent-count w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500" data-league="${l.key}" value="${recentToShow}">
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-1">Upcoming Games to Show</label>
                            <input type="number" min="0" class="sp-upcoming-count w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500" data-league="${l.key}" value="${upcomingToShow}">
                        </div>
                    </div>
                </div>
            `;
        }).join('');
        container.innerHTML = html || 'No sports configuration found.';
        
        // Add event listeners for display mode toggles
        const displayModeCheckboxes = container.querySelectorAll('.sp-display-mode');
        displayModeCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', function() {
                const league = this.getAttribute('data-league');
                const mode = this.getAttribute('data-mode');
                const isEnabled = this.checked;
                
                // Visual feedback using Tailwind classes
                const label = this.closest('label');
                
                if (isEnabled) {
                    label.classList.add('bg-green-50', 'border-green-200');
                    label.classList.remove('bg-gray-50', 'border-gray-200');
                } else {
                    label.classList.add('bg-red-50', 'border-red-200');
                    label.classList.remove('bg-gray-50', 'border-gray-200');
                }
                
                // Reset after a short delay
                setTimeout(() => {
                    label.classList.remove('bg-green-50', 'border-green-200', 'bg-red-50', 'border-red-200');
                    label.classList.add('bg-gray-50', 'border-gray-200');
                }, 1000);
                
                showNotification(`${league.toUpperCase()} ${mode} mode ${isEnabled ? 'enabled' : 'disabled'}`, 'success');
            });
        });
    } catch (err) {
        document.getElementById('sports-config').textContent = 'Failed to load sports configuration';
    }
}

async function saveSportsConfig() {
    try {
        const leagues = document.querySelectorAll('.sp-enabled');
        const fragment = {};
        leagues.forEach(chk => {
            const key = chk.getAttribute('data-league');
            const enabled = chk.checked;
            const livePriority = document.querySelector(`.sp-live-priority[data-league="${key}"]`)?.checked || false;
            const showOdds = document.querySelector(`.sp-show-odds[data-league="${key}"]`)?.checked || false;
            const favoritesOnly = document.querySelector(`.sp-favorites-only[data-league="${key}"]`)?.checked || false;
            const testMode = document.querySelector(`.sp-test-mode[data-league="${key}"]`)?.checked || false;
            const favs = document.querySelector(`.sp-favorites[data-league="${key}"]`)?.value || '';
            const favorite_teams = favs.split(',').map(s => s.trim()).filter(Boolean);
            const liveUpd = parseInt(document.querySelector(`.sp-live-update[data-league="${key}"]`)?.value || '30');
            const recentUpd = parseInt(document.querySelector(`.sp-recent-update[data-league="${key}"]`)?.value || '3600');
            const upcomingUpd = parseInt(document.querySelector(`.sp-upcoming-update[data-league="${key}"]`)?.value || '3600');
            const recentCount = parseInt(document.querySelector(`.sp-recent-count[data-league="${key}"]`)?.value || '1');
            const upcomingCount = parseInt(document.querySelector(`.sp-upcoming-count[data-league="${key}"]`)?.value || '1');
            
            // Get display modes
            const leaguePrefixes = {
                'nfl_scoreboard': 'nfl',
                'mlb_scoreboard': 'mlb',
                'milb_scoreboard': 'milb',
                'nhl_scoreboard': 'nhl',
                'nba_scoreboard': 'nba',
                'ncaa_fb_scoreboard': 'ncaa_fb',
                'ncaa_baseball_scoreboard': 'ncaa_baseball',
                'ncaam_basketball_scoreboard': 'ncaam_basketball',
                'ncaam_hockey_scoreboard': 'ncaam_hockey',
                'soccer_scoreboard': 'soccer'
            };
            const p = leaguePrefixes[key] || key;
            const liveModeEnabled = document.querySelector(`.sp-display-mode[data-league="${key}"][data-mode="live"]`)?.checked || false;
            const recentModeEnabled = document.querySelector(`.sp-display-mode[data-league="${key}"][data-mode="recent"]`)?.checked || false;
            const upcomingModeEnabled = document.querySelector(`.sp-display-mode[data-league="${key}"][data-mode="upcoming"]`)?.checked || false;
            
            fragment[key] = {
                enabled,
                live_priority: livePriority,
                show_odds: showOdds,
                show_favorite_teams_only: favoritesOnly,
                test_mode: testMode,
                favorite_teams,
                live_update_interval: liveUpd,
                recent_update_interval: recentUpd,
                upcoming_update_interval: upcomingUpd,
                recent_games_to_show: recentCount,
                upcoming_games_to_show: upcomingCount,
                display_modes: {
                    [`${p}_live`]: liveModeEnabled,
                    [`${p}_recent`]: recentModeEnabled,
                    [`${p}_upcoming`]: upcomingModeEnabled
                }
            };
        });
        await saveConfigJson(fragment);
    } catch (err) {
        showNotification('Error saving sports configuration: ' + err, 'error');
        return;
    }
    showNotification('Sports configuration saved', 'success');
}
