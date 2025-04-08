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
            self._process_forecast_data()
            
            self.last_update = time.time()
        except Exception as e:
            print(f"Error fetching weather data: {e}")
            self.weather_data = None
            self.forecast_data = None

    def _process_forecast_data(self) -> None:
        """Process the forecast data into hourly and daily forecasts."""
        if not self.forecast_data:
            return

        # Process hourly forecast (next 6 hours)
        self.hourly_forecast = []
        for item in self.forecast_data['list'][:6]:  # First 6 entries (3 hours each)
            hour = datetime.fromtimestamp(item['dt']).strftime('%I%p').lstrip('0')  # Remove leading zero
            temp = round(item['main']['temp'])
            condition = item['weather'][0]['main']
            icon = self.WEATHER_ICONS.get(condition, '❓')
            self.hourly_forecast.append({
                'hour': hour,
                'temp': temp,
                'condition': condition,
                'icon': icon
            })

        # Process daily forecast (next 3 days)
        daily_data = {}
        for item in self.forecast_data['list']:
            date = datetime.fromtimestamp(item['dt']).strftime('%Y-%m-%d')
            if date not in daily_data:
                daily_data[date] = {
                    'temps': [],
                    'conditions': []
                }
            daily_data[date]['temps'].append(item['main']['temp'])
            daily_data[date]['conditions'].append(item['weather'][0]['main'])

        # Calculate daily summaries
        self.daily_forecast = []
        for date, data in list(daily_data.items())[:3]:  # First 3 days
            avg_temp = round(sum(data['temps']) / len(data['temps']))
            condition = max(set(data['conditions']), key=data['conditions'].count)
            icon = self.WEATHER_ICONS.get(condition, '❓')
            display_date = datetime.strptime(date, '%Y-%m-%d').strftime('%a %d')
            self.daily_forecast.append({
                'date': display_date,
                'temp': avg_temp,
                'condition': condition,
                'icon': icon
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
        icon = self.WEATHER_ICONS.get(condition, '❓')
        
        # Format the display string with temp and large icon
        display_text = f"{temp}°F\n{icon}"
        
        # Draw both lines at once using the multi-line support in draw_text
        self.display_manager.draw_text(display_text, force_clear=force_clear)

    def display_hourly_forecast(self, scroll_amount: int = 0, force_clear: bool = False) -> None:
        """Display scrolling hourly forecast information."""
        if not self.hourly_forecast:
            self.get_weather()  # This will also update forecasts
            if not self.hourly_forecast:
                return

        # Update scroll position
        self.scroll_position = scroll_amount

        # Create the full scrolling text
        forecasts = []
        for forecast in self.hourly_forecast:
            forecasts.append(f"{forecast['hour']}\n{forecast['temp']}°F\n{forecast['icon']}")
        
        # Join with some spacing between each forecast
        display_text = "   |   ".join(forecasts)
        
        # Draw the scrolling text
        self.display_manager.draw_scrolling_text(
            display_text,
            self.scroll_position,
            force_clear=force_clear
        )

    def display_daily_forecast(self, force_clear: bool = False) -> None:
        """Display 3-day forecast information."""
        if not self.daily_forecast:
            self.get_weather()  # This will also update forecasts
            if not self.daily_forecast:
                return

        # Create a compact display of all three days
        lines = []
        for day in self.daily_forecast:
            lines.append(f"{day['date']}\n{day['temp']}°F {day['icon']}")
        
        # Join all lines with newlines
        display_text = "\n".join(lines)
        
        # Draw the forecast
        self.display_manager.draw_text(display_text, force_clear=force_clear) 