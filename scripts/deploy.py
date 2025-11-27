"""
SageMaker Endpoint Deployment Script for MedGemma
Loads configuration from .env file
"""
import os
import tarfile
import shutil
import boto3
from sagemaker.session import Session
from sagemaker.model import Model
from sagemaker.predictor import Predictor
from dotenv import load_dotenv

# Load environment variables
load_dotenv("config/.env")

# Configuration from .env
HF_TOKEN = os.getenv("HF_TOKEN")
MODEL_ID = os.getenv("MODEL_ID", "google/medgemma-4b-it")
INSTANCE_TYPE = os.getenv("INSTANCE_TYPE", "ml.g5.2xlarge")
INSTANCE_COUNT = int(os.getenv("INSTANCE_COUNT", "1"))
ENDPOINT_NAME = os.getenv("ENDPOINT_NAME")
S3_BUCKET = os.getenv("S3_BUCKET")
S3_PREFIX = os.getenv("S3_PREFIX", "medgemma4-text-endpoint")
AWS_REGION = os.getenv("AWS_REGION", "ap-southeast-1")
AWS_PROFILE = os.getenv("AWS_PROFILE", "default")
SAGEMAKER_ROLE = os.getenv("SAGEMAKER_ROLE")
ENABLE_TGI_STREAMING = False  # legacy deploy: always use custom handler for text+image

# Validate required variables
if not HF_TOKEN:
    raise ValueError("HF_TOKEN not found in .env file")

if not SAGEMAKER_ROLE:
    raise ValueError(
        "SAGEMAKER_ROLE not found in .env file. Please specify the full ARN of the SageMaker execution role.")

print("=" * 60)
print("MedGemma SageMaker Deployment Configuration")
print("=" * 60)
print(f"Model ID: {MODEL_ID}")
print(f"Instance Type: {INSTANCE_TYPE}")
print(f"Instance Count: {INSTANCE_COUNT}")
print(f"Endpoint Name: {ENDPOINT_NAME or 'Auto-generated'}")
print(f"S3 Bucket: {S3_BUCKET or 'Default SageMaker bucket'}")
print(f"S3 Prefix: {S3_PREFIX}")
print(f"AWS Region: {AWS_REGION}")
print(f"AWS Profile: {AWS_PROFILE}")
print(f"SageMaker Role: {SAGEMAKER_ROLE}")
print("=" * 60)

# Initialize boto3 session with profile
try:
    boto_session = boto3.Session(profile_name=AWS_PROFILE, region_name=AWS_REGION)
    # Test authentication
    sts = boto_session.client('sts')
    identity = sts.get_caller_identity()
    print(f"\nAuthenticated as: {identity['Arn']}")
except Exception as e:
    print(f"\n❌ Authentication failed: {e}")
    print(f"\n💡 To fix this, run: aws sso login --profile {AWS_PROFILE}")
    exit(1)

# Initialize SageMaker session with boto session
sess = Session(boto_session=boto_session)
bucket = S3_BUCKET or sess.default_bucket()

# Use the role from .env (not auto-detect)
role = SAGEMAKER_ROLE

print(f"Using S3 Bucket: {bucket}")
print(f"Using IAM Role: {role}")

# Verify the role exists
print("\n🔍 Verifying SageMaker execution role...")
iam_client = boto_session.client('iam')
role_name = role.split('/')[-1]

try:
    iam_client.get_role(RoleName=role_name)
    print(f"✅ Role verified: {role_name}")
except Exception as e:
    print(f"❌ Role not found: {role_name}")
    print(f"Error: {e}")
    print("\n💡 To create the role, run: bash setup/setup_aws.sh")
    exit(1)

# Clean previous build
print("\n🧹 Cleaning previous build...")
if os.path.exists("model"):
    shutil.rmtree("model")
if os.path.exists("build/model.tar.gz"):
    os.remove("build/model.tar.gz")

# Create model directory structure
print("📦 Packaging model artifacts...")
os.makedirs("model/code", exist_ok=True)

# Copy files
shutil.copy("src/inference.py", "model/code/inference.py")
shutil.copy("config/requirements.txt", "model/code/requirements.txt")

# Create tar.gz
os.makedirs("build", exist_ok=True)
model_tar_path = "build/model.tar.gz"
with tarfile.open(model_tar_path, "w:gz") as tar:
    tar.add("model", arcname=".")

print(f"✅ Created {model_tar_path}")

# Upload to S3
print(f"\n☁️  Uploading to S3...")
s3 = boto_session.client("s3")
model_s3_key = f"{S3_PREFIX}/model.tar.gz"
s3.upload_file(model_tar_path, bucket, model_s3_key)

model_data = f"s3://{bucket}/{model_s3_key}"
print(f"✅ Uploaded to: {model_data}")

# Get appropriate PyTorch inference image
region = sess.boto_region_name
image_uri = f"763104351884.dkr.ecr.{region}.amazonaws.com/pytorch-inference:2.6.0-gpu-py312-cu124-ubuntu22.04-sagemaker"

print(f"\n🐳 Using Docker image: {image_uri}")
print("\n🔨 Creating SageMaker Model...")
model = Model(
    model_data=model_data,
    image_uri=image_uri,
    role=role,
    sagemaker_session=sess,
    predictor_cls=Predictor,
    env={
        "HF_MODEL_ID": MODEL_ID,
        "HF_TOKEN": HF_TOKEN,
    },
)

# Deploy endpoint
print(f"\n🚀 Deploying endpoint...")
print(f"   Instance Type: {INSTANCE_TYPE}")
print(f"   Instance Count: {INSTANCE_COUNT}")
print("   This may take 5-10 minutes...")

deploy_kwargs = {
    "initial_instance_count": INSTANCE_COUNT,
    "instance_type": INSTANCE_TYPE,
}

if ENDPOINT_NAME:
    deploy_kwargs["endpoint_name"] = ENDPOINT_NAME

try:
    predictor = model.deploy(**deploy_kwargs)

    print("\n" + "=" * 60)
    print("✅ DEPLOYMENT SUCCESSFUL!")
    print("=" * 60)
    endpoint_name = predictor.endpoint_name if predictor else model.endpoint_name
    print(f"Endpoint Name: {endpoint_name}")
    print("=" * 60)

    # Save endpoint name to file
    with open("build/endpoint_info.txt", "w") as f:
        f.write(f"ENDPOINT_NAME={endpoint_name}\n")
        f.write(f"MODEL_DATA={model_data}\n")
        f.write(f"INSTANCE_TYPE={INSTANCE_TYPE}\n")
        f.write(f"REGION={region}\n")
        f.write(f"ROLE={role}\n")

    print("\n📝 Endpoint info saved to: build/endpoint_info.txt")
    print("\n💡 Test your endpoint with: python tests/test_endpoint.py")


except Exception as e:
    print(f"\n❌ Deployment failed: {e}")
    print("\nTroubleshooting:")
    print("1. Verify role exists and has correct permissions")
    print("2. Check S3 bucket is accessible")
    print("3. Ensure you're in the correct AWS region")
    exit(1)
