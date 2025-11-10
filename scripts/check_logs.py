"""
Check SageMaker Endpoint CloudWatch Logs
"""
import os
import boto3
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv("config/.env")

AWS_PROFILE = os.getenv("AWS_PROFILE", "default")
AWS_REGION = os.getenv("AWS_REGION", "ap-southeast-1")

# Load endpoint name
if os.path.exists("../build/endpoint_info.txt"):
    with open("../build/endpoint_info.txt") as f:
        for line in f:
            if line.startswith("ENDPOINT_NAME="):
                endpoint_name = line.strip().split("=", 1)[1]
                break
else:
    endpoint_name = os.getenv("ENDPOINT_NAME")

print(f"Checking logs for endpoint: {endpoint_name}")

# Create boto session
boto_session = boto3.Session(profile_name=AWS_PROFILE, region_name=AWS_REGION)
logs_client = boto_session.client("logs")

# Log group name follows pattern
log_group_name = f"/aws/sagemaker/Endpoints/{endpoint_name}"

print(f"Log group: {log_group_name}")
print("=" * 70)

try:
    # Get log streams (most recent first)
    response = logs_client.describe_log_streams(
        logGroupName=log_group_name,
        orderBy='LastEventTime',
        descending=True,
        limit=5
    )

    if not response['logStreams']:
        print("No log streams found yet. Endpoint may still be starting up.")
        exit(0)

    # Get the most recent log stream
    log_stream_name = response['logStreams'][0]['logStreamName']
    print(f"Most recent log stream: {log_stream_name}\n")

    # Get recent log events
    start_time = int((datetime.now() - timedelta(minutes=30)).timestamp() * 1000)

    log_response = logs_client.get_log_events(
        logGroupName=log_group_name,
        logStreamName=log_stream_name,
        startTime=start_time,
        startFromHead=False,
        limit=100
    )

    print("Recent logs:")
    print("=" * 70)

    for event in log_response['events']:
        timestamp = datetime.fromtimestamp(event['timestamp'] / 1000)
        message = event['message']
        print(f"[{timestamp}] {message}")

    print("=" * 70)

except logs_client.exceptions.ResourceNotFoundException:
    print(f"Log group not found: {log_group_name}")
    print("The endpoint may still be creating or hasn't generated logs yet.")
except Exception as e:
    print(f"Error retrieving logs: {e}")
