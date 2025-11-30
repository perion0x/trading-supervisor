"""
Supervisor Agent

Main orchestration component that coordinates specialized tools to generate
comprehensive trading recommendations.
"""

import logging
import re
import os
from typing import Dict, Any, List, Optional
from datetime import datetime

from src.tools.technical_analyst import analyze_technical
from src.tools.sentiment_analyst import analyze_sentiment
from src.models import TradingRecommendation, TechnicalAnalysis, SentimentAnalysis
from src.exceptions import InvalidTickerError, ValidationError
from src.utils.validation import validate_query, format_error_response

logger = logging.getLogger(__name__)


def extract_ticker(query: str) -> str:
    """
    Extract ticker symbol from natural language query.
    
    Looks for 1-5 uppercase letters that represent a stock ticker.
    Common patterns:
    - "Analyze AAPL"
    - "What about TSLA stock?"
    - "Should I buy MSFT?"
    
    Args:
        query: Natural language query string
        
    Returns:
        Extracted ticker symbol (uppercase)
        
    Raises:
        InvalidTickerError: If no valid ticker found
    """
    # Pattern: 1-5 uppercase letters, potentially surrounded by word boundaries
    # This matches common ticker formats
    pattern = r'\b([A-Z]{1,5})\b'
    
    matches = re.findall(pattern, query)
    
    if not matches:
        raise InvalidTickerError(f"No valid ticker symbol found in query: {query}")
    
    # Filter out common English words that might match the pattern
    common_words = {'I', 'A', 'THE', 'AND', 'OR', 'BUT', 'FOR', 'TO', 'OF', 'IN', 'ON', 'AT', 'BY'}
    
    valid_tickers = [m for m in matches if m not in common_words]
    
    if not valid_tickers:
        raise InvalidTickerError(f"No valid ticker symbol found in query: {query}")
    
    # Return the first valid ticker found
    ticker = valid_tickers[0]
    logger.info(f"Extracted ticker: {ticker} from query: {query}")
    
    return ticker


def determine_tools(query: str) -> List[str]:
    """
    Determine which tools to invoke based on query keywords.
    
    Analyzes the query to detect user intent:
    - Technical keywords → Technical Analyst Tool
    - Sentiment keywords → Sentiment Analyst Tool
    - General queries → Both tools
    
    Args:
        query: Natural language query string
        
    Returns:
        List of tool names to invoke: ['technical', 'sentiment'] or subset
    """
    query_lower = query.lower()
    
    # Keywords that indicate technical analysis interest
    technical_keywords = [
        'rsi', 'technical', 'price', 'momentum', 'overbought', 'oversold',
        'indicator', 'chart', 'trend', 'support', 'resistance'
    ]
    
    # Keywords that indicate sentiment analysis interest
    sentiment_keywords = [
        'sentiment', 'news', 'bullish', 'bearish', 'opinion', 'feeling',
        'market sentiment', 'buzz', 'hype', 'pessimistic', 'optimistic'
    ]
    
    # Check for keyword matches
    has_technical = any(keyword in query_lower for keyword in technical_keywords)
    has_sentiment = any(keyword in query_lower for keyword in sentiment_keywords)
    
    # Determine which tools to call
    tools = []
    
    if has_technical and not has_sentiment:
        # Only technical analysis requested
        tools = ['technical']
        logger.info(f"Query requests technical analysis only: {query}")
    elif has_sentiment and not has_technical:
        # Only sentiment analysis requested
        tools = ['sentiment']
        logger.info(f"Query requests sentiment analysis only: {query}")
    else:
        # General query or both requested → comprehensive analysis
        tools = ['technical', 'sentiment']
        logger.info(f"Query requests comprehensive analysis: {query}")
    
    return tools


