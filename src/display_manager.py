from rgbmatrix import RGBMatrix, RGBMatrixOptions
from PIL import Image, ImageDraw, ImageFont
import time
from typing import Dict, Any

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
            self.matrix = self._setup_matrix()
            self.font = ImageFont.truetype("DejaVuSans.ttf", 24)
            self.image = Image.new('RGB', (self.matrix.width, self.matrix.height))
            self.draw = ImageDraw.Draw(self.image)
            DisplayManager._initialized = True

    def _setup_matrix(self) -> RGBMatrix:
        """Setup the RGB matrix with the provided configuration."""
        options = RGBMatrixOptions()
        
        # Hardware specific settings
        options.hardware_mapping = 'adafruit-hat'  # Set for Adafruit Bonnet/HAT
        options.gpio_slowdown = 4  # Required for Pi 3
        options.rows = self.config.get('rows', 32)
        options.cols = self.config.get('cols', 64)
        options.chain_length = self.config.get('chain_length', 2)
        options.parallel = 1
        options.pwm_bits = 11
        options.brightness = self.config.get('brightness', 50)
        options.pwm_lsb_nanoseconds = 130
        options.led_rgb_sequence = "RGB"
        options.pixel_mapper_config = ""
        options.multiplexing = 0
        
        # Additional options for stability
        options.disable_hardware_pulsing = False
        options.show_refresh_rate = 0  # Turn off refresh rate display
        options.limit_refresh_rate_hz = 100
        
        return RGBMatrix(options=options)

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