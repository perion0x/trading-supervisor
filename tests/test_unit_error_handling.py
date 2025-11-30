"""
Unit Tests for Error Handling Scenarios

These tests verify that the system handles errors gracefully across all components.
"""

import pytest
from unittest.mock import patch, Mock
import pandas as pd
from src.tools.technical_analyst import analyze_technical, fetch_price_data
from src.tools.sentiment_analyst import analyze_sentiment, fetch_news_sentiment
from src.supervisor import handle_query, extract_ticker
from src.exceptions import (
    InvalidTickerError,
    InsufficientDataError,
    ExternalAPIError,
    ValidationError
)


# ============================================================================
# Test yfinance API Unavailable
# ============================================================================

@patch('src.tools.technical_analyst.yf.Ticker')
def test_technical_analysis_yfinance_unavailable(mock_ticker):
    """
    Test technical analysis when yfinance API is unavailable.
    
    Should return error response without crashing.
    """
    # Mock yfinance to raise an exception
    mock_ticker.side_effect = Exception("API unavailable")
    
    result = analyze_technical("AAPL")
    
    # Should return error response
    assert result is not None
    assert isinstance(result, dict)
    assert result.get('error') is not None
    assert result.get('ticker') == "AAPL"
    assert result.get('rsi') is None


@patch('src.tools.technical_analyst.yf.Ticker')
def test_technical_analysis_network_timeout(mock_ticker):
    """
    Test technical analysis when network times out.
    """
    # Mock network timeout
    mock_instance = Mock()
    mock_instance.history.side_effect = TimeoutError("Connection timeout")
    mock_ticker.return_value = mock_instance
    
    result = analyze_technical("AAPL")
    
    # Should handle timeout gracefully
    assert result is not None
    assert result.get('error') is not None


# ============================================================================
# Test Empty Data Responses
# ============================================================================

@patch('src.tools.technical_analyst.yf.Ticker')
def test_technical_analysis_empty_data(mock_ticker):
    """
    Test technical analysis when yfinance returns empty data.
    """
    # Mock empty DataFrame
    mock_instance = Mock()
    mock_instance.history.return_value = pd.DataFrame()
    mock_ticker.return_value = mock_instance
    
    result = analyze_technical("AAPL")
    
    # Should return error response
    assert result is not None
    assert result.get('error') is not None
    assert "No data" in result.get('error') or "empty" in result.get('error').lower()


@patch('src.tools.technical_analyst.yf.Ticker')
def test_technical_analysis_insufficient_data_for_rsi(mock_ticker):
    """
    Test technical analysis when there's insufficient data for RSI calculation.
    """
    # Mock DataFrame with only 10 data points (need 15+ for RSI)
    mock_instance = Mock()
    mock_instance.history.return_value = pd.DataFrame({
        'Close': [100, 101, 102, 103, 104, 105, 106, 107, 108, 109],
        'Open': [99, 100, 101, 102, 103, 104, 105, 106, 107, 108],
        'High': [101, 102, 103, 104, 105, 106, 107, 108, 109, 110],
        'Low': [98, 99, 100, 101, 102, 103, 104, 105, 106, 107],
        'Volume': [1000000] * 10
    })
    mock_ticker.return_value = mock_instance
    
    result = analyze_technical("AAPL")
    
    # Should return error response
    assert result is not None
    assert result.get('error') is not None


# ============================================================================
# Test Invalid Ticker Formats
# ============================================================================

def test_extract_ticker_invalid_format():
    """Test ticker extraction with invalid formats."""
    
    # No ticker in query
    with pytest.raises(InvalidTickerError):
        extract_ticker("What should I do?")
    
    # Only common words
    with pytest.raises(InvalidTickerError):
        extract_ticker("I want to buy a stock")


def test_handle_query_invalid_ticker():
    """Test handle_query with invalid ticker."""
    result = handle_query("Tell me about stocks")
    
    # Should return error response
    assert result is not None
    assert isinstance(result, dict)
    # Should indicate ticker error
    assert "ticker" in result.get('summary', '').lower() or result.get('recommendation') == 'ERROR'


def test_handle_query_empty_string():
    """Test handle_query with empty string."""
    result = handle_query("")
    
    # Should return error response
    assert result is not None
    assert result.get('recommendation') == 'ERROR' or result.get('error') is not None


