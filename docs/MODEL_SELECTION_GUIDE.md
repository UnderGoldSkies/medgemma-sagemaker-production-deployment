# docs/MODEL_SELECTION_GUIDE.md

# Model Selection Guide

## Available MedGemma Models

MedGemma is built on **Gemma 3** architecture by Google Health AI.

### 1. MedGemma 4B Multimodal ✅ **Default in This Tutorial**
- **Model ID**: `google/medgemma-4b-it`
- **Parameters**: 4 billion
- **Context**: 128K+ tokens
- **Input**: Text AND Images
- **Output**: Text only

**Best for:**
- Learning and tutorials
- Medical Q&A with image analysis
- Testing multimodal capabilities
- Cost-effective deployment

### 2. MedGemma 27B Multimodal (optional)
- **Model ID**: `google/medgemma-27b-it`
- **Parameters**: 27 billion
- **Context**: 128K+ tokens
- **Input**: Text AND Images
- **Output**: Text only

## What is Multimodal?

**Multimodal** = Can process both text and images

### Text-Only Example:
```python
Input: "What are symptoms of pneumonia?"
Output: "Common symptoms include fever, cough..."
```

### Multimodal Example (Text + Image):
```python
Input: "Analyze this chest X-ray" + [X-ray image]
Output: "The X-ray shows consolidation in the right lower lobe,
         consistent with pneumonia..."
```

## How to Change Models

### Method 1: Edit Configuration File (Recommended)

```bash
# Edit config/.env
nano config/.env
```

**For 4B Multimodal (Default):**
```bash
MODEL_ID=google/medgemma-4b-it
INSTANCE_TYPE=ml.g5.2xlarge    # ~$1.52/hour - NOT FREE ⚠️
```

**For 27B Multimodal (optional):**
```bash
MODEL_ID=google/medgemma-27b-it
INSTANCE_TYPE=ml.g5.12xlarge   # ~$7.09/hour - EXPENSIVE ⚠️
```

> ⚠️ **COST WARNING**: These instances are **NOT FREE**. You are charged per second while the endpoint is running.
> - **4B model**: ~$1.52/hour ($36.48/day)
> - **27B model**: ~$7.09/hour ($170/day)
>
> Always run `python scripts/cleanup.py` when done to stop billing!

> 💡 **Instance types are recommendations** based on model size. Smaller instances may fail due to insufficient memory. Larger instances cost more but don't improve performance.

## Request Model Access

**Required before using any model:**

1. Go to HuggingFace model page:
   - [medgemma-4b](https://huggingface.co/google/medgemma-4b)
   - [medgemma-27b](https://huggingface.co/google/medgemma-27b) (multimodal)

2. Click **"Request Access"**

3. Accept terms

4. Wait for approval (usually instant)

5. Use your HuggingFace token in `config/.env`

## Which Should You Choose?

### Use 4B if:
- ✅ Learning/building tutorials
- ✅ Need text + image analysis
- ✅ Want balanced performance

### Use 27B Multimodal if:
- ✅ Need best performance
- ✅ Production deployment
- ✅ Complex medical imaging

---

**Official Documentation:**
- [MedGemma Model Card](https://developers.google.com/health-ai-developer-foundations/medgemma/model-card)
- [Technical Report](https://arxiv.org/abs/2507.05201)
- [Google Health AI](https://developers.google.com/health-ai-developer-foundations)
