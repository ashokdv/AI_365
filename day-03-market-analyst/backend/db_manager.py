"""
Database management for stock data - Simplified version for backend API.
"""

from database import StockDatabase
from stock_data import StockDataFetcher, DEFAULT_SYMBOLS
import json
from datetime import datetime


class DatabaseManager:
    """Simplified database management utility class."""
    
    def __init__(self, db_path: str = "stock_data.db"):
        self.db = StockDatabase(db_path)
        self.fetcher = StockDataFetcher(db_path=db_path)
    
    def get_config(self) -> dict:
        """Get current configuration."""
        config_keys = [
            'default_fetch_days',
            'fetch_symbols', 
            'fetch_interval_minutes',
            'max_retries',
            'rate_limit_delay'
        ]
        
        config = {}
        for key in config_keys:
            config[key] = self.db.get_config_value(key, 'Not set')
        
        return config
    
    def get_statistics(self) -> dict:
        """Get database statistics."""
        return self.db.get_fetch_statistics()
    
    def set_symbols(self, symbols: str) -> dict:
        """Set the symbols to fetch."""
        try:
            symbol_list = [s.strip().upper() for s in symbols.split(',')]
            validated_symbols = ','.join(symbol_list)
            
            self.db.set_config_value('fetch_symbols', validated_symbols, 'Configured symbols to fetch')
            return {'success': True, 'message': f'Symbols updated: {validated_symbols}'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def set_fetch_days(self, days: int) -> dict:
        """Set default fetch days."""
        try:
            if days < 1 or days > 365:
                return {'success': False, 'message': 'Days must be between 1 and 365'}
            
            self.db.set_config_value('default_fetch_days', str(days), 'Default number of days for historical data')
            return {'success': True, 'message': f'Default fetch days set to: {days}'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def fetch_data(self, force: bool = False) -> dict:
        """Trigger data fetch."""
        try:
            results = self.fetcher.bulk_fetch_and_store(force_fetch=force)
            
            success_count = 0
            error_count = 0
            details = []
            
            for symbol, data in results.items():
                if 'error' in data:
                    error_count += 1
                    details.append({'symbol': symbol, 'status': 'error', 'message': data['error']})
                else:
                    success_count += 1
                    price = data.get('price', 0)
                    change = data.get('change', 0)
                    details.append({
                        'symbol': symbol, 
                        'status': 'success', 
                        'price': price, 
                        'change': change
                    })
            
            return {
                'success': True,
                'summary': f'{success_count} successful, {error_count} errors',
                'success_count': success_count,
                'error_count': error_count,
                'details': details
            }
            
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def test_connectivity(self) -> dict:
        """Test API connectivity."""
        try:
            test_symbols = ['AAPL', 'GOOGL']
            results = []
            
            for symbol in test_symbols:
                try:
                    data = self.fetcher.get_real_time_price(symbol, store_in_db=False)
                    if 'error' not in data:
                        results.append({
                            'symbol': symbol,
                            'status': 'success',
                            'price': data['price'],
                            'source': data['source']
                        })
                    else:
                        results.append({
                            'symbol': symbol,
                            'status': 'error',
                            'message': data['error']
                        })
                except Exception as e:
                    results.append({
                        'symbol': symbol,
                        'status': 'error',
                        'message': str(e)
                    })
            
            return {'success': True, 'results': results}
            
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def export_data(self, symbol: str) -> dict:
        """Export data for a symbol."""
        try:
            data = self.db.export_data(symbol, 'json')
            filename = f"{symbol}_export_{int(datetime.now().timestamp())}.json"
            
            with open(filename, 'w') as f:
                f.write(data)
            
            return {'success': True, 'filename': filename, 'data': json.loads(data)}
            
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def cleanup_data(self, days: int = 30) -> dict:
        """Clean up old data."""
        try:
            deleted_count = self.db.cleanup_old_data(days)
            return {
                'success': True, 
                'message': f'Cleaned up {deleted_count} old records (older than {days} days)',
                'deleted_count': deleted_count
            }
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def get_stock_data(self, symbol: str, days: int = None) -> dict:
        """Get stock data for a specific symbol."""
        try:
            # Get latest real-time data
            latest_data = self.db.get_latest_stock_data(symbol)
            
            # Get historical data
            if days is None:
                days = int(self.db.get_config_value('default_fetch_days', '30'))
            
            historical_data = self.db.get_historical_data(symbol, days)
            
            return {
                'success': True,
                'symbol': symbol,
                'latest_data': latest_data,
                'historical_data': historical_data.to_dict('records') if not historical_data.empty else [],
                'dates': historical_data.index.strftime('%Y-%m-%d').tolist() if not historical_data.empty else []
            }
            
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def close(self):
        """Close database connections."""
        self.fetcher.close()
        self.db.close()
