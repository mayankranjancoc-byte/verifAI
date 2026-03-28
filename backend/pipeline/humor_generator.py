"""
Humor Generator — Generates Hinglish jokes/roasts about misinformation.
Always pairs humor with a clear factual explanation.
Uses Gemini with high temperature for culturally aware, context-sensitive humor.
"""

from pipeline.gemini_client import generate_with_fallback, parse_json_response


HUMOR_PROMPT = """You are a witty Indian comedian who specializes in roasting misinformation in Hinglish.

The following content has been analyzed and found to be: {verdict}

Content:
---
{content}
---

Claims found:
{claims_text}

YOUR TASK:
1. Write a SHORT, funny Hinglish one-liner joke/roast about this misinformation
2. The joke should be smart, culturally relevant, and relatable to Indian audiences
3. Use a mix of Hindi and English (Hinglish)
4. Add one relevant emoji at the end
5. THEN write a clear, factual 1-2 sentence explanation of the truth

RULES:
- Keep the joke under 20 words
- Be witty, not mean-spirited
- Humor must NEVER dismiss the truth — it complements it
- Reference pop culture, daily life, or common Indian expressions
- If the content is TRUE, make a lighthearted positive comment instead of a roast

Respond in JSON (no markdown):
{{
  "joke": "your Hinglish joke here with emoji",
  "explanation": "Clear factual explanation of what is true and what is false."
}}
"""


async def generate_humor(content: str, verdict: str, claims: list) -> dict:
    """Generate a Hinglish humor response paired with factual explanation."""
    try:
        claims_text = "\n".join(
            f"- {c.get('text', str(c))}"
            for c in (claims[:3] if claims else [])
        ) or "No specific claims extracted."

        prompt = HUMOR_PROMPT.format(
            verdict=verdict,
            content=content[:1500],
            claims_text=claims_text[:500],
        )

        raw = await generate_with_fallback(
            prompt,
            temperature=0.9,
            max_tokens=500,
        )

        data = parse_json_response(raw)
        return {
            "joke": data.get("joke", ""),
            "explanation": data.get("explanation", ""),
        }

    except Exception as e:
        print(f"[HumorGenerator] Error: {e}")
        return {
            "joke": "Bhai, AI bhi confuse hai is news pe 🤖",
            "explanation": "We couldn't generate a humor response, but the fact-check analysis above is still valid."
        }
