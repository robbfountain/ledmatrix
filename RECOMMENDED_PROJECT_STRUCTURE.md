# LEDMatrix - Recommended Project Structure

This document outlines the recommended file and folder organization for the LEDMatrix project to improve maintainability, clarity, and scalability.

## Current vs Recommended Structure

### Executive Summary
The current structure mixes application code, configuration, assets, documentation, installation scripts, and external dependencies at the root level. The recommended structure groups related files into logical directories for better organization.

---

## Recommended Directory Tree

```
LEDMatrix/
│
├── README.md                           # Main project documentation
├── LICENSE                             # Project license
├── .gitignore                          # Git ignore patterns
├── .cursorignore                       # Cursor ignore patterns
│
├── docs/                               # 📚 All documentation files
│   ├── BACKGROUND_SERVICE_README.md
│   ├── AP_TOP_25_IMPLEMENTATION_SUMMARY.md
│   ├── TAILWIND_SETUP.md
│   ├── OF_THE_DAY_GUIDE.md
│   ├── branching_and_pr_guidelines.md  # GitHub workflow docs
│   ├── hardware/                       # Hardware-specific docs
│   │   ├── hardware_setup.md
│   │   └── display_settings.md
│   ├── configuration/                  # Configuration guides
│   │   ├── calendar_setup.md
│   │   ├── music_setup.md
│   │   ├── odds_ticker_setup.md
│   │   └── stocks_setup.md
│   └── api/                            # API documentation
│       └── web_interface_api.md
│
├── config/                             # ⚙️ Configuration files
│   ├── config.json                     # Main config (gitignored)
│   ├── config.template.json            # Template for new installs
│   ├── config_secrets.json             # API keys (gitignored)
│   ├── config_secrets.template.json    # Template for secrets
│   ├── spotify_auth.json               # Spotify auth cache (gitignored)
│   ├── ytm_auth.json                   # YTM auth cache (gitignored)
│   └── token.pickle                    # Google Calendar token (gitignored)
│
├── src/                                # 💻 Source code
│   ├── __init__.py
│   │
│   ├── core/                           # Core system components
│   │   ├── __init__.py
│   │   ├── config_manager.py
│   │   ├── cache_manager.py
│   │   ├── display_controller.py
│   │   ├── display_manager.py
│   │   └── layout_manager.py
│   │
│   ├── base_classes/                   # Base classes & architecture
│   │   ├── __init__.py
│   │   ├── sports.py
│   │   ├── baseball.py
│   │   ├── football.py
│   │   ├── hockey.py
│   │   ├── api_extractors.py
│   │   └── data_sources.py
│   │
│   ├── managers/                       # Feature managers
│   │   ├── __init__.py
│   │   │
│   │   ├── sports/                     # Sports-specific managers
│   │   │   ├── __init__.py
│   │   │   ├── mlb_manager.py
│   │   │   ├── milb_manager.py
│   │   │   ├── nba_managers.py
│   │   │   ├── nfl_managers.py
│   │   │   ├── nhl_managers.py
│   │   │   ├── ncaa_fb_managers.py
│   │   │   ├── ncaa_baseball_managers.py
│   │   │   ├── ncaam_basketball_managers.py
│   │   │   ├── ncaam_hockey_managers.py
│   │   │   ├── soccer_managers.py
│   │   │   ├── leaderboard_manager.py
│   │   │   └── odds_ticker_manager.py
│   │   │
│   │   ├── weather/                    # Weather-specific
│   │   │   ├── __init__.py
│   │   │   ├── weather_manager.py
│   │   │   └── weather_icons.py
│   │   │
│   │   ├── stocks/                     # Stock/financial managers
│   │   │   ├── __init__.py
│   │   │   ├── stock_manager.py
│   │   │   └── stock_news_manager.py
│   │   │
│   │   ├── music/                      # Music-specific
│   │   │   ├── __init__.py
│   │   │   ├── music_manager.py
│   │   │   ├── spotify_client.py
│   │   │   └── ytm_client.py
│   │   │
│   │   └── other/                      # Other managers
│   │       ├── __init__.py
│   │       ├── calendar_manager.py
│   │       ├── news_manager.py
│   │       ├── clock.py
│   │       ├── text_display.py
│   │       ├── youtube_display.py
│   │       └── of_the_day_manager.py
│   │
│   ├── utils/                          # Utility modules
│   │   ├── __init__.py
│   │   ├── dynamic_team_resolver.py
│   │   ├── logo_downloader.py
│   │   ├── font_test_manager.py
│   │   ├── background_cache_mixin.py
│   │   ├── generic_cache_mixin.py
│   │   └── odds_manager.py
│   │
│   ├── auth/                           # Authentication scripts
│   │   ├── __init__.py
│   │   ├── authenticate_spotify.py
│   │   ├── authenticate_ytm.py
│   │   └── calendar_registration.py
│   │
│   └── services/                       # Background services
│       ├── __init__.py
│       └── background_data_service.py
│
├── web/                                # 🌐 Web interface
│   ├── web_interface_v2.py             # Main Flask app (v2)
│   ├── web_interface.py                # Legacy Flask app (v1)
│   ├── start_web_v2.py                 # Web startup helper
│   ├── start_web_conditionally.py      # Conditional web starter
│   │
│   ├── templates/                      # HTML templates
│   │   ├── index_v3.html               # Latest version
│   │   ├── index_v2.html               # Version 2
│   │   └── index.html                  # Legacy version
│   │
│   └── static/                         # Static web assets
│       ├── css/
│       │   ├── input.css               # Tailwind input
│       │   └── output.css              # Compiled CSS
│       └── js/
│           ├── app.js
│           ├── actions.js
│           ├── display.js
│           ├── editor.js
│           ├── forms.js
│           ├── news.js
│           ├── socket.js
│           ├── sports.js
│           ├── state.js
│           ├── tabs.js
│           ├── utils.js
│           └── v3-functions.js
│
├── assets/                             # 📦 Static assets & data
│   ├── fonts/                          # Font files
│   │   ├── *.ttf
│   │   ├── *.bdf
│   │   └── bdf_font_guide
│   │
│   ├── sports/                         # Sports assets
│   │   ├── mlb_logos/
│   │   ├── milb_logos/
│   │   ├── nba_logos/
│   │   ├── nfl_logos/
│   │   ├── nhl_logos/
│   │   ├── ncaa_logos/
│   │   ├── soccer_logos/
│   │   ├── broadcast_logos/
│   │   └── all_team_abbreviations.txt
│   │
│   ├── stocks/                         # Stock/financial assets
│   │   ├── ticker_icons/
│   │   ├── crypto_icons/
│   │   ├── forex_icons/
│   │   └── nasdaq.json
│   │
│   ├── weather/                        # Weather assets
│   │   └── (weather icons)
│   │
│   ├── data/                           # Data files
│   │   └── team_league_map.json
│   │
│   └── of_the_day/                     # Daily content data
│       ├── word_of_the_day.json
│       ├── bible_verse_of_the_day.json
│       └── slovenian_word_of_the_day.json
│
├── tests/                              # 🧪 Test files (renamed from 'test')
│   ├── __init__.py
│   ├── unit/                           # Unit tests
│   │   ├── test_config_loading.py
│   │   ├── test_config_simple.py
│   │   └── test_config_validation.py
│   │
│   ├── integration/                    # Integration tests
│   │   ├── test_sports_integration.py
│   │   ├── test_baseball_managers_integration.py
│   │   └── test_web_interface.py
│   │
│   ├── manual/                         # Manual test scripts
│   │   ├── test_stock_toggle_chart.py
│   │   ├── test_odds_ticker.py
│   │   ├── test_leaderboard.py
│   │   └── run_font_test.py
│   │
│   └── utilities/                      # Test utilities & helpers
│       ├── check_espn_api.py
│       ├── check_team_images.py
│       ├── analyze_broadcast_logos.py
│       ├── create_league_logos.py
│       └── download_espn_ncaa_fb_logos.py
│
├── scripts/                            # 🔧 Installation & utility scripts
│   ├── installation/                   # Installation scripts
│   │   ├── first_time_install.sh
│   │   ├── install_service.sh
│   │   ├── install_web_service.sh
│   │   └── install_dependencies_apt.py
│   │
│   ├── setup/                          # Setup scripts
│   │   ├── setup_cache.sh
│   │   ├── configure_web_sudo.sh
│   │   └── migrate_config.sh
│   │
│   ├── maintenance/                    # Maintenance scripts
│   │   ├── fix_cache_permissions.sh
│   │   ├── fix_web_permissions.sh
│   │   ├── fix_assets_permissions.sh
│   │   ├── cleanup_venv.sh
│   │   └── clear_cache.py
│   │
│   └── control/                        # Service control scripts
│       ├── start_display.sh
│       ├── stop_display.sh
│       └── run_web_v2.sh
│
├── deployment/                         # 🚀 Deployment files
│   ├── systemd/                        # Systemd service files
│   │   ├── ledmatrix.service
│   │   └── ledmatrix-web.service
│   │
│   └── docker/                         # Docker files (future)
│       ├── Dockerfile
│       └── docker-compose.yml
│
├── hardware/                           # 🔌 Hardware-specific files
│   ├── rpi-rgb-led-matrix/             # External RGB LED library (submodule)
│   │   └── (library files)
│   │
│   └── 3d-models/                      # 3D printing files
│       ├── 4mm-pixel-pitch/
│       │   └── (STL files)
│       ├── 3mm-pixel-pitch/
│       │   └── (STL files)
│       ├── LICENSE.txt
│       └── README.txt
│
├── requirements/                       # 📋 Dependency management
│   ├── requirements.txt                # Core dependencies
│   ├── requirements-web.txt            # Web interface dependencies
│   ├── requirements-emulator.txt       # Emulator dependencies
│   ├── requirements-dev.txt            # Development dependencies
│   └── package.json                    # Node.js dependencies (Tailwind)
│
├── run.py                              # Main entry point
└── display_controller.py               # Display controller (could move to src/core)
```

