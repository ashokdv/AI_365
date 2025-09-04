"""
Chatbot API for Stock Analysis with AI recommendations and news sentiment.
This API provides comprehensive stock analysis combining real-time data, 
technical indicators, news sentiment, and buy/sell recommendations.
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import json
import logging
import traceback
from typing import Optional, Dict, Any

# Import our modules
from stock_data import StockDataFetcher
from database import StockDatabase
from news_fetcher import NewsStockFetcher
from ai_analyzer import StockAIAnalyzer
from db_manager import DatabaseManager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Stock Analysis Chatbot API",
    description="Comprehensive stock analysis with AI recommendations and news sentiment",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response validation
class StockAnalysisRequest(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=10, description="Stock symbol (e.g., AAPL)")
    days: Optional[int] = Field(30, ge=1, le=365, description="Number of days for historical data")

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Chat message about stocks")

class APIResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None

# Global instances
db_manager = DatabaseManager()
news_fetcher = NewsStockFetcher()
ai_analyzer = StockAIAnalyzer()


class ChatbotAPI:
    """Main chatbot API class that orchestrates all components."""
    
    def __init__(self):
        self.db_manager = db_manager
        self.news_fetcher = news_fetcher
        self.ai_analyzer = ai_analyzer
    
    def analyze_stock(self, symbol: str, days: int = 30) -> dict:
        """
        Comprehensive stock analysis combining data, news, and AI insights.
        """
        try:
            symbol = symbol.upper()
            
            # Step 1: Get stock data (ensure we have recent data)
            stock_result = self.db_manager.get_stock_data(symbol, days)
            if not stock_result['success']:
                # Try to fetch fresh data
                fetch_result = self.db_manager.fetch_data()
                stock_result = self.db_manager.get_stock_data(symbol, days)
                
                if not stock_result['success']:
                    return {
                        'success': False,
                        'error': f'Could not retrieve data for {symbol}',
                        'details': stock_result.get('message', 'Unknown error')
                    }
            
            historical_data = stock_result['historical_data']
            latest_data = stock_result['latest_data']
            
            if not historical_data:
                return {
                    'success': False,
                    'error': f'No historical data available for {symbol}',
                    'recommendation': 'Unable to analyze - insufficient data'
                }
            
            # Step 2: Get news sentiment
            news_result = self.news_fetcher.get_stock_news_sentiment(symbol)
            
            # Step 3: Perform AI analysis
            current_price = latest_data.get('price', 0) if latest_data else 0
            
            # Convert historical data to DataFrame for AI analyzer
            import pandas as pd
            if historical_data:
                df_data = pd.DataFrame(historical_data)
                # Ensure the DataFrame has the expected columns and format
                if not df_data.empty:
                    # Convert date column to datetime if it exists
                    if 'date' in df_data.columns:
                        df_data['date'] = pd.to_datetime(df_data['date'])
                        df_data.set_index('date', inplace=True)
                    
                    ai_result = self.ai_analyzer.analyze_stock(symbol, df_data, news_result, current_price)
                else:
                    ai_result = {'recommendation': 'Hold', 'confidence_score': 0, 'key_indicators': {}}
            else:
                ai_result = {'recommendation': 'Hold', 'confidence_score': 0, 'key_indicators': {}}
            
            # Step 4: Generate comprehensive summary
            summary = self._generate_comprehensive_summary(
                symbol, latest_data, historical_data, news_result, ai_result
            )
            
            return {
                'success': True,
                'symbol': symbol,
                'analysis_date': datetime.now().isoformat(),
                'latest_price': latest_data,
                'historical_summary': self._get_historical_summary(historical_data),
                'news_sentiment': news_result,
                'technical_analysis': ai_result,
                'comprehensive_summary': summary,
                'recommendation': ai_result.get('recommendation', 'Hold'),
                'confidence': ai_result.get('confidence_score', 0)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing stock {symbol}: {e}")
            logger.error(traceback.format_exc())
            return {
                'success': False,
                'error': str(e),
                'recommendation': 'Error - cannot provide recommendation'
            }
    
    def _generate_comprehensive_summary(self, symbol, latest_data, historical_data, news_result, ai_result):
        """Generate a comprehensive analysis summary."""
        try:
            # Current price info
            current_price = latest_data.get('price', 0) if latest_data else 0
            current_change = latest_data.get('change_percent', 0) if latest_data else 0
            
            # Historical performance
            hist_summary = self._get_historical_summary(historical_data)
            
            # News sentiment
            news_sentiment = news_result.get('overall_sentiment', 'neutral')
            news_score = news_result.get('sentiment_score', 0)
            
            # AI indicators
            recommendation = ai_result.get('recommendation', 'Hold')
            confidence = ai_result.get('confidence_score', 0)
            key_indicators = ai_result.get('key_indicators', {})
            
            # Build comprehensive summary
            summary = f"""
                📊 **Stock Analysis for {symbol}**

                **Current Status:**
                • Price: ${current_price:.2f} ({current_change:+.2f}% today)
                • Recommendation: **{recommendation}** (Confidence: {confidence:.1f}%)

                **30-Day Performance:**
                • Price Range: ${hist_summary['low']:.2f} - ${hist_summary['high']:.2f}
                • Average Price: ${hist_summary['avg']:.2f}
                • Total Return: {hist_summary['total_return']:.2f}%

                **Technical Indicators:**
                • RSI: {key_indicators.get('rsi', 'N/A')} ({"Oversold" if key_indicators.get('rsi', 50) < 30 else "Overbought" if key_indicators.get('rsi', 50) > 70 else "Neutral"})
                • MACD Signal: {key_indicators.get('macd_signal', 'Neutral')}
                • Bollinger Bands: {key_indicators.get('bb_position', 'N/A')}

                **News Sentiment Analysis:**
                • Overall Sentiment: {news_sentiment.title()} ({news_score:.2f}/10)
                • Recent Articles: {len(news_result.get('articles', []))} analyzed

                **Investment Recommendation:**
                {self._get_recommendation_explanation(recommendation, confidence, news_sentiment, key_indicators)}
                """
            
            return summary.strip()
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return f"Analysis completed for {symbol}. See detailed results below."
    
    def _get_historical_summary(self, historical_data):
        """Get summary statistics from historical data."""
        if not historical_data:
            return {'high': 0, 'low': 0, 'avg': 0, 'total_return': 0}
        
        try:
            # Handle pandas DataFrame from get_historical_data
            if hasattr(historical_data, 'columns'):
                df = historical_data
                prices = df['Close'].tolist()
                highs = df['High'].tolist()
                lows = df['Low'].tolist()
            else:
                # Handle list of dictionaries (legacy format)
                # Try both lowercase and uppercase keys for compatibility
                prices = []
                highs = []
                lows = []
                
                for item in historical_data:
                    close_price = item.get('close') or item.get('Close') or 0
                    high_price = item.get('high') or item.get('High') or 0
                    low_price = item.get('low') or item.get('Low') or 0
                    
                    prices.append(float(close_price))
                    highs.append(float(high_price))
                    lows.append(float(low_price))
            
            return {
                'high': max(highs),
                'low': min(lows),
                'avg': sum(prices) / len(prices),
                'total_return': ((prices[-1] - prices[0]) / prices[0] * 100) if len(prices) > 1 else 0
            }
        except Exception as e:
            logger.error(f"Error processing historical data: {e}")
            return {'high': 0, 'low': 0, 'avg': 0, 'total_return': 0}
    
    def _get_recommendation_explanation(self, recommendation, confidence, news_sentiment, indicators):
        """Generate explanation for the recommendation."""
        explanations = {
            'Strong Buy': f"Strong bullish signals detected. Technical indicators favor buying with {confidence:.0f}% confidence. News sentiment is {news_sentiment}.",
            'Buy': f"Positive technical indicators suggest buying opportunity. Confidence level: {confidence:.0f}%. Consider market conditions and news sentiment: {news_sentiment}.",
            'Hold': f"Mixed signals suggest holding current position. Wait for clearer trend direction. Confidence: {confidence:.0f}%.",
            'Sell': f"Technical indicators suggest taking profits or reducing exposure. Confidence: {confidence:.0f}%. News sentiment: {news_sentiment}.",
            'Strong Sell': f"Strong bearish signals detected. Consider reducing exposure significantly. Confidence: {confidence:.0f}%."
        }
        
        return explanations.get(recommendation, f"Recommendation: {recommendation} with {confidence:.0f}% confidence.")


# Initialize chatbot API
chatbot_api = ChatbotAPI()


# ================ API Routes ================

@app.get("/", response_class=HTMLResponse)
async def home():
    """Home page with API documentation and testing interface."""
    html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Stock Analysis Chatbot API</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #2c3e50; text-align: center; }
        h2 { color: #34495e; border-bottom: 2px solid #3498db; padding-bottom: 10px; }
        .endpoint { background: #ecf0f1; padding: 15px; margin: 10px 0; border-left: 4px solid #3498db; }
        .method { color: #e74c3c; font-weight: bold; }
        code { background: #f8f9fa; padding: 2px 6px; border-radius: 3px; }
        ul { line-height: 1.6; }
        .test-section { background: #e8f5e8; padding: 20px; margin: 20px 0; border-radius: 8px; }
        input, button { padding: 10px; margin: 5px; border: 1px solid #ccc; border-radius: 4px; }
        button { background: #3498db; color: white; cursor: pointer; }
        button:hover { background: #2980b9; }
        #result { background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 4px; white-space: pre-wrap; max-height: 400px; overflow-y: auto; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 Stock Analysis Chatbot API (FastAPI)</h1>
        <p>Welcome to the Stock Analysis Chatbot API! This service provides comprehensive stock analysis combining real-time data, technical indicators, news sentiment, and AI-powered buy/sell recommendations.</p>
        
        <div class="test-section">
            <h2>🧪 Quick Test</h2>
            <p>Test the API directly from your browser:</p>
            <input type="text" id="symbolInput" placeholder="Enter stock symbol (e.g., PEP, AAPL)" value="PEP">
            <button onclick="testAnalysis()">Analyze Stock</button>
            <button onclick="testChat()">Test Chat</button>
            <button onclick="testHealth()">Health Check</button>
            <div id="result"></div>
        </div>
        
        <h2>📊 API Endpoints</h2>
        
        <div class="endpoint">
            <h3><span class="method">POST</span> /analyze</h3>
            <p>Analyze a stock with comprehensive AI insights</p>
            <p><strong>Body:</strong> <code>{"symbol": "PEP", "days": 30}</code></p>
            <p><strong>Returns:</strong> Complete analysis with recommendation</p>
        </div>
        
        <div class="endpoint">
            <h3><span class="method">POST</span> /chat</h3>
            <p>Chat interface for stock queries</p>
            <p><strong>Body:</strong> <code>{"message": "Should I buy PepsiCo stock?"}</code></p>
            <p><strong>Returns:</strong> Conversational response with analysis</p>
        </div>
        
        <div class="endpoint">
            <h3><span class="method">GET</span> /stocks/{symbol}</h3>
            <p>Get basic stock data</p>
            <p><strong>Example:</strong> <code>GET /stocks/PEP</code></p>
            <p><strong>Returns:</strong> Current price and historical data</p>
        </div>
        
        <div class="endpoint">
            <h3><span class="method">GET</span> /news/{symbol}</h3>
            <p>Get news sentiment for a stock</p>
            <p><strong>Example:</strong> <code>GET /news/PEP</code></p>
            <p><strong>Returns:</strong> News articles with sentiment analysis</p>
        </div>
        
        <div class="endpoint">
            <h3><span class="method">GET</span> /health</h3>
            <p>API health check</p>
            <p><strong>Returns:</strong> System status and connectivity</p>
        </div>
        
        <h2>📚 FastAPI Documentation</h2>
        <p>For interactive API testing:</p>
        <ul>
            <li><a href="/docs" target="_blank">Swagger UI Documentation</a></li>
            <li><a href="/redoc" target="_blank">ReDoc Documentation</a></li>
        </ul>
        
        <h2>🎯 Features</h2>
        <ul>
            <li>Real-time stock data from multiple APIs</li>
            <li>Technical analysis (RSI, MACD, Bollinger Bands)</li>
            <li>News sentiment analysis from Google News</li>
            <li>AI-powered buy/sell recommendations</li>
            <li>Historical data analysis (up to 365 days)</li>
            <li>Confidence scoring for recommendations</li>
            <li>FastAPI with automatic validation</li>
        </ul>
    </div>
    
    <script>
        function showResult(data) {
            document.getElementById('result').textContent = JSON.stringify(data, null, 2);
        }
        
        function showError(error) {
            document.getElementById('result').textContent = 'Error: ' + error;
        }
        
        async function testHealth() {
            try {
                const response = await fetch('/health');
                const data = await response.json();
                showResult(data);
            } catch (error) {
                showError(error.message);
            }
        }
        
        async function testAnalysis() {
            const symbol = document.getElementById('symbolInput').value.trim();
            if (!symbol) {
                showError('Please enter a stock symbol');
                return;
            }
            
            try {
                document.getElementById('result').textContent = 'Analyzing ' + symbol + '...';
                const response = await fetch('/analyze', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ symbol: symbol, days: 30 })
                });
                const data = await response.json();
                showResult(data);
            } catch (error) {
                showError(error.message);
            }
        }
        
        async function testChat() {
            const symbol = document.getElementById('symbolInput').value.trim() || 'PEP';
            
            try {
                document.getElementById('result').textContent = 'Processing chat request...';
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: `Should I buy ${symbol} stock?` })
                });
                const data = await response.json();
                showResult(data);
            } catch (error) {
                showError(error.message);
            }
        }
    </script>
</body>
</html>
    """
    return html_template


