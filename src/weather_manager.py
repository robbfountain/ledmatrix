import requests
import time
from typing import Dict, Any
from PIL import Image, ImageDraw

class WeatherManager:
    def __init__(self, config: Dict[str, Any], display_manager):
        self.config = config
        self.display_manager = display_manager
        self.weather_config = config.get('weather', {})
        self.location = config.get('location', {})
        self.last_update = 0
        self.weather_data = None

    def _fetch_weather(self) -> None:
        """Fetch weather data from OpenWeatherMap API."""
        api_key = self.weather_config['api_key']
        city = self.location['city']
        state = self.location['state']
        country = self.location['country']
        units = self.weather_config.get('units', 'imperial')

        url = f"http://api.openweathermap.org/data/2.5/weather?q={city},{state},{country}&appid={api_key}&units={units}"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            self.weather_data = response.json()
            self.last_update = time.time()
        except Exception as e:
            print(f"Error fetching weather data: {e}")
            self.weather_data = None

    def get_weather(self) -> Dict[str, Any]:
        """Get current weather data, fetching new data if needed."""
        current_time = time.time()
        if (not self.weather_data or 
            current_time - self.last_update > self.weather_config.get('update_interval', 300)):
            self._fetch_weather()
        return self.weather_data

    def display_weather(self) -> None:
        """Display weather information on the LED matrix."""
        weather_data = self.get_weather()
        if not weather_data:
            return

        temp = round(weather_data['main']['temp'])
        condition = weather_data['weather'][0]['main']
        
        # Format the display string
        display_text = self.weather_config.get('display_format', '{temp}°F\n{condition}')
        display_text = display_text.format(temp=temp, condition=condition)

        # Split text into lines
        lines = display_text.split('\n')
        
        # Calculate vertical spacing
        total_height = len(lines) * 24  # Assuming 24px font height
        start_y = (self.display_manager.matrix.height - total_height) // 2

        # Clear the display
        self.display_manager.clear()

        # Draw each line centered
        for i, line in enumerate(lines):
            text_width = self.display_manager.font.getlength(line)
            x = (self.display_manager.matrix.width - text_width) // 2
            y = start_y + (i * 24)
            self.display_manager.draw_text(line, x, y) 