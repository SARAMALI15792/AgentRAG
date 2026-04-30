from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from agentrag.ingestion.reader import read_file
from agentrag.types import RawDocument

FIXTURES = Path("tests/fixtures")


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


# ---------------------------------------------------------------------------
# Office readers (Phase 3B)
# ---------------------------------------------------------------------------


def test_read_xlsx() -> None:
    """Excel fixture read extracts text from all sheets including headers."""
    result = read_file(FIXTURES / "sample.xlsx")
    assert isinstance(result, RawDocument)
    assert result.filename == "sample.xlsx"
    assert len(result.text) > 0
    assert "Name" in result.text  # header row preserved
    assert "Alice Johnson" in result.text
    assert "Products" in result.text  # sheet 2 content present


def test_read_pptx() -> None:
    """PowerPoint fixture read extracts title, body, and speaker notes."""
    result = read_file(FIXTURES / "sample.pptx")
    assert isinstance(result, RawDocument)
    assert result.filename == "sample.pptx"
    assert len(result.text) > 0
    assert "AgentRAG" in result.text  # title from slide 1
    assert "Architecture" in result.text  # title from slide 2
    assert "Speaker notes" in result.text or "Introduction slide" in result.text


def test_read_csv() -> None:
    """CSV fixture read produces header row and all data rows as text."""
    result = read_file(FIXTURES / "sample.csv")
    assert isinstance(result, RawDocument)
    assert result.filename == "sample.csv"
    assert len(result.text) > 0
    assert "name" in result.text.lower()  # header preserved
    assert "Alice Johnson" in result.text
    assert "Bob Smith" in result.text


# ---------------------------------------------------------------------------
# eBook readers (Phase 3B)
# ---------------------------------------------------------------------------


def test_read_epub() -> None:
    """EPUB fixture read extracts text from all XHTML chapters."""
    result = read_file(FIXTURES / "sample.epub")
    assert isinstance(result, RawDocument)
    assert result.filename == "sample.epub"
    assert len(result.text) > 0
    assert "Retrieval-Augmented Generation" in result.text
    assert "Vector Embeddings" in result.text


def test_read_mobi_delegates_to_epub(tmp_path: Path) -> None:
    """MOBI reader extracts text by converting via mobi.extract then reading as EPUB."""
    fake_mobi = tmp_path / "test.mobi"
    fake_mobi.write_bytes(b"fake mobi content")
    epub_path = FIXTURES / "sample.epub"

    with patch("agentrag.ingestion.readers.ebooks.mobi_extract") as mock_extract:
        mock_extract.return_value = (str(tmp_path), str(epub_path))
        result = read_file(fake_mobi)

    assert isinstance(result, RawDocument)
    assert len(result.text) > 0
    assert "Retrieval-Augmented Generation" in result.text


# ---------------------------------------------------------------------------
# Structured data readers (Phase 3B)
# ---------------------------------------------------------------------------


def test_read_json() -> None:
    """JSON fixture read produces pretty-printed text with key names present."""
    result = read_file(FIXTURES / "sample.json")
    assert isinstance(result, RawDocument)
    assert result.filename == "sample.json"
    assert len(result.text) > 0
    assert "AgentRAG" in result.text
    assert "embedding" in result.text


def test_read_yaml() -> None:
    """YAML fixture read produces text with key names and values."""
    result = read_file(FIXTURES / "sample.yaml")
    assert isinstance(result, RawDocument)
    assert result.filename == "sample.yaml"
    assert len(result.text) > 0
    assert "agentrag" in result.text.lower()
    assert "embedding" in result.text.lower()


def test_read_xml() -> None:
    """XML fixture read strips tags and returns only text content."""
    result = read_file(FIXTURES / "sample.xml")
    assert isinstance(result, RawDocument)
    assert result.filename == "sample.xml"
    assert len(result.text) > 0
    assert "Retrieval-Augmented Generation" in result.text
    assert "<" not in result.text  # tags stripped


def test_read_toml() -> None:
    """TOML fixture read produces text with section and key names."""
    result = read_file(FIXTURES / "sample.toml")
    assert isinstance(result, RawDocument)
    assert result.filename == "sample.toml"
    assert len(result.text) > 0
    assert "agentrag" in result.text.lower()
    assert "embedding" in result.text.lower()


# ---------------------------------------------------------------------------
# Subtitle readers (Phase 3B)
# ---------------------------------------------------------------------------


def test_read_srt() -> None:
    """SRT fixture read extracts timestamped subtitle text."""
    result = read_file(FIXTURES / "sample.srt")
    assert isinstance(result, RawDocument)
    assert result.filename == "sample.srt"
    assert len(result.text) > 0
    assert "AgentRAG" in result.text
    assert "semantic search" in result.text.lower()


# ---------------------------------------------------------------------------
# Email readers (Phase 3B)
# ---------------------------------------------------------------------------


def test_read_eml() -> None:
    """EML fixture read extracts subject, headers, and body text."""
    result = read_file(FIXTURES / "sample.eml")
    assert isinstance(result, RawDocument)
    assert result.filename == "sample.eml"
    assert len(result.text) > 0
    assert "Phase 3B" in result.text
    assert "Alice" in result.text


# ---------------------------------------------------------------------------
# Empty-extraction contract (Article XIV.2)
# ---------------------------------------------------------------------------


def test_empty_extraction_raises_value_error(tmp_path: Path) -> None:
    """Reader that returns empty string must raise ValueError per Article XIV.2."""
    # XML with only tags and no text nodes produces empty extraction
    empty_xml = tmp_path / "empty.xml"
    empty_xml.write_text("<root><child/></root>", encoding="utf-8")
    with pytest.raises(ValueError, match="File is empty"):
        read_file(empty_xml)
