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
        options.cols = hardware_config.get('cols', 64)
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
        options.limit_refresh_rate_hz = hardware_config.get('limit_refresh_rate_hz', 100)

        # Runtime configuration
        runtime_config = self.config.get('runtime', {})
        options.gpio_slowdown = runtime_config.get('gpio_slowdown', 3)
        logger.info("Setting GPIO slowdown to: %d", options.gpio_slowdown)

        # Initialize the matrix
        logger.info("Initializing RGB matrix with options...")
        self.matrix = RGBMatrix(options=options)
        logger.info("RGB matrix initialized successfully")
        
        # Apply rotation if specified
        self.rotation = hardware_config.get('rotation', 0)
        logger.info("Display rotation set to: %d degrees", self.rotation)

    def _draw_text(self, text, x, y, font, color=(255, 255, 255)):
        """Draw text on the canvas with optional rotation."""
        if self.rotation == 180:
            # For 180 degree rotation, flip coordinates
            width = self.matrix.width
            height = self.matrix.height
            # Get text size for proper positioning
            text_width, text_height = font.getsize(text)
            # Adjust coordinates for rotation
            x = width - x - text_width
            y = height - y - text_height
            
        self.draw.text((x, y), text, font=font, fill=color)
        self.matrix.SetImage(self.image)

    def clear(self):
        """Clear the display."""
        self.draw.rectangle((0, 0, self.matrix.width, self.matrix.height), fill=(0, 0, 0))
        self.matrix.SetImage(self.image)

    def draw_text(self, text: str, x: int, y: int, color: tuple = (255, 255, 255)):
        """Draw text on the display."""
        self.clear()
        self.draw.text((x, y), text, font=self.font, fill=color)
        self.matrix.SetImage(self.image)

    def cleanup(self):
        """Clean up resources."""
        self.matrix.Clear()
        # Reset the singleton state when cleaning up
        DisplayManager._instance = None
        DisplayManager._initialized = False 