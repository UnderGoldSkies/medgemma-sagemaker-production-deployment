# Usage Examples

## Quick Test

Test your deployed endpoint:

```bash
# Basic test
python tests/test_endpoint.py

# Test with medical image
python tests/test_with_image.py
```

## Python Code Example

```python
# examples/python/simple_text_inference.py

import json
import boto3

# Initialize client
client = boto3.client('sagemaker-runtime', region_name='us-east-1')

# Send a request
response = client.invoke_endpoint(
    EndpointName='your-endpoint-name',
    ContentType='application/json',
    Body=json.dumps({
        "inputs": "What are the symptoms of pneumonia?",
        "parameters": {"max_new_tokens": 256}
    })
)

# Get result
result = json.loads(response['Body'].read())
print(result['generated_text'])
```

## Try Different Questions

```python
questions = [
    "What are the common symptoms of pneumonia?",
    "Explain diabetes in simple terms",
    "What causes high blood pressure?",
    "How does insulin work?"
]

for question in questions:
    # Use the code above to get answers
    print(f"Q: {question}")
    print(f"A: {answer}\n")
```

## More Examples

Check the main [README](../README.md) for detailed usage instructions.
