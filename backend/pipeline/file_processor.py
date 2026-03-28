"""
File Processor — Handles PDF, image, and text file extraction.
- PDF: PyMuPDF (fitz) text extraction
- Images: Gemini Vision OCR + manipulation detection
- .txt: Direct text extraction
"""

import os
import base64

try:
    import fitz  # PyMuPDF
    HAS_FITZ = True
except ImportError:
    HAS_FITZ = False
    print("[FileProcessor] PyMuPDF not installed — PDF support disabled. Install with: pip install PyMuPDF")

from pipeline.gemini_client import generate_with_fallback, parse_json_response


async def process_file(file_data: dict) -> dict:
    """
    Process uploaded file and extract text + analysis.

    Args:
        file_data: {path, type, name, bytes}

    Returns:
        {
            file_type: "pdf|image|text",
            extracted_text: "...",
            image_analysis: {...} | null
        }
    """
    file_type = file_data.get("type", "")
    file_bytes = file_data.get("bytes", b"")
    file_name = file_data.get("name", "")

    if not file_bytes:
        return {"file_type": "unknown", "extracted_text": "", "image_analysis": None}

    if file_type == "application/pdf" or file_name.endswith(".pdf"):
        return await _process_pdf(file_data)
    elif file_type.startswith("image"):
        return await _process_image(file_bytes, file_type)
    elif file_type in ("text/plain",) or file_name.endswith(".txt"):
        return _process_text(file_bytes)
    else:
        return {"file_type": "unknown", "extracted_text": "", "image_analysis": None}


async def _process_pdf(file_data: dict) -> dict:
    """Extract text from PDF using PyMuPDF."""
    if not HAS_FITZ:
        return {
            "file_type": "pdf",
            "extracted_text": "[PDF processing unavailable — PyMuPDF not installed]",
            "image_analysis": None,
        }

    try:
        path = file_data.get("path", "")
        if not path or not os.path.exists(path):
            # Try from bytes
            import tempfile
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
            tmp.write(file_data.get("bytes", b""))
            tmp.close()
            path = tmp.name

        doc = fitz.open(path)
        text_parts = []
        for page in doc:
            text_parts.append(page.get_text())
        doc.close()

        full_text = "\n\n".join(text_parts).strip()

        return {
            "file_type": "pdf",
            "extracted_text": full_text[:10000],  # Cap at 10k chars
            "image_analysis": None,
            "page_count": len(text_parts),
        }

    except Exception as e:
        print(f"[FileProcessor] PDF error: {e}")
        return {
            "file_type": "pdf",
            "extracted_text": f"[PDF extraction error: {str(e)}]",
            "image_analysis": None,
        }


async def _process_image(image_bytes: bytes, mime_type: str) -> dict:
    """Use Gemini Vision for OCR + manipulation detection."""
    try:
        image_part = {
            "inline_data": {
                "mime_type": mime_type,
                "data": base64.b64encode(image_bytes).decode("utf-8")
            }
        }

        prompt = """Analyze this image:
1. Extract ALL text visible in the image (OCR) — include social media posts, headlines, captions, watermarks
2. Check for signs of manipulation (text overlays that look pasted, mismatched fonts, compression artifacts around text, signs of Photoshop/editing)
3. Note the image type (screenshot, photo, meme, infographic, etc.)

Respond in JSON only (no markdown):
{
  "extracted_text": "all text visible in the image",
  "is_potentially_manipulated": true|false,
  "manipulation_indicators": ["indicator1", "indicator2"],
  "image_type": "screenshot|photo|meme|infographic|edited",
  "metadata_anomalies": ["any suspicious observations"]
}"""

        raw = await generate_with_fallback(
            prompt,
            temperature=0.1,
            max_tokens=1500,
            multimodal_parts=[image_part],
        )

        data = parse_json_response(raw)

        return {
            "file_type": "image",
            "extracted_text": data.get("extracted_text", ""),
            "image_analysis": {
                "is_potentially_manipulated": data.get("is_potentially_manipulated", False),
                "manipulation_indicators": data.get("manipulation_indicators", []),
                "image_type": data.get("image_type", "unknown"),
                "metadata_anomalies": data.get("metadata_anomalies", []),
            }
        }

    except Exception as e:
        print(f"[FileProcessor] Image error: {e}")
        return {
            "file_type": "image",
            "extracted_text": "",
            "image_analysis": {"error": str(e)},
        }


def _process_text(file_bytes: bytes) -> dict:
    """Extract text from .txt file."""
    try:
        text = file_bytes.decode("utf-8", errors="replace")
        return {
            "file_type": "text",
            "extracted_text": text[:10000],
            "image_analysis": None,
        }
    except Exception as e:
        return {
            "file_type": "text",
            "extracted_text": f"[Text extraction error: {str(e)}]",
            "image_analysis": None,
        }
