"""
Technical Analyst Tool

Fetches live market data and calculates technical indicators (RSI).
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any
import pandas as pd
import numpy as np
import yfinance as yf

from src.models import TechnicalAnalysis
from src.exceptions import InsufficientDataError, ExternalAPIError
from src.utils.retry import exponential_backoff_retry

logger = logging.getLogger(__name__)


@exponential_backoff_retry(
    max_retries=3,
    initial_delay=1.0,
    backoff_factor=2.0,
    exceptions=(ExternalAPIError, Exception),
    timeout=10.0
)
def fetch_price_data(ticker: str, period: str = "3mo") -> pd.DataFrame:
    """
    Retrieve historical price data using yfinance with retry logic.
    
    Implements exponential backoff retry (3 attempts) with 10-second timeout.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL')
        period: Time period for historical data (default: '3mo')
        
    Returns:
        DataFrame with historical OHLCV data
        
    Raises:
        ExternalAPIError: If yfinance API fails or returns no data after retries
    """
    try:
        logger.info(f"Fetching price data for {ticker} with period {period}")
        stock = yf.Ticker(ticker)
        df = stock.history(period=period)
        
        if df is None or df.empty:
            raise ExternalAPIError(f"No data returned for ticker {ticker}")
        
        logger.info(f"Successfully fetched {len(df)} data points for {ticker}")
        return df
        
    except ExternalAPIError:
        # Re-raise our custom exception
        raise
    except Exception as e:
        logger.error(f"Failed to fetch price data for {ticker}: {str(e)}")
        raise ExternalAPIError(f"Failed to fetch price data: {str(e)}")


def calculate_rsi(prices: pd.Series, period: int = 14) -> float:
    """
    Calculate RSI (Relative Strength Index) using standard formula.
    
    RSI = 100 - (100 / (1 + RS))
    where RS = Average Gain / Average Loss over the period
    
    Args:
        prices: Series of closing prices
        period: RSI period (default: 14)
        
    Returns:
        RSI value between 0 and 100
        
    Raises:
        InsufficientDataError: If not enough data points for calculation
    """
    if len(prices) < period + 1:
        raise InsufficientDataError(
            f"Need at least {period + 1} data points for RSI calculation, got {len(prices)}"
        )
    
    # Calculate price changes (deltas)
    deltas = prices.diff()
    
    # Separate gains and losses
    gains = deltas.where(deltas > 0, 0.0)
    losses = -deltas.where(deltas < 0, 0.0)
    
    # Calculate average gain and average loss over the period
    avg_gain = gains.rolling(window=period, min_periods=period).mean()
    avg_loss = losses.rolling(window=period, min_periods=period).mean()
    
    # Calculate RS (Relative Strength)
    rs = avg_gain / avg_loss
    
    # Calculate RSI
    rsi = 100 - (100 / (1 + rs))
    
    # Return the most recent RSI value
    rsi_value = rsi.iloc[-1]
    
    # Handle edge cases where RSI might be NaN
    if pd.isna(rsi_value):
        # If all losses are zero, RSI = 100
        if avg_loss.iloc[-1] == 0:
            return 100.0
        # If all gains are zero, RSI = 0
        elif avg_gain.iloc[-1] == 0:
            return 0.0
        else:
            raise InsufficientDataError("Unable to calculate RSI - insufficient valid data")
    
    return float(rsi_value)


def interpret_rsi(rsi_value: float) -> str:
    """
    Interpret RSI value and classify as Overbought/Oversold/Neutral.
    
    Args:
        rsi_value: RSI value between 0 and 100
        
    Returns:
        Signal classification: "Overbought", "Oversold", or "Neutral"
    """
    if rsi_value > 70:
        return "Overbought"
    elif rsi_value < 30:
        return "Oversold"
    else:
        return "Neutral"


def analyze_technical(ticker: str) -> Dict[str, Any]:
    """
    Main function to orchestrate technical analysis.
    
    Fetches price data, calculates RSI, and returns comprehensive analysis.
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        Dictionary containing technical analysis results
    """
    try:
        # Fetch price data
        df = fetch_price_data(ticker)
        
        # Extract current price and calculate 24h change
        current_price = float(df['Close'].iloc[-1])
        if len(df) >= 2:
            prev_price = float(df['Close'].iloc[-2])
            price_change_24h = current_price - prev_price
        else:
            price_change_24h = 0.0
        
        # Calculate RSI
        rsi = calculate_rsi(df['Close'])
        
        # Interpret RSI signal
        rsi_signal = interpret_rsi(rsi)
        
        # Create TechnicalAnalysis object
        analysis = TechnicalAnalysis(
            ticker=ticker,
            current_price=current_price,
            rsi=rsi,
            rsi_signal=rsi_signal,
            price_change_24h=price_change_24h,
            timestamp=datetime.now()
        )
        
        logger.info(f"Technical analysis complete for {ticker}: RSI={rsi:.2f}, Signal={rsi_signal}")
        
        return {
            "ticker": analysis.ticker,
            "current_price": analysis.current_price,
            "rsi": analysis.rsi,
            "rsi_signal": analysis.rsi_signal,
            "price_change_24h": analysis.price_change_24h,
            "timestamp": analysis.timestamp.isoformat(),
            "error": None
        }
        
    except (InsufficientDataError, ExternalAPIError) as e:
        logger.error(f"Technical analysis failed for {ticker}: {str(e)}")
        return {
            "ticker": ticker,
            "current_price": None,
            "rsi": None,
            "rsi_signal": None,
            "price_change_24h": None,
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }
    except Exception as e:
        logger.error(f"Unexpected error in technical analysis for {ticker}: {str(e)}")
        return {
            "ticker": ticker,
            "current_price": None,
            "rsi": None,
            "rsi_signal": None,
            "price_change_24h": None,
            "timestamp": datetime.now().isoformat(),
            "error": f"Unexpected error: {str(e)}"
        }