---

## Key Organizational Improvements

### 1. **Documentation Consolidation** (`docs/`)
- All markdown documentation files moved to a dedicated directory
- Organized by category (hardware, configuration, API)
- Easier to find and maintain documentation

### 2. **Source Code Organization** (`src/`)
- **`core/`**: Essential system components
- **`managers/`**: Feature managers organized by domain
  - Sports managers grouped together
  - Weather, stocks, music each get their own subdirectory
- **`utils/`**: Utility functions and helpers
- **`auth/`**: All authentication scripts together
- **`services/`**: Background services

### 3. **Web Interface Separation** (`web/`)
- All web-related files in one place
- Templates and static assets together
- Clear separation from core display logic

### 4. **Asset Management** (`assets/`)
- Moved `of_the_day/` data into `assets/`
- All static resources in one location
- Organized by type and purpose

### 5. **Test Organization** (`tests/`)
- Renamed from `test` to `tests` (Python convention)
- Separated into unit, integration, manual, and utility tests
- Easier to run specific test suites

### 6. **Script Organization** (`scripts/`)
- Grouped by purpose: installation, setup, maintenance, control
- Clear naming conventions
- Easy to find the right script

### 7. **Deployment Files** (`deployment/`)
- Systemd service files
- Future Docker/containerization support
- Clear separation of deployment concerns

