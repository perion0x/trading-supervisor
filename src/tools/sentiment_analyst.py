"""
Sentiment Analyst Tool

Provides sentiment analysis for financial instruments using Alpha Vantage News Sentiment API.
"""

import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional
import requests

from src.models import SentimentAnalysis
from src.exceptions import ExternalAPIError
from src.utils.retry import exponential_backoff_retry
from src.utils.validation import validate_ticker, validate_api_key

logger = logging.getLogger(__name__)


# Alias for backward compatibility
SentimentAPIError = ExternalAPIError


@exponential_backoff_retry(
    max_retries=2,
    initial_delay=1.0,
    backoff_factor=2.0,
    exceptions=(ExternalAPIError, requests.exceptions.RequestException),
    timeout=15.0
)
def fetch_news_sentiment(ticker: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Fetch news sentiment data from Alpha Vantage API with retry logic.
    
    Implements exponential backoff retry (2 attempts) with 15-second timeout.
    
    Args:
        ticker: Stock ticker symbol
        api_key: Alpha Vantage API key (defaults to environment variable)
        
    Returns:
        Dictionary containing sentiment data from API
        
    Raises:
        ExternalAPIError: If API call fails after retries
    """
    # Validate inputs
    ticker = validate_ticker(ticker)
    
    if api_key is None:
        api_key = os.environ.get('ALPHA_VANTAGE_API_KEY')
    
    if not api_key:
        raise ExternalAPIError("Alpha Vantage API key not provided")
    
    # Validate API key
    api_key = validate_api_key(api_key)
    
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "NEWS_SENTIMENT",
        "tickers": ticker,
        "apikey": api_key,
        "limit": 50  # Get up to 50 recent news articles
    }
    
    try:
        logger.info(f"Fetching news sentiment for {ticker} from Alpha Vantage")
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Check for API errors
        if "Error Message" in data:
            raise ExternalAPIError(f"API Error: {data['Error Message']}")
        
        if "Note" in data:
            raise ExternalAPIError(f"API Rate Limit: {data['Note']}")
        
        if "feed" not in data:
            raise ExternalAPIError("No sentiment data returned from API")
        
        logger.info(f"Successfully fetched {len(data.get('feed', []))} news articles for {ticker}")
        return data
        
    except ExternalAPIError:
        # Re-raise our custom exception
        raise
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch sentiment data for {ticker}: {str(e)}")
        raise ExternalAPIError(f"Failed to fetch sentiment data: {str(e)}")


def calculate_aggregate_sentiment(sentiment_data: Dict[str, Any], ticker: str) -> tuple[str, float, str]:
    """
    Calculate aggregate sentiment from news articles.
    
    Args:
        sentiment_data: Raw data from Alpha Vantage API
        ticker: Stock ticker symbol
        
    Returns:
        Tuple of (sentiment, confidence, rationale)
    """
    feed = sentiment_data.get("feed", [])
    
    if not feed:
        # No news available - return neutral/uncertain
        return "Bearish", 0.5, f"No recent news articles found for {ticker}"
    
    # Collect sentiment scores for the specific ticker
    ticker_sentiments = []
    article_count = 0
    
    for article in feed:
        # Check if this article mentions our ticker
        ticker_sentiments_list = article.get("ticker_sentiment", [])
        
        for ts in ticker_sentiments_list:
            if ts.get("ticker") == ticker:
                # Get sentiment score and relevance
                sentiment_score = float(ts.get("ticker_sentiment_score", 0))
                relevance_score = float(ts.get("relevance_score", 0))
                
                # Weight by relevance
                weighted_score = sentiment_score * relevance_score
                ticker_sentiments.append(weighted_score)
                article_count += 1
    
    if not ticker_sentiments:
        return "Bearish", 0.5, f"No specific sentiment data found for {ticker} in recent news"
    
    # Calculate average sentiment
    avg_sentiment = sum(ticker_sentiments) / len(ticker_sentiments)
    
    # Determine bullish/bearish
    # Alpha Vantage scores: -1 (bearish) to +1 (bullish)
    if avg_sentiment > 0:
        sentiment = "Bullish"
    else:
        sentiment = "Bearish"
    
    # Calculate confidence based on:
    # 1. Magnitude of sentiment score
    # 2. Number of articles (more articles = more confidence)
    magnitude = abs(avg_sentiment)
    article_factor = min(article_count / 10.0, 1.0)  # Cap at 10 articles
    
    # Confidence ranges from 0.5 to 0.95
    confidence = 0.5 + (magnitude * 0.3) + (article_factor * 0.15)
    confidence = min(confidence, 0.95)
    confidence = round(confidence, 2)
    
    # Create rationale
    rationale = (
        f"Based on {article_count} recent news articles, "
        f"average sentiment score is {avg_sentiment:.3f} "
        f"({'positive' if avg_sentiment > 0 else 'negative'})"
    )
    
    return sentiment, confidence, rationale


def analyze_sentiment(ticker: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Main function to perform sentiment analysis using Alpha Vantage.
    
    Args:
        ticker: Stock ticker symbol
        api_key: Optional Alpha Vantage API key
        
    Returns:
        Dictionary containing sentiment analysis results
    """
    try:
        logger.info(f"Performing sentiment analysis for {ticker}")
        
        # Fetch sentiment data from Alpha Vantage
        sentiment_data = fetch_news_sentiment(ticker, api_key)
        
        # Calculate aggregate sentiment
        sentiment, confidence, rationale = calculate_aggregate_sentiment(sentiment_data, ticker)
        
        # Create SentimentAnalysis object
        analysis = SentimentAnalysis(
            ticker=ticker,
            sentiment=sentiment,
            confidence=confidence,
            rationale=rationale,
            timestamp=datetime.now()
        )
        
        logger.info(f"Sentiment analysis complete for {ticker}: {sentiment} (confidence: {confidence})")
        
        return {
            "ticker": analysis.ticker,
            "sentiment": analysis.sentiment,
            "confidence": analysis.confidence,
            "rationale": analysis.rationale,
            "timestamp": analysis.timestamp.isoformat(),
            "error": None
        }
        
    except ExternalAPIError as e:
        logger.error(f"Sentiment analysis failed for {ticker}: {str(e)}")
        return {
            "ticker": ticker,
            "sentiment": None,
            "confidence": None,
            "rationale": None,
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }
    except Exception as e:
        logger.error(f"Unexpected error in sentiment analysis for {ticker}: {str(e)}")
        return {
            "ticker": ticker,
            "sentiment": None,
            "confidence": None,
            "rationale": None,
            "timestamp": datetime.now().isoformat(),
            "error": f"Unexpected error: {str(e)}"
        }
