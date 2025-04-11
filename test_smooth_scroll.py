#!/usr/bin/env python3
import time
import sys
import os
from src.config_manager import ConfigManager
from src.display_manager import DisplayManager
from src.news_manager import NewsManager

def main():
    """Test the smooth scrolling performance of the news ticker."""
    try:
        # Load configuration
        config_manager = ConfigManager()
        config = config_manager.config
        
        # Initialize display manager
        display_manager = DisplayManager(config.get('display', {}))
        
        # Initialize news manager
        news_manager = NewsManager(config, display_manager)
        
        print("Smooth scrolling test started. Press Ctrl+C to exit.")
        print("Displaying news headlines with optimized scrolling...")
        
        # Clear the display first
        display_manager.clear()
        display_manager.update_display()
        
        # Display news headlines for a longer time to test scrolling performance
        start_time = time.time()
        frame_count = 0
        
        while time.time() - start_time < 60:  # Run for 1 minute
            news_manager.display_news()
            frame_count += 1
            
            # Print FPS every 5 seconds
            elapsed = time.time() - start_time
            if int(elapsed) % 5 == 0 and int(elapsed) > 0:
                fps = frame_count / elapsed
                print(f"FPS: {fps:.2f}")
                frame_count = 0
                start_time = time.time()
            
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