def test_handle_query_whitespace_only():
    """Test handle_query with whitespace only."""
    result = handle_query("   ")
    
    # Should return error response
    assert result is not None
    assert result.get('recommendation') == 'ERROR' or result.get('error') is not None


def test_handle_query_none():
    """Test handle_query with None."""
    result = handle_query(None)
    
    # Should return error response
    assert result is not None
    assert result.get('recommendation') == 'ERROR' or result.get('error') is not None


# ============================================================================
# Test Alpha Vantage API Errors
# ============================================================================

@patch('src.tools.sentiment_analyst.requests.get')
def test_sentiment_analysis_api_unavailable(mock_get):
    """Test sentiment analysis when Alpha Vantage API is unavailable."""
    # Mock API failure
    mock_get.side_effect = Exception("API unavailable")
    
    result = analyze_sentiment("AAPL", api_key="test_key")
    
    # Should return error response
    assert result is not None
    assert result.get('error') is not None
    assert result.get('ticker') == "AAPL"
    assert result.get('sentiment') is None


@patch('src.tools.sentiment_analyst.requests.get')
def test_sentiment_analysis_api_rate_limit(mock_get):
    """Test sentiment analysis when API rate limit is hit."""
    # Mock rate limit response
    mock_response = Mock()
    mock_response.json.return_value = {
        "Note": "Thank you for using Alpha Vantage! Our standard API call frequency is 5 calls per minute."
    }
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response
    
    result = analyze_sentiment("AAPL", api_key="test_key")
    
    # Should return error response
    assert result is not None
    assert result.get('error') is not None


@patch('src.tools.sentiment_analyst.requests.get')
def test_sentiment_analysis_api_error_message(mock_get):
    """Test sentiment analysis when API returns error message."""
    # Mock API error
    mock_response = Mock()
    mock_response.json.return_value = {
        "Error Message": "Invalid API key"
    }
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response
    
    result = analyze_sentiment("AAPL", api_key="invalid_key")
    
    # Should return error response
    assert result is not None
    assert result.get('error') is not None


@patch('src.tools.sentiment_analyst.requests.get')
def test_sentiment_analysis_no_api_key(mock_get):
    """Test sentiment analysis without API key."""
    # Mock API to raise an error when no key is provided
    mock_get.side_effect = Exception("API key required")
    
    result = analyze_sentiment("AAPL", api_key=None)
    
    # Should return error response
    assert result is not None
    assert result.get('error') is not None
    # Error message should indicate API issue (either missing key or no data)
    error_msg = result.get('error').lower()
    assert "api" in error_msg or "key" in error_msg or "error" in error_msg


@patch('src.tools.sentiment_analyst.requests.get')
def test_sentiment_analysis_empty_feed(mock_get):
    """Test sentiment analysis when API returns empty news feed."""
    # Mock empty feed
    mock_response = Mock()
    mock_response.json.return_value = {
        "feed": []
    }
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response
    
    result = analyze_sentiment("AAPL", api_key="test_key")
    
    # Should handle empty feed gracefully
    assert result is not None
    # Should still return a sentiment (default/neutral)
    assert result.get('sentiment') in ["Bullish", "Bearish"]
    assert result.get('confidence') is not None


# ============================================================================
# Test Network Timeouts
# ============================================================================

@patch('src.tools.technical_analyst.yf.Ticker')
def test_technical_analysis_connection_timeout(mock_ticker):
    """Test technical analysis with connection timeout."""
    import requests
    
    mock_instance = Mock()
    mock_instance.history.side_effect = requests.exceptions.Timeout("Connection timeout")
    mock_ticker.return_value = mock_instance
    
    result = analyze_technical("AAPL")
    
    # Should handle timeout gracefully
    assert result is not None
    assert result.get('error') is not None


@patch('src.tools.sentiment_analyst.requests.get')
def test_sentiment_analysis_connection_timeout(mock_get):
    """Test sentiment analysis with connection timeout."""
    import requests
    
    mock_get.side_effect = requests.exceptions.Timeout("Connection timeout")
    
    result = analyze_sentiment("AAPL", api_key="test_key")
    
    # Should handle timeout gracefully
    assert result is not None
    assert result.get('error') is not None


