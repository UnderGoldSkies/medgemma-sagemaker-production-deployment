# 🏥 Deploy MedGemma AI to AWS SageMaker

> A beginner-friendly guide to deploy Google's MedGemma medical AI model on AWS in 4 simple steps.

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![AWS SageMaker](https://img.shields.io/badge/AWS-SageMaker-orange.svg)](https://aws.amazon.com/sagemaker/)

## 📖 What You'll Learn

- ✅ How to set up AWS for AI model deployment
- ✅ How to deploy a medical AI model to the cloud
- ✅ How to test your deployed model
- ✅ How to clean up resources to avoid charges

## ⚡ Quick Overview

This tutorial deploys **MedGemma**, a medical AI model that can:
- Answer medical questions
- Analyze medical images (X-rays, CT scans, etc.)
- Provide clinical insights

**Cost**: ~$1.50/hour while running (you'll learn how to stop it!)

## 📋 What You Need

Before starting, make sure you have:

- [ ] **AWS Account** ([Sign up here](https://aws.amazon.com/free/))
- [ ] **Python 3.12+** installed ([Download here](https://www.python.org/downloads/))
- [ ] **AWS CLI** installed ([Installation guide](https://aws.amazon.com/cli/))
- [ ] **HuggingFace Account** ([Sign up here](https://huggingface.co/join))
- [ ] **Credit card** (for AWS - they offer free tier)

## 🚀 4-Step Tutorial

### Step 1: Setup Your Environment (5 minutes)

#### 1.1 Download the Project

```bash
# Clone or download this project
cd medgemma-sagemaker-production-deployment
```

#### 1.2 Install Python Dependencies

```bash
# Create a virtual environment (keeps things clean)
python3 -m venv venv

# Activate it
source venv/bin/activate  # On Mac/Linux
# OR
venv\Scripts\activate     # On Windows

# Install required packages
pip install -r config/requirements.txt
```

✅ **Success check**: You should see packages installing without errors.

---

### Step 2: Configure AWS (10 minutes)

#### 2.1 Configure AWS CLI

```bash
# Login to AWS
aws configure sso

# Follow the prompts:
# - SSO start URL: Get this from your AWS admin
# - SSO Region: us-east-1 (or your region)
# - CLI default region: us-east-1 (or your region)
```

#### 2.2 Get Your HuggingFace Token

1. Go to [HuggingFace Settings](https://huggingface.co/settings/tokens)
2. Click "New token"
3. Give it a name (e.g., "medgemma-deploy")
4. Select "Read" access
5. Copy the token (starts with `hf_...`)

#### 2.3 Create Your Configuration File

```bash
# Copy the example file
cp config/.env.example config/.env

# Open it in your favorite text editor
nano config/.env  # or use VS Code, TextEdit, Notepad, etc.
```

Fill in these values:
```bash
# Your AWS settings
AWS_PROFILE=default              # Usually "default"
AWS_REGION=us-east-1            # Your preferred AWS region

# Your HuggingFace token (from step 2.2)
HF_TOKEN=hf_YourTokenHere

# AWS resources (we'll create these)
S3_BUCKET=medgemma-deployment-YOUR-NAME  # Make it unique!
SAGEMAKER_ROLE=                 # Leave empty for now
```

#### 2.4 Create AWS Resources

```bash
# Run the setup script
bash setup/setup_aws.sh
```

This will:
- ✅ Check your AWS credentials
- ✅ Create an S3 bucket
- ✅ Create an IAM role for SageMaker

**Copy the IAM role ARN** it shows and add it to your `config/.env` file.

---

### Step 3: Test Your Setup (2 minutes)

Before deploying, let's make sure everything is configured correctly:

```bash
python setup/test_aws_connections.py
```

You should see all green checkmarks ✅:
```
✅ AWS Authentication: Successful
✅ IAM Role Access: Verified
✅ S3 Bucket Access: Confirmed
✅ SageMaker API: Available
✅ HuggingFace Token: Valid
```

❌ **If you see red X's**, check the error messages and fix them before continuing.

---

### Step 4: Deploy! (8 minutes)

Now for the exciting part - deploy your AI model:

```bash
python scripts/deploy.py
```

**What's happening:**
1. 📦 Packaging the model code
2. ☁️ Uploading to AWS S3
3. 🚀 Creating SageMaker endpoint
4. ⏳ Starting GPU server (this takes ~8 minutes)

You'll see a progress bar. Grab a coffee! ☕

**Success looks like this:**
```
✅ Deployment Complete!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Endpoint Name: medgemma-endpoint-20251110-143022
Status: InService
💰 Billing started at ~$1.50/hour

Next steps:
1. Test your endpoint: python tests/test_endpoint.py
2. Try with an image: python tests/test_with_image.py
3. When done: python scripts/cleanup.py
```

---

## 🧪 Test Your Deployment

### Basic Text Test

```bash
python tests/test_endpoint.py
```

Example output:
```
🔮 Testing MedGemma Endpoint
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📝 Question: What are the common symptoms of pneumonia?

✅ Response:
Common symptoms of pneumonia include fever, cough with mucus,
shortness of breath, chest pain when breathing or coughing,
and fatigue...

⏱️  Response time: 2.3 seconds
```

### Medical Image Analysis

```bash
python tests/test_with_image.py
```

This analyzes a chest X-ray image and provides medical insights.

### Try Your Own Queries

```python
# examples/python/simple_text_inference.py
from scripts.test_endpoint import invoke_endpoint

response = invoke_endpoint("Explain what diabetes is in simple terms")
print(response)
```

---

## 💰 Cost Management

### How Much Does This Cost?

- **While Running**: ~$1.50/hour (~$1,100/month if left running 24/7)
- **When Stopped**: $0/hour (just pennies for S3 storage)

### Stop Billing Immediately

```bash
python scripts/cleanup.py
```

This will:
1. Delete the SageMaker endpoint (stops billing)
2. Remove endpoint configuration
3. Clean up local files

**The S3 bucket remains** (costs ~$0.01/month). To delete it:
```bash
aws s3 rb s3://your-bucket-name --force
```

### View Costs

Check your AWS bill:
1. Go to [AWS Billing Console](https://console.aws.amazon.com/billing/)
2. Look for "SageMaker" charges
3. Set up billing alerts (recommended!)

---

## 📊 Monitor Your Deployment

### View Logs

```bash
# See recent activity
python scripts/check_logs.py

# Follow logs in real-time
python scripts/check_logs.py --follow
```

### Check Endpoint Status

```bash
aws sagemaker describe-endpoint \
  --endpoint-name $(cat build/endpoint_info.txt) \
  --query 'EndpointStatus' \
  --output text
```

Should show: `InService`

---

## 🎯 Use Cases

### Medical Q&A
Ask questions about symptoms, conditions, treatments.

### Image Analysis
Upload X-rays, CT scans, MRIs for AI analysis.

### Clinical Decision Support
Get evidence-based insights for patient care.

**⚠️ Important**: This is an AI model. Always validate outputs with qualified healthcare professionals.

---

## 🆘 Troubleshooting

### Problem: `deploy.py` fails with "ResourceLimitExceeded"

**Solution**: AWS limits GPU instances by default.
1. Go to [AWS Service Quotas](https://console.aws.amazon.com/servicequotas/)
2. Search for "SageMaker ml.g5.2xlarge"
3. Request an increase from 0 to 1

### Problem: "InvalidToken" error

**Solution**: Your HuggingFace token is invalid.
1. Check you copied it correctly to `config/.env`
2. Verify you requested access to `google/medgemma-4b-it` on HuggingFace

### Problem: Endpoint returns errors

**Solution**: Check the logs
```bash
python scripts/check_logs.py --tail 50
```

### Problem: AWS credentials expired

**Solution**: Re-authenticate
```bash
aws sso login --profile default
```

### Still Stuck?

1. Check [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for detailed info
2. Review error messages carefully
3. Check AWS CloudWatch logs

---

## 📁 Project Structure

```
medgemma-sagemaker-production-deployment/
│
├── config/                    # Configuration files
│   ├── .env.example          # Template (copy to .env)
│   ├── requirements.txt      # Python packages
│   └── trust-policy.json     # AWS IAM policy
│
├── scripts/                   # Main scripts
│   ├── deploy.py             # Deploy model
│   ├── test_endpoint.py      # Test deployment
│   ├── cleanup.py            # Delete resources
│   └── check_logs.py         # View logs
│
├── setup/                     # Setup helpers
│   ├── setup_aws.sh          # AWS configuration
│   └── test_aws_connections.py  # Validate setup
│
├── src/                       # Model code
│   └── inference.py          # Inference logic
│
├── tests/                     # Test files
│   └── test_images/          # Sample medical images
│
└── examples/                  # Usage examples
    └── python/               # Python examples
```

---

## 🎓 Learn More

### Recommended Reading

- [AWS SageMaker Basics](https://aws.amazon.com/sagemaker/)
- [What is MedGemma?](https://huggingface.co/google/medgemma-4b-it)

### Next Steps

1. ✅ Try different medical questions
2. ✅ Upload your own medical images
3. ✅ Integrate with your application
4. ✅ Learn about model fine-tuning
5. ✅ Explore cost optimization strategies

---

## 📝 License

MIT License - See [LICENSE](LICENSE) file

---

## ⚠️ Medical Disclaimer

This AI model is for educational and research purposes only. It should NOT be used as a substitute for professional medical advice, diagnosis, or treatment. Always consult qualified healthcare providers for medical decisions.

---

## 🌟 Acknowledgments

- **Google Research** for MedGemma model
- **AWS** for SageMaker platform
- **HuggingFace** for model hosting
- **UnderGoldSkies** for learning about medical AI!

---

**Ready to start?** Jump to [Step 1: Setup Your Environment](#step-1-setup-your-environment-5-minutes) ⬆️

**Questions?** Check [Troubleshooting](#-troubleshooting) ⬆️

**Done?** Don't forget to [cleanup](#-cost-management) to avoid charges! ⬆️
