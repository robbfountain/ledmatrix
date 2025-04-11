#!/usr/bin/env python3
import time
import sys
import os
from src.config_manager import ConfigManager
from src.display_manager import DisplayManager
from src.news_manager import NewsManager

def main():
    """Test the scrolling direction of the news ticker."""
    try:
        # Load configuration
        config_manager = ConfigManager()
        config = config_manager.load_config()
        
        # Initialize display manager
        display_manager = DisplayManager(config.get('display', {}))
        
        # Initialize news manager
        news_manager = NewsManager(config, display_manager)
        
        print("Starting scroll direction test...")
        print("This test will display a simple text message scrolling from left to right")
        print("Press Ctrl+C to exit")
        
        # Create a simple test message
        test_message = "TEST MESSAGE - This is a test of scrolling direction"
        
        # Create a text image for the test message
        text_image = news_manager._create_text_image(test_message)
        text_width = text_image.width
        
        # Clear the display
        display_manager.clear()
        display_manager.update_display()
        
        # Test scrolling from left to right
        scroll_position = 0
        while True:
            # Create a new frame
            frame_image = display_manager.create_blank_image()
            
            # Calculate the visible portion
            visible_width = min(display_manager.matrix.width, text_width)
            src_x = scroll_position
            src_width = min(visible_width, text_width - src_x)
            
            # Copy the visible portion
            if src_width > 0:
                src_region = text_image.crop((src_x, 0, src_x + src_width, display_manager.matrix.height))
                frame_image.paste(src_region, (0, 0))
            
            # Handle wrapping
            if src_x + src_width >= text_width:
                remaining_width = display_manager.matrix.width - src_width
                if remaining_width > 0:
                    wrap_src_width = min(remaining_width, text_width)
                    wrap_region = text_image.crop((0, 0, wrap_src_width, display_manager.matrix.height))
                    frame_image.paste(wrap_region, (src_width, 0))
            
            # Update the display
            display_manager.image = frame_image
            display_manager.draw = display_manager.create_draw_object()
            display_manager.update_display()
            
            # Update scroll position
            scroll_position += 1
            
            # Reset when we've scrolled past the end
            if scroll_position > text_width + display_manager.matrix.width:
                scroll_position = 0
                time.sleep(1)  # Pause briefly before restarting
            
            time.sleep(0.05)  # Control scroll speed
            
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"Error during test: {e}")
    finally:
        # Clean up
        display_manager.clear()
        display_manager.update_display()
        print("Test completed")

if __name__ == "__main__":
    main() 