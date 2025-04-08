import time
import logging
from typing import Dict, Any
from src.clock import Clock
from src.weather_manager import WeatherManager
from src.display_manager import DisplayManager
from src.config_manager import ConfigManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DisplayController:
    def __init__(self):
        self.config_manager = ConfigManager()
        self.config = self.config_manager.config
        self.display_manager = DisplayManager(self.config.get('display', {}))
        self.clock = Clock(display_manager=self.display_manager)
        self.weather = WeatherManager(self.config, self.display_manager)
        self.current_display = 'clock'
        self.last_switch = time.time()
        self.scroll_position = 0
        self.scroll_speed = 1  # Reduced scroll speed
        self.last_scroll = time.time()
        self.scroll_interval = 0.2  # Increased scroll interval for smoother scrolling
        self.force_clear = True  # Start with a clear screen
        self.update_interval = 0.1  # Consistent update interval
        logger.info("DisplayController initialized with display_manager: %s", id(self.display_manager))

    def run(self):
        """Run the display controller, switching between displays."""
        try:
            while True:
                current_time = time.time()
                
                # Check if we need to switch display mode
                if current_time - self.last_switch > self.config['display'].get('rotation_interval', 30):
                    # Cycle through: clock -> current weather -> hourly forecast -> daily forecast
                    if self.current_display == 'clock':
                        self.current_display = 'weather'
                    elif self.current_display == 'weather':
                        self.current_display = 'hourly'
                        self.scroll_position = 0  # Reset scroll position when switching to hourly
                    elif self.current_display == 'hourly':
                        self.current_display = 'daily'
                    else:  # daily
                        self.current_display = 'clock'
                    
                    logger.info("Switching display to: %s", self.current_display)
                    self.last_switch = current_time
                    self.force_clear = True  # Clear screen on mode switch
                    self.display_manager.clear()  # Ensure clean transition

                # Update scroll position for hourly forecast if needed
                if self.current_display == 'hourly' and current_time - self.last_scroll > self.scroll_interval:
                    self.scroll_position += self.scroll_speed
                    self.last_scroll = current_time
                    
                    # Reset scroll position if we've gone through all forecasts
                    if self.scroll_position > self.display_manager.matrix.width * 3:
                        self.scroll_position = 0
                        self.force_clear = True
                        self.display_manager.clear()

                # Display current screen
                try:
                    if self.current_display == 'clock':
                        self.clock.display_time(force_clear=self.force_clear)
                    elif self.current_display == 'weather':
                        self.weather.display_weather(force_clear=self.force_clear)
                    elif self.current_display == 'hourly':
                        self.weather.display_hourly_forecast(self.scroll_position, force_clear=self.force_clear)
                    else:  # daily
                        self.weather.display_daily_forecast(force_clear=self.force_clear)
                except Exception as e:
                    logger.error(f"Error updating display: {e}")
                    time.sleep(1)  # Wait a bit before retrying
                    continue

                # Reset force clear flag after use
                self.force_clear = False

                # Consistent sleep time for all modes
                time.sleep(self.update_interval)

        except KeyboardInterrupt:
            print("\nDisplay stopped by user")
        finally:
            self.display_manager.cleanup()

def main():
    controller = DisplayController()
    controller.run()

if __name__ == "__main__":
    main() 