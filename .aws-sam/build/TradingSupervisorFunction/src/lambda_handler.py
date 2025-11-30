"""
AWS Lambda Handler for Bedrock Agent Integration

This module provides the Lambda function entry point and utilities for
integrating the Multi-Agentic Trading Supervisor with AWS Bedrock Agents.
"""

import json
import logging
import os
from typing import Dict, Any, Optional

from src.supervisor import handle_query
from src.utils.logging_config import setup_logging
from src.exceptions import TradingSystemError

# Set up logging
setup_logging()
logger = logging.getLogger(__name__)


def parse_bedrock_event(event: Dict[str, Any]) -> str:
    """
    Extract query from AWS Bedrock Agent event format.
    
    Bedrock Agent events have the following structure:
    {
        "messageVersion": "1.0",
        "agent": {...},
        "inputText": "Analyze AAPL",
        "sessionId": "session-123",
        "sessionAttributes": {},
        "promptSessionAttributes": {}
    }
    
    Args:
        event: AWS Bedrock Agent event dictionary
        
    Returns:
        Extracted query string from inputText field
        
    Raises:
        ValueError: If event format is invalid or inputText is missing
    """
    logger.info(f"Parsing event: {json.dumps(event, default=str)}")
    
    # Validate event structure
    if not isinstance(event, dict):
        raise ValueError("Event must be a dictionary")
    
    # Check if this is an API Gateway event (has 'body' field)
    if 'body' in event:
        logger.info("Detected API Gateway event format")
        body = event.get('body', '{}')
        if isinstance(body, str):
            try:
                body = json.loads(body)
            except json.JSONDecodeError:
                raise ValueError("Invalid JSON in request body")
        event = body
    
    # Extract inputText field (primary query field in Bedrock events)
    input_text = event.get('inputText')
    
    if input_text is None:
        # Fallback: check for alternative field names
        input_text = event.get('query') or event.get('text')
    
    if not input_text:
        raise ValueError("No query found in event. Expected 'inputText', 'query', or 'text' field")
    
    if not isinstance(input_text, str):
        raise ValueError(f"Query must be a string, got {type(input_text)}")
    
    if not input_text.strip():
        raise ValueError("Query cannot be empty or whitespace only")
    
    logger.info(f"Extracted query: {input_text}")
    return input_text


