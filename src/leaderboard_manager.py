import time
import logging
import requests
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, timezone
import os
from PIL import Image, ImageDraw, ImageFont
import pytz
from display_manager import DisplayManager
from cache_manager import CacheManager
from config_manager import ConfigManager

# Import the API counter function from web interface
try:
    from web_interface_v2 import increment_api_counter
except ImportError:
    # Fallback if web interface is not available
    def increment_api_counter(kind: str, count: int = 1):
        pass

# Get logger
logger = logging.getLogger(__name__)

class LeaderboardManager:
    """Manager for displaying scrolling leaderboards for multiple sports leagues."""
    
    def __init__(self, config: Dict[str, Any], display_manager: DisplayManager):
        self.config = config
        self.display_manager = display_manager
        self.leaderboard_config = config.get('leaderboard', {})
        self.is_enabled = self.leaderboard_config.get('enabled', False)
        self.enabled_sports = self.leaderboard_config.get('enabled_sports', {})
        self.update_interval = self.leaderboard_config.get('update_interval', 3600)
        self.scroll_speed = self.leaderboard_config.get('scroll_speed', 2)
        self.scroll_delay = self.leaderboard_config.get('scroll_delay', 0.05)
        self.display_duration = self.leaderboard_config.get('display_duration', 30)
        self.loop = self.leaderboard_config.get('loop', True)
        self.request_timeout = self.leaderboard_config.get('request_timeout', 30)
        
        # Dynamic duration settings
        self.dynamic_duration_enabled = self.leaderboard_config.get('dynamic_duration', True)
        self.min_duration = self.leaderboard_config.get('min_duration', 30)
        self.max_duration = self.leaderboard_config.get('max_duration', 300)
        self.duration_buffer = self.leaderboard_config.get('duration_buffer', 0.1)
        self.dynamic_duration = 60  # Default duration in seconds
        self.total_scroll_width = 0  # Track total width for dynamic duration calculation
        
        # Initialize managers
        self.cache_manager = CacheManager()
        self.config_manager = ConfigManager()
        
        # State variables
        self.last_update = 0
        self.scroll_position = 0
        self.last_scroll_time = 0
        self.leaderboard_data = []
        self.current_sport_index = 0
        self.leaderboard_image = None  # This will hold the single, wide image
        self.last_display_time = 0
        
        # Font setup
        self.fonts = self._load_fonts()
        
        # League configurations with ESPN API endpoints
        self.league_configs = {
            'nfl': {
                'sport': 'football',
                'league': 'nfl',
                'logo_dir': 'assets/sports/nfl_logos',
                'league_logo': 'assets/sports/nfl_logos/nfl.png',
                'teams_url': 'https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams',
                'enabled': self.enabled_sports.get('nfl', {}).get('enabled', False),
                'top_teams': self.enabled_sports.get('nfl', {}).get('top_teams', 10)
            },
            'nba': {
                'sport': 'basketball',
                'league': 'nba',
                'logo_dir': 'assets/sports/nba_logos',
                'league_logo': 'assets/sports/nba_logos/nba.png',
                'teams_url': 'https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams',
                'enabled': self.enabled_sports.get('nba', {}).get('enabled', False),
                'top_teams': self.enabled_sports.get('nba', {}).get('top_teams', 10)
            },
            'mlb': {
                'sport': 'baseball',
                'league': 'mlb',
                'logo_dir': 'assets/sports/mlb_logos',
                'league_logo': 'assets/sports/mlb_logos/mlb.png',
                'teams_url': 'https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/teams',
                'enabled': self.enabled_sports.get('mlb', {}).get('enabled', False),
                'top_teams': self.enabled_sports.get('mlb', {}).get('top_teams', 10)
            },
            'ncaa_fb': {
                'sport': 'football',
                'league': 'college-football',
                'logo_dir': 'assets/sports/ncaa_fbs_logos',
                'league_logo': 'assets/sports/ncaa_fbs_logos/ncaa_fb.png',
                'teams_url': 'https://site.api.espn.com/apis/site/v2/sports/football/college-football/teams',
                'enabled': self.enabled_sports.get('ncaa_fb', {}).get('enabled', False),
                'top_teams': self.enabled_sports.get('ncaa_fb', {}).get('top_teams', 25)
            },
            'nhl': {
                'sport': 'hockey',
                'league': 'nhl',
                'logo_dir': 'assets/sports/nhl_logos',
                'league_logo': 'assets/sports/nhl_logos/nhl.png',
                'teams_url': 'https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/teams',
                'enabled': self.enabled_sports.get('nhl', {}).get('enabled', False),
                'top_teams': self.enabled_sports.get('nhl', {}).get('top_teams', 10)
            },
            'ncaam_basketball': {
                'sport': 'basketball',
                'league': 'mens-college-basketball',
                'logo_dir': 'assets/sports/ncaa_fbs_logos',
                'league_logo': 'assets/sports/ncaa_fbs_logos/ncaam.png',
                'teams_url': 'https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/teams',
                'enabled': self.enabled_sports.get('ncaam_basketball', {}).get('enabled', False),
                'top_teams': self.enabled_sports.get('ncaam_basketball', {}).get('top_teams', 25)
            }
        }
        
        logger.info(f"LeaderboardManager initialized with enabled sports: {[k for k, v in self.league_configs.items() if v['enabled']]}")

    def _load_fonts(self) -> Dict[str, ImageFont.FreeTypeFont]:
        """Load fonts for the leaderboard display."""
        try:
            return {
                'small': ImageFont.truetype("assets/fonts/PressStart2P-Regular.ttf", 6),
                'medium': ImageFont.truetype("assets/fonts/PressStart2P-Regular.ttf", 8),
                'large': ImageFont.truetype("assets/fonts/PressStart2P-Regular.ttf", 10)
            }
        except Exception as e:
            logger.error(f"Error loading fonts: {e}")
            return {
                'small': ImageFont.load_default(),
                'medium': ImageFont.load_default(),
                'large': ImageFont.load_default()
            }

    def _get_team_logo(self, team_abbr: str, logo_dir: str) -> Optional[Image.Image]:
        """Get team logo from the configured directory."""
        if not team_abbr or not logo_dir:
            logger.debug("Cannot get team logo with missing team_abbr or logo_dir")
            return None
        try:
            logo_path = os.path.join(logo_dir, f"{team_abbr}.png")
            logger.debug(f"Attempting to load logo from path: {logo_path}")
            if os.path.exists(logo_path):
                logo = Image.open(logo_path)
                logger.debug(f"Successfully loaded logo for {team_abbr} from {logo_path}")
                return logo
            else:
                logger.warning(f"Logo not found at path: {logo_path}")
                return None
        except Exception as e:
            logger.error(f"Error loading logo for {team_abbr} from {logo_dir}: {e}")
            return None

    def _get_league_logo(self, league_logo_path: str) -> Optional[Image.Image]:
        """Get league logo from the configured path."""
        if not league_logo_path:
            return None
        try:
            if os.path.exists(league_logo_path):
                logo = Image.open(league_logo_path)
                logger.debug(f"Successfully loaded league logo from {league_logo_path}")
                return logo
            else:
                logger.warning(f"League logo not found at path: {league_logo_path}")
                return None
        except Exception as e:
            logger.error(f"Error loading league logo from {league_logo_path}: {e}")
            return None

    def _fetch_standings(self, league_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fetch standings for a specific league from ESPN API."""
        try:
            # First, get all teams for the league
            teams_url = league_config['teams_url']
            response = requests.get(teams_url, timeout=self.request_timeout)
            response.raise_for_status()
            data = response.json()
            
            # Increment API counter for sports data
            increment_api_counter('sports', 1)
            
            standings = []
            sports = data.get('sports', [])
            
            if not sports:
                logger.warning(f"No sports data found for {league_config['league']}")
                return []
            
            leagues = sports[0].get('leagues', [])
            if not leagues:
                logger.warning(f"No leagues data found for {league_config['league']}")
                return []
            
            teams = leagues[0].get('teams', [])
            if not teams:
                logger.warning(f"No teams data found for {league_config['league']}")
                return []
            
            logger.info(f"Found {len(teams)} teams for {league_config['league']}")
            
            # For each team, fetch their individual record
            for team_data in teams:
                team = team_data.get('team', {})
                team_abbr = team.get('abbreviation')
                team_name = team.get('name', 'Unknown')
                
                if not team_abbr:
                    logger.warning(f"No abbreviation found for team {team_name}")
                    continue
                
                # Fetch individual team record
                team_record = self._fetch_team_record(team_abbr, league_config)
                
                if team_record:
                    standings.append({
                        'name': team_name,
                        'abbreviation': team_abbr,
                        'wins': team_record.get('wins', 0),
                        'losses': team_record.get('losses', 0),
                        'ties': team_record.get('ties', 0),
                        'win_percentage': team_record.get('win_percentage', 0)
                    })
            
            # Sort by win percentage (descending) and limit to top teams
            standings.sort(key=lambda x: x['win_percentage'], reverse=True)
            top_teams = standings[:league_config['top_teams']]
            
            logger.info(f"Fetched {len(top_teams)} teams for {league_config['league']}")
            return top_teams
            
        except Exception as e:
            logger.error(f"Error fetching standings for {league_config['league']}: {e}")
            return []

    def _fetch_team_record(self, team_abbr: str, league_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Fetch individual team record from ESPN API."""
        try:
            sport = league_config['sport']
            league = league_config['league']
            
            # Use a more specific endpoint for college sports
            if league == 'college-football':
                url = f"https://site.api.espn.com/apis/site/v2/sports/football/college-football/teams/{team_abbr}"
            else:
                url = f"https://site.api.espn.com/apis/site/v2/sports/{sport}/{league}/teams/{team_abbr}"

            response = requests.get(url, timeout=self.request_timeout)
            response.raise_for_status()
            data = response.json()
            
            # Increment API counter for sports data
            increment_api_counter('sports', 1)
            
            team_data = data.get('team', {})
            stats = team_data.get('stats', [])
            
            # Find wins and losses
            wins = 0
            losses = 0
            ties = 0
            
            for stat in stats:
                if stat.get('name') == 'wins':
                    wins = stat.get('value', 0)
                elif stat.get('name') == 'losses':
                    losses = stat.get('value', 0)
                elif stat.get('name') == 'ties':
                    ties = stat.get('value', 0)
            
            # Calculate win percentage
            total_games = wins + losses + ties
            win_percentage = wins / total_games if total_games > 0 else 0
            
            return {
                'wins': wins,
                'losses': losses,
                'ties': ties,
                'win_percentage': win_percentage
            }
            
        except Exception as e:
            logger.error(f"Error fetching record for {team_abbr} in league {league_config['league']}: {e}")
            return None

    def _fetch_all_standings(self) -> List[Dict[str, Any]]:
        """Fetch standings for all enabled leagues."""
        all_standings = []
        
        for league_key, league_config in self.league_configs.items():
            if not league_config['enabled']:
                continue
                
            logger.debug(f"Fetching standings for {league_key}")
            standings = self._fetch_standings(league_config)
            
            if standings:
                all_standings.append({
                    'league': league_key,
                    'league_config': league_config,
                    'teams': standings
                })
        
        return all_standings

    def _create_leaderboard_image(self) -> None:
        """Create the scrolling leaderboard image."""
        if not self.leaderboard_data:
            logger.warning("No leaderboard data available")
            return
        
        try:
            # Calculate total width needed
            total_width = 0
            team_height = 16  # Height for each team entry
            league_header_height = 20  # Height for league logo and name
            spacing = 10  # Spacing between leagues
            
            # Calculate width for each league section
            for league_data in self.leaderboard_data:
                league_config = league_data['league_config']
                teams = league_data['teams']
                
                # Width for league header (logo + name)
                league_width = 200  # Base width for league section
                
                # Width for team entries (number + logo + name + record)
                max_team_width = 0
                for i, team in enumerate(teams):
                    team_text = f"{i+1}. {team['abbreviation']} {team['wins']}-{team['losses']}"
                    if 'ties' in team:
                        team_text += f"-{team['ties']}"
                    
                    # Estimate text width (rough calculation)
                    text_width = len(team_text) * 6  # Approximate character width
                    team_width = 30 + text_width + 50  # Number + text + logo space
                    max_team_width = max(max_team_width, team_width)
                
                league_width = max(league_width, max_team_width)
                total_width += league_width + spacing
            
            # Create the main image
            height = self.display_manager.matrix.height
            self.leaderboard_image = Image.new('RGB', (total_width, height), (0, 0, 0))
            draw = ImageDraw.Draw(self.leaderboard_image)
            
            current_x = 0
            
            for league_data in self.leaderboard_data:
                league_key = league_data['league']
                league_config = league_data['league_config']
                teams = league_data['teams']
                
                # Draw league header
                league_logo = self._get_league_logo(league_config['league_logo'])
                if league_logo:
                    # Resize league logo to fit
                    logo_height = int(height * 0.4)
                    logo_width = int(logo_height * league_logo.width / league_logo.height)
                    league_logo = league_logo.resize((logo_width, logo_height), Image.Resampling.LANCZOS)
                    
                    # Paste league logo
                    logo_y = (height - logo_height) // 2
                    self.leaderboard_image.paste(league_logo, (current_x + 5, logo_y), league_logo if league_logo.mode == 'RGBA' else None)
                    current_x += logo_width + 10
                
                # Draw league name
                league_name = league_key.upper().replace('_', ' ')
                draw.text((current_x, 5), league_name, font=self.fonts['medium'], fill=(255, 255, 255))
                current_x += 150
                
                # Draw team standings
                team_y = league_header_height
                for i, team in enumerate(teams):
                    if team_y + team_height > height:
                        break
                    
                    # Draw team number
                    number_text = f"{i+1}."
                    draw.text((current_x, team_y), number_text, font=self.fonts['small'], fill=(255, 255, 0))
                    
                    # Draw team logo
                    team_logo = self._get_team_logo(team['abbreviation'], league_config['logo_dir'])
                    if team_logo:
                        # Resize team logo
                        logo_size = 12
                        team_logo = team_logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
                        
                        # Paste team logo
                        logo_x = current_x + 20
                        logo_y_pos = team_y + 2
                        self.leaderboard_image.paste(team_logo, (logo_x, logo_y_pos), team_logo if team_logo.mode == 'RGBA' else None)
                        
                        # Draw team name and record
                        team_text = f"{team['abbreviation']} {team['wins']}-{team['losses']}"
                        if 'ties' in team:
                            team_text += f"-{team['ties']}"
                        
                        draw.text((logo_x + logo_size + 5, team_y), team_text, font=self.fonts['small'], fill=(255, 255, 255))
                    else:
                        # Fallback if no logo
                        team_text = f"{team['abbreviation']} {team['wins']}-{team['losses']}"
                        if 'ties' in team:
                            team_text += f"-{team['ties']}"
                        
                        draw.text((current_x + 20, team_y), team_text, font=self.fonts['small'], fill=(255, 255, 255))
                    
                    team_y += team_height
                
                current_x += 200  # Width for team section
                current_x += spacing  # Add spacing between leagues
            
            # Calculate dynamic duration based on total width
            if self.dynamic_duration_enabled:
                scroll_time = (total_width / self.scroll_speed) * self.scroll_delay
                self.dynamic_duration = max(self.min_duration, min(self.max_duration, scroll_time + self.duration_buffer))
                logger.info(f"Calculated dynamic duration: {self.dynamic_duration:.1f}s for width {total_width}")
            
            self.total_scroll_width = total_width
            logger.info(f"Created leaderboard image with width {total_width}")
            
        except Exception as e:
            logger.error(f"Error creating leaderboard image: {e}")
            self.leaderboard_image = None

    def update(self) -> None:
        """Update leaderboard data."""
        current_time = time.time()
        
        if current_time - self.last_update < self.update_interval:
            return
        
        logger.info("Updating leaderboard data")
        
        try:
            self.leaderboard_data = self._fetch_all_standings()
            self.last_update = current_time
            
            if self.leaderboard_data:
                self._create_leaderboard_image()
            else:
                logger.warning("No leaderboard data fetched")
                
        except Exception as e:
            logger.error(f"Error updating leaderboard: {e}")

    def _display_fallback_message(self) -> None:
        """Display a fallback message when no data is available."""
        try:
            width = self.display_manager.matrix.width
            height = self.display_manager.matrix.height
            
            # Create a simple text image
            image = Image.new('RGB', (width, height), (0, 0, 0))
            draw = ImageDraw.Draw(image)
            
            text = "No Leaderboard Data"
            text_bbox = draw.textbbox((0, 0), text, font=self.fonts['medium'])
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            
            x = (width - text_width) // 2
            y = (height - text_height) // 2
            
            draw.text((x, y), text, font=self.fonts['medium'], fill=(255, 255, 255))
            
            self.display_manager.set_image(image)
            
        except Exception as e:
            logger.error(f"Error displaying fallback message: {e}")

    def display(self, force_clear: bool = False) -> None:
        """Display the leaderboard."""
        logger.debug("Entering leaderboard display method")
        logger.debug(f"Leaderboard enabled: {self.is_enabled}")
        logger.debug(f"Current scroll position: {self.scroll_position}")
        logger.debug(f"Leaderboard image width: {self.leaderboard_image.width if self.leaderboard_image else 'None'}")
        logger.debug(f"Dynamic duration: {self.dynamic_duration}s")
        
        if not self.is_enabled:
            logger.debug("Leaderboard is disabled, exiting display method.")
            return
        
        # Reset display start time when force_clear is True or when starting fresh
        if force_clear or not hasattr(self, '_display_start_time'):
            self._display_start_time = time.time()
            logger.debug(f"Reset/initialized display start time: {self._display_start_time}")
            # Also reset scroll position for clean start
            self.scroll_position = 0
        else:
            # Check if the display start time is too old (more than 2x the dynamic duration)
            current_time = time.time()
            elapsed_time = current_time - self._display_start_time
            if elapsed_time > (self.dynamic_duration * 2):
                logger.debug(f"Display start time is too old ({elapsed_time:.1f}s), resetting")
                self._display_start_time = current_time
                self.scroll_position = 0
        
        logger.debug(f"Number of leagues in data at start of display method: {len(self.leaderboard_data)}")
        if not self.leaderboard_data:
            logger.warning("Leaderboard has no data. Attempting to update...")
            self.update()
            if not self.leaderboard_data:
                logger.warning("Still no data after update. Displaying fallback message.")
                self._display_fallback_message()
                return
        
        if self.leaderboard_image is None:
            logger.warning("Leaderboard image is not available. Attempting to create it.")
            self._create_leaderboard_image()
            if self.leaderboard_image is None:
                logger.error("Failed to create leaderboard image.")
                self._display_fallback_message()
                return

        try:
            current_time = time.time()
            
            # Check if we should be scrolling
            should_scroll = current_time - self.last_scroll_time >= self.scroll_delay
            
            # Signal scrolling state to display manager
            if should_scroll:
                self.display_manager.set_scrolling_state(True)
            else:
                # If we're not scrolling, check if we should process deferred updates
                self.display_manager.process_deferred_updates()
            
            # Scroll the image
            if should_scroll:
                self.scroll_position += self.scroll_speed
                self.last_scroll_time = current_time
            
            # Calculate crop region
            width = self.display_manager.matrix.width
            height = self.display_manager.matrix.height
            
            # Handle looping based on configuration
            if self.loop:
                # Reset position when we've scrolled past the end for a continuous loop
                if self.scroll_position >= self.leaderboard_image.width:
                    logger.debug(f"Leaderboard loop reset: scroll_position {self.scroll_position} >= image width {self.leaderboard_image.width}")
                    self.scroll_position = 0
            else:
                # Stop scrolling when we reach the end
                if self.scroll_position >= self.leaderboard_image.width - width:
                    logger.debug(f"Leaderboard reached end: scroll_position {self.scroll_position} >= {self.leaderboard_image.width - width}")
                    self.scroll_position = self.leaderboard_image.width - width
                    # Signal that scrolling has stopped
                    self.display_manager.set_scrolling_state(False)
            
            # Check if we're at a natural break point for mode switching
            elapsed_time = current_time - self._display_start_time
            remaining_time = self.dynamic_duration - elapsed_time
            
            # If we have less than 2 seconds remaining and we're not at a clean break point,
            # try to complete the current league display
            if remaining_time < 2.0 and self.scroll_position > 0:
                # Calculate how much time we need to complete the current scroll position
                frames_to_complete = (self.leaderboard_image.width - self.scroll_position) / self.scroll_speed
                time_to_complete = frames_to_complete * self.scroll_delay
                
                if time_to_complete <= remaining_time:
                    # We have enough time to complete the scroll, continue normally
                    pass
                else:
                    # Not enough time, reset to beginning for clean transition
                    logger.debug(f"Display ending soon, resetting scroll position for clean transition")
                    self.scroll_position = 0
            
            # Create the visible part of the image by cropping from the leaderboard_image
            visible_image = self.leaderboard_image.crop((
                self.scroll_position,
                0,
                self.scroll_position + width,
                height
            ))
            
            # Display the visible portion
            self.display_manager.set_image(visible_image)
            
        except Exception as e:
            logger.error(f"Error in leaderboard display: {e}")
            self._display_fallback_message()
