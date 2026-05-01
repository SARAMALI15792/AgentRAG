"""eBook readers: .epub, .mobi."""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def _epub_to_text(epub_path: Path | str) -> str:
    """Extract plain text from an EPUB file via ebooklib + BeautifulSoup."""
    try:
        import ebooklib
        from ebooklib import epub
    except ImportError:
        raise ImportError(
            "ebooklib is required for .epub support. "
            "Install it with: pip install agentrag[ebooks]"
        ) from None

    from bs4 import BeautifulSoup

    book = epub.read_epub(str(epub_path), options={"ignore_ncx": True})
    parts: list[str] = []
    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        raw: bytes = item.get_content()
        soup = BeautifulSoup(raw, "html.parser")
        text = soup.get_text(separator="\n", strip=True)
        if text:
            parts.append(text)
    text = "\n\n".join(parts)
    if not text.strip():
        raise ValueError(f"No text content extracted from {epub_path}.")
    return text


def read_epub(path: Path) -> str:
    """Extract text from an EPUB file."""
    return _epub_to_text(path)


def mobi_extract(path: str) -> tuple[str, str]:
    """Thin wrapper around mobi.extract so tests can patch it."""
    try:
        from mobi import extract
    except ImportError:
        raise ImportError(
            "mobi is required for .mobi support. "
            "Install it with: pip install agentrag[ebooks]"
        ) from None
    return extract(path)  # type: ignore[no-any-return]


def read_mobi(path: Path) -> str:
    """Extract text from a MOBI file by converting to EPUB first."""
    import shutil

    tempdir, epub_path = mobi_extract(str(path))
    try:
        return _epub_to_text(epub_path)
    finally:
        shutil.rmtree(tempdir, ignore_errors=True)


# Register ebook readers
from agentrag.ingestion.reader_registry import register  # noqa: E402

register([".epub"], read_epub)
register([".mobi"], read_mobi)
