# AWS Lambda Deployment Guide

## Overview

This guide explains how to deploy the Multi-Agentic Trading Supervisor as an AWS Lambda function integrated with AWS Bedrock Agents. Three deployment methods are provided:

1. **AWS SAM (Recommended)** - Infrastructure as Code with CloudFormation
2. **Serverless Framework** - Simplified deployment with plugins
3. **Manual AWS CLI** - Direct deployment for testing

## Lambda Handler

The Lambda handler is implemented in `src/lambda_handler.py` and provides:

- **Entry Point**: `lambda_handler(event, context)` - AWS Lambda function handler
- **Event Parsing**: `parse_bedrock_event(event)` - Extracts queries from Bedrock Agent events
- **Response Formatting**: `format_bedrock_response(result)` - Formats responses for Bedrock

## Environment Variables

Configure the following environment variables in your Lambda function:

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `ALPHA_VANTAGE_API_KEY` | API key for Alpha Vantage sentiment analysis | No | None (uses mock sentiment) |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | No | INFO |
| `ACTION_GROUP_NAME` | Bedrock action group name | No | TradingTools |
| `API_PATH` | API path for Bedrock response | No | /analyze |

## Lambda Configuration

### Recommended Settings

```yaml
Runtime: Python 3.11 or higher
Memory: 512 MB
Timeout: 30 seconds
Architecture: x86_64 or arm64
```

### IAM Role Permissions

The Lambda execution role needs minimal permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    }
  ]
}
```

## Deployment Methods

### Method 1: AWS SAM (Recommended)

AWS SAM provides Infrastructure as Code with CloudFormation templates.

#### Prerequisites

```bash
# Install AWS SAM CLI
pip install aws-sam-cli

# Verify installation
sam --version
```

#### Deployment Steps

1. **Build the application**:
```bash
sam build
```

2. **Deploy (first time)**:
```bash
sam deploy --guided
```

You'll be prompted for:
- Stack name (e.g., `trading-supervisor-dev`)
- AWS Region (e.g., `us-east-1`)
- AlphaVantageApiKey (optional, press Enter to skip)
- Environment (dev/staging/prod)
- Confirm changes before deploy
- Allow SAM CLI IAM role creation

3. **Deploy (subsequent updates)**:
```bash
sam deploy
```

4. **View outputs**:
```bash
sam list stack-outputs --stack-name trading-supervisor-dev
```

#### SAM Configuration

The `template.yaml` file defines:
- Lambda function with proper IAM role
- CloudWatch Log Group with 7-day retention
- Environment-specific naming (dev/staging/prod)
- Parameterized API key configuration

#### SAM Commands

```bash
# Build
sam build

# Deploy to dev
sam deploy --parameter-overrides Environment=dev

# Deploy to prod with API key
sam deploy --parameter-overrides Environment=prod AlphaVantageApiKey=YOUR_KEY

# View logs
sam logs -n trading-supervisor-dev --tail

# Delete stack
sam delete --stack-name trading-supervisor-dev
```

### Method 2: Serverless Framework

Serverless Framework simplifies deployment with plugins and conventions.

#### Prerequisites

```bash
# Install Serverless Framework
npm install -g serverless

# Install Python requirements plugin
serverless plugin install -n serverless-python-requirements

# Verify installation
serverless --version
```

#### Deployment Steps

1. **Set environment variables** (optional):
```bash
export ALPHA_VANTAGE_API_KEY=your_api_key_here
export LOG_LEVEL=INFO
```

2. **Deploy to dev**:
```bash
serverless deploy
```

3. **Deploy to specific stage**:
```bash
serverless deploy --stage prod --region us-west-2
```

4. **View function info**:
```bash
serverless info
```

#### Serverless Configuration

The `serverless.yml` file defines:
- Lambda function with execution role
- CloudWatch Logs with retention
- Python requirements packaging
- Stage-based deployments (dev/staging/prod)

#### Serverless Commands

```bash
# Deploy
serverless deploy --stage dev

# Deploy function only (faster)
serverless deploy function -f tradingSupervisor

# View logs
serverless logs -f tradingSupervisor --tail