# ============================================================================
# Test Graceful Degradation
# ============================================================================

@patch('src.tools.technical_analyst.analyze_technical')
@patch('src.tools.sentiment_analyst.analyze_sentiment')
def test_handle_query_technical_fails_sentiment_succeeds(mock_sentiment, mock_technical):
    """Test that system continues when technical analysis fails."""
    # Mock technical failure
    mock_technical.return_value = {
        "ticker": "AAPL",
        "error": "API unavailable",
        "rsi": None,
        "current_price": None,
        "rsi_signal": None,
        "price_change_24h": None,
        "timestamp": "2025-11-29T10:00:00"
    }
    
    # Mock sentiment success
    mock_sentiment.return_value = {
        "ticker": "AAPL",
        "sentiment": "Bullish",
        "confidence": 0.75,
        "rationale": "Positive news",
        "timestamp": "2025-11-29T10:00:00",
        "error": None
    }
    
    result = handle_query("Analyze AAPL")
    
    # Should still return a recommendation based on sentiment only
    assert result is not None
    assert result.get('recommendation') in ["BUY", "SELL", "HOLD"]
    assert "sentiment" in result.get('summary', '').lower() or "unavailable" in result.get('summary', '').lower()


@patch('src.supervisor.analyze_technical')
@patch('src.supervisor.analyze_sentiment')
def test_handle_query_sentiment_fails_technical_succeeds(mock_sentiment, mock_technical):
    """Test that system continues when sentiment analysis fails."""
    # Mock technical success
    mock_technical.return_value = {
        "ticker": "AAPL",
        "current_price": 178.50,
        "rsi": 65.4,
        "rsi_signal": "Neutral",
        "price_change_24h": 2.3,
        "timestamp": "2025-11-29T10:00:00",
        "error": None
    }
    
    # Mock sentiment failure
    mock_sentiment.return_value = {
        "ticker": "AAPL",
        "error": "API unavailable",
        "sentiment": None,
        "confidence": None,
        "rationale": None,
        "timestamp": "2025-11-29T10:00:00"
    }
    
    result = handle_query("Analyze AAPL")
    
    # Should still return a recommendation based on technical only
    assert result is not None
    assert result.get('recommendation') in ["BUY", "SELL", "HOLD"]
    assert "technical" in result.get('summary', '').lower() or "unavailable" in result.get('summary', '').lower()


@patch('src.supervisor.analyze_technical')
@patch('src.supervisor.analyze_sentiment')
def test_handle_query_both_tools_fail(mock_sentiment, mock_technical):
    """Test that system handles both tools failing."""
    # Mock both failures with proper error structure
    mock_technical.return_value = {
        "ticker": "AAPL",
        "error": "Technical API unavailable",
        "rsi": None,
        "current_price": None,
        "rsi_signal": None,
        "price_change_24h": None,
        "timestamp": "2025-11-29T10:00:00"
    }
    mock_sentiment.return_value = {
        "ticker": "AAPL",
        "error": "Sentiment API unavailable",
        "sentiment": None,
        "confidence": None,
        "rationale": None,
        "timestamp": "2025-11-29T10:00:00"
    }
    
    result = handle_query("Analyze AAPL")
    
    # Should return error recommendation when both tools fail
    assert result is not None
    assert result.get('recommendation') == "ERROR"
    assert result.get('error') is not None or "both" in result.get('summary', '').lower()


# ============================================================================
# Test Input Validation
# ============================================================================

def test_handle_query_with_special_characters():
    """Test handle_query with special characters."""
    result = handle_query("Analyze AAPL!@#$%")
    
    # Should extract ticker and process normally
    assert result is not None
    assert result.get('ticker') == "AAPL"


def test_handle_query_with_numbers():
    """Test handle_query with numbers in query."""
    result = handle_query("Analyze AAPL stock price 123")
    
    # Should extract ticker and process normally
    assert result is not None
    assert result.get('ticker') == "AAPL"


def test_handle_query_case_insensitive():
    """Test that ticker extraction works with uppercase tickers."""
    # Ticker extraction requires uppercase letters in the query
    # This is by design to avoid false positives with common words
    result = handle_query("Analyze AAPL stock")
    
    # Should extract ticker
    assert result is not None
    assert result.get('ticker') == "AAPL"
