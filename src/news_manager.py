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
from src.config_manager import ConfigManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NewsManager:
    def __init__(self, config: Dict[str, Any], display_manager):
        self.config = config
        self.config_manager = ConfigManager()
        self.display_manager = display_manager
        self.stocks_config = config.get('stocks', {})
        self.news_config = config.get('news', {})
        self.last_update = 0
        self.news_data = {}
        self.current_news_index = 0
        self.scroll_position = 0
        self.scroll_speed = self.news_config.get('scroll_speed', 1)  # Pixels to move per frame
        self.scroll_delay = self.news_config.get('scroll_delay', 0.05)  # Delay between scroll updates
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        # Initialize with first update
        self.update_news_data()
        
    def _fetch_news_for_symbol(self, symbol: str) -> List[Dict[str, Any]]:
        """Fetch news headlines for a stock symbol."""
        try:
            # Using Yahoo Finance API to get news
            encoded_symbol = urllib.parse.quote(symbol)
            url = f"https://query1.finance.yahoo.com/v1/finance/search?q={encoded_symbol}&lang=en-US&region=US&quotesCount=0&newsCount={self.news_config.get('max_headlines_per_symbol', 5)}"
            
            response = requests.get(url, headers=self.headers, timeout=5)
            if response.status_code != 200:
                logger.error(f"Failed to fetch news for {symbol}: HTTP {response.status_code}")
                return []
                
            data = response.json()
            news_items = data.get('news', [])
            
            # Process and format news items
            formatted_news = []
            for item in news_items:
                formatted_news.append({
                    "title": item.get('title', ''),
                    "publisher": item.get('publisher', ''),
                    "link": item.get('link', ''),
                    "published": item.get('providerPublishTime', 0)
                })
                
            logger.info(f"Fetched {len(formatted_news)} news items for {symbol}")
            return formatted_news
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error fetching news for {symbol}: {e}")
            return []
        except (ValueError, IndexError, KeyError) as e:
            logger.error(f"Error parsing news data for {symbol}: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching news for {symbol}: {e}")
            return []
            
    def update_news_data(self):
        """Update news data for all configured stock symbols."""
        current_time = time.time()
        update_interval = self.news_config.get('update_interval', 300)  # Default to 5 minutes
        
        # If not enough time has passed, keep using existing data
        if current_time - self.last_update < update_interval:
            return
            
        # Get symbols from config
        symbols = self.stocks_config.get('symbols', [])
        if not symbols:
            logger.warning("No stock symbols configured for news")
            return
            
        # Create temporary storage for new data
        new_data = {}
        success = False
        
        for symbol in symbols:
            # Add a small delay between requests to avoid rate limiting
            time.sleep(random.uniform(0.1, 0.3))
            news_items = self._fetch_news_for_symbol(symbol)
            if news_items:
                new_data[symbol] = news_items
                success = True
                
        if success:
            # Only update the displayed data when we have new data
            self.news_data = new_data
            self.last_update = current_time
            self.current_news_index = 0
            self.scroll_position = 0
            logger.info(f"Updated news data for {len(new_data)} symbols")
        else:
            logger.error("Failed to fetch news for any configured stocks")
            
    def display_news(self):
        """Display news headlines by scrolling them across the screen."""
        if not self.news_config.get('enabled', False):
            return
            
        # Start update in background if needed
        if time.time() - self.last_update >= self.news_config.get('update_interval', 300):
            self.update_news_data()
            
        if not self.news_data:
            logger.warning("No news data available to display")
            return
            
        # Get all news items from all symbols
        all_news = []
        for symbol, news_items in self.news_data.items():
            for item in news_items:
                all_news.append({
                    "symbol": symbol,
                    "title": item["title"],
                    "publisher": item["publisher"]
                })
                
        if not all_news:
            return
            
        # Get the current news item to display
        current_news = all_news[self.current_news_index]
        
        # Format the news text
        news_text = f"{current_news['symbol']}: {current_news['title']}"
        
        # Get text dimensions
        bbox = self.display_manager.draw.textbbox((0, 0), news_text, font=self.display_manager.small_font)
        text_width = bbox[2] - bbox[0]
        
        # Clear the display
        self.display_manager.clear()
        
        # Draw the news text at the current scroll position
        self.display_manager.draw_text(
            news_text,
            x=self.display_manager.matrix.width - self.scroll_position,
            y=16,  # Center vertically
            color=(255, 255, 255),  # White
            small_font=True
        )
        
        # Update the display
        self.display_manager.update_display()
        
        # Update scroll position
        self.scroll_position += self.scroll_speed
        
        # If we've scrolled past the end of the text, move to the next news item
        if self.scroll_position > text_width + self.display_manager.matrix.width:
            self.scroll_position = 0
            self.current_news_index = (self.current_news_index + 1) % len(all_news)
            
        # Add a small delay to control scroll speed
        time.sleep(self.scroll_delay)
        
        # Return True if we've displayed all news items
        return self.current_news_index == 0 and self.scroll_position == 0 