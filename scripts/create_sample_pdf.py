"""Generate tests/fixtures/sample.pdf.

Run once, commit binary, never regenerate in CI.
"""

# not run in CI

from __future__ import annotations

import sys
from pathlib import Path


def _build_pdf() -> bytes:
    lines = [
        "AgentRAG Sample PDF Fixture",
        "",
        "This document is used as a test fixture for the AgentRAG ingestion pipeline.",
        "It verifies that reader.py can extract text from PDF files using PyMuPDF.",
        "",
        "The ingestion pipeline reads this file, extracts its text content, then",
        "chunks the text into overlapping token windows before generating dense",
        "vector embeddings with a local sentence-transformers model.",
        "",
        "Semantic retrieval over PDF content is a primary AgentRAG use case.",
        "Users can ingest research papers, contracts, manuals, and other PDFs,",
        "then query them using natural language through the MCP tool interface.",
        "",
        "This fixture is a single page of plain text for basic ingestion testing.",
    ]

    content_parts: list[str] = []
    y = 720
    for line in lines:
        safe = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        content_parts.append(f"BT /F1 11 Tf 50 {y} Td ({safe}) Tj ET")
        y -= 16

    content_str = "\n".join(content_parts)
    content_bytes = content_str.encode("latin-1")
    content_len = len(content_bytes)

    obj1 = b"1 0 obj\n<</Type /Catalog /Pages 2 0 R>>\nendobj\n"
    obj2 = b"2 0 obj\n<</Type /Pages /Kids [3 0 R] /Count 1>>\nendobj\n"
    obj3 = (
        b"3 0 obj\n"
        b"<</Type /Page /Parent 2 0 R /MediaBox [0 0 612 792]"
        b" /Contents 4 0 R"
        b" /Resources <</Font <</F1 <</Type /Font /Subtype /Type1"
        b" /BaseFont /Helvetica>>>>>>>>\n"
        b"endobj\n"
    )
    obj4_header = f"4 0 obj\n<</Length {content_len}>>\nstream\n".encode("latin-1")
    obj4 = obj4_header + content_bytes + b"\nendstream\nendobj\n"

    header = b"%PDF-1.4\n"
    body = header
    offsets: dict[int, int] = {}
    for num, obj in [(1, obj1), (2, obj2), (3, obj3), (4, obj4)]:
        offsets[num] = len(body)
        body += obj

    xref_offset = len(body)
    xref = b"xref\n0 5\n0000000000 65535 f \n"
    for num in [1, 2, 3, 4]:
        xref += f"{offsets[num]:010d} 00000 n \n".encode()

    trailer = (
        f"trailer\n<</Size 5 /Root 1 0 R>>\n" f"startxref\n{xref_offset}\n%%EOF\n"
    ).encode()
    return body + xref + trailer


def main() -> None:
    repo_root = Path(__file__).parent.parent
    output = repo_root / "tests" / "fixtures" / "sample.pdf"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(_build_pdf())
    print(f"Written: {output}")


if __name__ == "__main__":
    sys.exit(main() or 0)
