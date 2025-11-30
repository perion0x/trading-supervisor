"""
Property-based tests for Supervisor Agent.

These tests verify universal properties that should hold across all inputs.
"""

import pytest
import os
from hypothesis import given, strategies as st, settings
from unittest.mock import patch, MagicMock

from src.supervisor import (
    extract_ticker,
    determine_tools,
    synthesize_recommendation,
    handle_query,
    InvalidTickerError
)

# Set API key for tests
os.environ['ALPHA_VANTAGE_API_KEY'] = '14U5E6FZS0OZ4JES'


# Hypothesis strategies for generating test data

# Generate valid ticker symbols (1-5 uppercase ASCII letters only)
ticker_strategy = st.text(
    alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ',
    min_size=1,
    max_size=5
).filter(lambda t: t not in {'I', 'A', 'THE', 'AND', 'OR', 'BUT', 'FOR', 'TO', 'OF', 'IN', 'ON', 'AT', 'BY'})

# Generate query templates with ticker placeholder
query_templates = [
    "Analyze {}",
    "What about {} stock?",
    "Should I buy {}?",
    "Tell me about {}",
    "{} analysis please",
    "What's your take on {}?",
    "Is {} a good buy?",
]

# Generate queries with embedded tickers
@st.composite
def query_with_ticker_strategy(draw):
    ticker = draw(ticker_strategy)
    template = draw(st.sampled_from(query_templates))
    query = template.format(ticker)
    return query, ticker


# Feature: multi-agent-trading-supervisor, Property 1: Ticker extraction correctness
@given(data=query_with_ticker_strategy())
@settings(max_examples=100)
def test_ticker_extraction_correctness(data):
    """
    Property 1: Ticker extraction correctness
    Validates: Requirements 1.1
    
    For any user query containing a valid stock ticker symbol, the Supervisor
    Agent should correctly extract and identify the ticker symbol regardless of
    query phrasing or surrounding text.
    """
    query, expected_ticker = data
    
    try:
        extracted_ticker = extract_ticker(query)
        assert extracted_ticker == expected_ticker, \
            f"Expected {expected_ticker}, got {extracted_ticker} from query: {query}"
    except InvalidTickerError:
        # This should not happen with our generated queries
        pytest.fail(f"Failed to extract ticker from valid query: {query}")


# Feature: multi-agent-trading-supervisor, Property 2: Dual tool invocation
@given(ticker=ticker_strategy)
@settings(max_examples=100, deadline=None)
def test_dual_tool_invocation(ticker):
    """
    Property 2: Dual tool invocation
    Validates: Requirements 1.2
    
    For any general analysis query with a ticker symbol, the Supervisor Agent
    should invoke both the Technical Analyst Tool and the Sentiment Analyst Tool.
    """
    # Create a general query (no specific keywords)
    query = f"Analyze {ticker}"
    
    # Mock both tools to track invocations
    with patch('src.supervisor.analyze_technical') as mock_tech, \
         patch('src.supervisor.analyze_sentiment') as mock_sent:
        
        # Setup mocks to return valid data
        mock_tech.return_value = {
            "ticker": ticker,
            "current_price": 100.0,
            "rsi": 50.0,
            "rsi_signal": "Neutral",
            "price_change_24h": 0.0,
            "timestamp": "2025-11-29T00:00:00",
            "error": None
        }
        
        mock_sent.return_value = {
            "ticker": ticker,
            "sentiment": "Bullish",
            "confidence": 0.7,
            "rationale": "Test rationale",
            "timestamp": "2025-11-29T00:00:00",
            "error": None
        }
        
        # Call handle_query
        result = handle_query(query)
        
        # Verify both tools were called
        assert mock_tech.called, "Technical Analyst Tool should be called for general query"
        assert mock_sent.called, "Sentiment Analyst Tool should be called for general query"
        
        # Verify ticker was passed correctly
        mock_tech.assert_called_once_with(ticker)
        mock_sent.assert_called_once()


