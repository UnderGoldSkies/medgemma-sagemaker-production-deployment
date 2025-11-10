"""
Comprehensive AWS Connection and Permissions Test
Tests all AWS services used in the MedGemma deployment
"""
import os
import sys
import boto3
import sagemaker
from dotenv import load_dotenv
from botocore.exceptions import ClientError, NoCredentialsError

load_dotenv("../config/.env")

# Configuration
S3_BUCKET = os.getenv("S3_BUCKET")
S3_PREFIX = os.getenv("S3_PREFIX", "medgemma4-text-endpoint")
AWS_REGION = os.getenv("AWS_REGION", "ap-southeast-1")
AWS_PROFILE = os.getenv("AWS_PROFILE", "default")  # Added profile support
SAGEMAKER_ROLE = os.getenv("SAGEMAKER_ROLE")

# Test results tracking
test_results = []

def print_header(text):
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)

def print_test(number, description):
    print(f"\n{number} {description}")

def log_result(test_name, success, message=""):
    test_results.append({
        "test": test_name,
        "success": success,
        "message": message
    })
    if success:
        print(f"✅ {message}" if message else "✅ Success")
    else:
        print(f"❌ {message}" if message else "❌ Failed")

print_header("AWS Connection & Permissions Test Suite")
print("Testing all AWS services required for MedGemma deployment")
print(f"Region: {AWS_REGION}")
print(f"Profile: {AWS_PROFILE}")
print("=" * 70)

# ============================================================================
# TEST 1: AWS AUTHENTICATION (STS)
# ============================================================================
print_test("1️⃣", "Testing AWS Authentication (STS)")

try:
    # Create session with profile
    session = boto3.Session(profile_name=AWS_PROFILE, region_name=AWS_REGION)
    sts_client = session.client("sts")
    identity = sts_client.get_caller_identity()

    account_id = identity['Account']
    arn = identity['Arn']
    user_id = identity['UserId']

    print(f"   Account ID: {account_id}")
    print(f"   ARN: {arn}")
    print(f"   User ID: {user_id}")

    # Extract role/user name
    if ':assumed-role/' in arn:
        role_name = arn.split('assumed-role/')[1].split('/')[0]
        print(f"   Role Name: {role_name}")
        log_result("STS Authentication", True, f"Authenticated as role: {role_name}")
    elif ':user/' in arn:
        user_name = arn.split('user/')[1]
        print(f"   User Name: {user_name}")
        log_result("STS Authentication", True, f"Authenticated as user: {user_name}")
    else:
        log_result("STS Authentication", True, "Authenticated successfully")

except NoCredentialsError:
    log_result("STS Authentication", False, "No AWS credentials found")
    print("\n💡 To fix this:")
    print(f"   1. Run: aws sso login --profile {AWS_PROFILE}")
    print("   2. Complete authentication in your browser")
    print("   3. Run this script again")
    sys.exit(1)
except ClientError as e:
    error_code = e.response['Error']['Code']
    if error_code == 'InvalidClientTokenId':
        log_result("STS Authentication", False, "SSO session expired or invalid")
        print("\n💡 To fix this:")
        print(f"   1. Run: aws sso login --profile {AWS_PROFILE}")
        print("   2. Complete authentication in your browser")
        print("   3. Run this script again")
    else:
        log_result("STS Authentication", False, f"Error: {e}")
    sys.exit(1)
except Exception as e:
    log_result("STS Authentication", False, f"Unexpected error: {e}")
    sys.exit(1)

# ============================================================================
# TEST 2: IAM ROLE ACCESS
# ============================================================================
print_test("2️⃣", "Testing IAM Role Access")

iam_client = session.client("iam")

try:
    # Try to get SageMaker execution role
    sess = sagemaker.Session(boto_session=session)

    if SAGEMAKER_ROLE:
        role = SAGEMAKER_ROLE
        print(f"   Using custom role from .env: {role}")
    else:
        try:
            role = sagemaker.get_execution_role(sagemaker_session=sess)
            print(f"   Auto-detected role: {role}")
        except Exception as e:
            log_result("IAM Role", False, f"Cannot auto-detect role: {e}")
            print("   💡 Set SAGEMAKER_ROLE in .env file")
            role = None

    if role:
        # Extract role name from ARN
        role_name = role.split('/')[-1]

        # Try to get role details
        try:
            role_details = iam_client.get_role(RoleName=role_name)
            print(f"   Role exists: {role_name}")
            log_result("IAM Role", True, f"Role accessible: {role_name}")
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchEntity':
                log_result("IAM Role", False, f"Role not found: {role_name}")
            elif e.response['Error']['Code'] == 'AccessDenied':
                log_result("IAM Role", True, f"Role exists but cannot read details (permissions OK for deployment)")
            else:
                log_result("IAM Role", False, f"Error checking role: {e}")

