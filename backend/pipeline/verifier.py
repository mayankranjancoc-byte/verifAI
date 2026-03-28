"""
Multi-Source Verifier — Queries real external APIs to verify claims.
Sources:
1. Google Fact Check Tools API
2. GDELT API (free, no key)
3. Wikipedia API (free, no key)
4. NewsAPI (requires key)

Each claim is verified independently against ALL sources in parallel.
Returns per-claim: confirmed_count, denied_count, unverifiable flag, source_links.
"""

import os
import asyncio
import httpx

FACT_CHECK_API = "https://factchecktools.googleapis.com/v1alpha1/claims:search"
GDELT_API = "https://api.gdeltproject.org/api/v2/doc/doc"
WIKIPEDIA_API = "https://en.wikipedia.org/api/rest_v1/page/summary"
NEWSAPI_URL = "https://newsapi.org/v2/everything"


async def verify_claims(claims: list, original_query: str) -> dict:
    """
    Verify each claim against multiple real sources.
    Returns structured per-claim evidence and aggregated source list.
    """
    api_key = os.environ.get("GOOGLE_FACT_CHECK_API_KEY", os.environ.get("GEMINI_API_KEY", ""))
    news_api_key = os.environ.get("NEWS_API_KEY", "")

    verified_claims = []
    all_sources = []

    async with httpx.AsyncClient(timeout=15.0) as client:
        for claim_obj in claims[:5]:
            claim_text = claim_obj.get("text", str(claim_obj)) if isinstance(claim_obj, dict) else str(claim_obj)
            entities = claim_obj.get("entities", []) if isinstance(claim_obj, dict) else []

            if not claim_text or len(claim_text.strip()) < 5:
                continue

            # Query all sources in parallel for this claim
            results = await asyncio.gather(
                _query_fact_check(client, claim_text, api_key),
                _query_gdelt(client, claim_text),
                _query_newsapi(client, claim_text, news_api_key),
                _query_wikipedia(client, entities),
                return_exceptions=True,
            )

            fact_check_results = results[0] if not isinstance(results[0], Exception) else []
            gdelt_results = results[1] if not isinstance(results[1], Exception) else []
            news_results = results[2] if not isinstance(results[2], Exception) else []
            wiki_results = results[3] if not isinstance(results[3], Exception) else []

            # Aggregate: count confirms/denials
            confirmed_by = []
            contradicted_by = []

            # Fact Check API — most authoritative
            for fc in fact_check_results:
                rating = fc.get("rating", "").lower()
                source_entry = {
                    "source": fc.get("publisher", "Fact Checker"),
                    "url": fc.get("url", ""),
                    "stance": "contradicts" if _is_denial_rating(rating) else "supports",
                    "excerpt": fc.get("title", ""),
                }
                if _is_denial_rating(rating):
                    contradicted_by.append(source_entry)
                else:
                    confirmed_by.append(source_entry)
                all_sources.append(source_entry)

            # GDELT articles — coverage only, NOT confirmation
            # News articles that discuss a claim don't prove it true
            corroborating = []
            for article in gdelt_results:
                source_entry = {
                    "source": article.get("domain", "News"),
                    "url": article.get("url", ""),
                    "stance": "neutral",
                    "excerpt": article.get("title", ""),
                }
                corroborating.append(source_entry)
                all_sources.append(source_entry)

            # NewsAPI articles — coverage only, NOT confirmation
            for article in news_results:
                source_entry = {
                    "source": article.get("source", {}).get("name", "News"),
                    "url": article.get("url", ""),
                    "stance": "neutral",
                    "excerpt": article.get("title", ""),
                }
                corroborating.append(source_entry)
                all_sources.append(source_entry)

            # Wikipedia — entity verification (confirms entity exists, NOT the claim)
            for wiki in wiki_results:
                source_entry = {
                    "source": "Wikipedia",
                    "url": wiki.get("url", ""),
                    "stance": "neutral",
                    "excerpt": wiki.get("extract", "")[:150],
                }
                corroborating.append(source_entry)
                all_sources.append(source_entry)

            total_authoritative = len(confirmed_by) + len(contradicted_by)
            total_coverage = len(corroborating)
            # Only use authoritative fact-check results for confirmed/denied
            # News coverage alone doesn't verify a claim
            unverifiable = total_authoritative == 0 and total_coverage < 3

            verified_claims.append({
                "text": claim_text,
                "status": _compute_status(confirmed_by, contradicted_by, unverifiable),
                "confirmed_count": len(confirmed_by),
                "denied_count": len(contradicted_by),
                "coverage_count": total_coverage,
                "unverifiable": unverifiable,
                "confirmed_by": confirmed_by[:3],
                "contradicted_by": contradicted_by[:3],
                "corroborating": corroborating[:3],
                "confidence": min(100, total_authoritative * 25 + total_coverage * 5) if not unverifiable else 0,
            })

    # Deduplicate sources by URL
    seen_urls = set()
    unique_sources = []
    for s in all_sources:
        url = s.get("url", "")
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique_sources.append(s)

    return {
        "verified_claims": verified_claims,
        "sources": unique_sources[:10],
        "total_sources_queried": len(all_sources),
    }


