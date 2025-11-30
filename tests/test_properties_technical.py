"""
Property-based tests for Technical Analyst Tool.

These tests verify universal properties that should hold across all inputs.
"""

import pytest
import pandas as pd
import numpy as np
from hypothesis import given, strategies as st, settings

from src.tools.technical_analyst import (
    calculate_rsi,
    interpret_rsi,
    analyze_technical,
    InsufficientDataError
)


# Hypothesis strategies for generating test data

# Generate valid price series (positive floats)
price_strategy = st.floats(min_value=1.0, max_value=10000.0, allow_nan=False, allow_infinity=False)

# Generate price series with enough data for RSI calculation (minimum 15 points)
price_series_strategy = st.lists(
    price_strategy,
    min_size=20,  # Enough for RSI calculation (14 + 1 for diff + buffer)
    max_size=100
)

# Generate valid ticker symbols (1-5 uppercase letters)
ticker_strategy = st.text(
    alphabet=st.characters(whitelist_categories=('Lu',)),
    min_size=1,
    max_size=5
)


# Feature: multi-agent-trading-supervisor, Property 18: RSI bounds invariant
@given(prices=price_series_strategy)
@settings(max_examples=100)
def test_rsi_bounds_invariant(prices):
    """
    Property 18: RSI bounds invariant
    Validates: Requirements 8.3
    
    For any price dataset, the calculated RSI value should always be 
    within the valid range of 0 to 100 (inclusive).
    """
    # Convert to pandas Series
    price_series = pd.Series(prices)
    
    try:
        # Calculate RSI
        rsi = calculate_rsi(price_series)
        
        # Verify RSI is within bounds
        assert 0 <= rsi <= 100, f"RSI {rsi} is outside valid range [0, 100]"
        
        # Verify RSI is a valid number (not NaN or infinity)
        assert not np.isnan(rsi), "RSI should not be NaN"
        assert not np.isinf(rsi), "RSI should not be infinite"
        
    except InsufficientDataError:
        # This is acceptable - not enough data for calculation
        pass


# Feature: multi-agent-trading-supervisor, Property 19: RSI formula correctness
@given(prices=price_series_strategy)
@settings(max_examples=100)
def test_rsi_formula_correctness(prices):
    """
    Property 19: RSI formula correctness
    Validates: Requirements 8.5
    
    For any price dataset with sufficient history, the RSI calculation should 
    match the result from a reference implementation using the standard formula:
    RSI = 100 - (100 / (1 + RS)), where RS is the ratio of average gains to 
    average losses over 14 periods.
    """
    # Convert to pandas Series
    price_series = pd.Series(prices)
    
    try:
        # Calculate RSI using our implementation
        our_rsi = calculate_rsi(price_series, period=14)
        
        # Reference implementation
        deltas = price_series.diff()
        gains = deltas.where(deltas > 0, 0.0)
        losses = -deltas.where(deltas < 0, 0.0)
        
        avg_gain = gains.rolling(window=14, min_periods=14).mean()
        avg_loss = losses.rolling(window=14, min_periods=14).mean()
        
        # Handle edge case where avg_loss is 0
        if avg_loss.iloc[-1] == 0:
            reference_rsi = 100.0
        elif avg_gain.iloc[-1] == 0:
            reference_rsi = 0.0
        else:
            rs = avg_gain.iloc[-1] / avg_loss.iloc[-1]
            reference_rsi = 100 - (100 / (1 + rs))
        
        # Verify our implementation matches reference (within floating point tolerance)
        assert abs(our_rsi - reference_rsi) < 0.01, \
            f"RSI mismatch: our={our_rsi}, reference={reference_rsi}"
        
    except InsufficientDataError:
        # This is acceptable - not enough data for calculation
        pass


# Feature: multi-agent-trading-supervisor, Property 5: Technical data retrieval
@given(ticker=ticker_strategy)
@settings(max_examples=100, deadline=None)
def test_technical_data_retrieval(ticker):
    """
    Property 5: Technical data retrieval
    Validates: Requirements 2.1
    
    For any valid ticker symbol, when the Technical Analyst Tool is invoked,
    it should attempt to retrieve price data from yfinance.
    """
    from unittest.mock import patch, MagicMock
    
    # Mock yfinance to avoid actual API calls
    with patch('src.tools.technical_analyst.yf.Ticker') as mock_ticker:
        # Create a mock that returns valid data
        mock_instance = MagicMock()
        mock_df = pd.DataFrame({
            'Close': [100.0 + i for i in range(30)]
        })
        mock_instance.history.return_value = mock_df
        mock_ticker.return_value = mock_instance
        
        # Call analyze_technical
        result = analyze_technical(ticker)
        
        # Verify yfinance was called with the ticker
        mock_ticker.assert_called_once_with(ticker)
        mock_instance.history.assert_called_once()


# Feature: multi-agent-trading-supervisor, Property 7: Technical output completeness
@given(ticker=ticker_strategy)
@settings(max_examples=100, deadline=None)
def test_technical_output_completeness(ticker):
    """
    Property 7: Technical output completeness
    Validates: Requirements 2.3
    
    For any successful technical analysis, the output should contain both 
    the RSI value and current price information.
    """
    from unittest.mock import patch, MagicMock
    
    # Mock yfinance to avoid actual API calls
    with patch('src.tools.technical_analyst.yf.Ticker') as mock_ticker:
        # Create a mock that returns valid data
        mock_instance = MagicMock()
        mock_df = pd.DataFrame({
            'Close': [100.0 + i for i in range(30)]
        })
        mock_instance.history.return_value = mock_df
        mock_ticker.return_value = mock_instance
        
        # Call analyze_technical
        result = analyze_technical(ticker)
        
        # Verify output completeness - should have RSI and current_price
        if result.get('error') is None:
            # Successful analysis should have both RSI and price
            assert 'rsi' in result, "Output missing RSI"
            assert result['rsi'] is not None, "RSI should not be None"
            assert 'current_price' in result, "Output missing current_price"
            assert result['current_price'] is not None, "Current price should not be None"
            
            # Also verify other expected fields
            assert 'ticker' in result
            assert 'rsi_signal' in result
            assert 'price_change_24h' in result
            assert 'timestamp' in result
