import time
from datetime import datetime
import pytz
from typing import Dict, Any
from config_manager import ConfigManager
from display_manager import DisplayManager

class Clock:
    def __init__(self):
        self.config_manager = ConfigManager()
        self.config = self.config_manager.config
        self.display_manager = DisplayManager(self.config.get('display', {}))
        self.location = self.config.get('location', {})
        self.clock_config = self.config.get('clock', {})
        # Use configured timezone if available, otherwise try to determine it
        self.timezone = self._get_timezone()

    def _get_timezone(self) -> pytz.timezone:
        """Get timezone based on location or config."""
        # First try to use timezone from config if it exists
        if 'timezone' in self.config:
            try:
                return pytz.timezone(self.config['timezone'])
            except pytz.exceptions.UnknownTimeZoneError:
                print(f"Warning: Invalid timezone in config: {self.config['timezone']}")

        # If no timezone in config or it's invalid, try to determine from location
        try:
            from timezonefinder import TimezoneFinder
            from geopy.geocoders import Nominatim
            from geopy.exc import GeocoderTimedOut

            # Get coordinates for the location
            geolocator = Nominatim(user_agent="led_matrix_clock")
            location_str = f"{self.location['city']}, {self.location['state']}, {self.location['country']}"
            
            try:
                location = geolocator.geocode(location_str, timeout=5)  # 5 second timeout
                if location:
                    # Find timezone from coordinates
                    tf = TimezoneFinder()
                    timezone_str = tf.timezone_at(lng=location.longitude, lat=location.latitude)
                    if timezone_str:
                        return pytz.timezone(timezone_str)
            except GeocoderTimedOut:
                print("Warning: Timeout while looking up location coordinates")
            except Exception as e:
                print(f"Warning: Error finding timezone from location: {e}")
        
        except Exception as e:
            print(f"Warning: Error importing geolocation libraries: {e}")
        
        # Fallback to US/Central for Dallas
        print("Using fallback timezone: US/Central")
        return pytz.timezone('US/Central')

    def get_current_time(self) -> str:
        """Get the current time in the configured timezone."""
        current_time = datetime.now(self.timezone)
        return current_time.strftime(self.clock_config.get('format', '%H:%M:%S'))

    def display_time(self) -> None:
        """Display the current time."""
        current_time = self.get_current_time()
        
        # Center the text on the display
        text_width = self.display_manager.font.getlength(current_time)
        x = (self.display_manager.matrix.width - text_width) // 2
        y = (self.display_manager.matrix.height - 24) // 2
        
        self.display_manager.clear()
        self.display_manager.draw_text(current_time, x, y)

if __name__ == "__main__":
    clock = Clock()
    try:
        while True:
            clock.display_time()
            time.sleep(clock.clock_config.get('update_interval', 1))
    except KeyboardInterrupt:
        print("\nClock stopped by user")
    finally:
        clock.display_manager.cleanup() 