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

# ── Trusted / well-known domains ──
# Sources from these domains are prioritized in the output and displayed first.
TRUSTED_DOMAINS = {
    # Indian Government & Institutional
    "pib.gov.in", "pibindia.wordpress.com", "india.gov.in", "mohfw.gov.in",
    "icmr.gov.in", "mygov.in",
    # Indian Fact-Checkers
    "altnews.in", "boomlive.in", "thequint.com", "factly.in", "vishvasnews.com",
    "newschecker.in", "factchecker.in",
    # Indian News (Major)
    "timesofindia.indiatimes.com", "ndtv.com", "thehindu.com",
    "indianexpress.com", "hindustantimes.com", "livemint.com",
    "economictimes.indiatimes.com", "news18.com", "scroll.in",
    "thewire.in", "deccanherald.com",
    # International Wire Services & Major Outlets
    "reuters.com", "apnews.com", "afp.com",
    "bbc.com", "bbc.co.uk",
    "nytimes.com", "washingtonpost.com", "theguardian.com",
    "cnn.com", "aljazeera.com", "dw.com",
    # International Fact-Checkers
    "snopes.com", "politifact.com", "factcheck.org", "fullfact.org",
    # Science & Health
    "who.int", "cdc.gov", "nih.gov", "nature.com", "sciencedirect.com",
    "thelancet.com", "bmj.com",
    # Tech (for tech-related claims)
    "techcrunch.com", "arstechnica.com", "wired.com",
}


def _is_trusted_domain(url: str) -> bool:
    """Check if a URL belongs to a trusted/well-known domain."""
    try:
        from urllib.parse import urlparse
        hostname = urlparse(url).hostname or ""
        hostname = hostname.replace("www.", "")
        return hostname in TRUSTED_DOMAINS
    except Exception:
        return False


def _get_domain_name(url: str) -> str:
    """Extract a clean domain name from a URL."""
    try:
        from urllib.parse import urlparse
        hostname = urlparse(url).hostname or ""
        return hostname.replace("www.", "")
    except Exception:
        return url


def _source_sort_key(source: dict) -> tuple:
    """Sort sources: fact-checkers first, then trusted, then others."""
    url = source.get("url", "")
    stance = source.get("stance", "neutral")
    is_trusted = _is_trusted_domain(url)
    # Priority: contradicts (fact-checked denial) > supports > neutral
    # Within each: trusted domains first
    stance_order = 0 if stance == "contradicts" else (1 if stance == "supports" else 2)
    trust_order = 0 if is_trusted else 1
    return (stance_order, trust_order)


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
                "corroborating": corroborating[:5],
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

    # Sort: fact-checked + trusted domains first, then others
    unique_sources.sort(key=_source_sort_key)

    return {
        "verified_claims": verified_claims,
        "sources": unique_sources[:15],
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
            # Retry with Hindi for Indian claims
            params["languageCode"] = "hi"
            resp = await client.get(FACT_CHECK_API, params=params)
            if resp.status_code != 200:
                return []

        data = resp.json()
        results = []
        for claim in data.get("claims", [])[:5]:
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
        # Add domain filter to prefer trusted sources
        trusted_filter = " OR ".join([f"domain:{d}" for d in [
            "bbc.com", "reuters.com", "ndtv.com", "timesofindia.indiatimes.com",
            "thehindu.com", "altnews.in", "boomlive.in", "apnews.com",
        ]])
        enhanced_query = f"({query[:100]}) ({trusted_filter})"

        params = {
            "query": enhanced_query[:500],
            "mode": "ArtList",
            "maxrecords": "10",
            "format": "json",
            "sort": "DateDesc",
        }
        resp = await client.get(GDELT_API, params=params)

        # If domain-filtered query returns nothing, fallback to plain query
        if resp.status_code != 200:
            params["query"] = query[:150]
            resp = await client.get(GDELT_API, params=params)
            if resp.status_code != 200:
                return []

        data = resp.json()
        articles = data.get("articles", [])

        # If domain filter was too strict and returned nothing, retry plain
        if not articles:
            params["query"] = query[:150]
            params["maxrecords"] = "10"
            resp = await client.get(GDELT_API, params=params)
            if resp.status_code == 200:
                data = resp.json()
                articles = data.get("articles", [])

        # Sort: trusted domains first
        articles.sort(key=lambda a: 0 if _is_trusted_domain(a.get("url", "")) else 1)

        return [
            {
                "title": a.get("title", ""),
                "url": a.get("url", ""),
                "domain": a.get("domain", ""),
                "date": a.get("seendate", ""),
            }
            for a in articles[:10]
        ]
    except Exception as e:
        print(f"[Verifier] GDELT error: {e}")
        return []


async def _query_newsapi(client: httpx.AsyncClient, query: str, api_key: str) -> list:
    """Query NewsAPI for headline cross-referencing."""
    if not api_key:
        return []
    try:
        # Prefer trusted Indian + international domains
        params = {
            "q": query[:100],
            "apiKey": api_key,
            "sortBy": "relevancy",
            "pageSize": 10,
            "language": "en",
            "domains": ",".join([
                "bbc.co.uk", "reuters.com", "apnews.com",
                "ndtv.com", "timesofindia.indiatimes.com", "thehindu.com",
                "indianexpress.com", "hindustantimes.com",
                "theguardian.com", "aljazeera.com",
            ]),
        }
        resp = await client.get(NEWSAPI_URL, params=params)

        articles = []
        if resp.status_code == 200:
            data = resp.json()
            articles = data.get("articles", [])

        # If domain filter was too strict, retry without domain filter
        if len(articles) < 3:
            params.pop("domains", None)
            params["pageSize"] = 10
            resp = await client.get(NEWSAPI_URL, params=params)
            if resp.status_code == 200:
                data = resp.json()
                # Merge: keep domain-filtered results first, add others
                seen = {a.get("url") for a in articles}
                for a in data.get("articles", []):
                    if a.get("url") not in seen:
                        articles.append(a)

        # Sort: trusted domains first
        articles.sort(key=lambda a: 0 if _is_trusted_domain(a.get("url", "")) else 1)

        return articles[:10]
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
