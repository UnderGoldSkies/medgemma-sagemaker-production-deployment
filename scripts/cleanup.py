"""
Complete Cleanup - Delete ALL Resources Created in Tutorial
This removes:
- SageMaker Endpoint (stops $1.52/hour billing)
- Endpoint Configuration
- Model
- S3 Bucket and all contents
- IAM Role
- CloudWatch Logs
"""
import os
import boto3
from dotenv import load_dotenv

load_dotenv("config/.env")

# Get AWS configuration
AWS_PROFILE = os.getenv("AWS_PROFILE", "default")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
S3_BUCKET = os.getenv("S3_BUCKET")
SAGEMAKER_ROLE = os.getenv("SAGEMAKER_ROLE")

# Extract role name from ARN
if SAGEMAKER_ROLE:
    ROLE_NAME = SAGEMAKER_ROLE.split('/')[-1]
else:
    ROLE_NAME = "MedGemmaSageMakerRole"

print("=" * 70)
print("🗑️  COMPLETE CLEANUP - DELETE ALL RESOURCES")
print("=" * 70)
print("\n⚠️  This will delete:")
print("   - SageMaker Endpoint (stops billing)")
print("   - Endpoint Configuration")
print("   - Model")
print(f"   - S3 Bucket: {S3_BUCKET}")
print(f"   - IAM Role: {ROLE_NAME}")
print("   - CloudWatch Logs")
print("   - Local files")
print("\n⚠️  This action CANNOT be undone!")
print("\n" + "=" * 70)

# Confirm total deletion
response = input("\nType 'DELETE ALL' to proceed: ")
if response != 'DELETE ALL':
    print("❌ Cleanup cancelled.")
    exit(0)

# Create boto session
try:
    boto_session = boto3.Session(profile_name=AWS_PROFILE, region_name=AWS_REGION)
    sts = boto_session.client('sts')
    identity = sts.get_caller_identity()
    print(f"\n✅ Authenticated as: {identity['Arn']}\n")
except Exception as e:
    print(f"❌ Authentication failed: {e}")
    exit(1)

sagemaker_client = boto_session.client("sagemaker")
s3_client = boto_session.client("s3")
iam_client = boto_session.client("iam")
logs_client = boto_session.client("logs")

# ============================================================================
# Step 1: Delete SageMaker Endpoint
# ============================================================================
print("\n" + "=" * 70)
print("STEP 1: Delete SageMaker Endpoint")
print("=" * 70)

endpoint_name = None
if os.path.exists("build/endpoint_info.txt"):
    with open("build/endpoint_info.txt") as f:
        for line in f:
            if line.startswith("ENDPOINT_NAME="):
                endpoint_name = line.strip().split("=", 1)[1]
                break

if endpoint_name:
    try:
        # Get endpoint details
        endpoint_desc = sagemaker_client.describe_endpoint(EndpointName=endpoint_name)
        endpoint_config_name = endpoint_desc['EndpointConfigName']

        # Get model names
        config_desc = sagemaker_client.describe_endpoint_config(EndpointConfigName=endpoint_config_name)
        model_names = [v['ModelName'] for v in config_desc.get('ProductionVariants', [])]

        # Delete endpoint
        print(f"🗑️  Deleting endpoint: {endpoint_name}")
        sagemaker_client.delete_endpoint(EndpointName=endpoint_name)
        print(f"✅ Deleted endpoint: {endpoint_name}")

        # Delete endpoint config
        print(f"🗑️  Deleting endpoint config: {endpoint_config_name}")
        sagemaker_client.delete_endpoint_config(EndpointConfigName=endpoint_config_name)
        print(f"✅ Deleted endpoint config: {endpoint_config_name}")

        # Delete models
        for model_name in model_names:
            print(f"🗑️  Deleting model: {model_name}")
            sagemaker_client.delete_model(ModelName=model_name)
            print(f"✅ Deleted model: {model_name}")

    except sagemaker_client.exceptions.ClientError as e:
        if 'Could not find' in str(e):
            print("ℹ️  No endpoint found (may already be deleted)")
        else:
            print(f"⚠️  Error deleting endpoint: {e}")
else:
    print("ℹ️  No endpoint info found (skipping)")

# ============================================================================
# Step 2: Delete S3 Bucket and Contents
# ============================================================================
print("\n" + "=" * 70)
print("STEP 2: Delete S3 Bucket")
print("=" * 70)

if S3_BUCKET:
    try:
        # Check if bucket exists
        s3_client.head_bucket(Bucket=S3_BUCKET)

        # List and delete all objects
        print(f"🗑️  Deleting all objects in bucket: {S3_BUCKET}")

        # Delete all object versions (if versioning enabled)
        paginator = s3_client.get_paginator('list_object_versions')
        delete_count = 0

        for page in paginator.paginate(Bucket=S3_BUCKET):
            objects_to_delete = []

            # Add versions
            if 'Versions' in page:
                for version in page['Versions']:
                    objects_to_delete.append({
                        'Key': version['Key'],
                        'VersionId': version['VersionId']
                    })

            # Add delete markers
            if 'DeleteMarkers' in page:
                for marker in page['DeleteMarkers']:
                    objects_to_delete.append({
                        'Key': marker['Key'],
                        'VersionId': marker['VersionId']
                    })

            if objects_to_delete:
                s3_client.delete_objects(
                    Bucket=S3_BUCKET,
                    Delete={'Objects': objects_to_delete}
                )
                delete_count += len(objects_to_delete)

        print(f"✅ Deleted {delete_count} object(s)")

        # Delete the bucket
        print(f"🗑️  Deleting bucket: {S3_BUCKET}")
        s3_client.delete_bucket(Bucket=S3_BUCKET)
        print(f"✅ Deleted bucket: {S3_BUCKET}")

    except s3_client.exceptions.NoSuchBucket:
        print(f"ℹ️  Bucket {S3_BUCKET} not found (may already be deleted)")
    except Exception as e:
        print(f"⚠️  Error deleting S3 bucket: {e}")
