import time
import logging
import requests
import json
import random
from typing import Dict, Any, List, Tuple
from datetime import datetime
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StockManager:
    def __init__(self, config: Dict[str, Any], display_manager):
        self.config = config
        self.display_manager = display_manager
        self.stocks_config = config.get('stocks', {})
        self.last_update = 0
        self.stock_data = {}
        self.current_stock_index = 0
        self.base_url = "https://query2.finance.yahoo.com"
        self.logo_cache = {}
        
        # Set logos directory path (assuming it exists)
        self.logos_dir = "assets/logos/stocks"
        
        # Default colors for stocks
        self.default_colors = [
            (0, 255, 0),    # Green
            (0, 255, 255),  # Cyan
            (255, 255, 0),  # Yellow
            (255, 165, 0),  # Orange
            (128, 0, 128),  # Purple
            (255, 0, 0),    # Red
            (0, 0, 255),    # Blue
            (255, 192, 203) # Pink
        ]
        
    def _get_stock_color(self, symbol: str) -> Tuple[int, int, int]:
        """Get a consistent color for a stock symbol."""
        # Use the symbol as a seed for consistent color assignment
        random.seed(hash(symbol))
        color_index = random.randint(0, len(self.default_colors) - 1)
        random.seed()  # Reset the seed
        return self.default_colors[color_index]
        
    def _fetch_stock_data(self, symbol: str) -> Dict[str, Any]:
        """Fetch stock data from Yahoo Finance API."""
        try:
            # Use Yahoo Finance API directly
            url = f"{self.base_url}/v8/finance/chart/{symbol}"
            params = {
                "interval": "1m",
                "period": "1d"
            }
            response = requests.get(url, params=params)
            data = response.json()
            
            if "chart" not in data or "result" not in data["chart"] or not data["chart"]["result"]:
                logger.error(f"Invalid response for {symbol}: {data}")
                return None
                
            result = data["chart"]["result"][0]
            meta = result["meta"]
            
            # Extract price data
            price = meta.get("regularMarketPrice", 0)
            prev_close = meta.get("chartPreviousClose", 0)
            
            # Calculate change percentage
            change_pct = 0
            if prev_close > 0:
                change_pct = ((price - prev_close) / prev_close) * 100
                
            # Get company name if available
            company_name = meta.get("instrumentInfo", {}).get("longName", symbol)
                
            return {
                "symbol": symbol,
                "name": company_name,
                "price": price,
                "change": change_pct,
                "open": prev_close
            }
        except Exception as e:
            logger.error(f"Error fetching stock data for {symbol}: {e}")
            return None
            
    def _download_logo(self, symbol: str) -> str:
        """Download company logo for a stock symbol."""
        logo_path = os.path.join(self.logos_dir, f"{symbol}.png")
        
        # If logo already exists, return the path
        if os.path.exists(logo_path):
            return logo_path
            
        try:
            # Try to get logo from Yahoo Finance
            url = f"https://query2.finance.yahoo.com/v7/finance/options/{symbol}"
            response = requests.get(url)
            data = response.json()
            
            if "optionChain" in data and "result" in data["optionChain"] and data["optionChain"]["result"]:
                result = data["optionChain"]["result"][0]
                if "quote" in result and "logoUrl" in result["quote"]:
                    logo_url = result["quote"]["logoUrl"]
                    
                    # Download the logo
                    logo_response = requests.get(logo_url)
                    if logo_response.status_code == 200:
                        try:
                            with open(logo_path, "wb") as f:
                                f.write(logo_response.content)
                            logger.info(f"Downloaded logo for {symbol}")
                            return logo_path
                        except IOError as e:
                            logger.error(f"Could not write logo file for {symbol}: {e}")
                            return None
            
            # If we couldn't get a logo, create a placeholder
            return self._create_placeholder_logo(symbol, logo_path)
            
        except Exception as e:
            logger.error(f"Error downloading logo for {symbol}: {e}")
            # Create a placeholder logo
            return self._create_placeholder_logo(symbol, logo_path)
            
    def _create_placeholder_logo(self, symbol: str, logo_path: str) -> str:
        """Create a placeholder logo with the stock symbol."""
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            # Create a 32x32 image with a colored background
            color = self._get_stock_color(symbol)
            img = Image.new('RGB', (32, 32), color)
            draw = ImageDraw.Draw(img)
            
            # Try to load a font, fall back to default if not available
            try:
                font = ImageFont.truetype("assets/fonts/PressStart2P-Regular.ttf", 8)
            except:
                font = ImageFont.load_default()
                
            # Draw the symbol
            text_bbox = draw.textbbox((0, 0), symbol, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            
            # Center the text
            x = (32 - text_width) // 2
            y = (32 - text_height) // 2
            
            draw.text((x, y), symbol, fill=(255, 255, 255), font=font)
            
            try:
                # Save the image
                img.save(logo_path)
                logger.info(f"Created placeholder logo for {symbol}")
                return logo_path
            except IOError as e:
                logger.error(f"Could not save placeholder logo for {symbol}: {e}")
                return None
            
        except Exception as e:
            logger.error(f"Error creating placeholder logo for {symbol}: {e}")
            return None

    def update_stock_data(self):
        """Update stock data if enough time has passed."""
        current_time = time.time()
        if current_time - self.last_update < self.stocks_config.get('update_interval', 60):
            return
            
        # Get symbols from config
        symbols = self.stocks_config.get('symbols', [])
        
        # If symbols is a list of strings, convert to list of dicts
        if symbols and isinstance(symbols[0], str):
            symbols = [{"symbol": symbol} for symbol in symbols]
            
        for stock in symbols:
            symbol = stock['symbol']
            data = self._fetch_stock_data(symbol)
            if data:
                # Add color if not specified
                if 'color' not in stock:
                    data['color'] = self._get_stock_color(symbol)
                else:
                    data['color'] = tuple(stock['color'])
                    
                # Try to get logo
                logo_path = self._download_logo(symbol)
                if logo_path:
                    data['logo_path'] = logo_path
                
                self.stock_data[symbol] = data
                
        self.last_update = current_time

    def display_stocks(self, force_clear: bool = False):
        """Display stock information on the LED matrix."""
        if not self.stocks_config.get('enabled', False):
            return
            
        self.update_stock_data()
        
        if not self.stock_data:
            logger.warning("No stock data available to display")
            return
            
        # Clear the display if forced or if this is the first stock
        if force_clear or self.current_stock_index == 0:
            self.display_manager.clear()
            
        # Get the current stock to display
        symbols = list(self.stock_data.keys())
        if not symbols:
            return
            
        current_symbol = symbols[self.current_stock_index]
        data = self.stock_data[current_symbol]
        
        # Format the display text
        display_format = self.stocks_config.get('display_format', "{symbol}: ${price} ({change}%)")
        display_text = display_format.format(
            symbol=data['symbol'],
            price=f"{data['price']:.2f}",
            change=f"{data['change']:+.2f}"
        )
        
        # Draw the stock information
        color = (0, 255, 0) if data['change'] >= 0 else (255, 0, 0)  # Green for up, red for down
        self.display_manager.draw_text(display_text, color=color)
        self.display_manager.update_display()
        
        # Move to next stock for next update
        self.current_stock_index = (self.current_stock_index + 1) % len(symbols) 