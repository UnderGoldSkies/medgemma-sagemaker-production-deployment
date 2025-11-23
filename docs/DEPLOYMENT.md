# MedGemma SageMaker Endpoint Deployment

A production-ready deployment system for Google's MedGemma medical AI model on AWS SageMaker. This enables scalable, GPU-accelerated inference for medical image analysis and text generation.

## 📋 Table of Contents

- [Architecture Overview](#architecture-overview)
- [Prerequisites](#prerequisites)
- [Setup Instructions](#setup-instructions)
- [Deployment Guide](#deployment-guide)
- [Testing](#testing)
- [Usage](#usage)
- [Monitoring](#monitoring)
- [Cleanup](#cleanup)
- [Troubleshooting](#troubleshooting)
- [Cost Estimation](#cost-estimation)

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                       AWS Account                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐        ┌──────────────────────────────┐    │
│  │   S3 Bucket │◄───────│  model.tar.gz                │    │
│  │             │        │ (inference.py + requirements)│    │
│  └─────────────┘        └──────────────────────────────┘    │
│         ▲                                                   │
│         │                                                   │
│  ┌──────┴──────────────────────────────────────────────┐    │
│  │         SageMaker Endpoint                          │    │
│  │  ┌────────────────────────────────────────────┐     │    │
│  │  │  ml.g5.2xlarge Instance (GPU)              │     │    │
│  │  │  ┌──────────────────────────────────────┐  │     │    │
│  │  │  │ PyTorch Container                    │  │     │    │
│  │  │  │ - Loads model from S3                │  │     │    │
│  │  │  │ - MedGemma in GPU memory             │  │     │    │
│  │  │  │ - REST API on port 8080              │  │     │    │
│  │  │  └──────────────────────────────────────┘  │     │    │
│  │  └────────────────────────────────────────────┘     │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  CloudWatch Logs & Metrics                          │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### Key Components

- **S3**: Stores model artifacts (`model.tar.gz`)
- **SageMaker Endpoint**: Hosts the MedGemma model on GPU instances
- **PyTorch Container**: AWS-managed Docker image with PyTorch 2.6.0
- **CloudWatch**: Logs and metrics for monitoring
- **IAM Role**: Manages permissions for SageMaker execution

## ✅ Prerequisites

### AWS Requirements

1. **AWS Account** with programmatic access
2. **AWS CLI** installed and configured with SSO
3. **IAM Role** with the following permissions:
   - `AmazonSageMakerFullAccess`
   - `AmazonS3FullAccess` (or specific bucket access)
   - `CloudWatchLogsFullAccess`
   - `AmazonEC2ContainerRegistryReadOnly`

4. **S3 Bucket** in your target region

### Local Requirements

- **Python 3.12+**
- **HuggingFace Account** with access to `google/medgemma-4b-it`
- **macOS** (or Linux/Windows with appropriate modifications)

## 🚀 Setup Instructions

### 1. Clone and Navigate to Repository

```bash
cd /path/to/your/project/medgemma-api-endpoint-deployment
```

### 2. Set Python Version

```bash
# Ensure Python 3.12 is active
pyenv local 3.12
# or
python3 --version  # Should be 3.12+
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

**Key packages:**
- `boto3` - AWS SDK
- `sagemaker` - SageMaker Python SDK
- `transformers` - HuggingFace models
- `torch` - PyTorch
- `Pillow` - Image processing

### 4. Configure AWS SSO

```bash
# Login to AWS SSO
aws sso login --profile your-profile-name

# Verify credentials
aws sts get-caller-identity --profile your-profile-name
```

### 5. Create and Configure `.env` File

```bash
cp .env.example .env  # If example exists, or create new
```

Edit `.env` with your configuration:

```bash
# AWS Configuration
AWS_PROFILE=your-profile-name
AWS_REGION=your-aws-region

# HuggingFace Configuration
HF_TOKEN=hf_YourHuggingFaceTokenHere
MODEL_ID=google/medgemma-4b-it

# SageMaker Configuration
INSTANCE_TYPE=ml.g5.2xlarge
INSTANCE_COUNT=1
S3_BUCKET=your-s3-bucket-name
SAGEMAKER_ROLE=arn:aws:iam::123456789012:role/YourSageMakerExecutionRole

# Optional: Custom endpoint name
# ENDPOINT_NAME=medgemma-endpoint-$(date +%Y%m%d-%H%M%S)
```

### 6. Get HuggingFace Token

1. Go to [HuggingFace Settings](https://huggingface.co/settings/tokens)
2. Create a new token with `read` access
3. Request access to `google/medgemma-4b-it` model
4. Add token to `.env` file

### 7. Create or Verify IAM Role

You can use an existing SageMaker role or create a new one:

```bash
# Create a new role using the trust policy
aws iam create-role \
  --role-name YourSageMakerExecutionRole \
  --assume-role-policy-document file://trust-policy.json

# Attach required policies
aws iam attach-role-policy \
  --role-name YourSageMakerExecutionRole \
  --policy-arn arn:aws:iam::aws:policy/AmazonSageMakerFullAccess

# Get the role ARN and add to .env
aws iam get-role --role-name YourSageMakerExecutionRole --query 'Role.Arn' --output text
```

### 8. Verify AWS Connections

Before deploying, run the connection test:

```bash
python test_aws_connections.py
```

This will validate:
- ✅ AWS authentication
- ✅ IAM role access
- ✅ S3 bucket permissions
- ✅ SageMaker API access
- ✅ ECR image availability
- ✅ CloudWatch Logs access

**Expected output:**
```
✅ AWS Authentication: Successful
✅ IAM Role Access: Verified
✅ S3 Bucket Access: Confirmed
✅ SageMaker API: Available
✅ ECR Image: Accessible
✅ CloudWatch Logs: Writable
```

## 🚢 Deployment Guide

### Step 1: Deploy the Endpoint

```bash
python deploy.py
```

**What happens during deployment:**

1. **Package Model** (~30 seconds)
   - Creates `model/` directory structure
   - Copies `inference.py` and `requirements.txt`
   - Creates `model.tar.gz` archive

2. **Upload to S3** (~10 seconds)
   - Uploads model artifact to S3 bucket
   - Displays S3 URI

3. **Create SageMaker Model** (~20 seconds)
   - Registers model with SageMaker
   - Links to PyTorch container image

4. **Deploy Endpoint** (~5-8 minutes)
   - Provisions `ml.g5.2xlarge` GPU instance
   - Downloads model from S3
   - Loads MedGemma into GPU memory
   - Starts inference server

**Expected output:**
```
🚀 Starting MedGemma SageMaker Deployment
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📦 Step 1: Packaging model artifacts...
   ✓ Model directory created
   ✓ Files copied
   ✓ Archive created: model.tar.gz (45.2 MB)

📤 Step 2: Uploading to S3...
   ✓ Uploaded to: s3://your-bucket/medgemma/model.tar.gz

🎯 Step 3: Creating SageMaker model...
   ✓ Model created: medgemma-model-20251110-143022

🚀 Step 4: Deploying endpoint...
   Instance: ml.g5.2xlarge
   Status: Creating...
   ⏳ This will take 5-8 minutes...

   [Progress bar shows deployment status]

✅ Deployment Complete!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Endpoint Name: medgemma-endpoint-20251110-143022
Endpoint URL: runtime.sagemaker.your-region.amazonaws.com/endpoints/medgemma-endpoint-20251110-143022
Status: InService

💰 Billing started at ~$1.50/hour
```

### Step 2: Verify Deployment Status

```bash
# Check endpoint status
aws sagemaker describe-endpoint \
  --endpoint-name $(cat endpoint_info.txt) \
  --profile your-profile-name
```

Or use the AWS Console:
1. Go to [SageMaker Console](https://console.aws.amazon.com/sagemaker)
2. Navigate to **Inference → Endpoints**
3. Find your endpoint and verify status is **InService**

## 🧪 Testing

### Test 1: Text-Only Inference

```bash
python test_endpoint.py
```

**Example request:**
```python
{
    "inputs": "What are the common symptoms of pneumonia?",
    "parameters": {
        "max_new_tokens": 256,
        "temperature": 0.7
    }
}
```

### Test 2: Medical Image Analysis

```bash
python test_with_image.py
```

**Example with chest X-ray:**
```python
{
    "inputs": "Analyze this chest X-ray and identify any abnormalities.",
    "image": "<base64_encoded_image>",
    "parameters": {
        "max_new_tokens": 512
    }
}
```

### Test 3: Custom Medical Images

Place your medical images in `test_images/` and modify `test_with_image.py`:

```python
image_path = "test_images/your_image.png"
```

### Expected Test Results

**Successful response:**
```json
{
    "generated_text": "The chest X-ray shows clear lung fields with no visible infiltrates or consolidations. The cardiac silhouette appears normal in size and shape...",
    "inference_time": 2.3
}
```

**Error response:**
```json
{
    "error": "ModelError",
    "message": "Failed to process image: Invalid format"
}
```

## 📊 Monitoring

### Check Logs

```bash
# View recent logs
python check_logs.py

# Tail logs in real-time
python check_logs.py --follow

# View logs for specific time range
python check_logs.py --start-time "2025-11-10 14:00:00" --end-time "2025-11-10 15:00:00"
```

### CloudWatch Console

1. Go to [CloudWatch Console](https://console.aws.amazon.com/cloudwatch)
2. Navigate to **Logs → Log groups**
3. Find `/aws/sagemaker/Endpoints/medgemma-endpoint-*`
4. View inference logs, errors, and performance metrics

### Key Metrics to Monitor

- **Invocation Count**: Number of inference requests
- **Model Latency**: Time to generate response
- **Instance CPU/GPU Usage**: Resource utilization
- **4xx/5xx Errors**: Client/server errors

## 💻 Usage

### Python SDK Usage

```python
import boto3
import json
import base64
from PIL import Image
from io import BytesIO

# Initialize client
sagemaker_runtime = boto3.client(
    'sagemaker-runtime',
    region_name='your-aws-region'
)

# Text-only inference
def invoke_text_only(prompt: str, endpoint_name: str):
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 256,
            "temperature": 0.7
        }
    }

    response = sagemaker_runtime.invoke_endpoint(
        EndpointName=endpoint_name,
        ContentType='application/json',
        Body=json.dumps(payload),
        Accept='application/json'
    )

    result = json.loads(response['Body'].read().decode())
    return result['generated_text']

# Image + text inference
def invoke_with_image(prompt: str, image_path: str, endpoint_name: str):
    # Load and encode image
    with Image.open(image_path) as img:
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode()

    payload = {
        "inputs": prompt,
        "image": img_base64,
        "parameters": {
            "max_new_tokens": 512
        }
    }

    response = sagemaker_runtime.invoke_endpoint(
        EndpointName=endpoint_name,
        ContentType='application/json',
        Body=json.dumps(payload),
        Accept='application/json'
    )

    result = json.loads(response['Body'].read().decode())
    return result['generated_text']

# Example usage
endpoint_name = 'your-endpoint-name'
response = invoke_text_only("What are the symptoms of diabetes?", endpoint_name)
print(response)

image_response = invoke_with_image(
    "Analyze this chest X-ray",
    "test_images/chest_xray.png",
    endpoint_name
)
print(image_response)
```

### REST API Usage (cURL)

```bash
# Get AWS credentials
AWS_ACCESS_KEY_ID=$(aws configure get aws_access_key_id --profile your-profile-name)
AWS_SECRET_ACCESS_KEY=$(aws configure get aws_secret_access_key --profile your-profile-name)
AWS_SESSION_TOKEN=$(aws configure get aws_session_token --profile your-profile-name)

# Invoke endpoint (requires AWS SigV4 signing)
# Use AWS SDK or tools like awscurl for proper authentication
```

### Integration with Backend API

See the `medical-ai-medgemma/backend` project for FastAPI integration example.

## 🧹 Cleanup

### Delete Endpoint and Resources

```bash
python cleanup.py
```

**What gets deleted:**
1. SageMaker Endpoint (stops billing)
2. Endpoint Configuration
3. Model resource
4. S3 Bucket and IAM Roles
5. Local files (`model.tar.gz`, `endpoint_info.txt`)


### Manual Cleanup (if script fails)

```bash
# 1. Delete endpoint (stops billing)
aws sagemaker delete-endpoint \
  --endpoint-name your-endpoint-name \
  --profile your-profile-name

# 2. Delete endpoint config
aws sagemaker delete-endpoint-config \
  --endpoint-config-name your-endpoint-config-name \
  --profile your-profile-name

# 3. Delete model
aws sagemaker delete-model \
  --model-name your-model-name \
  --profile your-profile-name

# 4. Delete S3 bucket contents and bucket
# ⚠️ This deletes ALL files in the bucket!
aws s3 rm s3://your-bucket-name --recursive --profile your-profile-name
aws s3 rb s3://your-bucket-name --profile your-profile-name

# 5. Detach IAM policies from role
aws iam detach-role-policy \
  --role-name MedGemmaSageMakerRole \
  --policy-arn arn:aws:iam::aws:policy/AmazonSageMakerFullAccess \
  --profile your-profile-name

aws iam detach-role-policy \
  --role-name MedGemmaSageMakerRole \
  --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess \
  --profile your-profile-name

# 6. Delete IAM role
aws iam delete-role \
  --role-name MedGemmaSageMakerRole \
  --profile your-profile-name

# 7. Verify all resources deleted
echo "Checking remaining endpoints..."
aws sagemaker list-endpoints \
  --query 'Endpoints[].EndpointName' \
  --output table \
  --profile your-profile-name

echo "Checking S3 buckets..."
aws s3 ls --profile your-profile-name | grep medgemma

echo "Checking IAM roles..."
aws iam get-role \
  --role-name MedGemmaSageMakerRole \
  --profile your-profile-name 2>&1 | grep -q "NoSuchEntity" && echo "✅ Role deleted" || echo "⚠️ Role still exists"
```

## 🔧 Troubleshooting

### Issue: Deployment fails with "ResourceLimitExceeded"

**Solution:**
```bash
# Request quota increase for ml.g5.2xlarge instances
# Go to AWS Service Quotas console
# Search for "SageMaker ml.g5.2xlarge for endpoint usage"
# Request increase from 0 to 1
```

### Issue: "UnauthorizedOperation" when accessing S3

**Solution:**
```bash
# Verify IAM role has S3 permissions
aws iam get-role-policy \
  --role-name YourSageMakerExecutionRole \
  --policy-name S3Access

# Add S3 policy if missing
aws iam put-role-policy \
  --role-name YourSageMakerExecutionRole \
  --policy-name S3Access \
  --policy-document file://s3-policy.json
```

### Issue: Model loading fails with "HuggingFaceTokenError"

**Solution:**
```bash
# Verify HF token has access to model
curl -H "Authorization: Bearer $HF_TOKEN" \
  https://huggingface.co/api/models/google/medgemma-4b-it

# Request access to model on HuggingFace website
# Update .env with correct token
```

### Issue: Endpoint returns 5xx errors

**Solution:**
```bash
# Check CloudWatch logs
python check_logs.py --tail 50

# Common causes:
# - Out of GPU memory (try smaller batch size)
# - Invalid input format (check JSON structure)
# - Model loading timeout (increase health check timeout)
```

### Issue: Slow inference times (>10 seconds)

**Solution:**
```bash
# Check instance metrics in CloudWatch
# Consider:
# - Upgrading to ml.g5.4xlarge (more GPU memory)
# - Reducing max_new_tokens parameter
# - Using bfloat16 precision (already default)
# - Implementing request batching
```

### Issue: AWS SSO session expired

**Solution:**
```bash
# Re-authenticate
aws sso login --profile your-profile-name

# Verify credentials
aws sts get-caller-identity --profile your-profile-name
```

## 💰 Cost Estimation

### Hourly Costs (varies by region)

| Resource | Cost | Notes |
|----------|------|-------|
| ml.g5.2xlarge | ~$1.00-$2.00/hour | GPU instance (24GB memory) |
| S3 Storage | ~$0.023/GB/month | Model artifact (~45MB) |
| Data Transfer | $0.09/GB | Inference requests/responses |
| CloudWatch Logs | $0.50/GB | First 5GB free/month |

### Monthly Cost Estimate (24/7 operation)

```
Instance:        $1.50/hour × 730 hours = $1,095/month (example)
S3 Storage:      $0.023 × 0.045 GB      = $0.001/month
Data Transfer:   Variable (depends on usage)
CloudWatch:      Free tier (typically <5GB)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TOTAL:           ~$1,095/month (plus data transfer)
```

### Cost Optimization Tips

1. **Delete endpoint when not in use**
   ```bash
   python cleanup.py  # Stops billing immediately
   ```

2. **Use scheduled scaling** (for predictable workloads)
   ```python
   # Scale down during off-hours
   sagemaker_client.update_endpoint_weights_and_capacities(
       EndpointName=endpoint_name,
       DesiredWeightsAndCapacities=[
           {'VariantName': 'AllTraffic', 'DesiredInstanceCount': 0}
       ]
   )
   ```

3. **Use smaller instance types** (if performance allows)
   - `ml.g5.xlarge`: ~$0.70-$1.50/hour (16GB GPU)
   - Trade-off: Slower inference, less concurrent capacity

4. **Implement request batching** (reduce per-request overhead)

5. **Monitor CloudWatch costs** (set up billing alerts)

## 📁 Project Structure

```
medgemma-api-endpoint-deployment/
├── README.md                           # This file
├── .env                                # Environment configuration
├── .envrc                              # direnv configuration
├── .gitignore                          # Git ignore rules
├── .python-version                     # Python version (3.12)
├── requirements.txt                    # Python dependencies
│
├── deploy.py                           # Main deployment script
├── cleanup.py                          # Resource cleanup
├── inference.py                        # SageMaker inference handler
│
├── test_aws_connections.py             # Pre-deployment validation
├── test_endpoint.py                    # Endpoint testing
├── test_with_image.py                  # Image inference testing
├── check_logs.py                       # CloudWatch log viewer
│
├── trust-policy.json                   # IAM trust policy
├── endpoint_info.txt                   # Deployed endpoint name (generated)
├── model.tar.gz                        # Model artifact (generated)
│
├── model/                              # Model package (generated)
│   └── code/
│       ├── inference.py                # Inference logic
│       └── requirements.txt            # Model dependencies
│
└── test_images/                        # Test medical images
    ├── chest_xray.png
    └── medical_image.png
```

## 🔗 Related Resources

- [AWS SageMaker Documentation](https://docs.aws.amazon.com/sagemaker/)
- [HuggingFace Transformers](https://huggingface.co/docs/transformers)
- [MedGemma Model Card](https://huggingface.co/google/medgemma-4b-it)
- [PyTorch SageMaker Containers](https://github.com/aws/sagemaker-pytorch-inference-toolkit)

## 📝 License

This project is part of the NUH_Projects repository. Check the main repository for license information.

## 🤝 Support

For issues or questions:
1. Check the [Troubleshooting](#troubleshooting) section
2. Review CloudWatch logs: `python check_logs.py`
3. Verify AWS permissions: `python test_aws_connections.py`
4. Contact the project maintainer

## 🎯 Next Steps

After successful deployment:
1. ✅ Test endpoint with sample medical images
2. ✅ Integrate with backend API (see `medical-ai-medgemma` project)
3. ✅ Set up CloudWatch alarms for errors/latency
4. ✅ Implement request caching for common queries
5. ✅ Configure auto-scaling for production workloads
6. ✅ Set up CI/CD pipeline for model updates

---

**Last Updated:** 10 November 2025
**Version:** 1.0.0
**Maintainer:** Project Team
