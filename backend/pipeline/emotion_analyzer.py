"""
Emotion Analyzer — Detects emotional manipulation in text.
Identifies fear-mongering, urgency, outrage, and other manipulation tactics.
Uses Gemini for nuanced understanding of Hindi/English emotional language.
"""

from pipeline.gemini_client import generate_with_fallback, parse_json_response


EMOTION_PROMPT = """Analyze the emotional manipulation level in the following text.

Text:
---
{content}
---

Rate the emotional manipulation intensity from 0-100, where:
- 0-20: Neutral, factual reporting
- 21-50: Mild emotional framing
- 51-80: Significant emotional manipulation (fear, outrage, urgency)
- 81-100: Extreme emotional manipulation (panic-inducing, hate-inciting)

Respond in JSON (no markdown):
{{
  "intensity": 0-100,
  "label": "one-line description of the manipulation type detected",
  "tactics": ["tactic1", "tactic2"]
}}
"""


async def analyze_emotion(text: str) -> dict:
    """Analyze emotional manipulation intensity in text."""
    if not text or len(text.strip()) < 20:
        return {"intensity": 0, "label": "Insufficient text for analysis."}

    try:
        raw = await generate_with_fallback(
            EMOTION_PROMPT.format(content=text[:2000]),
            temperature=0.1,
            max_tokens=300,
        )

        data = parse_json_response(raw)
        return {
            "intensity": min(100, max(0, int(data.get("intensity", 0)))),
            "label": data.get("label", ""),
        }

    except Exception as e:
        print(f"[EmotionAnalyzer] Error: {e}")
        return {"intensity": 0, "label": "Could not analyze emotional content."}
