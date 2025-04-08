from rgbmatrix import RGBMatrix, RGBMatrixOptions
from PIL import Image, ImageDraw, ImageFont
import time
from typing import Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DisplayManager:
    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(DisplayManager, cls).__new__(cls)
        return cls._instance

    def __init__(self, config: Dict[str, Any]):
        # Only initialize once
        if not DisplayManager._initialized:
            self.config = config
            logger.info("Initializing DisplayManager with config: %s", config)
            self._setup_matrix()  # This now sets self.matrix and self.font
            DisplayManager._initialized = True

    def _setup_matrix(self):
        """Initialize the RGB matrix with configuration settings."""
        options = RGBMatrixOptions()
        
        # Hardware configuration
        hardware_config = self.config.get('hardware', {})
        options.rows = hardware_config.get('rows', 32)
        options.cols = hardware_config.get('cols', 64)  # Each panel is 64 columns
        options.chain_length = hardware_config.get('chain_length', 2)
        options.parallel = hardware_config.get('parallel', 1)
        options.hardware_mapping = hardware_config.get('hardware_mapping', 'adafruit-hat-pwm')
        logger.info("Setting hardware mapping to: %s", options.hardware_mapping)
        options.brightness = hardware_config.get('brightness', 60)
        options.pwm_bits = hardware_config.get('pwm_bits', 8)
        options.pwm_lsb_nanoseconds = hardware_config.get('pwm_lsb_nanoseconds', 130)
        options.led_rgb_sequence = hardware_config.get('led_rgb_sequence', 'RGB')
        options.pixel_mapper_config = hardware_config.get('pixel_mapper_config', '')
        options.row_address_type = hardware_config.get('row_addr_type', 0)
        options.multiplexing = hardware_config.get('multiplexing', 0)
        options.disable_hardware_pulsing = hardware_config.get('disable_hardware_pulsing', True)
        options.show_refresh_rate = hardware_config.get('show_refresh_rate', True)
        options.limit_refresh_rate_hz = hardware_config.get('limit_refresh_rate_hz', 100)

        # Runtime configuration
        runtime_config = self.config.get('runtime', {})
        options.gpio_slowdown = runtime_config.get('gpio_slowdown', 2)
        logger.info("Setting GPIO slowdown to: %d", options.gpio_slowdown)

        # Initialize the matrix
        logger.info("Initializing RGB matrix with options...")
        self.matrix = RGBMatrix(options=options)
        logger.info("RGB matrix initialized successfully")
        logger.info(f"Matrix dimensions: {self.matrix.width}x{self.matrix.height}")
        
        # Create double buffer
        self.offscreen_canvas = self.matrix.CreateFrameCanvas()
        
        # Create image with full chain width
        self.image = Image.new('RGB', (self.matrix.width, self.matrix.height))
        self.draw = ImageDraw.Draw(self.image)
        
        # Initialize font
        try:
            self.font = ImageFont.truetype("DejaVuSans.ttf", 14)
            logger.info("Font initialized successfully")
        except Exception as e:
            logger.error(f"Failed to load font: {e}")
            raise
        
        # Draw a test pattern
        self._draw_test_pattern()

    def _draw_test_pattern(self):
        """Draw a test pattern to verify the display is working."""
        # Clear the display first
        self.clear()
        
        # Draw a red rectangle border
        self.draw.rectangle([0, 0, self.matrix.width-1, self.matrix.height-1], outline=(255, 0, 0))
        
        # Draw a diagonal line
        self.draw.line([0, 0, self.matrix.width-1, self.matrix.height-1], fill=(0, 255, 0))
        
        # Draw some text
        self.draw.text((10, 10), "TEST", font=self.font, fill=(0, 0, 255))
        
        # Update the display using double buffering
        self.update_display()
        
        # Wait a moment
        time.sleep(2)

    def update_display(self):
        """Update the display using double buffering."""
        # Copy the current image to the offscreen canvas
        self.offscreen_canvas.SetImage(self.image)
        # Swap the canvases
        self.offscreen_canvas = self.matrix.SwapOnVSync(self.offscreen_canvas)

    def clear(self):
        """Clear the display."""
        self.draw.rectangle((0, 0, self.matrix.width, self.matrix.height), fill=(0, 0, 0))
        self.update_display()

    def draw_text(self, text: str, x: int = None, y: int = None, color: tuple = (255, 255, 255), force_clear: bool = False):
        """Draw text on the display with automatic centering."""
        if force_clear:
            self.clear()
        else:
            # Just create a new blank image without updating display
            self.image = Image.new('RGB', (self.matrix.width, self.matrix.height))
            self.draw = ImageDraw.Draw(self.image)
        
        # Split text into lines if it contains newlines
        lines = text.split('\n')
        
        # Calculate total height of all lines
        line_heights = []
        line_widths = []
        total_height = 0
        padding = 2  # Add padding between lines
        edge_padding = 2  # Minimum padding from display edges
        
        for line in lines:
            bbox = self.draw.textbbox((0, 0), line, font=self.font)
            line_width = bbox[2] - bbox[0]
            line_height = bbox[3] - bbox[1]
            line_heights.append(line_height)
            line_widths.append(line_width)
            total_height += line_height
        
        # Add padding between lines
        if len(lines) > 1:
            total_height += padding * (len(lines) - 1)
        
        # Calculate starting Y position to center all lines vertically
        if y is None:
            y = max(edge_padding, (self.matrix.height - total_height) // 2)
        
        # Draw each line
        current_y = y
        for i, line in enumerate(lines):
            if x is None:
                # Center this line horizontally
                line_x = (self.matrix.width - line_widths[i]) // 2
            else:
                line_x = x
            
            # Ensure x coordinate stays within bounds
            line_x = max(edge_padding, min(line_x, self.matrix.width - line_widths[i] - edge_padding))
            
            # Ensure y coordinate stays within bounds
            current_y = max(edge_padding, min(current_y, self.matrix.height - line_heights[i] - edge_padding))
            
            logger.info(f"Drawing line '{line}' at position ({line_x}, {current_y})")
            self.draw.text((line_x, current_y), line, font=self.font, fill=color)
            
            # Calculate next line position
            current_y += line_heights[i] + padding
        
        # Update the display using double buffering
        self.update_display()

    def draw_scrolling_text(self, text: str, scroll_position: int, force_clear: bool = False) -> None:
        """Draw scrolling text on the display."""
        if force_clear:
            self.clear()
        else:
            # Just create a new blank image without updating display
            self.image = Image.new('RGB', (self.matrix.width * 2, self.matrix.height))  # Double width for scrolling
            self.draw = ImageDraw.Draw(self.image)
        
        # Calculate text dimensions
        bbox = self.draw.textbbox((0, 0), text, font=self.font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Draw text at current scroll position
        y = (self.matrix.height - text_height) // 2
        self.draw.text((self.matrix.width - scroll_position, y), text, font=self.font, fill=(255, 255, 255))
        
        # If text has scrolled past the left edge, draw it again at the right
        if scroll_position > text_width:
            self.draw.text((self.matrix.width * 2 - scroll_position, y), text, font=self.font, fill=(255, 255, 255))
        
        # Create a cropped version of the image that's the size of our display
        visible_portion = self.image.crop((0, 0, self.matrix.width, self.matrix.height))
        
        # Update the display with the visible portion
        self.matrix.SetImage(visible_portion)

    def cleanup(self):
        """Clean up resources."""
        self.matrix.Clear()
        # Reset the singleton state when cleaning up
        DisplayManager._instance = None
        DisplayManager._initialized = False 