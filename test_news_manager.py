#!/usr/bin/env python3
import time
import sys
import os
from src.config_manager import ConfigManager
from src.display_manager import DisplayManager
from src.news_manager import NewsManager

def main():
    """Test the NewsManager class directly."""
    try:
        # Load configuration
        config_manager = ConfigManager()
        config = config_manager.load_config()
        
        # Initialize display manager
        display_manager = DisplayManager(config.get('display', {}))
        
        # Initialize news manager
        news_manager = NewsManager(config, display_manager)
        
        # Test the scrolling behavior
        # You can customize these parameters:
        # - test_message: The message to scroll
        # - scroll_speed: Pixels to move per frame (higher = faster)
        # - scroll_delay: Delay between scroll updates (lower = faster)
        # - max_iterations: Maximum number of iterations to run (None = run indefinitely)
        news_manager.test_scroll(
            test_message="This is a test of the NewsManager scrolling behavior. You can adjust the speed and delay to find the optimal settings.",
            scroll_speed=2,  # Adjust this to change scroll speed
            scroll_delay=0.05,  # Adjust this to change scroll smoothness
            max_iterations=3  # Set to None to run indefinitely
        )
            
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"Error during test: {e}")
    finally:
        print("Test completed")

if __name__ == "__main__":
    main() 