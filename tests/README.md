# Tests

This directory contains all test files and test data.

## Test Scripts

### test_endpoint.py
Tests basic text-based medical Q&A functionality.

**Usage:**
```bash
python tests/test_endpoint.py
```

**What it does:**
- Connects to deployed SageMaker endpoint
- Sends medical questions
- Validates responses
- Measures inference time

### test_with_image.py
Tests medical image analysis capabilities.

**Usage:**
```bash
python tests/test_with_image.py
```

**What it does:**
- Loads sample chest X-ray
- Encodes image to base64
- Sends to endpoint with prompt
- Displays AI analysis

## Test Data

### test_images/
Contains sample medical images for testing:
- `chest_xray.png` - Sample chest X-ray
- `medical_image.png` - General medical image

**Add your own:**
```bash
# Place your medical images here
cp /path/to/your/xray.png tests/test_images/my_xray.png

# Then test with it
python tests/test_with_image.py
# (modify script to use your image)
```

## Running Tests

### Quick Test
```bash
# Test text inference
python tests/test_endpoint.py

# Test image analysis
python tests/test_with_image.py
```

### Custom Test
```python
# tests/my_custom_test.py
import sys
import os
sys.path.insert(0, os.path.abspath('..'))

from tests.test_endpoint import invoke_endpoint

# Your custom test
response = invoke_endpoint("Your medical question here")
print(response)
```

## Prerequisites

Before running tests:
1. ✅ Deploy the endpoint: `python scripts/deploy.py`
2. ✅ Verify `build/endpoint_info.txt` exists
3. ✅ Check `config/.env` is configured

## Troubleshooting

**Test fails with "endpoint not found":**
- Verify deployment: `cat build/endpoint_info.txt`
- Check endpoint status in AWS Console

**Test timeout:**
- First inference may take longer (cold start)
- Check CloudWatch logs: `python scripts/check_logs.py`

**Image test fails:**
- Verify image format (PNG/JPG)
- Check image size (<5MB recommended)
- Ensure proper encoding

## Expected Results

### test_endpoint.py Success
```
✅ Response received
⏱️  Inference time: 2.3s
Response quality: Medical information provided
```

### test_with_image.py Success
```
✅ Image loaded and encoded
✅ Analysis received
⏱️  Inference time: 4.1s
Analysis: [Medical findings from X-ray]
```

---

**Need help?** Check [docs/TROUBLESHOOTING.md](../docs/TROUBLESHOOTING.md)
