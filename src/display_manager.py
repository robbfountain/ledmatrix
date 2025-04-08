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
        
        # Get hardware and runtime configs
        hw_config = self.config.get('hardware', {})
        runtime_config = self.config.get('runtime', {})
        
        # Hardware specific settings
        options.rows = hw_config.get('rows', 32)
        options.cols = hw_config.get('cols', 64)
        options.chain_length = hw_config.get('chain_length', 2)
        options.parallel = hw_config.get('parallel', 1)
        options.brightness = hw_config.get('brightness', 50)
        options.hardware_mapping = hw_config.get('hardware_mapping', 'adafruit-hat')
        options.pwm_bits = hw_config.get('pwm_bits', 11)
        options.pwm_lsb_nanoseconds = hw_config.get('pwm_lsb_nanoseconds', 130)
        options.led_rgb_sequence = hw_config.get('led_rgb_sequence', 'RGB')
        options.pixel_mapper_config = hw_config.get('pixel_mapper_config', '')
        options.multiplexing = hw_config.get('multiplexing', 0)
        options.row_address_type = hw_config.get('row_addr_type', 0)
        options.panel_type = hw_config.get('panel_type', '')
        
        # Display options
        options.show_refresh_rate = hw_config.get('show_refresh_rate', False)
        options.limit_refresh_rate_hz = hw_config.get('limit_refresh_rate_hz', 100)
        options.inverse_colors = hw_config.get('inverse_colors', False)
        options.disable_hardware_pulsing = hw_config.get('disable_hardware_pulsing', False)
        
        # Runtime options
        options.gpio_slowdown = runtime_config.get('gpio_slowdown', 4)
        
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