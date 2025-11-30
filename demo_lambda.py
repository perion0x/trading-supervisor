"""
Demo script for AWS Lambda Handler with Bedrock Integration

This script demonstrates how the Lambda handler processes Bedrock Agent events
and returns properly formatted responses.
"""

import json
from src.lambda_handler import lambda_handler


class MockContext:
    """Mock AWS Lambda context for testing"""
    def __init__(self):
        self.request_id = "demo-request-123"
        self.function_name = "trading-supervisor"
        self.memory_limit_in_mb = 512


def demo_bedrock_event():
    """Demonstrate Lambda handler with a Bedrock Agent event"""
    print("=" * 80)
    print("AWS Lambda Handler Demo - Bedrock Agent Integration")
    print("=" * 80)
    print()
    
    # Create a sample Bedrock Agent event
    event = {
        "messageVersion": "1.0",
        "agent": {
            "name": "TradingSupervisor",
            "id": "agent-123",
            "alias": "prod",
            "version": "1"
        },
        "inputText": "Analyze AAPL stock",
        "sessionId": "session-demo-123",
        "sessionAttributes": {},
        "promptSessionAttributes": {}
    }
    
    print("Input Event:")
    print(json.dumps(event, indent=2))
    print()
    
    # Create mock context
    context = MockContext()
    
    # Invoke Lambda handler
    print("Invoking Lambda handler...")
    print()
    
    response = lambda_handler(event, context)
    
    print("Response:")
    print(json.dumps(response, indent=2))
    print()
    
    # Extract and display the message
    response_body = response["response"]["responseBody"]["application/json"]["body"]
    parsed_body = json.loads(response_body)
    
    print("=" * 80)
    print("Formatted Message for User:")
    print("=" * 80)
    print(parsed_body["message"])
    print()


def demo_error_handling():
    """Demonstrate error handling with invalid event"""
    print("=" * 80)
    print("Error Handling Demo")
    print("=" * 80)
    print()
    
    # Create an invalid event (missing inputText)
    event = {
        "messageVersion": "1.0",
        "sessionId": "session-error-123"
    }
    
    print("Invalid Event (missing inputText):")
    print(json.dumps(event, indent=2))
    print()
    
    context = MockContext()
    
    print("Invoking Lambda handler...")
    print()
    
    response = lambda_handler(event, context)
    
    print("Error Response:")
    print(json.dumps(response, indent=2))
    print()
    
    # Check status code
    status_code = response["response"]["httpStatusCode"]
    print(f"HTTP Status Code: {status_code}")
    print()


def demo_alternative_query_formats():
    """Demonstrate handling of alternative query field names"""
    print("=" * 80)
    print("Alternative Query Format Demo")
    print("=" * 80)
    print()
    
    # Event with 'query' field instead of 'inputText'
    event = {
        "messageVersion": "1.0",
        "query": "What about TSLA?",
        "sessionId": "session-alt-123"
    }
    
    print("Event with 'query' field:")
    print(json.dumps(event, indent=2))
    print()
    
    context = MockContext()
    
    response = lambda_handler(event, context)
    
    response_body = response["response"]["responseBody"]["application/json"]["body"]
    parsed_body = json.loads(response_body)
    
    print("Response Message:")
    print(parsed_body["message"][:200] + "...")
    print()


if __name__ == "__main__":
    # Run demos
    demo_bedrock_event()
    print("\n" + "=" * 80 + "\n")
    
    demo_error_handling()
    print("\n" + "=" * 80 + "\n")
    
    demo_alternative_query_formats()
    
    print("=" * 80)
    print("Demo Complete!")
    print("=" * 80)
