"""
Score Calculator — Deterministic, transparent reality score.
No LLM involved. Score is computed purely from external API evidence counts.

Formula:
  per_claim_score = confirmed / (confirmed + denied) * 100
  base_score = average(all per_claim_scores)
  manipulation_penalty = emotion_score * 0.15  (max 15 point penalty)
  final = clamp(base_score - manipulation_penalty, 0, 100)
"""


def compute_reality_score(verified_claims: list, emotion_score: int = 0) -> dict:
    """
    Compute a transparent reality score from real verification results.

    Args:
        verified_claims: list of {text, confirmed_count, denied_count, unverifiable}
        emotion_score: overall manipulation score (0-100) from emotion exploit analyzer

    Returns:
        {
            "reality_score": 0-100,
            "formula": "human-readable formula explanation",
            "claims_average": 0-100,
            "manipulation_penalty": 0-15,
            "per_claim_scores": [{claim, score, status}]
        }
    """
    if not verified_claims:
        return {
            "reality_score": 50,
            "formula": "No verifiable claims found — defaulting to neutral score",
            "claims_average": 50,
            "manipulation_penalty": 0,
            "per_claim_scores": [],
        }

    per_claim_scores = []

    for claim in verified_claims:
        confirmed = claim.get("confirmed_count", 0)
        denied = claim.get("denied_count", 0)
        coverage = claim.get("coverage_count", 0)
        unverifiable = claim.get("unverifiable", False)

        if unverifiable:
            score = 35  # Penalize unverifiable — don't assume true
            status = "unverifiable"
        else:
            authoritative_total = confirmed + denied
            if authoritative_total == 0:
                # No fact-checker verdicts — only news coverage
                # Coverage alone doesn't verify a claim; it means the topic is discussed
                if coverage >= 3:
                    score = 45  # Discussed but unverified
                elif coverage >= 1:
                    score = 40  # Barely discussed
                else:
                    score = 35  # No data at all
                status = "unverifiable"
            elif denied == 0:
                score = min(95, 60 + confirmed * 8)  # Confirmed by fact-checkers
                status = "confirmed"
            elif confirmed == 0:
                score = max(5, 25 - denied * 8)  # All denials from fact-checkers
                status = "contradicted"
            else:
                score = (confirmed / authoritative_total) * 100
                status = "confirmed" if score >= 50 else "contradicted"

        per_claim_scores.append({
            "claim": claim.get("text", "")[:100],
            "score": round(score),
            "status": status,
        })

    claims_average = sum(c["score"] for c in per_claim_scores) / len(per_claim_scores)
    manipulation_penalty = min(15, (emotion_score / 100) * 15)

    final_score = max(0, min(100, round(claims_average - manipulation_penalty)))

    formula = f"Base claim score ({round(claims_average)}%) minus manipulation penalty ({round(manipulation_penalty)}%)"

    return {
        "reality_score": final_score,
        "formula": formula,
        "claims_average": round(claims_average),
        "manipulation_penalty": round(manipulation_penalty),
        "per_claim_scores": per_claim_scores,
    }


def compute_verdict(reality_score: int) -> str:
    """Derive verdict label from the reality score."""
    if reality_score >= 80:
        return "TRUE"
    elif reality_score >= 60:
        return "MOSTLY TRUE"
    elif reality_score >= 40:
        return "UNVERIFIABLE"
    elif reality_score >= 20:
        return "MOSTLY FALSE"
    else:
        return "FALSE"
