"""Tests for the URL reader (Phase 3B web reader)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


def test_read_url_returns_text() -> None:
    """URL reader fetches HTML and returns plain text via BeautifulSoup."""
    from agentrag.ingestion.readers.web import read_url

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = (
        "<html><body><h1>Hello</h1><p>World content here.</p></body></html>"
    )
    mock_response.raise_for_status = MagicMock()

    with patch("agentrag.ingestion.readers.web.httpx") as mock_httpx:
        mock_client = MagicMock()
        mock_httpx.Client.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_httpx.Client.return_value.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = mock_response

        result = read_url("https://example.com/page")

    assert "Hello" in result
    assert "World content here" in result
    assert "<" not in result  # tags stripped


def test_read_url_strips_boilerplate() -> None:
    """URL reader strips nav/header/footer/script/style tags."""
    from agentrag.ingestion.readers.web import read_url

    html = """<html><body>
        <header>HEADER_SENTINEL</header>
        <nav>NAV_SENTINEL</nav>
        <main><p>BODY_SENTINEL</p></main>
        <footer>FOOTER_SENTINEL</footer>
        <script>SCRIPT_SENTINEL</script>
    </body></html>"""

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = html
    mock_response.raise_for_status = MagicMock()

    with patch("agentrag.ingestion.readers.web.httpx") as mock_httpx:
        mock_client = MagicMock()
        mock_httpx.Client.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_httpx.Client.return_value.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = mock_response

        result = read_url("https://example.com")

    assert "BODY_SENTINEL" in result
    assert "HEADER_SENTINEL" not in result
    assert "NAV_SENTINEL" not in result
    assert "FOOTER_SENTINEL" not in result
    assert "SCRIPT_SENTINEL" not in result


def _patch_httpx_exceptions(mock_httpx: MagicMock) -> None:
    """Set real exception classes on the mocked httpx module."""
    import httpx

    mock_httpx.HTTPStatusError = httpx.HTTPStatusError
    mock_httpx.TimeoutException = httpx.TimeoutException
    mock_httpx.RequestError = httpx.RequestError


def test_read_url_raises_on_http_error() -> None:
    """URL reader raises ConnectionError on 4xx/5xx HTTP status."""
    import httpx

    from agentrag.ingestion.readers.web import read_url

    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "404", request=MagicMock(), response=MagicMock()
    )

    with patch("agentrag.ingestion.readers.web.httpx") as mock_httpx:
        _patch_httpx_exceptions(mock_httpx)
        mock_client = MagicMock()
        mock_httpx.Client.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_httpx.Client.return_value.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = mock_response

        with pytest.raises(ConnectionError, match="HTTP error"):
            read_url("https://example.com/missing")


def test_read_url_raises_on_timeout() -> None:
    """URL reader raises ConnectionError on request timeout."""
    import httpx

    from agentrag.ingestion.readers.web import read_url

    with patch("agentrag.ingestion.readers.web.httpx") as mock_httpx:
        _patch_httpx_exceptions(mock_httpx)
        mock_client = MagicMock()
        mock_httpx.Client.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_httpx.Client.return_value.__exit__ = MagicMock(return_value=False)
        mock_client.get.side_effect = httpx.TimeoutException("timed out")

        with pytest.raises(ConnectionError, match="timed out"):
            read_url("https://slow.example.com")


def test_read_url_raises_on_malformed_url() -> None:
    """URL reader raises ValueError on malformed URL."""
    from agentrag.ingestion.readers.web import read_url

    with pytest.raises(ValueError, match="Invalid URL"):
        read_url("not-a-url")


def test_read_url_raises_value_error_on_empty_content() -> None:
    """URL reader raises ValueError when extracted text is empty."""
    from agentrag.ingestion.readers.web import read_url

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = "<html><body><script>var x=1;</script></body></html>"
    mock_response.raise_for_status = MagicMock()

    with patch("agentrag.ingestion.readers.web.httpx") as mock_httpx:
        mock_client = MagicMock()
        mock_httpx.Client.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_httpx.Client.return_value.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = mock_response

        with pytest.raises(ValueError, match="No text content"):
            read_url("https://empty.example.com")
