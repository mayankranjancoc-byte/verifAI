"""
Shared AI client with Gemini primary + OpenRouter fallback.
Handles rate limits by trying Gemini first, then falling back to OpenRouter.
"""

import os
import time
import json
import httpx
import google.generativeai as genai

_configured = False
_models = {}

# Gemini models to try first
GEMINI_MODELS = [
    "gemini-2.0-flash-lite",
    "gemini-2.0-flash",
]

# OpenRouter models to try as fallback (free)
OPENROUTER_MODELS = [
    "google/gemini-3-flash-preview",
    "meta-llama/llama-3.3-70b-instruct:free",
    "mistralai/mistral-small-3.1-24b-instruct:free",
    "google/gemma-3-27b-it:free",
]

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MAX_RETRIES = 1
RETRY_DELAY = 2


def _configure_gemini():
    global _configured
    if not _configured:
        api_key = os.environ.get("GEMINI_API_KEY", "")
        if api_key:
            genai.configure(api_key=api_key)
            _configured = True


def get_gemini_model(model_name: str):
    """Get a cached Gemini model instance."""
    _configure_gemini()
    if model_name not in _models:
        _models[model_name] = genai.GenerativeModel(model_name)
    return _models[model_name]


async def _try_gemini(prompt_text, temperature, max_tokens, multimodal_parts=None):
    """Try Gemini models. Returns response text or raises on all failures."""
    _configure_gemini()
    if not _configured:
        raise Exception("Gemini not configured")

    content = [prompt_text]
    if multimodal_parts:
        content = [prompt_text] + multimodal_parts

    for model_name in GEMINI_MODELS:
        try:
            model = get_gemini_model(model_name)
            response = model.generate_content(
                content,
                generation_config=genai.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                )
            )
            return response.text.strip()
        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "quota" in err_str.lower():
                print(f"[AI] Gemini {model_name} rate-limited, trying next...")
                continue
            else:
                print(f"[AI] Gemini {model_name} error: {e}")
                continue

    raise Exception("All Gemini models exhausted or rate-limited")


async def _try_openrouter(prompt_text, temperature, max_tokens):
    """Try OpenRouter models as fallback. Returns response text."""
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key:
        raise Exception("OPENROUTER_API_KEY not set")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:5173",
        "X-Title": "VerifAI",
    }

    for model_name in OPENROUTER_MODELS:
        try:
            payload = {
                "model": model_name,
                "messages": [
                    {"role": "user", "content": prompt_text}
                ],
                "temperature": temperature,
                "max_tokens": max_tokens,
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(OPENROUTER_URL, headers=headers, json=payload)

                if resp.status_code == 429:
                    print(f"[AI] OpenRouter {model_name} rate-limited, trying next...")
                    continue

                if resp.status_code != 200:
                    print(f"[AI] OpenRouter {model_name} error {resp.status_code}: {resp.text[:200]}")
                    continue

                data = resp.json()
                choices = data.get("choices", [])
                if choices:
                    return choices[0].get("message", {}).get("content", "").strip()
                else:
                    print(f"[AI] OpenRouter {model_name} returned no choices")
                    continue

        except Exception as e:
            print(f"[AI] OpenRouter {model_name} exception: {e}")
            continue

    raise Exception("All OpenRouter models exhausted")


async def generate_with_fallback(
    prompt,
    temperature=0.2,
    max_tokens=2000,
    multimodal_parts=None,
):
    """
    Generate content: try Gemini first, then OpenRouter fallback.
    Returns the raw response text.
    """
    # 1. Try Gemini (supports multimodal)
    try:
        return await _try_gemini(prompt, temperature, max_tokens, multimodal_parts)
    except Exception as gemini_err:
        print(f"[AI] Gemini failed: {gemini_err}")

    # 2. Fallback to OpenRouter (text-only)
    if multimodal_parts:
        print("[AI] OpenRouter fallback does not support multimodal, using text-only prompt")

    try:
        return await _try_openrouter(prompt, temperature, max_tokens)
    except Exception as or_err:
        print(f"[AI] OpenRouter also failed: {or_err}")
        raise or_err


def parse_json_response(raw):
    """Parse a JSON response, stripping markdown fences."""
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()
    if text.startswith("json"):
        text = text[4:].strip()
    return json.loads(text)
