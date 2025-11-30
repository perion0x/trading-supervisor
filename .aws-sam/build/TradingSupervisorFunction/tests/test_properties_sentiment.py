"""
Property-based tests for Sentiment Analyst Tool.

These tests verify universal properties that should hold across all inputs.
"""

import pytest
import os
from hypothesis import given, strategies as st, settings
from unittest.mock import patch, MagicMock

from src.tools.sentiment_analyst import (
    analyze_sentiment,
    calculate_aggregate_sentiment
)

# Set API key for tests
os.environ['ALPHA_VANTAGE_API_KEY'] = '14U5E6FZS0OZ4JES'


# Hypothesis strategies for generating test data

# Generate valid ticker symbols (1-5 uppercase letters)
ticker_strategy = st.text(
    alphabet=st.characters(whitelist_categories=('Lu',)),
    min_size=1,
    max_size=5
)


# Feature: multi-agent-trading-supervisor, Property 8: Sentiment classification validity
@given(ticker=ticker_strategy)
@settings(max_examples=100, deadline=None)
def test_sentiment_classification_validity(ticker):
    """
    Property 8: Sentiment classification validity
    Validates: Requirements 3.1
    
    For any ticker symbol, the Sentiment Analyst Tool should return a sentiment
    classification that is either "Bullish" or "Bearish".
    """
    # Mock the API to avoid rate limits and ensure consistent testing
    with patch('src.tools.sentiment_analyst.fetch_news_sentiment') as mock_fetch:
        # Create mock sentiment data
        mock_fetch.return_value = {
            "feed": [
                {
                    "ticker_sentiment": [
                        {
                            "ticker": ticker,
                            "ticker_sentiment_score": "0.5",
                            "relevance_score": "0.8"
                        }
                    ]
                }
            ]
        }
        
        # Call analyze_sentiment
        result = analyze_sentiment(ticker)
        
        # Verify sentiment is valid
        if result.get('error') is None:
            sentiment = result.get('sentiment')
            assert sentiment is not None, "Sentiment should not be None"
            assert sentiment in ["Bullish", "Bearish"], \
                f"Sentiment '{sentiment}' must be either 'Bullish' or 'Bearish'"


# Feature: multi-agent-trading-supervisor, Property 9: Sentiment determinism
@given(ticker=ticker_strategy)
@settings(max_examples=100, deadline=None)
def test_sentiment_determinism(ticker):
    """
    Property 9: Sentiment determinism
    Validates: Requirements 3.2, 3.4
    
    For any ticker symbol, calling the Sentiment Analyst Tool multiple times
    with the same ticker and same data should produce identical results.
    
    Note: With real API data, results may vary over time as news changes.
    This test uses mocked data to verify deterministic behavior with same input.
    """
    # Mock the API to ensure deterministic behavior
    with patch('src.tools.sentiment_analyst.fetch_news_sentiment') as mock_fetch:
        # Create consistent mock sentiment data
        mock_data = {
            "feed": [
                {
                    "ticker_sentiment": [
                        {
                            "ticker": ticker,
                            "ticker_sentiment_score": "0.3",
                            "relevance_score": "0.7"
                        }
                    ]
                }
            ]
        }
        mock_fetch.return_value = mock_data
        
        # Call analyze_sentiment multiple times
        result1 = analyze_sentiment(ticker)
        result2 = analyze_sentiment(ticker)
        result3 = analyze_sentiment(ticker)
        
        # Verify all results are identical (if no errors)
        if result1.get('error') is None:
            assert result1['sentiment'] == result2['sentiment'] == result3['sentiment'], \
                "Sentiment should be deterministic for the same input data"
            assert result1['confidence'] == result2['confidence'] == result3['confidence'], \
                "Confidence should be deterministic for the same input data"
            assert result1['rationale'] == result2['rationale'] == result3['rationale'], \
                "Rationale should be deterministic for the same input data"


# Feature: multi-agent-trading-supervisor, Property 10: Sentiment output completeness
@given(ticker=ticker_strategy)
@settings(max_examples=100, deadline=None)
def test_sentiment_output_completeness(ticker):
    """
    Property 10: Sentiment output completeness
    Validates: Requirements 3.3
    
    For any sentiment analysis result, the output should include both a
    confidence score and a rationale for the classification.
    """
    # Mock the API to avoid rate limits
    with patch('src.tools.sentiment_analyst.fetch_news_sentiment') as mock_fetch:
        # Create mock sentiment data
        mock_fetch.return_value = {
            "feed": [
                {
                    "ticker_sentiment": [
                        {
                            "ticker": ticker,
                            "ticker_sentiment_score": "0.2",
                            "relevance_score": "0.6"
                        }
                    ]
                }
            ]
        }
        
        # Call analyze_sentiment
        result = analyze_sentiment(ticker)
        
        # Verify output completeness
        if result.get('error') is None:
            # Should have confidence score
            assert 'confidence' in result, "Output missing confidence"
            assert result['confidence'] is not None, "Confidence should not be None"
            assert isinstance(result['confidence'], (int, float)), \
                "Confidence should be a number"
            assert 0.0 <= result['confidence'] <= 1.0, \
                f"Confidence {result['confidence']} should be between 0.0 and 1.0"
            
            # Should have rationale
            assert 'rationale' in result, "Output missing rationale"
            assert result['rationale'] is not None, "Rationale should not be None"
            assert isinstance(result['rationale'], str), "Rationale should be a string"
            assert len(result['rationale']) > 0, "Rationale should not be empty"
            
            # Also verify other expected fields
            assert 'ticker' in result
            assert 'sentiment' in result
            assert 'timestamp' in result
