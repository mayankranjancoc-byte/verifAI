"""
Verdict Engine — Combines all signals into a final verdict.
Uses Gemini to reason over claims + evidence and produce:
- Reality score (0-100)
- Verdict: TRUE / MISLEADING / FALSE / UNVERIFIED
- Highlighted text spans with risk scores (for heatmaps)
- Context drift detection
- Trust trail
- Key intelligence insights

Inspired by ARG (AAAI 2024): "Bad Actor, Good Advisor" approach where
the LLM acts as a reasoning advisor, not a direct classifier.
"""

import json
from pipeline.gemini_client import generate_with_fallback, parse_json_response


VERDICT_PROMPT = """You are a senior fact-check analyst and misinformation expert. Analyze the following content and evidence to produce a comprehensive intelligence report.

ORIGINAL CONTENT:
---
{content}
---

EXTRACTED CLAIMS:
{claims_json}

EVIDENCE FROM FACT-CHECK DATABASES:
{evidence_json}

MULTIMODAL ANALYSIS (if available):
{multimodal_json}

YOUR TASK:
1. Evaluate each claim against the evidence
2. Detect any context drift (old content presented as new, out-of-context usage)
3. Identify emotionally manipulative language
4. Assess source credibility
5. Generate a final verdict

IMPORTANT RULES:
- If evidence is insufficient, mark as UNVERIFIED — never guess
- If sources conflict, show the conflict explicitly
- Be honest about uncertainty
- Consider Hindi/Hinglish content with equal rigor

Respond in this exact JSON format (no markdown, raw JSON only):
{{
  "verdict": "TRUE|FALSE|MISLEADING|UNVERIFIED",
  "reality_score": 0-100,
  "reasoning": "brief explanation of your verdict",
  "claims": [
    {{
      "text": "the claim text as it appears in the content",
      "highlights": [
        {{
          "word": "suspicious_word_or_phrase",
          "risk": 0.0-1.0,
          "reason": "why this is flagged"
        }}
      ],
      "virality_spike": "description of spread pattern if detectable, or null"
    }}
  ],
  "context_drift": {{
    "detected": true|false,
    "message": "explanation of context drift if detected",
    "original_date": "YYYY-MM-DD or null"
  }},
  "key_insights": [
    {{
      "icon": "check|warning|error",
      "text": "insight text"
    }}
  ],
  "trust_trail": [
    {{
      "name": "source name",
      "stance": "supporting|contradicting",
      "url": "source url or empty"
    }}
  ]
}}
"""


async def generate_verdict(
    content: str,
    claims: list,
    evidence: dict,
    multimodal_report: dict = None
) -> dict:
    """Generate a comprehensive verdict using Gemini reasoning."""
    try:
        claims_json = json.dumps(claims[:5], indent=2, ensure_ascii=False)
        evidence_json = json.dumps(evidence, indent=2, ensure_ascii=False)
        multimodal_json = json.dumps(multimodal_report or {}, indent=2, ensure_ascii=False)

        prompt = VERDICT_PROMPT.format(
            content=content[:3000],
            claims_json=claims_json[:2000],
            evidence_json=evidence_json[:2000],
            multimodal_json=multimodal_json[:1000],
        )

        raw = await generate_with_fallback(
            prompt,
            temperature=0.2,
            max_tokens=3000,
        )

        result = parse_json_response(raw)
        
        # Validate required fields
        if "verdict" not in result:
            result["verdict"] = "UNVERIFIED"
        if "reality_score" not in result:
            result["reality_score"] = 50
        if "claims" not in result:
            result["claims"] = []
        if "key_insights" not in result:
            result["key_insights"] = [{"icon": "warning", "text": "Analysis completed with limited evidence."}]
        if "trust_trail" not in result:
            result["trust_trail"] = []
        if "context_drift" not in result:
            result["context_drift"] = {"detected": False}

        return result

    except json.JSONDecodeError as e:
        print(f"[VerdictEngine] JSON parse error: {e}")
        return _fallback_verdict(content, claims)
    except Exception as e:
        print(f"[VerdictEngine] Error: {e}")
        return _fallback_verdict(content, claims)


def _fallback_verdict(content: str, claims: list) -> dict:
    """Fallback when Gemini fails — returns honest UNVERIFIED result."""
    return {
        "verdict": "UNVERIFIED",
        "reality_score": 50,
        "reasoning": "Unable to fully verify — LLM analysis encountered an issue.",
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
            {"icon": "warning", "text": "Automated analysis could not reach a definitive conclusion."},
            {"icon": "warning", "text": "Manual verification recommended."}
        ],
        "trust_trail": [],
    }