def _is_denial_rating(rating: str) -> bool:
    """Check if a fact-check rating indicates denial/false."""
    denials = ["false", "pants on fire", "mostly false", "incorrect",
               "misleading", "fake", "hoax", "no", "fiction", "wrong",
               "not true", "debunked", "fabricated"]
    return any(d in rating for d in denials)


def _compute_status(confirmed, contradicted, unverifiable):
    if unverifiable:
        return "unverifiable"
    if len(contradicted) > 0 and len(contradicted) >= len(confirmed):
        return "contradicted"
    if len(confirmed) > len(contradicted):
        return "confirmed"
    return "unverifiable"


# ── External API Queries ──

async def _query_fact_check(client: httpx.AsyncClient, query: str, api_key: str) -> list:
    """Query Google Fact Check Tools API."""
    if not api_key:
        return []
    try:
        params = {"query": query[:200], "key": api_key, "languageCode": "en"}
        resp = await client.get(FACT_CHECK_API, params=params)
        if resp.status_code != 200:
            return []

        data = resp.json()
        results = []
        for claim in data.get("claims", [])[:3]:
            for review in claim.get("claimReview", [])[:1]:
                results.append({
                    "claim_text": claim.get("text", ""),
                    "claimant": claim.get("claimant", "Unknown"),
                    "rating": review.get("textualRating", ""),
                    "publisher": review.get("publisher", {}).get("name", "Unknown"),
                    "url": review.get("url", ""),
                    "title": review.get("title", ""),
                })
        return results
    except Exception as e:
        print(f"[Verifier] Fact Check API error: {e}")
        return []


async def _query_gdelt(client: httpx.AsyncClient, query: str) -> list:
    """Query GDELT for global news coverage. Free, no key needed."""
    try:
        params = {
            "query": query[:150],
            "mode": "ArtList",
            "maxrecords": "5",
            "format": "json",
            "sort": "DateDesc",
        }
        resp = await client.get(GDELT_API, params=params)
        if resp.status_code != 200:
            return []

        data = resp.json()
        articles = data.get("articles", [])
        return [
            {
                "title": a.get("title", ""),
                "url": a.get("url", ""),
                "domain": a.get("domain", ""),
                "date": a.get("seendate", ""),
            }
            for a in articles[:5]
        ]
    except Exception as e:
        print(f"[Verifier] GDELT error: {e}")
        return []


async def _query_newsapi(client: httpx.AsyncClient, query: str, api_key: str) -> list:
    """Query NewsAPI for headline cross-referencing."""
    if not api_key:
        return []
    try:
        params = {
            "q": query[:100],
            "apiKey": api_key,
            "sortBy": "relevancy",
            "pageSize": 5,
            "language": "en",
        }
        resp = await client.get(NEWSAPI_URL, params=params)
        if resp.status_code != 200:
            print(f"[Verifier] NewsAPI error: {resp.status_code}")
            return []

        data = resp.json()
        return data.get("articles", [])[:5]
    except Exception as e:
        print(f"[Verifier] NewsAPI error: {e}")
        return []


async def _query_wikipedia(client: httpx.AsyncClient, entities: list) -> list:
    """Verify entities via Wikipedia API."""
    if not entities:
        return []

    results = []
    for entity in entities[:3]:
        try:
            url = f"{WIKIPEDIA_API}/{entity.replace(' ', '_')}"
            resp = await client.get(url, headers={"Accept": "application/json"})
            if resp.status_code != 200:
                continue

            data = resp.json()
            if data.get("type") == "standard":
                results.append({
                    "entity": entity,
                    "extract": data.get("extract", ""),
                    "url": data.get("content_urls", {}).get("desktop", {}).get("page", ""),
                })
        except Exception:
            continue

    return results