except Exception as e:
    log_result("IAM Role", False, f"Unexpected error: {e}")

# ============================================================================
# TEST 3: S3 BUCKET ACCESS
# ============================================================================
print_test("3️⃣", "Testing S3 Bucket Access")

s3_client = session.client("s3")

# Determine bucket
if S3_BUCKET:
    bucket = S3_BUCKET
    print(f"   Using custom bucket: {bucket}")
else:
    bucket = sess.default_bucket()
    print(f"   Using default SageMaker bucket: {bucket}")

# 3.1: Check bucket exists
try:
    s3_client.head_bucket(Bucket=bucket)
    log_result("S3 Bucket Exists", True, f"Bucket '{bucket}' is accessible")
except ClientError as e:
    error_code = e.response['Error']['Code']
    if error_code == '404':
        log_result("S3 Bucket Exists", False, f"Bucket '{bucket}' does not exist")
    elif error_code == '403':
        log_result("S3 Bucket Exists", False, f"Access denied to bucket '{bucket}'")
    else:
        log_result("S3 Bucket Exists", False, f"Error: {e}")

# 3.2: Check bucket region
try:
    location = s3_client.get_bucket_location(Bucket=bucket)
    bucket_region = location['LocationConstraint'] or 'us-east-1'
    print(f"   Bucket region: {bucket_region}")

    if bucket_region == AWS_REGION:
        log_result("S3 Bucket Region", True, "Bucket in correct region")
    else:
        log_result("S3 Bucket Region", False, f"Region mismatch: bucket in {bucket_region}, using {AWS_REGION}")
except ClientError as e:
    log_result("S3 Bucket Region", False, f"Cannot check region: {e}")

# ============================================================================
# TEST 4: S3 PERMISSIONS
# ============================================================================
print_test("4️⃣", "Testing S3 Permissions")

test_key = f"{S3_PREFIX}/connection_test.txt"
test_content = "Connection test file"

# 4.1: ListBucket permission
try:
    response = s3_client.list_objects_v2(
        Bucket=bucket,
        Prefix=S3_PREFIX,
        MaxKeys=1
    )
    log_result("S3 ListBucket", True, "Can list objects in bucket")
except ClientError as e:
    log_result("S3 ListBucket", False, f"Cannot list objects: {e}")

# 4.2: PutObject permission
try:
    s3_client.put_object(
        Bucket=bucket,
        Key=test_key,
        Body=test_content.encode('utf-8')
    )
    log_result("S3 PutObject", True, "Can upload objects to bucket")
except ClientError as e:
    log_result("S3 PutObject", False, f"Cannot upload: {e}")

# 4.3: GetObject permission
try:
    response = s3_client.get_object(Bucket=bucket, Key=test_key)
    content = response['Body'].read().decode('utf-8')
    if content == test_content:
        log_result("S3 GetObject", True, "Can read objects from bucket")
    else:
        log_result("S3 GetObject", False, "Read content doesn't match")
except ClientError as e:
    log_result("S3 GetObject", False, f"Cannot read: {e}")

# 4.4: DeleteObject permission
try:
    s3_client.delete_object(Bucket=bucket, Key=test_key)
    log_result("S3 DeleteObject", True, "Can delete objects from bucket")
except ClientError as e:
    log_result("S3 DeleteObject", False, f"Cannot delete: {e}")

# ============================================================================
# TEST 5: SAGEMAKER PERMISSIONS
# ============================================================================
print_test("5️⃣", "Testing SageMaker Permissions")

sagemaker_client = session.client("sagemaker")

# 5.1: List models permission
try:
    response = sagemaker_client.list_models(MaxResults=1)
    log_result("SageMaker ListModels", True, "Can list SageMaker models")
except ClientError as e:
    log_result("SageMaker ListModels", False, f"Cannot list models: {e}")

# 5.2: List endpoints permission
try:
    response = sagemaker_client.list_endpoints(MaxResults=1)
    log_result("SageMaker ListEndpoints", True, "Can list SageMaker endpoints")
except ClientError as e:
    log_result("SageMaker ListEndpoints", False, f"Cannot list endpoints: {e}")

