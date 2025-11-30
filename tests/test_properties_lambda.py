"""
Property-Based Tests for AWS Lambda Handler and Bedrock Integration

These tests verify correctness properties for Lambda handler functions
using Hypothesis for property-based testing.
"""

import pytest
from hypothesis import given, strategies as st, settings
import json
from datetime import datetime

from src.lambda_handler import parse_bedrock_event, format_bedrock_response


# ============================================================================
# Hypothesis Strategies for Test Data Generation
# ============================================================================

# Generate valid ticker symbols (1-5 uppercase letters)
ticker_strategy = st.text(
    alphabet=st.characters(whitelist_categories=('Lu',), max_codepoint=90),
    min_size=1,
    max_size=5
)

# Generate valid query strings with embedded tickers
query_strategy = st.builds(
    lambda ticker, prefix, suffix: f"{prefix} {ticker} {suffix}",
    ticker=ticker_strategy,
    prefix=st.sampled_from(["Analyze", "What about", "Tell me about", "Check", "Should I buy"]),
    suffix=st.sampled_from(["stock", "please", "now", "today", ""])
)

# Generate session IDs
session_id_strategy = st.text(
    alphabet=st.characters(whitelist_categories=('L', 'N'), blacklist_characters='-'),
    min_size=5,
    max_size=20
).map(lambda s: f"session-{s}")

# Generate valid Bedrock Agent events
bedrock_event_strategy = st.builds(
    lambda query, session_id: {
        "messageVersion": "1.0",
        "agent": {
            "name": "TradingSupervisor",
            "id": "agent-123",
            "alias": "prod",
            "version": "1"
        },
        "inputText": query,
        "sessionId": session_id,
        "sessionAttributes": {},
        "promptSessionAttributes": {}
    },
    query=query_strategy,
    session_id=session_id_strategy
)

# Generate recommendation types
recommendation_strategy = st.sampled_from(["BUY", "SELL", "HOLD"])

# Generate sentiment types
sentiment_strategy = st.sampled_from(["Bullish", "Bearish"])

# Generate RSI signals
rsi_signal_strategy = st.sampled_from(["Overbought", "Oversold", "Neutral"])

# Generate valid RSI values (0-100)
rsi_strategy = st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False)

# Generate valid prices
price_strategy = st.floats(min_value=1.0, max_value=10000.0, allow_nan=False, allow_infinity=False)

# Generate confidence scores (0.0-1.0)
confidence_strategy = st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)

# Generate price change values
price_change_strategy = st.floats(min_value=-100, max_value=100, allow_nan=False, allow_infinity=False)

# Generate trading recommendation results
trading_result_strategy = st.builds(
    lambda ticker, rec, rsi, rsi_sig, price, price_change, sent, conf: {
        "ticker": ticker,
        "recommendation": rec,
        "technical_analysis": {
            "ticker": ticker,
            "current_price": price,
            "rsi": rsi,
            "rsi_signal": rsi_sig,
            "price_change_24h": price_change,
            "timestamp": datetime.now().isoformat()
        },
        "sentiment_analysis": {
            "ticker": ticker,
            "sentiment": sent,
            "confidence": conf,
            "rationale": f"Mock sentiment for {ticker}",
            "timestamp": datetime.now().isoformat()
        },
        "summary": f"{rec} recommendation for {ticker}",
        "confidence": conf,
        "timestamp": datetime.now().isoformat(),
        "error": None
    },
    ticker=ticker_strategy,
    rec=recommendation_strategy,
    rsi=rsi_strategy,
    rsi_sig=rsi_signal_strategy,
    price=price_strategy,
    price_change=price_change_strategy,
    sent=sentiment_strategy,
    conf=confidence_strategy
)


# ============================================================================
# Property 11: Bedrock Event Parsing
# Feature: multi-agent-trading-supervisor, Property 11: Bedrock event parsing
# Validates: Requirements 4.3
# ============================================================================

