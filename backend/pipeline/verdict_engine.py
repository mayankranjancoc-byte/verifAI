"""
Verdict Engine — Combines all signals into a final verdict.
Now uses REAL external API evidence for scoring (via score_calculator).
LLM is only used for reasoning explanation, heatmap highlights, and context drift.
NOT for the actual reality score.
"""

import json
from pipeline.gemini_client import generate_with_fallback, parse_json_response


REASONING_PROMPT = """You are a senior fact-check analyst. Based on the evidence below, provide analysis and explanation.

ORIGINAL CONTENT:
---
{content}
---

EXTRACTED CLAIMS:
{claims_json}

REAL VERIFICATION RESULTS (from external APIs):
{verification_json}

EMOTION EXPLOIT ANALYSIS:
{emotion_json}

YOUR TASK:
1. Explain WHY each claim is confirmed or contradicted based on the real evidence
2. Detect any context drift (old content presented as new, out-of-context usage)
3. Generate highlighted text spans showing risky phrases with risk scores (0.0-1.0)
4. List key intelligence insights backed by the evidence
5. Build a trust trail with real source names and URLs

IMPORTANT: The reality score is already computed mathematically from external sources.
You are providing the REASONING and CONTEXT, not the score.
Use the verification_results to justify your analysis.

Respond in JSON only (no markdown):
{{
  "reasoning": "brief explanation of the overall verdict",
  "claims": [
    {{
      "text": "the claim text",
      "highlights": [
        {{
          "word": "suspicious_word_or_phrase",
          "risk": 0.0-1.0,
          "reason": "why flagged"
        }}
      ],
      "virality_spike": "description or null"
    }}
  ],
  "context_drift": {{
    "detected": true|false,
    "message": "explanation if detected",
    "original_date": "YYYY-MM-DD or null"
  }},
  "key_insights": [
    {{
      "icon": "check|warning|error",
      "text": "insight text backed by evidence"
    }}
  ],
  "trust_trail": [
    {{
      "name": "source name",
      "stance": "supporting|contradicting",
      "url": "real source URL"
    }}
  ]
}}
"""


async def generate_verdict(
    content: str,
    claims: list,
    verification_results: dict,
    emotion_exploit: dict,
    multimodal_report: dict = None
) -> dict:
    """
    Generate verdict reasoning using LLM, but with real evidence context.
    The reality_score is NOT generated here — it comes from score_calculator.
    """
    try:
        claims_json = json.dumps(claims[:5], indent=2, ensure_ascii=False)
        verification_json = json.dumps(verification_results, indent=2, ensure_ascii=False)
        emotion_json = json.dumps(emotion_exploit, indent=2, ensure_ascii=False)

        prompt = REASONING_PROMPT.format(
            content=content[:3000],
            claims_json=claims_json[:2000],
            verification_json=verification_json[:3000],
            emotion_json=emotion_json[:1000],
        )

        raw = await generate_with_fallback(
            prompt,
            temperature=0.2,
            max_tokens=3000,
        )

        result = parse_json_response(raw)

        # Validate
        if "claims" not in result:
            result["claims"] = []
        if "key_insights" not in result:
            result["key_insights"] = [{"icon": "warning", "text": "Analysis completed with limited evidence."}]
        if "trust_trail" not in result:
            result["trust_trail"] = []
        if "context_drift" not in result:
            result["context_drift"] = {"detected": False}

        return result

    except Exception as e:
        print(f"[VerdictEngine] Error: {e}")
        return _fallback_verdict(content, claims)


def _fallback_verdict(content: str, claims: list) -> dict:
    """Fallback when LLM reasoning fails."""
    return {
        "reasoning": "LLM reasoning unavailable — verdict based on external API evidence only.",
        "claims": [
            {
                "text": c.get("text", str(c))[:200] if isinstance(c, dict) else str(c)[:200],
                "highlights": [
                    {"word": w.get("word", ""), "risk": 0.5, "reason": w.get("reason", "Needs verification")}
                    for w in (c.get("suspicious_words", []) if isinstance(c, dict) else [])
                ],
                "virality_spike": None,
            }
            for c in claims[:3]
        ],
        "context_drift": {"detected": False},
        "key_insights": [
            {"icon": "warning", "text": "LLM reasoning unavailable — score is based on external API matches."},
            {"icon": "warning", "text": "Manual verification recommended."}
        ],
        "trust_trail": [],
    }
