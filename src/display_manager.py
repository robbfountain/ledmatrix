from rgbmatrix import RGBMatrix, RGBMatrixOptions
from PIL import Image, ImageDraw, ImageFont
import time
from typing import Dict, Any

class DisplayManager:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.matrix = self._setup_matrix()
        self.font = ImageFont.truetype("DejaVuSans.ttf", 24)
        self.image = Image.new('RGB', (self.matrix.width, self.matrix.height))
        self.draw = ImageDraw.Draw(self.image)

    def _setup_matrix(self) -> RGBMatrix:
        """Setup the RGB matrix with the provided configuration."""
        options = RGBMatrixOptions()
        options.rows = self.config.get('rows', 32)
        options.cols = self.config.get('cols', 64)
        options.chain_length = self.config.get('chain_length', 2)
        options.hardware_mapping = 'adafruit-hat'
        options.gpio_slowdown = 4
        options.brightness = self.config.get('brightness', 50)
        
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