def format_bedrock_response(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format trading recommendation for AWS Bedrock Agent response.
    
    Bedrock Agent expects responses in a specific format with:
    - messageVersion: Version identifier
    - response: The actual response content
    - sessionAttributes: Optional session state
    
    Args:
        result: Trading recommendation dictionary from supervisor
        
    Returns:
        Bedrock-compliant response dictionary
    """
    logger.info(f"Formatting Bedrock response for result: {json.dumps(result, default=str)}")
    
    # Check if this is an error response
    is_error = result.get('error') is not None or result.get('recommendation') == 'ERROR'
    
    # Build human-readable response text
    if is_error:
        response_text = f"Error: {result.get('summary', 'Unable to process request')}"
        if result.get('error'):
            response_text += f"\nDetails: {result['error']}"
    else:
        ticker = result.get('ticker', 'Unknown')
        recommendation = result.get('recommendation', 'HOLD')
        summary = result.get('summary', 'No summary available')
        confidence = result.get('confidence', 0.0)
        
        response_text = f"Trading Analysis for {ticker}\n\n"
        response_text += f"Recommendation: {recommendation}\n"
        response_text += f"Confidence: {confidence:.0%}\n\n"
        response_text += f"Summary: {summary}\n\n"
        
        # Add technical analysis details if available
        tech = result.get('technical_analysis')
        if tech and not tech.get('error'):
            response_text += f"Technical Analysis:\n"
            response_text += f"  - Current Price: ${tech.get('current_price', 'N/A')}\n"
            response_text += f"  - RSI: {tech.get('rsi', 'N/A')}\n"
            response_text += f"  - Signal: {tech.get('rsi_signal', 'N/A')}\n\n"
        
        # Add sentiment analysis details if available
        sent = result.get('sentiment_analysis')
        if sent and not sent.get('error'):
            response_text += f"Sentiment Analysis:\n"
            response_text += f"  - Sentiment: {sent.get('sentiment', 'N/A')}\n"
            response_text += f"  - Confidence: {sent.get('confidence', 0):.0%}\n"
    
    # Format in Bedrock Agent response structure
    bedrock_response = {
        "messageVersion": "1.0",
        "response": {
            "actionGroup": os.environ.get('ACTION_GROUP_NAME', 'TradingTools'),
            "apiPath": os.environ.get('API_PATH', '/analyze'),
            "httpMethod": "POST",
            "httpStatusCode": 200 if not is_error else 500,
            "responseBody": {
                "application/json": {
                    "body": json.dumps({
                        "result": result,
                        "message": response_text
                    })
                }
            }
        },
        "sessionAttributes": {
            "lastTicker": result.get('ticker', ''),
            "lastRecommendation": result.get('recommendation', ''),
            "timestamp": result.get('timestamp', '')
        }
    }
    
    logger.info("Bedrock response formatted successfully")
    return bedrock_response


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda entry point for Bedrock Agent integration.
    
    This function:
    1. Parses the Bedrock Agent event to extract the query
    2. Calls the Supervisor Agent to process the query
    3. Formats the response for Bedrock Agent
    4. Handles errors gracefully
    
    Args:
        event: AWS Lambda event (Bedrock Agent format)
        context: AWS Lambda context object
        
    Returns:
        Bedrock-compliant response dictionary
    """
    # Log invocation details
    logger.info(f"Lambda invoked with request ID: {context.aws_request_id if context else 'N/A'}")
    logger.info(f"Event: {json.dumps(event, default=str)}")
    
    # Detect if this is an API Gateway event
    is_api_gateway = 'httpMethod' in event or 'requestContext' in event
    
    try:
        # Step 1: Parse event to extract query
        query = parse_bedrock_event(event)
        
        # Step 2: Get API key from environment (optional)
        api_key = os.environ.get('ALPHA_VANTAGE_API_KEY')
        
        # Step 3: Process query through Supervisor Agent
        logger.info(f"Processing query: {query}")
        result = handle_query(query, api_key)
        
        # Step 4: Format response based on event type
        if is_api_gateway:
            # Return API Gateway format
            response = {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'POST,GET,OPTIONS'
                },
                'body': json.dumps(result)
            }
        else:
            # Return Bedrock format
            response = format_bedrock_response(result)
        
        logger.info("Lambda execution completed successfully")
        return response
        
    except ValueError as e:
        # Event parsing errors
        logger.error(f"Event parsing error: {str(e)}")
        error_result = {
            "ticker": None,
            "recommendation": "ERROR",
            "summary": f"Invalid request format: {str(e)}",
            "error": str(e),
            "timestamp": None
        }
        if is_api_gateway:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps(error_result)
            }
        return format_bedrock_response(error_result)
        
    except TradingSystemError as e:
        # Known system errors
        logger.error(f"Trading system error: {str(e)}")
        error_result = {
            "ticker": None,
            "recommendation": "ERROR",
            "summary": f"Analysis failed: {str(e)}",
            "error": str(e),
            "timestamp": None
        }
        if is_api_gateway:
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps(error_result)
            }
        return format_bedrock_response(error_result)
        
    except Exception as e:
        # Unexpected errors
        logger.error(f"Unexpected error in Lambda handler: {str(e)}", exc_info=True)
        error_result = {
            "ticker": None,
            "recommendation": "ERROR",
            "summary": "An unexpected error occurred",
            "error": str(e),
            "timestamp": None
        }
        return format_bedrock_response(error_result)
