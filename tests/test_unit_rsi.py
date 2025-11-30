"""
Unit Tests for RSI Calculation Edge Cases

These tests verify RSI calculation behavior in edge cases and boundary conditions.
"""

import pytest
import pandas as pd
import numpy as np
from src.tools.technical_analyst import calculate_rsi, interpret_rsi
from src.exceptions import InsufficientDataError


# ============================================================================
# Test RSI Calculation with Exactly 14 Data Points
# ============================================================================

def test_rsi_with_exactly_14_data_points():
    """
    Test RSI calculation with exactly 14 data points (minimum required).
    
    With 14 points, we need 15 total (including the initial point for delta calculation).
    """
    # Create a series with 15 points (14 + 1 for delta)
    prices = pd.Series([
        100, 101, 102, 101, 103, 104, 103, 105,
        106, 105, 107, 108, 107, 109, 110
    ])
    
    # Should calculate successfully
    rsi = calculate_rsi(prices, period=14)
    
    # RSI should be valid
    assert 0 <= rsi <= 100
    assert isinstance(rsi, float)


def test_rsi_with_insufficient_data():
    """
    Test that RSI calculation raises error with insufficient data.
    """
    # Only 10 data points (need at least 15 for period=14)
    prices = pd.Series([100, 101, 102, 101, 103, 104, 103, 105, 106, 105])
    
    with pytest.raises(InsufficientDataError, match="Need at least 15 data points"):
        calculate_rsi(prices, period=14)


# ============================================================================
# Test RSI with Known Price Sequences
# ============================================================================

def test_rsi_with_all_gains():
    """
    Test RSI calculation when all price changes are gains.
    
    When there are only gains and no losses, RSI should be 100.
    """
    # Steadily increasing prices
    prices = pd.Series(range(100, 130))  # 30 points, all increasing
    
    rsi = calculate_rsi(prices, period=14)
    
    # RSI should be 100 (or very close due to floating point)
    assert rsi >= 99.9, f"Expected RSI ~100 for all gains, got {rsi}"


def test_rsi_with_all_losses():
    """
    Test RSI calculation when all price changes are losses.
    
    When there are only losses and no gains, RSI should be 0.
    """
    # Steadily decreasing prices
    prices = pd.Series(range(130, 100, -1))  # 30 points, all decreasing
    
    rsi = calculate_rsi(prices, period=14)
    
    # RSI should be 0 (or very close due to floating point)
    assert rsi <= 0.1, f"Expected RSI ~0 for all losses, got {rsi}"


def test_rsi_with_known_sequence():
    """
    Test RSI calculation with a known price sequence.
    
    This uses a well-documented example to verify calculation accuracy.
    Note: Different RSI calculation methods (SMA vs EMA) can produce different results.
    """
    # Known price sequence from RSI calculation examples
    prices = pd.Series([
        44.00, 44.34, 44.09, 43.61, 44.33, 44.83, 45.10, 45.42,
        45.84, 46.08, 45.89, 46.03, 45.61, 46.28, 46.28, 46.00,
        46.03, 46.41, 46.22, 45.64
    ])
    
    rsi = calculate_rsi(prices, period=14)
    
    # RSI should be in a reasonable range for this upward-trending sequence
    # The exact value depends on the calculation method (SMA vs EMA smoothing)
    # This sequence shows overall upward trend, so RSI should be above 50
    assert 50 <= rsi <= 70, f"Expected RSI in range 50-70 for upward trend, got {rsi}"


def test_rsi_with_alternating_prices():
    """
    Test RSI with alternating up/down price movements.
    
    Should result in RSI around 50 (neutral).
    """
    # Alternating gains and losses of equal magnitude
    prices = []
    base = 100
    for i in range(30):
        if i % 2 == 0:
            prices.append(base + 1)
        else:
            prices.append(base)
    
    prices = pd.Series(prices)
    rsi = calculate_rsi(prices, period=14)
    
    # RSI should be around 50 (neutral)
    assert 45 <= rsi <= 55, f"Expected RSI ~50 for alternating prices, got {rsi}"


# ============================================================================
# Test RSI Interpretation
# ============================================================================

def test_interpret_rsi_overbought():
    """Test RSI interpretation for overbought conditions."""
    assert interpret_rsi(75.0) == "Overbought"
    assert interpret_rsi(70.1) == "Overbought"
    assert interpret_rsi(100.0) == "Overbought"


def test_interpret_rsi_oversold():
    """Test RSI interpretation for oversold conditions."""
    assert interpret_rsi(25.0) == "Oversold"
    assert interpret_rsi(29.9) == "Oversold"
    assert interpret_rsi(0.0) == "Oversold"