else:
    print("ℹ️  No S3 bucket specified (skipping)")

# ============================================================================
# Step 3: Delete IAM Role
# ============================================================================
print("\n" + "=" * 70)
print("STEP 3: Delete IAM Role")
print("=" * 70)

try:
    # Detach policies first
    print(f"🗑️  Detaching policies from role: {ROLE_NAME}")

    attached_policies = iam_client.list_attached_role_policies(RoleName=ROLE_NAME)
    for policy in attached_policies['AttachedPolicies']:
        print(f"   Detaching: {policy['PolicyName']}")
        iam_client.detach_role_policy(
            RoleName=ROLE_NAME,
            PolicyArn=policy['PolicyArn']
        )

    # Delete inline policies
    inline_policies = iam_client.list_role_policies(RoleName=ROLE_NAME)
    for policy_name in inline_policies['PolicyNames']:
        print(f"   Deleting inline policy: {policy_name}")
        iam_client.delete_role_policy(
            RoleName=ROLE_NAME,
            PolicyName=policy_name
        )

    # Delete the role
    print(f"🗑️  Deleting IAM role: {ROLE_NAME}")
    iam_client.delete_role(RoleName=ROLE_NAME)
    print(f"✅ Deleted IAM role: {ROLE_NAME}")

except iam_client.exceptions.NoSuchEntityException:
    print(f"ℹ️  Role {ROLE_NAME} not found (may already be deleted)")
except Exception as e:
    print(f"⚠️  Error deleting IAM role: {e}")

# ============================================================================
# Step 4: Delete CloudWatch Logs
# ============================================================================
print("\n" + "=" * 70)
print("STEP 4: Delete CloudWatch Logs")
print("=" * 70)

try:
    # List all log groups related to SageMaker
    log_groups = logs_client.describe_log_groups(
        logGroupNamePrefix='/aws/sagemaker/'
    )

    deleted_count = 0
    for log_group in log_groups['logGroups']:
        log_group_name = log_group['logGroupName']

        # Only delete if it contains our endpoint name or "medgemma"
        if endpoint_name and endpoint_name in log_group_name or 'medgemma' in log_group_name.lower():
            print(f"🗑️  Deleting log group: {log_group_name}")
            logs_client.delete_log_group(logGroupName=log_group_name)
            deleted_count += 1

    if deleted_count > 0:
        print(f"✅ Deleted {deleted_count} log group(s)")
    else:
        print("ℹ️  No relevant log groups found")

except Exception as e:
    print(f"⚠️  Error deleting CloudWatch logs: {e}")

# ============================================================================
# Step 5: Clean Up Local Files
# ============================================================================
print("\n" + "=" * 70)
print("STEP 5: Clean Up Local Files")
print("=" * 70)

local_files = [
    "build/endpoint_info.txt",
    "build/model.tar.gz",
    "model/"
]

for file_path in local_files:
    try:
        if os.path.isfile(file_path):
            os.remove(file_path)
            print(f"✅ Removed: {file_path}")
        elif os.path.isdir(file_path):
            import shutil
            shutil.rmtree(file_path)
            print(f"✅ Removed directory: {file_path}")
    except Exception as e:
        print(f"⚠️  Could not remove {file_path}: {e}")

# ============================================================================
# Step 6: Verify Complete Cleanup
# ============================================================================
print("\n" + "=" * 70)
print("STEP 6: Verify Complete Cleanup")
print("=" * 70)

print("\n🔍 Checking for remaining resources...\n")

# Check endpoints
try:
    endpoints = sagemaker_client.list_endpoints()
    if endpoints['Endpoints']:
        print(f"⚠️  Found {len(endpoints['Endpoints'])} SageMaker endpoint(s):")
        for ep in endpoints['Endpoints']:
            print(f"   - {ep['EndpointName']} ({ep['EndpointStatus']})")
    else:
        print("✅ No SageMaker endpoints found")
except Exception as e:
    print(f"⚠️  Could not check endpoints: {e}")

# Check S3 buckets
if S3_BUCKET:
    try:
        s3_client.head_bucket(Bucket=S3_BUCKET)
        print(f"⚠️  S3 bucket still exists: {S3_BUCKET}")
    except s3_client.exceptions.NoSuchBucket:
        print(f"✅ S3 bucket deleted: {S3_BUCKET}")
    except Exception as e:
        print(f"⚠️  Could not check S3 bucket: {e}")

# Check IAM role
try:
    iam_client.get_role(RoleName=ROLE_NAME)
    print(f"⚠️  IAM role still exists: {ROLE_NAME}")
except iam_client.exceptions.NoSuchEntityException:
    print(f"✅ IAM role deleted: {ROLE_NAME}")
except Exception as e:
    print(f"⚠️  Could not check IAM role: {e}")

# ============================================================================
# Final Summary
# ============================================================================
print("\n" + "=" * 70)
print("✅ COMPLETE CLEANUP FINISHED!")
print("=" * 70)

print("\n📊 Summary:")
print("   ✅ SageMaker resources deleted (billing stopped)")
print("   ✅ S3 bucket and contents removed")
print("   ✅ IAM role deleted")
print("   ✅ CloudWatch logs cleaned up")
print("   ✅ Local files removed")

print("\n💡 To deploy again, you'll need to:")
print("   1. Run: bash setup/setup_aws.sh")
print("   2. Update config/.env with new S3 bucket and IAM role")
print("   3. Run: python scripts/deploy.py")

print("\n" + "=" * 70)
