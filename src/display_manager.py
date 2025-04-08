from rgbmatrix import RGBMatrix, RGBMatrixOptions
from PIL import Image, ImageDraw, ImageFont
import time
from typing import Dict, Any, List
import logging
import math
from .weather_icons import WeatherIcons

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
            self._setup_matrix()
            self._load_fonts()
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

    def _load_fonts(self):
        """Load fonts for different text sizes."""
        try:
            # Load regular font (size 14 for better readability)
            self.font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
            # Load small font (size 8 for compact display)
            self.small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 8)
            logger.info("Fonts loaded successfully")
        except Exception as e:
            logger.error(f"Error loading fonts: {e}")
            # Fallback to default bitmap font if TTF loading fails
            self.font = ImageFont.load_default()
            self.small_font = self.font

    def draw_text(self, text: str, x: int = None, y: int = None, color: tuple = (255, 255, 255), 
                 force_clear: bool = False, small_font: bool = False):
        """Draw text on the display with automatic centering."""
        if force_clear:
            self.clear()
        else:
            # Just create a new blank image without updating display
            self.image = Image.new('RGB', (self.matrix.width, self.matrix.height))
            self.draw = ImageDraw.Draw(self.image)
        
        # Select font based on small_font parameter
        font = self.small_font if small_font else self.font
        
        # Split text into lines if it contains newlines
        lines = text.split('\n')
        
        # Calculate total height of all lines
        line_heights = []
        line_widths = []
        total_height = 0
        padding = 2  # Add padding between lines
        edge_padding = 2  # Minimum padding from display edges
        
        for line in lines:
            bbox = self.draw.textbbox((0, 0), line, font=font)
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
            
            # Draw the text (removed logging to reduce spam)
            self.draw.text((line_x, current_y), line, font=font, fill=color)
            
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

    def draw_sun(self, x: int, y: int, size: int = 16):
        """Draw a sun icon using yellow circles and lines."""
        center = (x + size//2, y + size//2)
        radius = size//3
        
        # Draw the center circle
        self.draw.ellipse([center[0]-radius, center[1]-radius, 
                          center[0]+radius, center[1]+radius], 
                         fill=(255, 255, 0))  # Yellow
        
        # Draw the rays
        ray_length = size//4
        for angle in range(0, 360, 45):
            rad = math.radians(angle)
            start_x = center[0] + (radius * math.cos(rad))
            start_y = center[1] + (radius * math.sin(rad))
            end_x = center[0] + ((radius + ray_length) * math.cos(rad))
            end_y = center[1] + ((radius + ray_length) * math.sin(rad))
            self.draw.line([start_x, start_y, end_x, end_y], fill=(255, 255, 0), width=2)

    def draw_cloud(self, x: int, y: int, size: int = 16, color=(200, 200, 200)):
        """Draw a cloud icon."""
        # Draw multiple circles to form a cloud shape
        self.draw.ellipse([x+size//4, y+size//3, x+size//4+size//2, y+size//3+size//2], fill=color)
        self.draw.ellipse([x+size//2, y+size//3, x+size//2+size//2, y+size//3+size//2], fill=color)
        self.draw.ellipse([x+size//3, y+size//6, x+size//3+size//2, y+size//6+size//2], fill=color)

    def draw_rain(self, x: int, y: int, size: int = 16):
        """Draw rain icon with cloud and droplets."""
        # Draw cloud
        self.draw_cloud(x, y, size)
        
        # Draw rain drops
        drop_color = (0, 0, 255)  # Blue
        drop_size = size//6
        for i in range(3):
            drop_x = x + size//4 + (i * size//3)
            drop_y = y + size//2
            self.draw.line([drop_x, drop_y, drop_x, drop_y+drop_size], 
                          fill=drop_color, width=2)

    def draw_snow(self, x: int, y: int, size: int = 16):
        """Draw snow icon with cloud and snowflakes."""
        # Draw cloud
        self.draw_cloud(x, y, size)
        
        # Draw snowflakes
        snow_color = (200, 200, 255)  # Light blue
        for i in range(3):
            center_x = x + size//4 + (i * size//3)
            center_y = y + size//2 + size//4
            # Draw a small star shape
            for angle in range(0, 360, 60):
                rad = math.radians(angle)
                end_x = center_x + (size//8 * math.cos(rad))
                end_y = center_y + (size//8 * math.sin(rad))
                self.draw.line([center_x, center_y, end_x, end_y], 
                             fill=snow_color, width=1)

    # Weather icon color constants
    WEATHER_COLORS = {
        'sun': (255, 200, 0),    # Bright yellow
        'cloud': (200, 200, 200), # Light gray
        'rain': (0, 100, 255),    # Light blue
        'snow': (220, 220, 255),  # Ice blue
        'storm': (255, 255, 0)    # Lightning yellow
    }

    def _draw_sun(self, x: int, y: int, size: int) -> None:
        """Draw a sun icon with rays."""
        center_x, center_y = x + size//2, y + size//2
        radius = size//4
        ray_length = size//3
        
        # Draw the main sun circle
        self.draw.ellipse([center_x - radius, center_y - radius, 
                          center_x + radius, center_y + radius], 
                         fill=self.WEATHER_COLORS['sun'])
        
        # Draw sun rays
        for angle in range(0, 360, 45):
            rad = math.radians(angle)
            start_x = center_x + int((radius + 2) * math.cos(rad))
            start_y = center_y + int((radius + 2) * math.sin(rad))
            end_x = center_x + int((radius + ray_length) * math.cos(rad))
            end_y = center_y + int((radius + ray_length) * math.sin(rad))
            self.draw.line([start_x, start_y, end_x, end_y], 
                         fill=self.WEATHER_COLORS['sun'], width=2)

    def _draw_cloud(self, x: int, y: int, size: int) -> None:
        """Draw a cloud using multiple circles."""
        cloud_color = self.WEATHER_COLORS['cloud']
        base_y = y + size//2
        
        # Draw main cloud body (3 overlapping circles)
        circle_radius = size//4
        positions = [
            (x + size//3, base_y),           # Left circle
            (x + size//2, base_y - size//6), # Top circle
            (x + 2*size//3, base_y)          # Right circle
        ]
        
        for cx, cy in positions:
            self.draw.ellipse([cx - circle_radius, cy - circle_radius,
                             cx + circle_radius, cy + circle_radius],
                            fill=cloud_color)

    def _draw_rain(self, x: int, y: int, size: int) -> None:
        """Draw rain drops falling from a cloud."""
        self._draw_cloud(x, y, size)
        rain_color = self.WEATHER_COLORS['rain']
        
        # Draw rain drops at an angle
        drop_size = size//8
        drops = [
            (x + size//4, y + 2*size//3),
            (x + size//2, y + 3*size//4),
            (x + 3*size//4, y + 2*size//3)
        ]
        
        for dx, dy in drops:
            # Draw angled rain drops
            self.draw.line([dx, dy, dx - drop_size//2, dy + drop_size],
                         fill=rain_color, width=2)

    def _draw_snow(self, x: int, y: int, size: int) -> None:
        """Draw snowflakes falling from a cloud."""
        self._draw_cloud(x, y, size)
        snow_color = self.WEATHER_COLORS['snow']
        
        # Draw snowflakes
        flake_size = size//6
        flakes = [
            (x + size//4, y + 2*size//3),
            (x + size//2, y + 3*size//4),
            (x + 3*size//4, y + 2*size//3)
        ]
        
        for fx, fy in flakes:
            # Draw a snowflake (six-pointed star)
            for angle in range(0, 360, 60):
                rad = math.radians(angle)
                end_x = fx + int(flake_size * math.cos(rad))
                end_y = fy + int(flake_size * math.sin(rad))
                self.draw.line([fx, fy, end_x, end_y],
                             fill=snow_color, width=1)

    def _draw_storm(self, x: int, y: int, size: int) -> None:
        """Draw a storm cloud with lightning bolt."""
        self._draw_cloud(x, y, size)
        
        # Draw lightning bolt
        bolt_color = self.WEATHER_COLORS['storm']
        bolt_points = [
            (x + size//2, y + size//2),          # Top
            (x + 3*size//5, y + 2*size//3),      # Middle right
            (x + 2*size//5, y + 2*size//3),      # Middle left
            (x + size//2, y + 5*size//6)         # Bottom
        ]
        self.draw.polygon(bolt_points, fill=bolt_color)

    def draw_weather_icon(self, condition: str, x: int, y: int, size: int = 16) -> None:
        """Draw a weather icon based on the condition."""
        # Clear the area where the icon will be drawn
        self.draw.rectangle([x, y, x + size, y + size],
                          fill=(0, 0, 0))
        
        # Draw the appropriate weather icon
        if condition.lower() in ['clear', 'sunny']:
            self._draw_sun(x, y, size)
        elif condition.lower() in ['clouds', 'cloudy', 'partly cloudy']:
            self._draw_cloud(x, y, size)
        elif condition.lower() in ['rain', 'drizzle', 'shower']:
            self._draw_rain(x, y, size)
        elif condition.lower() in ['snow', 'sleet', 'hail']:
            self._draw_snow(x, y, size)
        elif condition.lower() in ['thunderstorm', 'storm']:
            self._draw_storm(x, y, size)
        else:
            # Default to sun if condition is unknown
            self._draw_sun(x, y, size)
        
        self.update_display()

    def draw_text_with_icons(self, text: str, icons: List[tuple] = None, x: int = None, y: int = None, 
                            color: tuple = (255, 255, 255), force_clear: bool = False):
        """Draw text with weather icons at specified positions."""
        if force_clear:
            self.clear()
        else:
            self.image = Image.new('RGB', (self.matrix.width, self.matrix.height))
            self.draw = ImageDraw.Draw(self.image)
        
        # First draw the text
        self.draw_text(text, x, y, color, force_clear=False)
        
        # Then draw any icons
        if icons:
            for icon_type, icon_x, icon_y in icons:
                WeatherIcons.draw_weather_icon(self.draw, icon_type, icon_x, icon_y)
        
        # Update the display
        self.update_display()

    def cleanup(self):
        """Clean up resources."""
        self.matrix.Clear()
        # Reset the singleton state when cleaning up
        DisplayManager._instance = None
        DisplayManager._initialized = False 