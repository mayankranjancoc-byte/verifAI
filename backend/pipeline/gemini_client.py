"""
Shared AI client with Gemini primary + OpenRouter fallback.
Uses Gemini REST API directly (no heavy SDK) to stay under Vercel's 250MB limit.
Handles rate limits by trying Gemini first, then falling back to OpenRouter.
"""

import os
import json
import httpx

# Gemini REST API config
GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
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


async def _try_gemini(prompt_text, temperature, max_tokens, multimodal_parts=None):
    """Try Gemini models via REST API. Returns response text or raises."""
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        raise Exception("Gemini not configured — GEMINI_API_KEY missing")

    # Build content parts
    parts = [{"text": prompt_text}]
    if multimodal_parts:
        for part in multimodal_parts:
            if isinstance(part, dict):
                parts.append(part)
            elif hasattr(part, 'mime_type'):
                # Handle legacy genai Image/Part objects (local dev only)
                parts.append({"text": str(part)})

    payload = {
        "contents": [{"parts": parts}],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
        }
    }

    for model_name in GEMINI_MODELS:
        url = f"{GEMINI_API_BASE}/{model_name}:generateContent?key={api_key}"
        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                resp = await client.post(url, json=payload)

                if resp.status_code == 429:
                    print(f"[AI] Gemini {model_name} rate-limited, trying next...")
                    continue

                if resp.status_code != 200:
                    print(f"[AI] Gemini {model_name} error {resp.status_code}: {resp.text[:300]}")
                    continue

                data = resp.json()
                candidates = data.get("candidates", [])
                if candidates:
                    content = candidates[0].get("content", {})
                    text_parts = content.get("parts", [])
                    if text_parts:
                        return text_parts[0].get("text", "").strip()

                print(f"[AI] Gemini {model_name} returned no content")
                continue

        except Exception as e:
            print(f"[AI] Gemini {model_name} exception: {e}")
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
        "HTTP-Referer": "https://verifai-app.vercel.app",
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
    Generate content: try Gemini REST API first, then OpenRouter fallback.
    Returns the raw response text.
    """
    # 1. Try Gemini (supports multimodal via REST)
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
