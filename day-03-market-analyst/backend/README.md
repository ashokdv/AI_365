# 🤖 Stock Analysis Chatbot Backend (FastAPI)

A comprehensive stock analysis API built with FastAPI that combines real-time data, technical indicators, news sentiment analysis, and AI-powered investment recommendations.

## 🚀 Features

- **Real-time Stock Data**: Fetches current prices from Yahoo Finance and Alpha Vantage APIs
- **Technical Analysis**: RSI, MACD, Bollinger Bands, and other indicators
- **News Sentiment Analysis**: Analyzes Google News articles for sentiment impact
- **AI Recommendations**: Buy/Sell/Hold recommendations with confidence scores
- **Database Storage**: SQLite database for persistent data storage
- **FastAPI Framework**: High-performance API with automatic documentation
- **Interactive Testing**: Built-in Swagger UI and ReDoc documentation

## 📁 Project Structure

```
backend/
├── chatbot_api.py          # Main FastAPI server
├── stock_data.py           # Stock data fetching and processing
├── database.py             # SQLite database operations
├── news_fetcher.py         # Google News RSS feed analysis
├── ai_analyzer.py          # Technical analysis and AI recommendations
├── db_manager.py           # Database management utilities
├── test_api.py            # API testing script
├── start_chatbot.bat      # Windows startup script
├── requirements.txt        # Python dependencies
├── stock_data.db          # SQLite database (created automatically)
└── README.md              # This file
```

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.8+
- Internet connection for API access

### Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### Run the FastAPI Server
```bash
python chatbot_api.py
```

Or use the convenient startup script:
```bash
start_chatbot.bat
```

The API will be available at: http://localhost:8000

## 📊 API Documentation

FastAPI provides automatic interactive documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## 🔗 API Endpoints

### 1. Stock Analysis
**POST /analyze**
```json
{
  "symbol": "AAPL",
  "days": 30
}
```
**Returns**: Comprehensive stock analysis with recommendation

### 2. Chat Interface
**POST /chat**
```json
{
  "message": "Should I buy Apple stock?"
}
```
**Returns**: Conversational response with analysis

### 3. Stock Data
**GET /stocks/{symbol}**
**Returns**: Basic stock data and historical prices

### 4. News Sentiment
**GET /news/{symbol}**
**Returns**: News articles with sentiment analysis

### 5. Health Check
**GET /health**
**Returns**: API status and component health

## 💡 Usage Examples

### Test via Swagger UI
1. Open http://localhost:8000/docs in your browser
2. Click on any endpoint to expand it
3. Click "Try it out" button
4. Enter parameters and click "Execute"

### Test via Command Line
```bash
# Health check
curl http://localhost:8000/health

# Analyze Apple stock
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"symbol": "AAPL", "days": 30}'

# Chat query
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Should I buy Tesla stock?"}'
```

### Test via Python
```python
import requests

# Analyze a stock
response = requests.post('http://localhost:8000/analyze', 
                        json={'symbol': 'AAPL', 'days': 30})
result = response.json()
print(f"Recommendation: {result['recommendation']}")
print(f"Confidence: {result['confidence']:.1f}%")
```

## 🔧 Configuration

The system uses these default configurations (stored in SQLite):

- **Default fetch days**: 5 days of historical data
- **Supported symbols**: AAPL, GOOGL, MSFT, AMZN, TSLA, META, NVDA, NFLX, AMD, INTC
- **Rate limiting**: 1-second delay between API calls
- **Max retries**: 3 attempts per API call

## 🧪 Technical Analysis Features

### Technical Indicators
- **RSI (Relative Strength Index)**: Identifies overbought/oversold conditions
- **MACD (Moving Average Convergence Divergence)**: Trend momentum indicator
- **Bollinger Bands**: Price volatility and support/resistance levels
- **Moving Averages**: Short-term and long-term trend analysis

