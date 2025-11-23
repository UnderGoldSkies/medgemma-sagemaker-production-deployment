"""
Test MedGemma SageMaker Endpoint
Tests both text-only and image+text inputs (Non-streaming)
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
from botocore.config import Config

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent

load_dotenv(PROJECT_ROOT / "config/.env")

# Get AWS configuration
AWS_PROFILE = os.getenv("AWS_PROFILE", "default")
AWS_REGION = os.getenv("AWS_REGION", "ap-southeast-1")
MAX_NEW_TOKENS = int(os.getenv("MAX_NEW_TOKENS", "512"))
READ_TIMEOUT_SECONDS = int(os.getenv("READ_TIMEOUT_SECONDS", "300"))

# Create boto session
config = Config(
    read_timeout=READ_TIMEOUT_SECONDS,
    connect_timeout=60,
    retries={'max_attempts': 2}
)

boto_session = boto3.Session(profile_name=AWS_PROFILE, region_name=AWS_REGION)
runtime_client = boto_session.client('sagemaker-runtime', config=config)

endpoint_info_path = PROJECT_ROOT / "build/endpoint_info.txt"
# Load endpoint name from file or env
if endpoint_info_path.exists():
    with open(endpoint_info_path) as f:
        for line in f:
            if line.startswith("ENDPOINT_NAME="):
                endpoint_name = line.strip().split("=", 1)[1]
                break
else:
    endpoint_name = os.getenv("ENDPOINT_NAME")
    if not endpoint_name:
        raise ValueError("Endpoint name not found. Deploy first with: python scripts/deploy.py")

print(f"Testing endpoint: {endpoint_name}")
print(f"AWS Profile: {AWS_PROFILE}")
print(f"Region: {AWS_REGION}")
print(f"Timeout: {READ_TIMEOUT_SECONDS} seconds")
print(f"Max new tokens (env MAX_NEW_TOKENS): {MAX_NEW_TOKENS}")

# Create predictor with custom session
sess = sagemaker.Session(boto_session=boto_session, sagemaker_runtime_client=runtime_client)

predictor = Predictor(
    endpoint_name=endpoint_name,
    sagemaker_session=sess,
    serializer=JSONSerializer(),
    deserializer=JSONDeserializer(),
)

# Test case 1: General medical query (text-only)
print("\n" + "=" * 60)
print("Test 1: General Medical Query (Text-Only) - NON-STREAMING")
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
    "max_new_tokens": MAX_NEW_TOKENS,
    "stream": False,
}

try:
    response = predictor.predict(payload)
    if isinstance(response, str):
        generated = response
    elif isinstance(response, dict):
        if "generated_text" in response:
            generated = response["generated_text"]
        elif "choices" in response and response["choices"]:
            generated = response["choices"][0]["message"]["content"]
        else:
            raise ValueError(f"Unexpected response shape: {response}")
    elif isinstance(response, list) and response and isinstance(response[0], dict):
        if "generated_text" in response[0]:
            generated = response[0]["generated_text"]
        else:
            raise ValueError(f"Unexpected response shape: {response}")
    else:
        raise ValueError(f"Unexpected response type: {type(response)} -> {response}")

    print(f"\nResponse:\n{generated}")
    print(f"\n({len(generated)} characters)")
except Exception as e:
    print(f"\n❌ Error: {e}")
    print("\n💡 Make sure you've run: aws sso login --profile default")
    exit(1)

# Test case 2: Clinical scenario (text-only)
print("\n" + "=" * 60)
print("Test 2: Clinical Scenario (Text-Only) - NON-STREAMING")
print("=" * 60)

messages = [
    {
        "role": "system",
        "content": [{"type": "text", "text": "You are a senior internal medicine consultant."}],
    },
    {
        "role": "user",
        "content": [
            {"type": "text", "text": "A 55-year-old man presents with chest pain after exertion, relieved by rest. What is the likely diagnosis and next steps? Provide a detailed answer."}
        ],
    },
]

payload = {
    "messages": messages,
    "max_new_tokens": MAX_NEW_TOKENS,
    "stream": False,
}

response = predictor.predict(payload)
if isinstance(response, dict) and "generated_text" in response:
    generated = response["generated_text"]
elif isinstance(response, list) and response and isinstance(response[0], dict) and "generated_text" in response[0]:
    generated = response[0]["generated_text"]
else:
    raise ValueError(f"Unexpected response shape: {response}")

print(f"\nResponse:\n{generated}")
print(f"\n({len(generated)} characters)")

# Test case 3: Medical image analysis (image+text)
print("\n" + "=" * 60)
print("Test 3: Medical Image Analysis (Image + Text) - NON-STREAMING")
print("=" * 60)

test_image_path = BASE_DIR / "test_images" / "medical_image.png"
if test_image_path.exists():
    print(f"📷 Loading image: {test_image_path}")
    with open(test_image_path, "rb") as img_file:
        image_base64 = base64.b64encode(img_file.read()).decode("utf-8")

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image", "image": image_base64},
                {"type": "text", "text": "Describe what you see in this medical image in detail. What abnormalities, if any, are present? What would be your clinical recommendations?"}
            ],
        },
    ]

    payload = {
        "messages": messages,
        "max_new_tokens": MAX_NEW_TOKENS,
        "stream": False,
    }

    response = predictor.predict(payload)
    print(f"\nResponse:\n{response['generated_text']}")
    print(f"\n({len(response['generated_text'])} characters)")
else:
    print(f"⚠️  Test image not found at '{test_image_path}'")
    print("   Skipping this test.")

# Test case 4: Chest X-ray interpretation
print("\n" + "=" * 60)
print("Test 4: Chest X-ray Interpretation (Image + Text) - NON-STREAMING")
print("=" * 60)

chest_xray_path = BASE_DIR / "test_images" / "chest_xray.png"
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
                {"type": "text", "text": "Please provide a comprehensive interpretation of this chest X-ray. Describe all findings and provide a complete differential diagnosis."}
            ],
        },
    ]

    payload = {
        "messages": messages,
        "max_new_tokens": MAX_NEW_TOKENS,
    }

    response = predictor.predict(payload)
    print(f"\nResponse:\n{response['generated_text']}")
    print(f"\n({len(response['generated_text'])} characters)")
else:
    print(f"⚠️  Chest X-ray not found at '{chest_xray_path}'")
    print("   Skipping this test.")

print("\n" + "=" * 60)
print("✅ Testing complete!")
print("=" * 60)
print("\n💡 Tips:")
print(f"   - Test images: {BASE_DIR / 'test_images'}/")
print("   - Supported formats: JPG, PNG")
print("   - Use max_new_tokens to control response length")