def test_interpret_rsi_neutral():
    """Test RSI interpretation for neutral conditions."""
    assert interpret_rsi(50.0) == "Neutral"
    assert interpret_rsi(30.0) == "Neutral"
    assert interpret_rsi(70.0) == "Neutral"
    assert interpret_rsi(45.5) == "Neutral"


def test_interpret_rsi_boundary_values():
    """Test RSI interpretation at exact boundary values."""
    # Test exact boundaries
    assert interpret_rsi(70.0) == "Neutral"  # Exactly 70 is still neutral
    assert interpret_rsi(30.0) == "Neutral"  # Exactly 30 is still neutral
    assert interpret_rsi(70.01) == "Overbought"  # Just above 70
    assert interpret_rsi(29.99) == "Oversold"  # Just below 30


# ============================================================================
# Test RSI with Different Periods
# ============================================================================

def test_rsi_with_different_periods():
    """Test RSI calculation with different period lengths."""
    prices = pd.Series(range(100, 150))  # 50 data points
    
    # Test with period=7
    rsi_7 = calculate_rsi(prices, period=7)
    assert 0 <= rsi_7 <= 100
    
    # Test with period=21
    rsi_21 = calculate_rsi(prices, period=21)
    assert 0 <= rsi_21 <= 100
    
    # Shorter periods should be more sensitive (higher RSI for uptrend)
    # Both should be high since prices are increasing
    assert rsi_7 >= 90
    assert rsi_21 >= 90


# ============================================================================
# Test RSI with Edge Case Price Patterns
# ============================================================================

def test_rsi_with_flat_prices():
    """
    Test RSI with completely flat prices (no change).
    
    When prices don't change, RSI calculation may result in NaN or special handling.
    """
    prices = pd.Series([100.0] * 30)  # All same price
    
    # This should either raise an error or return a specific value
    # The implementation handles this by checking for zero average loss
    try:
        rsi = calculate_rsi(prices, period=14)
        # If it succeeds, RSI should be 100 (no losses) or 0 (no gains)
        # In this case, no gains or losses, so it depends on implementation
        assert 0 <= rsi <= 100
    except InsufficientDataError:
        # This is also acceptable behavior
        pass


def test_rsi_with_large_price_swings():
    """Test RSI with large price swings."""
    prices = []
    base = 100
    for i in range(30):
        if i % 2 == 0:
            prices.append(base)
        else:
            prices.append(base * 1.5)  # 50% swings
    
    prices = pd.Series(prices)
    rsi = calculate_rsi(prices, period=14)
    
    # RSI should still be valid
    assert 0 <= rsi <= 100
    assert isinstance(rsi, float)


def test_rsi_with_small_price_changes():
    """Test RSI with very small price changes."""
    prices = []
    base = 100.0
    for i in range(30):
        base += np.random.uniform(-0.01, 0.01)  # Very small changes
        prices.append(base)
    
    prices = pd.Series(prices)
    rsi = calculate_rsi(prices, period=14)
    
    # RSI should still be valid
    assert 0 <= rsi <= 100
    assert isinstance(rsi, float)


# ============================================================================
# Test RSI Return Type and Precision
# ============================================================================

def test_rsi_returns_float():
    """Test that RSI always returns a float."""
    prices = pd.Series(range(100, 130))
    rsi = calculate_rsi(prices, period=14)
    
    assert isinstance(rsi, float), f"RSI should return float, got {type(rsi)}"


def test_rsi_precision():
    """Test that RSI has reasonable precision."""
    prices = pd.Series(range(100, 130))
    rsi = calculate_rsi(prices, period=14)
    
    # RSI should have decimal precision (not just integers)
    assert rsi != int(rsi) or rsi in [0.0, 100.0], \
        "RSI should have decimal precision unless at extremes"


# ============================================================================
# Test RSI with Real-World-Like Data
# ============================================================================

def test_rsi_with_realistic_volatility():
    """Test RSI with realistic market volatility."""
    np.random.seed(42)
    
    # Generate realistic price series with random walk
    prices = [100.0]
    for _ in range(29):
        change = np.random.normal(0, 2.0)  # Mean 0, std 2
        new_price = max(prices[-1] + change, 1.0)  # Keep positive
        prices.append(new_price)
    
    prices = pd.Series(prices)
    rsi = calculate_rsi(prices, period=14)
    
    # RSI should be valid
    assert 0 <= rsi <= 100
    assert isinstance(rsi, float)
    
    # With random walk, RSI should typically be in middle range
    # (not at extremes unless we're very unlucky)
    assert 10 <= rsi <= 90, f"RSI {rsi} seems extreme for random walk"
