"""
Integration Tests for End-to-End Flow

These tests verify the complete system flow from query to recommendation
using real ticker symbols and actual API calls (when available).
"""

import pytest
import os
from src.supervisor import handle_query
from src.lambda_handler import lambda_handler, parse_bedrock_event, format_bedrock_response


# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


# ============================================================================
# End-to-End Flow Tests
# ============================================================================

def test_e2e_complete_flow_with_real_ticker():
    """
    Test complete flow from query to recommendation with a real ticker.
    
    This test uses AAPL as a well-known ticker that should always have data.
    Note: Requires internet connection and working yfinance API.
    """
    query = "Analyze AAPL stock"
    
    # Execute complete flow
    result = handle_query(query)
    
    # Verify result structure
    assert result is not None
    assert isinstance(result, dict)
    
    # Verify required fields
    assert 'ticker' in result
    assert 'recommendation' in result
    assert 'technical_analysis' in result
    assert 'sentiment_analysis' in result
    assert 'summary' in result
    assert 'confidence' in result
    assert 'timestamp' in result
    
    # Verify ticker was extracted correctly
    assert result['ticker'] == 'AAPL'
    
    # Verify recommendation is valid
    assert result['recommendation'] in ['BUY', 'SELL', 'HOLD', 'ERROR']
    
    # Verify technical analysis (should succeed with yfinance)
    tech = result['technical_analysis']
    if tech and not tech.get('error'):
        assert tech['ticker'] == 'AAPL'
        assert tech['current_price'] is not None
        assert tech['current_price'] > 0
        assert tech['rsi'] is not None
        assert 0 <= tech['rsi'] <= 100
        assert tech['rsi_signal'] in ['Overbought', 'Oversold', 'Neutral']
    
    # Verify sentiment analysis (may fail without API key)
    sent = result['sentiment_analysis']
    if sent and not sent.get('error'):
        assert sent['ticker'] == 'AAPL'
        assert sent['sentiment'] in ['Bullish', 'Bearish']
        assert 0 <= sent['confidence'] <= 1
    
    # Verify confidence score
    assert 0 <= result['confidence'] <= 1
    
    # Verify summary is present
    assert len(result['summary']) > 0


def test_e2e_with_multiple_tickers():
    """
    Test end-to-end flow with multiple well-known tickers.
    """
    tickers = ['AAPL', 'MSFT', 'GOOGL']
    
    for ticker in tickers:
        query = f"What about {ticker}?"
        result = handle_query(query)
        
        # Basic validation
        assert result is not None
        assert result['ticker'] == ticker
        assert result['recommendation'] in ['BUY', 'SELL', 'HOLD', 'ERROR']
        
        # Should have at least technical analysis (yfinance should work)
        tech = result['technical_analysis']
        assert tech is not None
        
        if not tech.get('error'):
            assert tech['rsi'] is not None
            assert 0 <= tech['rsi'] <= 100


def test_e2e_with_technical_keywords():
    """
    Test that technical keywords trigger appropriate tool selection.
    """
    query = "What's the technical analysis for MSFT?"
    result = handle_query(query)
    
    assert result is not None
    assert result['ticker'] == 'MSFT'
    
    # Technical analysis should be present
    tech = result['technical_analysis']
    assert tech is not None
    
    if not tech.get('error'):
        assert tech['rsi'] is not None


def test_e2e_with_sentiment_keywords():
    """
    Test that sentiment keywords trigger appropriate tool selection.
    """
    query = "What's the sentiment for TSLA?"
    result = handle_query(query)
    
    assert result is not None
    assert result['ticker'] == 'TSLA'
    
    # Sentiment analysis should be attempted (may have error without API key)
    # The result should still contain sentiment_analysis field
    assert 'sentiment_analysis' in result
    
    # Note: With sentiment keywords, only sentiment tool may be called
    # depending on the implementation of determine_tools()


# ============================================================================
# Lambda Handler Integration Tests
# ============================================================================

class MockLambdaContext:
    """Mock AWS Lambda context for testing."""
    def __init__(self):
        self.request_id = "test-request-123"
        self.function_name = "trading-supervisor-test"
        self.memory_limit_in_mb = 512


def test_e2e_lambda_handler_with_bedrock_event():
    """
    Test complete Lambda handler flow with Bedrock Agent event.
    """
    # Create a Bedrock Agent event
    event = {
        "messageVersion": "1.0",
        "agent": {
            "name": "TradingSupervisor",
            "id": "agent-test-123",
            "alias": "test",
            "version": "1"
        },
        "inputText": "Analyze AAPL",
        "sessionId": "session-test-123",
        "sessionAttributes": {},
        "promptSessionAttributes": {}
    }
    
    context = MockLambdaContext()
    
    # Execute Lambda handler
    response = lambda_handler(event, context)
    
    # Verify response structure
    assert response is not None
    assert isinstance(response, dict)
    
    # Verify Bedrock response format
    assert 'messageVersion' in response
    assert response['messageVersion'] == '1.0'
    
    assert 'response' in response
    response_obj = response['response']
    
    assert 'httpStatusCode' in response_obj
    assert response_obj['httpStatusCode'] in [200, 500]
    
    assert 'responseBody' in response_obj
    assert 'application/json' in response_obj['responseBody']
    
    # Verify session attributes
    assert 'sessionAttributes' in response
    session_attrs = response['sessionAttributes']
    assert 'lastTicker' in session_attrs
    assert 'lastRecommendation' in session_attrs


