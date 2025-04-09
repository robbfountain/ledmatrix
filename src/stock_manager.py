import time
import logging
import requests
import json
import random
from typing import Dict, Any, List, Tuple
from datetime import datetime
import os
import urllib.parse
import re

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
        
    def _extract_json_from_html(self, html: str) -> Dict:
        """Extract the JSON data from Yahoo Finance HTML."""
        try:
            # Look for the finance data in the HTML
            patterns = [
                r'root\.App\.main = (.*?);\s*</script>',
                r'"QuotePageStore":\s*({.*?}),\s*"',
                r'{"regularMarketPrice":.*?"regularMarketChangePercent".*?}'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, html, re.DOTALL)
                if match:
                    json_str = match.group(1)
                    try:
                        data = json.loads(json_str)
                        if isinstance(data, dict):
                            if 'context' in data:
                                # First pattern matched
                                context = data.get('context', {})
                                dispatcher = context.get('dispatcher', {})
                                stores = dispatcher.get('stores', {})
                                quote_data = stores.get('QuoteSummaryStore', {})
                                if quote_data:
                                    return quote_data
                            else:
                                # Direct quote data
                                return data
                    except json.JSONDecodeError:
                        continue
                        
            # If we get here, try one last attempt to find the price data directly
            price_match = re.search(r'"regularMarketPrice":{"raw":([\d.]+)', html)
            change_match = re.search(r'"regularMarketChangePercent":{"raw":([-\d.]+)', html)
            prev_close_match = re.search(r'"regularMarketPreviousClose":{"raw":([\d.]+)', html)
            name_match = re.search(r'"shortName":"([^"]+)"', html)
            
            if price_match:
                return {
                    "price": {
                        "regularMarketPrice": {"raw": float(price_match.group(1))},
                        "regularMarketChangePercent": {"raw": float(change_match.group(1)) if change_match else 0},
                        "regularMarketPreviousClose": {"raw": float(prev_close_match.group(1)) if prev_close_match else 0},
                        "shortName": name_match.group(1) if name_match else None
                    }
                }
            
            return {}
        except Exception as e:
            logger.error(f"Error extracting JSON data: {e}")
            return {}
        
    def _fetch_stock_data(self, symbol: str) -> Dict[str, Any]:
        """Fetch stock data from Yahoo Finance public API."""
        try:
            # Use Yahoo Finance public API
            encoded_symbol = urllib.parse.quote(symbol)
            url = f"https://finance.yahoo.com/quote/{encoded_symbol}"
            
            response = requests.get(url, headers=self.headers, timeout=5)
            if response.status_code != 200:
                logger.error(f"Failed to fetch data for {symbol}: HTTP {response.status_code}")
                return None
                
            # Extract the embedded JSON data
            quote_data = self._extract_json_from_html(response.text)
            if not quote_data:
                logger.error(f"Could not extract quote data for {symbol}")
                return None
                
            # Get the price data
            price = quote_data.get('price', {})
            if not price:
                logger.error(f"No price data found for {symbol}")
                return None
                
            regular_market = price.get('regularMarketPrice', {})
            previous_close = price.get('regularMarketPreviousClose', {})
            change_percent = price.get('regularMarketChangePercent', {})
            
            # Extract raw values with fallbacks
            current_price = regular_market.get('raw', 0) if isinstance(regular_market, dict) else regular_market
            prev_close = previous_close.get('raw', current_price) if isinstance(previous_close, dict) else previous_close
            change_pct = change_percent.get('raw', 0) if isinstance(change_percent, dict) else change_percent
            
            # If we don't have a change percentage, calculate it
            if change_pct == 0 and prev_close > 0:
                change_pct = ((current_price - prev_close) / prev_close) * 100
            
            # Get company name
            name = price.get('shortName', symbol)
            
            logger.debug(f"Processed data for {symbol}: price={current_price}, change={change_pct}%")
            
            return {
                "symbol": symbol,
                "name": name,
                "price": current_price,
                "change": change_pct,
                "open": prev_close
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error fetching data for {symbol}: {e}")
            return None
        except (ValueError, IndexError) as e:
            logger.error(f"Error parsing data for {symbol}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching data for {symbol}: {e}")
            return None

    def update_stock_data(self):
        """Update stock data if enough time has passed."""
        current_time = time.time()
        update_interval = self.stocks_config.get('update_interval', 60)
        
        # Add a small random delay to prevent exact timing matches
        if current_time - self.last_update < update_interval + random.uniform(0, 2):
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
            # Add a small delay between requests to avoid rate limiting
            time.sleep(random.uniform(0.5, 1.5))
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