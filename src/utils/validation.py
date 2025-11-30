"""
Input validation utilities for the Multi-Agentic Trading Supervisor system.

This module provides functions for validating user inputs, data formats,
and system constraints.
"""

import re
from typing import Any, Dict, Optional, Union
from datetime import datetime

from src.exceptions import ValidationError


def validate_ticker(ticker: Any) -> str:
    """
    Validate a stock ticker symbol.
    
    Valid tickers are 1-5 uppercase letters (e.g., AAPL, MSFT, GOOGL).
    
    Args:
        ticker: Ticker symbol to validate
        
    Returns:
        Validated ticker symbol (uppercase)
        
    Raises:
        ValidationError: If ticker is invalid
    """
    if ticker is None:
        raise ValidationError("Ticker cannot be None")
    
    if not isinstance(ticker, str):
        raise ValidationError(
            f"Ticker must be a string, got {type(ticker).__name__}"
        )
    
    ticker = ticker.strip().upper()
    
    if not ticker:
        raise ValidationError("Ticker cannot be empty or whitespace only")
    
    if not re.match(r'^[A-Z]{1,5}$', ticker):
        raise ValidationError(
            f"Invalid ticker format: '{ticker}'. "
            "Ticker must be 1-5 uppercase letters (e.g., AAPL, MSFT)"
        )
    
    return ticker


def validate_query(query: Any) -> str:
    """
    Validate a user query string.
    
    Args:
        query: Query string to validate
        
    Returns:
        Validated query string
        
    Raises:
        ValidationError: If query is invalid
    """
    if query is None:
        raise ValidationError("Query cannot be None")
    
    if not isinstance(query, str):
        raise ValidationError(
            f"Query must be a string, got {type(query).__name__}"
        )
    
    query = query.strip()
    
    if not query:
        raise ValidationError("Query cannot be empty or whitespace only")
    
    if len(query) > 1000:
        raise ValidationError(
            f"Query too long: {len(query)} characters. Maximum is 1000 characters"
        )
    
    return query


def validate_rsi(rsi: Any) -> float:
    """
    Validate an RSI value.
    
    RSI must be a number between 0 and 100 (inclusive).
    
    Args:
        rsi: RSI value to validate
        
    Returns:
        Validated RSI value as float
        
    Raises:
        ValidationError: If RSI is invalid
    """
    if rsi is None:
        raise ValidationError("RSI cannot be None")
    
    if not isinstance(rsi, (int, float)):
        raise ValidationError(
            f"RSI must be a number, got {type(rsi).__name__}"
        )
    
    if not (0 <= rsi <= 100):
        raise ValidationError(
            f"RSI must be between 0 and 100, got {rsi}"
        )
    
    return float(rsi)


def validate_price(price: Any, field_name: str = "Price") -> float:
    """
    Validate a price value.
    
    Price must be a positive number.
    
    Args:
        price: Price value to validate
        field_name: Name of the field for error messages
        
    Returns:
        Validated price as float
        
    Raises:
        ValidationError: If price is invalid
    """
    if price is None:
        raise ValidationError(f"{field_name} cannot be None")
    
    if not isinstance(price, (int, float)):
        raise ValidationError(
            f"{field_name} must be a number, got {type(price).__name__}"
        )
    
    if price <= 0:
        raise ValidationError(
            f"{field_name} must be positive, got {price}"
        )
    
    return float(price)


def validate_confidence(confidence: Any) -> float:
    """
    Validate a confidence score.
    
    Confidence must be a number between 0.0 and 1.0 (inclusive).
    
    Args:
        confidence: Confidence score to validate
        
    Returns:
        Validated confidence as float
        
    Raises:
        ValidationError: If confidence is invalid
    """
    if confidence is None:
        raise ValidationError("Confidence cannot be None")
    
    if not isinstance(confidence, (int, float)):
        raise ValidationError(
            f"Confidence must be a number, got {type(confidence).__name__}"
        )
    
    if not (0.0 <= confidence <= 1.0):
        raise ValidationError(
            f"Confidence must be between 0.0 and 1.0, got {confidence}"
        )
    
    return float(confidence)


