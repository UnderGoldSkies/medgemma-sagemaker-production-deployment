"""
Complete Cleanup - Delete ALL Resources Created in Tutorial
This removes:
- SageMaker Endpoint (stops $1.52/hour billing)
- Endpoint Configuration
- Model
- Orphaned Models (from failed deployments)
- S3 Bucket and all contents
- IAM Role
- CloudWatch Logs
"""
import os
import sys
import boto3
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).parent.parent
load_dotenv(PROJECT_ROOT / "config/.env")

# Get AWS configuration
AWS_PROFILE = os.getenv("AWS_PROFILE", "default")
AWS_REGION = os.getenv("AWS_REGION", "ap-southeast-1")
S3_BUCKET = os.getenv("S3_BUCKET")
SAGEMAKER_ROLE = os.getenv("SAGEMAKER_ROLE")

# Extract role name from ARN
ROLE_NAME = SAGEMAKER_ROLE.split("/")[-1] if SAGEMAKER_ROLE else None

# Create boto session
boto_session = boto3.Session(profile_name=AWS_PROFILE, region_name=AWS_REGION)
sagemaker_client = boto_session.client('sagemaker')
s3_client = boto_session.client('s3')
iam_client = boto_session.client('iam')
logs_client = boto_session.client('logs')

def get_active_models():
    """Get models that are currently in use by endpoints"""
    active_models = set()

    try:
        # Get all endpoints
        endpoints = sagemaker_client.list_endpoints()['Endpoints']

        for ep in endpoints:
            try:
                # Get endpoint config
                endpoint_desc = sagemaker_client.describe_endpoint(EndpointName=ep['EndpointName'])
                config_name = endpoint_desc['EndpointConfigName']

                # Get model from config
                config_desc = sagemaker_client.describe_endpoint_config(EndpointConfigName=config_name)
                for variant in config_desc['ProductionVariants']:
                    active_models.add(variant['ModelName'])
            except Exception as e:
                print(f"⚠️  Warning checking endpoint {ep['EndpointName']}: {e}")
    except Exception as e:
        print(f"⚠️  Warning listing endpoints: {e}")

    return active_models

def find_orphaned_models():
    """Find models not attached to any endpoint"""
    try:
        # Get all models
        all_models = sagemaker_client.list_models()['Models']

        # Get models in use
        active_models = get_active_models()

        # Find orphaned models
        orphaned = [m for m in all_models if m['ModelName'] not in active_models]

        return orphaned
    except Exception as e:
        print(f"⚠️  Warning finding orphaned models: {e}")
        return []

def display_orphaned_models(orphaned_models):
    """Display orphaned models in a formatted table"""
    if not orphaned_models:
        return

    print("\n" + "="*90)
    print(f"🗑️  Found {len(orphaned_models)} orphaned models from failed deployments:")
    print("="*90)
    print(f"{'Model Name':<65} {'Created':<25}")
    print("-"*90)

    for model in orphaned_models:
        created = model['CreationTime'].strftime('%Y-%m-%d %H:%M:%S')
        print(f"{model['ModelName']:<65} {created:<25}")

    print("="*90)

def cleanup_orphaned_models(orphaned_models):
    """Delete orphaned models"""
    if not orphaned_models:
        return 0

    deleted_count = 0

    print("\n🗑️  Deleting orphaned models...")
    for model in orphaned_models:
        model_name = model['ModelName']
        try:
            sagemaker_client.delete_model(ModelName=model_name)
            print(f"✅ Deleted orphaned model: {model_name}")
            deleted_count += 1
        except Exception as e:
            print(f"❌ Error deleting model {model_name}: {e}")

    return deleted_count

