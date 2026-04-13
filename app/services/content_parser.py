from __future__ import annotations

import hashlib
import ipaddress
import re
from urllib.parse import urlparse

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

# RFC1918 + link-local + loopback blocks blocked for SSRF protection
_BLOCKED_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.0.0/16"),  # link-local / AWS metadata
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
]


def _assert_safe_url(url: str) -> None:
    """Raise ValueError if the URL targets a private/internal address."""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"Unsupported scheme '{parsed.scheme}'. Only http/https allowed.")

    hostname = parsed.hostname
    if not hostname:
        raise ValueError("URL has no hostname.")

    # Block bare hostnames with no dot (e.g. 'localhost', internal service names)
    if "." not in hostname and ":" not in hostname:
        raise ValueError(f"Hostname '{hostname}' is not a public address.")

    try:
        addr = ipaddress.ip_address(hostname)
        for network in _BLOCKED_NETWORKS:
            if addr in network:
                raise ValueError(f"Requests to '{hostname}' are not allowed.")
    except ValueError as exc:
        # Re-raise only SSRF errors; DNS hostnames that aren't IPs are fine
        if "not allowed" in str(exc) or "Unsupported" in str(exc) or "no hostname" in str(exc):
            raise
        # ip_address() raised because hostname is a domain name — that's fine


async def get_content(input_type: str, input_value: str) -> str:
    # Routes based on input type (url or text) to fetch or return content
    if input_type == "url":
        return await fetch_url(input_value)
    return input_value


async def fetch_url(url: str, timeout: float = 10.0) -> str:
    # Fetches raw HTML from a URL with caching, SSRF protection, and timeout
    _assert_safe_url(url)

    cache_key = hashlib.sha256(url.encode()).hexdigest()
    if cache_key in _URL_CACHE:
        return _URL_CACHE[cache_key]

    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=timeout) as client:
            response = await client.get(url, headers={"User-Agent": "AEGIS-AEO-Bot/1.0"})
            response.raise_for_status()
            html = response.text
    except httpx.TimeoutException:
        raise ValueError(f"Request timed out after {timeout}s fetching '{url}'.")
    except httpx.HTTPStatusError as exc:
        raise ValueError(f"HTTP {exc.response.status_code} fetching '{url}'.") from exc
    except Exception as exc:
        raise ValueError(f"Fetch failed: {exc}") from exc

    soup = BeautifulSoup(html, "html.parser")
    body = soup.find("body")
    body_text = body.get_text(strip=True) if body else html.strip()
    if not body_text:
        raise ValueError("Empty body returned.")

    _URL_CACHE[cache_key] = html
    return html


def bust_cache(url: str) -> bool:
    """Remove a URL from the cache. Returns True if it was present."""
    cache_key = hashlib.sha256(url.encode()).hexdigest()
    if cache_key in _URL_CACHE:
        del _URL_CACHE[cache_key]
        return True
    return False


def bust_all_cache() -> int:
    """Clear the entire URL cache. Returns the number of entries cleared."""
    count = len(_URL_CACHE)
    _URL_CACHE.clear()
    return count


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