def validate_sentiment(sentiment: Any) -> str:
    """
    Validate a sentiment classification.
    
    Sentiment must be either "Bullish" or "Bearish".
    
    Args:
        sentiment: Sentiment classification to validate
        
    Returns:
        Validated sentiment string
        
    Raises:
        ValidationError: If sentiment is invalid
    """
    if sentiment is None:
        raise ValidationError("Sentiment cannot be None")
    
    if not isinstance(sentiment, str):
        raise ValidationError(
            f"Sentiment must be a string, got {type(sentiment).__name__}"
        )
    
    valid_sentiments = ["Bullish", "Bearish"]
    
    if sentiment not in valid_sentiments:
        raise ValidationError(
            f"Sentiment must be one of {valid_sentiments}, got '{sentiment}'"
        )
    
    return sentiment


def validate_recommendation(recommendation: Any) -> str:
    """
    Validate a trading recommendation.
    
    Recommendation must be "BUY", "SELL", or "HOLD".
    
    Args:
        recommendation: Trading recommendation to validate
        
    Returns:
        Validated recommendation string
        
    Raises:
        ValidationError: If recommendation is invalid
    """
    if recommendation is None:
        raise ValidationError("Recommendation cannot be None")
    
    if not isinstance(recommendation, str):
        raise ValidationError(
            f"Recommendation must be a string, got {type(recommendation).__name__}"
        )
    
    valid_recommendations = ["BUY", "SELL", "HOLD", "ERROR"]
    
    if recommendation not in valid_recommendations:
        raise ValidationError(
            f"Recommendation must be one of {valid_recommendations}, got '{recommendation}'"
        )
    
    return recommendation


def validate_api_key(api_key: Any) -> str:
    """
    Validate an API key.
    
    Args:
        api_key: API key to validate
        
    Returns:
        Validated API key string
        
    Raises:
        ValidationError: If API key is invalid
    """
    if api_key is None:
        raise ValidationError("API key cannot be None")
    
    if not isinstance(api_key, str):
        raise ValidationError(
            f"API key must be a string, got {type(api_key).__name__}"
        )
    
    api_key = api_key.strip()
    
    if not api_key:
        raise ValidationError("API key cannot be empty or whitespace only")
    
    if len(api_key) < 8:
        raise ValidationError("API key appears to be too short (minimum 8 characters)")
    
    return api_key


def format_error_response(
    error: Exception,
    ticker: Optional[str] = None,
    include_details: bool = True
) -> Dict[str, Any]:
    """
    Format an error into a standardized error response.
    
    Args:
        error: Exception that occurred
        ticker: Optional ticker symbol associated with the error
        include_details: Whether to include detailed error information
        
    Returns:
        Dictionary containing formatted error response
    """
    error_type = type(error).__name__
    error_message = str(error)
    
    # Map exception types to error codes
    error_code_map = {
        'InvalidTickerError': 'INVALID_TICKER',
        'InsufficientDataError': 'INSUFFICIENT_DATA',
        'ExternalAPIError': 'EXTERNAL_API_ERROR',
        'ToolExecutionError': 'TOOL_EXECUTION_ERROR',
        'ValidationError': 'VALIDATION_ERROR',
        'TimeoutError': 'TIMEOUT_ERROR',
    }
    
    error_code = error_code_map.get(error_type, 'UNKNOWN_ERROR')
    
    response = {
        "success": False,
        "ticker": ticker,
        "recommendation": "ERROR",
        "technical_analysis": None,
        "sentiment_analysis": None,
        "summary": error_message,
        "confidence": 0.0,
        "timestamp": datetime.now().isoformat(),
        "error": {
            "code": error_code,
            "message": error_message,
        }
    }
    
    if include_details:
        response["error"]["type"] = error_type
        response["error"]["details"] = (
            "Please check your input and try again. "
            "If the problem persists, contact support."
        )
    
    return response


def validate_dict_structure(
    data: Any,
    required_fields: list[str],
    field_name: str = "Data"
) -> Dict[str, Any]:
    """
    Validate that a dictionary contains required fields.
    
    Args:
        data: Data to validate
        required_fields: List of required field names
        field_name: Name of the data structure for error messages
        
    Returns:
        Validated dictionary
        
    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(data, dict):
        raise ValidationError(
            f"{field_name} must be a dictionary, got {type(data).__name__}"
        )
    
    missing_fields = [field for field in required_fields if field not in data]
    
    if missing_fields:
        raise ValidationError(
            f"{field_name} missing required fields: {', '.join(missing_fields)}"
        )
    
    return data
