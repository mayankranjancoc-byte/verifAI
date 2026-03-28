"""
Claim Extractor — Uses Gemini to extract verifiable claims from text.
Inspired by the ARG paper (AAAI 2024): LLM acts as advisor to identify
specific factual assertions that can be independently verified.
"""

import json
from pipeline.gemini_client import generate_with_fallback, parse_json_response


EXTRACT_PROMPT = """You are a misinformation analysis expert. Extract all verifiable factual claims from the following content.

For each claim:
1. Extract the exact claim text
2. Identify key entities (people, organizations, places, dates)
3. Identify words/phrases that are emotionally charged or potentially misleading

IMPORTANT: Focus on factual assertions that can be verified against real sources.
Handle Hindi, Hinglish, and English content equally.

Content to analyze:
---
{content}
---

Respond in this exact JSON format (no markdown, just raw JSON):
{{
  "claims": [
    {{
      "text": "the full claim text",
      "entities": ["entity1", "entity2"],
      "suspicious_words": [
        {{"word": "word_or_phrase", "reason": "why this is suspicious"}}
      ],
      "language": "en|hi|hinglish"
    }}
  ],
  "summary": "one-line summary of what the content is about"
}}

If no verifiable claims are found, return:
{{"claims": [], "summary": "No verifiable claims found"}}
"""


async def extract_claims(text: str) -> list:
    """Extract verifiable claims from text using Gemini."""
    if not text or len(text.strip()) < 10:
        return []

    try:
        raw = await generate_with_fallback(
            EXTRACT_PROMPT.format(content=text[:4000]),
            temperature=0.1,
            max_tokens=2000,
        )
        data = parse_json_response(raw)
        return data.get("claims", [])

    except Exception as e:
        print(f"[ClaimExtractor] Error: {e}")
        return [{
            "text": text[:500],
            "entities": [],
            "suspicious_words": [],
            "language": "en"
        }]
