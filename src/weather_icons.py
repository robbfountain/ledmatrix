from PIL import Image, ImageDraw
import math

class WeatherIcons:
    @staticmethod
    def draw_sun(draw: ImageDraw, x: int, y: int, size: int = 16, color: tuple = (255, 200, 0)):
        """Draw a sun icon with rays."""
        center_x = x + size // 2
        center_y = y + size // 2
        radius = size // 3
        
        # Draw main sun circle
        draw.ellipse([
            center_x - radius, center_y - radius,
            center_x + radius, center_y + radius
        ], fill=color)
        
        # Draw rays
        ray_length = size // 4
        for angle in range(0, 360, 45):
            rad = math.radians(angle)
            start_x = center_x + (radius * math.cos(rad))
            start_y = center_y + (radius * math.sin(rad))
            end_x = center_x + ((radius + ray_length) * math.cos(rad))
            end_y = center_y + ((radius + ray_length) * math.sin(rad))
            draw.line([start_x, start_y, end_x, end_y], fill=color, width=2)

    @staticmethod
    def draw_cloud(draw: ImageDraw, x: int, y: int, size: int = 16, color: tuple = (200, 200, 200)):
        """Draw a cloud icon."""
        # Draw multiple circles to form cloud shape
        circle_size = size // 2
        positions = [
            (x + size//4, y + size//3),
            (x + size//2, y + size//3),
            (x + size//3, y + size//6)
        ]
        
        for pos_x, pos_y in positions:
            draw.ellipse([
                pos_x, pos_y,
                pos_x + circle_size, pos_y + circle_size
            ], fill=color)

    @staticmethod
    def draw_rain(draw: ImageDraw, x: int, y: int, size: int = 16):
        """Draw rain icon with cloud and droplets."""
        # Draw cloud first
        WeatherIcons.draw_cloud(draw, x, y, size)
        
        # Draw rain drops
        drop_color = (0, 150, 255)  # Light blue
        drop_length = size // 3
        drop_spacing = size // 4
        
        for i in range(3):
            drop_x = x + size//4 + (i * drop_spacing)
            drop_y = y + size//2
            draw.line([
                drop_x, drop_y,
                drop_x - 2, drop_y + drop_length
            ], fill=drop_color, width=2)

    @staticmethod
    def draw_snow(draw: ImageDraw, x: int, y: int, size: int = 16):
        """Draw snow icon with cloud and snowflakes."""
        # Draw cloud first
        WeatherIcons.draw_cloud(draw, x, y, size)
        
        # Draw snowflakes
        snow_color = (200, 200, 255)  # Light blue-white
        flake_size = size // 6
        flake_spacing = size // 4
        
        for i in range(3):
            center_x = x + size//4 + (i * flake_spacing)
            center_y = y + size//2
            
            # Draw 6-point snowflake
            for angle in range(0, 360, 60):
                rad = math.radians(angle)
                end_x = center_x + (flake_size * math.cos(rad))
                end_y = center_y + (flake_size * math.sin(rad))
                draw.line([center_x, center_y, end_x, end_y], fill=snow_color, width=1)

    @staticmethod
    def draw_thunderstorm(draw: ImageDraw, x: int, y: int, size: int = 16):
        """Draw thunderstorm icon with cloud and lightning."""
        # Draw dark cloud
        WeatherIcons.draw_cloud(draw, x, y, size, color=(100, 100, 100))
        
        # Draw lightning bolt
        lightning_color = (255, 255, 0)  # Yellow
        bolt_points = [
            (x + size//2, y + size//3),
            (x + size//2 - size//4, y + size//2),
            (x + size//2, y + size//2),
            (x + size//2 - size//4, y + size//2 + size//4)
        ]
        draw.line(bolt_points, fill=lightning_color, width=2)

    @staticmethod
    def draw_mist(draw: ImageDraw, x: int, y: int, size: int = 16):
        """Draw mist/fog icon."""
        mist_color = (200, 200, 200)  # Light gray
        wave_height = size // 4
        wave_spacing = size // 3
        
        for i in range(3):
            wave_y = y + size//3 + (i * wave_spacing)
            draw.line([
                x + size//4, wave_y,
                x + size//4 + size//2, wave_y + wave_height
            ], fill=mist_color, width=2)

    @staticmethod
    def draw_weather_icon(draw: ImageDraw, condition: str, x: int, y: int, size: int = 16):
        """Draw the appropriate weather icon based on the condition."""
        condition = condition.lower()
        
        if 'clear' in condition or 'sunny' in condition:
            WeatherIcons.draw_sun(draw, x, y, size)
        elif 'cloud' in condition:
            WeatherIcons.draw_cloud(draw, x, y, size)
        elif 'rain' in condition or 'drizzle' in condition:
            WeatherIcons.draw_rain(draw, x, y, size)
        elif 'snow' in condition:
            WeatherIcons.draw_snow(draw, x, y, size)
        elif 'thunder' in condition or 'storm' in condition:
            WeatherIcons.draw_thunderstorm(draw, x, y, size)
        elif 'mist' in condition or 'fog' in condition or 'haze' in condition:
            WeatherIcons.draw_mist(draw, x, y, size)
        else:
            # Default to cloud for unknown conditions
            WeatherIcons.draw_cloud(draw, x, y, size) 