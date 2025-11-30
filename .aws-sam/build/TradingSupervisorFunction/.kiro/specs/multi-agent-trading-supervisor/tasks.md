# Implementation Plan

- [x] 1. Set up project structure and dependencies
  - Create directory structure: `src/`, `src/tools/`, `src/utils/`, `tests/`
  - Create `requirements.txt` with yfinance, pandas, numpy, requests, boto3, pytest, hypothesis
  - Create `__init__.py` files for Python package structure
  - Set up basic logging configuration
  - _Requirements: 5.1, 5.2, 5.4_

- [x] 2. Implement core data models
  - Create `src/models.py` with dataclasses for Query, TechnicalAnalysis, SentimentAnalysis, TradingRecommendation
  - Implement validation methods for each model
  - Add timestamp generation utilities
  - _Requirements: 5.1_

- [x] 3. Implement Technical Analyst Tool
  - Create `src/tools/technical_analyst.py`
  - Implement `fetch_price_data()` function using yfinance
  - Implement `calculate_rsi()` function with standard 14-period formula
  - Implement `interpret_rsi()` function (Overbought > 70, Oversold < 30, Neutral otherwise)
  - Implement `analyze_technical()` main function that orchestrates the analysis
  - Add error handling for API failures and insufficient data
  - _Requirements: 2.1, 2.2, 2.3, 8.1, 8.5_

- [x] 3.1 Write property test for RSI bounds invariant
  - **Property 18: RSI bounds invariant**
  - **Validates: Requirements 8.3**
  - Generate random price series, verify RSI is always between 0 and 100
  - _Requirements: 8.3_

- [x] 3.2 Write property test for RSI formula correctness
  - **Property 19: RSI formula correctness**
  - **Validates: Requirements 8.5**
  - Compare implementation against reference RSI calculation
  - _Requirements: 8.5_

- [x] 3.3 Write property test for technical data retrieval
  - **Property 5: Technical data retrieval**
  - **Validates: Requirements 2.1**
  - Generate random valid tickers, verify yfinance is called
  - _Requirements: 2.1_

- [x] 3.4 Write property test for technical output completeness
  - **Property 7: Technical output completeness**
  - **Validates: Requirements 2.3**
  - Generate random analysis results, verify RSI and price are present
  - _Requirements: 2.3_

- [x] 4. Implement Sentiment Analyst Tool
  - Create `src/tools/sentiment_analyst.py`
  - Implement `fetch_news_sentiment()` function using Alpha Vantage News Sentiment API
  - Implement `calculate_aggregate_sentiment()` function to process news articles
  - Implement `analyze_sentiment()` main function
  - Add retry logic with exponential backoff for API calls
  - Ensure consistent results for same ticker within session
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] 4.1 Write property test for sentiment classification validity
  - **Property 8: Sentiment classification validity**
  - **Validates: Requirements 3.1**
  - Generate random tickers, verify sentiment is "Bullish" or "Bearish"
  - _Requirements: 3.1_

- [x] 4.2 Write property test for sentiment determinism
  - **Property 9: Sentiment determinism**
  - **Validates: Requirements 3.2, 3.4**
  - Generate random tickers, call multiple times with same API data, verify consistent processing
  - _Requirements: 3.2, 3.4_

- [x] 4.3 Write property test for sentiment output completeness
  - **Property 10: Sentiment output completeness**
  - **Validates: Requirements 3.3**
  - Generate random sentiment results, verify confidence and rationale present
  - _Requirements: 3.3_

- [x] 5. Implement Supervisor Agent core logic
  - Create `src/supervisor.py`
  - Implement `extract_ticker()` function to parse ticker from queries
  - Implement `determine_tools()` function for intelligent tool selection based on query keywords
  - Implement decision synthesis logic that combines technical and sentiment results
  - Create recommendation mapping (RSI + Sentiment → BUY/SELL/HOLD)
  - Implement `handle_query()` main orchestration function
  - Add graceful degradation when tools fail
  - _Requirements: 1.1, 1.2, 1.3, 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 5.1 Write property test for ticker extraction correctness
  - **Property 1: Ticker extraction correctness**
  - **Validates: Requirements 1.1**
  - Generate random queries with embedded tickers, verify extraction
  - _Requirements: 1.1_

- [x] 5.2 Write property test for dual tool invocation
  - **Property 2: Dual tool invocation**
  - **Validates: Requirements 1.2**
  - Generate random general queries, verify both tools are called
  - _Requirements: 1.2_

- [x] 5.3 Write property test for complete recommendation synthesis
  - **Property 3: Complete recommendation synthesis**
  - **Validates: Requirements 1.3, 6.4**
  - Generate random tool results, verify all required fields in recommendation
  - _Requirements: 1.3, 6.4_

