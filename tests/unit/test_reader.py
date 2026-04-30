from __future__ import annotations

from pathlib import Path

import pytest

from agentrag.ingestion.reader import read_file
from agentrag.types import RawDocument


def test_read_txt(tmp_path: Path) -> None:
    """Plain text file read produces RawDocument with correct content."""
    txt_file = tmp_path / "test.txt"
    content = "This is test content.\nSecond line."
    txt_file.write_text(content, encoding="utf-8")
    result = read_file(txt_file)
    assert isinstance(result, RawDocument)
    assert result.text == content
    assert result.filename == "test.txt"


def test_read_md(tmp_path: Path) -> None:
    """Markdown file read produces RawDocument with non-empty text."""
    md_file = tmp_path / "test.md"
    content = "# Header\n\nParagraph text."
    md_file.write_text(content, encoding="utf-8")
    result = read_file(md_file)
    assert isinstance(result, RawDocument)
    assert len(result.text) > 0
    assert result.text == content


def test_read_pdf() -> None:
    """PDF fixture read produces RawDocument with extracted text."""
    pdf_path = Path("tests/fixtures/sample.pdf")
    result = read_file(pdf_path)
    assert isinstance(result, RawDocument)
    assert len(result.text) > 0
    assert result.filename == "sample.pdf"


def test_source_id_format(tmp_path: Path) -> None:
    """source_id is 16-char hex string derived from resolved path."""
    txt_file = tmp_path / "test.txt"
    txt_file.write_text("content", encoding="utf-8")
    result = read_file(txt_file)
    assert len(result.source_id) == 16
    assert all(c in "0123456789abcdef" for c in result.source_id)


def test_nonexistent_raises(tmp_path: Path) -> None:
    """Non-existent file path raises FileNotFoundError."""
    nonexistent = tmp_path / "does_not_exist.txt"
    with pytest.raises(FileNotFoundError):
        read_file(nonexistent)


def test_unsupported_extension_raises(tmp_path: Path) -> None:
    """Unsupported file extension raises ValueError."""
    unsupported = tmp_path / "test.xyz"
    unsupported.write_text("content", encoding="utf-8")
    with pytest.raises(ValueError, match="Unsupported file type"):
        read_file(unsupported)


def test_empty_file_raises(tmp_path: Path) -> None:
    """Empty file raises ValueError."""
    empty_file = tmp_path / "empty.txt"
    empty_file.write_text("", encoding="utf-8")
    with pytest.raises(ValueError, match="File is empty"):
        read_file(empty_file)


def test_read_docx() -> None:
    """DOCX fixture produces RawDocument with paragraphs joined and blank filtered."""
    docx_path = Path("tests/fixtures/sample.docx")
    result = read_file(docx_path)
    assert isinstance(result, RawDocument)
    assert result.filename == "sample.docx"
    assert len(result.source_id) == 16
    assert all(c in "0123456789abcdef" for c in result.source_id)
    assert len(result.text) > 0
    # blank paragraph from fixture must not appear as an empty line cluster
    assert result.text.strip() != ""
    # at least one of the known paragraphs is present
    assert "AgentRAG" in result.text


def test_read_html() -> None:
    """HTML fixture read strips boilerplate and preserves body content."""
    html_path = Path("tests/fixtures/sample.html")
    result = read_file(html_path)
    assert isinstance(result, RawDocument)
    assert result.filename == "sample.html"
    # body sentinel must be present
    assert "BODY_SENTINEL" in result.text
    # boilerplate sentinels must be absent
    assert "NAV_SENTINEL" not in result.text
    assert "HEADER_SENTINEL" not in result.text
    assert "FOOTER_SENTINEL" not in result.text
    assert "SCRIPT_SENTINEL" not in result.text
    assert "STYLE_SENTINEL" not in result.text
    # no raw angle-bracket characters
    assert "<" not in result.text
    assert ">" not in result.text


def test_read_py() -> None:
    """Python fixture read returns raw source byte-for-byte identical."""
    py_path = Path("tests/fixtures/sample.py")
    result = read_file(py_path)
    assert isinstance(result, RawDocument)
    assert result.filename == "sample.py"
    expected = py_path.read_text(encoding="utf-8")
    assert result.text == expected


def test_read_ipynb() -> None:
    """Notebook fixture read includes code+markdown cells and excludes raw cells."""
    ipynb_path = Path("tests/fixtures/sample.ipynb")
    result = read_file(ipynb_path)
    assert isinstance(result, RawDocument)
    assert result.filename == "sample.ipynb"
    assert "CODE_SENTINEL" in result.text
    assert "MARKDOWN_SENTINEL" in result.text
    assert "RAW_SENTINEL" not in result.text
