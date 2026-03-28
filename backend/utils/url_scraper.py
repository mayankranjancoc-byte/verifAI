"""
URL Scraper — Extracts readable text and metadata from URLs.
Uses trafilatura for clean text extraction with fallback to BeautifulSoup.
"""

import httpx
import trafilatura
from bs4 import BeautifulSoup


async def scrape_url(url: str) -> dict | None:
    """Scrape text content from a URL."""
    try:
        async with httpx.AsyncClient(
            timeout=12.0,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        ) as client:
            resp = await client.get(url)

            if resp.status_code != 200:
                return None

            html = resp.text

            # Try trafilatura first (best quality extraction)
            extracted = trafilatura.extract(
                html,
                include_comments=False,
                include_tables=True,
                output_format="txt",
            )

            # Get title
            title = ""
            try:
                soup = BeautifulSoup(html, "html.parser")
                title_tag = soup.find("title")
                if title_tag:
                    title = title_tag.get_text(strip=True)
                
                # Also try og:title
                og_title = soup.find("meta", property="og:title")
                if og_title and og_title.get("content"):
                    title = og_title["content"]
            except Exception:
                pass

            if extracted:
                return {
                    "title": title or "Untitled",
                    "text": extracted[:5000],
                    "url": url,
                }

            # Fallback: BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")
            # Remove scripts and styles
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()
            text = soup.get_text(separator="\n", strip=True)

            if text:
                return {
                    "title": title or "Untitled",
                    "text": text[:5000],
                    "url": url,
                }

            return None

    except Exception as e:
        print(f"[URLScraper] Error scraping {url}: {e}")
        return None
