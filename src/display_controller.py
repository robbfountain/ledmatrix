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
        logger.info("DisplayController initialized with display_manager: %s", id(self.display_manager))

    def run(self):
        """Run the display controller, switching between displays."""
        try:
            while True:
                current_time = time.time()
                rotation_interval = self.config['display'].get('rotation_interval', 10)

                # Switch display if interval has passed
                if current_time - self.last_switch > rotation_interval:
                    logger.info("Switching display from %s to %s", 
                              self.current_display,
                              'weather' if self.current_display == 'clock' else 'clock')
                    self.current_display = 'weather' if self.current_display == 'clock' else 'clock'
                    self.last_switch = current_time

                # Display current screen
                if self.current_display == 'clock':
                    logger.debug("Updating clock display")
                    self.clock.display_time()
                else:
                    logger.debug("Updating weather display")
                    self.weather.display_weather()

                # Small delay to prevent CPU overload
                time.sleep(0.1)

        except KeyboardInterrupt:
            print("\nDisplay stopped by user")
        finally:
            self.display_manager.cleanup()

def main():
    controller = DisplayController()
    controller.run()

if __name__ == "__main__":
    main() 