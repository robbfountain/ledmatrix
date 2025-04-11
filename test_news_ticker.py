#!/usr/bin/env python3
import time
import sys
import os
from src.config_manager import ConfigManager
from src.display_manager import DisplayManager
from src.news_manager import NewsManager

def main():
    """Test the news ticker functionality."""
    try:
        # Load configuration
        config_manager = ConfigManager()
        config = config_manager.config
        
        # Initialize display manager
        display_manager = DisplayManager(config.get('display', {}))
        
        # Initialize news manager
        news_manager = NewsManager(config, display_manager)
        
        print("News ticker test started. Press Ctrl+C to exit.")
        print("Displaying news headlines for configured stock symbols...")
        
        # Display news headlines for a limited time (30 seconds)
        start_time = time.time()
        while time.time() - start_time < 30:
            news_manager.display_news()
            
        print("Test completed successfully.")
        
    except KeyboardInterrupt:
        print("\nTest interrupted by user.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Clean up
        if 'display_manager' in locals():
            display_manager.clear()
            display_manager.update_display()
            display_manager.cleanup()

if __name__ == "__main__":
    main() 