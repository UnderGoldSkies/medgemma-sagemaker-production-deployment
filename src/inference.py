import os
import json
import base64
from io import BytesIO
from typing import Dict, Any

import torch
from transformers import AutoModelForImageTextToText, AutoProcessor
from PIL import Image


def model_fn(model_dir: str):
    """
    Called once when the container starts.
    Loads MedGemma-4b-it from Hugging Face using HF_MODEL_ID + HF_TOKEN.
    """
    model_id = os.getenv("HF_MODEL_ID", "google/medgemma-4b-it")
    hf_token = os.getenv("HF_TOKEN")

    device = "cuda" if torch.cuda.is_available() else "cpu"

    model = AutoModelForImageTextToText.from_pretrained(
        model_id,
        torch_dtype=torch.bfloat16 if device == "cuda" else torch.float32,
        device_map="auto" if device == "cuda" else None,
        token=hf_token,
    )

    processor = AutoProcessor.from_pretrained(model_id, token=hf_token)

    return {"model": model, "processor": processor}


def input_fn(request_body: str, request_content_type: str) -> Dict[str, Any]:
    """
    Deserialize input data and prepare for prediction.
    Handles both text-only and image+text requests.
    """
    if request_content_type != "application/json":
        raise ValueError(f"Unsupported content type: {request_content_type}")

    data = json.loads(request_body)
    messages = data.get("messages", [])

    # Process messages to decode base64 images to PIL Images
    processed_messages = []

    for message in messages:
        processed_content = []

        if isinstance(message.get("content"), list):
            for item in message["content"]:
                if item.get("type") == "image":
                    # Decode base64 image to PIL Image
                    image_data = base64.b64decode(item["image"])
                    pil_image = Image.open(BytesIO(image_data))

                    # Put the actual PIL Image in the message (like Google Colab)
                    processed_content.append({
                        "type": "image",
                        "image": pil_image  # ← Actual PIL Image, not base64
                    })
                else:
                    processed_content.append(item)
        else:
            processed_content = message["content"]

        processed_messages.append({
            "role": message["role"],
            "content": processed_content
        })

    return {
        "messages": processed_messages,
        "max_new_tokens": data.get("max_new_tokens", 200)
    }


def predict_fn(data, model_dict):
    """
    Apply model to the incoming request
    """
    processor = model_dict["processor"]
    model_instance = model_dict["model"]

    # Extract data prepared by input_fn
    messages = data["messages"]
    max_new_tokens = data.get("max_new_tokens", 200)

    # Check if there are images in the messages
    has_images = any(
        isinstance(msg.get("content"), list) and
        any(item.get("type") == "image" for item in msg["content"])
        for msg in messages
    )

    # Apply chat template
    if has_images:
        # For image+text: apply_chat_template handles PIL Images in messages
        inputs = processor.apply_chat_template(
            messages,
            add_generation_prompt=True,
            tokenize=True,
            return_dict=True,
            return_tensors="pt",
        )
    else:
        # For text-only: use chat template
        text_prompt = processor.apply_chat_template(
            messages,
            add_generation_prompt=True,
            tokenize=False,
        )
        inputs = processor.tokenizer(
            text_prompt,
            return_tensors="pt",
        )

    # Move to GPU if available
    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.bfloat16 if device == "cuda" else torch.float32

    # For image inputs, also move dtype
    if has_images:
        inputs = inputs.to(device, dtype=dtype)
    else:
        inputs = {k: v.to(device) for k, v in inputs.items()}

    # Generate
    with torch.inference_mode():
        outputs = model_instance.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
        )

    # Decode output (remove the input tokens)
    input_len = inputs["input_ids"].shape[-1]
    generation = outputs[0][input_len:]
    generated_text = processor.decode(generation, skip_special_tokens=True)

    return {"generated_text": generated_text}


def output_fn(prediction: Dict[str, Any], response_content_type: str):
    """
    Serialize prediction output back to JSON.
    """
    body = json.dumps(prediction)
    return body, "application/json"