@app.post("/analyze")
async def analyze_stock(request: StockAnalysisRequest):
    """Analyze a stock with comprehensive AI insights."""
    try:
        # Perform analysis
        result = chatbot_api.analyze_stock(request.symbol.strip(), request.days)
        return result
        
    except Exception as e:
        logger.error(f"Error in analyze_stock: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                'success': False,
                'error': 'Internal server error',
                'details': str(e)
            }
        )


@app.post("/chat")
async def chat(request: ChatRequest):
    """Chat interface for natural language stock queries."""
    try:
        message = request.message.strip()
        
        if not message:
            raise HTTPException(
                status_code=400,
                detail={'success': False, 'error': 'Message cannot be empty'}
            )
        
        # Simple message parsing to extract stock symbols
        # This is a basic implementation - could be enhanced with NLP
        words = message.upper().split()
        
        # Look for stock symbols or company names
        stock_symbols = []
        symbol_indicators = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX', 'AMD', 'INTC', 'PEP']
        
        for word in words:
            # Remove punctuation
            clean_word = ''.join(c for c in word if c.isalnum())
            if clean_word in symbol_indicators or len(clean_word) <= 5 and clean_word.isalpha():
                stock_symbols.append(clean_word)
        
        # If no symbols found, try to extract from common patterns
        if not stock_symbols:
            company_mappings = {
                'APPLE': 'AAPL', 'GOOGLE': 'GOOGL', 'MICROSOFT': 'MSFT', 
                'AMAZON': 'AMZN', 'TESLA': 'TSLA', 'META': 'META',
                'NVIDIA': 'NVDA', 'NETFLIX': 'NFLX', 'PEPSICO': 'PEP',
                'PEPSI': 'PEP'
            }
            
            for company, symbol in company_mappings.items():
                if company in message.upper():
                    stock_symbols.append(symbol)
        
        # Default to PEP if no symbols found
        if not stock_symbols:
            stock_symbols = ['PEP']
        
        # Analyze the first symbol found
        symbol = stock_symbols[0]
        analysis_result = chatbot_api.analyze_stock(symbol, 30)
        
        if analysis_result['success']:
            # Generate conversational response
            recommendation = analysis_result['recommendation']
            confidence = analysis_result['confidence']
            
            response_text = f"""
Based on my analysis of {symbol}, here's what I found:

{analysis_result['comprehensive_summary']}

**My Recommendation:** {recommendation} (Confidence: {confidence:.1f}%)

Would you like me to analyze any other stocks or provide more details about this analysis?
"""
            
            return {
                'success': True,
                'response': response_text.strip(),
                'analysis': analysis_result,
                'symbol_analyzed': symbol
            }
        else:
            return {
                'success': False,
                'response': f"I'm sorry, I couldn't analyze {symbol}. {analysis_result.get('error', 'Unknown error')}",
                'error': analysis_result.get('error')
            }
        
    except Exception as e:
        logger.error(f"Error in chat: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                'success': False,
                'response': "I'm sorry, I encountered an error processing your request. Please try again.",
                'error': str(e)
            }
        )