def cleanup_sagemaker_resources(endpoint_name):
    """Delete SageMaker endpoint, config, and associated model"""
    try:
        print(f"\n{'='*60}")
        print(f"🗑️  Deleting SageMaker endpoint: {endpoint_name}")
        print(f"{'='*60}")

        # Get endpoint details
        response = sagemaker_client.describe_endpoint(EndpointName=endpoint_name)
        config_name = response['EndpointConfigName']

        # Delete endpoint
        sagemaker_client.delete_endpoint(EndpointName=endpoint_name)
        print(f"✅ Deleted endpoint: {endpoint_name}")

        # Get config details to find model
        try:
            config = sagemaker_client.describe_endpoint_config(EndpointConfigName=config_name)
            model_name = config['ProductionVariants'][0]['ModelName']
        except Exception as e:
            print(f"⚠️  Could not get model name from config: {e}")
            model_name = None

        # Delete endpoint config
        sagemaker_client.delete_endpoint_config(EndpointConfigName=config_name)
        print(f"✅ Deleted endpoint config: {config_name}")

        # Delete model
        if model_name:
            sagemaker_client.delete_model(ModelName=model_name)
            print(f"✅ Deleted model: {model_name}")

        return True
    except sagemaker_client.exceptions.ResourceNotFound:
        print(f"⚠️  Endpoint '{endpoint_name}' not found - may already be deleted")
        return False
    except Exception as e:
        print(f"❌ Error during SageMaker cleanup: {e}")
        return False

def cleanup_s3_bucket():
    """Delete S3 bucket and all contents"""
    if not S3_BUCKET:
        print("⚠️  No S3 bucket configured. Skipping S3 cleanup.")
        return

    print(f"\n{'='*60}")
    print(f"🗑️  Deleting S3 bucket: {S3_BUCKET}")
    print(f"{'='*60}")

    try:
        # Delete all objects in bucket
        print("Deleting all objects in bucket...")
        paginator = s3_client.get_paginator('list_objects_v2')

        for page in paginator.paginate(Bucket=S3_BUCKET):
            if 'Contents' in page:
                objects = [{'Key': obj['Key']} for obj in page['Contents']]
                s3_client.delete_objects(
                    Bucket=S3_BUCKET,
                    Delete={'Objects': objects}
                )
                print(f"  Deleted {len(objects)} objects")

        # Delete bucket
        s3_client.delete_bucket(Bucket=S3_BUCKET)
        print(f"✅ Deleted S3 bucket: {S3_BUCKET}")

    except s3_client.exceptions.NoSuchBucket:
        print(f"⚠️  Bucket '{S3_BUCKET}' not found - may already be deleted")
    except Exception as e:
        print(f"❌ Error during S3 cleanup: {e}")

def cleanup_iam_role():
    """Delete IAM role"""
    if not ROLE_NAME:
        print("⚠️  No IAM role configured. Skipping IAM cleanup.")
        return

    print(f"\n{'='*60}")
    print(f"🗑️  Deleting IAM role: {ROLE_NAME}")
    print(f"{'='*60}")

    try:
        # Detach all managed policies
        attached_policies = iam_client.list_attached_role_policies(RoleName=ROLE_NAME)
        for policy in attached_policies['AttachedPolicies']:
            iam_client.detach_role_policy(
                RoleName=ROLE_NAME,
                PolicyArn=policy['PolicyArn']
            )
            print(f"  Detached policy: {policy['PolicyName']}")

        # Delete role
        iam_client.delete_role(RoleName=ROLE_NAME)
        print(f"✅ Deleted IAM role: {ROLE_NAME}")

    except iam_client.exceptions.NoSuchEntityException:
        print(f"⚠️  Role '{ROLE_NAME}' not found - may already be deleted")
    except Exception as e:
        print(f"❌ Error during IAM cleanup: {e}")

def cleanup_cloudwatch_logs(endpoint_name):
    """Delete CloudWatch log groups"""
    print(f"\n{'='*60}")
    print(f"🗑️  Deleting CloudWatch logs")
    print(f"{'='*60}")

    try:
        # Get all log groups
        log_groups = logs_client.describe_log_groups()

        deleted_count = 0
        for log_group in log_groups['logGroups']:
            log_group_name = log_group['logGroupName']

            # Delete log groups related to this endpoint or containing "medgemma"
            if endpoint_name.lower() in log_group_name.lower() or 'medgemma' in log_group_name.lower():
                logs_client.delete_log_group(logGroupName=log_group_name)
                print(f"✅ Deleted log group: {log_group_name}")
                deleted_count += 1

        if deleted_count == 0:
            print("  No matching log groups found")

    except Exception as e:
        print(f"❌ Error during CloudWatch cleanup: {e}")