def synthesize_recommendation(
    ticker: str,
    technical_result: Optional[Dict[str, Any]],
    sentiment_result: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Synthesize trading recommendation from tool results.
    
    Decision matrix:
    - RSI > 70 (Overbought) + Bearish Sentiment → SELL
    - RSI < 30 (Oversold) + Bullish Sentiment → BUY
    - RSI Neutral + Bullish Sentiment → BUY
    - RSI Neutral + Bearish Sentiment → SELL
    - RSI Overbought + Bullish Sentiment → HOLD (conflicting)
    - RSI Oversold + Bearish Sentiment → HOLD (conflicting)
    
    Args:
        ticker: Stock ticker symbol
        technical_result: Technical analysis result (or None if failed)
        sentiment_result: Sentiment analysis result (or None if failed)
        
    Returns:
        Dictionary containing trading recommendation
    """
    # Handle case where both tools failed
    if (technical_result is None or technical_result.get('error')) and \
       (sentiment_result is None or sentiment_result.get('error')):
        return {
            "ticker": ticker,
            "recommendation": "ERROR",
            "technical_analysis": None,
            "sentiment_analysis": None,
            "summary": "Unable to generate recommendation - both analysis tools failed",
            "confidence": 0.0,
            "timestamp": datetime.now().isoformat(),
            "error": "All tools failed"
        }
    
    # Extract technical signals
    rsi_signal = None
    rsi_value = None
    if technical_result and not technical_result.get('error'):
        rsi_signal = technical_result.get('rsi_signal')
        rsi_value = technical_result.get('rsi')
    
    # Extract sentiment signals
    sentiment = None
    sentiment_confidence = 0.5
    if sentiment_result and not sentiment_result.get('error'):
        sentiment = sentiment_result.get('sentiment')
        sentiment_confidence = sentiment_result.get('confidence', 0.5)
    
    # Decision synthesis logic
    recommendation = "HOLD"  # Default
    confidence = 0.5
    summary_parts = []
    
    # Case 1: Both tools succeeded
    if rsi_signal and sentiment:
        if rsi_signal == "Overbought" and sentiment == "Bearish":
            recommendation = "SELL"
            confidence = 0.8
            summary_parts.append(f"Strong sell signal: RSI overbought ({rsi_value:.1f}) with bearish sentiment")
        
        elif rsi_signal == "Oversold" and sentiment == "Bullish":
            recommendation = "BUY"
            confidence = 0.8
            summary_parts.append(f"Strong buy signal: RSI oversold ({rsi_value:.1f}) with bullish sentiment")
        
        elif rsi_signal == "Neutral" and sentiment == "Bullish":
            recommendation = "BUY"
            confidence = 0.65
            summary_parts.append(f"Buy signal: Neutral momentum ({rsi_value:.1f}) with positive sentiment")
        
        elif rsi_signal == "Neutral" and sentiment == "Bearish":
            recommendation = "SELL"
            confidence = 0.65
            summary_parts.append(f"Sell signal: Neutral momentum ({rsi_value:.1f}) with negative sentiment")
        
        elif rsi_signal == "Overbought" and sentiment == "Bullish":
            recommendation = "HOLD"
            confidence = 0.5
            summary_parts.append(f"Hold: Conflicting signals - overbought ({rsi_value:.1f}) but bullish sentiment")
        
        elif rsi_signal == "Oversold" and sentiment == "Bearish":
            recommendation = "HOLD"
            confidence = 0.5
            summary_parts.append(f"Hold: Conflicting signals - oversold ({rsi_value:.1f}) but bearish sentiment")
        
        # Adjust confidence based on sentiment confidence
        confidence = (confidence + sentiment_confidence) / 2
    
    # Case 2: Only technical succeeded
    elif rsi_signal and not sentiment:
        summary_parts.append("Based on technical analysis only (sentiment unavailable)")
        
        if rsi_signal == "Overbought":
            recommendation = "SELL"
            confidence = 0.6
            summary_parts.append(f"RSI overbought ({rsi_value:.1f}) suggests potential pullback")
        elif rsi_signal == "Oversold":
            recommendation = "BUY"
            confidence = 0.6
            summary_parts.append(f"RSI oversold ({rsi_value:.1f}) suggests potential bounce")
        else:
            recommendation = "HOLD"
            confidence = 0.5
            summary_parts.append(f"RSI neutral ({rsi_value:.1f}) - no clear technical signal")
    
    # Case 3: Only sentiment succeeded
    elif sentiment and not rsi_signal:
        summary_parts.append("Based on sentiment analysis only (technical unavailable)")
        
        if sentiment == "Bullish":
            recommendation = "BUY"
            confidence = sentiment_confidence * 0.8
            summary_parts.append(f"Bullish sentiment ({sentiment_confidence:.0%} confidence)")
        else:
            recommendation = "SELL"
            confidence = sentiment_confidence * 0.8
            summary_parts.append(f"Bearish sentiment ({sentiment_confidence:.0%} confidence)")
    
    # Build summary
    summary = ". ".join(summary_parts) + "."
    
    return {
        "ticker": ticker,
        "recommendation": recommendation,
        "technical_analysis": technical_result,
        "sentiment_analysis": sentiment_result,
        "summary": summary,
        "confidence": round(confidence, 2),
        "timestamp": datetime.now().isoformat(),
        "error": None
    }


def handle_query(query: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Main orchestration function for handling user queries.
    
    Workflow:
    1. Validate and extract ticker from query
    2. Determine which tools to invoke
    3. Call appropriate tools
    4. Synthesize results into recommendation
    5. Handle errors gracefully
    
    Args:
        query: Natural language query from user
        api_key: Optional Alpha Vantage API key for sentiment analysis
        
    Returns:
        Dictionary containing comprehensive trading recommendation
    """
    try:
        logger.info(f"Handling query: {query}")
        
        # Step 0: Validate query input
        try:
            query = validate_query(query)
        except ValidationError as e:
            logger.error(f"Query validation failed: {str(e)}")
            return format_error_response(e, ticker=None)
        
        # Step 1: Extract ticker
        try:
            ticker = extract_ticker(query)
        except InvalidTickerError as e:
            logger.error(f"Ticker extraction failed: {str(e)}")
            return format_error_response(e, ticker=None)
        
        # Step 2: Determine which tools to call
        tools = determine_tools(query)
        
        # Step 3: Call tools (with graceful degradation)
        technical_result = None
        sentiment_result = None
        
        if 'technical' in tools:
            try:
                logger.info(f"Calling Technical Analyst for {ticker}")
                technical_result = analyze_technical(ticker)
            except Exception as e:
                logger.error(f"Technical analysis failed: {str(e)}")
                technical_result = {"error": str(e)}
        
        if 'sentiment' in tools:
            try:
                logger.info(f"Calling Sentiment Analyst for {ticker}")
                sentiment_result = analyze_sentiment(ticker, api_key)
            except Exception as e:
                logger.error(f"Sentiment analysis failed: {str(e)}")
                sentiment_result = {"error": str(e)}
        
        # Step 4: Synthesize recommendation
        recommendation = synthesize_recommendation(ticker, technical_result, sentiment_result)
        
        logger.info(f"Generated recommendation for {ticker}: {recommendation['recommendation']}")
        
        return recommendation
        
    except Exception as e:
        logger.error(f"Unexpected error in handle_query: {str(e)}")
        return format_error_response(e, ticker=None)