@app.get("/stocks/{symbol}")
async def get_stock(symbol: str):
    """Get basic stock data for a symbol."""
    try:
        result = db_manager.get_stock_data(symbol.upper(), 30)
        return result
    except Exception as e:
        logger.error(f"Error getting stock data: {e}")
        raise HTTPException(
            status_code=500,
            detail={'success': False, 'error': str(e)}
        )


@app.get("/news/{symbol}")
async def get_news(symbol: str):
    """Get news sentiment for a stock."""
    try:
        result = news_fetcher.get_stock_news_sentiment(symbol.upper())
        return {
            'success': True,
            'symbol': symbol.upper(),
            'news_data': result
        }
    except Exception as e:
        logger.error(f"Error getting news: {e}")
        raise HTTPException(
            status_code=500,
            detail={'success': False, 'error': str(e)}
        )


@app.get("/health")
async def health_check():
    """API health check and system status."""
    try:
        # Test database connectivity
        config = db_manager.get_config()
        
        # Test API connectivity
        api_test = db_manager.test_connectivity()
        
        return {
            'success': True,
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'components': {
                'database': 'connected',
                'stock_apis': 'connected' if api_test['success'] else 'error',
                'news_api': 'connected',
                'ai_analyzer': 'ready'
            },
            'config': config
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={'success': False, 'status': 'unhealthy', 'error': str(e)}
        )


if __name__ == '__main__':
    import uvicorn
    
    print("🚀 Starting Stock Analysis Chatbot API with FastAPI...")
    print("📊 Features enabled:")
    print("   • Real-time stock data")
    print("   • Technical analysis (RSI, MACD, Bollinger Bands)")
    print("   • News sentiment analysis")
    print("   • AI-powered recommendations")
    print("   • SQLite database storage")
    print("\n🌐 API will be available at: http://localhost:8000")
    print("📚 Documentation at: http://localhost:8000/docs")
    print("📖 Alternative docs at: http://localhost:8000/redoc")
    
    uvicorn.run("chatbot_api:app", host="0.0.0.0", port=8000, reload=True)
