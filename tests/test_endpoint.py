"""
Test MedGemma SageMaker Endpoint
Tests both text-only and image+text inputs
"""
import os
import base64
import boto3
import sagemaker
from pathlib import Path
from dotenv import load_dotenv
from sagemaker.predictor import Predictor
from sagemaker.serializers import JSONSerializer
from sagemaker.deserializers import JSONDeserializer

load_dotenv("config/.env")

# Get AWS configuration
AWS_PROFILE = os.getenv("AWS_PROFILE", "default")
AWS_REGION = os.getenv("AWS_REGION", "ap-southeast-1")

# Create boto session with profile
boto_session = boto3.Session(profile_name=AWS_PROFILE, region_name=AWS_REGION)

# Load endpoint name from file or env
if os.path.exists("build/endpoint_info.txt"):
    with open("build/endpoint_info.txt") as f:
        for line in f:
            if line.startswith("ENDPOINT_NAME="):
                endpoint_name = line.strip().split("=", 1)[1]
                break
else:
    endpoint_name = os.getenv("ENDPOINT_NAME")
    if not endpoint_name:
        raise ValueError("Endpoint name not found. Deploy first with: python deploy.py")

print(f"Testing endpoint: {endpoint_name}")
print(f"AWS Profile: {AWS_PROFILE}")
print(f"Region: {AWS_REGION}")

# Create predictor with boto session
predictor = Predictor(
    endpoint_name=endpoint_name,
    sagemaker_session=None,  # Will be created from boto_session
    serializer=JSONSerializer(),
    deserializer=JSONDeserializer(),
)

# Update the predictor's session to use our boto session
predictor.sagemaker_session = sagemaker.Session(boto_session=boto_session)

# Test case 1: General medical query (text-only)
print("\n" + "=" * 60)
print("Test 1: General Medical Query (Text-Only)")
print("=" * 60)

messages = [
    {
        "role": "system",
        "content": [{"type": "text", "text": "You are a doctor."}],
    },
    {
        "role": "user",
        "content": [
            {"type": "text", "text": "Explain what are the symptoms that warrant a health screening."}
        ],
    },
]

payload = {
    "messages": messages,
    "max_new_tokens": 128,
}

try:
    response = predictor.predict(payload)
    print(f"\nResponse:\n{response['generated_text']}")
except Exception as e:
    print(f"\n❌ Error: {e}")
    print("\n💡 Make sure you've run: aws sso login --profile default")
    exit(1)

# Test case 2: Clinical scenario (text-only)
print("\n" + "=" * 60)
print("Test 2: Clinical Scenario (Text-Only)")
print("=" * 60)

messages = [
    {
        "role": "system",
        "content": [{"type": "text", "text": "You are a senior internal medicine consultant."}],
    },
    {
        "role": "user",
        "content": [
            {"type": "text", "text": "A 55-year-old man presents with chest pain after exertion, relieved by rest. What is the likely diagnosis and next step?"}
        ],
    },
]

payload = {"messages": messages, "max_new_tokens": 500}
response = predictor.predict(payload)
print(f"\nResponse:\n{response['generated_text']}")

# Test case 3: Medical image analysis (image+text)
print("\n" + "=" * 60)
print("Test 3: Medical Image Analysis (Image + Text)")
print("=" * 60)

# Look for test image in test_images folder
test_image_path = Path("test_images") / "medical_image.png"
if test_image_path.exists():
    print(f"📷 Loading image: {test_image_path}")
    # Read and encode image
    with open(test_image_path, "rb") as img_file:
        image_base64 = base64.b64encode(img_file.read()).decode("utf-8")

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image", "image": image_base64},
                {"type": "text", "text": "Describe what you see in this medical image. What abnormalities, if any, are present?"}
            ],
        },
    ]

    payload = {
        "messages": messages,
        "max_new_tokens": 300,
    }

    response = predictor.predict(payload)
    print(f"\nResponse:\n{response['generated_text']}")
else:
    print(f"⚠️  Test image not found at '{test_image_path}'")
    print("   To test image input, place a medical image at this path and run again.")
    print("   Example: X-ray, CT scan, or dermatology image")

# Test case 4: Chest X-ray interpretation example
print("\n" + "=" * 60)
print("Test 4: Chest X-ray Interpretation (Image + Text)")
print("=" * 60)

# Look for chest X-ray in test_images folder
chest_xray_path = Path("test_images") / "chest_xray.png"
if chest_xray_path.exists():
    print(f"📷 Loading image: {chest_xray_path}")
    with open(chest_xray_path, "rb") as img_file:
        image_base64 = base64.b64encode(img_file.read()).decode("utf-8")

    messages = [
        {
            "role": "system",
            "content": [{"type": "text", "text": "You are a radiologist specializing in chest imaging."}],
        },
        {
            "role": "user",
            "content": [
                {"type": "image", "image": image_base64},
                {"type": "text", "text": "Please interpret this chest X-ray. Describe the findings and provide a differential diagnosis."}
            ],
        },
    ]

    payload = {
        "messages": messages,
        "max_new_tokens": 500,
    }

    response = predictor.predict(payload)
    print(f"\nResponse:\n{response['generated_text']}")
else:
    print(f"⚠️  Chest X-ray not found at '{chest_xray_path}'")
    print("   Skipping this test. Place a chest X-ray image to test this functionality.")

print("\n" + "=" * 60)
print("✅ Testing complete!")
print("=" * 60)
print("\n💡 Tips:")
print("   - Test images are loaded from: test_images/")
print("   - Supported formats: JPG, PNG")
print("   - Images are sent as base64-encoded strings")
print("\n📝 Test with specific image:")
print("   python test_with_image.py test_images/chest_xray.png 'Your question'")