@given(bedrock_event_strategy)
@settings(max_examples=100)
def test_property_11_bedrock_event_parsing(event):
    """
    Property 11: Bedrock event parsing
    
    For any valid AWS Bedrock Agent event format, the Lambda handler should
    correctly parse and extract the user query.
    
    Validates: Requirements 4.3
    """
    # Parse the event
    extracted_query = parse_bedrock_event(event)
    
    # Property: Extracted query should match the inputText field
    assert extracted_query == event['inputText'], \
        f"Extracted query '{extracted_query}' does not match inputText '{event['inputText']}'"
    
    # Property: Extracted query should be a non-empty string
    assert isinstance(extracted_query, str), \
        f"Extracted query should be a string, got {type(extracted_query)}"
    
    assert len(extracted_query.strip()) > 0, \
        "Extracted query should not be empty or whitespace only"


@given(query_strategy, session_id_strategy)
@settings(max_examples=100)
def test_property_11_alternative_field_names(query, session_id):
    """
    Property 11 (variant): Bedrock event parsing with alternative field names
    
    The parser should handle alternative field names like 'query' or 'text'
    as fallbacks when 'inputText' is not present.
    
    Validates: Requirements 4.3
    """
    # Test with 'query' field
    event_with_query = {
        "messageVersion": "1.0",
        "query": query,
        "sessionId": session_id
    }
    
    extracted = parse_bedrock_event(event_with_query)
    assert extracted == query, \
        f"Should extract from 'query' field: expected '{query}', got '{extracted}'"
    
    # Test with 'text' field
    event_with_text = {
        "messageVersion": "1.0",
        "text": query,
        "sessionId": session_id
    }
    
    extracted = parse_bedrock_event(event_with_text)
    assert extracted == query, \
        f"Should extract from 'text' field: expected '{query}', got '{extracted}'"


def test_property_11_invalid_event_handling():
    """
    Property 11 (edge case): Invalid event handling
    
    The parser should raise appropriate errors for invalid events.
    
    Validates: Requirements 4.3
    """
    # Test with non-dict event
    with pytest.raises(ValueError, match="Event must be a dictionary"):
        parse_bedrock_event("not a dict")
    
    # Test with missing query fields
    with pytest.raises(ValueError, match="No query found in event"):
        parse_bedrock_event({"messageVersion": "1.0"})
    
    # Test with empty query
    with pytest.raises(ValueError, match="Query cannot be empty"):
        parse_bedrock_event({"inputText": "   "})
    
    # Test with non-string query
    with pytest.raises(ValueError, match="Query must be a string"):
        parse_bedrock_event({"inputText": 123})


# ============================================================================
# Property 12: Bedrock Response Formatting
# Feature: multi-agent-trading-supervisor, Property 12: Bedrock response formatting
# Validates: Requirements 4.4
# ============================================================================

