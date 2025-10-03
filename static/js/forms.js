/**
 * Form Handlers
 * Handles form submissions for all configuration forms
 */

function initializeForms() {
    // Schedule form
    document.getElementById('schedule-form')?.addEventListener('submit', async function(e) {
        e.preventDefault();
        const formData = new FormData(this);
        
        try {
            const response = await fetch('/save_schedule', {
                method: 'POST',
                body: formData
            });
            const result = await response.json();
            showNotification(result.message, result.status);
        } catch (error) {
            showNotification('Error saving schedule: ' + error.message, 'error');
        }
    });

    // Display form
    document.getElementById('display-form')?.addEventListener('submit', async function(e) {
        e.preventDefault();
        const formData = new FormData(this);
        formData.append('config_type', 'main');
        
        try {
            const response = await fetch('/save_config', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const result = await response.json();
            showNotification(result.message, result.status);
        } catch (error) {
            showNotification('Error saving display settings: ' + error.message, 'error');
        }
    });

    // General form
    document.getElementById('general-form')?.addEventListener('submit', async function(e) { 
        e.preventDefault();
        const payload = {
            web_display_autostart: document.getElementById('web_display_autostart').checked,
            timezone: document.getElementById('timezone').value,
            location: {
                city: document.getElementById('city').value,
                state: document.getElementById('state').value,
                country: document.getElementById('country').value
            }
        };
        await saveConfigJson(payload);
    });

    // Clock form
    document.getElementById('clock-form')?.addEventListener('submit', async function(e) {
        e.preventDefault();
        const payload = {
            clock: {
                enabled: document.getElementById('clock_enabled').checked,
                format: document.getElementById('clock_format').value,
                update_interval: parseInt(document.getElementById('clock_update_interval').value)
            }
        };
        await saveConfigJson(payload);
    });

    // Durations form
    document.getElementById('durations-form')?.addEventListener('submit', async function(e) {
        e.preventDefault();
        const inputs = document.querySelectorAll('.duration-input');
        const durations = {};
        inputs.forEach(inp => {
            durations[inp.dataset.name] = parseInt(inp.value);
        });
        const payload = { display: { display_durations: durations } };
        await saveConfigJson(payload);
    });

    // Weather form
    document.getElementById('weather-form')?.addEventListener('submit', async function(e) {
        e.preventDefault();
        const payload = {
            weather: {
                enabled: document.getElementById('weather_enabled').checked,
                update_interval: parseInt(document.getElementById('weather_update_interval').value),
                units: document.getElementById('weather_units').value,
                display_format: document.getElementById('weather_display_format').value
            },
            location: {
                city: document.getElementById('weather_city').value,
                state: document.getElementById('weather_state').value
            }
        };
        await saveConfigJson(payload);
    });

    // Stocks form
    document.getElementById('stocks-form')?.addEventListener('submit', async function(e) {
        e.preventDefault();
        const symbols = document.getElementById('stocks_symbols').value.split(',').map(s => s.trim()).filter(Boolean);
        const payload = {
            stocks: {
                enabled: document.getElementById('stocks_enabled').checked,
                update_interval: parseInt(document.getElementById('stocks_update_interval').value),
                scroll_speed: parseFloat(document.getElementById('stocks_scroll_speed').value),
                scroll_delay: parseFloat(document.getElementById('stocks_scroll_delay').value),
                toggle_chart: document.getElementById('stocks_toggle_chart').checked,
                dynamic_duration: document.getElementById('stocks_dynamic_duration').checked,
                min_duration: parseInt(document.getElementById('stocks_min_duration').value),
                max_duration: parseInt(document.getElementById('stocks_max_duration').value),
                duration_buffer: parseFloat(document.getElementById('stocks_duration_buffer').value),
                symbols: symbols,
                display_format: document.getElementById('stocks_display_format').value
            }
        };
        await saveConfigJson(payload);
    });

    // Crypto form
    document.getElementById('crypto-form')?.addEventListener('submit', async function(e) {
        e.preventDefault();
        const symbols = document.getElementById('crypto_symbols').value.split(',').map(s => s.trim()).filter(Boolean);
        const payload = {
            crypto: {
                enabled: document.getElementById('crypto_enabled').checked,
                update_interval: parseInt(document.getElementById('crypto_update_interval').value),
                symbols: symbols
            }
        };
        await saveConfigJson(payload);
    });

    // Stock news form
    document.getElementById('stocknews-form')?.addEventListener('submit', async function(e) {
        e.preventDefault();
        const payload = {
            stock_news: {
                enabled: document.getElementById('stocknews_enabled').checked,
                update_interval: parseInt(document.getElementById('stocknews_update_interval').value),
                scroll_speed: parseFloat(document.getElementById('stocknews_scroll_speed').value),
                scroll_delay: parseFloat(document.getElementById('stocknews_scroll_delay').value),
                max_headlines_per_symbol: parseInt(document.getElementById('stocknews_max_headlines_per_symbol').value),
                headlines_per_rotation: parseInt(document.getElementById('stocknews_headlines_per_rotation').value),
                dynamic_duration: document.getElementById('stocknews_dynamic_duration').checked,
                min_duration: parseInt(document.getElementById('stocknews_min_duration').value),
                max_duration: parseInt(document.getElementById('stocknews_max_duration').value),
                duration_buffer: parseFloat(document.getElementById('stocknews_duration_buffer').value)
            }
        };
        await saveConfigJson(payload);
    });

    // Odds form
    document.getElementById('odds-form')?.addEventListener('submit', async function(e) {
        e.preventDefault();
        const leagues = document.getElementById('odds_enabled_leagues').value.split(',').map(s => s.trim()).filter(Boolean);
        const payload = {
            odds_ticker: {
                enabled: document.getElementById('odds_enabled').checked,
                update_interval: parseInt(document.getElementById('odds_update_interval').value),
                scroll_speed: parseFloat(document.getElementById('odds_scroll_speed').value),
                scroll_delay: parseFloat(document.getElementById('odds_scroll_delay').value),
                games_per_favorite_team: parseInt(document.getElementById('odds_games_per_favorite_team').value),
                max_games_per_league: parseInt(document.getElementById('odds_max_games_per_league').value),
                future_fetch_days: parseInt(document.getElementById('odds_future_fetch_days').value),
                enabled_leagues: leagues,
                sort_order: document.getElementById('odds_sort_order').value,
                show_favorite_teams_only: document.getElementById('odds_show_favorite_teams_only').checked,
                show_odds_only: document.getElementById('odds_show_odds_only').checked,
                loop: document.getElementById('odds_loop').checked,
                show_channel_logos: document.getElementById('odds_show_channel_logos').checked,
                dynamic_duration: document.getElementById('odds_dynamic_duration').checked,
                min_duration: parseInt(document.getElementById('odds_min_duration').value),
                max_duration: parseInt(document.getElementById('odds_max_duration').value),
                duration_buffer: parseFloat(document.getElementById('odds_duration_buffer').value)
            }
        };
        await saveConfigJson(payload);
    });

    // Leaderboard form
    document.getElementById('leaderboard-form')?.addEventListener('submit', async function(e) {
        e.preventDefault();
        const payload = {
            leaderboard: {
                enabled: document.getElementById('leaderboard_enabled').checked,
                update_interval: parseInt(document.getElementById('leaderboard_update_interval').value),
                scroll_speed: parseFloat(document.getElementById('leaderboard_scroll_speed').value),
                scroll_delay: parseFloat(document.getElementById('leaderboard_scroll_delay').value),
                display_duration: parseInt(document.getElementById('leaderboard_display_duration').value),
                loop: document.getElementById('leaderboard_loop').checked,
                request_timeout: parseInt(document.getElementById('leaderboard_request_timeout').value),
                dynamic_duration: document.getElementById('leaderboard_dynamic_duration').checked,
                min_duration: parseInt(document.getElementById('leaderboard_min_duration').value),
                max_duration: parseInt(document.getElementById('leaderboard_max_duration').value),
                duration_buffer: parseFloat(document.getElementById('leaderboard_duration_buffer').value),
                enabled_sports: {
                    nfl: {
                        enabled: document.getElementById('leaderboard_nfl_enabled').checked,
                        top_teams: parseInt(document.getElementById('leaderboard_nfl_top_teams').value)
                    },
                    nba: {
                        enabled: document.getElementById('leaderboard_nba_enabled').checked,
                        top_teams: parseInt(document.getElementById('leaderboard_nba_top_teams').value)
                    },
                    mlb: {
                        enabled: document.getElementById('leaderboard_mlb_enabled').checked,
                        top_teams: parseInt(document.getElementById('leaderboard_mlb_top_teams').value)
                    },
                    ncaa_fb: {
                        enabled: document.getElementById('leaderboard_ncaa_fb_enabled').checked,
                        top_teams: parseInt(document.getElementById('leaderboard_ncaa_fb_top_teams').value),
                        show_ranking: document.getElementById('leaderboard_ncaa_fb_show_ranking').checked
                    },
                    nhl: {
                        enabled: document.getElementById('leaderboard_nhl_enabled').checked,
                        top_teams: parseInt(document.getElementById('leaderboard_nhl_top_teams').value)
                    },
                    ncaam_basketball: {
                        enabled: document.getElementById('leaderboard_ncaam_basketball_enabled').checked,
                        top_teams: parseInt(document.getElementById('leaderboard_ncaam_basketball_top_teams').value)
                    }
                }
            }
        };
        await saveConfigJson(payload);
    });

    // Of The Day form
    document.getElementById('of_the_day-form')?.addEventListener('submit', async function(e) {
        e.preventDefault();
        const categoryOrder = document.getElementById('of_the_day_category_order').value.split(',').map(s => s.trim()).filter(Boolean);
        const payload = {
            of_the_day: {
                enabled: document.getElementById('of_the_day_enabled').checked,
                update_interval: parseInt(document.getElementById('of_the_day_update_interval').value),
                display_rotate_interval: parseInt(document.getElementById('of_the_day_display_rotate_interval').value),
                subtitle_rotate_interval: parseInt(document.getElementById('of_the_day_subtitle_rotate_interval').value),
                category_order: categoryOrder,
                categories: {
                    word_of_the_day: {
                        enabled: document.getElementById('of_the_day_word_enabled').checked,
                        data_file: document.getElementById('of_the_day_word_data_file').value,
                        display_name: document.getElementById('of_the_day_word_display_name').value
                    },
                    slovenian_word_of_the_day: {
                        enabled: document.getElementById('of_the_day_slovenian_enabled').checked,
                        data_file: document.getElementById('of_the_day_slovenian_data_file').value,
                        display_name: document.getElementById('of_the_day_slovenian_display_name').value
                    }
                }
            }
        };
        await saveConfigJson(payload);
    });

    // Text form
    document.getElementById('text-form')?.addEventListener('submit', async function(e) {
        e.preventDefault();
        const payload = {
            text_display: {
                enabled: document.getElementById('text_enabled').checked,
                text: document.getElementById('text_text').value,
                font_path: document.getElementById('text_font_path').value,
                font_size: parseInt(document.getElementById('text_font_size').value),
                scroll: document.getElementById('text_scroll').checked,
                scroll_speed: parseInt(document.getElementById('text_scroll_speed').value),
                scroll_gap_width: parseInt(document.getElementById('text_scroll_gap_width').value),
                text_color: hexToRgbArray(document.getElementById('text_text_color').value),
                background_color: hexToRgbArray(document.getElementById('text_background_color').value)
            }
        };
        await saveConfigJson(payload);
    });

    // YouTube form
    document.getElementById('youtube-form')?.addEventListener('submit', async function(e) {
        e.preventDefault();
        const payload = {
            youtube: {
                enabled: document.getElementById('youtube_enabled').checked,
                update_interval: parseInt(document.getElementById('youtube_update_interval').value)
            }
        };
        await saveConfigJson(payload);
    });

    // Music form
    document.getElementById('music-form')?.addEventListener('submit', async function(e) {
        e.preventDefault();
        const payload = {
            music: {
                enabled: document.getElementById('music_enabled').checked,
                preferred_source: document.getElementById('music_preferred_source').value,
                YTM_COMPANION_URL: document.getElementById('ytm_companion_url').value,
                POLLING_INTERVAL_SECONDS: parseInt(document.getElementById('music_polling_interval').value)
            }
        };
        await saveConfigJson(payload);
    });

    // Calendar form
    document.getElementById('calendar-form')?.addEventListener('submit', async function(e) {
        e.preventDefault();
        const calendars = document.getElementById('calendar_calendars').value.split(',').map(s => s.trim()).filter(Boolean);
        const payload = {
            calendar: {
                enabled: document.getElementById('calendar_enabled').checked,
                max_events: parseInt(document.getElementById('calendar_max_events').value),
                update_interval: parseInt(document.getElementById('calendar_update_interval').value),
                calendars: calendars
            }
        };
        await saveConfigJson(payload);
    });

    // Initialize color inputs for text form
    const textColorInput = document.getElementById('text_text_color');
    const textBgColorInput = document.getElementById('text_background_color');
    if (textColorInput && textColorInput.dataset.rgb) {
        try {
            const rgb = JSON.parse(textColorInput.dataset.rgb);
            textColorInput.value = rgbToHex(rgb);
        } catch {}
    }
    if (textBgColorInput && textBgColorInput.dataset.rgb) {
        try {
            const rgb = JSON.parse(textBgColorInput.dataset.rgb);
            textBgColorInput.value = rgbToHex(rgb);
        } catch {}
    }

    // Initialize color inputs for news form
    const newsTextColor = document.getElementById('news_text_color');
    const newsSepColor = document.getElementById('news_separator_color');
    if (newsTextColor && newsTextColor.dataset.rgb) {
        try {
            const rgb = JSON.parse(newsTextColor.dataset.rgb);
            newsTextColor.value = rgbToHex(rgb);
        } catch {}
    }
    if (newsSepColor && newsSepColor.dataset.rgb) {
        try {
            const rgb = JSON.parse(newsSepColor.dataset.rgb);
            newsSepColor.value = rgbToHex(rgb);
        } catch {}
    }
}