### 8. **Hardware Files** (`hardware/`)
- External LED matrix library (could be a git submodule)
- 3D printing files organized by display type
- Hardware-specific documentation

### 9. **Requirements Management** (`requirements/`)
- All dependency files in one location
- Separated by purpose (core, web, dev, emulator)
- Clear dependency management

---

## Migration Strategy

### Phase 1: Low-Risk Documentation & Assets
```bash
# Create new directories
mkdir -p docs/{hardware,configuration,api}
mkdir -p assets/of_the_day

# Move documentation
mv BACKGROUND_SERVICE_README.md docs/
mv AP_TOP_25_IMPLEMENTATION_SUMMARY.md docs/
mv TAILWIND_SETUP.md docs/

# Move of_the_day data
mv of_the_day/* assets/of_the_day/
rmdir of_the_day
```

### Phase 2: Scripts & Utilities
```bash
# Create script directories
mkdir -p scripts/{installation,setup,maintenance,control}

# Move scripts
mv first_time_install.sh scripts/installation/
mv install_service.sh scripts/installation/
mv setup_cache.sh scripts/setup/
mv start_display.sh scripts/control/
mv stop_display.sh scripts/control/
```

### Phase 3: Source Code Reorganization
```bash
# Create source subdirectories
mkdir -p src/{core,managers/{sports,weather,stocks,music,other},utils,auth,services}

# Move core files
mv src/config_manager.py src/core/
mv src/cache_manager.py src/core/
mv src/display_manager.py src/core/

# Move managers
mv src/mlb_manager.py src/managers/sports/
mv src/weather_manager.py src/managers/weather/
mv src/stock_manager.py src/managers/stocks/

# Move auth scripts
mv src/authenticate_spotify.py src/auth/
mv calendar_registration.py src/auth/
```