# Invoke function
serverless invoke -f tradingSupervisor --data '{"inputText":"Analyze AAPL"}'

# Remove deployment
serverless remove --stage dev
```

### Method 3: Manual AWS CLI

Direct deployment using AWS CLI for testing purposes.

#### 1. Package Dependencies

```bash
# Create deployment package
mkdir -p package
pip install -r requirements.txt -t package/
cp -r src package/
cd package
zip -r ../lambda-deployment.zip .
cd ..
```

#### 2. Create IAM Role

```bash
# Create trust policy
cat > trust-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

# Create role
aws iam create-role \
  --role-name trading-supervisor-execution-role \
  --assume-role-policy-document file://trust-policy.json

# Attach basic execution policy
aws iam attach-role-policy \
  --role-name trading-supervisor-execution-role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
```

#### 3. Create Lambda Function

```bash
aws lambda create-function \
  --function-name trading-supervisor \
  --runtime python3.11 \
  --role arn:aws:iam::YOUR_ACCOUNT_ID:role/trading-supervisor-execution-role \
  --handler src.lambda_handler.lambda_handler \
  --zip-file fileb://lambda-deployment.zip \
  --timeout 30 \
  --memory-size 512 \
  --environment Variables="{LOG_LEVEL=INFO,ACTION_GROUP_NAME=TradingTools,API_PATH=/analyze}"
```

#### 4. Update Lambda Function (for updates)

```bash
aws lambda update-function-code \
  --function-name trading-supervisor \
  --zip-file fileb://lambda-deployment.zip
```

#### 5. Test Lambda Function

```bash
# Create test event
cat > test-event.json << EOF
{
  "messageVersion": "1.0",
  "inputText": "Analyze AAPL",
  "sessionId": "test-session"
}
EOF

# Invoke function
aws lambda invoke \
  --function-name trading-supervisor \
  --payload file://test-event.json \
  --cli-binary-format raw-in-base64-out \
  response.json

# View response
cat response.json
```

## Deployment Comparison

| Feature | AWS SAM | Serverless Framework | Manual CLI |
|---------|---------|---------------------|------------|
| **Ease of Use** | Medium | Easy | Hard |
| **Infrastructure as Code** | Yes (CloudFormation) | Yes (Custom) | No |
| **Rollback Support** | Yes | Yes | No |
| **Multi-environment** | Yes | Yes | Manual |
| **Plugin Ecosystem** | Limited | Extensive | N/A |
| **Best For** | Production, AWS-native | Rapid development | Testing only |

**Recommendation**: Use AWS SAM for production deployments, Serverless Framework for rapid iteration.

## Bedrock Agent Integration

### Event Format

Bedrock Agent sends events in this format:

```json
{
  "messageVersion": "1.0",
  "agent": {
    "name": "TradingSupervisor",
    "id": "agent-id",
    "alias": "prod",
    "version": "1"
  },
  "inputText": "Analyze AAPL",
  "sessionId": "session-123",
  "sessionAttributes": {},
  "promptSessionAttributes": {}
}
```

### Response Format

Lambda returns responses in Bedrock-compliant format:

```json
{
  "messageVersion": "1.0",
  "response": {
    "actionGroup": "TradingTools",
    "apiPath": "/analyze",
    "httpMethod": "POST",
    "httpStatusCode": 200,
    "responseBody": {
      "application/json": {
        "body": "{...}"
      }
    }
  },
  "sessionAttributes": {
    "lastTicker": "AAPL",
    "lastRecommendation": "BUY",
    "timestamp": "2025-11-29T10:30:00Z"
  }
}
```

### Connecting Lambda to Bedrock Agent

After deploying the Lambda function, connect it to a Bedrock Agent:

1. **Get Lambda ARN**:
```bash
# SAM
sam list stack-outputs --stack-name trading-supervisor-dev

# Serverless
serverless info --stage dev

