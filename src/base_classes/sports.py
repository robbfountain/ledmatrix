import logging
import os
import time
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import pytz
import requests
from PIL import Image, ImageDraw, ImageFont
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.background_data_service import get_background_service

# Import new architecture components (individual classes will import what they need)
from src.base_classes.api_extractors import APIDataExtractor
from src.base_classes.data_sources import DataSource
from src.cache_manager import CacheManager
from src.display_manager import DisplayManager
from src.dynamic_team_resolver import DynamicTeamResolver
from src.logo_downloader import LogoDownloader, download_missing_logo
from src.odds_manager import OddsManager


class SportsCore(ABC):
    def __init__(self, config: Dict[str, Any], display_manager: DisplayManager, cache_manager: CacheManager, logger: logging.Logger, sport_key: str):
        self.logger = logger
        self.config = config
        self.cache_manager = cache_manager
        self.config_manager = self.cache_manager.config_manager
        self.odds_manager = OddsManager(
            self.cache_manager, self.config_manager)
        self.display_manager = display_manager
        self.display_width = self.display_manager.matrix.width
        self.display_height = self.display_manager.matrix.height

        self.sport_key = sport_key
        self.sport = None
        self.league = None
        
        # Initialize new architecture components (will be overridden by sport-specific classes)
        self.sport_config = None
        self.api_extractor: APIDataExtractor
        self.data_source: DataSource
        self.mode_config = config.get(f"{sport_key}_scoreboard", {})  # Changed config key
        self.is_enabled: bool = self.mode_config.get("enabled", False)
        self.show_odds: bool = self.mode_config.get("show_odds", False)
        self.test_mode: bool = self.mode_config.get("test_mode", False)
        self.logo_dir = Path(self.mode_config.get("logo_dir", "assets/sports/ncaa_logos")) # Changed logo dir
        self.update_interval: int = self.mode_config.get(
            "update_interval_seconds", 60)
        self.show_records: bool = self.mode_config.get('show_records', False)
        self.show_ranking: bool = self.mode_config.get('show_ranking', False)
        # Number of games to show (instead of time-based windows)
        self.recent_games_to_show: int = self.mode_config.get(
            "recent_games_to_show", 5)  # Show last 5 games
        self.upcoming_games_to_show: int = self.mode_config.get(
            "upcoming_games_to_show", 10)  # Show next 10 games
        self.show_favorite_teams_only: bool = self.mode_config.get("show_favorite_teams_only", False)
        self.show_all_live: bool = self.mode_config.get("show_all_live", False)

        self.session = requests.Session()
        retry_strategy = Retry(
            total=5,  # increased number of retries
            backoff_factor=1,  # increased backoff factor
            # added 429 to retry list
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "HEAD", "OPTIONS"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

        self._logo_cache = {}

        # Set up headers
        self.headers = {
            'User-Agent': 'LEDMatrix/1.0 (https://github.com/yourusername/LEDMatrix; contact@example.com)',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive'
        }
        self.last_update = 0
        self.current_game = None
        self.fonts = self._load_fonts()
        
        # Initialize dynamic team resolver and resolve favorite teams
        self.dynamic_resolver = DynamicTeamResolver()
        raw_favorite_teams = self.mode_config.get("favorite_teams", [])
        self.favorite_teams = self.dynamic_resolver.resolve_teams(raw_favorite_teams, sport_key)
        
        # Log dynamic team resolution
        if raw_favorite_teams != self.favorite_teams:
            self.logger.info(f"Resolved dynamic teams: {raw_favorite_teams} -> {self.favorite_teams}")
        else:
            self.logger.info(f"Favorite teams: {self.favorite_teams}")
            
        self.logger.setLevel(logging.INFO)
        
        # Initialize team rankings cache
        self._team_rankings_cache = {}
        self._rankings_cache_timestamp = 0
        self._rankings_cache_duration = 3600  # Cache rankings for 1 hour

        # Initialize background data service
        background_config = self.mode_config.get("background_service", {})
        if background_config.get("enabled", True):  # Default to enabled
            max_workers = background_config.get("max_workers", 3)
            self.background_service = get_background_service(self.cache_manager, max_workers)
            self.background_fetch_requests = {}  # Track background fetch requests
            self.background_enabled = True
            self.logger.info(f"Background service enabled with {max_workers} workers")
        else:
            self.background_service = None
            self.background_fetch_requests = {}
            self.background_enabled = False
            self.logger.info("Background service disabled")

    def _get_season_schedule_dates(self) -> tuple[str, str]:
        return "", ""

    def _draw_scorebug_layout(self, game: Dict, force_clear: bool = False) -> None:
        """Placeholder draw method - subclasses should override."""
        # This base method will be simple, subclasses provide specifics
        try:
            img = Image.new('RGB', (self.display_width, self.display_height), (0, 0, 0))
            draw = ImageDraw.Draw(img)
            status = game.get("status_text", "N/A")
            self._draw_text_with_outline(draw, status, (2, 2), self.fonts['status'])
            self.display_manager.image.paste(img, (0, 0))
            # Don't call update_display here, let subclasses handle it after drawing
        except Exception as e:
            self.logger.error(f"Error in base _draw_scorebug_layout: {e}", exc_info=True)


    def display(self, force_clear: bool = False) -> None:
        """Common display method for all NCAA FB managers""" # Updated docstring
        if not self.is_enabled: # Check if module is enabled
             return

        if not self.current_game:
            current_time = time.time()
            if not hasattr(self, '_last_warning_time'):
                self._last_warning_time = 0
            if current_time - getattr(self, '_last_warning_time', 0) > 300:
                self.logger.warning(f"No game data available to display in {self.__class__.__name__}")
                setattr(self, '_last_warning_time', current_time)
            return

        try:
            self._draw_scorebug_layout(self.current_game, force_clear)
            # display_manager.update_display() should be called within subclass draw methods
            # or after calling display() in the main loop. Let's keep it out of the base display.
        except Exception as e:
             self.logger.error(f"Error during display call in {self.__class__.__name__}: {e}", exc_info=True)


    def _load_fonts(self):
        """Load fonts used by the scoreboard."""
        fonts = {}
        try:
            fonts['score'] = ImageFont.truetype("assets/fonts/PressStart2P-Regular.ttf", 10)
            fonts['time'] = ImageFont.truetype("assets/fonts/PressStart2P-Regular.ttf", 8)
            fonts['team'] = ImageFont.truetype("assets/fonts/PressStart2P-Regular.ttf", 8)
            fonts['status'] = ImageFont.truetype("assets/fonts/4x6-font.ttf", 6) # Using 4x6 for status
            fonts['detail'] = ImageFont.truetype("assets/fonts/4x6-font.ttf", 6) # Added detail font
            fonts['rank'] = ImageFont.truetype("assets/fonts/PressStart2P-Regular.ttf", 10)
            logging.info("Successfully loaded fonts") # Changed log prefix
        except IOError:
            logging.warning("Fonts not found, using default PIL font.") # Changed log prefix
            fonts['score'] = ImageFont.load_default()
            fonts['time'] = ImageFont.load_default()
            fonts['team'] = ImageFont.load_default()
            fonts['status'] = ImageFont.load_default()
            fonts['detail'] = ImageFont.load_default()
            fonts['rank'] = ImageFont.load_default()
        return fonts

    def _draw_dynamic_odds(self, draw: ImageDraw.Draw, odds: Dict[str, Any], width: int, height: int) -> None:
        """Draw odds with dynamic positioning - only show negative spread and position O/U based on favored team."""
        home_team_odds = odds.get('home_team_odds', {})
        away_team_odds = odds.get('away_team_odds', {})
        home_spread = home_team_odds.get('spread_odds')
        away_spread = away_team_odds.get('spread_odds')

        # Get top-level spread as fallback
        top_level_spread = odds.get('spread')
        
        # If we have a top-level spread and the individual spreads are None or 0, use the top-level
        if top_level_spread is not None:
            if home_spread is None or home_spread == 0.0:
                home_spread = top_level_spread
            if away_spread is None:
                away_spread = -top_level_spread

        # Determine which team is favored (has negative spread)
        home_favored = home_spread is not None and home_spread < 0
        away_favored = away_spread is not None and away_spread < 0
        
        # Only show the negative spread (favored team)
        favored_spread = None
        favored_side = None
        
        if home_favored:
            favored_spread = home_spread
            favored_side = 'home'
            self.logger.debug(f"Home team favored with spread: {favored_spread}")
        elif away_favored:
            favored_spread = away_spread
            favored_side = 'away'
            self.logger.debug(f"Away team favored with spread: {favored_spread}")
        else:
            self.logger.debug("No clear favorite - spreads: home={home_spread}, away={away_spread}")
        
        # Show the negative spread on the appropriate side
        if favored_spread is not None:
            spread_text = str(favored_spread)
            font = self.fonts['detail']  # Use detail font for odds
            
            if favored_side == 'home':
                # Home team is favored, show spread on right side
                spread_width = draw.textlength(spread_text, font=font)
                spread_x = width - spread_width  # Top right
                spread_y = 0
                self._draw_text_with_outline(draw, spread_text, (spread_x, spread_y), font, fill=(0, 255, 0))
                self.logger.debug(f"Showing home spread '{spread_text}' on right side")
            else:
                # Away team is favored, show spread on left side
                spread_x = 0  # Top left
                spread_y = 0
                self._draw_text_with_outline(draw, spread_text, (spread_x, spread_y), font, fill=(0, 255, 0))
                self.logger.debug(f"Showing away spread '{spread_text}' on left side")
        
        # Show over/under on the opposite side of the favored team
        over_under = odds.get('over_under')
        if over_under is not None:
            ou_text = f"O/U: {over_under}"
            font = self.fonts['detail']  # Use detail font for odds
            ou_width = draw.textlength(ou_text, font=font)
            
            if favored_side == 'home':
                # Home team is favored, show O/U on left side (opposite of spread)
                ou_x = 0  # Top left
                ou_y = 0
                self.logger.debug(f"Showing O/U '{ou_text}' on left side (home favored)")
            elif favored_side == 'away':
                # Away team is favored, show O/U on right side (opposite of spread)
                ou_x = width - ou_width  # Top right
                ou_y = 0
                self.logger.debug(f"Showing O/U '{ou_text}' on right side (away favored)")
            else:
                # No clear favorite, show O/U in center
                ou_x = (width - ou_width) // 2
                ou_y = 0
                self.logger.debug(f"Showing O/U '{ou_text}' in center (no clear favorite)")
            
            self._draw_text_with_outline(draw, ou_text, (ou_x, ou_y), font, fill=(0, 255, 0))

    def _draw_text_with_outline(self, draw, text, position, font, fill=(255, 255, 255), outline_color=(0, 0, 0)):
        """Draw text with a black outline for better readability."""
        x, y = position
        for dx, dy in [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]:
            draw.text((x + dx, y + dy), text, font=font, fill=outline_color)
        draw.text((x, y), text, font=font, fill=fill)

    def _load_and_resize_logo(self, team_id: str, team_abbrev: str, logo_path: Path, logo_url: str | None ) -> Optional[Image.Image]:
        """Load and resize a team logo, with caching and automatic download if missing."""
        self.logger.debug(f"Logo path: {logo_path}")
        if team_abbrev in self._logo_cache:
            self.logger.debug(f"Using cached logo for {team_abbrev}")
            return self._logo_cache[team_abbrev]

        try:
            # Try different filename variations first (for cases like TA&M vs TAANDM)
            actual_logo_path = None
            filename_variations = LogoDownloader.get_logo_filename_variations(team_abbrev)
            
            for filename in filename_variations:
                test_path = logo_path.parent / filename
                if test_path.exists():
                    actual_logo_path = test_path
                    self.logger.debug(f"Found logo at alternative path: {actual_logo_path}")
                    break
            
            # If no variation found, try to download missing logo
            if not actual_logo_path and not logo_path.exists():
                self.logger.info(f"Logo not found for {team_abbrev} at {logo_path}. Attempting to download.")
                
                # Try to download the logo from ESPN API (this will create placeholder if download fails)
                download_missing_logo(self.sport_key, team_id, team_abbrev, logo_path, logo_url)
                actual_logo_path = logo_path

            # Use the original path if no alternative was found
            if not actual_logo_path:
                actual_logo_path = logo_path

            # Only try to open the logo if the file exists
            if os.path.exists(actual_logo_path):
                logo = Image.open(actual_logo_path)
            else:
                self.logger.error(f"Logo file still doesn't exist at {actual_logo_path} after download attempt")
                return None
            if logo.mode != 'RGBA':
                logo = logo.convert('RGBA')

            max_width = int(self.display_width * 1.5)
            max_height = int(self.display_height * 1.5)
            logo.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            self._logo_cache[team_abbrev] = logo
            return logo

        except Exception as e:
            self.logger.error(f"Error loading logo for {team_abbrev}: {e}", exc_info=True)
            return None

    def _fetch_odds(self, game: Dict) -> None:
        """Fetch odds for a specific game using the new architecture."""
        try:
            if not self.show_odds:
                return
            
            # Determine update interval based on game state
            is_live = game.get('is_live', False)
            update_interval = self.mode_config.get("live_odds_update_interval", 60) if is_live \
                else self.mode_config.get("odds_update_interval", 3600)
            
            # Fetch odds using OddsManager
            odds_data = self.odds_manager.get_odds(
                sport=self.sport,
                league=self.league,
                event_id=game['id'],
                update_interval_seconds=update_interval
            )
            
            if odds_data:
                game['odds'] = odds_data
                self.logger.debug(f"Successfully fetched and attached odds for game {game['id']}")
            else:
                self.logger.debug(f"No odds data returned for game {game['id']}")
                
        except Exception as e:
            self.logger.error(f"Error fetching odds for game {game.get('id', 'N/A')}: {e}")

    def _get_timezone(self):
        try:
            timezone_str = self.config.get('timezone', 'UTC')
            return pytz.timezone(timezone_str)
        except pytz.UnknownTimeZoneError:
            return pytz.utc

    def _should_log(self, warning_type: str, cooldown: int = 60) -> bool:
        """Check if we should log a warning based on cooldown period."""
        current_time = time.time()
        if current_time - self._last_warning_time > cooldown:
            self._last_warning_time = current_time
            return True
        return False

    def _fetch_team_rankings(self) -> Dict[str, int]:
        """Fetch team rankings using the new architecture components."""
        current_time = time.time()
        
        # Check if we have cached rankings that are still valid
        if (self._team_rankings_cache and 
            current_time - self._rankings_cache_timestamp < self._rankings_cache_duration):
            return self._team_rankings_cache
        
        try:
            data = self.data_source.fetch_standings(self.sport, self.league)
            
            rankings = {}
            rankings_data = data.get('rankings', [])
            
            if rankings_data:
                # Use the first ranking (usually AP Top 25)
                first_ranking = rankings_data[0]
                teams = first_ranking.get('ranks', [])
                
                for team_data in teams:
                    team_info = team_data.get('team', {})
                    team_abbr = team_info.get('abbreviation', '')
                    current_rank = team_data.get('current', 0)
                    
                    if team_abbr and current_rank > 0:
                        rankings[team_abbr] = current_rank
            
            # Cache the results
            self._team_rankings_cache = rankings
            self._rankings_cache_timestamp = current_time
            
            self.logger.debug(f"Fetched rankings for {len(rankings)} teams")
            return rankings
            
        except Exception as e:
            self.logger.error(f"Error fetching team rankings: {e}")
            return {}

    def _extract_game_details_common(self, game_event: Dict) -> tuple[Dict | None, Dict | None, Dict | None, Dict | None, Dict | None]:
        if not game_event: 
            return None, None, None, None, None
        try:
            competition = game_event["competitions"][0]
            status = competition["status"]
            competitors = competition["competitors"]
            game_date_str = game_event["date"]
            situation = competition.get("situation")
            start_time_utc = None
            try:
                start_time_utc = datetime.fromisoformat(game_date_str.replace("Z", "+00:00"))
            except ValueError:
                logging.warning(f"Could not parse game date: {game_date_str}")

            home_team = next((c for c in competitors if c.get("homeAway") == "home"), None)
            away_team = next((c for c in competitors if c.get("homeAway") == "away"), None)

            if not home_team or not away_team:
                self.logger.warning(f"Could not find home or away team in event: {game_event.get('id')}")
                return None, None, None, None, None

            home_abbr = home_team["team"]["abbreviation"]
            away_abbr = away_team["team"]["abbreviation"]
            
            # Check if this is a favorite team game BEFORE doing expensive logging
            is_favorite_game = (home_abbr in self.favorite_teams or away_abbr in self.favorite_teams)
            
            # Only log debug info for favorite team games
            if is_favorite_game:
                self.logger.debug(f"Processing favorite team game: {game_event.get('id')}")
                self.logger.debug(f"Found teams: {away_abbr}@{home_abbr}, Status: {status['type']['name']}, State: {status['type']['state']}")
            
            game_time, game_date = "", ""
            if start_time_utc:
                local_time = start_time_utc.astimezone(self._get_timezone())
                game_time = local_time.strftime("%I:%M%p").lstrip('0')
                
                # Check date format from config
                use_short_date_format = self.config.get('display', {}).get('use_short_date_format', False)
                if use_short_date_format:
                    game_date = local_time.strftime("%-m/%-d")
                else:
                    game_date = self.display_manager.format_date_with_ordinal(local_time)


            home_record = home_team.get('records', [{}])[0].get('summary', '') if home_team.get('records') else ''
            away_record = away_team.get('records', [{}])[0].get('summary', '') if away_team.get('records') else ''
            
            # Don't show "0-0" records - set to blank instead
            if home_record in {"0-0", "0-0-0"}:
                home_record = ''
            if away_record in {"0-0", "0-0-0"}:
                away_record = ''

            details = {
                "id": game_event.get("id"),
                "game_time": game_time,
                "game_date": game_date,
                "start_time_utc": start_time_utc,
                "status_text": status["type"]["shortDetail"], # e.g., "Final", "7:30 PM", "Q1 12:34"
                "is_live": status["type"]["state"] == "in",
                "is_final": status["type"]["state"] == "post",
                "is_upcoming": (status["type"]["state"] == "pre" or 
                               status["type"]["name"].lower() in ['scheduled', 'pre-game', 'status_scheduled']),
                "is_halftime": status["type"]["state"] == "halftime" or status["type"]["name"] == "STATUS_HALFTIME", # Added halftime check
                "home_abbr": home_abbr,
                "home_id": home_team["id"],
                "home_score": home_team.get("score", "0"),
                "home_logo_path": self.logo_dir / Path(f"{LogoDownloader.normalize_abbreviation(home_abbr)}.png"),
                "home_logo_url": home_team["team"].get("logo"),
                "home_record": home_record,
                "away_record": away_record,
                "away_abbr": away_abbr,
                "away_id": away_team["id"],
                "away_score": away_team.get("score", "0"),
                "away_logo_path": self.logo_dir / Path(f"{LogoDownloader.normalize_abbreviation(away_abbr)}.png"),
                "away_logo_url": away_team["team"].get("logo"),
                "is_within_window": True, # Whether game is within display window

            }
            return details, home_team, away_team, status, situation
        except Exception as e:
            # Log the problematic event structure if possible
            logging.error(f"Error extracting game details: {e} from event: {game_event.get('id')}", exc_info=True)
            return None, None, None, None, None

    @abstractmethod
    def _extract_game_details(self, game_event: dict) -> dict | None:
        details, _, _, _, _ = self._extract_game_details_common(game_event)
        return details

    @abstractmethod
    def _fetch_data(self) -> Optional[Dict]:
        pass

    def _fetch_todays_games(self) -> Optional[Dict]:
        """Fetch only today's games for live updates (not entire season)."""
        try:
            now = datetime.now()
            formatted_date = now.strftime("%Y%m%d")
            # Fetch todays games only
            url = f"https://site.api.espn.com/apis/site/v2/sports/{self.sport}/{self.league}/scoreboard"
            response = self.session.get(url, params={"dates": formatted_date, "limit": 1000}, headers=self.headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            events = data.get('events', [])
            
            self.logger.info(f"Fetched {len(events)} todays games for {self.sport} - {self.league}")
            return {'events': events}
        except requests.exceptions.RequestException as e:
            self.logger.error(f"API error fetching todays games for {self.sport} - {self.league}: {e}")
            return None
        
    def _get_weeks_data(self) -> Optional[Dict]:
        """
        Get partial data for immediate display while background fetch is in progress.
        This fetches current/recent games only for quick response.
        """
        try:
            # Fetch current week and next few days for immediate display
            now = datetime.now(pytz.utc)
            immediate_events = []
            
            start_date = now + timedelta(weeks=-2)
            end_date = now + timedelta(weeks=1)
            date_str = f"{start_date.strftime('%Y%m%d')}-{end_date.strftime('%Y%m%d')}"
            url = f"https://site.api.espn.com/apis/site/v2/sports/{self.sport}/{self.league}/scoreboard"
            response = self.session.get(url, params={"dates": date_str, "limit": 1000},headers=self.headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            immediate_events = data.get('events', [])
                
            if immediate_events:
                self.logger.info(f"Fetched {len(immediate_events)} events {date_str}")
                return {'events': immediate_events}
                
        except requests.exceptions.RequestException as e:
            self.logger.warning(f"Error fetching this weeks games for {self.sport} - {self.league} - {date_str}: {e}")
        return None

    def _custom_scorebug_layout(self, game: dict, draw_overlay: ImageDraw.ImageDraw):
        pass

class SportsUpcoming(SportsCore):
    def __init__(self, config: Dict[str, Any], display_manager: DisplayManager, cache_manager: CacheManager, logger: logging.Logger, sport_key: str):
        super().__init__(config, display_manager, cache_manager, logger, sport_key)
        self.upcoming_games = [] # Store all fetched upcoming games initially
        self.games_list = [] # Filtered list for display (favorite teams)
        self.current_game_index = 0
        self.last_update = 0
        self.update_interval = self.mode_config.get("upcoming_update_interval", 3600) # Check for recent games every hour
        self.last_log_time = 0
        self.log_interval = 300
        self.last_warning_time = 0
        self.warning_cooldown = 300
        self.last_game_switch = 0
        self.game_display_duration = 15 # Display each upcoming game for 15 seconds

    def update(self):
        """Update upcoming games data."""
        if not self.is_enabled: return
        current_time = time.time()
        if current_time - self.last_update < self.update_interval:
            return

        self.last_update = current_time
        
        # Fetch rankings if enabled
        if self.show_ranking:
            self._fetch_team_rankings()
        
        try:
            data = self._fetch_data() # Uses shared cache
            if not data or 'events' not in data:
                self.logger.warning("No events found in shared data.") # Changed log prefix
                if not self.games_list: self.current_game = None
                return

            events = data['events']
            # self.logger.info(f"Processing {len(events)} events from shared data.") # Changed log prefix

            processed_games = []
            favorite_games_found = 0
            all_upcoming_games = 0  # Count all upcoming games regardless of favorites
            
            for event in events:
                game = self._extract_game_details(event)
                # Count all upcoming games for debugging
                if game and game['is_upcoming']:
                    all_upcoming_games += 1
                    
                # Filter criteria: must be upcoming ('pre' state)
                if game and game['is_upcoming']:
                    # Only fetch odds for games that will be displayed
                    if self.show_favorite_teams_only:
                        if not self.favorite_teams:
                            continue
                        if game['home_abbr'] not in self.favorite_teams and game['away_abbr'] not in self.favorite_teams:
                            continue
                    processed_games.append(game)
                    # Count favorite team games for logging
                    if (game['home_abbr'] in self.favorite_teams or 
                        game['away_abbr'] in self.favorite_teams):
                        favorite_games_found += 1
                    if self.show_odds:
                        self._fetch_odds(game)

            # Enhanced logging for debugging
            self.logger.info(f"Found {all_upcoming_games} total upcoming games in data")
            self.logger.info(f"Found {len(processed_games)} upcoming games after filtering")

            if processed_games:
                for game in processed_games[:3]:  # Show first 3
                    self.logger.info(f"  {game['away_abbr']}@{game['home_abbr']} - {game['start_time_utc']}")
            
            if self.favorite_teams and all_upcoming_games > 0:
                self.logger.info(f"Favorite teams: {self.favorite_teams}")
                self.logger.info(f"Found {favorite_games_found} favorite team upcoming games")

            # Filter for favorite teams only if the config is set
            if self.show_favorite_teams_only:                
                # Select one game per favorite team (earliest upcoming game for each team)
                team_games = []
                for team in self.favorite_teams:
                    # Find games where this team is playing                  
                    if team_specific_games := [game for game in processed_games if game['home_abbr'] == team or game['away_abbr'] == team]:
                        # Sort by game time and take the earliest
                        team_specific_games.sort(key=lambda g: g.get('start_time_utc') or datetime.max.replace(tzinfo=timezone.utc))
                        team_games.append(team_specific_games[0])
                
                # Sort the final list by game time
                team_games.sort(key=lambda g: g.get('start_time_utc') or datetime.max.replace(tzinfo=timezone.utc))
            else:
                team_games = processed_games # Show all upcoming if no favorites
                # Sort by game time, earliest first
                team_games.sort(key=lambda g: g.get('start_time_utc') or datetime.max.replace(tzinfo=timezone.utc))
                # Limit to the specified number of upcoming games
                team_games = team_games[:self.upcoming_games_to_show]

            # Log changes or periodically
            should_log = (
                 current_time - self.last_log_time >= self.log_interval or
                 len(team_games) != len(self.games_list) or
                 any(g1['id'] != g2.get('id') for g1, g2 in zip(self.games_list, team_games)) or
                 (not self.games_list and team_games)
             )

            # Check if the list of games to display has changed
            new_game_ids = {g['id'] for g in team_games}
            current_game_ids = {g['id'] for g in self.games_list}

            if new_game_ids != current_game_ids:
                 self.logger.info(f"Found {len(team_games)} upcoming games within window for display.") # Changed log prefix
                 self.games_list = team_games
                 if not self.current_game or not self.games_list or self.current_game['id'] not in new_game_ids:
                      self.current_game_index = 0
                      self.current_game = self.games_list[0] if self.games_list else None
                      self.last_game_switch = current_time
                 else:
                      try:
                           self.current_game_index = next(i for i, g in enumerate(self.games_list) if g['id'] == self.current_game['id'])
                           self.current_game = self.games_list[self.current_game_index]
                      except StopIteration:
                           self.current_game_index = 0
                           self.current_game = self.games_list[0]
                           self.last_game_switch = current_time

            elif self.games_list:
                 self.current_game = self.games_list[self.current_game_index] # Update data

            if not self.games_list:
                 self.logger.info("No relevant upcoming games found to display.") # Changed log prefix
                 self.current_game = None

            if should_log and not self.games_list:
                 # Log favorite teams only if no games are found and logging is needed
                 self.logger.debug(f"Favorite teams: {self.favorite_teams}") # Changed log prefix
                 self.logger.debug(f"Total upcoming games before filtering: {len(processed_games)}") # Changed log prefix
                 self.last_log_time = current_time
            elif should_log:
                self.last_log_time = current_time

        except Exception as e:
            self.logger.error(f"Error updating upcoming games: {e}", exc_info=True) # Changed log prefix
            # self.current_game = None # Decide if clear on error

    def _draw_scorebug_layout(self, game: Dict, force_clear: bool = False) -> None:
        """Draw the layout for an upcoming NCAA FB game.""" # Updated docstring
        try:
            main_img = Image.new('RGBA', (self.display_width, self.display_height), (0, 0, 0, 255))
            overlay = Image.new('RGBA', (self.display_width, self.display_height), (0, 0, 0, 0))
            draw_overlay = ImageDraw.Draw(overlay)

            home_logo = self._load_and_resize_logo(game["home_id"], game["home_abbr"], game["home_logo_path"], game.get("home_logo_url"))
            away_logo = self._load_and_resize_logo(game["away_id"], game["away_abbr"], game["away_logo_path"], game.get("away_logo_url"))

            if not home_logo or not away_logo:
                self.logger.error(f"Failed to load logos for game: {game.get('id')}") # Changed log prefix
                draw_final = ImageDraw.Draw(main_img.convert('RGB'))
                self._draw_text_with_outline(draw_final, "Logo Error", (5,5), self.fonts['status'])
                self.display_manager.image.paste(main_img.convert('RGB'), (0, 0))
                self.display_manager.update_display()
                return

            center_y = self.display_height // 2

            # MLB-style logo positions
            home_x = self.display_width - home_logo.width + 2
            home_y = center_y - (home_logo.height // 2)
            main_img.paste(home_logo, (home_x, home_y), home_logo)

            away_x = -2
            away_y = center_y - (away_logo.height // 2)
            main_img.paste(away_logo, (away_x, away_y), away_logo)

            # Draw Text Elements on Overlay
            game_date = game.get("game_date", "")
            game_time = game.get("game_time", "")

            # Note: Rankings are now handled in the records/rankings section below

            # "Next Game" at the top (use smaller status font)
            status_font = self.fonts['status']
            if self.display_width > 128:
                status_font = self.fonts['time']
            status_text = "Next Game"
            status_width = draw_overlay.textlength(status_text, font=status_font)
            status_x = (self.display_width - status_width) // 2
            status_y = 1 # Changed from 2
            self._draw_text_with_outline(draw_overlay, status_text, (status_x, status_y), status_font)

            # Date text (centered, below "Next Game")
            date_width = draw_overlay.textlength(game_date, font=self.fonts['time'])
            date_x = (self.display_width - date_width) // 2
            # Adjust Y position to stack date and time nicely
            date_y = center_y - 7 # Raise date slightly
            self._draw_text_with_outline(draw_overlay, game_date, (date_x, date_y), self.fonts['time'])

            # Time text (centered, below Date)
            time_width = draw_overlay.textlength(game_time, font=self.fonts['time'])
            time_x = (self.display_width - time_width) // 2
            time_y = date_y + 9 # Place time below date
            self._draw_text_with_outline(draw_overlay, game_time, (time_x, time_y), self.fonts['time'])

            # Draw odds if available
            if 'odds' in game and game['odds']:
                self._draw_dynamic_odds(draw_overlay, game['odds'], self.display_width, self.display_height)

            # Draw records or rankings if enabled
            if self.show_records or self.show_ranking:
                try:
                    record_font = ImageFont.truetype("assets/fonts/4x6-font.ttf", 6)
                    self.logger.debug(f"Loaded 6px record font successfully")
                except IOError:
                    record_font = ImageFont.load_default()
                    self.logger.warning(f"Failed to load 6px font, using default font (size: {record_font.size})")
                
                # Get team abbreviations
                away_abbr = game.get('away_abbr', '')
                home_abbr = game.get('home_abbr', '')
                
                record_bbox = draw_overlay.textbbox((0,0), "0-0", font=record_font)
                record_height = record_bbox[3] - record_bbox[1]
                record_y = self.display_height - record_height
                self.logger.debug(f"Record positioning: height={record_height}, record_y={record_y}, display_height={self.display_height}")

                # Display away team info
                if away_abbr:
                    if self.show_ranking and self.show_records:
                        # When both rankings and records are enabled, rankings replace records completely
                        away_rank = self._team_rankings_cache.get(away_abbr, 0)
                        if away_rank > 0:
                            away_text = f"#{away_rank}"
                        else:
                            # Show nothing for unranked teams when rankings are prioritized
                            away_text = ''
                    elif self.show_ranking:
                        # Show ranking only if available
                        away_rank = rankself._team_rankings_cacheings.get(away_abbr, 0)
                        if away_rank > 0:
                            away_text = f"#{away_rank}"
                        else:
                            away_text = ''
                    elif self.show_records:
                        # Show record only when rankings are disabled
                        away_text = game.get('away_record', '')
                    else:
                        away_text = ''
                    
                    if away_text:
                        away_record_x = 0
                        self.logger.debug(f"Drawing away ranking '{away_text}' at ({away_record_x}, {record_y}) with font size {record_font.size if hasattr(record_font, 'size') else 'unknown'}")
                        self._draw_text_with_outline(draw_overlay, away_text, (away_record_x, record_y), record_font)

                # Display home team info
                if home_abbr:
                    if self.show_ranking and self.show_records:
                        # When both rankings and records are enabled, rankings replace records completely
                        home_rank = self._team_rankings_cache.get(home_abbr, 0)
                        if home_rank > 0:
                            home_text = f"#{home_rank}"
                        else:
                            # Show nothing for unranked teams when rankings are prioritized
                            home_text = ''
                    elif self.show_ranking:
                        # Show ranking only if available
                        home_rank = self._team_rankings_cache.get(home_abbr, 0)
                        if home_rank > 0:
                            home_text = f"#{home_rank}"
                        else:
                            home_text = ''
                    elif self.show_records:
                        # Show record only when rankings are disabled
                        home_text = game.get('home_record', '')
                    else:
                        home_text = ''
                    
                    if home_text:
                        home_record_bbox = draw_overlay.textbbox((0,0), home_text, font=record_font)
                        home_record_width = home_record_bbox[2] - home_record_bbox[0]
                        home_record_x = self.display_width - home_record_width
                        self.logger.debug(f"Drawing home ranking '{home_text}' at ({home_record_x}, {record_y}) with font size {record_font.size if hasattr(record_font, 'size') else 'unknown'}")
                        self._draw_text_with_outline(draw_overlay, home_text, (home_record_x, record_y), record_font)

            # Composite and display
            main_img = Image.alpha_composite(main_img, overlay)
            main_img = main_img.convert('RGB')
            self.display_manager.image.paste(main_img, (0, 0))
            self.display_manager.update_display() # Update display here

        except Exception as e:
            self.logger.error(f"Error displaying upcoming game: {e}", exc_info=True) # Changed log prefix

    def display(self, force_clear=False):
        """Display upcoming games, handling switching."""
        if not self.is_enabled: return

        if not self.games_list:
            if self.current_game: self.current_game = None # Clear state if list empty
            current_time = time.time()
            # Log warning periodically if no games found
            if current_time - self.last_warning_time > self.warning_cooldown:
                self.logger.info("No upcoming games found for favorite teams to display.") # Changed log prefix
                self.last_warning_time = current_time
            return # Skip display update

        try:
            current_time = time.time()

            # Check if it's time to switch games
            if len(self.games_list) > 1 and current_time - self.last_game_switch >= self.game_display_duration:
                self.current_game_index = (self.current_game_index + 1) % len(self.games_list)
                self.current_game = self.games_list[self.current_game_index]
                self.last_game_switch = current_time
                force_clear = True # Force redraw on switch
                
                # Log team switching with sport prefix
                if self.current_game:
                    away_abbr = self.current_game.get('away_abbr', 'UNK')
                    home_abbr = self.current_game.get('home_abbr', 'UNK')
                    sport_prefix = self.sport_key.upper() if hasattr(self, 'sport_key') else 'SPORT'
                    self.logger.info(f"[{sport_prefix} Upcoming] Showing {away_abbr} vs {home_abbr}")
                else:
                    self.logger.debug(f"Switched to game index {self.current_game_index}")

            if self.current_game:
                self._draw_scorebug_layout(self.current_game, force_clear)
            # update_display() is called within _draw_scorebug_layout for upcoming

        except Exception as e:
            self.logger.error(f"Error in display loop: {e}", exc_info=True) # Changed log prefix


class SportsRecent(SportsCore):

    def __init__(self, config: Dict[str, Any], display_manager: DisplayManager, cache_manager: CacheManager, logger: logging.Logger, sport_key: str):
        super().__init__(config, display_manager, cache_manager, logger, sport_key)
        self.recent_games = [] # Store all fetched recent games initially
        self.games_list = [] # Filtered list for display (favorite teams)
        self.current_game_index = 0
        self.last_update = 0
        self.update_interval = self.mode_config.get("recent_update_interval", 3600) # Check for recent games every hour
        self.last_game_switch = 0
        self.game_display_duration = 15 # Display each recent game for 15 seconds

    def update(self):
        """Update recent games data."""
        if not self.is_enabled: return
        current_time = time.time()
        if current_time - self.last_update < self.update_interval:
            return

        self.last_update = current_time # Update time even if fetch fails
        
        # Fetch rankings if enabled
        if self.show_ranking:
            self._fetch_team_rankings()
        
        try:
            data = self._fetch_data() # Uses shared cache
            if not data or 'events' not in data:
                self.logger.warning("No events found in shared data.") # Changed log prefix
                if not self.games_list: 
                    self.current_game = None # Clear display if no games were showing
                return

            events = data['events']
            self.logger.info(f"Processing {len(events)} events from shared data.") # Changed log prefix

            # Define date range for "recent" games (last 21 days to capture games from 3 weeks ago)
            now = datetime.now(timezone.utc)
            recent_cutoff = now - timedelta(days=21)
            self.logger.info(f"Current time: {now}, Recent cutoff: {recent_cutoff} (21 days ago)")
            
            # Process games and filter for final games, date range & favorite teams
            processed_games = []
            for event in events:
                game = self._extract_game_details(event)
                # Filter criteria: must be final AND within recent date range
                if game and game['is_final']:
                    game_time = game.get('start_time_utc')
                    if game_time and game_time >= recent_cutoff:
                        processed_games.append(game)
            # Filter for favorite teams
            if self.favorite_teams:
                # Get all games involving favorite teams
                favorite_team_games = [game for game in processed_games
                                      if game['home_abbr'] in self.favorite_teams or
                                         game['away_abbr'] in self.favorite_teams]
                self.logger.info(f"Found {len(favorite_team_games)} favorite team games out of {len(processed_games)} total final games within last 21 days")
                
                # Select one game per favorite team (most recent game for each team)
                team_games = []
                for team in self.favorite_teams:
                    # Find games where this team is playing
                    team_specific_games = [game for game in favorite_team_games
                                          if game['home_abbr'] == team or game['away_abbr'] == team]
                    
                    if team_specific_games:
                        # Sort by game time and take the most recent
                        team_specific_games.sort(key=lambda g: g.get('start_time_utc') or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
                        team_games.append(team_specific_games[0])
                
                # Sort the final list by game time (most recent first)
                team_games.sort(key=lambda g: g.get('start_time_utc') or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
                
                # Debug: Show which games are selected for display
                for i, game in enumerate(team_games):
                    self.logger.info(f"Game {i+1} for display: {game['away_abbr']} @ {game['home_abbr']} - {game.get('start_time_utc')} - Score: {game['away_score']}-{game['home_score']}")
            else:
                 team_games = processed_games # Show all recent games if no favorites defined
                 self.logger.info(f"Found {len(processed_games)} total final games within last 21 days (no favorite teams configured)")
                 # Sort by game time, most recent first
                 team_games.sort(key=lambda g: g.get('start_time_utc') or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
                 # Limit to the specified number of recent games
                 team_games = team_games[:self.recent_games_to_show]

            # Check if the list of games to display has changed
            new_game_ids = {g['id'] for g in team_games}
            current_game_ids = {g['id'] for g in self.games_list}

            if new_game_ids != current_game_ids:
                self.logger.info(f"Found {len(team_games)} final games within window for display.") # Changed log prefix
                self.games_list = team_games
                # Reset index if list changed or current game removed
                if not self.current_game or not self.games_list or self.current_game['id'] not in new_game_ids:
                     self.current_game_index = 0
                     self.current_game = self.games_list[0] if self.games_list else None
                     self.last_game_switch = current_time # Reset switch timer
                else:
                     # Try to maintain position if possible
                     try:
                          self.current_game_index = next(i for i, g in enumerate(self.games_list) if g['id'] == self.current_game['id'])
                          self.current_game = self.games_list[self.current_game_index] # Update data just in case
                     except StopIteration:
                          self.current_game_index = 0
                          self.current_game = self.games_list[0]
                          self.last_game_switch = current_time

            elif self.games_list:
                 # List content is same, just update data for current game
                 self.current_game = self.games_list[self.current_game_index]

            if not self.games_list:
                 self.logger.info("No relevant recent games found to display.") # Changed log prefix
                 self.current_game = None # Ensure display clears if no games

        except Exception as e:
            self.logger.error(f"Error updating recent games: {e}", exc_info=True) # Changed log prefix
            # Don't clear current game on error, keep showing last known state
            # self.current_game = None # Decide if we want to clear display on error

    def _draw_scorebug_layout(self, game: Dict, force_clear: bool = False) -> None:
        """Draw the layout for a recently completed NCAA FB game.""" # Updated docstring
        try:
            main_img = Image.new('RGBA', (self.display_width, self.display_height), (0, 0, 0, 255))
            overlay = Image.new('RGBA', (self.display_width, self.display_height), (0, 0, 0, 0))
            draw_overlay = ImageDraw.Draw(overlay)

            home_logo = self._load_and_resize_logo(game["home_id"], game["home_abbr"], game["home_logo_path"], game.get("home_logo_url"))
            away_logo = self._load_and_resize_logo(game["away_id"], game["away_abbr"], game["away_logo_path"], game.get("away_logo_url"))

            if not home_logo or not away_logo:
                self.logger.error(f"Failed to load logos for game: {game.get('id')}") # Changed log prefix
                # Draw placeholder text if logos fail (similar to live)
                draw_final = ImageDraw.Draw(main_img.convert('RGB'))
                self._draw_text_with_outline(draw_final, "Logo Error", (5,5), self.fonts['status'])
                self.display_manager.image.paste(main_img.convert('RGB'), (0, 0))
                self.display_manager.update_display()
                return

            center_y = self.display_height // 2

            # MLB-style logo positioning (closer to edges)
            home_x = self.display_width - home_logo.width + 2
            home_y = center_y - (home_logo.height // 2)
            main_img.paste(home_logo, (home_x, home_y), home_logo)

            away_x = -2
            away_y = center_y - (away_logo.height // 2)
            main_img.paste(away_logo, (away_x, away_y), away_logo)

            # Draw Text Elements on Overlay
            # Note: Rankings are now handled in the records/rankings section below

            # Final Scores (Centered, same position as live)
            home_score = str(game.get("home_score", "0"))
            away_score = str(game.get("away_score", "0"))
            score_text = f"{away_score}-{home_score}"
            score_width = draw_overlay.textlength(score_text, font=self.fonts['score'])
            score_x = (self.display_width - score_width) // 2
            score_y = self.display_height - 14
            self._draw_text_with_outline(draw_overlay, score_text, (score_x, score_y), self.fonts['score'])

            # "Final" text (Top center)
            status_text = game.get("period_text", "Final") # Use formatted period text (e.g., "Final/OT") or default "Final"
            status_width = draw_overlay.textlength(status_text, font=self.fonts['time'])
            status_x = (self.display_width - status_width) // 2
            status_y = 1
            self._draw_text_with_outline(draw_overlay, status_text, (status_x, status_y), self.fonts['time'])

            # Draw odds if available
            if 'odds' in game and game['odds']:
                self._draw_dynamic_odds(draw_overlay, game['odds'], self.display_width, self.display_height)

            # Draw records or rankings if enabled
            if self.show_records or self.show_ranking:
                try:
                    record_font = ImageFont.truetype("assets/fonts/4x6-font.ttf", 6)
                    self.logger.debug(f"Loaded 6px record font successfully")
                except IOError:
                    record_font = ImageFont.load_default()
                    self.logger.warning(f"Failed to load 6px font, using default font (size: {record_font.size})")
                
                # Get team abbreviations
                away_abbr = game.get('away_abbr', '')
                home_abbr = game.get('home_abbr', '')
                
                record_bbox = draw_overlay.textbbox((0,0), "0-0", font=record_font)
                record_height = record_bbox[3] - record_bbox[1]
                record_y = self.display_height - record_height
                self.logger.debug(f"Record positioning: height={record_height}, record_y={record_y}, display_height={self.display_height}")

                # Display away team info
                if away_abbr:
                    if self.show_ranking and self.show_records:
                        # When both rankings and records are enabled, rankings replace records completely
                        away_rank = self._team_rankings_cache.get(away_abbr, 0)
                        if away_rank > 0:
                            away_text = f"#{away_rank}"
                        else:
                            # Show nothing for unranked teams when rankings are prioritized
                            away_text = ''
                    elif self.show_ranking:
                        # Show ranking only if available
                        away_rank = self._team_rankings_cache.get(away_abbr, 0)
                        if away_rank > 0:
                            away_text = f"#{away_rank}"
                        else:
                            away_text = ''
                    elif self.show_records:
                        # Show record only when rankings are disabled
                        away_text = game.get('away_record', '')
                    else:
                        away_text = ''
                    
                    if away_text:
                        away_record_x = 0
                        self.logger.debug(f"Drawing away ranking '{away_text}' at ({away_record_x}, {record_y}) with font size {record_font.size if hasattr(record_font, 'size') else 'unknown'}")
                        self._draw_text_with_outline(draw_overlay, away_text, (away_record_x, record_y), record_font)

                # Display home team info
                if home_abbr:
                    if self.show_ranking and self.show_records:
                        # When both rankings and records are enabled, rankings replace records completely
                        home_rank = self._team_rankings_cache.get(home_abbr, 0)
                        if home_rank > 0:
                            home_text = f"#{home_rank}"
                        else:
                            # Show nothing for unranked teams when rankings are prioritized
                            home_text = ''
                    elif self.show_ranking:
                        # Show ranking only if available
                        home_rank = self._team_rankings_cache.get(home_abbr, 0)
                        if home_rank > 0:
                            home_text = f"#{home_rank}"
                        else:
                            home_text = ''
                    elif self.show_records:
                        # Show record only when rankings are disabled
                        home_text = game.get('home_record', '')
                    else:
                        home_text = ''
                    
                    if home_text:
                        home_record_bbox = draw_overlay.textbbox((0,0), home_text, font=record_font)
                        home_record_width = home_record_bbox[2] - home_record_bbox[0]
                        home_record_x = self.display_width - home_record_width
                        self.logger.debug(f"Drawing home ranking '{home_text}' at ({home_record_x}, {record_y}) with font size {record_font.size if hasattr(record_font, 'size') else 'unknown'}")
                        self._draw_text_with_outline(draw_overlay, home_text, (home_record_x, record_y), record_font)

            self._custom_scorebug_layout(game, draw_overlay)
            # Composite and display
            main_img = Image.alpha_composite(main_img, overlay)
            main_img = main_img.convert('RGB')
            self.display_manager.image.paste(main_img, (0, 0))
            self.display_manager.update_display() # Update display here

        except Exception as e:
            self.logger.error(f"Error displaying recent game: {e}", exc_info=True) # Changed log prefix

    def display(self, force_clear=False):
        """Display recent games, handling switching."""
        if not self.is_enabled or not self.games_list:
            # If disabled or no games, ensure display might be cleared by main loop if needed
            # Or potentially clear it here? For now, rely on main loop/other managers.
            if not self.games_list and self.current_game:
                 self.current_game = None # Clear internal state if list becomes empty
            return

        try:
            current_time = time.time()

            # Check if it's time to switch games
            if len(self.games_list) > 1 and current_time - self.last_game_switch >= self.game_display_duration:
                self.current_game_index = (self.current_game_index + 1) % len(self.games_list)
                self.current_game = self.games_list[self.current_game_index]
                self.last_game_switch = current_time
                force_clear = True # Force redraw on switch
                
                # Log team switching with sport prefix
                if self.current_game:
                    away_abbr = self.current_game.get('away_abbr', 'UNK')
                    home_abbr = self.current_game.get('home_abbr', 'UNK')
                    sport_prefix = self.sport_key.upper() if hasattr(self, 'sport_key') else 'SPORT'
                    self.logger.info(f"[{sport_prefix} Recent] Showing {away_abbr} vs {home_abbr}")
                else:
                    self.logger.debug(f"Switched to game index {self.current_game_index}")

            if self.current_game:
                self._draw_scorebug_layout(self.current_game, force_clear)
            # update_display() is called within _draw_scorebug_layout for recent

        except Exception as e:
            self.logger.error(f"Error in display loop: {e}", exc_info=True) # Changed log prefix

class SportsLive(SportsCore):

    def __init__(self, config: Dict[str, Any], display_manager: DisplayManager, cache_manager: CacheManager, logger: logging.Logger, sport_key: str):
        super().__init__(config, display_manager, cache_manager, logger, sport_key)
        self.update_interval = self.mode_config.get("live_update_interval", 15)
        self.no_data_interval = 300
        self.last_update = 0
        self.live_games = []
        self.current_game_index = 0
        self.last_game_switch = 0
        self.game_display_duration = self.mode_config.get("live_game_duration", 20)
        self.last_display_update = 0
        self.last_log_time = 0
        self.log_interval = 300
        self.last_count_log_time = 0  # Track when we last logged count data
        self.count_log_interval = 5  # Only log count data every 5 seconds

    @abstractmethod
    def _test_mode_update(self) -> None:
        return

    def update(self):
        """Update live game data and handle game switching."""
        if not self.is_enabled:
            return

        # Define current_time and interval before the problematic line (originally line 455)
        # Ensure 'import time' is present at the top of the file.
        current_time = time.time()

        # Define interval using a pattern similar to NFLLiveManager's update method.
        # Uses getattr for robustness, assuming attributes for live_games, test_mode,
        # no_data_interval, and update_interval are available on self.
        _live_games_attr = self.live_games
        _test_mode_attr = self.test_mode # test_mode is often from a base class or config
        _no_data_interval_attr = self.no_data_interval # Default similar to NFLLiveManager
        _update_interval_attr = self.update_interval  # Default similar to NFLLiveManager

        interval = _no_data_interval_attr if not _live_games_attr and not _test_mode_attr else _update_interval_attr
        
        # Original line from traceback (line 455), now with variables defined:
        if current_time - self.last_update >= interval:
            self.last_update = current_time

            # Fetch rankings if enabled
            if self.show_ranking:
                self._fetch_team_rankings()

            if self.test_mode:
                # Simulate clock running down in test mode
                self._test_mode_update()
            else:
                # Fetch live game data
                data = self._fetch_data()
                new_live_games = []
                if data and "events" in data:
                    for game in data["events"]:
                        details = self._extract_game_details(game)
                        if details and (details["is_live"] or details["is_halftime"]):
                            # If show_favorite_teams_only is true, only add if it's a favorite.
                            # Otherwise, add all games.
                            if self.show_all_live or not self.show_favorite_teams_only or (self.show_favorite_teams_only and (details["home_abbr"] in self.favorite_teams or details["away_abbr"] in self.favorite_teams)):
                                if self.show_odds:
                                    self._fetch_odds(details)
                                new_live_games.append(details)
                    # Log changes or periodically
                    current_time_for_log = time.time() # Use a consistent time for logging comparison
                    should_log = (
                        current_time_for_log - self.last_log_time >= self.log_interval or
                        len(new_live_games) != len(self.live_games) or
                        any(g1['id'] != g2.get('id') for g1, g2 in zip(self.live_games, new_live_games)) or # Check if game IDs changed
                        (not self.live_games and new_live_games) # Log if games appeared
                    )

                    if should_log:
                        if new_live_games:
                            filter_text = "favorite teams" if self.show_favorite_teams_only or self.show_all_live else "all teams"
                            self.logger.info(f"Found {len(new_live_games)} live/halftime games for {filter_text}.")
                            for game_info in new_live_games: # Renamed game to game_info
                                self.logger.info(f"  - {game_info['away_abbr']}@{game_info['home_abbr']} ({game_info.get('status_text', 'N/A')})")
                        else:
                            filter_text = "favorite teams" if self.show_favorite_teams_only or self.show_all_live else "criteria"
                            self.logger.info(f"No live/halftime games found for {filter_text}.")
                        self.last_log_time = current_time_for_log


                    # Update game list and current game
                    if new_live_games:
                        # Check if the games themselves changed, not just scores/time
                        new_game_ids = {g['id'] for g in new_live_games}
                        current_game_ids = {g['id'] for g in self.live_games}

                        if new_game_ids != current_game_ids:
                            self.live_games = sorted(new_live_games, key=lambda g: g.get('start_time_utc') or datetime.now(timezone.utc)) # Sort by start time
                            # Reset index if current game is gone or list is new
                            if not self.current_game or self.current_game['id'] not in new_game_ids:
                                self.current_game_index = 0
                                self.current_game = self.live_games[0] if self.live_games else None
                                self.last_game_switch = current_time
                            else:
                                # Find current game's new index if it still exists
                                try:
                                     self.current_game_index = next(i for i, g in enumerate(self.live_games) if g['id'] == self.current_game['id'])
                                     self.current_game = self.live_games[self.current_game_index] # Update current_game with fresh data
                                except StopIteration: # Should not happen if check above passed, but safety first
                                     self.current_game_index = 0
                                     self.current_game = self.live_games[0]
                                     self.last_game_switch = current_time

                        else:
                             # Just update the data for the existing games
                             temp_game_dict = {g['id']: g for g in new_live_games}
                             self.live_games = [temp_game_dict.get(g['id'], g) for g in self.live_games] # Update in place
                             if self.current_game:
                                  self.current_game = temp_game_dict.get(self.current_game['id'], self.current_game)

                        # Display update handled by main loop based on interval

                    else:
                        # No live games found
                        if self.live_games: # Were there games before?
                            self.logger.info("Live games previously showing have ended or are no longer live.") # Changed log prefix
                        self.live_games = []
                        self.current_game = None
                        self.current_game_index = 0

                else:
                    # Error fetching data or no events
                     if self.live_games: # Were there games before?
                         self.logger.warning("Could not fetch update; keeping existing live game data for now.") # Changed log prefix
                     else:
                         self.logger.warning("Could not fetch data and no existing live games.") # Changed log prefix
                         self.current_game = None # Clear current game if fetch fails and no games were active

            # Handle game switching (outside test mode check)
            if not self.test_mode and len(self.live_games) > 1 and (current_time - self.last_game_switch) >= self.game_display_duration:
                self.current_game_index = (self.current_game_index + 1) % len(self.live_games)
                self.current_game = self.live_games[self.current_game_index]
                self.last_game_switch = current_time
                self.logger.info(f"Switched live view to: {self.current_game['away_abbr']}@{self.current_game['home_abbr']}") # Changed log prefix
                # Force display update via flag or direct call if needed, but usually let main loop handle