### AI Recommendation Engine
- **Buy Signals**: Strong bullish indicators across multiple metrics
- **Sell Signals**: Bearish indicators suggesting profit-taking
- **Hold Signals**: Mixed or neutral indicators
- **Confidence Scoring**: 0-100% confidence based on signal strength

## 📰 News Sentiment Analysis

### News Sources
- Google News RSS feeds
- Real-time article collection
- Multiple news outlets aggregation

### Sentiment Processing
- Keyword-based sentiment analysis
- Positive/negative sentiment scoring
- Impact assessment on stock recommendations
- Article relevance filtering

## 💾 Database Schema

### Tables
- **stock_data**: Real-time price data
- **historical_data**: Historical price information
- **fetch_tracking**: API call tracking and rate limiting
- **configuration**: System settings and parameters

### Features
- Automatic schema creation
- Data deduplication
- Configurable retention policies
- Export capabilities

## 🔍 Error Handling

FastAPI provides excellent error handling with:

- **Automatic Validation**: Pydantic models validate request/response data
- **HTTP Exception Handling**: Proper status codes and error messages
- **API Failures**: Automatic fallback between data sources
- **Rate Limiting**: Built-in delays and retry mechanisms
- **Graceful Degradation**: Partial results when some components fail

## 🚦 Status Codes

- **200**: Success
- **400**: Bad Request (invalid input)
- **404**: Endpoint not found
- **422**: Validation Error
- **500**: Internal server error

## 📈 FastAPI Advantages

- **High Performance**: Built on Starlette and Pydantic for speed
- **Automatic Documentation**: Interactive API docs generated automatically
- **Type Hints**: Full Python type hint support
- **Modern Python**: Uses latest Python features (3.8+)
- **Standards-based**: Based on OpenAPI and JSON Schema
- **Async Support**: Native async/await support for better performance

## 🔒 Security Considerations

- **Input Validation**: Pydantic models ensure data integrity
- **CORS Configuration**: Configurable cross-origin access
- **Error Masking**: Internal errors don't expose sensitive information
- **Rate Limiting**: Built-in protection against API abuse

## 🚀 Future Enhancements

- WebSocket support for real-time updates
- Authentication and authorization
- API rate limiting with Redis
- Containerization with Docker
- More technical indicators (Stochastic, Williams %R)
- Machine learning model integration
- Multi-timeframe analysis
- Portfolio tracking capabilities

## 🐛 Troubleshooting

### Common Issues

1. **API Not Starting**
   ```bash
   # Check dependencies
   pip install -r requirements.txt
   
   # Verify Python version
   python --version  # Should be 3.8+
   ```

2. **Port Already in Use**
   ```bash
   # Check what's using port 8000
   netstat -ano | findstr :8000
   
   # Kill the process if needed
   taskkill /PID <process_id> /F
   ```

3. **Database Errors**
   ```bash
   # Delete and recreate database
   del stock_data.db
   python chatbot_api.py
   ```

4. **Import Errors**
   ```bash
   # Ensure you're in the correct directory
   cd backend
   python chatbot_api.py
   ```

### Logs and Debugging
- Server logs are displayed in the terminal with timestamp
- Uvicorn provides detailed request logs
- Check the Swagger UI for endpoint testing
- Enable debug mode for detailed error traces

## 📞 Support

For issues or questions:
1. Check the troubleshooting section above
2. Review server logs for error messages
3. Test individual endpoints using Swagger UI at http://localhost:8000/docs
4. Verify all dependencies are installed correctly

## 📦 Dependencies

- **FastAPI**: Modern, fast web framework
- **Uvicorn**: ASGI server for running FastAPI
- **Pydantic**: Data validation using Python type hints
- **Pandas**: Data manipulation and analysis
- **Requests**: HTTP library for API calls
- **BeautifulSoup4**: Web scraping for news
- **NumPy**: Numerical computing

---

**Made with ❤️ for intelligent stock analysis using FastAPI**
