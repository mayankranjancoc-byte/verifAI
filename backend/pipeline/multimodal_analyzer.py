"""
Multimodal Analyzer — Handles image, audio, and video content.
Uses Gemini multimodal for:
- Image/text consistency checking (inspired by MM-FakeNews-Detection)
- Image manipulation detection
- Audio transcription analysis
- Video frame consistency
"""

import os
import base64
from pipeline.gemini_client import generate_with_fallback, parse_json_response


IMAGE_ANALYSIS_PROMPT = """You are a forensic media analyst. Analyze this image in the context of the following text claim.

Text claim: {text}

Examine the image for:
1. Does the image match the text claim? (consistency check)
2. Signs of manipulation (splicing, cloning, face swapping, text overlay edits)
3. Metadata clues (watermarks, compression artifacts suggesting re-sharing)
4. Whether this looks like a stock photo, screenshot, or original photograph
5. Any signs this image is from a different time period or context than claimed

Respond in JSON (no markdown):
{{
  "image_text_match": true|false,
  "manipulation_detected": true|false,
  "manipulation_details": "description if detected, else empty",
  "image_type": "original|screenshot|stock|meme|edited",
  "context_notes": "any relevant observations about the image context",
  "confidence": 0.0-1.0
}}
"""

AUDIO_ANALYSIS_PROMPT = """Transcribe and analyze this audio content.

1. Provide a text transcription
2. Note the language(s) used
3. Identify any claims being made
4. Note if the audio appears edited, spliced, or manipulated

Respond in JSON (no markdown):
{{
  "transcription": "full transcription text",
  "language": "detected language",
  "claims_in_audio": ["claim1", "claim2"],
  "manipulation_detected": true|false,
  "notes": "any relevant observations"
}}
"""


async def analyze_multimodal(text: str, file_data: dict) -> dict:
    """Analyze uploaded media files for misinformation signals."""
    if not file_data:
        return None

    file_type = file_data.get("type", "")
    file_bytes = file_data.get("bytes", b"")
    
    if not file_bytes:
        return None

    try:
        if file_type.startswith("image"):
            return await _analyze_image(text, file_bytes, file_type)
        elif file_type.startswith("audio"):
            return await _analyze_audio(file_bytes, file_type)
        elif file_type.startswith("video"):
            return await _analyze_video(text, file_bytes, file_type)
        else:
            return None

    except Exception as e:
        print(f"[MultimodalAnalyzer] Error: {e}")
        return {"error": str(e), "transcription": None}


async def _analyze_image(text: str, image_bytes: bytes, mime_type: str) -> dict:
    """Analyze image for manipulation and text-image consistency."""
    try:
        image_part = {
            "inline_data": {
                "mime_type": mime_type,
                "data": base64.b64encode(image_bytes).decode("utf-8")
            }
        }

        raw = await generate_with_fallback(
            IMAGE_ANALYSIS_PROMPT.format(text=text[:500]),
            temperature=0.1,
            max_tokens=1000,
            multimodal_parts=[image_part],
        )

        result = parse_json_response(raw)
        result["type"] = "image"
        result["transcription"] = None
        return result

    except Exception as e:
        print(f"[MultimodalAnalyzer] Image analysis error: {e}")
        return {"type": "image", "error": str(e), "transcription": None}


async def _analyze_audio(audio_bytes: bytes, mime_type: str) -> dict:
    """Transcribe and analyze audio content."""
    try:
        audio_part = {
            "inline_data": {
                "mime_type": mime_type,
                "data": base64.b64encode(audio_bytes).decode("utf-8")
            }
        }

        raw = await generate_with_fallback(
            AUDIO_ANALYSIS_PROMPT,
            temperature=0.1,
            max_tokens=2000,
            multimodal_parts=[audio_part],
        )

        result = parse_json_response(raw)
        result["type"] = "audio"
        return result

    except Exception as e:
        print(f"[MultimodalAnalyzer] Audio analysis error: {e}")
        return {"type": "audio", "error": str(e), "transcription": None}


async def _analyze_video(text: str, video_bytes: bytes, mime_type: str) -> dict:
    """Analyze video content — uses Gemini's video understanding."""
    try:
        video_part = {
            "inline_data": {
                "mime_type": mime_type,
                "data": base64.b64encode(video_bytes).decode("utf-8")
            }
        }

        prompt = f"""Analyze this video in the context of the claim: "{text[:300]}"

1. Transcribe any speech in the video
2. Check if the video content matches the text claim
3. Detect any signs of editing or manipulation
4. Note the visual content and context

Respond in JSON (no markdown):
{{{{
  "transcription": "speech transcription if any",
  "video_text_match": true|false,
  "manipulation_detected": true|false,
  "notes": "observations",
  "confidence": 0.0-1.0
}}}}"""

        raw = await generate_with_fallback(
            prompt,
            temperature=0.1,
            max_tokens=2000,
            multimodal_parts=[video_part],
        )

        result = parse_json_response(raw)
        result["type"] = "video"
        return result

    except Exception as e:
        print(f"[MultimodalAnalyzer] Video analysis error: {e}")
        return {"type": "video", "error": str(e), "transcription": None}
