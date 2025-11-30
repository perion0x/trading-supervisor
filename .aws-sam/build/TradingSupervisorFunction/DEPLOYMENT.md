# Multi-Agentic Trading Supervisor - Deployment Guide

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Deployment Methods](#deployment-methods)
4. [Configuration](#configuration)
5. [Deployment Steps](#deployment-steps)
6. [Verification](#verification)
7. [Monitoring](#monitoring)
8. [Troubleshooting](#troubleshooting)

## Overview

This guide provides comprehensive instructions for deploying the Multi-Agentic Trading Supervisor to AWS Lambda with Bedrock Agent integration. The system can be deployed using three methods:

- **AWS SAM** (Recommended for production)
- **Serverless Framework** (Recommended for rapid development)
- **Manual AWS CLI** (For testing only)

### Architecture

```
User Query → Bedrock Agent → Lambda Function → Trading Supervisor
                                    ↓
                          Technical Analyst (yfinance)
                          Sentiment Analyst (Alpha Vantage)
                                    ↓
                          Trading Recommendation → User
```

## Prerequisites

### Required Tools

1. **AWS Account** with appropriate permissions
2. **AWS CLI** configured with credentials
   ```bash
   aws configure
   ```

3. **Python 3.11+** installed
   ```bash
   python --version
   ```

4. **Git** for version control

### Optional Tools (based on deployment method)

**For AWS SAM:**
```bash
pip install aws-sam-cli
sam --version
```

**For Serverless Framework:**
```bash
npm install -g serverless
serverless --version
```

### AWS Permissions Required

Your AWS user/role needs:
- `lambda:*` - Lambda function management
- `iam:CreateRole`, `iam:AttachRolePolicy` - IAM role creation
- `logs:*` - CloudWatch Logs access
- `cloudformation:*` - Stack management (for SAM)
- `bedrock:*` - Bedrock Agent integration (optional)

## Deployment Methods

### Method Comparison

| Feature | AWS SAM | Serverless | Manual CLI |
|---------|---------|------------|------------|
| **Complexity** | Medium | Low | High |
| **IaC Support** | ✅ CloudFormation | ✅ Custom | ❌ |
| **Rollback** | ✅ Automatic | ✅ Built-in | ❌ Manual |
| **Multi-env** | ✅ Parameters | ✅ Stages | ⚠️ Manual |
| **CI/CD Ready** | ✅ | ✅ | ⚠️ |
| **Best For** | Production | Development | Testing |

## Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `ALPHA_VANTAGE_API_KEY` | API key for sentiment analysis | No | '' (mock mode) |
| `LOG_LEVEL` | Logging verbosity | No | INFO |
| `ACTION_GROUP_NAME` | Bedrock action group | No | TradingTools |
| `API_PATH` | Bedrock API path | No | /analyze |

### Lambda Settings

```yaml
Runtime: python3.11
Memory: 512 MB
Timeout: 30 seconds
Architecture: x86_64
```

### IAM Role Policy

Minimal permissions required:

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

## Deployment Steps

### Option 1: AWS SAM (Recommended)

#### 1. Install SAM CLI

```bash
pip install aws-sam-cli
sam --version
```

#### 2. Build Application

```bash
sam build
```

#### 3. Deploy (First Time)

```bash
sam deploy --guided
```

You'll be prompted for:
- **Stack name**: `trading-supervisor-dev`
- **AWS Region**: `us-east-1` (or your preferred region)
- **AlphaVantageApiKey**: (optional, press Enter to skip)
- **Environment**: `dev` (or `staging`, `prod`)
- **Confirm changes**: Y
- **Allow IAM role creation**: Y
- **Save arguments to config**: Y

#### 4. Deploy (Updates)

```bash
sam deploy
```

#### 5. View Outputs

```bash
sam list stack-outputs --stack-name trading-supervisor-dev
```

#### SAM Commands Reference

```bash
# Build
sam build

# Deploy to specific environment
sam deploy --parameter-overrides Environment=prod

# View logs
sam logs -n trading-supervisor-dev --tail

# Delete deployment
sam delete --stack-name trading-supervisor-dev
```

### Option 2: Serverless Framework

#### 1. Install Serverless

```bash
npm install -g serverless
serverless plugin install -n serverless-python-requirements
```

#### 2. Configure Environment (Optional)

```bash
export ALPHA_VANTAGE_API_KEY=your_api_key
export LOG_LEVEL=INFO
```

#### 3. Deploy

```bash
# Deploy to dev
serverless deploy

# Deploy to specific stage
serverless deploy --stage prod --region us-west-2
```

#### 4. View Info

```bash
serverless info --stage dev
```

#### Serverless Commands Reference

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

### Option 3: Manual AWS CLI

#### 1. Create Deployment Package

```bash
# Install dependencies
mkdir -p package
pip install -r requirements.txt -t package/

# Copy source code
cp -r src package/

# Create ZIP
cd package
zip -r ../lambda-deployment.zip .
cd ..
```

#### 2. Create IAM Role

```bash
# Create trust policy
cat > trust-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {"Service": "lambda.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

# Create role
aws iam create-role \
  --role-name trading-supervisor-execution-role \
  --assume-role-policy-document file://trust-policy.json

# Attach policy
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
  --environment Variables="{LOG_LEVEL=INFO,ACTION_GROUP_NAME=TradingTools}"
```

#### 4. Update Function (for updates)

```bash
aws lambda update-function-code \
  --function-name trading-supervisor \
  --zip-file fileb://lambda-deployment.zip
```

## Verification

### 1. Test Lambda Function

```bash
# Create test event
cat > test-event.json << 'EOF'
{
  "messageVersion": "1.0",
  "inputText": "Analyze AAPL",
  "sessionId": "test-session-123"
}
EOF

# Invoke function
aws lambda invoke \
  --function-name trading-supervisor-dev \
  --payload file://test-event.json \
  --cli-binary-format raw-in-base64-out \
  response.json

# View response
cat response.json | python -m json.tool
```

### 2. Check Logs

```bash
# SAM
sam logs -n trading-supervisor-dev --tail

# Serverless
serverless logs -f tradingSupervisor --tail

# AWS CLI
aws logs tail /aws/lambda/trading-supervisor-dev --follow
```

### 3. Run Local Tests

```bash
# Run all tests
pytest tests/ -v

# Run property-based tests
pytest tests/test_properties_lambda.py -v

# Run integration tests
pytest tests/test_integration_e2e.py -v
```

### 4. Test with Demo Script

```bash
python demo_lambda.py
```

## Bedrock Agent Integration

### 1. Get Lambda ARN

```bash
# SAM
sam list stack-outputs --stack-name trading-supervisor-dev

# Serverless
serverless info --stage dev

# CLI
aws lambda get-function \
  --function-name trading-supervisor-dev \
  --query 'Configuration.FunctionArn' \
  --output text
```

### 2. Create Bedrock Agent

Via AWS Console:
1. Navigate to Amazon Bedrock
2. Click "Agents" → "Create Agent"
3. Name: `TradingSupervisor`
4. Instruction: "You are a fund manager that analyzes stocks using technical and sentiment analysis tools."
5. Model: Select foundation model (e.g., Claude)
6. Create action group: `TradingTools`
7. Link Lambda function ARN
8. Upload API schema (see below)

### 3. API Schema for Bedrock

```json
{
  "openapi": "3.0.0",
  "info": {
    "title": "Trading Supervisor API",
    "version": "1.0.0"
  },
  "paths": {
    "/analyze": {
      "post": {
        "summary": "Analyze stock ticker",
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
                    "description": "Stock ticker (e.g., AAPL)"
                  }
                },
                "required": ["ticker"]
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "Analysis result"
          }
        }
      }
    }
  }
}
```

### 4. Grant Bedrock Permissions

```bash
aws lambda add-permission \
  --function-name trading-supervisor-dev \
  --statement-id bedrock-agent-access \
  --action lambda:InvokeFunction \
  --principal bedrock.amazonaws.com \
  --source-arn arn:aws:bedrock:REGION:ACCOUNT:agent/AGENT_ID
```

## Monitoring

### CloudWatch Metrics

Key metrics to monitor:
- **Invocations**: Total function calls
- **Duration**: Execution time (target: < 10s)
- **Errors**: Failed invocations
- **Throttles**: Rate limiting events
- **Concurrent Executions**: Parallel invocations

### CloudWatch Logs

View logs:
```bash
aws logs tail /aws/lambda/trading-supervisor-dev --follow
```

### Custom Dashboards

Create CloudWatch dashboard:
1. Navigate to CloudWatch → Dashboards
2. Create dashboard: `TradingSupervisor`
3. Add widgets for key metrics
4. Set up alarms for errors and latency

### Alarms

```bash
# Create error alarm
aws cloudwatch put-metric-alarm \
  --alarm-name trading-supervisor-errors \
  --alarm-description "Alert on Lambda errors" \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --threshold 5 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=FunctionName,Value=trading-supervisor-dev
```

## Troubleshooting

### Common Issues

#### 1. Timeout Errors

**Symptom**: Lambda times out after 30 seconds

**Solutions**:
- Check yfinance API connectivity
- Verify network configuration
- Increase timeout (max 900s for Lambda)
- Check for infinite loops in code

#### 2. Import Errors

**Symptom**: `ModuleNotFoundError` in Lambda

**Solutions**:
- Verify all dependencies in deployment package
- Check Python version compatibility (3.11)
- Rebuild deployment package
- Ensure `src/` directory structure is correct

#### 3. Permission Errors

**Symptom**: `AccessDeniedException` or IAM errors

**Solutions**:
- Verify IAM role has required permissions
- Check CloudWatch Logs permissions
- Ensure Lambda execution role is attached
- Review trust policy

#### 4. Event Parsing Errors

**Symptom**: `ValueError: No query found in event`

**Solutions**:
- Verify event format matches Bedrock specification
- Check `inputText` field is present
- Test with sample event locally
- Review Lambda logs for event structure

#### 5. API Rate Limiting

**Symptom**: yfinance or Alpha Vantage errors

**Solutions**:
- Implement caching for frequent tickers
- Add exponential backoff retry logic
- Use Alpha Vantage premium tier
- Monitor API usage

### Debug Commands

```bash
# Check function configuration
aws lambda get-function-configuration \
  --function-name trading-supervisor-dev

# View recent errors
aws logs filter-log-events \
  --log-group-name /aws/lambda/trading-supervisor-dev \
  --filter-pattern "ERROR"

# Test locally
python -c "from src.lambda_handler import lambda_handler; \
  print(lambda_handler({'inputText': 'Analyze AAPL'}, None))"
```

### Getting Help

- Check CloudWatch Logs for detailed error messages
- Review `LAMBDA_DEPLOYMENT.md` for additional details
- Run local tests: `pytest tests/ -v`
- Check AWS Lambda documentation
- Review Bedrock Agent integration guide

## CI/CD Integration

### GitHub Actions

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy Trading Supervisor

on:
  push:
    branches: [main, develop]

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
        run: pip install aws-sam-cli pytest
      
      - name: Run tests
        run: pytest tests/ -v
      
      - name: Configure AWS
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      
      - name: Deploy
        run: |
          sam build
          sam deploy --no-confirm-changeset
```

## Rollback Procedures

### SAM Rollback

```bash
# View stack events
aws cloudformation describe-stack-events \
  --stack-name trading-supervisor-dev

# Rollback
aws cloudformation cancel-update-stack \
  --stack-name trading-supervisor-dev
```

### Serverless Rollback

```bash
serverless rollback --timestamp TIMESTAMP
```

### Manual Rollback

```bash
aws lambda update-function-code \
  --function-name trading-supervisor-dev \
  --zip-file fileb://previous-version.zip
```

## Cost Optimization

- Use ARM64 architecture for 20% cost savings
- Implement caching to reduce API calls
- Set appropriate memory size (512 MB recommended)
- Use Lambda reserved concurrency if needed
- Monitor and optimize cold start times

## Security Best Practices

1. **Secrets Management**: Store API keys in AWS Secrets Manager
2. **Least Privilege**: Use minimal IAM permissions
3. **VPC**: Deploy in VPC for private resource access
4. **Encryption**: Enable encryption for environment variables
5. **Logging**: Sanitize logs to avoid exposing sensitive data

## Quick Start Checklist

- [ ] Install AWS SAM CLI or Serverless Framework
- [ ] Configure AWS credentials
- [ ] Clone repository
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Run tests: `pytest tests/ -v`
- [ ] Deploy to dev: `sam deploy --guided` or `serverless deploy`
- [ ] Test deployment with sample event
- [ ] Check CloudWatch logs
- [ ] Create Bedrock Agent (optional)
- [ ] Test end-to-end integration
- [ ] Set up monitoring and alarms
- [ ] Deploy to production

## Additional Resources

- [AWS SAM Documentation](https://docs.aws.amazon.com/serverless-application-model/)
- [Serverless Framework Docs](https://www.serverless.com/framework/docs)
- [AWS Lambda Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)
- [Amazon Bedrock Agents Guide](https://docs.aws.amazon.com/bedrock/latest/userguide/agents.html)
- Project README: `README.md`
- Lambda-specific guide: `LAMBDA_DEPLOYMENT.md`
