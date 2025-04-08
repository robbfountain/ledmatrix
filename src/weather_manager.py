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
        self.last_draw_time = 0  # Add draw time tracking to reduce flickering

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

        current_time = time.time()
        temp = round(weather_data['main']['temp'])
        condition = weather_data['weather'][0]['main']
        
        # Only update display if forced or data changed
        if force_clear or not hasattr(self, 'last_temp') or temp != self.last_temp or condition != self.last_condition:
            # Draw temperature text and weather icon
            text = f"{temp}°F"
            icon_x = (self.display_manager.matrix.width - 20) // 2  # Center the 20px icon
            icon_y = 2  # Near the top
            
            # Clear and draw
            if force_clear:
                self.display_manager.clear()
            
            # Draw icon and text
            self.display_manager.draw_weather_icon(condition, icon_x, icon_y, size=16)
            self.display_manager.draw_text(
                text,
                y=icon_y + 18,  # Position text below icon
                small_font=False
            )
            
            # Update cache
            self.last_temp = temp
            self.last_condition = condition

    def display_hourly_forecast(self, scroll_amount: int = 0, force_clear: bool = False) -> None:
        """Display scrolling hourly forecast information."""
        if not self.hourly_forecast:
            self.get_weather()  # This will also update forecasts
            if not self.hourly_forecast:
                return

        current_time = time.time()
        # Only update if forced or enough time has passed (100ms minimum between updates)
        if not force_clear and current_time - self.last_draw_time < 0.1:
            return

        # Clear display when starting new scroll
        if force_clear:
            self.display_manager.clear()

        # Calculate base positions
        display_width = self.display_manager.matrix.width
        display_height = self.display_manager.matrix.height
        forecast_width = display_width // 2  # Each forecast takes half the width
        icon_size = 12  # Slightly smaller icons for better fit

        # Create a new image for this frame
        self.display_manager.image = Image.new('RGB', (self.display_manager.matrix.width, self.display_manager.matrix.height))
        self.display_manager.draw = ImageDraw.Draw(self.display_manager.image)

        # Create the forecast display
        for i, forecast in enumerate(self.hourly_forecast):
            # Calculate x position with scrolling
            x_pos = display_width - scroll_amount + (i * forecast_width)
            
            # Only draw if the forecast would be visible
            if x_pos < -forecast_width or x_pos > display_width:
                continue

            # Draw icon at top
            icon_x = x_pos + (forecast_width - icon_size) // 2
            icon_y = 2
            self.display_manager.draw_weather_icon(forecast['condition'], icon_x, icon_y, size=icon_size)

            # Draw hour below icon
            hour_text = forecast['hour']
            hour_y = icon_y + icon_size + 2
            self.display_manager.draw_text(
                hour_text,
                x=x_pos + forecast_width // 2,  # Center in section
                y=hour_y,
                small_font=True
            )

            # Draw temperature at bottom
            temp_text = f"{forecast['temp']}°"
            temp_y = display_height - 8  # 8 pixels from bottom
            self.display_manager.draw_text(
                temp_text,
                x=x_pos + forecast_width // 2,  # Center in section
                y=temp_y,
                small_font=True
            )

            # Draw separator line if not last forecast
            if i < len(self.hourly_forecast) - 1:
                sep_x = x_pos + forecast_width - 1
                if 0 <= sep_x <= display_width:
                    self.display_manager.draw.line(
                        [(sep_x, 0), (sep_x, display_height)],
                        fill=(64, 64, 64)  # Dim gray line
                    )

        # Update the display
        self.display_manager.update_display()
        self.last_draw_time = current_time

    def display_daily_forecast(self, force_clear: bool = False) -> None:
        """Display 3-day forecast information."""
        if not self.daily_forecast:
            self.get_weather()
            if not self.daily_forecast:
                return

        current_time = time.time()
        # Only update if forced or enough time has passed
        if not force_clear and current_time - self.last_draw_time < 0.1:
            return

        # Create new image for this frame
        self.display_manager.image = Image.new('RGB', (self.display_manager.matrix.width, self.display_manager.matrix.height))
        self.display_manager.draw = ImageDraw.Draw(self.display_manager.image)

        # Calculate layout parameters
        display_width = self.display_manager.matrix.width
        display_height = self.display_manager.matrix.height
        section_width = display_width // 3  # Width for each day
        icon_size = 12  # Smaller icons for better fit

        for i, day in enumerate(self.daily_forecast):
            # Calculate base x position for this section
            x_base = i * section_width
            
            # Draw day name at top (e.g., "MON")
            day_text = day['date'].upper()
            self.display_manager.draw_text(
                day_text,
                x=x_base + section_width // 2,  # Center in section
                y=2,  # Near top
                small_font=True
            )

            # Draw weather icon in middle
            icon_x = x_base + (section_width - icon_size) // 2
            icon_y = (display_height - icon_size) // 2
            self.display_manager.draw_weather_icon(
                day['condition'],
                icon_x,
                icon_y,
                size=icon_size
            )

            # Draw temperature at bottom (e.g., "45°/65°")
            temp_text = f"{day['temp_low']}°/{day['temp_high']}°"
            self.display_manager.draw_text(
                temp_text,
                x=x_base + section_width // 2,  # Center in section
                y=display_height - 8,  # 8 pixels from bottom
                small_font=True
            )

            # Draw separator line if not last day
            if i < len(self.daily_forecast) - 1:
                sep_x = x_base + section_width - 1
                self.display_manager.draw.line(
                    [(sep_x, 0), (sep_x, display_height)],
                    fill=(64, 64, 64)  # Dim gray line
                )

        # Update the display
        self.display_manager.update_display()
        self.last_draw_time = current_time 