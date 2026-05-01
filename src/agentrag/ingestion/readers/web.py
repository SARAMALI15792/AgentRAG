"""URL reader — fetch web pages and extract text via BeautifulSoup."""

from __future__ import annotations

import logging

try:
    import httpx
except ImportError:
    raise ImportError(
        "httpx is required for URL ingestion. "
        "Install it with: pip install agentrag[web]"
    ) from None

try:
    from bs4 import BeautifulSoup
except ImportError:
    raise ImportError(
        "beautifulsoup4 is required for URL ingestion. "
        "Install it with: pip install agentrag[web]"
    ) from None

logger = logging.getLogger(__name__)

_TIMEOUT = 30.0


def read_url(url: str) -> str:
    """Fetch a URL and return its text content; raise on failure."""
    if not url.startswith(("http://", "https://")):
        raise ValueError(
            f"Invalid URL: {url!r}. URL must start with http:// or https://"
        )

    try:
        with httpx.Client(timeout=_TIMEOUT, follow_redirects=True) as client:
            response = client.get(url)
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise ConnectionError(
            f"HTTP error fetching {url}: {exc.response.status_code}"
        ) from exc
    except httpx.TimeoutException as exc:
        raise ConnectionError(
            f"Request timed out fetching {url}. "
            "Check your network connection or increase AGENTRAG_INGEST_TIMEOUT."
        ) from exc
    except httpx.RequestError as exc:
        raise ConnectionError(f"Network error fetching {url}: {exc}") from exc

    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup.find_all(["nav", "header", "footer", "script", "style"]):
        tag.decompose()
    text = soup.get_text(separator="\n", strip=True)

    if not text.strip():
        raise ValueError(
            f"No text content extracted from {url}. "
            "The page may be JavaScript-rendered or contain only non-text elements."
        )
    return text
