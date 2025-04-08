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
            self._setup_matrix()  # This now sets self.matrix
            self.font = ImageFont.truetype("DejaVuSans.ttf", 24)
            self.image = Image.new('RGB', (self.matrix.width, self.matrix.height))
            self.draw = ImageDraw.Draw(self.image)
            DisplayManager._initialized = True

    def _setup_matrix(self):
        """Initialize the RGB matrix with configuration settings."""
        options = RGBMatrixOptions()
        
        # Hardware configuration
        hardware_config = self.config.get('hardware', {})
        options.rows = hardware_config.get('rows', 32)
        options.cols = hardware_config.get('cols', 32)  # Each panel is 32 columns
        options.chain_length = hardware_config.get('chain_length', 2)
        options.parallel = hardware_config.get('parallel', 1)
        options.hardware_mapping = hardware_config.get('hardware_mapping', 'adafruit-hat-pwm')
        logger.info("Setting hardware mapping to: %s", options.hardware_mapping)
        options.brightness = hardware_config.get('brightness', 50)
        options.pwm_bits = hardware_config.get('pwm_bits', 11)
        options.pwm_lsb_nanoseconds = hardware_config.get('pwm_lsb_nanoseconds', 130)
        options.led_rgb_sequence = hardware_config.get('led_rgb_sequence', 'RGB')
        options.pixel_mapper_config = hardware_config.get('pixel_mapper_config', '')
        options.row_address_type = hardware_config.get('row_addr_type', 0)
        options.multiplexing = hardware_config.get('multiplexing', 0)
        options.disable_hardware_pulsing = hardware_config.get('disable_hardware_pulsing', True)
        options.show_refresh_rate = hardware_config.get('show_refresh_rate', False)
        options.limit_refresh_rate_hz = hardware_config.get('limit_refresh_rate_hz', 120)

        # Runtime configuration
        runtime_config = self.config.get('runtime', {})
        options.gpio_slowdown = runtime_config.get('gpio_slowdown', 4)
        logger.info("Setting GPIO slowdown to: %d", options.gpio_slowdown)

        # Initialize the matrix
        logger.info("Initializing RGB matrix with options...")
        self.matrix = RGBMatrix(options=options)
        logger.info("RGB matrix initialized successfully")
        logger.info(f"Matrix dimensions: {self.matrix.width}x{self.matrix.height}")
        
        # Create image with full chain width
        self.image = Image.new('RGB', (self.matrix.width, self.matrix.height))
        self.draw = ImageDraw.Draw(self.image)

    def _draw_text(self, text, x, y, font, color=(255, 255, 255)):
        """Draw text on the canvas."""
        self.draw.text((x, y), text, font=font, fill=color)
        self.matrix.SetImage(self.image)

    def clear(self):
        """Clear the display."""
        self.draw.rectangle((0, 0, self.matrix.width, self.matrix.height), fill=(0, 0, 0))
        self.matrix.SetImage(self.image)

    def draw_text(self, text: str, x: int = None, y: int = None, color: tuple = (255, 255, 255)):
        """Draw text on the display with automatic centering."""
        self.clear()
        
        # Get text size
        text_bbox = self.draw.textbbox((0, 0), text, font=self.font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        # Calculate center position if not specified
        if x is None:
            x = (self.matrix.width - text_width) // 2
        if y is None:
            y = (self.matrix.height - text_height) // 2
            
        logger.info(f"Drawing text '{text}' at position ({x}, {y})")
        self.draw.text((x, y), text, font=self.font, fill=color)
        self.matrix.SetImage(self.image)

    def cleanup(self):
        """Clean up resources."""
        self.matrix.Clear()
        # Reset the singleton state when cleaning up
        DisplayManager._instance = None
        DisplayManager._initialized = False 