# Simple Deployment Guide

A step-by-step walkthrough for absolute beginners.

## Before You Start

### What is this?

This tutorial deploys **MedGemma**, an AI model that can:
- Answer medical questions
- Analyze medical images
- Provide healthcare insights

### What you'll need (20 minutes total)

- AWS account
- Python installed on your computer
- Basic command line knowledge
- Credit card (for AWS verification)

### How much does it cost?

- **Deployment**: Free (uses AWS free tier where possible)
- **Running**: ~$1.50/hour (~$36/day if left running)
- **Storage**: ~$0.01/month

**Don't worry!** We'll show you how to stop it when you're done.

---

## Part 1: Get Your Accounts Ready

### 1.1 AWS Account

1. Go to [aws.amazon.com](https://aws.amazon.com)
2. Click "Create an AWS Account"
3. Follow the signup process
4. Verify your email and phone
5. Add a credit card (required, but you won't be charged unless you exceed free tier)

### 1.2 HuggingFace Account

1. Go to [huggingface.co](https://huggingface.co/join)
2. Sign up with email
3. Verify your email
4. Go to Settings → Access Tokens
5. Create a new token (name it "medgemma")
6. Copy the token (starts with `hf_`)

### 1.3 Request Model Access

1. Go to [google/medgemma-4b-it](https://huggingface.co/google/medgemma-4b-it)
2. Click "Request Access" button
3. Fill out the form
4. Wait for approval (usually instant)

---

## Part 2: Install Software

### 2.1 Install Python

**Mac:**
```bash
# Check if Python is installed
python3 --version

# If not, install with Homebrew
brew install python@3.12
```

**Windows:**
1. Download from [python.org](https://www.python.org/downloads/)
2. Run installer
3. ✅ Check "Add Python to PATH"

**Linux:**
```bash
sudo apt update
sudo apt install python3.12
```

### 2.2 Install AWS CLI

**Mac:**
```bash
brew install awscli
```

**Windows:**
1. Download installer from [AWS CLI](https://aws.amazon.com/cli/)
2. Run installer

**Linux:**
```bash
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
```

Verify installation:
```bash
aws --version
# Should show: aws-cli/2.x.x...
```

---

## Part 3: Configure AWS

### 3.1 Configure AWS CLI

```bash
aws configure
```

Enter when prompted:
```
AWS Access Key ID: [Get from AWS Console → Security Credentials]
AWS Secret Access Key: [Get from AWS Console → Security Credentials]
Default region name: us-east-1
Default output format: json
```

**To get AWS keys:**
1. Login to AWS Console
2. Click your name (top right) → Security Credentials
3. Scroll to "Access keys"
4. Click "Create access key"
5. Copy both keys

### 3.2 Test AWS Connection

```bash
aws sts get-caller-identity
```

Should show your AWS account info.

---

## Part 4: Setup the Project

### 4.1 Download Project

```bash
# Navigate to where you want the project
cd ~/Documents  # or wherever you like

# If you have git:
git clone <repository-url>

# Or download and unzip the project
```

### 4.2 Navigate to Project

```bash
cd medgemma-sagemaker-production-deployment
```

### 4.3 Create Virtual Environment

```bash
# Create it
python3 -m venv venv

# Activate it (Mac/Linux)
source venv/bin/activate

# Activate it (Windows)
venv\Scripts\activate

# Your prompt should now show (venv)
```

### 4.4 Install Python Packages

```bash
pip install -r config/requirements.txt
```

Wait for installation (~2 minutes).

---

## Part 5: Configure the Project

### 5.1 Create Configuration File

```bash
cp config/.env.example config/.env
```

### 5.2 Edit Configuration

Open `config/.env` in a text editor:

```bash
# Mac
open -a TextEdit config/.env

# Windows
notepad config/.env

# Linux
nano config/.env
```

Fill in these values:

```bash
# AWS settings
AWS_PROFILE=default
AWS_REGION=us-east-1

# HuggingFace (from Part 1.2)
HF_TOKEN=hf_xxxYourTokenHerexxx

# AWS resources (make it unique with your name!)
S3_BUCKET=medgemma-deployment-johnsmith
SAGEMAKER_ROLE=                    # Leave empty for now
```

Save and close the file.

### 5.3 Create AWS Resources

```bash
bash setup/setup_aws.sh
```

This creates:
- S3 bucket for storing model
- IAM role for SageMaker

**Copy the IAM role ARN** from the output:
```
SAGEMAKER_ROLE=arn:aws:iam::123456789012:role/MedGemmaSageMakerRole
```

Paste it into your `config/.env` file.

---

## Part 6: Test Your Setup

### 6.1 Run Connection Tests

```bash
python setup/test_aws_connections.py
```

You should see:
```
✅ AWS Authentication: Successful
✅ IAM Role Access: Verified
✅ S3 Bucket Access: Confirmed
✅ SageMaker API: Available
✅ HuggingFace Token: Valid
```

### 6.2 Fix Any Errors

If you see ❌ red X's:

**AWS Authentication Failed:**
- Run `aws configure` again
- Check your access keys

**IAM Role Error:**
- Make sure you copied the full role ARN to `.env`
- Check there are no extra spaces

**S3 Bucket Error:**
- Make sure bucket name is unique
- Try a different region in `.env`

**HuggingFace Token Error:**
- Check you copied the full token
- Verify you were granted access to medgemma-4b-it

---

## Part 7: Deploy!

### 7.1 Start Deployment

```bash
python scripts/deploy.py
```

### 7.2 What Happens Next

1. **Packaging** (~30 seconds)
   - Preparing model files

2. **Uploading** (~10 seconds)
   - Sending to AWS S3

3. **Creating Model** (~30 seconds)
   - Registering with SageMaker

4. **Deploying Endpoint** (~8 minutes) ⏰
   - Starting GPU server
   - Loading AI model
   - This is the longest step - go get coffee!

### 7.3 Success!

You should see:
```
✅ Deployment Complete!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Endpoint Name: medgemma-endpoint-20251110-143022
Status: InService
💰 Billing started at ~$1.50/hour
```

**The endpoint is now live!** You're paying ~$1.50/hour from this point.

---

## Part 8: Test Your AI Model

### 8.1 Basic Test

```bash
python tests/test_endpoint.py
```

You should see the AI answer a medical question!

### 8.2 Test with Medical Image

```bash
python tests/test_with_image.py
```

This analyzes a chest X-ray.

### 8.3 Try Your Own Question

Edit `scripts/test_endpoint.py` and change the question, then run it again!

---

## Part 9: Stop Billing! (Important!)

When you're done testing:

```bash
python scripts/cleanup.py
```

This will:
1. ✅ Delete the SageMaker endpoint (stops billing)
2. ✅ Remove configurations
3. ✅ Clean up local files

**The S3 bucket remains** (costs ~$0.01/month). To delete it:
```bash
aws s3 rb s3://your-bucket-name --force
```

### Verify Deletion

Check in AWS Console:
1. Go to [SageMaker Console](https://console.aws.amazon.com/sagemaker)
2. Click "Endpoints" in left menu
3. Should be empty or show "Deleting"

---

## Part 10: Next Steps

Congratulations! 🎉 You just deployed an AI model to the cloud!

### What you learned:

- ✅ AWS basics (IAM, S3, SageMaker)
- ✅ Python environments
- ✅ AI model deployment
- ✅ Cloud cost management

### Learn more:

1. Try different medical questions
2. Upload your own medical images
3. Read about [SageMaker](https://aws.amazon.com/sagemaker/)
4. Explore [MedGemma capabilities](https://huggingface.co/google/medgemma-4b-it)

---

## Troubleshooting

### "Command not found" errors

Make sure your virtual environment is activated:
```bash
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows
```

### Deployment takes too long

It should take ~8 minutes. If it's been >15 minutes:
1. Check AWS console for errors
2. Run `python scripts/check_logs.py`

### "ResourceLimitExceeded" error

AWS limits GPU instances by default:
1. Go to [Service Quotas Console](https://console.aws.amazon.com/servicequotas/)
2. Search "SageMaker ml.g5.2xlarge"
3. Request increase to 1

### Costs are adding up

Delete the endpoint immediately:
```bash
python scripts/cleanup.py
```

### Still stuck?

- Check `python scripts/check_logs.py`
- Review error messages carefully
- Ask for help (open an issue)

---

**Remember**: Always run `cleanup.py` when done to avoid charges! 💰
