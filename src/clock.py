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
        self.timezone = self._get_timezone()

    def _get_timezone(self) -> str:
        """Get timezone based on location."""
        from timezonefinder import TimezoneFinder
        from geopy.geocoders import Nominatim

        try:
            # Get coordinates for the location
            geolocator = Nominatim(user_agent="led_matrix_clock")
            location_str = f"{self.location['city']}, {self.location['state']}, {self.location['country']}"
            location = geolocator.geocode(location_str)
            
            if location:
                # Find timezone from coordinates
                tf = TimezoneFinder()
                timezone_str = tf.timezone_at(lng=location.longitude, lat=location.latitude)
                return pytz.timezone(timezone_str)
        except Exception as e:
            print(f"Error finding timezone: {e}")
        
        # Fallback to UTC
        return pytz.UTC

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