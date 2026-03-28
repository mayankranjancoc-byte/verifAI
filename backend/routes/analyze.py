"""
/api/analyze — Main analysis endpoint.
Accepts text, URL, or file uploads. Runs the full verification pipeline.
Inspired by ARG (AAAI 2024) pipeline: extract claims → retrieve evidence → generate verdict.
"""

import os
import json
import tempfile
import traceback
from fastapi import APIRouter, UploadFile, File, Form
from typing import Optional

from pipeline.claim_extractor import extract_claims
from pipeline.evidence_retriever import retrieve_evidence
from pipeline.verdict_engine import generate_verdict
from pipeline.humor_generator import generate_humor
from pipeline.emotion_analyzer import analyze_emotion
from pipeline.multimodal_analyzer import analyze_multimodal
from utils.url_scraper import scrape_url

router = APIRouter()


@router.post("/analyze")
async def analyze(
    content: str = Form(""),
    file: Optional[UploadFile] = File(None)
):
    """
    Main analysis endpoint.
    - content: text, URL, or claim to verify
    - file: optional image, audio, or video file
    """
    try:
        raw_text = content.strip()
        file_data = None
        file_type = None
        original_query = raw_text

        # 1. Handle file upload
        if file:
            file_bytes = await file.read()
            file_type = file.content_type or ""
            suffix = os.path.splitext(file.filename)[1] if file.filename else ""
            
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
            tmp.write(file_bytes)
            tmp.close()
            file_data = {
                "path": tmp.name,
                "type": file_type,
                "name": file.filename,
                "bytes": file_bytes
            }

        # 2. Handle URL input
        if raw_text and is_url(raw_text):
            scraped = await scrape_url(raw_text)
            if scraped:
                raw_text = f"[Source URL: {original_query}]\n\n{scraped['title']}\n\n{scraped['text']}"
            else:
                raw_text = f"[URL provided but could not be scraped: {original_query}]"

        # 3. Handle multimodal content
        multimodal_report = None
        if file_data:
            multimodal_report = await analyze_multimodal(raw_text, file_data)
            if multimodal_report and multimodal_report.get("transcription"):
                raw_text = f"{raw_text}\n\n[Transcription from uploaded media]:\n{multimodal_report['transcription']}"

        # 4. Extract claims (ARG-inspired: use LLM as advisor)
        claims = await extract_claims(raw_text)

        # 5. Retrieve evidence (fact-check APIs + web search)
        evidence = await retrieve_evidence(claims, original_query)

        # 6. Generate verdict + reality score + heatmap + trust trail
        verdict_result = await generate_verdict(
            raw_text, claims, evidence, multimodal_report
        )

        # 7. Analyze emotional manipulation
        emotion = await analyze_emotion(raw_text)

        # 8. Generate Hinglish humor
        humor = await generate_humor(
            raw_text,
            verdict_result.get("verdict", "UNVERIFIED"),
            claims
        )

        # 9. Compose final response
        response = {
            "verdict": verdict_result.get("verdict", "UNVERIFIED"),
            "reality_score": verdict_result.get("reality_score", 50),
            "claims": verdict_result.get("claims", []),
            "context_drift": verdict_result.get("context_drift", {"detected": False}),
            "key_insights": verdict_result.get("key_insights", []),
            "trust_trail": verdict_result.get("trust_trail", []),
            "emotion_analysis": emotion,
            "humor": humor,
            "sources": evidence.get("sources", []),
            "_originalQuery": original_query,
        }

        # Clean up temp file
        if file_data and os.path.exists(file_data["path"]):
            os.unlink(file_data["path"])

        return response

    except Exception as e:
        traceback.print_exc()
        return {
            "verdict": "ERROR",
            "reality_score": 0,
            "claims": [],
            "context_drift": {"detected": False},
            "key_insights": [{"icon": "error", "text": f"Analysis error: {str(e)}"}],
            "trust_trail": [],
            "emotion_analysis": {"intensity": 0, "label": ""},
            "humor": {"joke": "", "explanation": ""},
            "sources": [],
            "_originalQuery": content,
        }


def is_url(text: str) -> bool:
    return text.startswith("http://") or text.startswith("https://")
