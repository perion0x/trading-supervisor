"""
Core data models for the Multi-Agentic Trading Supervisor system.

This module defines the data structures used throughout the system for
queries, analysis results, and trading recommendations.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import re


def generate_timestamp() -> datetime:
    """Generate a UTC timestamp for the current moment.
    
    Returns:
        datetime: Current UTC timestamp
    """
    return datetime.utcnow()


@dataclass
class Query:
    """Represents a user query for stock analysis.
    
    Attributes:
        text: The raw query text from the user
        ticker: Optional extracted ticker symbol
        user_id: Optional user identifier
        session_id: Optional session identifier for tracking
    """
    text: str
    ticker: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    
    def validate(self) -> tuple[bool, Optional[str]]:
        """Validate the query data.
        
        Returns:
            tuple: (is_valid, error_message)
        """
        if not self.text or not isinstance(self.text, str):
            return False, "Query text must be a non-empty string"
        
        if self.text.strip() == "":
            return False, "Query text cannot be empty or whitespace only"
        
        if self.ticker is not None:
            if not isinstance(self.ticker, str):
                return False, "Ticker must be a string"
            if not re.match(r'^[A-Z]{1,5}$', self.ticker):
                return False, f"Invalid ticker format: {self.ticker}"
        
        return True, None


@dataclass
class TechnicalAnalysis:
    """Results from technical analysis of a financial instrument.
    
    Attributes:
        ticker: Stock ticker symbol
        current_price: Current price of the stock
        rsi: Relative Strength Index value (0-100)
        rsi_signal: Interpretation of RSI (Overbought/Oversold/Neutral)
        price_change_24h: 24-hour price change
        timestamp: When the analysis was performed
        error: Optional error message if analysis failed
    """
    ticker: str
    current_price: float
    rsi: float
    rsi_signal: str
    price_change_24h: float
    timestamp: datetime = field(default_factory=generate_timestamp)
    error: Optional[str] = None
    
    def validate(self) -> tuple[bool, Optional[str]]:
        """Validate the technical analysis data.
        
        Returns:
            tuple: (is_valid, error_message)
        """
        if not self.ticker or not isinstance(self.ticker, str):
            return False, "Ticker must be a non-empty string"
        
        if not re.match(r'^[A-Z]{1,5}$', self.ticker):
            return False, f"Invalid ticker format: {self.ticker}"
        
        if not isinstance(self.current_price, (int, float)) or self.current_price <= 0:
            return False, "Current price must be a positive number"
        
        if not isinstance(self.rsi, (int, float)) or not (0 <= self.rsi <= 100):
            return False, "RSI must be between 0 and 100"
        
        valid_signals = ["Overbought", "Oversold", "Neutral"]
        if self.rsi_signal not in valid_signals:
            return False, f"RSI signal must be one of {valid_signals}"
        
        if not isinstance(self.price_change_24h, (int, float)):
            return False, "Price change must be a number"
        
        if not isinstance(self.timestamp, datetime):
            return False, "Timestamp must be a datetime object"
        
        return True, None


@dataclass
class SentimentAnalysis:
    """Results from sentiment analysis of a financial instrument.
    
    Attributes:
        ticker: Stock ticker symbol
        sentiment: Sentiment classification (Bullish/Bearish)
        confidence: Confidence score (0.0-1.0)
        rationale: Explanation for the sentiment classification
        timestamp: When the analysis was performed
        error: Optional error message if analysis failed
    """
    ticker: str
    sentiment: str
    confidence: float
    rationale: str
    timestamp: datetime = field(default_factory=generate_timestamp)
    error: Optional[str] = None
    
    def validate(self) -> tuple[bool, Optional[str]]:
        """Validate the sentiment analysis data.
        
        Returns:
            tuple: (is_valid, error_message)
        """
        if not self.ticker or not isinstance(self.ticker, str):
            return False, "Ticker must be a non-empty string"
        
        if not re.match(r'^[A-Z]{1,5}$', self.ticker):
            return False, f"Invalid ticker format: {self.ticker}"
        
        valid_sentiments = ["Bullish", "Bearish"]
        if self.sentiment not in valid_sentiments:
            return False, f"Sentiment must be one of {valid_sentiments}"
        
        if not isinstance(self.confidence, (int, float)) or not (0.0 <= self.confidence <= 1.0):
            return False, "Confidence must be between 0.0 and 1.0"
        
        if not self.rationale or not isinstance(self.rationale, str):
            return False, "Rationale must be a non-empty string"
        
        if not isinstance(self.timestamp, datetime):
            return False, "Timestamp must be a datetime object"
        
        return True, None


@dataclass
class TradingRecommendation:
    """Final trading recommendation combining technical and sentiment analysis.
    
    Attributes:
        ticker: Stock ticker symbol
        recommendation: Trading action (BUY/SELL/HOLD)
        technical_analysis: Technical analysis results
        sentiment_analysis: Sentiment analysis results
        summary: Human-readable summary of the recommendation
        confidence: Overall confidence in the recommendation (0.0-1.0)
        timestamp: When the recommendation was generated
    """
    ticker: str
    recommendation: str
    technical_analysis: TechnicalAnalysis
    sentiment_analysis: SentimentAnalysis
    summary: str
    confidence: float
    timestamp: datetime = field(default_factory=generate_timestamp)
    
    def validate(self) -> tuple[bool, Optional[str]]:
        """Validate the trading recommendation data.
        
        Returns:
            tuple: (is_valid, error_message)
        """
        if not self.ticker or not isinstance(self.ticker, str):
            return False, "Ticker must be a non-empty string"
        
        if not re.match(r'^[A-Z]{1,5}$', self.ticker):
            return False, f"Invalid ticker format: {self.ticker}"
        
        valid_recommendations = ["BUY", "SELL", "HOLD"]
        if self.recommendation not in valid_recommendations:
            return False, f"Recommendation must be one of {valid_recommendations}"
        
        # Validate nested technical analysis
        tech_valid, tech_error = self.technical_analysis.validate()
        if not tech_valid:
            return False, f"Invalid technical analysis: {tech_error}"
        
        # Validate nested sentiment analysis
        sent_valid, sent_error = self.sentiment_analysis.validate()
        if not sent_valid:
            return False, f"Invalid sentiment analysis: {sent_error}"
        
        # Ensure ticker consistency
        if self.technical_analysis.ticker != self.ticker:
            return False, "Technical analysis ticker does not match recommendation ticker"
        
        if self.sentiment_analysis.ticker != self.ticker:
            return False, "Sentiment analysis ticker does not match recommendation ticker"
        
        if not isinstance(self.confidence, (int, float)) or not (0.0 <= self.confidence <= 1.0):
            return False, "Confidence must be between 0.0 and 1.0"
        
        if not self.summary or not isinstance(self.summary, str):
            return False, "Summary must be a non-empty string"
        
        if not isinstance(self.timestamp, datetime):
            return False, "Timestamp must be a datetime object"
        
        return True, None
