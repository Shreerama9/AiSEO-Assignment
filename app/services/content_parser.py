from __future__ import annotations

import hashlib
import re

import httpx
from bs4 import BeautifulSoup
from cachetools import TTLCache

try:
    import trafilatura
    _HAS_TRAFILATURA = True
except ImportError:  # pragma: no cover
    _HAS_TRAFILATURA = False

_BOILERPLATE_TAGS = ["nav", "header", "footer", "aside", "script", "style"]
_URL_CACHE: TTLCache = TTLCache(maxsize=128, ttl=3600)


async def get_content(input_type: str, input_value: str) -> str:
    # Routes based on input type (url or text) to fetch or return content
    if input_type == "url":
        return await fetch_url(input_value)
    return input_value


async def fetch_url(url: str, timeout: float = 10.0) -> str:
    # Fetches raw HTML from a URL with caching and error handling
    cache_key = hashlib.sha256(url.encode()).hexdigest()
    if cache_key in _URL_CACHE:
        return _URL_CACHE[cache_key]

    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=timeout) as client:
            response = await client.get(url, headers={"User-Agent": "AEGIS-AEO-Bot/1.0"})
            response.raise_for_status()
            html = response.text
    except Exception as exc:
        raise ValueError(f"Fetch failed: {exc}") from exc

    soup = BeautifulSoup(html, "html.parser")
    body = soup.find("body")
    body_text = body.get_text(strip=True) if body else html.strip()
    if not body_text:
        raise ValueError("Empty body returned.")

    _URL_CACHE[cache_key] = html
    return html


def extract_first_paragraph(html: str) -> str:
    # Returns the first meaningful block of text from HTML
    if _HAS_TRAFILATURA:
        clean = trafilatura.extract(html, include_comments=False, include_tables=False)
        if clean:
            for block in clean.split("\n\n"):
                if len(block.strip().split()) >= 5:
                    return block.strip()

    soup = BeautifulSoup(html, "html.parser")
    for tag in soup.find_all(_BOILERPLATE_TAGS):
        tag.decompose()

    for p in soup.find_all("p"):
        text = p.get_text(separator=" ", strip=True)
        if len(text.split()) >= 5:
            return text

    blocks = soup.get_text(separator="\n").split("\n\n")
    for block in blocks:
        if len(block.strip().split()) >= 5:
            return block.strip()

    return html.strip()


def strip_boilerplate(html: str) -> str:
    # Removes navigation and non-prose elements to isolate the main text
    if _HAS_TRAFILATURA:
        clean = trafilatura.extract(html, include_comments=False, include_tables=False)
        if clean:
            return re.sub(r"\s{2,}", " ", clean).strip()

    soup = BeautifulSoup(html, "html.parser")
    for tag in soup.find_all(_BOILERPLATE_TAGS):
        tag.decompose()

    return re.sub(r"\s{2,}", " ", soup.get_text(separator=" ", strip=True)).strip()


def parse_html(html: str) -> BeautifulSoup:
    # Returns a BeautifulSoup object from raw HTML
    return BeautifulSoup(html, "html.parser")
