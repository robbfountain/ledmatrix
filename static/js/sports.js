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
                <div style="border:1px solid #ddd; border-radius:6px; padding:12px; margin:10px 0;">
                    <div style="display:flex; justify-content: space-between; align-items:center; margin-bottom:8px;">
                        <label style="display:flex; align-items:center; gap:8px; margin:0;">
                            <input type="checkbox" data-league="${l.key}" class="sp-enabled" ${sec.enabled ? 'checked' : ''}>
                            <strong>${l.label}</strong>
                        </label>
                        <div style="display:flex; gap:6px;">
                            <button type="button" class="btn btn-info" onclick="startOnDemand('${p}_live')"><i class="fas fa-bolt"></i> Live</button>
                            <button type="button" class="btn btn-info" onclick="startOnDemand('${p}_recent')"><i class="fas fa-bolt"></i> Recent</button>
                            <button type="button" class="btn btn-info" onclick="startOnDemand('${p}_upcoming')"><i class="fas fa-bolt"></i> Upcoming</button>
                            <button type="button" class="btn btn-secondary" onclick="stopOnDemand()"><i class="fas fa-ban"></i> Stop</button>
                        </div>
                    </div>
                    <div style="margin-top:15px;">
                        <h4 style="margin: 0 0 10px 0; color: var(--primary-color); font-size: 16px;">
                            <i class="fas fa-toggle-on"></i> Display Modes
                        </h4>
                        <div class="display-mode-toggle">
                            <label>
                                <input type="checkbox" data-league="${l.key}" class="sp-display-mode" data-mode="live" ${liveModeEnabled ? 'checked' : ''}>
                                <i class="fas fa-circle mode-icon mode-live"></i>
                                <span class="mode-label mode-live">Live Mode</span>
                            </label>
                        </div>
                        <div class="display-mode-toggle">
                            <label>
                                <input type="checkbox" data-league="${l.key}" class="sp-display-mode" data-mode="recent" ${recentModeEnabled ? 'checked' : ''}>
                                <i class="fas fa-history mode-icon mode-recent"></i>
                                <span class="mode-label mode-recent">Recent Mode</span>
                            </label>
                        </div>
                        <div class="display-mode-toggle">
                            <label>
                                <input type="checkbox" data-league="${l.key}" class="sp-display-mode" data-mode="upcoming" ${upcomingModeEnabled ? 'checked' : ''}>
                                <i class="fas fa-clock mode-icon mode-upcoming"></i>
                                <span class="mode-label mode-upcoming">Upcoming Mode</span>
                            </label>
                        </div>
                    </div>
                    <div class="form-row" style="margin-top:10px;">
                        <div class="form-group">
                            <label>Live Priority</label>
                            <input type="checkbox" data-league="${l.key}" class="sp-live-priority" ${sec.live_priority ? 'checked' : ''}>
                        </div>
                        <div class="form-group">
                            <label>Show Odds</label>
                            <input type="checkbox" data-league="${l.key}" class="sp-show-odds" ${sec.show_odds ? 'checked' : ''}>
                        </div>
                        <div class="form-group">
                            <label>Favorites Only</label>
                            <input type="checkbox" data-league="${l.key}" class="sp-favorites-only" ${sec.show_favorite_teams_only ? 'checked' : ''}>
                        </div>
                        <div class="form-group">
                            <label>Favorite Teams</label>
                            <input type="text" data-league="${l.key}" class="form-control sp-favorites" value="${fav}">
                            <div class="description">Comma-separated abbreviations</div>
                        </div>
                    </div>
                    <div class="form-row" style="margin-top:10px;">
                        <div class="form-group">
                            <label>Live Update Interval (sec)</label>
                            <input type="number" min="10" class="form-control sp-live-update" data-league="${l.key}" value="${liveUpd}">
                        </div>
                        <div class="form-group">
                            <label>Recent Update Interval (sec)</label>
                            <input type="number" min="60" class="form-control sp-recent-update" data-league="${l.key}" value="${recentUpd}">
                        </div>
                        <div class="form-group">
                            <label>Upcoming Update Interval (sec)</label>
                            <input type="number" min="60" class="form-control sp-upcoming-update" data-league="${l.key}" value="${upcomingUpd}">
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label>Recent Games to Show</label>
                            <input type="number" min="0" class="form-control sp-recent-count" data-league="${l.key}" value="${recentToShow}">
                        </div>
                        <div class="form-group">
                            <label>Upcoming Games to Show</label>
                            <input type="number" min="0" class="form-control sp-upcoming-count" data-league="${l.key}" value="${upcomingToShow}">
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
                
                // Visual feedback
                const label = this.closest('label');
                const toggle = this.closest('.display-mode-toggle');
                
                if (isEnabled) {
                    toggle.style.backgroundColor = 'rgba(46, 204, 113, 0.1)';
                    toggle.style.borderColor = '#2ecc71';
                } else {
                    toggle.style.backgroundColor = 'rgba(231, 76, 60, 0.1)';
                    toggle.style.borderColor = '#e74c3c';
                }
                
                // Reset after a short delay
                setTimeout(() => {
                    toggle.style.backgroundColor = '';
                    toggle.style.borderColor = '';
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

