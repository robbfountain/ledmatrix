import time
from datetime import datetime
import pytz
from config_manager import ConfigManager
from display_manager import DisplayManager

class Clock:
    def __init__(self):
        self.config_manager = ConfigManager()
        self.display_manager = DisplayManager(self.config_manager.get_display_config())
        self.timezone = pytz.timezone(self.config_manager.get_timezone())
        self.clock_config = self.config_manager.get_clock_config()

    def get_current_time(self) -> str:
        """Get the current time in the configured timezone."""
        current_time = datetime.now(self.timezone)
        return current_time.strftime(self.clock_config.get('format', '%H:%M:%S'))

    def run(self):
        """Run the clock display."""
        try:
            while True:
                current_time = self.get_current_time()
                # Center the text on the display
                text_width = self.display_manager.font.getlength(current_time)
                x = (self.display_manager.matrix.width - text_width) // 2
                y = (self.display_manager.matrix.height - 24) // 2
                
                self.display_manager.draw_text(current_time, x, y)
                time.sleep(self.clock_config.get('update_interval', 1))
        except KeyboardInterrupt:
            print("Clock stopped by user")
        finally:
            self.display_manager.cleanup()

if __name__ == "__main__":
    clock = Clock()
    clock.run() 