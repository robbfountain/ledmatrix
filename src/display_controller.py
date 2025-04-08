import time
from typing import Dict, Any
from clock import Clock
from weather_manager import WeatherManager
from display_manager import DisplayManager
from config_manager import ConfigManager

class DisplayController:
    def __init__(self):
        self.config_manager = ConfigManager()
        self.config = self.config_manager.config
        self.display_manager = DisplayManager(self.config.get('display', {}))
        self.clock = Clock()
        self.weather = WeatherManager(self.config, self.display_manager)
        self.current_display = 'clock'
        self.last_switch = time.time()

    def run(self):
        """Run the display controller, switching between displays."""
        try:
            while True:
                current_time = time.time()
                rotation_interval = self.config['display'].get('rotation_interval', 10)

                # Switch display if interval has passed
                if current_time - self.last_switch > rotation_interval:
                    self.current_display = 'weather' if self.current_display == 'clock' else 'clock'
                    self.last_switch = current_time

                # Display current screen
                if self.current_display == 'clock':
                    self.clock.display_time()
                else:
                    self.weather.display_weather()

                # Small delay to prevent CPU overload
                time.sleep(0.1)

        except KeyboardInterrupt:
            print("\nDisplay stopped by user")
        finally:
            self.display_manager.cleanup()

if __name__ == "__main__":
    controller = DisplayController()
    controller.run() 