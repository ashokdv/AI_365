"""
News fetcher module to get stock-related news from Google News and other sources.
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
import re


class NewsStockFetcher:
    """Fetches stock-related news from various sources."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def get_stock_news(self, symbol: str, days: int = 7) -> List[Dict]:
        """
        Get news related to a specific stock symbol.
        
        Args:
            symbol (str): Stock symbol (e.g., 'AAPL')
            days (int): Number of days to look back for news
            
        Returns:
            List[Dict]: List of news articles
        """
        try:
            # Get company name for better search results
            company_names = self._get_company_name(symbol)
            
            news_articles = []
            
            # Search for news using multiple queries
            queries = [symbol, f"{symbol} stock", f"{symbol} earnings"]
            if company_names:
                queries.extend([company_names, f"{company_names} stock"])
            
            for query in queries[:3]:  # Limit to 3 queries to avoid rate limiting
                try:
                    articles = self._search_google_news(query, days)
                    news_articles.extend(articles)
                except Exception as e:
                    print(f"Error fetching news for query '{query}': {e}")
                    continue
            
            # Remove duplicates based on title
            seen_titles = set()
            unique_articles = []
            for article in news_articles:
                title = article.get('title', '').lower()
                if title not in seen_titles:
                    seen_titles.add(title)
                    unique_articles.append(article)
            
            # Sort by date (most recent first)
            unique_articles.sort(key=lambda x: x.get('published_date', ''), reverse=True)
            
            return unique_articles[:10]  # Return top 10 articles
            
        except Exception as e:
            print(f"Error getting stock news for {symbol}: {e}")
            return []
    
    def _get_company_name(self, symbol: str) -> str:
        """Get company name from symbol."""
        company_map = {
            'AAPL': 'Apple Inc',
            'GOOGL': 'Alphabet Google',
            'MSFT': 'Microsoft Corporation',
            'AMZN': 'Amazon',
            'TSLA': 'Tesla',
            'META': 'Meta Facebook',
            'NVDA': 'NVIDIA',
            'NFLX': 'Netflix',
            'DIS': 'Disney',
            'ORCL': 'Oracle'
        }
        return company_map.get(symbol.upper(), '')
    
    def _search_google_news(self, query: str, days: int) -> List[Dict]:
        """Search Google News for articles."""
        try:
            # Google News RSS feed
            url = "https://news.google.com/rss/search"
            params = {
                'q': query,
                'hl': 'en-US',
                'gl': 'US',
                'ceid': 'US:en'
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            # Parse RSS feed
            articles = self._parse_rss_feed(response.content)
            
            # Filter by date
            cutoff_date = datetime.now() - timedelta(days=days)
            recent_articles = []
            
            for article in articles:
                try:
                    pub_date = datetime.strptime(article.get('published_date', ''), '%a, %d %b %Y %H:%M:%S %Z')
                    if pub_date >= cutoff_date:
                        recent_articles.append(article)
                except:
                    # If date parsing fails, include the article anyway
                    recent_articles.append(article)
            
            return recent_articles
            
        except Exception as e:
            print(f"Error searching Google News: {e}")
            return []
    
    def _parse_rss_feed(self, content: bytes) -> List[Dict]:
        """Parse RSS feed content."""
        try:
            soup = BeautifulSoup(content, 'xml')
            articles = []
            
            for item in soup.find_all('item'):
                article = {
                    'title': self._clean_text(item.find('title').text if item.find('title') else ''),
                    'description': self._clean_text(item.find('description').text if item.find('description') else ''),
                    'link': item.find('link').text if item.find('link') else '',
                    'published_date': item.find('pubDate').text if item.find('pubDate') else '',
                    'source': self._extract_source(item.find('source').text if item.find('source') else ''),
                    'sentiment': 'neutral'  # Default sentiment, can be analyzed later
                }
                
                if article['title']:  # Only add if we have a title
                    articles.append(article)
            
            return articles
            
        except Exception as e:
            print(f"Error parsing RSS feed: {e}")
            return []
    
    def _clean_text(self, text: str) -> str:
        """Clean and format text."""
        if not text:
            return ''
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _extract_source(self, source_text: str) -> str:
        """Extract source name from source text."""
        if not source_text:
            return 'Unknown'
        
        # Try to extract source name (usually after last dash or in parentheses)
        if ' - ' in source_text:
            return source_text.split(' - ')[-1].strip()
        elif '(' in source_text and ')' in source_text:
            match = re.search(r'\(([^)]+)\)', source_text)
            if match:
                return match.group(1).strip()
        
        return source_text.strip()
    
    def analyze_news_sentiment(self, articles: List[Dict]) -> Dict:
        """
        Analyze sentiment of news articles (basic keyword-based analysis).
        
        Args:
            articles (List[Dict]): List of news articles
            
        Returns:
            Dict: Sentiment analysis results
        """
        if not articles:
            return {
                'overall_sentiment': 'neutral',
                'positive_count': 0,
                'negative_count': 0,
                'neutral_count': 0,
                'confidence': 0
            }
        
        positive_keywords = [
            'profit', 'growth', 'increase', 'rise', 'gain', 'bull', 'up', 'surge', 
            'rally', 'boost', 'positive', 'strong', 'beat', 'exceed', 'outperform',
            'upgrade', 'buy', 'recommend', 'bullish', 'optimistic'
        ]
        
        negative_keywords = [
            'loss', 'decline', 'fall', 'drop', 'bear', 'down', 'crash', 'plunge',
            'negative', 'weak', 'miss', 'underperform', 'downgrade', 'sell', 
            'bearish', 'pessimistic', 'warning', 'concern', 'risk'
        ]
        
        sentiment_scores = []
        
        for article in articles:
            text = f"{article.get('title', '')} {article.get('description', '')}".lower()
            
            positive_score = sum(1 for keyword in positive_keywords if keyword in text)
            negative_score = sum(1 for keyword in negative_keywords if keyword in text)
            
            if positive_score > negative_score:
                sentiment = 'positive'
                score = 1
            elif negative_score > positive_score:
                sentiment = 'negative'
                score = -1
            else:
                sentiment = 'neutral'
                score = 0
            
            article['sentiment'] = sentiment
            sentiment_scores.append(score)
        
        # Calculate overall sentiment
        avg_score = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
        
        if avg_score > 0.1:
            overall_sentiment = 'positive'
        elif avg_score < -0.1:
            overall_sentiment = 'negative'
        else:
            overall_sentiment = 'neutral'
        
        positive_count = sum(1 for score in sentiment_scores if score > 0)
        negative_count = sum(1 for score in sentiment_scores if score < 0)
        neutral_count = len(sentiment_scores) - positive_count - negative_count
        
        return {
            'overall_sentiment': overall_sentiment,
            'positive_count': positive_count,
            'negative_count': negative_count,
            'neutral_count': neutral_count,
            'confidence': abs(avg_score),
            'articles_analyzed': len(articles),
            'sentiment_score': (avg_score + 1) * 5  # Convert to 0-10 scale
        }
    
    def get_stock_news_sentiment(self, symbol: str, days: int = 7) -> Dict:
        """Get stock news and analyze sentiment in one call."""
        try:
            # Get news articles
            articles = self.get_stock_news(symbol, days)
            
            if not articles:
                return {
                    'success': False,
                    'message': f'No news found for {symbol}',
                    'overall_sentiment': 'neutral',
                    'sentiment_score': 5.0,
                    'articles': [],
                    'positive_count': 0,
                    'negative_count': 0,
                    'neutral_count': 0
                }
            
            # Analyze sentiment
            sentiment_analysis = self.analyze_news_sentiment(articles)
            
            return {
                'success': True,
                'symbol': symbol,
                'overall_sentiment': sentiment_analysis['overall_sentiment'],
                'sentiment_score': sentiment_analysis['sentiment_score'],
                'positive_count': sentiment_analysis['positive_count'],
                'negative_count': sentiment_analysis['negative_count'],
                'neutral_count': sentiment_analysis['neutral_count'],
                'confidence': sentiment_analysis['confidence'],
                'articles_analyzed': sentiment_analysis['articles_analyzed'],
                'articles': articles[:5]  # Return first 5 articles with sentiment
            }
            
        except Exception as e:
            print(f"Error getting news sentiment for {symbol}: {e}")
            return {
                'success': False,
                'message': str(e),
                'overall_sentiment': 'neutral',
                'sentiment_score': 5.0,
                'articles': [],
                'positive_count': 0,
                'negative_count': 0,
                'neutral_count': 0
            }
    
    def get_market_news(self, limit: int = 5) -> List[Dict]:
        """Get general market news."""
        try:
            queries = ['stock market', 'S&P 500', 'nasdaq', 'dow jones']
            all_articles = []
            
            for query in queries:
                try:
                    articles = self._search_google_news(query, days=3)
                    all_articles.extend(articles[:2])  # Get 2 articles per query
                except:
                    continue
            
            # Remove duplicates and return limited results
            seen_titles = set()
            unique_articles = []
            for article in all_articles:
                title = article.get('title', '').lower()
                if title not in seen_titles and len(unique_articles) < limit:
                    seen_titles.add(title)
                    unique_articles.append(article)
            
            return unique_articles
            
        except Exception as e:
            print(f"Error getting market news: {e}")
            return []
    
    def close(self):
        """Close the session."""
        self.session.close()
