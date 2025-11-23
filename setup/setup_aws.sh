#!/bin/bash

################################################################################
# AWS Setup Helper Script
#
# This script helps beginners set up AWS for MedGemma deployment.
################################################################################

set -e

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  AWS Setup for MedGemma Deployment${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

################################################################################
# STEP 1: Check AWS CLI
################################################################################

echo -e "${YELLOW}Step 1/4: Checking AWS CLI...${NC}"

if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI not found!${NC}"
    echo ""
    echo "Install it from: https://aws.amazon.com/cli/"
    echo ""
    echo "For Mac: brew install awscli"
    echo "For Windows: Download installer from AWS website"
    echo "For Linux: sudo apt-get install awscli"
    exit 1
fi

echo -e "${GREEN}✅ AWS CLI detected: $(aws --version)${NC}"
echo ""

################################################################################
# STEP 2: Check AWS Authentication
################################################################################

echo -e "${YELLOW}Step 2/4: Checking AWS authentication...${NC}"

# Load environment
if [ -f "config/.env" ]; then
    set -a
    source config/.env
    set +a
else
    echo -e "${RED}❌ config/.env not found!${NC}"
    echo ""
    echo "Create it by copying the example:"
    echo "  cp config/.env.example config/.env"
    echo ""
    echo "Then edit it with your settings."
    exit 1
fi

if [ -z "$AWS_PROFILE" ]; then
    echo -e "${RED}❌ AWS_PROFILE not set in config/.env${NC}"
    exit 1
fi

if [ -z "$AWS_REGION" ]; then
    echo -e "${RED}❌ AWS_REGION not set in config/.env${NC}"
    exit 1
fi

# Test authentication
if aws sts get-caller-identity --profile "$AWS_PROFILE" &> /dev/null; then
    echo -e "${GREEN}✅ AWS authentication successful${NC}"

    # Get account info
    ACCOUNT_ID=$(aws sts get-caller-identity --profile "$AWS_PROFILE" --query 'Account' --output text)
    USER_ARN=$(aws sts get-caller-identity --profile "$AWS_PROFILE" --query 'Arn' --output text)

    echo ""
    echo "Authenticated as:"
    echo "  Account: $ACCOUNT_ID"
    echo "  User: $USER_ARN"
    echo ""
    echo -e "${GREEN}Continuing to next step...${NC}"
    echo ""
else
    echo -e "${RED}❌ AWS authentication failed${NC}"
    echo ""
    echo "Run this command to login:"
    echo "  aws sso login --profile $AWS_PROFILE"
    echo ""
    exit 1
fi

################################################################################
# STEP 3: Create S3 Bucket
################################################################################

echo -e "${YELLOW}Step 3/4: Setting up S3 bucket...${NC}"

if [ -z "$S3_BUCKET" ]; then
    echo -e "${RED}❌ S3_BUCKET not set in config/.env${NC}"
    echo ""
    echo "Add this line to config/.env:"
    echo "  S3_BUCKET=medgemma-deployment-YOUR-NAME"
    exit 1
fi

# Check if bucket exists
if aws s3 ls "s3://$S3_BUCKET" --profile "$AWS_PROFILE" 2>/dev/null; then
    echo -e "${GREEN}✅ S3 bucket already exists: $S3_BUCKET${NC}"
else
    echo "Creating S3 bucket: $S3_BUCKET"

    if [ "$AWS_REGION" == "us-east-1" ]; then
        aws s3 mb "s3://$S3_BUCKET" --profile "$AWS_PROFILE"
    else
        aws s3 mb "s3://$S3_BUCKET" --region "$AWS_REGION" --profile "$AWS_PROFILE"
    fi

    echo -e "${GREEN}✅ S3 bucket created: $S3_BUCKET${NC}"
fi

echo ""

################################################################################
# STEP 4: Create IAM Role
################################################################################

echo -e "${YELLOW}Step 4/4: Setting up IAM role...${NC}"

ROLE_NAME="MedGemmaSageMakerRole"

# Check if role exists
if aws iam get-role --role-name "$ROLE_NAME" --profile "$AWS_PROFILE" &>/dev/null; then
    echo -e "${GREEN}✅ IAM role already exists: $ROLE_NAME${NC}"
    ROLE_ARN=$(aws iam get-role --role-name "$ROLE_NAME" --profile "$AWS_PROFILE" --query 'Role.Arn' --output text)
else
    echo "Creating IAM role: $ROLE_NAME"

    # Create role
    aws iam create-role \
        --role-name "$ROLE_NAME" \
        --assume-role-policy-document file://config/trust-policy.json \
        --profile "$AWS_PROFILE" \
        --description "SageMaker execution role for MedGemma deployment" \
        &>/dev/null

    # Attach policies
    aws iam attach-role-policy \
        --role-name "$ROLE_NAME" \
        --policy-arn "arn:aws:iam::aws:policy/AmazonSageMakerFullAccess" \
        --profile "$AWS_PROFILE"

    aws iam attach-role-policy \
        --role-name "$ROLE_NAME" \
        --policy-arn "arn:aws:iam::aws:policy/AmazonS3FullAccess" \
        --profile "$AWS_PROFILE"

    echo -e "${GREEN}✅ IAM role created: $ROLE_NAME${NC}"

    ROLE_ARN=$(aws iam get-role --role-name "$ROLE_NAME" --profile "$AWS_PROFILE" --query 'Role.Arn' --output text)
fi

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ AWS Setup Complete!${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${YELLOW}📝 Add this to your config/.env file:${NC}"
echo ""
echo "SAGEMAKER_ROLE=$ROLE_ARN"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Update config/.env with the IAM role ARN above"
echo "2. Deploy: python scripts/deploy.py"
echo ""
