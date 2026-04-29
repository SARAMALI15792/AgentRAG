"""File reader — converts local files to RawDocument."""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path

import pymupdf

from agentrag.types import RawDocument

logger = logging.getLogger(__name__)


def read_file(path: Path) -> RawDocument:
    """Read a local file and return its content as a RawDocument."""
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    suffix = path.suffix.lower()
    if suffix not in {".pdf", ".txt", ".md"}:
        raise ValueError(f"Unsupported file type: {suffix}")

    # Compute stable source_id from resolved absolute path
    source_id = hashlib.sha256(str(path.resolve()).encode()).hexdigest()[:16]

    # Extract text based on file type
    if suffix == ".pdf":
        text = _read_pdf(path)
    else:  # .txt or .md
        text = path.read_text(encoding="utf-8")

    if not text.strip():
        raise ValueError(f"File is empty: {path}")

    return RawDocument(
        source_id=source_id,
        filename=path.name,
        text=text,
        metadata={},
    )


def _read_pdf(path: Path) -> str:
    """Extract all text from a PDF file using pymupdf."""
    doc = pymupdf.open(str(path))  # type: ignore[no-untyped-call]
    pages = [page.get_text() for page in doc]  # type: ignore[attr-defined]
    doc.close()  # type: ignore[no-untyped-call]
    return "\n".join(pages)
