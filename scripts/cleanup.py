"""
Delete SageMaker Endpoint and Resources
"""
import os
import boto3
from dotenv import load_dotenv

load_dotenv("config/.env")

# Get AWS configuration
AWS_PROFILE = os.getenv("AWS_PROFILE", "default")
AWS_REGION = os.getenv("AWS_REGION", "ap-southeast-1")

# Create boto session with profile
try:
    boto_session = boto3.Session(profile_name=AWS_PROFILE, region_name=AWS_REGION)
    # Test authentication
    sts = boto_session.client('sts')
    identity = sts.get_caller_identity()
    print(f"Authenticated as: {identity['Arn']}\n")
except Exception as e:
    print(f"❌ Authentication failed: {e}")
    print(f"\n💡 To fix this, run: aws sso login --profile {AWS_PROFILE}")
    exit(1)

# Load endpoint name
if os.path.exists("../build/endpoint_info.txt"):
    with open("../build/endpoint_info.txt") as f:
        for line in f:
            if line.startswith("ENDPOINT_NAME="):
                endpoint_name = line.strip().split("=", 1)[1]
                break
else:
    endpoint_name = input("Enter endpoint name to delete: ")

print(f"🗑️  Deleting endpoint: {endpoint_name}")
print(f"Region: {AWS_REGION}")
print(f"Profile: {AWS_PROFILE}\n")

# Confirm deletion
response = input(f"Are you sure you want to delete '{endpoint_name}'? (yes/no): ")
if response.lower() not in ['yes', 'y']:
    print("❌ Deletion cancelled.")
    exit(0)

client = boto_session.client("sagemaker")

try:
    # Get endpoint details first
    print("\n🔍 Checking endpoint status...")
    endpoint_desc = client.describe_endpoint(EndpointName=endpoint_name)
    endpoint_config_name = endpoint_desc['EndpointConfigName']
    endpoint_status = endpoint_desc['EndpointStatus']

    print(f"   Status: {endpoint_status}")
    print(f"   Config: {endpoint_config_name}")

    # Get endpoint config details BEFORE deleting it
    print(f"\n🔍 Getting endpoint config details...")
    config_desc = client.describe_endpoint_config(EndpointConfigName=endpoint_config_name)
    model_names = [variant['ModelName'] for variant in config_desc.get('ProductionVariants', [])]
    print(f"   Found {len(model_names)} model(s): {', '.join(model_names)}")

    # Delete endpoint
    print(f"\n🗑️  Deleting endpoint...")
    client.delete_endpoint(EndpointName=endpoint_name)
    print(f"✅ Endpoint deletion initiated: {endpoint_name}")
    print("   (Deletion in progress, may take a few minutes)")

    # Delete endpoint config
    print(f"\n🗑️  Deleting endpoint config...")
    try:
        client.delete_endpoint_config(EndpointConfigName=endpoint_config_name)
        print(f"✅ Deleted endpoint config: {endpoint_config_name}")
    except Exception as e:
        print(f"⚠️  Could not delete endpoint config: {e}")
        print("   (It may be in use or already deleted)")

    # Delete associated models (using the info we got earlier)
    print(f"\n🗑️  Deleting associated models...")
    for model_name in model_names:
        try:
            client.delete_model(ModelName=model_name)
            print(f"✅ Deleted model: {model_name}")
        except Exception as e:
            print(f"⚠️  Could not delete model {model_name}: {e}")

    # Clean up local files
    print(f"\n🧹 Cleaning up local files...")
    if os.path.exists("../build/endpoint_info.txt"):
        os.remove("../build/endpoint_info.txt")
        print("✅ Removed endpoint_info.txt")

    if os.path.exists("../build/model.tar.gz"):
        os.remove("../build/model.tar.gz")
        print("✅ Removed model.tar.gz")

    if os.path.exists("model"):
        import shutil
        shutil.rmtree("model")
        print("✅ Removed model/ directory")

    print("\n" + "=" * 60)
    print("✅ Cleanup complete!")
    print("=" * 60)
    print("\n💡 Note: Endpoint deletion is asynchronous.")
    print("   Check status with:")
    print(f"   aws sagemaker describe-endpoint --endpoint-name {endpoint_name} --profile {AWS_PROFILE}")

except client.exceptions.ClientError as e:
    error_code = e.response['Error']['Code']
    if 'Could not find endpoint' in str(e):
        print(f"⚠️  Endpoint '{endpoint_name}' not found. It may already be deleted.")

        # Still clean up local files
        if os.path.exists("../build/endpoint_info.txt"):
            os.remove("../build/endpoint_info.txt")
            print("✅ Removed endpoint_info.txt")
    else:
        print(f"❌ Error: {e}")

except Exception as e:
    print(f"❌ Error: {e}")
    print("\nTroubleshooting:")
    print(f"1. Check if endpoint exists: aws sagemaker list-endpoints --profile {AWS_PROFILE}")
    print(f"2. Verify authentication: aws sts get-caller-identity --profile {AWS_PROFILE}")
    print(f"3. Check region is correct: {AWS_REGION}")