- [x] 5.4 Write property test for invalid ticker rejection
  - **Property 4: Invalid ticker rejection**
  - **Validates: Requirements 1.4**
  - Generate invalid ticker strings, verify error responses
  - _Requirements: 1.4_

- [x] 5.5 Write property test for query-based tool selection (technical)
  - **Property 13: Query-based tool selection (technical keywords)**
  - **Validates: Requirements 6.1**
  - Generate queries with technical keywords, verify Technical Tool is called
  - _Requirements: 6.1_

- [x] 5.6 Write property test for query-based tool selection (sentiment)
  - **Property 14: Query-based tool selection (sentiment keywords)**
  - **Validates: Requirements 6.2**
  - Generate queries with sentiment keywords, verify Sentiment Tool is called
  - _Requirements: 6.2_

- [x] 5.7 Write property test for default comprehensive analysis
  - **Property 15: Default comprehensive analysis**
  - **Validates: Requirements 6.3**
  - Generate general queries, verify both tools are invoked
  - _Requirements: 6.3_

- [x] 5.8 Write property test for graceful degradation
  - **Property 16: Graceful degradation on tool failure**
  - **Validates: Requirements 6.5**
  - Simulate tool failures, verify system continues with partial results
  - _Requirements: 6.5_

- [x] 6. Implement error handling and validation
  - Create `src/exceptions.py` with custom exception classes
  - Implement input validation utilities in `src/utils/validation.py`
  - Add error response formatting functions
  - Implement retry logic with exponential backoff for yfinance calls
  - Add timeout handling for all external calls
  - _Requirements: 1.4, 2.4, 2.5, 3.5, 5.3, 7.1, 7.2, 7.3_

- [x] 6.1 Write property test for input validation
  - **Property 17: Input validation**
  - **Validates: Requirements 7.3**
  - Generate invalid input types, verify clear error messages
  - _Requirements: 7.3_

- [x] 7. Implement AWS Lambda handler and Bedrock integration
  - Create `src/lambda_handler.py` with `lambda_handler()` entry point
  - Implement `parse_bedrock_event()` to extract queries from Bedrock event format
  - Implement `format_bedrock_response()` to format responses for Bedrock
  - Wire Lambda handler to Supervisor Agent
  - Add environment variable configuration
  - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [x] 7.1 Write property test for Bedrock event parsing
  - **Property 11: Bedrock event parsing**
  - **Validates: Requirements 4.3**
  - Generate valid Bedrock events, verify correct query extraction
  - _Requirements: 4.3_

- [x] 7.2 Write property test for Bedrock response formatting
  - **Property 12: Bedrock response formatting**
  - **Validates: Requirements 4.4**
  - Generate random recommendations, verify Bedrock-compliant formatting
  - _Requirements: 4.4_

- [x] 8. Create test infrastructure and utilities
  - Set up pytest configuration in `pytest.ini`
  - Create test fixtures for mock data in `tests/conftest.py`
  - Create Hypothesis strategies for generating test data
  - Set up test data generators for tickers, prices, queries
  - Configure Hypothesis to run 100 iterations per property test
  - _Requirements: Testing Strategy_

- [x] 8.1 Write unit tests for RSI calculation edge cases
  - Test with exactly 14 data points
  - Test with known price sequences
  - Test with all gains or all losses
  - _Requirements: 2.2, 8.1_

- [x] 8.2 Write unit tests for error handling scenarios
  - Test yfinance API unavailable
  - Test empty data responses
  - Test network timeouts
  - Test invalid ticker formats
  - _Requirements: 2.4, 2.5, 7.1, 7.2_

- [x] 8.3 Write integration test for end-to-end flow
  - Test complete flow from query to recommendation
  - Use real ticker symbols (AAPL, MSFT)
  - Verify all components work together
  - _Requirements: All_

- [x] 9. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 10. Create deployment configuration
  - Create `serverless.yml` or AWS SAM template for Lambda deployment
  - Configure Lambda function settings (memory, timeout, environment variables)
  - Create IAM role with minimal required permissions
  - Document deployment steps in `DEPLOYMENT.md`
  - _Requirements: 4.1, 4.5_

- [x] 11. Create project documentation
  - Create `README.md` with project overview, setup instructions, and usage examples
  - Document API schemas for tools
  - Create architecture diagram in documentation
  - Add example queries and expected responses
  - _Requirements: 5.1_

- [x] 12. Final checkpoint - Verify complete system
  - Ensure all tests pass, ask the user if questions arise.
