"""
/api/analyze — Main analysis endpoint.
Accepts text, URL, or file uploads. Runs the full verification pipeline.
Pipeline: Extract claims → Verify via real APIs → Score deterministically →
          Analyze emotion exploit → Generate reasoning → Humor (if not sensitive)
"""

import os
import json
import tempfile
import traceback
from datetime import datetime, timezone
from fastapi import APIRouter, UploadFile, File, Form
from typing import Optional

from pipeline.claim_extractor import extract_claims
from pipeline.verifier import verify_claims
from pipeline.score_calculator import compute_reality_score, compute_verdict
from pipeline.verdict_engine import generate_verdict
from pipeline.emotion_exploit_analyzer import analyze_emotion_exploit
from pipeline.humor_generator import generate_humor
from pipeline.multimodal_analyzer import analyze_multimodal
from pipeline.file_processor import process_file
from utils.url_scraper import scrape_url

router = APIRouter()


@router.post("/analyze")
async def analyze(
    content: str = Form(""),
    file: Optional[UploadFile] = File(None),
    reanalyze: str = Form(""),  # If set, contains cached claims JSON
):
    """
    Main analysis endpoint.
    - content: text, URL, or claim to verify
    - file: optional image, audio, video, PDF, or text file
    - reanalyze: if provided, skip claim extraction and use cached claims
    """
    try:
        raw_text = content.strip()
        file_data = None
        file_analysis = None
        original_query = raw_text
        timestamp = datetime.now(timezone.utc).isoformat()

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

            # Process file (PDF, image OCR, text extraction)
            file_analysis = await process_file(file_data)
            if file_analysis and file_analysis.get("extracted_text"):
                extracted = file_analysis["extracted_text"]
                if raw_text:
                    raw_text = f"{raw_text}\n\n[Extracted from {file.filename}]:\n{extracted}"
                else:
                    raw_text = extracted

        # 2. Handle URL input
        if raw_text and is_url(raw_text):
            scraped = await scrape_url(raw_text)
            if scraped:
                raw_text = f"[Source URL: {original_query}]\n\n{scraped['title']}\n\n{scraped['text']}"
            else:
                raw_text = f"[URL provided but could not be scraped: {original_query}]"

        # 3. Handle multimodal content (image/audio/video analysis)
        multimodal_report = None
        if file_data and file_data.get("type", "").startswith(("image", "audio", "video")):
            multimodal_report = await analyze_multimodal(raw_text, file_data)
            if multimodal_report and multimodal_report.get("transcription"):
                raw_text = f"{raw_text}\n\n[Transcription from uploaded media]:\n{multimodal_report['transcription']}"

        # 4. Extract claims (use cached if re-analyzing)
        if reanalyze:
            try:
                claims = json.loads(reanalyze)
            except Exception:
                claims = await extract_claims(raw_text)
        else:
            claims = await extract_claims(raw_text)

        # 5. Verify claims against REAL external APIs
        verification = await verify_claims(claims, original_query)

        # 6. Analyze emotional exploitation (5 tactics)
        emotion_exploit = await analyze_emotion_exploit(raw_text)

        # 7. Compute deterministic reality score
        score_result = compute_reality_score(
            verification.get("verified_claims", []),
            emotion_exploit.get("overall_manipulation_score", 0),
        )
        reality_score = score_result["reality_score"]
        verdict = compute_verdict(reality_score)

        # 8. Generate LLM reasoning (context, highlights, insights — NOT the score)
        verdict_result = await generate_verdict(
            raw_text, claims, verification, emotion_exploit, multimodal_report
        )

        # 9. Generate Hinglish humor (suppressed if sensitive)
        sensitive = emotion_exploit.get("sensitive_topic", False)
        sensitivity_reason = emotion_exploit.get("sensitivity_reason", "")
        humor = await generate_humor(
            raw_text, verdict, claims,
            sensitive=sensitive,
            sensitivity_reason=sensitivity_reason,
        )

        # 10. Build trust trail from real sources
        trust_trail = verdict_result.get("trust_trail", [])
        # Merge in real source URLs from verification
        for src in verification.get("sources", [])[:6]:
            if src.get("url") and not any(t.get("url") == src["url"] for t in trust_trail):
                trust_trail.append({
                    "name": src.get("source", "Source"),
                    "stance": src.get("stance", "neutral"),
                    "url": src.get("url", ""),
                    "excerpt": src.get("excerpt", ""),
                })

        # 11. Compose final response (full schema)
        response = {
            "verdict": verdict,
            "reality_score": reality_score,
            "score_breakdown": {
                "formula": score_result.get("formula", ""),
                "claims_average": score_result.get("claims_average", 0),
                "manipulation_penalty": score_result.get("manipulation_penalty", 0),
                "per_claim_scores": score_result.get("per_claim_scores", []),
            },
            "claims": verdict_result.get("claims", []),
            "verified_claims": verification.get("verified_claims", []),
            "context_drift": verdict_result.get("context_drift", {"detected": False}),
            "key_insights": verdict_result.get("key_insights", []),
            "trust_trail": trust_trail[:8],
            "emotion_exploit": {
                "overall_manipulation_score": emotion_exploit.get("overall_manipulation_score", 0),
                "sensitive_topic": sensitive,
                "tactics": emotion_exploit.get("tactics", {}),
            },
            "emotion_analysis": {
                "intensity": emotion_exploit.get("overall_manipulation_score", 0),
                "label": _build_emotion_label(emotion_exploit),
            },
            "humor": humor,
            "file_analysis": file_analysis,
            "sources": [
                {"name": s.get("source", ""), "url": s.get("url", "")}
                for s in verification.get("sources", [])[:8]
                if s.get("url")
            ],
            "analysis_timestamp": timestamp,
            "verification_method": "multi-source-api",
            "_originalQuery": original_query,
            "_cached_claims": json.dumps(claims),  # For re-analyze
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
            "score_breakdown": {"formula": "", "claims_average": 0, "manipulation_penalty": 0, "per_claim_scores": []},
            "claims": [],
            "verified_claims": [],
            "context_drift": {"detected": False},
            "key_insights": [{"icon": "error", "text": f"Analysis error: {str(e)}"}],
            "trust_trail": [],
            "emotion_exploit": {"overall_manipulation_score": 0, "tactics": {}},
            "emotion_analysis": {"intensity": 0, "label": ""},
            "humor": {"joke": "", "explanation": "", "suppressed": False},
            "file_analysis": None,
            "sources": [],
            "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
            "verification_method": "error",
            "_originalQuery": content,
        }


