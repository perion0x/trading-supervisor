"""
Custom exception classes for the Multi-Agentic Trading Supervisor system.

This module defines a hierarchy of exceptions used throughout the system
for error handling and validation.
"""


class TradingSystemError(Exception):
    """Base exception for all trading system errors.
    
    All custom exceptions in the system should inherit from this class.
    """
    pass


class InvalidTickerError(TradingSystemError):
    """Raised when a ticker symbol is invalid or cannot be extracted.
    
    Examples:
        - No ticker found in query
        - Malformed ticker format
        - Ticker contains invalid characters
    """
    pass


class InsufficientDataError(TradingSystemError):
    """Raised when there is insufficient data for analysis.
    
    Examples:
        - Not enough historical price data for RSI calculation
        - Empty dataset returned from API
        - Missing required data fields
    """
    pass


class ExternalAPIError(TradingSystemError):
    """Raised when an external API call fails.
    
    Examples:
        - yfinance API unavailable
        - Alpha Vantage API error
        - Network connectivity issues
        - API rate limiting
    """
    pass


class ToolExecutionError(TradingSystemError):
    """Raised when a tool fails to execute properly.
    
    Examples:
        - Tool invocation timeout
        - Unexpected exception during tool execution
        - Tool returns invalid data format
    """
    pass


class ValidationError(TradingSystemError):
    """Raised when input validation fails.
    
    Examples:
        - Invalid query format
        - Missing required fields
        - Data type mismatch
        - Value out of valid range
    """
    pass


class TimeoutError(TradingSystemError):
    """Raised when an operation exceeds its timeout limit.
    
    Examples:
        - API call timeout
        - Tool execution timeout
        - Data fetch timeout
    """
    pass
