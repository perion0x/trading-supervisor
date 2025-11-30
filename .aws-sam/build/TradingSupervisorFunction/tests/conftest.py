"""
Pytest configuration and shared fixtures for test suite.

This module provides reusable test fixtures, mock data generators,
and Hypothesis strategies for property-based testing.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from hypothesis import strategies as st
from typing import Dict, Any


# ============================================================================
# Pytest Fixtures
# ============================================================================

@pytest.fixture
def sample_ticker():
    """Provide a sample ticker symbol for testing."""
    return "AAPL"


@pytest.fixture
def sample_tickers():
    """Provide a list of sample ticker symbols for testing."""
    return ["AAPL", "MSFT", "GOOGL", "TSLA", "AMZN"]


@pytest.fixture
def sample_price_data():
    """
    Generate sample price data for testing RSI calculations.
    
    Returns a pandas DataFrame with realistic OHLCV data.
    """
    dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
    
    # Generate realistic price movements
    np.random.seed(42)
    base_price = 150.0
    prices = []
    
    for i in range(30):
        # Random walk with slight upward bias
        change = np.random.normal(0.5, 2.0)
        base_price = max(base_price + change, 1.0)  # Ensure positive prices
        prices.append(base_price)
    
    df = pd.DataFrame({
        'Open': [p * 0.99 for p in prices],
        'High': [p * 1.02 for p in prices],
        'Low': [p * 0.98 for p in prices],
        'Close': prices,
        'Volume': np.random.randint(1000000, 10000000, 30)
    }, index=dates)
    
    return df


@pytest.fixture
def sample_price_series():
    """Generate a simple price series for RSI testing."""
    return pd.Series([
        44, 44.34, 44.09, 43.61, 44.33, 44.83, 45.10, 45.42, 45.84, 46.08,
        45.89, 46.03, 45.61, 46.28, 46.28, 46.00, 46.03, 46.41, 46.22, 45.64
    ])


@pytest.fixture
def sample_technical_result():
    """Provide a sample technical analysis result."""
    return {
        "ticker": "AAPL",
        "current_price": 178.50,
        "rsi": 65.4,
        "rsi_signal": "Neutral",
        "price_change_24h": 2.3,
        "timestamp": datetime.now().isoformat(),
        "error": None
    }


@pytest.fixture
def sample_sentiment_result():
    """Provide a sample sentiment analysis result."""
    return {
        "ticker": "AAPL",
        "sentiment": "Bullish",
        "confidence": 0.75,
        "rationale": "Based on 15 recent news articles, average sentiment score is 0.234 (positive)",
        "timestamp": datetime.now().isoformat(),
        "error": None
    }


@pytest.fixture
def sample_trading_recommendation():
    """Provide a sample trading recommendation."""
    return {
        "ticker": "AAPL",
        "recommendation": "BUY",
        "technical_analysis": {
            "ticker": "AAPL",
            "current_price": 178.50,
            "rsi": 65.4,
            "rsi_signal": "Neutral",
            "price_change_24h": 2.3,
            "timestamp": datetime.now().isoformat(),
            "error": None
        },
        "sentiment_analysis": {
            "ticker": "AAPL",
            "sentiment": "Bullish",
            "confidence": 0.75,
            "rationale": "Based on 15 recent news articles, average sentiment score is 0.234 (positive)",
            "timestamp": datetime.now().isoformat(),
            "error": None
        },
        "summary": "Buy signal: Neutral momentum (65.4) with positive sentiment",
        "confidence": 0.70,
        "timestamp": datetime.now().isoformat(),
        "error": None
    }


@pytest.fixture
def sample_bedrock_event():
    """Provide a sample AWS Bedrock Agent event."""
    return {
        "messageVersion": "1.0",
        "agent": {
            "name": "TradingSupervisor",
            "id": "agent-123",
            "alias": "prod",
            "version": "1"
        },
        "inputText": "Analyze AAPL",
        "sessionId": "session-test-123",
        "sessionAttributes": {},
        "promptSessionAttributes": {}
    }


@pytest.fixture
def mock_alpha_vantage_response():
    """Provide a mock Alpha Vantage News Sentiment API response."""
    return {
        "items": "50",
        "sentiment_score_definition": "x <= -0.35: Bearish; -0.35 < x <= -0.15: Somewhat-Bearish; -0.15 < x < 0.15: Neutral; 0.15 <= x < 0.35: Somewhat_Bullish; x >= 0.35: Bullish",
        "relevance_score_definition": "0 < x <= 1, with a higher score indicating higher relevance.",
        "feed": [
            {
                "title": "Apple Announces New Product Line",
                "url": "https://example.com/article1",
                "time_published": "20251129T120000",
                "authors": ["John Doe"],
                "summary": "Apple announces exciting new products...",
                "banner_image": "https://example.com/image1.jpg",
                "source": "TechNews",
                "category_within_source": "Technology",
                "source_domain": "technews.com",
                "topics": [
                    {
                        "topic": "Technology",
                        "relevance_score": "0.9"
                    }
                ],
                "overall_sentiment_score": 0.25,
                "overall_sentiment_label": "Somewhat-Bullish",
                "ticker_sentiment": [
                    {
                        "ticker": "AAPL",
                        "relevance_score": "0.8",
                        "ticker_sentiment_score": "0.3",
                        "ticker_sentiment_label": "Somewhat-Bullish"
                    }
                ]
            },
            {
                "title": "Market Analysis: Tech Stocks Rally",
                "url": "https://example.com/article2",
                "time_published": "20251129T100000",
                "authors": ["Jane Smith"],
                "summary": "Tech stocks show strong performance...",
                "banner_image": "https://example.com/image2.jpg",
                "source": "MarketWatch",
                "category_within_source": "Markets",
                "source_domain": "marketwatch.com",
                "topics": [
                    {
                        "topic": "Financial Markets",
                        "relevance_score": "0.95"
                    }
                ],
                "overall_sentiment_score": 0.4,
                "overall_sentiment_label": "Bullish",
                "ticker_sentiment": [
                    {
                        "ticker": "AAPL",
                        "relevance_score": "0.6",
                        "ticker_sentiment_score": "0.35",
                        "ticker_sentiment_label": "Bullish"
                    }
                ]
            }
        ]
    }


# ============================================================================
# Hypothesis Strategies for Property-Based Testing
# ============================================================================

# Generate valid ticker symbols (1-5 uppercase letters)
ticker_strategy = st.text(
    alphabet=st.characters(whitelist_categories=('Lu',), max_codepoint=90),
    min_size=1,
    max_size=5
)

# Generate valid prices (positive floats)
price_strategy = st.floats(
    min_value=1.0,
    max_value=10000.0,
    allow_nan=False,
    allow_infinity=False
)

# Generate valid RSI values (0-100)
rsi_strategy = st.floats(
    min_value=0.0,
    max_value=100.0,
    allow_nan=False,
    allow_infinity=False
)

# Generate price series for RSI calculation (at least 20 data points)
price_series_strategy = st.lists(
    price_strategy,
    min_size=20,
    max_size=100
)

# Generate confidence scores (0.0-1.0)
confidence_strategy = st.floats(
    min_value=0.0,
    max_value=1.0,
    allow_nan=False,
    allow_infinity=False
)

# Generate recommendation types
recommendation_strategy = st.sampled_from(["BUY", "SELL", "HOLD"])

# Generate sentiment types
sentiment_strategy = st.sampled_from(["Bullish", "Bearish"])

# Generate RSI signals
rsi_signal_strategy = st.sampled_from(["Overbought", "Oversold", "Neutral"])


# ============================================================================
# Test Data Generators
# ============================================================================

def generate_price_dataframe(num_points: int = 30, base_price: float = 100.0, seed: int = None) -> pd.DataFrame:
    """
    Generate a realistic price DataFrame for testing.
    
    Args:
        num_points: Number of data points to generate
        base_price: Starting price
        seed: Random seed for reproducibility
        
    Returns:
        DataFrame with OHLCV data
    """
    if seed is not None:
        np.random.seed(seed)
    
    dates = pd.date_range(end=datetime.now(), periods=num_points, freq='D')
    prices = []
    current_price = base_price
    
    for _ in range(num_points):
        # Random walk
        change = np.random.normal(0, 2.0)
        current_price = max(current_price + change, 1.0)
        prices.append(current_price)
    
    df = pd.DataFrame({
        'Open': [p * 0.99 for p in prices],
        'High': [p * 1.02 for p in prices],
        'Low': [p * 0.98 for p in prices],
        'Close': prices,
        'Volume': np.random.randint(1000000, 10000000, num_points)
    }, index=dates)
    
    return df


def generate_query_with_ticker(ticker: str) -> str:
    """
    Generate a natural language query containing a ticker.
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        Query string
    """
    templates = [
        f"Analyze {ticker}",
        f"What about {ticker} stock?",
        f"Should I buy {ticker}?",
        f"Tell me about {ticker}",
        f"Give me analysis for {ticker}",
        f"What's the outlook for {ticker}?"
    ]
    
    import random
    return random.choice(templates)


def generate_mock_news_article(ticker: str, sentiment_score: float = 0.0) -> Dict[str, Any]:
    """
    Generate a mock news article for testing sentiment analysis.
    
    Args:
        ticker: Stock ticker symbol
        sentiment_score: Sentiment score (-1 to 1)
        
    Returns:
        Mock article dictionary
    """
    sentiment_label = "Bullish" if sentiment_score > 0 else "Bearish"
    
    return {
        "title": f"News about {ticker}",
        "url": "https://example.com/article",
        "time_published": datetime.now().strftime("%Y%m%dT%H%M%S"),
        "summary": f"Article discussing {ticker} performance",
        "overall_sentiment_score": sentiment_score,
        "ticker_sentiment": [
            {
                "ticker": ticker,
                "relevance_score": "0.8",
                "ticker_sentiment_score": str(sentiment_score),
                "ticker_sentiment_label": sentiment_label
            }
        ]
    }


# ============================================================================
# Helper Functions for Tests
# ============================================================================

def assert_valid_rsi(rsi_value: float):
    """Assert that RSI value is within valid range."""
    assert isinstance(rsi_value, (int, float)), f"RSI must be numeric, got {type(rsi_value)}"
    assert 0 <= rsi_value <= 100, f"RSI must be between 0 and 100, got {rsi_value}"


def assert_valid_price(price: float):
    """Assert that price is valid."""
    assert isinstance(price, (int, float)), f"Price must be numeric, got {type(price)}"
    assert price > 0, f"Price must be positive, got {price}"


def assert_valid_confidence(confidence: float):
    """Assert that confidence score is valid."""
    assert isinstance(confidence, (int, float)), f"Confidence must be numeric, got {type(confidence)}"
    assert 0 <= confidence <= 1, f"Confidence must be between 0 and 1, got {confidence}"


def assert_valid_ticker(ticker: str):
    """Assert that ticker format is valid."""
    assert isinstance(ticker, str), f"Ticker must be string, got {type(ticker)}"
    assert 1 <= len(ticker) <= 5, f"Ticker must be 1-5 characters, got {len(ticker)}"
    assert ticker.isupper(), f"Ticker must be uppercase, got {ticker}"
    assert ticker.isalpha(), f"Ticker must be alphabetic, got {ticker}"
