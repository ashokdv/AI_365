"""
Database module for storing and retrieving stock data.
Uses SQLite for local storage with automatic schema creation.
"""

import sqlite3
import json
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import os


class StockDatabase:
    """Database handler for stock market data."""
    
    def __init__(self, db_path: str = "stock_data.db"):
        """
        Initialize database connection and create tables if needed.
        
        Args:
            db_path (str): Path to SQLite database file
        """
        self.db_path = db_path
        self.conn = None
        self.connect()
        self.create_tables()
    
    def connect(self):
        """Create database connection."""
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row  # Enable column access by name
            self.conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign keys
        except Exception as e:
            print(f"Error connecting to database: {e}")
            raise
    
    def create_tables(self):
        """Create database tables if they don't exist."""
        try:
            cursor = self.conn.cursor()
            
            # Stock data table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS stock_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    price REAL NOT NULL,
                    change_amount REAL,
                    change_percent REAL,
                    volume INTEGER,
                    high REAL,
                    low REAL,
                    open_price REAL,
                    previous_close REAL,
                    market_cap REAL,
                    pe_ratio REAL,
                    data_source TEXT,
                    timestamp DATETIME NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Historical data table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS historical_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    date DATE NOT NULL,
                    open_price REAL NOT NULL,
                    high REAL NOT NULL,
                    low REAL NOT NULL,
                    close_price REAL NOT NULL,
                    volume INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(symbol, date)
                )
            """)
            
            # Fetch tracking table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS fetch_tracking (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL UNIQUE,
                    last_fetch_date DATETIME NOT NULL,
                    last_historical_date DATE,
                    fetch_count INTEGER DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Configuration table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS configuration (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT NOT NULL UNIQUE,
                    value TEXT NOT NULL,
                    description TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Market status table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS market_status (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE NOT NULL UNIQUE,
                    is_open BOOLEAN NOT NULL,
                    open_time TIME,
                    close_time TIME,
                    notes TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for better performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_stock_symbol_timestamp ON stock_data(symbol, timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_historical_symbol_date ON historical_data(symbol, date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_fetch_tracking_symbol ON fetch_tracking(symbol)")
            
            self.conn.commit()
            
            # Insert default configuration if not exists
            self._insert_default_config()
            
        except Exception as e:
            print(f"Error creating tables: {e}")
            raise
    
    def _insert_default_config(self):
        """Insert default configuration values."""
        default_configs = [
            ('default_fetch_days', '5', 'Default number of days to fetch historical data'),
            ('fetch_symbols', 'AAPL,GOOGL,MSFT,AMZN,TSLA,META,NVDA,NFLX,DIS,ORCL', 'Default symbols to fetch'),
            ('fetch_interval_minutes', '15', 'Interval between fetches in minutes'),
            ('max_retries', '3', 'Maximum retry attempts for failed API calls'),
            ('rate_limit_delay', '0.2', 'Delay between API calls in seconds'),
        ]
        
        cursor = self.conn.cursor()
        for key, value, description in default_configs:
            cursor.execute("""
                INSERT OR IGNORE INTO configuration (key, value, description)
                VALUES (?, ?, ?)
            """, (key, value, description))
        
        self.conn.commit()
    
    def store_stock_data(self, symbol: str, data: Dict):
        """
        Store real-time stock data.
        
        Args:
            symbol (str): Stock symbol
            data (Dict): Stock data dictionary
        """
        try:
            cursor = self.conn.cursor()
            
            cursor.execute("""
                INSERT INTO stock_data (
                    symbol, price, change_amount, change_percent, volume,
                    high, low, open_price, previous_close, data_source, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                symbol,
                data.get('price', 0),
                data.get('change', 0),
                data.get('change_percent', 0),
                data.get('volume', 0),
                data.get('high', 0),
                data.get('low', 0),
                data.get('open', 0),
                data.get('previous_close', 0),
                data.get('source', 'Unknown'),
                data.get('timestamp', datetime.now().isoformat())
            ))
            
            # Update fetch tracking
            self._update_fetch_tracking(symbol)
            
            self.conn.commit()
            
        except Exception as e:
            print(f"Error storing stock data for {symbol}: {e}")
            self.conn.rollback()
    
    def store_historical_data(self, symbol: str, df: pd.DataFrame):
        """
        Store historical data from DataFrame.
        
        Args:
            symbol (str): Stock symbol
            df (pd.DataFrame): Historical data with OHLCV columns
        """
        try:
            cursor = self.conn.cursor()
            
            for date, row in df.iterrows():
                cursor.execute("""
                    INSERT OR REPLACE INTO historical_data (
                        symbol, date, open_price, high, low, close_price, volume
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    symbol,
                    date.date(),
                    row.get('Open', 0),
                    row.get('High', 0),
                    row.get('Low', 0),
                    row.get('Close', 0),
                    row.get('Volume', 0)
                ))
            
            # Update last historical date
            if not df.empty:
                last_date = df.index[-1].date()
                cursor.execute("""
                    UPDATE fetch_tracking 
                    SET last_historical_date = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE symbol = ?
                """, (last_date, symbol))
            
            self.conn.commit()
            
        except Exception as e:
            print(f"Error storing historical data for {symbol}: {e}")
            self.conn.rollback()
    
    def _update_fetch_tracking(self, symbol: str):
        """Update fetch tracking information."""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO fetch_tracking (
                symbol, last_fetch_date, fetch_count, updated_at
            ) VALUES (
                ?, 
                CURRENT_TIMESTAMP,
                COALESCE((SELECT fetch_count FROM fetch_tracking WHERE symbol = ?), 0) + 1,
                CURRENT_TIMESTAMP
            )
        """, (symbol, symbol))
    
    def get_last_fetch_date(self, symbol: str) -> Optional[datetime]:
        """Get the last fetch date for a symbol."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT last_fetch_date FROM fetch_tracking WHERE symbol = ?
            """, (symbol,))
            
            result = cursor.fetchone()
            if result:
                return datetime.fromisoformat(result[0])
            return None
            
        except Exception as e:
            print(f"Error getting last fetch date for {symbol}: {e}")
            return None
    
    def get_last_historical_date(self, symbol: str) -> Optional[datetime]:
        """Get the last historical data date for a symbol."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT MAX(date) FROM historical_data WHERE symbol = ?
            """, (symbol,))
            
            result = cursor.fetchone()
            if result and result[0]:
                return datetime.strptime(result[0], '%Y-%m-%d')
            return None
            
        except Exception as e:
            print(f"Error getting last historical date for {symbol}: {e}")
            return None
    
    def get_symbols_to_fetch(self) -> List[str]:
        """Get symbols that need to be fetched based on configuration."""
        try:
            # Get symbols from configuration
            symbols_config = self.get_config_value('fetch_symbols', 'AAPL,GOOGL,MSFT')
            symbols = [s.strip() for s in symbols_config.split(',')]
            
            # Filter symbols that haven't been fetched recently
            fetch_interval = int(self.get_config_value('fetch_interval_minutes', '15'))
            cutoff_time = datetime.now() - timedelta(minutes=fetch_interval)
            
            symbols_to_fetch = []
            for symbol in symbols:
                last_fetch = self.get_last_fetch_date(symbol)
                if last_fetch is None or last_fetch < cutoff_time:
                    symbols_to_fetch.append(symbol)
            
            return symbols_to_fetch
            
        except Exception as e:
            print(f"Error getting symbols to fetch: {e}")
            return []
    
    def get_latest_stock_data(self, symbol: str) -> Optional[Dict]:
        """Get the latest stock data for a symbol."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT * FROM stock_data 
                WHERE symbol = ? 
                ORDER BY timestamp DESC 
                LIMIT 1
            """, (symbol,))
            
            result = cursor.fetchone()
            if result:
                return dict(result)
            return None
            
        except Exception as e:
            print(f"Error getting latest stock data for {symbol}: {e}")
            return None
    
    def get_historical_data(self, symbol: str, days: int = None) -> pd.DataFrame:
        """
        Get historical data for a symbol.
        
        Args:
            symbol (str): Stock symbol
            days (int): Number of days to retrieve (None for all data)
            
        Returns:
            pd.DataFrame: Historical data
        """
        try:
            cursor = self.conn.cursor()
            
            if days:
                start_date = (datetime.now() - timedelta(days=days)).date()
                cursor.execute("""
                    SELECT date, open_price, high, low, close_price, volume
                    FROM historical_data 
                    WHERE symbol = ? AND date >= ?
                    ORDER BY date
                """, (symbol, start_date))
            else:
                cursor.execute("""
                    SELECT date, open_price, high, low, close_price, volume
                    FROM historical_data 
                    WHERE symbol = ?
                    ORDER BY date
                """, (symbol,))
            
            results = cursor.fetchall()
            
            if results:
                df = pd.DataFrame(results, columns=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
                df['Date'] = pd.to_datetime(df['Date'])
                df.set_index('Date', inplace=True)
                return df
            else:
                return pd.DataFrame()
                
        except Exception as e:
            print(f"Error getting historical data for {symbol}: {e}")
            return pd.DataFrame()
    
    def get_config_value(self, key: str, default: str = None) -> str:
        """Get configuration value by key."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT value FROM configuration WHERE key = ?", (key,))
            
            result = cursor.fetchone()
            if result:
                return result[0]
            return default
            
        except Exception as e:
            print(f"Error getting config value for {key}: {e}")
            return default
    
    def set_config_value(self, key: str, value: str, description: str = None):
        """Set configuration value."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO configuration (key, value, description, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """, (key, value, description))
            
            self.conn.commit()
            
        except Exception as e:
            print(f"Error setting config value for {key}: {e}")
            self.conn.rollback()
    
    def get_fetch_statistics(self) -> Dict:
        """Get fetch statistics."""
        try:
            cursor = self.conn.cursor()
            
            # Total records
            cursor.execute("SELECT COUNT(*) FROM stock_data")
            total_records = cursor.fetchone()[0]
            
            # Unique symbols
            cursor.execute("SELECT COUNT(DISTINCT symbol) FROM stock_data")
            unique_symbols = cursor.fetchone()[0]
            
            # Last fetch times
            cursor.execute("""
                SELECT symbol, last_fetch_date, fetch_count 
                FROM fetch_tracking 
                ORDER BY last_fetch_date DESC
            """)
            fetch_info = cursor.fetchall()
            
            # Historical data coverage
            cursor.execute("""
                SELECT symbol, COUNT(*) as days_count, MIN(date) as start_date, MAX(date) as end_date
                FROM historical_data 
                GROUP BY symbol
            """)
            historical_info = cursor.fetchall()
            
            return {
                'total_records': total_records,
                'unique_symbols': unique_symbols,
                'fetch_tracking': [dict(row) for row in fetch_info],
                'historical_coverage': [dict(row) for row in historical_info]
            }
            
        except Exception as e:
            print(f"Error getting fetch statistics: {e}")
            return {}
    
    def cleanup_old_data(self, days_to_keep: int = 365):
        """Remove old stock data to manage database size."""
        try:
            cursor = self.conn.cursor()
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            cursor.execute("""
                DELETE FROM stock_data 
                WHERE timestamp < ?
            """, (cutoff_date.isoformat(),))
            
            deleted_count = cursor.rowcount
            self.conn.commit()
            
            print(f"Cleaned up {deleted_count} old records")
            return deleted_count
            
        except Exception as e:
            print(f"Error cleaning up old data: {e}")
            self.conn.rollback()
            return 0
    
    def export_data(self, symbol: str, format: str = 'json') -> str:
        """Export data for a symbol in specified format."""
        try:
            # Get all data for symbol
            stock_data = []
            cursor = self.conn.cursor()
            
            cursor.execute("""
                SELECT * FROM stock_data 
                WHERE symbol = ? 
                ORDER BY timestamp
            """, (symbol,))
            
            stock_records = [dict(row) for row in cursor.fetchall()]
            
            historical_df = self.get_historical_data(symbol)
            historical_records = historical_df.to_dict('records') if not historical_df.empty else []
            
            export_data = {
                'symbol': symbol,
                'real_time_data': stock_records,
                'historical_data': historical_records,
                'export_timestamp': datetime.now().isoformat()
            }
            
            if format == 'json':
                return json.dumps(export_data, indent=2, default=str)
            else:
                return str(export_data)
                
        except Exception as e:
            print(f"Error exporting data for {symbol}: {e}")
            return ""
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
    
    def __del__(self):
        """Destructor to ensure connection is closed."""
        self.close()
