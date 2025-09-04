"""
AI-powered stock analysis module for buy/sell recommendations.
Uses technical indicators and news sentiment analysis.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import requests
import json


class StockAIAnalyzer:
    """AI-powered stock analysis for buy/sell recommendations."""
    
    def __init__(self, llama_api_url: str = None):
        """
        Initialize AI analyzer.
        
        Args:
            llama_api_url (str): URL for Llama API endpoint (optional)
        """
        self.llama_api_url = llama_api_url
    
    def analyze_stock(self, symbol: str, price_data: pd.DataFrame, news_sentiment: Dict, current_price: float) -> Dict:
        """
        Comprehensive stock analysis with buy/sell recommendation.
        
        Args:
            symbol (str): Stock symbol
            price_data (pd.DataFrame): Historical price data (OHLCV)
            news_sentiment (Dict): News sentiment analysis results
            current_price (float): Current stock price
            
        Returns:
            Dict: Complete analysis with recommendation
        """
        try:
            if price_data.empty:
                return self._create_error_response("No historical data available")
            
            # Technical analysis
            technical_analysis = self._technical_analysis(price_data, current_price)
            
            # Trend analysis
            trend_analysis = self._trend_analysis(price_data)
            
            # Volume analysis
            volume_analysis = self._volume_analysis(price_data)
            
            # Risk assessment
            risk_assessment = self._risk_assessment(price_data)
            
            # Combine all factors for final recommendation
            recommendation = self._generate_recommendation(
                technical_analysis, trend_analysis, volume_analysis, 
                risk_assessment, news_sentiment
            )
            
            # Generate AI summary
            ai_summary = self._generate_ai_summary(
                symbol, technical_analysis, trend_analysis, 
                news_sentiment, recommendation
            )
            
            return {
                'symbol': symbol,
                'current_price': current_price,
                'recommendation': recommendation,
                'technical_analysis': technical_analysis,
                'trend_analysis': trend_analysis,
                'volume_analysis': volume_analysis,
                'risk_assessment': risk_assessment,
                'news_sentiment': news_sentiment,
                'ai_summary': ai_summary,
                'analysis_timestamp': datetime.now().isoformat(),
                'confidence_score': recommendation.get('confidence', 0)
            }
            
        except Exception as e:
            return self._create_error_response(f"Analysis error: {str(e)}")
    
    def _technical_analysis(self, df: pd.DataFrame, current_price: float) -> Dict:
        """Perform technical analysis on price data."""
        try:
            # Calculate technical indicators
            indicators = {}
            
            # Moving Averages
            indicators['sma_5'] = df['Close'].rolling(window=5).mean().iloc[-1] if len(df) >= 5 else current_price
            indicators['sma_10'] = df['Close'].rolling(window=10).mean().iloc[-1] if len(df) >= 10 else current_price
            indicators['sma_20'] = df['Close'].rolling(window=20).mean().iloc[-1] if len(df) >= 20 else current_price
            
            # RSI (Relative Strength Index)
            indicators['rsi'] = self._calculate_rsi(df['Close'])
            
            # MACD
            macd_data = self._calculate_macd(df['Close'])
            indicators.update(macd_data)
            
            # Bollinger Bands
            bb_data = self._calculate_bollinger_bands(df['Close'])
            indicators.update(bb_data)
            
            # Support and Resistance
            support_resistance = self._find_support_resistance(df)
            indicators.update(support_resistance)
            
            # Price position analysis
            price_analysis = self._analyze_price_position(current_price, indicators)
            
            return {
                'indicators': indicators,
                'price_analysis': price_analysis,
                'signals': self._generate_technical_signals(indicators, current_price)
            }
            
        except Exception as e:
            return {'error': f"Technical analysis error: {str(e)}"}
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """Calculate RSI indicator."""
        try:
            if len(prices) < period + 1:
                return 50.0  # Neutral RSI
            
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            return float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50.0
        except:
            return 50.0
    
    def _calculate_macd(self, prices: pd.Series) -> Dict:
        """Calculate MACD indicator."""
        try:
            if len(prices) < 26:
                return {'macd': 0, 'macd_signal': 0, 'macd_histogram': 0}
            
            ema_12 = prices.ewm(span=12).mean()
            ema_26 = prices.ewm(span=26).mean()
            macd = ema_12 - ema_26
            macd_signal = macd.ewm(span=9).mean()
            macd_histogram = macd - macd_signal
            
            return {
                'macd': float(macd.iloc[-1]) if not pd.isna(macd.iloc[-1]) else 0,
                'macd_signal': float(macd_signal.iloc[-1]) if not pd.isna(macd_signal.iloc[-1]) else 0,
                'macd_histogram': float(macd_histogram.iloc[-1]) if not pd.isna(macd_histogram.iloc[-1]) else 0
            }
        except:
            return {'macd': 0, 'macd_signal': 0, 'macd_histogram': 0}
    
    def _calculate_bollinger_bands(self, prices: pd.Series, period: int = 20) -> Dict:
        """Calculate Bollinger Bands."""
        try:
            if len(prices) < period:
                current_price = prices.iloc[-1]
                return {
                    'bb_upper': current_price * 1.02,
                    'bb_middle': current_price,
                    'bb_lower': current_price * 0.98
                }
            
            sma = prices.rolling(window=period).mean()
            std = prices.rolling(window=period).std()
            
            bb_upper = sma + (std * 2)
            bb_lower = sma - (std * 2)
            
            return {
                'bb_upper': float(bb_upper.iloc[-1]) if not pd.isna(bb_upper.iloc[-1]) else prices.iloc[-1] * 1.02,
                'bb_middle': float(sma.iloc[-1]) if not pd.isna(sma.iloc[-1]) else prices.iloc[-1],
                'bb_lower': float(bb_lower.iloc[-1]) if not pd.isna(bb_lower.iloc[-1]) else prices.iloc[-1] * 0.98
            }
        except:
            current_price = prices.iloc[-1]
            return {
                'bb_upper': current_price * 1.02,
                'bb_middle': current_price,
                'bb_lower': current_price * 0.98
            }
    
    def _find_support_resistance(self, df: pd.DataFrame) -> Dict:
        """Find support and resistance levels."""
        try:
            highs = df['High'].rolling(window=5).max()
            lows = df['Low'].rolling(window=5).min()
            
            resistance = float(highs.max()) if not highs.empty else df['Close'].iloc[-1] * 1.05
            support = float(lows.min()) if not lows.empty else df['Close'].iloc[-1] * 0.95
            
            return {
                'resistance_level': resistance,
                'support_level': support
            }
        except:
            current_price = df['Close'].iloc[-1]
            return {
                'resistance_level': current_price * 1.05,
                'support_level': current_price * 0.95
            }
    
    def _analyze_price_position(self, current_price: float, indicators: Dict) -> Dict:
        """Analyze current price position relative to indicators."""
        analysis = {}
        
        # Position relative to moving averages
        sma_20 = indicators.get('sma_20', current_price)
        if current_price > sma_20:
            analysis['ma_position'] = 'above'
            analysis['ma_signal'] = 'bullish'
        else:
            analysis['ma_position'] = 'below'
            analysis['ma_signal'] = 'bearish'
        
        # Position relative to Bollinger Bands
        bb_upper = indicators.get('bb_upper', current_price * 1.02)
        bb_lower = indicators.get('bb_lower', current_price * 0.98)
        
        if current_price > bb_upper:
            analysis['bb_position'] = 'overbought'
        elif current_price < bb_lower:
            analysis['bb_position'] = 'oversold'
        else:
            analysis['bb_position'] = 'normal'
        
        return analysis
    
    def _generate_technical_signals(self, indicators: Dict, current_price: float) -> List[str]:
        """Generate technical trading signals."""
        signals = []
        
        # RSI signals
        rsi = indicators.get('rsi', 50)
        if rsi > 70:
            signals.append("RSI indicates overbought condition")
        elif rsi < 30:
            signals.append("RSI indicates oversold condition")
        
        # MACD signals
        macd = indicators.get('macd', 0)
        macd_signal = indicators.get('macd_signal', 0)
        if macd > macd_signal:
            signals.append("MACD shows bullish momentum")
        else:
            signals.append("MACD shows bearish momentum")
        
        # Moving average signals
        sma_5 = indicators.get('sma_5', current_price)
        sma_20 = indicators.get('sma_20', current_price)
        if sma_5 > sma_20:
            signals.append("Short-term MA above long-term MA (bullish)")
        else:
            signals.append("Short-term MA below long-term MA (bearish)")
        
        return signals
    
    def _trend_analysis(self, df: pd.DataFrame) -> Dict:
        """Analyze price trends."""
        try:
            if len(df) < 5:
                return {'trend': 'insufficient_data', 'strength': 0}
            
            # Calculate trend over different periods
            short_term_change = (df['Close'].iloc[-1] - df['Close'].iloc[-5]) / df['Close'].iloc[-5] * 100
            medium_term_change = (df['Close'].iloc[-1] - df['Close'].iloc[-10]) / df['Close'].iloc[-10] * 100 if len(df) >= 10 else short_term_change
            
            # Determine trend direction
            if short_term_change > 2:
                trend = 'bullish'
                strength = min(abs(short_term_change) / 5, 1.0)
            elif short_term_change < -2:
                trend = 'bearish'
                strength = min(abs(short_term_change) / 5, 1.0)
            else:
                trend = 'sideways'
                strength = 0.5
            
            return {
                'trend': trend,
                'strength': strength,
                'short_term_change': short_term_change,
                'medium_term_change': medium_term_change
            }
            
        except Exception as e:
            return {'trend': 'unknown', 'strength': 0, 'error': str(e)}
    
    def _volume_analysis(self, df: pd.DataFrame) -> Dict:
        """Analyze trading volume."""
        try:
            if 'Volume' not in df.columns or len(df) < 5:
                return {'volume_trend': 'unknown', 'volume_strength': 0}
            
            recent_volume = df['Volume'].iloc[-5:].mean()
            avg_volume = df['Volume'].mean()
            
            volume_ratio = recent_volume / avg_volume if avg_volume > 0 else 1
            
            if volume_ratio > 1.5:
                volume_trend = 'increasing'
            elif volume_ratio < 0.7:
                volume_trend = 'decreasing'
            else:
                volume_trend = 'normal'
            
            return {
                'volume_trend': volume_trend,
                'volume_ratio': volume_ratio,
                'recent_avg_volume': recent_volume,
                'overall_avg_volume': avg_volume
            }
            
        except Exception as e:
            return {'volume_trend': 'unknown', 'error': str(e)}
    
    def _risk_assessment(self, df: pd.DataFrame) -> Dict:
        """Assess investment risk based on volatility."""
        try:
            if len(df) < 5:
                return {'risk_level': 'unknown', 'volatility': 0}
            
            # Calculate volatility (standard deviation of returns)
            returns = df['Close'].pct_change().dropna()
            volatility = returns.std() * np.sqrt(252)  # Annualized volatility
            
            # Risk levels based on volatility
            if volatility > 0.4:
                risk_level = 'high'
            elif volatility > 0.2:
                risk_level = 'medium'
            else:
                risk_level = 'low'
            
            return {
                'risk_level': risk_level,
                'volatility': float(volatility),
                'max_drawdown': self._calculate_max_drawdown(df['Close'])
            }
            
        except Exception as e:
            return {'risk_level': 'unknown', 'error': str(e)}
    
    def _calculate_max_drawdown(self, prices: pd.Series) -> float:
        """Calculate maximum drawdown."""
        try:
            peak = prices.expanding().max()
            drawdown = (prices - peak) / peak
            return float(drawdown.min())
        except:
            return 0.0
    
    def _generate_recommendation(self, technical: Dict, trend: Dict, volume: Dict, risk: Dict, news: Dict) -> Dict:
        """Generate final buy/sell recommendation."""
        try:
            # Initialize scoring system
            score = 0
            factors = []
            
            # Technical analysis factors
            if 'indicators' in technical:
                rsi = technical['indicators'].get('rsi', 50)
                if rsi < 30:
                    score += 2
                    factors.append("RSI oversold (bullish)")
                elif rsi > 70:
                    score -= 2
                    factors.append("RSI overbought (bearish)")
                
                macd = technical['indicators'].get('macd', 0)
                macd_signal = technical['indicators'].get('macd_signal', 0)
                if macd > macd_signal:
                    score += 1
                    factors.append("MACD bullish crossover")
                else:
                    score -= 1
                    factors.append("MACD bearish crossover")
            
            # Trend factors
            if trend.get('trend') == 'bullish':
                score += 2
                factors.append("Strong bullish trend")
            elif trend.get('trend') == 'bearish':
                score -= 2
                factors.append("Strong bearish trend")
            
            # News sentiment factors
            news_sentiment = news.get('overall_sentiment', 'neutral')
            if news_sentiment == 'positive':
                score += 1
                factors.append("Positive news sentiment")
            elif news_sentiment == 'negative':
                score -= 1
                factors.append("Negative news sentiment")
            
            # Risk adjustment
            risk_level = risk.get('risk_level', 'medium')
            if risk_level == 'high':
                score -= 1
                factors.append("High volatility risk")
            
            # Generate recommendation
            if score >= 3:
                recommendation = 'strong_buy'
                action = 'BUY'
                confidence = min(score / 5 * 100, 95)
            elif score >= 1:
                recommendation = 'buy'
                action = 'BUY'
                confidence = min(score / 3 * 100, 80)
            elif score <= -3:
                recommendation = 'strong_sell'
                action = 'SELL'
                confidence = min(abs(score) / 5 * 100, 95)
            elif score <= -1:
                recommendation = 'sell'
                action = 'SELL'
                confidence = min(abs(score) / 3 * 100, 80)
            else:
                recommendation = 'hold'
                action = 'HOLD'
                confidence = 60
            
            return {
                'recommendation': recommendation,
                'action': action,
                'confidence': round(confidence, 1),
                'score': score,
                'factors': factors,
                'reasoning': self._generate_reasoning(recommendation, factors)
            }
            
        except Exception as e:
            return {
                'recommendation': 'hold',
                'action': 'HOLD',
                'confidence': 50,
                'error': str(e)
            }
    
    def _generate_reasoning(self, recommendation: str, factors: List[str]) -> str:
        """Generate human-readable reasoning for the recommendation."""
        reasoning_map = {
            'strong_buy': "Strong technical indicators and positive sentiment suggest this is an excellent buying opportunity.",
            'buy': "Multiple positive indicators suggest this stock has good upward potential.",
            'hold': "Mixed signals suggest maintaining current position and monitoring closely.",
            'sell': "Several negative indicators suggest it may be time to consider selling.",
            'strong_sell': "Strong negative indicators suggest immediate selling may be prudent."
        }
        
        base_reasoning = reasoning_map.get(recommendation, "Analysis is inconclusive.")
        
        if factors:
            factor_summary = " Key factors include: " + ", ".join(factors[:3])
            return base_reasoning + factor_summary
        
        return base_reasoning
    
    def _generate_ai_summary(self, symbol: str, technical: Dict, trend: Dict, news: Dict, recommendation: Dict) -> str:
        """Generate AI-powered summary of the analysis."""
        try:
            # If we have Llama API, use it
            if self.llama_api_url:
                return self._get_llama_summary(symbol, technical, trend, news, recommendation)
            
            # Otherwise, generate rule-based summary
            return self._generate_rule_based_summary(symbol, technical, trend, news, recommendation)
            
        except Exception as e:
            return f"Summary generation error: {str(e)}"
    
    def _get_llama_summary(self, symbol: str, technical: Dict, trend: Dict, news: Dict, recommendation: Dict) -> str:
        """Get AI summary from Llama API."""
        try:
            prompt = f"""
            Analyze the stock {symbol} and provide a concise investment summary:
            
            Technical Analysis: RSI={technical.get('indicators', {}).get('rsi', 'N/A')}, 
            Trend: {trend.get('trend', 'unknown')}, 
            News Sentiment: {news.get('overall_sentiment', 'neutral')},
            Recommendation: {recommendation.get('action', 'HOLD')} with {recommendation.get('confidence', 0)}% confidence
            
            Provide a 2-3 sentence summary with key insights and risks.
            """
            
            response = requests.post(
                self.llama_api_url,
                json={"prompt": prompt, "max_tokens": 150},
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json().get('response', self._generate_rule_based_summary(symbol, technical, trend, news, recommendation))
            else:
                return self._generate_rule_based_summary(symbol, technical, trend, news, recommendation)
                
        except Exception as e:
            return self._generate_rule_based_summary(symbol, technical, trend, news, recommendation)
    
    def _generate_rule_based_summary(self, symbol: str, technical: Dict, trend: Dict, news: Dict, recommendation: Dict) -> str:
        """Generate rule-based summary."""
        action = recommendation.get('action', 'HOLD')
        confidence = recommendation.get('confidence', 0)
        trend_direction = trend.get('trend', 'unknown')
        news_sentiment = news.get('overall_sentiment', 'neutral')
        
        if action == 'BUY':
            summary = f"💹 {symbol} shows strong buying signals with {confidence}% confidence. "
        elif action == 'SELL':
            summary = f"📉 {symbol} indicates selling pressure with {confidence}% confidence. "
        else:
            summary = f"⚖️ {symbol} suggests holding position with mixed signals. "
        
        summary += f"The stock is in a {trend_direction} trend with {news_sentiment} news sentiment. "
        
        # Add risk note
        if confidence > 80:
            summary += "High confidence in this analysis."
        elif confidence < 60:
            summary += "Lower confidence - proceed with caution."
        else:
            summary += "Moderate confidence in this recommendation."
        
        return summary
    
    def _create_error_response(self, error_msg: str) -> Dict:
        """Create standardized error response."""
        return {
            'error': error_msg,
            'recommendation': {
                'action': 'HOLD',
                'confidence': 0,
                'reasoning': 'Unable to analyze due to insufficient data'
            },
            'ai_summary': f"Analysis failed: {error_msg}"
        }