@given(trading_result_strategy)
@settings(max_examples=100)
def test_property_12_bedrock_response_formatting(result):
    """
    Property 12: Bedrock response formatting
    
    For any trading recommendation generated by the system, the Lambda handler
    should format it according to AWS Bedrock Agent response specifications.
    
    Validates: Requirements 4.4
    """
    # Format the response
    bedrock_response = format_bedrock_response(result)
    
    # Property: Response must be a dictionary
    assert isinstance(bedrock_response, dict), \
        f"Response should be a dict, got {type(bedrock_response)}"
    
    # Property: Response must have required Bedrock fields
    assert "messageVersion" in bedrock_response, \
        "Response must contain 'messageVersion' field"
    
    assert "response" in bedrock_response, \
        "Response must contain 'response' field"
    
    assert "sessionAttributes" in bedrock_response, \
        "Response must contain 'sessionAttributes' field"
    
    # Property: messageVersion should be "1.0"
    assert bedrock_response["messageVersion"] == "1.0", \
        f"messageVersion should be '1.0', got '{bedrock_response['messageVersion']}'"
    
    # Property: response field should contain required sub-fields
    response_obj = bedrock_response["response"]
    assert "actionGroup" in response_obj, \
        "response must contain 'actionGroup' field"
    
    assert "httpStatusCode" in response_obj, \
        "response must contain 'httpStatusCode' field"
    
    assert "responseBody" in response_obj, \
        "response must contain 'responseBody' field"
    
    # Property: httpStatusCode should be 200 for successful results
    if not result.get('error') and result.get('recommendation') != 'ERROR':
        assert response_obj["httpStatusCode"] == 200, \
            f"Successful results should have status 200, got {response_obj['httpStatusCode']}"
    
    # Property: responseBody should contain application/json
    response_body = response_obj["responseBody"]
    assert "application/json" in response_body, \
        "responseBody must contain 'application/json' field"
    
    # Property: JSON body should be parseable
    json_body = response_body["application/json"]["body"]
    parsed_body = json.loads(json_body)
    
    assert "result" in parsed_body, \
        "JSON body must contain 'result' field"
    
    assert "message" in parsed_body, \
        "JSON body must contain 'message' field"
    
    # Property: sessionAttributes should contain relevant tracking info
    session_attrs = bedrock_response["sessionAttributes"]
    assert "lastTicker" in session_attrs, \
        "sessionAttributes must contain 'lastTicker'"
    
    assert "lastRecommendation" in session_attrs, \
        "sessionAttributes must contain 'lastRecommendation'"
    
    assert "timestamp" in session_attrs, \
        "sessionAttributes must contain 'timestamp'"
    
    # Property: Session attributes should match the result
    assert session_attrs["lastTicker"] == result.get("ticker", ""), \
        "lastTicker should match result ticker"
    
    assert session_attrs["lastRecommendation"] == result.get("recommendation", ""), \
        "lastRecommendation should match result recommendation"


@given(ticker_strategy)
@settings(max_examples=100)
def test_property_12_error_response_formatting(ticker):
    """
    Property 12 (variant): Error response formatting
    
    For any error result, the response should have appropriate error formatting
    and status codes.
    
    Validates: Requirements 4.4
    """
    # Create an error result
    error_result = {
        "ticker": ticker,
        "recommendation": "ERROR",
        "summary": "Analysis failed",
        "error": "Test error message",
        "timestamp": datetime.now().isoformat()
    }
    
    # Format the response
    bedrock_response = format_bedrock_response(error_result)
    
    # Property: Error responses should have status 500
    assert bedrock_response["response"]["httpStatusCode"] == 500, \
        f"Error responses should have status 500, got {bedrock_response['response']['httpStatusCode']}"
    
    # Property: Response message should indicate error
    json_body = bedrock_response["response"]["responseBody"]["application/json"]["body"]
    parsed_body = json.loads(json_body)
    
    assert "Error:" in parsed_body["message"], \
        "Error response message should contain 'Error:'"


def test_property_12_response_structure_completeness():
    """
    Property 12 (edge case): Response structure completeness
    
    Verify that all required fields are present even with minimal input.
    
    Validates: Requirements 4.4
    """
    # Minimal result
    minimal_result = {
        "ticker": "AAPL",
        "recommendation": "HOLD",
        "summary": "Test summary",
        "confidence": 0.5,
        "timestamp": datetime.now().isoformat()
    }
    
    response = format_bedrock_response(minimal_result)
    
    # Verify complete structure
    assert response["messageVersion"] == "1.0"
    assert "response" in response
    assert "sessionAttributes" in response
    assert response["response"]["httpStatusCode"] == 200
    assert "responseBody" in response["response"]
    assert "application/json" in response["response"]["responseBody"]
    
    # Verify JSON is valid
    json_body = response["response"]["responseBody"]["application/json"]["body"]
    parsed = json.loads(json_body)
    assert "result" in parsed
    assert "message" in parsed