# Feature: multi-agent-trading-supervisor, Property 3: Complete recommendation synthesis
@given(ticker=ticker_strategy)
@settings(max_examples=100)
def test_complete_recommendation_synthesis(ticker):
    """
    Property 3: Complete recommendation synthesis
    Validates: Requirements 1.3, 6.4
    
    For any pair of tool results (technical and sentiment), the Supervisor Agent
    should produce a trading recommendation containing all required fields: ticker,
    recommendation type, technical analysis data, sentiment analysis data, and summary.
    """
    # Create mock tool results
    technical_result = {
        "ticker": ticker,
        "current_price": 150.0,
        "rsi": 65.0,
        "rsi_signal": "Neutral",
        "price_change_24h": 2.5,
        "timestamp": "2025-11-29T00:00:00",
        "error": None
    }
    
    sentiment_result = {
        "ticker": ticker,
        "sentiment": "Bullish",
        "confidence": 0.75,
        "rationale": "Positive news sentiment",
        "timestamp": "2025-11-29T00:00:00",
        "error": None
    }
    
    # Synthesize recommendation
    recommendation = synthesize_recommendation(ticker, technical_result, sentiment_result)
    
    # Verify all required fields are present
    assert 'ticker' in recommendation, "Missing ticker field"
    assert recommendation['ticker'] == ticker, "Ticker mismatch"
    
    assert 'recommendation' in recommendation, "Missing recommendation field"
    assert recommendation['recommendation'] in ['BUY', 'SELL', 'HOLD'], \
        f"Invalid recommendation: {recommendation['recommendation']}"
    
    assert 'technical_analysis' in recommendation, "Missing technical_analysis field"
    assert recommendation['technical_analysis'] is not None, "Technical analysis should not be None"
    
    assert 'sentiment_analysis' in recommendation, "Missing sentiment_analysis field"
    assert recommendation['sentiment_analysis'] is not None, "Sentiment analysis should not be None"
    
    assert 'summary' in recommendation, "Missing summary field"
    assert isinstance(recommendation['summary'], str), "Summary should be a string"
    assert len(recommendation['summary']) > 0, "Summary should not be empty"
    
    assert 'confidence' in recommendation, "Missing confidence field"
    assert isinstance(recommendation['confidence'], (int, float)), "Confidence should be numeric"
    assert 0.0 <= recommendation['confidence'] <= 1.0, "Confidence should be between 0 and 1"
    
    assert 'timestamp' in recommendation, "Missing timestamp field"


# Feature: multi-agent-trading-supervisor, Property 4: Invalid ticker rejection
@given(invalid_query=st.text(alphabet=st.characters(blacklist_categories=('Lu',)), min_size=5, max_size=50))
@settings(max_examples=100)
def test_invalid_ticker_rejection(invalid_query):
    """
    Property 4: Invalid ticker rejection
    Validates: Requirements 1.4
    
    For any invalid or malformed ticker symbol, the Supervisor Agent should return
    an error response indicating the ticker is not recognized, without attempting analysis.
    """
    # Skip if query accidentally contains uppercase letters
    if any(c.isupper() for c in invalid_query):
        return
    
    try:
        extract_ticker(invalid_query)
        # If we get here, extraction succeeded when it shouldn't have
        pytest.fail(f"Should have raised InvalidTickerError for query: {invalid_query}")
    except InvalidTickerError:
        # This is expected
        pass


# Feature: multi-agent-trading-supervisor, Property 13: Query-based tool selection (technical keywords)
@given(ticker=ticker_strategy)
@settings(max_examples=100)
def test_query_based_tool_selection_technical(ticker):
    """
    Property 13: Query-based tool selection (technical keywords)
    Validates: Requirements 6.1
    
    For any user query containing technical analysis keywords (e.g., "RSI",
    "technical", "price", "momentum"), the Supervisor Agent should invoke the
    Technical Analyst Tool.
    """
    # Technical keywords
    technical_queries = [
        f"What is the RSI for {ticker}?",
        f"Show me technical analysis for {ticker}",
        f"What's the price momentum of {ticker}?",
        f"Is {ticker} overbought?",
    ]
    
    for query in technical_queries:
        tools = determine_tools(query)
        assert 'technical' in tools, \
            f"Technical tool should be selected for query: {query}"


# Feature: multi-agent-trading-supervisor, Property 14: Query-based tool selection (sentiment keywords)
@given(ticker=ticker_strategy)
@settings(max_examples=100)
def test_query_based_tool_selection_sentiment(ticker):
    """
    Property 14: Query-based tool selection (sentiment keywords)
    Validates: Requirements 6.2
    
    For any user query containing sentiment keywords (e.g., "sentiment", "news",
    "bullish", "bearish"), the Supervisor Agent should invoke the Sentiment Analyst Tool.
    """
    # Sentiment keywords
    sentiment_queries = [
        f"What is the sentiment on {ticker}?",
        f"Is {ticker} bullish or bearish?",
        f"What's the news sentiment for {ticker}?",
        f"How do people feel about {ticker}?",
    ]
    
    for query in sentiment_queries:
        tools = determine_tools(query)
        assert 'sentiment' in tools, \
            f"Sentiment tool should be selected for query: {query}"


