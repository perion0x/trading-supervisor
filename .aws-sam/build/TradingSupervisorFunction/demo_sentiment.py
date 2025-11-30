#!/usr/bin/env python
"""
Demo script to test real-time sentiment analysis with Alpha Vantage API.
"""

import os
import json
from src.tools.sentiment_analyst import analyze_sentiment

# Set your API key
os.environ['ALPHA_VANTAGE_API_KEY'] = '14U5E6FZS0OZ4JES'

def demo_sentiment_analysis():
    """Run sentiment analysis on popular stocks."""
    
    print("=" * 70)
    print("Real-Time Sentiment Analysis Demo")
    print("Using Alpha Vantage News Sentiment API")
    print("=" * 70)
    
    # Test with popular tickers
    tickers = ['AAPL', 'TSLA', 'NVDA', 'MSFT', 'AMZN']
    
    for ticker in tickers:
        print(f"\n{'─' * 70}")
        print(f"📊 Analyzing: {ticker}")
        print('─' * 70)
        
        result = analyze_sentiment(ticker)
        
        if result['error']:
            print(f"❌ Error: {result['error']}")
        else:
            # Determine emoji based on sentiment
            emoji = "🐂" if result['sentiment'] == "Bullish" else "🐻"
            
            print(f"{emoji} Sentiment: {result['sentiment']}")
            print(f"📈 Confidence: {result['confidence']:.2%}")
            print(f"💬 Rationale: {result['rationale']}")
            print(f"🕐 Timestamp: {result['timestamp']}")
    
    print(f"\n{'=' * 70}")
    print("Demo Complete!")
    print("=" * 70)

if __name__ == "__main__":
    demo_sentiment_analysis()