def is_url(text: str) -> bool:
    return text.startswith("http://") or text.startswith("https://")


@router.post("/reverify")
async def reverify(
    content: str = Form(""),
    cached_claims: str = Form(""),
):
    """
    Re-verify endpoint: skips Gemini claim extraction entirely.
    Takes cached claims and re-queries ONLY external APIs for fresh results.
    Makes re-analyze deterministically useful (no LLM re-roll).
    """
    try:
        timestamp = datetime.now(timezone.utc).isoformat()

        # Parse cached claims
        try:
            claims = json.loads(cached_claims) if cached_claims else []
        except Exception:
            claims = []

        if not claims:
            return {
                "verdict": "ERROR",
                "reality_score": 0,
                "error": "No cached claims provided for re-verification",
                "analysis_timestamp": timestamp,
            }

        # Re-verify against real APIs (skip Gemini entirely)
        verification = await verify_claims(claims, content)

        # Recompute deterministic score (re-use existing emotion if available)
        score_result = compute_reality_score(
            verification.get("verified_claims", []),
            0,  # No emotion re-analysis on reverify
        )
        reality_score = score_result["reality_score"]
        verdict = compute_verdict(reality_score)

        # Build trust trail from real sources
        trust_trail = []
        for src in verification.get("sources", [])[:8]:
            if src.get("url"):
                trust_trail.append({
                    "name": src.get("source", "Source"),
                    "stance": src.get("stance", "neutral"),
                    "url": src.get("url", ""),
                    "excerpt": src.get("excerpt", ""),
                })

        return {
            "verdict": verdict,
            "reality_score": reality_score,
            "score_breakdown": {
                "formula": score_result.get("formula", ""),
                "claims_average": score_result.get("claims_average", 0),
                "manipulation_penalty": 0,
                "per_claim_scores": score_result.get("per_claim_scores", []),
            },
            "verified_claims": verification.get("verified_claims", []),
            "trust_trail": trust_trail,
            "sources": [
                {"name": s.get("source", ""), "url": s.get("url", "")}
                for s in verification.get("sources", [])[:8]
                if s.get("url")
            ],
            "analysis_timestamp": timestamp,
            "verification_method": "reverify-api-only",
            "_originalQuery": content,
            "_cached_claims": cached_claims,
        }

    except Exception as e:
        traceback.print_exc()
        return {
            "verdict": "ERROR",
            "reality_score": 0,
            "error": str(e),
            "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
        }


def _build_emotion_label(exploit: dict) -> str:
    """Build a human-readable label from tactics."""
    tactics = exploit.get("tactics", {})
    top_tactics = sorted(
        [(name, data.get("score", 0)) for name, data in tactics.items()],
        key=lambda x: x[1],
        reverse=True,
    )
    active = [(n.replace("_", " ").title(), s) for n, s in top_tactics if s >= 4]
    if not active:
        return "Low manipulation detected"
    return ", ".join(f"{name} ({score}/10)" for name, score in active[:3])