def test_e2e_lambda_handler_with_invalid_event():
    """
    Test Lambda handler with invalid event format.
    """
    # Invalid event (missing inputText)
    event = {
        "messageVersion": "1.0",
        "sessionId": "session-test-123"
    }
    
    context = MockLambdaContext()
    
    # Execute Lambda handler
    response = lambda_handler(event, context)
    
    # Should return error response
    assert response is not None
    assert response['response']['httpStatusCode'] == 500


# ============================================================================
# Component Integration Tests
# ============================================================================

def test_e2e_supervisor_with_both_tools():
    """
    Test supervisor orchestration with both tools.
    """
    query = "Give me a complete analysis of AAPL"
    result = handle_query(query)
    
    assert result is not None
    assert result['ticker'] == 'AAPL'
    
    # Both tools should be invoked
    assert result['technical_analysis'] is not None
    assert result['sentiment_analysis'] is not None
    
    # Should have a synthesized recommendation
    assert result['recommendation'] in ['BUY', 'SELL', 'HOLD', 'ERROR']
    assert len(result['summary']) > 0


def test_e2e_recommendation_synthesis():
    """
    Test that recommendation synthesis works correctly.
    
    This test verifies that the supervisor correctly combines
    technical and sentiment signals into a recommendation.
    """
    query = "Analyze MSFT"
    result = handle_query(query)
    
    assert result is not None
    
    tech = result['technical_analysis']
    sent = result['sentiment_analysis']
    rec = result['recommendation']
    
    # If both tools succeeded, verify synthesis logic
    if tech and not tech.get('error') and sent and not sent.get('error'):
        rsi_signal = tech['rsi_signal']
        sentiment = sent['sentiment']
        
        # Verify synthesis follows expected patterns
        if rsi_signal == 'Overbought' and sentiment == 'Bearish':
            assert rec == 'SELL', "Overbought + Bearish should be SELL"
        elif rsi_signal == 'Oversold' and sentiment == 'Bullish':
            assert rec == 'BUY', "Oversold + Bullish should be BUY"
        elif rsi_signal == 'Neutral' and sentiment == 'Bullish':
            assert rec == 'BUY', "Neutral + Bullish should be BUY"
        elif rsi_signal == 'Neutral' and sentiment == 'Bearish':
            assert rec == 'SELL', "Neutral + Bearish should be SELL"
        else:
            # Conflicting signals should result in HOLD
            assert rec == 'HOLD', f"Conflicting signals ({rsi_signal} + {sentiment}) should be HOLD"


# ============================================================================
# Real-World Scenario Tests
# ============================================================================

def test_e2e_realistic_user_queries():
    """
    Test with realistic user queries.
    """
    queries = [
        "Should I buy AAPL?",
        "What do you think about MSFT stock?",
        "Is GOOGL a good investment?",
        "Tell me about TSLA",
        "Analyze AMZN for me"
    ]
    
    for query in queries:
        result = handle_query(query)
        
        # All queries should return valid results
        assert result is not None
        assert result['recommendation'] in ['BUY', 'SELL', 'HOLD', 'ERROR']
        assert result['ticker'] is not None
        assert len(result['summary']) > 0


def test_e2e_with_api_key_environment_variable():
    """
    Test that system uses API key from environment variable.
    """
    # Save original API key
    original_key = os.environ.get('ALPHA_VANTAGE_API_KEY')
    
    try:
        # Set a test API key
        os.environ['ALPHA_VANTAGE_API_KEY'] = 'test_key_12345'
        
        query = "Analyze AAPL"
        result = handle_query(query)
        
        # Should attempt to use the API key
        # (will likely fail with invalid key, but that's expected)
        assert result is not None
        
    finally:
        # Restore original API key
        if original_key:
            os.environ['ALPHA_VANTAGE_API_KEY'] = original_key
        elif 'ALPHA_VANTAGE_API_KEY' in os.environ:
            del os.environ['ALPHA_VANTAGE_API_KEY']


# ============================================================================
# Performance and Reliability Tests
# ============================================================================

@pytest.mark.slow
def test_e2e_multiple_sequential_requests():
    """
    Test system reliability with multiple sequential requests.
    
    This test is marked as 'slow' because it makes multiple API calls.
    """
    tickers = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'AMZN']
    
    results = []
    for ticker in tickers:
        query = f"Analyze {ticker}"
        result = handle_query(query)
        results.append(result)
    
    # All requests should succeed
    assert len(results) == len(tickers)
    
    for i, result in enumerate(results):
        assert result is not None
        assert result['ticker'] == tickers[i]
        assert result['recommendation'] in ['BUY', 'SELL', 'HOLD', 'ERROR']


def test_e2e_response_time_reasonable():
    """
    Test that response time is reasonable (< 30 seconds).
    
    This is important for Lambda timeout constraints.
    """
    import time
    
    query = "Analyze AAPL"
    
    start_time = time.time()
    result = handle_query(query)
    end_time = time.time()
    
    elapsed_time = end_time - start_time
    
    # Should complete within 30 seconds (Lambda timeout)
    assert elapsed_time < 30, f"Request took {elapsed_time:.2f}s, exceeds 30s timeout"
    
    # Verify result is valid
    assert result is not None
    assert result['recommendation'] in ['BUY', 'SELL', 'HOLD', 'ERROR']
