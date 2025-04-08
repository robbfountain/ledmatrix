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

        # First get coordinates using geocoding API
        geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={city},{state},{country}&limit=1&appid={api_key}"
        
        try:
            # Get coordinates
            response = requests.get(geo_url)
            response.raise_for_status()
            geo_data = response.json()
            
            if not geo_data:
                print(f"Could not find coordinates for {city}, {state}")
                return
                
            lat = geo_data[0]['lat']
            lon = geo_data[0]['lon']
            
            # Get current weather and forecast using coordinates
            weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units={units}"
            forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={api_key}&units={units}"
            
            # Fetch current weather
            response = requests.get(weather_url)
            response.raise_for_status()
            self.weather_data = response.json()

            # Fetch forecast
            response = requests.get(forecast_url)
            response.raise_for_status()
            self.forecast_data = response.json()

            # Process forecast data
            self._process_forecast_data(self.forecast_data)
            
            self.last_update = time.time()
            print("Weather data updated successfully")
        except Exception as e:
            print(f"Error fetching weather data: {e}")
            self.weather_data = None
            self.forecast_data = None

    def _process_forecast_data(self, forecast_data: Dict[str, Any]) -> None:
        """Process forecast data into hourly and daily forecasts."""
        if not forecast_data:
            return

        # Process hourly forecast (next 6 hours)
        hourly_list = forecast_data.get('list', [])[:6]  # Get next 6 3-hour forecasts
        self.hourly_forecast = []
        
        for hour_data in hourly_list:
            dt = datetime.fromtimestamp(hour_data['dt'])
            temp = round(hour_data['main']['temp'])
            condition = hour_data['weather'][0]['main']
            self.hourly_forecast.append({
                'hour': dt.strftime('%I%p').lstrip('0'),  # Remove leading 0
                'temp': temp,
                'condition': condition
            })

        # Process daily forecast (next 3 days)
        daily_data = {}
        for item in hourly_list:
            date = datetime.fromtimestamp(item['dt']).strftime('%Y-%m-%d')
            if date not in daily_data:
                daily_data[date] = {
                    'temps': [],
                    'conditions': [],
                    'date': datetime.fromtimestamp(item['dt'])
                }
            daily_data[date]['temps'].append(item['main']['temp'])
            daily_data[date]['conditions'].append(item['weather'][0]['main'])

        # Calculate daily summaries
        self.daily_forecast = []
        for date, data in list(daily_data.items())[:3]:  # First 3 days
            temps = data['temps']
            temp_high = round(max(temps))
            temp_low = round(min(temps))
            condition = max(set(data['conditions']), key=data['conditions'].count)
            
            self.daily_forecast.append({
                'date': data['date'].strftime('%a'),  # Day name (Mon, Tue, etc.)
                'date_str': data['date'].strftime('%m/%d'),  # Date (4/8, 4/9, etc.)
                'temp_high': temp_high,
                'temp_low': temp_low,
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

        # Calculate layout parameters
        display_width = self.display_manager.matrix.width
        display_height = self.display_manager.matrix.height
        day_width = display_width // 3  # Divide screen into 3 equal sections
        icon_size = 16
        padding = 4  # Padding between elements

        # Create text lines and collect icon information
        lines = []
        icons = []
        
        for i, day in enumerate(self.daily_forecast):
            # Calculate horizontal position for this day
            x_offset = i * day_width
            
            # Format the day, date, and temperature
            day_str = day['date']  # Day name (Mon, Tue, etc.)
            date_str = day['date_str']  # Date (4/8, 4/9, etc.)
            temp_str = f"{day['temp_low']}°F / {day['temp_high']}°F"
            
            # Position the text and icon
            text_x = x_offset + (day_width // 2)  # Center text horizontally
            day_y = padding  # Day name at the top
            date_y = day_y + 10  # Date below the day name
            temp_y = display_height - padding - 10  # Temperature at the bottom
            
            # Position icon in the middle
            icon_x = x_offset + (day_width // 2) - (icon_size // 2)
            icon_y = (display_height // 2) - (icon_size // 2)
            
            # Add the formatted lines
            lines.append((day_str, text_x, day_y))
            lines.append((date_str, text_x, date_y))
            lines.append((temp_str, text_x, temp_y))
            
            # Add icon position
            icons.append((day['condition'], icon_x, icon_y))

        # Draw everything
        self.display_manager.draw_text_with_icons(
            "",  # Empty text as we'll draw lines manually
            icons=icons,
            force_clear=force_clear
        )
        
        # Draw each line of text
        for text, x, y in lines:
            self.display_manager.draw_text(text, x=x, y=y, force_clear=False) 