"""
Simple API service for stock data using Flask.
Run this to create a REST API for stock data.
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from stock_data import StockDataFetcher, format_price_change, is_trading_hours, DEFAULT_SYMBOLS
from database import StockDatabase
import json
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend integration

# Market indices
MARKET_INDICES = {
    'S&P 500': '^GSPC',
    'Dow Jones': '^DJI',
    'NASDAQ': '^IXIC',
    'Russell 2000': '^RUT',
    'VIX': '^VIX'
}

# Global stock data fetcher instance
fetcher = StockDataFetcher()


@app.route('/')
def home():
    """Home endpoint with API information."""
    return jsonify({
        'message': 'Stock Data API',
        'version': '1.0',
        'endpoints': [
            '/api/stock/<symbol>',
            '/api/stocks',
            '/api/market-status',
            '/api/historical/<symbol>',
            '/api/indices',
            '/api/popular-stocks'
        ]
    })


@app.route('/api/stock/<symbol>')
def get_stock_data(symbol):
    """Get real-time data for a single stock."""
    try:
        symbol = symbol.upper()
        data = fetcher.get_real_time_price(symbol)
        
        if 'error' in data:
            return jsonify({'error': data['error']}), 400
        
        return jsonify(data)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/stocks')
def get_multiple_stocks():
    """Get data for multiple stocks from query parameters."""
    try:
        symbols_param = request.args.get('symbols', '')
        
        if not symbols_param:
            return jsonify({'error': 'No symbols provided. Use ?symbols=AAPL,GOOGL,MSFT'}), 400
        
        symbols = [s.strip().upper() for s in symbols_param.split(',')]
        
        if len(symbols) > 20:  # Limit to prevent abuse
            return jsonify({'error': 'Too many symbols. Maximum 20 allowed.'}), 400
        
        data = fetcher.get_multiple_stocks(symbols)
        return jsonify(data)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/market-status')
def get_market_status():
    """Get current market status."""
    try:
        status = fetcher.get_market_status()
        return jsonify(status)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/historical/<symbol>')
def get_historical_data(symbol):
    """Get historical data for a stock."""
    try:
        symbol = symbol.upper()
        period = request.args.get('period', '1mo')
        
        # Validate period
        valid_periods = ['1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'max']
        if period not in valid_periods:
            return jsonify({'error': f'Invalid period. Valid options: {valid_periods}'}), 400
        
        df = fetcher.get_historical_data(symbol, period)
        
        # Convert DataFrame to JSON-friendly format
        data = {
            'symbol': symbol,
            'period': period,
            'data': df.to_dict('records'),
            'dates': [date.isoformat() for date in df.index],
            'summary': {
                'total_days': len(df),
                'start_date': df.index[0].isoformat(),
                'end_date': df.index[-1].isoformat(),
                'latest_close': float(df['Close'].iloc[-1]),
                'period_high': float(df['High'].max()),
                'period_low': float(df['Low'].min()),
                'average_volume': float(df['Volume'].mean())
            }
        }
        
        return jsonify(data)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/indices')
def get_market_indices():
    """Get data for major market indices."""
    try:
        indices_data = {}
        
        for name, symbol in MARKET_INDICES.items():
            data = fetcher.get_real_time_price(symbol)
            if 'error' not in data:
                indices_data[name] = data
            else:
                indices_data[name] = {'error': data['error']}
        
        return jsonify(indices_data)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/popular-stocks')
def get_popular_stocks():
    """Get data for popular stocks."""
    try:
        limit = request.args.get('limit', 10)
        try:
            limit = int(limit)
            limit = min(limit, 20)  # Maximum 20 stocks
        except ValueError:
            limit = 10
        
        symbols = DEFAULT_SYMBOLS[:limit]
        data = fetcher.get_multiple_stocks(symbols)
        
        return jsonify(data)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/search')
def search_stock():
    """Simple stock search (returns available symbols)."""
    try:
        query = request.args.get('q', '').upper()
        
        if len(query) < 1:
            return jsonify({'error': 'Query too short'}), 400
        
        # Simple search in default symbols
        matches = [stock for stock in DEFAULT_SYMBOLS if query in stock]
        
        # Also search in indices
        index_matches = [symbol for name, symbol in MARKET_INDICES.items() 
                        if query in symbol.upper() or query in name.upper()]
        
        results = {
            'query': query,
            'stocks': matches,
            'indices': index_matches,
            'total': len(matches) + len(index_matches)
        }
        
        return jsonify(results)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/watchlist', methods=['POST'])
def create_watchlist():
    """Create a watchlist and get data for all symbols."""
    try:
        data = request.get_json()
        
        if not data or 'symbols' not in data:
            return jsonify({'error': 'No symbols provided in request body'}), 400
        
        symbols = [s.strip().upper() for s in data['symbols']]
        
        if len(symbols) > 20:
            return jsonify({'error': 'Too many symbols. Maximum 20 allowed.'}), 400
        
        watchlist_data = fetcher.get_multiple_stocks(symbols)
        
        # Calculate portfolio summary if shares are provided
        portfolio_summary = None
        if 'shares' in data:
            shares_dict = data['shares']
            total_value = 0
            total_change = 0
            
            for symbol in symbols:
                if symbol in watchlist_data and 'error' not in watchlist_data[symbol]:
                    shares = shares_dict.get(symbol, 0)
                    price = watchlist_data[symbol]['price']
                    change = watchlist_data[symbol]['change']
                    
                    position_value = price * shares
                    position_change = change * shares
                    
                    total_value += position_value
                    total_change += position_change
            
            portfolio_summary = {
                'total_value': round(total_value, 2),
                'total_change': round(total_change, 2),
                'total_change_percent': round((total_change / (total_value - total_change)) * 100, 2) if total_value != total_change else 0
            }
        
        result = {
            'watchlist': watchlist_data,
            'portfolio_summary': portfolio_summary,
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    print("🚀 Starting Stock Data API Server...")
    print("📊 Available endpoints:")
    print("   GET  /")
    print("   GET  /api/stock/<symbol>")
    print("   GET  /api/stocks?symbols=AAPL,GOOGL,MSFT")
    print("   GET  /api/market-status")
    print("   GET  /api/historical/<symbol>?period=1mo")
    print("   GET  /api/indices")
    print("   GET  /api/popular-stocks?limit=10")
    print("   GET  /api/search?q=AAPL")
    print("   POST /api/watchlist")
    print("")
    print("🌐 Server running on: http://localhost:5000")
    print("📝 Use Ctrl+C to stop the server")
    
    try:
        app.run(debug=True, host='0.0.0.0', port=5000)
    finally:
        fetcher.close()
