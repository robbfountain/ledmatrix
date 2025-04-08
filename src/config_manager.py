import json
import os
from typing import Dict, Any

class ConfigManager:
    def __init__(self, config_path: str = None, secrets_path: str = None):
        # Get the project root directory
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Set default paths relative to project root
        self.config_path = config_path or os.path.join(project_root, "config", "config.json")
        self.secrets_path = secrets_path or os.path.join(project_root, "config", "config_secrets.json")
        
        self.config: Dict[str, Any] = {}
        self.load_config()

    def load_config(self) -> None:
        """Load configuration from JSON files."""
        try:
            # Load main config
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)

            # Load and merge secrets if they exist
            if os.path.exists(self.secrets_path):
                with open(self.secrets_path, 'r') as f:
                    secrets = json.load(f)
                    # Deep merge secrets into config
                    self._deep_merge(self.config, secrets)
            
        except FileNotFoundError as e:
            if str(e).find('config_secrets.json') == -1:  # Only raise if main config is missing
                print(f"Configuration file not found at {self.config_path}")
                raise
        except json.JSONDecodeError:
            print("Error parsing configuration file")
            raise

    def _deep_merge(self, target: Dict, source: Dict) -> None:
        """Deep merge source dict into target dict."""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_merge(target[key], value)
            else:
                target[key] = value

    def get_timezone(self) -> str:
        """Get the configured timezone."""
        return self.config.get('timezone', 'UTC')

    def get_display_config(self) -> Dict[str, Any]:
        """Get display configuration."""
        return self.config.get('display', {})

    def get_clock_config(self) -> Dict[str, Any]:
        """Get clock configuration."""
        return self.config.get('clock', {}) 