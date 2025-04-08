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
        
        # Format the display string with both temp and condition
        display_text = f"{temp}°F\n{condition}"
        
        # Draw both lines at once using the multi-line support in draw_text
        self.display_manager.draw_text(display_text) 