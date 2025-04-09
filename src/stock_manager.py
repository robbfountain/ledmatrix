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
        self.base_url = "https://query1.finance.yahoo.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
    def _get_stock_color(self, symbol: str) -> Tuple[int, int, int]:
        """Get color based on stock performance."""
        if symbol not in self.stock_data:
            return (255, 255, 255)  # White for unknown
        
        change = self.stock_data[symbol].get('change', 0)
        if change > 0:
            return (0, 255, 0)  # Green for positive
        elif change < 0:
            return (255, 0, 0)  # Red for negative
        return (255, 255, 0)  # Yellow for no change
        
    def _fetch_stock_data(self, symbol: str) -> Dict[str, Any]:
        """Fetch stock data from Yahoo Finance API."""
        try:
            # Use Yahoo Finance quote endpoint
            url = f"{self.base_url}/v7/finance/quote"
            params = {
                "symbols": symbol
            }
            
            response = requests.get(url, params=params, headers=self.headers)
            response.raise_for_status()  # Raise an error for bad status codes
            
            data = response.json()
            logger.debug(f"Raw response for {symbol}: {data}")
            
            if not data or "quoteResponse" not in data or "result" not in data["quoteResponse"] or not data["quoteResponse"]["result"]:
                logger.error(f"Invalid response format for {symbol}")
                return None
            
            quote = data["quoteResponse"]["result"][0]
            
            # Extract required fields with fallbacks
            price = quote.get("regularMarketPrice", 0)
            prev_close = quote.get("regularMarketPreviousClose", price)
            change_pct = quote.get("regularMarketChangePercent", 0)
            
            # If we didn't get a change percentage, calculate it
            if change_pct == 0 and prev_close != 0:
                change_pct = ((price - prev_close) / prev_close) * 100
            
            return {
                "symbol": symbol,
                "name": quote.get("longName", symbol),
                "price": price,
                "change": change_pct,
                "open": prev_close
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error fetching data for {symbol}: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error for {symbol}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching data for {symbol}: {e}")
            return None

    def update_stock_data(self):
        """Update stock data if enough time has passed."""
        current_time = time.time()
        if current_time - self.last_update < self.stocks_config.get('update_interval', 60):
            return
            
        # Get symbols from config
        symbols = self.stocks_config.get('symbols', [])
        if not symbols:
            logger.warning("No stock symbols configured")
            return
            
        # If symbols is a list of strings, convert to list of dicts
        if isinstance(symbols[0], str):
            symbols = [{"symbol": symbol} for symbol in symbols]
            
        success = False  # Track if we got any successful updates
        for stock in symbols:
            symbol = stock['symbol']
            data = self._fetch_stock_data(symbol)
            if data:
                self.stock_data[symbol] = data
                success = True
                logger.info(f"Updated {symbol}: ${data['price']:.2f} ({data['change']:+.2f}%)")
                
        if success:
            self.last_update = current_time
        else:
            logger.error("Failed to fetch data for any configured stocks")

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