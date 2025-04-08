import requests
import time
from datetime import datetime
from typing import Dict, Any, List
from PIL import Image, ImageDraw

class WeatherManager:
    # Weather condition to larger colored icons (we'll use these as placeholders until you provide custom ones)
    WEATHER_ICONS = {
        'Clear': '🌞',      # Larger sun with rays
        'Clouds': '☁️',     # Cloud
        'Rain': '🌧️',      # Rain cloud
        'Snow': '❄️',      # Snowflake
        'Thunderstorm': '⛈️', # Storm cloud
        'Drizzle': '🌦️',    # Sun behind rain cloud
        'Mist': '🌫️',      # Fog
        'Fog': '🌫️',       # Fog
        'Haze': '🌫️',      # Fog
        'Smoke': '🌫️',     # Fog
        'Dust': '🌫️',      # Fog
        'Sand': '🌫️',      # Fog
        'Ash': '🌫️',       # Fog
        'Squall': '💨',     # Dash symbol
        'Tornado': '🌪️'     # Tornado
    }

    def __init__(self, config: Dict[str, Any], display_manager):
        self.config = config
        self.display_manager = display_manager
        self.weather_config = config.get('weather', {})
        self.location = config.get('location', {})
        self.last_update = 0
        self.weather_data = None
        self.forecast_data = None
        self.hourly_forecast = None
        self.daily_forecast = None
        self.scroll_position = 0

    def _fetch_weather(self) -> None:
        """Fetch current weather and forecast data from OpenWeatherMap API."""
        api_key = self.weather_config.get('api_key')
        if not api_key:
            print("No API key configured for weather")
            return

        city = self.location['city']
        state = self.location['state']
        country = self.location['country']
        units = self.weather_config.get('units', 'imperial')

        # Get current weather
        current_url = f"http://api.openweathermap.org/data/2.5/weather?q={city},{state},{country}&appid={api_key}&units={units}"
        
        # Get forecast data (includes hourly and daily)
        forecast_url = f"http://api.openweathermap.org/data/2.5/forecast?q={city},{state},{country}&appid={api_key}&units={units}"
        
        try:
            # Fetch current weather
            response = requests.get(current_url)
            response.raise_for_status()
            self.weather_data = response.json()

            # Fetch forecast
            response = requests.get(forecast_url)
            response.raise_for_status()
            self.forecast_data = response.json()

            # Process forecast data
            self._process_forecast_data(self.forecast_data)
            
            self.last_update = time.time()
        except Exception as e:
            print(f"Error fetching weather data: {e}")
            self.weather_data = None
            self.forecast_data = None

    def _process_forecast_data(self, forecast_data: Dict[str, Any]) -> None:
        """Process forecast data into hourly and daily forecasts."""
        if not forecast_data:
            return

        # Process hourly forecast (next 6 hours)
        hourly = forecast_data.get('hourly', [])[:6]
        self.hourly_forecast = []
        for hour in hourly:
            dt = datetime.fromtimestamp(hour['dt'])
            temp = round(hour['temp'])
            condition = hour['weather'][0]['main']
            self.hourly_forecast.append({
                'hour': dt.strftime('%I%p'),
                'temp': temp,
                'condition': condition
            })

        # Process daily forecast (next 3 days)
        daily = forecast_data.get('daily', [])[1:4]  # Skip today, get next 3 days
        self.daily_forecast = []
        for day in daily:
            dt = datetime.fromtimestamp(day['dt'])
            temp = round(day['temp']['day'])
            condition = day['weather'][0]['main']
            self.daily_forecast.append({
                'date': dt.strftime('%a'),
                'temp': temp,
                'condition': condition
            })

    def get_weather(self) -> Dict[str, Any]:
        """Get current weather data, fetching new data if needed."""
        current_time = time.time()
        if (not self.weather_data or 
            current_time - self.last_update > self.weather_config.get('update_interval', 300)):
            self._fetch_weather()
        return self.weather_data

    def display_weather(self, force_clear: bool = False) -> None:
        """Display current weather information on the LED matrix."""
        weather_data = self.get_weather()
        if not weather_data:
            return

        temp = round(weather_data['main']['temp'])
        condition = weather_data['weather'][0]['main']
        
        # Draw temperature text and weather icon
        text = f"{temp}°F"
        icon_x = (self.display_manager.matrix.width - 20) // 2  # Center the 20px icon
        icon_y = 2  # Near the top
        self.display_manager.draw_text_with_icons(
            text,
            icons=[(condition, icon_x, icon_y)],
            force_clear=force_clear
        )

    def display_hourly_forecast(self, scroll_amount: int = 0, force_clear: bool = False) -> None:
        """Display scrolling hourly forecast information."""
        if not self.hourly_forecast:
            self.get_weather()  # This will also update forecasts
            if not self.hourly_forecast:
                return

        # Update scroll position
        self.scroll_position = scroll_amount

        # Create the full scrolling text with icons
        forecasts = []
        icons = []
        x_offset = self.display_manager.matrix.width - scroll_amount
        icon_size = 16

        for i, forecast in enumerate(self.hourly_forecast):
            # Add text
            forecasts.append(f"{forecast['hour']}\n{forecast['temp']}°F")
            
            # Calculate icon position
            icon_x = x_offset + (i * (icon_size * 3))  # Space icons out
            icon_y = 2  # Near top
            icons.append((forecast['condition'], icon_x, icon_y))

        # Join with spacing
        display_text = "   |   ".join(forecasts)
        
        # Draw everything
        self.display_manager.draw_text_with_icons(
            display_text,
            icons=icons,
            x=x_offset,
            force_clear=force_clear
        )

    def display_daily_forecast(self, force_clear: bool = False) -> None:
        """Display 3-day forecast information."""
        if not self.daily_forecast:
            self.get_weather()  # This will also update forecasts
            if not self.daily_forecast:
                return

        # Create text lines and collect icon information
        lines = []
        icons = []
        y_offset = 2
        icon_size = 16

        for i, day in enumerate(self.daily_forecast):
            lines.append(f"{day['date']}: {day['temp']}°F")
            icons.append((
                day['condition'],
                self.display_manager.matrix.width - icon_size - 2,  # Right align
                y_offset + (i * (icon_size + 2))  # Stack vertically
            ))
        
        # Join lines and draw everything
        display_text = "\n".join(lines)
        self.display_manager.draw_text_with_icons(
            display_text,
            icons=icons,
            force_clear=force_clear
        ) 