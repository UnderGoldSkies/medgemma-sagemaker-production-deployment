"""
Simple example of text-only inference with MedGemma endpoint.
"""

import json
import boto3
import os
import sys
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Load environment variables
load_dotenv("config/.env")

def invoke_medgemma(prompt: str, endpoint_name: str = None):
    """
    Send a text prompt to MedGemma endpoint and get response.

    Args:
        prompt: Medical question or instruction
        endpoint_name: SageMaker endpoint name (reads from build/endpoint_info.txt if None)

    Returns:
        Generated text response
    """

    # Get endpoint name
    if endpoint_name is None:
        try:
            with open("build/endpoint_info.txt", "r") as f:
                endpoint_name = f.read().strip()
        except FileNotFoundError:
            print("❌ Error: build/endpoint_info.txt not found")
            print("Deploy the endpoint first: python scripts/deploy.py")
            sys.exit(1)

    # Initialize SageMaker runtime client
    client = boto3.client(
        'sagemaker-runtime',
        region_name=os.getenv('AWS_REGION')
    )

    # Prepare payload
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 256,
            "temperature": 0.7,
            "top_p": 0.9
        }
    }

    print(f"🔮 Invoking endpoint: {endpoint_name}")
    print(f"📝 Prompt: {prompt}\n")

    try:
        # Invoke endpoint
        response = client.invoke_endpoint(
            EndpointName=endpoint_name,
            ContentType='application/json',
            Body=json.dumps(payload),
            Accept='application/json'
        )

        # Parse response
        result = json.loads(response['Body'].read().decode())
        generated_text = result.get('generated_text', '')

        print(f"✅ Response:")
        print(f"{generated_text}\n")

        # Show inference time
        inference_time = result.get('inference_time', 0)
        print(f"⏱️  Inference time: {inference_time:.2f}s")

        return generated_text

    except Exception as e:
        print(f"❌ Error invoking endpoint: {e}")
        return None


def main():
    """Run example queries."""

    # Example medical questions
    examples = [
        "What are the common symptoms of pneumonia?",
        "Explain the difference between Type 1 and Type 2 diabetes.",
        "What are the warning signs of a heart attack?",
        "How does insulin work in the body?",
    ]

    print("🏥 MedGemma Simple Inference Example\n")
    print("=" * 60)

    for i, prompt in enumerate(examples, 1):
        print(f"\n📋 Example {i}/{len(examples)}")
        print("-" * 60)

        invoke_medgemma(prompt)

        if i < len(examples):
            print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
