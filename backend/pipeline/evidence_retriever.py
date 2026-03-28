"""
Evidence Retriever — Multi-source fact-checking.
Uses:
1. Google Fact Check Tools API (free) — matches against existing fact-checks
2. Web search for corroborating/contradicting evidence

Inspired by:
- firojalam/Detecting-Previously-Fact-Checked-Claims (Elasticsearch + SBERT matching)
- Fugant1/Unfaker (API-based fact checking pipeline)
"""

import os
import json
import httpx

FACT_CHECK_API = "https://factchecktools.googleapis.com/v1alpha1/claims:search"
GOOGLE_SEARCH_API = "https://www.googleapis.com/customsearch/v1"


async def retrieve_evidence(claims: list, original_query: str) -> dict:
    """Retrieve evidence from multiple sources for the given claims."""
    all_fact_checks = []
    all_sources = []
    
    api_key = os.environ.get("GOOGLE_API_KEY", os.environ.get("GEMINI_API_KEY", ""))
    search_api_key = os.environ.get("SEARCH_API_KEY", "")
    search_engine_id = os.environ.get("SEARCH_ENGINE_ID", "")

    async with httpx.AsyncClient(timeout=15.0) as client:
        # 1. Query Google Fact Check Tools API for each claim
        for claim in claims[:3]:  # Limit to top 3 claims
            claim_text = claim.get("text", "") if isinstance(claim, dict) else str(claim)
            if not claim_text:
                continue

            fact_checks = await _search_fact_checks(client, claim_text, api_key)
            all_fact_checks.extend(fact_checks)

        # 2. Web search for additional evidence
        if search_api_key and search_engine_id:
            search_results = await _web_search(
                client, original_query, search_api_key, search_engine_id
            )
            all_sources.extend(search_results)

        # 3. Fallback: use Fact Check API results as sources
        for fc in all_fact_checks:
            all_sources.append({
                "name": fc.get("publisher", "Fact Check"),
                "url": fc.get("url", ""),
                "stance": "supporting",  # Fact-checkers that found this claim
                "rating": fc.get("rating", ""),
            })

    return {
        "fact_checks": all_fact_checks,
        "sources": all_sources[:6],  # Cap at 6 sources
    }


async def _search_fact_checks(client: httpx.AsyncClient, query: str, api_key: str) -> list:
    """Search Google Fact Check Tools API for previously fact-checked claims."""
    if not api_key:
        return []

    try:
        params = {
            "query": query[:200],
            "key": api_key,
            "languageCode": "en",
        }
        resp = await client.get(FACT_CHECK_API, params=params)
        
        if resp.status_code != 200:
            # Try Hindi
            params["languageCode"] = "hi"
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
        print(f"[EvidenceRetriever] Fact Check API error: {e}")
        return []


async def _web_search(
    client: httpx.AsyncClient, query: str, api_key: str, engine_id: str
) -> list:
    """Search Google Custom Search for corroborating/contradicting evidence."""
    try:
        params = {
            "key": api_key,
            "cx": engine_id,
            "q": f"fact check {query[:150]}",
            "num": 5,
        }
        resp = await client.get(GOOGLE_SEARCH_API, params=params)
        
        if resp.status_code != 200:
            return []

        data = resp.json()
        results = []

        for item in data.get("items", [])[:5]:
            results.append({
                "name": item.get("displayLink", item.get("link", "")),
                "url": item.get("link", ""),
                "title": item.get("title", ""),
                "snippet": item.get("snippet", ""),
                "stance": "supporting",  # Will be refined by verdict engine
            })

        return results

    except Exception as e:
        print(f"[EvidenceRetriever] Web search error: {e}")
        return []
