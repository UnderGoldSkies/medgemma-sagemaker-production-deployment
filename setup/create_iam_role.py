#!/usr/bin/env python3
"""
Create IAM role for SageMaker execution with required permissions.
"""

import json
import boto3
import os
import sys
from dotenv import load_dotenv

# Load from config directory
load_dotenv("../config/.env")

def create_sagemaker_role(role_name: str = "MedGemmaSageMakerRole"):
    """Create IAM role for SageMaker with necessary permissions."""

    iam = boto3.client('iam', region_name=os.getenv('AWS_REGION'))

    # Trust policy for SageMaker
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "sagemaker.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }

    print(f"🔐 Creating IAM role: {role_name}")

    try:
        # Create role
        response = iam.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description="Execution role for MedGemma SageMaker endpoint"
        )

        role_arn = response['Role']['Arn']
        print(f"✅ Role created: {role_arn}")

        # Attach policies
        policies = [
            "arn:aws:iam::aws:policy/AmazonSageMakerFullAccess",
            "arn:aws:iam::aws:policy/AmazonS3FullAccess",
            "arn:aws:iam::aws:policy/CloudWatchLogsFullAccess",
            "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
        ]

        for policy_arn in policies:
            iam.attach_role_policy(
                RoleName=role_name,
                PolicyArn=policy_arn
            )
            print(f"✅ Attached policy: {policy_arn.split('/')[-1]}")

        print(f"\n✅ Setup complete!")
        print(f"\n📝 Add this to your config/.env file:")
        print(f"SAGEMAKER_ROLE={role_arn}")

        return role_arn

    except iam.exceptions.EntityAlreadyExistsException:
        print(f"⚠️  Role {role_name} already exists")
        role = iam.get_role(RoleName=role_name)
        role_arn = role['Role']['Arn']
        print(f"Using existing role: {role_arn}")
        return role_arn

    except Exception as e:
        print(f"❌ Error creating role: {e}")
        return None

if __name__ == "__main__":
    role_name = sys.argv[1] if len(sys.argv) > 1 else "MedGemmaSageMakerRole"
    create_sagemaker_role(role_name)
