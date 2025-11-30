#!/usr/bin/env python
"""
Demo script for the Multi-Agentic Trading Supervisor.

Shows the Supervisor Agent orchestrating multiple specialized tools to provide
comprehensive trading recommendations.
"""

import os
from src.supervisor import handle_query

# Set API key
os.environ['ALPHA_VANTAGE_API_KEY'] = '14U5E6FZS0OZ4JES'


def print_recommendation(result):
    """Pretty print a trading recommendation."""
    print(f"\n{'='*80}")
    print(f"🎯 RECOMMENDATION: {result['recommendation']}")
    print(f"📊 Ticker: {result['ticker']}")
    print(f"💪 Confidence: {result['confidence']:.0%}")
    print(f"{'='*80}")
    
    # Technical Analysis
    if result['technical_analysis'] and not result['technical_analysis'].get('error'):
        tech = result['technical_analysis']
        print(f"\n📈 TECHNICAL ANALYSIS:")
        print(f"   Price: ${tech['current_price']:.2f}")
        print(f"   RSI: {tech['rsi']:.1f} ({tech['rsi_signal']})")
        print(f"   24h Change: ${tech['price_change_24h']:.2f}")
    
    # Sentiment Analysis
    if result['sentiment_analysis'] and not result['sentiment_analysis'].get('error'):
        sent = result['sentiment_analysis']
        emoji = "🐂" if sent['sentiment'] == "Bullish" else "🐻"
        print(f"\n📰 SENTIMENT ANALYSIS:")
        print(f"   {emoji} {sent['sentiment']} ({sent['confidence']:.0%} confidence)")
        print(f"   {sent['rationale']}")
    
    # Summary
    print(f"\n💡 SUMMARY:")
    print(f"   {result['summary']}")
    print(f"\n{'='*80}\n")


def main():
    """Run comprehensive demo of the Supervisor Agent."""
    
    print("\n" + "="*80)
    print("🤖 MULTI-AGENTIC TRADING SUPERVISOR DEMO")
    print("="*80)
    print("\nDemonstrating intelligent agent orchestration with specialized tools:")
    print("  • Technical Analyst (RSI, price trends)")
    print("  • Sentiment Analyst (news sentiment)")
    print("  • Supervisor Agent (decision synthesis)")
    
    # Demo 1: General comprehensive analysis
    print("\n\n" + "🔹"*40)
    print("DEMO 1: General Query - Comprehensive Analysis")
    print("🔹"*40)
    print("\nQuery: 'Should I buy AAPL?'")
    print("Expected: Both technical and sentiment analysis")
    
    result = handle_query("Should I buy AAPL?")
    print_recommendation(result)
    
    # Demo 2: Technical-specific query
    print("\n" + "🔹"*40)
    print("DEMO 2: Technical Query - Intelligent Tool Selection")
    print("🔹"*40)
    print("\nQuery: 'What is the RSI for TSLA?'")
    print("Expected: Only technical analysis (sentiment skipped)")
    
    result = handle_query("What is the RSI for TSLA?")
    print_recommendation(result)
    
    # Demo 3: Sentiment-specific query
    print("\n" + "🔹"*40)
    print("DEMO 3: Sentiment Query - Intelligent Tool Selection")
    print("🔹"*40)
    print("\nQuery: 'What's the sentiment on NVDA?'")
    print("Expected: Only sentiment analysis (technical skipped)")
    
    result = handle_query("What's the sentiment on NVDA?")
    print_recommendation(result)
    
    # Demo 4: Multiple stocks comparison
    print("\n" + "🔹"*40)
    print("DEMO 4: Multi-Stock Analysis")
    print("🔹"*40)
    
    tickers = ['MSFT', 'GOOGL', 'AMZN']
    print(f"\nAnalyzing: {', '.join(tickers)}")
    
    for ticker in tickers:
        result = handle_query(f"Analyze {ticker}")
        print(f"\n{ticker}: {result['recommendation']} "
              f"(Confidence: {result['confidence']:.0%})")
    
    print("\n\n" + "="*80)
    print("✅ DEMO COMPLETE")
    print("="*80)
    print("\nKey Features Demonstrated:")
    print("  ✓ Natural language query understanding")
    print("  ✓ Intelligent tool selection based on keywords")
    print("  ✓ Multi-source data fusion (yfinance + Alpha Vantage)")
    print("  ✓ Decision synthesis (RSI + Sentiment → BUY/SELL/HOLD)")
    print("  ✓ Graceful degradation when tools fail")
    print("  ✓ Comprehensive recommendations with confidence scores")
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    main()