# CLI
aws lambda get-function --function-name trading-supervisor --query 'Configuration.FunctionArn'
```

2. **Create Bedrock Agent** (via AWS Console or CLI):
   - Navigate to AWS Bedrock console
   - Create new agent: "TradingSupervisor"
   - Set instruction: "You are a fund manager that analyzes stocks using technical and sentiment analysis tools."
   - Add action group: "TradingTools"
   - Link Lambda function ARN
   - Define API schema (see below)

3. **API Schema for Bedrock**:
```json
{
  "openapi": "3.0.0",
  "info": {
    "title": "Trading Supervisor API",
    "version": "1.0.0",
    "description": "API for stock trading analysis"
  },
  "paths": {
    "/analyze": {
      "post": {
        "summary": "Analyze a stock ticker",
        "description": "Provides comprehensive trading analysis combining technical indicators and sentiment",
        "operationId": "analyzeStock",
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "properties": {
                  "ticker": {
                    "type": "string",
                    "description": "Stock ticker symbol (e.g., AAPL, MSFT)"
                  }
                },
                "required": ["ticker"]
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "Successful analysis",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "properties": {
                    "ticker": {"type": "string"},
                    "recommendation": {"type": "string"},
                    "summary": {"type": "string"},
                    "confidence": {"type": "number"}
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
```

4. **Grant Lambda Permissions**:
```bash
aws lambda add-permission \
  --function-name trading-supervisor \
  --statement-id bedrock-agent-access \
  --action lambda:InvokeFunction \
  --principal bedrock.amazonaws.com \
  --source-arn arn:aws:bedrock:REGION:ACCOUNT:agent/AGENT_ID
```

## Testing

### Local Testing

Run the demo script to test locally:

```bash
python demo_lambda.py
```

### Property-Based Tests

Run the property-based tests:

```bash
pytest tests/test_properties_lambda.py -v
```

### Integration Testing

Test with a sample Bedrock event:

```python
from src.lambda_handler import lambda_handler

event = {
    "messageVersion": "1.0",
    "inputText": "Analyze AAPL",
    "sessionId": "test-session"
}

class MockContext:
    request_id = "test-123"

response = lambda_handler(event, MockContext())
print(response)
```

## Monitoring

### CloudWatch Logs

Lambda automatically logs to CloudWatch. View logs:

```bash
aws logs tail /aws/lambda/trading-supervisor --follow
```

### Key Metrics to Monitor

- **Invocations**: Number of Lambda invocations
- **Duration**: Execution time (should be < 10 seconds)
- **Errors**: Failed invocations
- **Throttles**: Rate limiting events

### Custom Metrics

The handler logs:
- Query extraction success/failure
- Tool invocation results
- Recommendation generation
- Error details

## Troubleshooting

### Common Issues

1. **Timeout Errors**
   - Increase Lambda timeout (max 30s for yfinance calls)
   - Check network connectivity to yfinance API

2. **Import Errors**
   - Ensure all dependencies are in the deployment package
   - Verify Python version compatibility

3. **Event Parsing Errors**
   - Check event format matches Bedrock Agent specification
   - Verify `inputText` field is present

4. **API Rate Limiting**
   - yfinance may rate limit requests
   - Implement caching for frequently requested tickers

## Cost Optimization

- Use ARM64 architecture for lower costs
- Implement caching to reduce API calls
- Set appropriate memory size (512 MB recommended)
- Use Lambda reserved concurrency if needed

## Security Best Practices

1. **Environment Variables**: Store API keys in AWS Secrets Manager
2. **IAM Roles**: Use least-privilege permissions
3. **VPC**: Deploy in VPC if accessing private resources
4. **Encryption**: Enable encryption at rest for environment variables

## CI/CD Integration

### GitHub Actions Example

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy Trading Supervisor

on:
  push:
    branches:
      - main
      - develop

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install aws-sam-cli
          pip install -r requirements.txt
      
      - name: Run tests
        run: |
          pytest tests/ -v
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      
      - name: SAM Build
        run: sam build
      
      - name: SAM Deploy
        run: |
          if [ "${{ github.ref }}" == "refs/heads/main" ]; then
            sam deploy --no-confirm-changeset --no-fail-on-empty-changeset \
              --parameter-overrides Environment=prod
          else
            sam deploy --no-confirm-changeset --no-fail-on-empty-changeset \
              --parameter-overrides Environment=dev
          fi
```

### GitLab CI Example

Create `.gitlab-ci.yml`:

```yaml
stages:
  - test
  - deploy

variables:
  AWS_DEFAULT_REGION: us-east-1

test:
  stage: test
  image: python:3.11
  script:
    - pip install -r requirements.txt
    - pytest tests/ -v
  only:
    - branches

deploy_dev:
  stage: deploy
  image: python:3.11
  script:
    - pip install aws-sam-cli
    - sam build
    - sam deploy --parameter-overrides Environment=dev
  only:
    - develop

deploy_prod:
  stage: deploy
  image: python:3.11
  script:
    - pip install aws-sam-cli
    - sam build
    - sam deploy --parameter-overrides Environment=prod
  only:
    - main
  when: manual
```

## Environment-Specific Deployments

### Development Environment

```bash
# SAM
sam deploy --parameter-overrides Environment=dev

# Serverless
serverless deploy --stage dev
```

### Staging Environment

```bash
# SAM
sam deploy --parameter-overrides Environment=staging

# Serverless
serverless deploy --stage staging
```

### Production Environment

```bash
# SAM
sam deploy --parameter-overrides Environment=prod AlphaVantageApiKey=YOUR_PROD_KEY

# Serverless
export ALPHA_VANTAGE_API_KEY=YOUR_PROD_KEY
serverless deploy --stage prod
```

## Post-Deployment Verification

### 1. Check Lambda Function

```bash
# Get function info
aws lambda get-function --function-name trading-supervisor-dev

# Check environment variables
aws lambda get-function-configuration --function-name trading-supervisor-dev
```

### 2. Test Lambda Invocation

```bash
# Create test event
echo '{"inputText":"Analyze AAPL","sessionId":"test"}' > event.json

# Invoke
aws lambda invoke \
  --function-name trading-supervisor-dev \
  --payload file://event.json \
  --cli-binary-format raw-in-base64-out \
  output.json

# View result
cat output.json | jq .
```

### 3. Monitor Logs

```bash
# SAM
sam logs -n trading-supervisor-dev --tail

# Serverless
serverless logs -f tradingSupervisor --tail

# AWS CLI
aws logs tail /aws/lambda/trading-supervisor-dev --follow
```

### 4. Run Integration Tests

```bash
# Local test
python demo_lambda.py

# Property-based tests
pytest tests/test_properties_lambda.py -v

# Full test suite
pytest tests/ -v
```

## Rollback Procedures

### SAM Rollback

```bash
# List stack events
aws cloudformation describe-stack-events --stack-name trading-supervisor-dev

# Rollback to previous version
aws cloudformation cancel-update-stack --stack-name trading-supervisor-dev
```

### Serverless Rollback

```bash
# Rollback to previous deployment
serverless rollback --timestamp TIMESTAMP
```

### Manual Rollback

```bash
# Update to previous code version
aws lambda update-function-code \
  --function-name trading-supervisor-dev \
  --zip-file fileb://previous-version.zip
```

## Next Steps

1. **Deploy Lambda function** using preferred method (SAM recommended)
2. **Create Bedrock Agent** in AWS Console
3. **Configure action group** pointing to Lambda ARN
4. **Test end-to-end integration** with sample queries
5. **Set up monitoring** with CloudWatch dashboards
6. **Configure alerts** for errors and performance issues
7. **Optimize based on usage patterns** and metrics
8. **Implement CI/CD pipeline** for automated deployments

## Quick Start Checklist

- [ ] Install AWS SAM CLI or Serverless Framework
- [ ] Configure AWS credentials (`aws configure`)
- [ ] Set environment variables (optional: `ALPHA_VANTAGE_API_KEY`)
- [ ] Run tests locally (`pytest tests/ -v`)
- [ ] Deploy to dev environment
- [ ] Verify deployment with test invocation
- [ ] Check CloudWatch logs
- [ ] Create Bedrock Agent (if using Bedrock)
- [ ] Test end-to-end flow
- [ ] Deploy to production when ready