# 5.3: Describe endpoint configs permission
try:
    response = sagemaker_client.list_endpoint_configs(MaxResults=1)
    log_result("SageMaker ListEndpointConfigs", True, "Can list endpoint configurations")
except ClientError as e:
    log_result("SageMaker ListEndpointConfigs", False, f"Cannot list configs: {e}")

# ============================================================================
# TEST 6: ECR PERMISSIONS (Docker Images)
# ============================================================================
print_test("6️⃣", "Testing ECR Permissions (Docker Images)")

ecr_client = session.client("ecr")

# Check if can get authorization token (needed to pull images)
try:
    response = ecr_client.get_authorization_token()
    log_result("ECR Authorization", True, "Can get ECR authorization token")
except ClientError as e:
    if e.response['Error']['Code'] == 'AccessDeniedException':
        log_result("ECR Authorization", False, "Access denied to ECR")
    else:
        log_result("ECR Authorization", False, f"Error: {e}")

# ============================================================================
# TEST 7: CLOUDWATCH LOGS PERMISSIONS
# ============================================================================
print_test("7️⃣", "Testing CloudWatch Logs Permissions")

logs_client = session.client("logs")

# Check if can describe log groups
try:
    response = logs_client.describe_log_groups(limit=1)
    log_result("CloudWatch Logs", True, "Can access CloudWatch Logs")
except ClientError as e:
    log_result("CloudWatch Logs", False, f"Cannot access logs: {e}")

# ============================================================================
# TEST 8: SECRETS MANAGER (Optional - for secure token storage)
# ============================================================================
print_test("8️⃣", "Testing Secrets Manager (Optional)")

secrets_client = session.client("secretsmanager")

try:
    response = secrets_client.list_secrets(MaxResults=1)
    log_result("Secrets Manager", True, "Can access Secrets Manager (optional)")
except ClientError as e:
    log_result("Secrets Manager", False, f"Cannot access (not required): {e}")

# ============================================================================
# SUMMARY
# ============================================================================
print_header("Test Summary")

passed = sum(1 for r in test_results if r['success'])
failed = sum(1 for r in test_results if not r['success'])
total = len(test_results)

print(f"\nTotal Tests: {total}")
print(f"✅ Passed: {passed}")
print(f"❌ Failed: {failed}")

if failed > 0:
    print("\n" + "=" * 70)
    print("Failed Tests:")
    print("=" * 70)
    for result in test_results:
        if not result['success']:
            print(f"❌ {result['test']}: {result['message']}")

print("\n" + "=" * 70)
print("Configuration Summary")
print("=" * 70)
print(f"AWS Region: {AWS_REGION}")
print(f"AWS Profile: {AWS_PROFILE}")
print(f"S3 Bucket: {bucket}")
print(f"S3 Prefix: {S3_PREFIX}")
print(f"Account ID: {account_id}")
print(f"Current Identity: {arn}")
if role:
    print(f"SageMaker Role: {role}")
print("=" * 70)

# ============================================================================
# RECOMMENDATIONS
# ============================================================================
if failed > 0:
    print("\n" + "=" * 70)
    print("⚠️  Recommendations")
    print("=" * 70)

    # Check for common issues
    if not any(r['test'] == 'STS Authentication' and r['success'] for r in test_results):
        print(f"• Run 'aws sso login --profile {AWS_PROFILE}' to authenticate")

    if not any(r['test'].startswith('S3') and r['success'] for r in test_results):
        print("• Check S3 bucket name in .env file")
        print("• Ensure IAM role has S3 permissions")

    if not any(r['test'].startswith('SageMaker') and r['success'] for r in test_results):
        print("• Ensure IAM role has SageMaker permissions")
        print("• Check if you're in the correct AWS region")

    if not any(r['test'] == 'IAM Role' and r['success'] for r in test_results):
        print("• Set SAGEMAKER_ROLE in .env file")
        print("• Ensure the role has proper trust relationship with SageMaker")

    print("\n💡 Required IAM Permissions:")
    print("   S3: GetObject, PutObject, DeleteObject, ListBucket")
    print("   SageMaker: CreateModel, CreateEndpoint, CreateEndpointConfig")
    print("   ECR: GetAuthorizationToken, BatchGetImage")
    print("   CloudWatch: CreateLogGroup, CreateLogStream, PutLogEvents")
    print("=" * 70)

# Exit code
if failed == 0:
    print("\n✅ All tests passed! You're ready to deploy.")
    sys.exit(0)
else:
    print(f"\n❌ {failed} test(s) failed. Please fix the issues above before deploying.")
    sys.exit(1)
