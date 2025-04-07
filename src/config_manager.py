import json
import os
from typing import Dict, Any

class ConfigManager:
    def __init__(self, config_path: str = "../config/config.json"):
        self.config_path = config_path
        self.config: Dict[str, Any] = {}
        self.load_config()

    def load_config(self) -> None:
        """Load configuration from JSON file."""
        try:
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
        except FileNotFoundError:
            print(f"Configuration file not found at {self.config_path}")
            raise
        except json.JSONDecodeError:
            print("Error parsing configuration file")
            raise

    def get_timezone(self) -> str:
        """Get the configured timezone."""
        return self.config.get('timezone', 'UTC')

    def get_display_config(self) -> Dict[str, Any]:
        """Get display configuration."""
        return self.config.get('display', {})

    def get_clock_config(self) -> Dict[str, Any]:
        """Get clock configuration."""
        return self.config.get('clock', {}) 