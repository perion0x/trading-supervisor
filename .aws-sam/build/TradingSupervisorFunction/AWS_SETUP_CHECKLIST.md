# AWS Setup Checklist for Trading Supervisor Deployment

## ✅ Step 1: Create AWS Account (5-10 minutes)
- [ ] Go to https://aws.amazon.com/free/
- [ ] Click "Create a Free Account"
- [ ] Enter email and password
- [ ] Provide contact information
- [ ] Add payment method (for verification - won't be charged in free tier)
- [ ] Complete phone verification
- [ ] Choose "Basic Support - Free" plan
- [ ] Wait for account activation email

## ✅ Step 2: Sign In to AWS Console
- [ ] Go to https://console.aws.amazon.com/
- [ ] Sign in with your root account credentials
- [ ] You should see the AWS Management Console

## ✅ Step 3: Create IAM User for Deployment
1. [ ] In AWS Console, search for "IAM" in the top search bar
2. [ ] Click on "IAM" service
3. [ ] Click "Users" in the left sidebar
4. [ ] Click "Create user" button
5. [ ] Enter username: `trading-supervisor-deployer`
6. [ ] Click "Next"

### Set Permissions:
7. [ ] Choose "Attach policies directly"
8. [ ] Search and select these policies:
   - [ ] `AWSLambda_FullAccess`
   - [ ] `IAMFullAccess`
   - [ ] `CloudWatchLogsFullAccess`
   - [ ] `AWSCloudFormationFullAccess`
9. [ ] Click "Next"
10. [ ] Click "Create user"

### Create Access Keys:
11. [ ] Click on the user you just created
12. [ ] Go to "Security credentials" tab
13. [ ] Scroll down to "Access keys"
14. [ ] Click "Create access key"
15. [ ] Choose "Command Line Interface (CLI)"
16. [ ] Check the confirmation checkbox
17. [ ] Click "Create access key"
18. [ ] **IMPORTANT**: Copy both:
    - Access Key ID
    - Secret Access Key
    - (Or download the CSV file)
19. [ ] Click "Done"

## ✅ Step 4: Tools Installation (Automated - In Progress)
- [x] Homebrew (already installed)
- [x] AWS CLI (installed)
- [ ] AWS SAM CLI (downloading... ~38 MB)

## ✅ Step 5: Configure AWS Credentials (After Tools Install)
Run this command and enter your credentials:
```bash
aws configure
```

You'll be prompted for:
- AWS Access Key ID: [paste from step 18]
- AWS Secret Access Key: [paste from step 18]
- Default region name: `us-east-1`
- Default output format: `json`

## ✅ Step 6: Deploy Your Trading Supervisor
```bash
# Build the Lambda package
sam build

# Deploy (guided mode for first time)
sam deploy --guided
```

During deployment, accept defaults for most options:
- Stack Name: `trading-supervisor`
- AWS Region: `us-east-1`
- Parameter AlphaVantageApiKey: [your key or leave blank]
- Parameter Environment: `dev`
- Confirm changes: `Y`
- Allow IAM role creation: `Y`
- Save configuration: `Y`

## ✅ Step 7: Test Your Deployment
```bash
# Invoke the Lambda function
aws lambda invoke \
  --function-name trading-supervisor-dev \
  --payload '{"inputText": "Analyze AAPL"}' \
  response.json

# View the response
cat response.json
```

## 🎉 Success Indicators
- [ ] SAM deploy completes without errors
- [ ] You see CloudFormation outputs with Lambda ARN
- [ ] Test invocation returns a trading recommendation
- [ ] You can see the function in AWS Lambda console

## 📞 Need Help?
If you get stuck at any step, let me know which step number and I'll help troubleshoot!

---

**Current Status**: Waiting for SAM CLI to finish downloading...
**Next Step**: Configure AWS credentials once SAM CLI is installed
