import requests
import json
import time
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
import pandas as pd
from database import StockDatabase


# Configuration constants
ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')
RATE_LIMIT_DELAY = 0.2
REQUEST_TIMEOUT = 30
DEFAULT_FETCH_DAYS = 5

# Default symbols to track
DEFAULT_SYMBOLS = [
    'AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 
    'META', 'NVDA', 'NFLX', 'DIS', 'ORCL'
]


class StockDataFetcher:
    """
    A class to fetch real-time stock data from various free APIs.
    Uses Alpha Vantage as primary source with fallback options.
    """
    
    def __init__(self, api_key: Optional[str] = None, db_path: str = "stock_data.db"):
        """
        Initialize the StockDataFetcher.
        
        Args:
            api_key (str, optional): Alpha Vantage API key. Get free key from https://www.alphavantage.co/support/#api-key
            db_path (str): Path to SQLite database file
        """
        self.api_key = api_key
        self.base_url_alpha = "https://www.alphavantage.co/query"
        self.base_url_finnhub = "https://finnhub.io/api/v1"
        self.base_url_polygon = "https://api.polygon.io/v2"
        
        # Initialize database
        self.db = StockDatabase(db_path)
        
        # Session for connection pooling
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Stock-Data-Fetcher/1.0'
        })
        
    def get_real_time_price(self, symbol: str, store_in_db: bool = True) -> Dict:
        """
        Get real-time stock price for a given symbol.
        
        Args:
            symbol (str): Stock symbol (e.g., 'AAPL', 'GOOGL')
            store_in_db (bool): Whether to store the data in database
            
        Returns:
            Dict: Stock price information
        """
        try:
            # Try Alpha Vantage first if API key is available
            if self.api_key:
                data = self._get_price_alpha_vantage(symbol)
            else:
                # Use free APIs
                data = self._get_price_free_api(symbol)
            
            # Store in database if requested and data is valid
            if store_in_db and 'error' not in data:
                self.db.store_stock_data(symbol, data)
            
            return data
            
        except Exception as e:
            return {
                'symbol': symbol,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _get_price_alpha_vantage(self, symbol: str) -> Dict:
        """Get stock price from Alpha Vantage API."""
        params = {
            'function': 'GLOBAL_QUOTE',
            'symbol': symbol,
            'apikey': self.api_key
        }
        
        response = self.session.get(self.base_url_alpha, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        if 'Global Quote' in data:
            quote = data['Global Quote']
            
            # Alpha Vantage provides last trading day, use it if available
            last_trading_day = quote.get('07. latest trading day')
            if last_trading_day:
                # Combine date with current time (Alpha Vantage doesn't provide exact time)
                timestamp = f"{last_trading_day}T{datetime.now().time().isoformat()}"
            else:
                timestamp = datetime.now().isoformat()
            
            return {
                'symbol': symbol,
                'price': float(quote.get('05. price', 0)),
                'change': float(quote.get('09. change', 0)),
                'change_percent': quote.get('10. change percent', '0%').strip('%'),
                'volume': int(quote.get('06. volume', 0)),
                'high': float(quote.get('03. high', 0)),
                'low': float(quote.get('04. low', 0)),
                'open': float(quote.get('02. open', 0)),
                'previous_close': float(quote.get('08. previous close', 0)),
                'timestamp': timestamp,
                'last_trading_day': last_trading_day,
                'source': 'Alpha Vantage'
            }
        else:
            raise Exception(f"No data found for symbol {symbol}")
    
    def _get_price_free_api(self, symbol: str) -> Dict:
        """Get stock price from free APIs."""
        try:
            # Try Yahoo Finance alternative endpoint
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if 'chart' in data and data['chart']['result']:
                result = data['chart']['result'][0]
                meta = result['meta']
                
                # Use market timestamp if available, otherwise current time
                market_timestamp = meta.get('regularMarketTime')
                if market_timestamp:
                    timestamp = datetime.fromtimestamp(market_timestamp).isoformat()
                else:
                    timestamp = datetime.now().isoformat()
                
                return {
                    'symbol': symbol,
                    'price': meta.get('regularMarketPrice', 0),
                    'change': meta.get('regularMarketPrice', 0) - meta.get('previousClose', 0),
                    'change_percent': ((meta.get('regularMarketPrice', 0) - meta.get('previousClose', 0)) / meta.get('previousClose', 1)) * 100,
                    'volume': meta.get('regularMarketVolume', 0),
                    'high': meta.get('regularMarketDayHigh', 0),
                    'low': meta.get('regularMarketDayLow', 0),
                    'open': meta.get('regularMarketDayOpen', 0),
                    'previous_close': meta.get('previousClose', 0),
                    'timestamp': timestamp,
                    'market_timestamp': market_timestamp,
                    'source': 'Yahoo Finance'
                }
            else:
                raise Exception(f"No data found for symbol {symbol}")
                
        except Exception as e:
            # Return error if no real data available
            raise Exception(f"Failed to fetch real-time data for {symbol}: {str(e)}")
    
    def get_multiple_stocks(self, symbols: List[str] = None, store_in_db: bool = True) -> Dict[str, Dict]:
        """
        Get real-time data for multiple stocks.
        
        Args:
            symbols (List[str], optional): List of stock symbols. If None, uses configured symbols
            store_in_db (bool): Whether to store data in database
            
        Returns:
            Dict[str, Dict]: Dictionary with symbol as key and stock data as value
        """
        if symbols is None:
            symbols = self.db.get_symbols_to_fetch()
        
        results = {}
        rate_limit_delay = float(self.db.get_config_value('rate_limit_delay', '0.2'))
        
        for symbol in symbols:
            try:
                results[symbol] = self.get_real_time_price(symbol, store_in_db)
                # Add delay to avoid rate limiting
                time.sleep(rate_limit_delay)
            except Exception as e:
                results[symbol] = {
                    'symbol': symbol,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }
        
        return results
    
    def get_historical_data(self, symbol: str, period: str = None, force_fetch: bool = False) -> pd.DataFrame:
        """
        Get historical stock data with database integration.
        
        Args:
            symbol (str): Stock symbol
            period (str): Time period ('1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max')
            force_fetch (bool): Force fetch from API even if data exists in DB
            
        Returns:
            pd.DataFrame: Historical stock data
        """
        if period is None:
            period = f"{self.db.get_config_value('default_fetch_days', '5')}d"
        
        try:
            # Check if we have recent data in database unless force_fetch is True
            if not force_fetch:
                days = self._period_to_days(period)
                db_data = self.db.get_historical_data(symbol, days)
                
                # If we have sufficient recent data, return it
                if not db_data.empty:
                    last_date = self.db.get_last_historical_date(symbol)
                    if last_date and (datetime.now() - last_date).days < 1:
                        return db_data
            
            # Fetch new data from API
            if self.api_key:
                df = self._get_historical_alpha_vantage(symbol, period)
            else:
                df = self._get_historical_free_api(symbol, period)
            
            # Store in database
            if not df.empty:
                self.db.store_historical_data(symbol, df)
            
            return df
            
        except Exception as e:
            # Try to get data from database as fallback
            days = self._period_to_days(period)
            db_data = self.db.get_historical_data(symbol, days)
            
            if not db_data.empty:
                print(f"Warning: Using cached data for {symbol} due to API error: {e}")
                return db_data
            else:
                raise Exception(f"No historical data available for {symbol}: {e}")
    
    def _period_to_days(self, period: str) -> int:
        """Convert period string to number of days."""
        period_map = {
            '1d': 1, '5d': 5, '1mo': 30, '3mo': 90,
            '6mo': 180, '1y': 365, '2y': 730, '5y': 1825, '10y': 3650
        }
        return period_map.get(period, 30)
    
    def _get_historical_alpha_vantage(self, symbol: str, period: str) -> pd.DataFrame:
        """Get historical data from Alpha Vantage."""
        params = {
            'function': 'TIME_SERIES_DAILY',
            'symbol': symbol,
            'apikey': self.api_key,
            'outputsize': 'full'
        }
        
        response = self.session.get(self.base_url_alpha, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        if 'Time Series (Daily)' in data:
            time_series = data['Time Series (Daily)']
            df = pd.DataFrame.from_dict(time_series, orient='index')
            df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            df.index = pd.to_datetime(df.index)
            df = df.astype(float)
            df = df.sort_index()
            
            # Filter by period
            if period != 'max':
                days_map = {
                    '1d': 1, '5d': 5, '1mo': 30, '3mo': 90,
                    '6mo': 180, '1y': 365, '2y': 730, '5y': 1825, '10y': 3650
                }
                days = days_map.get(period, 30)
                start_date = datetime.now() - timedelta(days=days)
                df = df[df.index >= start_date]
            
            return df
        else:
            raise Exception(f"No historical data found for {symbol}")
    
    def _get_historical_free_api(self, symbol: str, period: str) -> pd.DataFrame:
        """Get historical data from free API."""
        try:
            # Try Yahoo Finance historical data endpoint
            # Calculate date range
            end_date = datetime.now()
            days = self._period_to_days(period)
            start_date = end_date - timedelta(days=days)
            
            start_timestamp = int(start_date.timestamp())
            end_timestamp = int(end_date.timestamp())
            
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
            params = {
                'period1': start_timestamp,
                'period2': end_timestamp,
                'interval': '1d',
                'includePrePost': 'false'
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if 'chart' in data and data['chart']['result'] and data['chart']['result'][0]['timestamp']:
                result = data['chart']['result'][0]
                timestamps = result['timestamp']
                indicators = result['indicators']['quote'][0]
                
                # Create DataFrame
                df_data = []
                for i, timestamp in enumerate(timestamps):
                    date = datetime.fromtimestamp(timestamp)
                    df_data.append({
                        'Open': indicators['open'][i] or 0,
                        'High': indicators['high'][i] or 0,
                        'Low': indicators['low'][i] or 0,
                        'Close': indicators['close'][i] or 0,
                        'Volume': indicators['volume'][i] or 0
                    })
                
                df = pd.DataFrame(df_data, index=pd.to_datetime([datetime.fromtimestamp(ts) for ts in timestamps]))
                return df
            else:
                raise Exception(f"No historical data found for {symbol}")
                
        except Exception as e:
            raise Exception(f"Failed to fetch historical data for {symbol}: {str(e)}")
    
    def close(self):
        """Close the session and database connection."""
        self.session.close()
        self.db.close()
    
    def get_database_stats(self) -> Dict:
        """Get database statistics."""
        return self.db.get_fetch_statistics()
    
    def configure_fetch_settings(self, **kwargs):
        """Configure fetch settings in database."""
        for key, value in kwargs.items():
            self.db.set_config_value(key, str(value))
    
    def get_cached_data(self, symbol: str) -> Optional[Dict]:
        """Get latest cached data for a symbol."""
        return self.db.get_latest_stock_data(symbol)
    
    def bulk_fetch_and_store(self, force_fetch: bool = False) -> Dict:
        """Fetch and store data for all configured symbols."""
        symbols = self.db.get_symbols_to_fetch()
        
        if force_fetch:
            # Get all configured symbols regardless of last fetch time
            symbols_config = self.db.get_config_value('fetch_symbols', 'AAPL,GOOGL,MSFT')
            symbols = [s.strip() for s in symbols_config.split(',')]
        
        results = self.get_multiple_stocks(symbols, store_in_db=True)
        
        # Also fetch historical data if needed
        default_days = int(self.db.get_config_value('default_fetch_days', '5'))
        for symbol in symbols:
            if 'error' not in results.get(symbol, {}):
                try:
                    self.get_historical_data(symbol, f"{default_days}d", force_fetch=force_fetch)
                except Exception as e:
                    print(f"Warning: Could not fetch historical data for {symbol}: {e}")
        
        return results
    
    def get_market_status(self) -> Dict:
        """
        Get current market status.
        
        Returns:
            Dict: Market status information
        """
        now = datetime.now()
        
        # Simple market hours check (US market: 9:30 AM - 4:00 PM ET)
        market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
        market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
        
        is_weekday = now.weekday() < 5  # Monday = 0, Sunday = 6
        is_market_hours = market_open <= now <= market_close
        
        is_open = is_weekday and is_market_hours
        
        return {
            'is_open': is_open,
            'current_time': now.isoformat(),
            'market_open': market_open.time().isoformat(),
            'market_close': market_close.time().isoformat(),
            'next_open': self._get_next_market_open().isoformat() if not is_open else None,
            'timezone': 'ET'
        }
    
    def _get_next_market_open(self) -> datetime:
        """Calculate next market open time."""
        now = datetime.now()
        
        # If it's before market open today and it's a weekday
        if now.time() < datetime.now().replace(hour=9, minute=30).time() and now.weekday() < 5:
            return now.replace(hour=9, minute=30, second=0, microsecond=0)
        
        # Otherwise, next weekday
        days_ahead = 1
        while (now + timedelta(days=days_ahead)).weekday() >= 5:  # Skip weekends
            days_ahead += 1
        
        next_day = now + timedelta(days=days_ahead)
        return next_day.replace(hour=9, minute=30, second=0, microsecond=0)
    
    def close(self):
        """Close the session."""
        self.session.close()


# Example usage and utility functions
def format_price_change(change: float, change_percent: float) -> str:
    """Format price change with appropriate signs and colors."""
    sign = "+" if change >= 0 else ""
    return f"{sign}{change:.2f} ({sign}{change_percent:.2f}%)"


def is_trading_hours() -> bool:
    """Check if it's currently trading hours."""
    fetcher = StockDataFetcher()
    status = fetcher.get_market_status()
    fetcher.close()
    return status['is_open']