### Phase 4: Web & Testing
```bash
# Create web directory
mkdir -p web/{templates,static}

# Move web files
mv web_interface*.py web/
mv start_web*.py web/
mv templates web/
mv static web/

# Reorganize tests
mkdir -p tests/{unit,integration,manual,utilities}
# Move appropriate test files to each subdirectory
```

### Phase 5: Deployment & Hardware
```bash
# Create deployment directories
mkdir -p deployment/systemd
mkdir -p hardware/3d-models

# Move service files
mv *.service deployment/systemd/

# Move hardware files
mv "Matrix Stand STL" hardware/3d-models/4mm-pixel-pitch/
mv rpi-rgb-led-matrix-master hardware/rpi-rgb-led-matrix
```

### Phase 6: Requirements
```bash
# Create requirements directory
mkdir -p requirements

# Move and rename requirement files
mv requirements.txt requirements/
mv requirements_web_v2.txt requirements/requirements-web.txt
mv requirements-emulator.txt requirements/
mv package.json requirements/
```

---

## Import Path Updates

After reorganization, import statements will need updates:

### Before:
```python
from cache_manager import CacheManager
from mlb_manager import MLBManager
from weather_manager import WeatherManager
```

### After:
```python
from src.core.cache_manager import CacheManager
from src.managers.sports.mlb_manager import MLBManager
from src.managers.weather.weather_manager import WeatherManager
```

### Recommended: Use Relative Imports Within Packages
```python
# In src/managers/sports/mlb_manager.py
from ...core.cache_manager import CacheManager
from ...base_classes.baseball import BaseballManager
```

---

## Benefits of Recommended Structure

### ✅ **Clarity**
- Clear separation of concerns
- Easy to find specific files
- Logical grouping of related code

### ✅ **Maintainability**
- Easier to add new features
- Clear where new files should go
- Reduced coupling between components

### ✅ **Scalability**
- Structure supports growth
- Easy to add new sports, managers, features
- Modular architecture

### ✅ **Developer Experience**
- New contributors can navigate easily
- Clear project organization
- Standard Python project layout

### ✅ **Testing**
- Clear test organization
- Easy to run specific test suites
- Separation of unit and integration tests

### ✅ **Deployment**
- Deployment files isolated
- Easy to create Docker containers
- Service files clearly organized

---

## Notes & Considerations

1. **Git Submodules**: Consider making `rpi-rgb-led-matrix` a git submodule rather than a copied directory
2. **Virtual Environments**: Add `venv/` or `.venv/` to `.gitignore`
3. **Cache Directories**: Document cache locations in a dedicated file
4. **Config Templates**: Keep templates in version control, actual configs gitignored
5. **Migration Script**: Create a script to automate the migration process
6. **Update Documentation**: Update README.md and all docs to reflect new paths
7. **CI/CD**: Consider adding `.github/workflows/` for automated testing
8. **Environment Variables**: Consider using `.env` files for configuration

---

## Additional Recommendations

### Future Enhancements
- Add `logs/` directory for application logs
- Add `backups/` directory for configuration backups
- Add `cache/` directory for local caching (gitignored)
- Add `.github/` for GitHub-specific files (templates, workflows)
- Consider adding `api/` directory if you build a REST API
- Add `monitoring/` for Prometheus/Grafana configs

### Code Quality
- Add `pyproject.toml` for modern Python project configuration
- Add `.pre-commit-hooks.yaml` for git hooks
- Add `setup.py` or `setup.cfg` for package installation
- Consider adding type hints and using `mypy`

### Security
- Keep all credentials in `config_secrets.json` (gitignored)
- Use environment variables for sensitive data
- Add `.env.example` template file
- Consider using secrets management tools

---

## Conclusion

This recommended structure follows Python best practices, improves code organization, and sets up the project for future growth. The migration can be done incrementally, starting with low-risk changes (documentation and assets) and gradually moving to code reorganization.

The structure balances immediate needs with future scalability, making the codebase more maintainable for both current and future contributors.