# Feature: multi-agent-trading-supervisor, Property 15: Default comprehensive analysis
@given(ticker=ticker_strategy)
@settings(max_examples=100)
def test_default_comprehensive_analysis(ticker):
    """
    Property 15: Default comprehensive analysis
    Validates: Requirements 6.3
    
    For any general query without specific tool keywords (e.g., "Analyze AAPL"),
    the Supervisor Agent should invoke both tools.
    """
    # General queries without specific keywords
    general_queries = [
        f"Analyze {ticker}",
        f"What about {ticker}?",
        f"Tell me about {ticker}",
        f"Should I invest in {ticker}?",
    ]
    
    for query in general_queries:
        tools = determine_tools(query)
        assert 'technical' in tools and 'sentiment' in tools, \
            f"Both tools should be selected for general query: {query}"


# Feature: multi-agent-trading-supervisor, Property 16: Graceful degradation on tool failure
@given(ticker=ticker_strategy)
@settings(max_examples=100)
def test_graceful_degradation(ticker):
    """
    Property 16: Graceful degradation on tool failure
    Validates: Requirements 6.5
    
    For any scenario where one tool fails, the Supervisor Agent should continue
    processing with the available tool results and clearly indicate which tool
    failed in the response.
    """
    # Test case 1: Technical fails, sentiment succeeds
    technical_failed = {"error": "API unavailable"}
    sentiment_success = {
        "ticker": ticker,
        "sentiment": "Bullish",
        "confidence": 0.7,
        "rationale": "Positive sentiment",
        "timestamp": "2025-11-29T00:00:00",
        "error": None
    }
    
    result = synthesize_recommendation(ticker, technical_failed, sentiment_success)
    
    assert result['recommendation'] in ['BUY', 'SELL', 'HOLD'], \
        "Should still provide recommendation with partial data"
    assert 'sentiment' in result['summary'].lower() or 'unavailable' in result['summary'].lower(), \
        "Summary should indicate which tool succeeded/failed"
    
    # Test case 2: Sentiment fails, technical succeeds
    technical_success = {
        "ticker": ticker,
        "current_price": 100.0,
        "rsi": 45.0,
        "rsi_signal": "Neutral",
        "price_change_24h": 1.0,
        "timestamp": "2025-11-29T00:00:00",
        "error": None
    }
    sentiment_failed = {"error": "Rate limit exceeded"}
    
    result = synthesize_recommendation(ticker, technical_success, sentiment_failed)
    
    assert result['recommendation'] in ['BUY', 'SELL', 'HOLD'], \
        "Should still provide recommendation with partial data"
    assert 'technical' in result['summary'].lower() or 'unavailable' in result['summary'].lower(), \
        "Summary should indicate which tool succeeded/failed"


# Feature: multi-agent-trading-supervisor, Property 17: Input validation
@given(invalid_input=st.one_of(
    st.none(),
    st.integers(),
    st.floats(),
    st.booleans(),
    st.lists(st.text()),
    st.dictionaries(st.text(), st.text()),
    st.just(""),  # Empty string
    st.just("   "),  # Whitespace only
    st.text(min_size=1001, max_size=2000)  # Too long
))
@settings(max_examples=100)
def test_input_validation(invalid_input):
    """
    Property 17: Input validation
    Validates: Requirements 7.3
    
    For any input that is not a valid query format (wrong type, missing required
    fields), the system should validate the input and return a clear error message
    without crashing.
    """
    # Call handle_query with invalid input
    result = handle_query(invalid_input)
    
    # Verify the system didn't crash and returned an error response
    assert isinstance(result, dict), "Should return a dictionary response"
    assert 'success' in result or 'error' in result or 'recommendation' in result, \
        "Response should contain error information"
    
    # If there's an error field, verify it has a clear message
    if 'error' in result and result['error'] is not None:
        if isinstance(result['error'], dict):
            assert 'message' in result['error'], "Error should have a message"
            assert isinstance(result['error']['message'], str), "Error message should be a string"
            assert len(result['error']['message']) > 0, "Error message should not be empty"
        elif isinstance(result['error'], str):
            assert len(result['error']) > 0, "Error message should not be empty"
    
    # Verify recommendation is ERROR for invalid inputs
    if 'recommendation' in result:
        assert result['recommendation'] == 'ERROR', \
            f"Invalid input should result in ERROR recommendation, got {result['recommendation']}"
    
    # Verify summary contains error information
    if 'summary' in result:
        assert isinstance(result['summary'], str), "Summary should be a string"
        assert len(result['summary']) > 0, "Summary should not be empty"
