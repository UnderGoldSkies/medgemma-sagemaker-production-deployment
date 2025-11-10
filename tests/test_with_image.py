"""
Test MedGemma endpoint with a specific medical image
Usage:
  python test_with_image.py <path_to_image> [question]
  python test_with_image.py <image_name_in_test_images> [question]
"""
import os
import sys
import base64
import boto3
from pathlib import Path
from dotenv import load_dotenv
from sagemaker.predictor import Predictor
from sagemaker.serializers import JSONSerializer
from sagemaker.deserializers import JSONDeserializer
import sagemaker

load_dotenv("config/.env")

if len(sys.argv) < 2:
    print("Usage: python test_with_image.py <path_to_image> [question]")
    print("\nExamples:")
    print("  python test_with_image.py chest_xray.png 'What do you see in this chest X-ray?'")
    print("  python test_with_image.py test_images/chest_xray.png 'Describe the findings'")
    print("  python test_with_image.py /full/path/to/image.jpg 'Analyze this image'")
    print("\nAvailable images in test_images/:")
    test_images_dir = Path("test_images")
    if test_images_dir.exists():
        for img in sorted(test_images_dir.glob("*.png")):
            print(f"  - {img.name}")
        for img in sorted(test_images_dir.glob("*.jpg")):
            print(f"  - {img.name}")
    sys.exit(1)

image_input = sys.argv[1]
question = sys.argv[2] if len(sys.argv) > 2 else "Describe what you see in this medical image."

# Try to find the image
image_path = None

# Check if it's a full path
if os.path.exists(image_input):
    image_path = image_input
# Check in test_images folder
elif os.path.exists(os.path.join("test_images", image_input)):
    image_path = os.path.join("test_images", image_input)
# Check if it's already a path in test_images
elif image_input.startswith("test_images/") and os.path.exists(image_input):
    image_path = image_input

if not image_path:
    print(f"❌ Error: Image not found at '{image_input}'")
    print("\n💡 Available images in test_images/:")
    test_images_dir = Path("test_images")
    if test_images_dir.exists():
        for img in sorted(test_images_dir.glob("*.png")):
            print(f"  - {img.name}")
        for img in sorted(test_images_dir.glob("*.jpg")):
            print(f"  - {img.name}")
    sys.exit(1)

# Get AWS configuration
AWS_PROFILE = os.getenv("AWS_PROFILE", "default")
AWS_REGION = os.getenv("AWS_REGION", "ap-southeast-1")

# Create boto session with profile
boto_session = boto3.Session(profile_name=AWS_PROFILE, region_name=AWS_REGION)

# Load endpoint name
if os.path.exists("build/endpoint_info.txt"):
    with open("build/endpoint_info.txt") as f:
        for line in f:
            if line.startswith("ENDPOINT_NAME="):
                endpoint_name = line.strip().split("=", 1)[1]
                break
else:
    endpoint_name = os.getenv("ENDPOINT_NAME")
    if not endpoint_name:
        print("❌ Error: Endpoint name not found. Deploy first with: python deploy.py")
        sys.exit(1)

print(f"🔬 Testing endpoint: {endpoint_name}")
print(f"📷 Image: {image_path}")
print(f"❓ Question: {question}")
print("=" * 60)

# Read and encode image
with open(image_path, "rb") as img_file:
    image_base64 = base64.b64encode(img_file.read()).decode("utf-8")

# Create predictor with boto session
predictor = Predictor(
    endpoint_name=endpoint_name,
    sagemaker_session=sagemaker.Session(boto_session=boto_session),
    serializer=JSONSerializer(),
    deserializer=JSONDeserializer(),
)

# Prepare payload
messages = [
    {
        "role": "system",
        "content": [{"type": "text", "text": "You are an expert medical doctor analyzing medical images."}],
    },
    {
        "role": "user",
        "content": [
            {"type": "image", "image": image_base64},
            {"type": "text", "text": question}
        ],
    },
]

payload = {
    "messages": messages,
    "max_new_tokens": 500,
}

print("\n🤖 Generating response...\n")

try:
    response = predictor.predict(payload)
    print("Response:")
    print("=" * 60)
    print(response['generated_text'])
    print("=" * 60)
    print("\n✅ Test complete!")
except Exception as e:
    print(f"❌ Error: {e}")
    print("\n💡 Make sure you've run: aws sso login --profile default")
    sys.exit(1)
