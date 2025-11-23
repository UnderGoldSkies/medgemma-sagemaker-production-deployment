import os
import json
import base64
from io import BytesIO
from typing import Dict, Any

import torch
from transformers import AutoModelForImageTextToText, AutoProcessor, TextIteratorStreamer
from PIL import Image
from threading import Thread

# Global variables for model caching
MODEL_CACHE = None


def model_fn(model_dir: str):
    """
    Called once when the container starts.
    Loads MedGemma-4b-it from Hugging Face using HF_MODEL_ID + HF_TOKEN.
    """
    global MODEL_CACHE

    if MODEL_CACHE is not None:
        return MODEL_CACHE

    model_id = os.getenv("HF_MODEL_ID", "google/medgemma-4b-it")
    hf_token = os.getenv("HF_TOKEN")

    device = "cuda" if torch.cuda.is_available() else "cpu"

    print(f"Loading model: {model_id}")
    print(f"Device: {device}")

    # Load with optimizations
    model = AutoModelForImageTextToText.from_pretrained(
        model_id,
        torch_dtype=torch.bfloat16 if device == "cuda" else torch.float32,
        device_map="auto" if device == "cuda" else None,
        token=hf_token,
        low_cpu_mem_usage=True,  # Optimize memory
    )

    # Enable optimizations
    if device == "cuda":
        model = model.eval()  # Set to eval mode
        torch.backends.cudnn.benchmark = True  # Optimize CUDA

    processor = AutoProcessor.from_pretrained(model_id, token=hf_token)

    MODEL_CACHE = {"model": model, "processor": processor}
    print("✅ Model loaded successfully")

    return MODEL_CACHE


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

                    # Resize large images for faster processing
                    max_size = 1024
                    if max(pil_image.size) > max_size:
                        pil_image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

                    processed_content.append({
                        "type": "image",
                        "image": pil_image
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
        "max_new_tokens": min(
            data.get("max_new_tokens", int(os.getenv("MAX_NEW_TOKENS", "1024"))),
            2048,
        ),  # Cap at 2048
        "stream": data.get("stream", False),
        "temperature": data.get("temperature", 0.7),
        "top_p": data.get("top_p", 0.9),
        "do_sample": data.get("do_sample", True),
    }


def predict_fn(data, model_dict):
    """
    Apply model to the incoming request
    Supports both streaming and non-streaming responses
    """
    processor = model_dict["processor"]
    model_instance = model_dict["model"]

    messages = data["messages"]
    max_new_tokens = data.get("max_new_tokens", 1024)
    stream = data.get("stream", False)
    temperature = data.get("temperature", 0.7)
    top_p = data.get("top_p", 0.9)
    do_sample = data.get("do_sample", True)

    # Check if there are images
    has_images = any(
        isinstance(msg.get("content"), list) and
        any(item.get("type") == "image" for item in msg["content"])
        for msg in messages
    )

    # Apply chat template
    if has_images:
        inputs = processor.apply_chat_template(
            messages,
            add_generation_prompt=True,
            tokenize=True,
            return_dict=True,
            return_tensors="pt",
        )
    else:
        text_prompt = processor.apply_chat_template(
            messages,
            add_generation_prompt=True,
            tokenize=False,
        )
        inputs = processor.tokenizer(
            text_prompt,
            return_tensors="pt",
        )

    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.bfloat16 if device == "cuda" else torch.float32

    if has_images:
        inputs = inputs.to(device, dtype=dtype)
    else:
        inputs = {k: v.to(device) for k, v in inputs.items()}

    input_len = inputs["input_ids"].shape[-1]

    # Generation parameters - optimized for speed
    generation_kwargs = {
        "max_new_tokens": max_new_tokens,
        "do_sample": do_sample,
        "temperature": temperature if do_sample else None,
        "top_p": top_p if do_sample else None,
        "pad_token_id": processor.tokenizer.eos_token_id,
        "use_cache": True,
    }

    if stream:
        # Streaming response
        streamer = TextIteratorStreamer(
            processor.tokenizer,
            skip_prompt=True,
            skip_special_tokens=True,
            timeout=300.0
        )

        generation_kwargs["streamer"] = streamer

        # Run generation in a separate thread
        thread = Thread(
            target=model_instance.generate,
            kwargs={**inputs, **generation_kwargs}
        )
        thread.start()

        def generate_stream():
            try:
                for text in streamer:
                    yield text
            except Exception as e:
                print(f"Streaming error: {e}")
                yield f"[Error: {str(e)}]"

        return {"stream": generate_stream(), "is_streaming": True}

    else:
        # Non-streaming response with timeout protection
        try:
            with torch.inference_mode():
                outputs = model_instance.generate(
                    **inputs,
                    **generation_kwargs
                )

            generation = outputs[0][input_len:]
            generated_text = processor.decode(generation, skip_special_tokens=True)

            return {"generated_text": generated_text, "is_streaming": False}

        except Exception as e:
            print(f"Generation error: {e}")
            return {
                "generated_text": f"Error during generation: {str(e)}",
                "is_streaming": False
            }


def output_fn(prediction: Dict[str, Any], response_content_type: str):
    """
    Serialize prediction output back to JSON or stream.
    """
    if prediction.get("is_streaming"):
        def stream_response():
            try:
                for chunk in prediction["stream"]:
                    yield f"data: {json.dumps({'text': chunk})}\n\n"
                yield "data: [DONE]\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"

        return stream_response(), "text/event-stream"

    body = json.dumps({"generated_text": prediction["generated_text"]})
    return body, "application/json"