def cleanup_local_files():
    """Delete local build files"""
    print(f"\n{'='*60}")
    print(f"🗑️  Deleting local files")
    print(f"{'='*60}")

    files_to_delete = [
        PROJECT_ROOT / "build/endpoint_info.txt",
        PROJECT_ROOT / "build/model.tar.gz",
    ]

    for file_path in files_to_delete:
        if file_path.exists():
            file_path.unlink()
            print(f"✅ Deleted: {file_path}")

    # Delete model directory if it exists
    model_dir = PROJECT_ROOT / "model"
    if model_dir.exists():
        import shutil
        shutil.rmtree(model_dir)
        print(f"✅ Deleted directory: {model_dir}")

def main():
    """Main cleanup function"""
    print("\n" + "="*60)
    print("🧹 COMPLETE CLEANUP SCRIPT")
    print("="*60)
    print("\nThis will delete:")
    print("  • SageMaker Endpoint (stops billing ~$1.52/hour)")
    print("  • Endpoint Configuration")
    print("  • Model")
    print("  • Orphaned models from failed deployments")
    print("  • S3 Bucket and all contents")
    print("  • IAM Role")
    print("  • CloudWatch Logs")
    print("  • Local build files")
    print("\n⚠️  WARNING: This action cannot be undone!")
    print("="*60)

    # Get endpoint name from build file
    endpoint_name = None
    endpoint_info_path = PROJECT_ROOT / "build/endpoint_info.txt"

    if endpoint_info_path.exists():
        with open(endpoint_info_path) as f:
            for line in f:
                if line.startswith("ENDPOINT_NAME="):
                    endpoint_name = line.strip().split("=", 1)[1]
                    break

    if not endpoint_name:
        print("\n⚠️  No endpoint info found in build/endpoint_info.txt")
        print("Will skip SageMaker endpoint cleanup (may already be deleted)")
    else:
        print(f"\nEndpoint to delete: {endpoint_name}")

    # Check for orphaned models
    print("\n🔍 Checking for orphaned models...")
    orphaned_models = find_orphaned_models()

    if orphaned_models:
        display_orphaned_models(orphaned_models)
        print("\n💡 These models are from failed deployments and are not attached to any endpoint.")
    else:
        print("✅ No orphaned models found")

    # Confirm deletion
    print("\n" + "="*60)
    response = input("Type 'DELETE ALL' to proceed with cleanup: ")

    if response != 'DELETE ALL':
        print("\n❌ Cleanup cancelled")
        sys.exit(0)

    # Ask about orphaned models separately if found
    delete_orphaned = False
    if orphaned_models:
        print("\n" + "="*60)
        orphaned_response = input(f"Delete {len(orphaned_models)} orphaned models? (yes/no): ")
        delete_orphaned = orphaned_response.lower() in ['yes', 'y']

    print("\n🚀 Starting cleanup...")
    print("="*60)

    # Step 1: Cleanup SageMaker endpoint resources
    if endpoint_name:
        cleanup_sagemaker_resources(endpoint_name)

    # Step 2: Cleanup orphaned models
    if delete_orphaned and orphaned_models:
        deleted_count = cleanup_orphaned_models(orphaned_models)
        print(f"\n✅ Deleted {deleted_count} orphaned models")
    elif orphaned_models and not delete_orphaned:
        print(f"\n⏭️  Skipped deleting {len(orphaned_models)} orphaned models")
        print("   Run 'python scripts/cleanup_orphaned_models.py --delete' later to remove them")

    # Step 3: Cleanup S3 bucket
    cleanup_s3_bucket()

    # Step 4: Cleanup IAM role
    cleanup_iam_role()

    # Step 5: Cleanup CloudWatch logs
    if endpoint_name:
        cleanup_cloudwatch_logs(endpoint_name)

    # Step 6: Cleanup local files
    cleanup_local_files()

    # Final summary
    print("\n" + "="*60)
    print("✅ CLEANUP COMPLETE!")
    print("="*60)
    print("\n💰 Cost savings:")
    if endpoint_name:
        print("   • Endpoint billing stopped (~$1.52/hour = $36/day)")
    print("   • S3 storage freed (~$0.05/month)")
    if delete_orphaned and orphaned_models:
        print(f"   • {len(orphaned_models)} orphaned models removed (clutter cleanup)")
    print("\n🎉 All resources have been deleted!")
    print("="*60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Cleanup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
