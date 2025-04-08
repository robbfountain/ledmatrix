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
        self.last_draw_time = 0
        # Layout constants
        self.PADDING = 2
        self.ICON_SIZE = {
            'large': 16,
            'medium': 12,
            'small': 8
        }
        self.COLORS = {
            'text': (255, 255, 255),
            'highlight': (255, 200, 0),
            'separator': (64, 64, 64),
            'temp_high': (255, 100, 100),
            'temp_low': (100, 100, 255)
        }

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
        """Display current weather information using a static layout."""
        weather_data = self.get_weather()
        if not weather_data:
            return

        # Always clear and redraw
        self.display_manager.clear()
        
        # Calculate layout
        display_width = self.display_manager.matrix.width
        display_height = self.display_manager.matrix.height
        
        # Get weather data
        temp = round(weather_data['main']['temp'])
        condition = weather_data['weather'][0]['main']
        humidity = weather_data['main']['humidity']
        
        # Draw temperature (large, centered)
        temp_text = f"{temp}°F"
        self.display_manager.draw_text(
            temp_text,
            y=2,  # Near top
            color=self.COLORS['highlight'],
            small_font=False
        )
        
        # Draw weather icon below temperature
        icon_x = (display_width - self.ICON_SIZE['large']) // 2
        icon_y = display_height // 2 - 4
        self.display_manager.draw_weather_icon(condition, icon_x, icon_y, size=self.ICON_SIZE['large'])
        
        # Draw humidity at bottom
        humidity_text = f"Humidity: {humidity}%"
        self.display_manager.draw_text(
            humidity_text,
            y=display_height - 8,
            color=self.COLORS['text'],
            small_font=True
        )
        
        # Update display
        self.display_manager.update_display()

    def display_hourly_forecast(self, scroll_position: int = 0, force_clear: bool = False) -> None:
        """Display static hourly forecast showing next 3 hours."""
        if not self.hourly_forecast:
            self.get_weather()
            if not self.hourly_forecast:
                return

        # Always clear and redraw
        self.display_manager.clear()

        # Calculate layout parameters
        display_width = self.display_manager.matrix.width
        display_height = self.display_manager.matrix.height
        section_width = display_width // 3  # Show 3 hours
        
        # Draw header
        header_text = "NEXT 3 HOURS"
        self.display_manager.draw_text(
            header_text,
            y=1,
            color=self.COLORS['highlight'],
            small_font=True
        )
        
        # Draw separator line
        self.display_manager.draw.line(
            [(0, 8), (display_width, 8)],
            fill=self.COLORS['separator']
        )

        # Show first 3 hours
        for i, forecast in enumerate(self.hourly_forecast[:3]):
            x_base = i * section_width
            
            # Draw time
            self.display_manager.draw_text(
                forecast['hour'],
                x=x_base + section_width // 2,
                y=10,
                color=self.COLORS['text'],
                small_font=True
            )

            # Draw icon
            icon_x = x_base + (section_width - self.ICON_SIZE['medium']) // 2
            icon_y = 14
            self.display_manager.draw_weather_icon(
                forecast['condition'],
                icon_x,
                icon_y,
                size=self.ICON_SIZE['medium']
            )

            # Draw temperature
            temp_text = f"{forecast['temp']}°F"
            self.display_manager.draw_text(
                temp_text,
                x=x_base + section_width // 2,
                y=display_height - 8,
                color=self.COLORS['text'],
                small_font=True
            )

            # Draw separator lines
            if i < 2:  # Only draw between sections
                sep_x = x_base + section_width - 1
                self.display_manager.draw.line(
                    [(sep_x, 8), (sep_x, display_height)],
                    fill=self.COLORS['separator']
                )

        # Update display
        self.display_manager.update_display()

    def display_daily_forecast(self, force_clear: bool = False) -> None:
        """Display static 3-day forecast."""
        if not self.daily_forecast:
            self.get_weather()
            if not self.daily_forecast:
                return

        # Always clear and redraw
        self.display_manager.clear()

        # Calculate layout parameters
        display_width = self.display_manager.matrix.width
        display_height = self.display_manager.matrix.height
        section_width = display_width // 3

        # Draw header
        header_text = "3-DAY FORECAST"
        self.display_manager.draw_text(
            header_text,
            y=1,
            color=self.COLORS['highlight'],
            small_font=True
        )
        
        # Draw separator line
        self.display_manager.draw.line(
            [(0, 8), (display_width, 8)],
            fill=self.COLORS['separator']
        )

        for i, day in enumerate(self.daily_forecast):
            x_base = i * section_width
            
            # Draw day name
            day_text = day['date'].upper()
            self.display_manager.draw_text(
                day_text,
                x=x_base + section_width // 2,
                y=10,
                color=self.COLORS['text'],
                small_font=True
            )

            # Draw weather icon
            icon_x = x_base + (section_width - self.ICON_SIZE['medium']) // 2
            icon_y = 14
            self.display_manager.draw_weather_icon(
                day['condition'],
                icon_x,
                icon_y,
                size=self.ICON_SIZE['medium']
            )

            # Draw temperatures with different colors for high/low
            temp_text = f"{day['temp_low']}°/{day['temp_high']}°"
            self.display_manager.draw_text(
                temp_text,
                x=x_base + section_width // 2,
                y=display_height - 8,
                color=self.COLORS['text'],
                small_font=True
            )

            # Draw separator lines
            if i < 2:  # Only draw between sections
                sep_x = x_base + section_width - 1
                self.display_manager.draw.line(
                    [(sep_x, 8), (sep_x, display_height)],
                    fill=self.COLORS['separator']
                )

        # Update display
        self.display_manager.update_display() 