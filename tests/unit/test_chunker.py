from __future__ import annotations

from unittest.mock import MagicMock, patch

from agentrag.config import Settings
from agentrag.ingestion.chunker import chunk_document
from agentrag.types import RawDocument


def make_mock_tokenizer() -> MagicMock:
    """Create mock tokenizer that returns one token per word."""
    mock_tok = MagicMock()

    def encode_side_effect(text: str) -> list[int]:
        # One token per word (split on whitespace)
        return list(range(len(text.split())))

    def decode_side_effect(ids: list[int], **kwargs: object) -> str:
        # Return placeholder words (ignore kwargs like skip_special_tokens)
        return " ".join([f"word{i}" for i in ids])

    mock_tok.encode.side_effect = encode_side_effect
    mock_tok.decode.side_effect = decode_side_effect
    return mock_tok


def test_long_text_produces_multiple_chunks(settings: Settings) -> None:
    """Long text exceeding chunk_size produces multiple chunks."""
    # Create text with 600 words (exceeds chunk_size=512 tokens)
    long_text = " ".join([f"word{i}" for i in range(600)])
    doc = RawDocument(
        source_id="test_source",
        filename="test.txt",
        text=long_text,
        metadata={},
    )
    with patch("agentrag.ingestion.chunker.AutoTokenizer") as mock_at:
        mock_at.from_pretrained.return_value = make_mock_tokenizer()
        chunks = chunk_document(doc, settings)
    assert len(chunks) > 1
    # Each chunk should have token count <= chunk_size
    for chunk in chunks:
        token_count = len(chunk.text.split())
        assert token_count <= settings.chunk_size


def test_consecutive_chunks_overlap(settings: Settings) -> None:
    """Consecutive chunks have overlapping content."""
    long_text = " ".join([f"word{i}" for i in range(600)])
    doc = RawDocument(
        source_id="test_source",
        filename="test.txt",
        text=long_text,
        metadata={},
    )
    with patch("agentrag.ingestion.chunker.AutoTokenizer") as mock_at:
        mock_at.from_pretrained.return_value = make_mock_tokenizer()
        chunks = chunk_document(doc, settings)
    if len(chunks) >= 2:
        # Check character position overlap
        assert chunks[0].end_char > chunks[1].start_char


def test_short_text_produces_one_chunk(settings: Settings) -> None:
    """Text shorter than chunk_size produces exactly one chunk."""
    short_text = " ".join([f"word{i}" for i in range(100)])
    doc = RawDocument(
        source_id="test_source",
        filename="test.txt",
        text=short_text,
        metadata={},
    )
    with patch("agentrag.ingestion.chunker.AutoTokenizer") as mock_at:
        mock_at.from_pretrained.return_value = make_mock_tokenizer()
        chunks = chunk_document(doc, settings)
    assert len(chunks) == 1
    assert chunks[0].index == 0


def test_chunk_id_format(settings: Settings) -> None:
    """chunk_id follows format {source_id}_{index}."""
    text = " ".join([f"word{i}" for i in range(600)])
    doc = RawDocument(
        source_id="testsource",
        filename="test.txt",
        text=text,
        metadata={},
    )
    with patch("agentrag.ingestion.chunker.AutoTokenizer") as mock_at:
        mock_at.from_pretrained.return_value = make_mock_tokenizer()
        chunks = chunk_document(doc, settings)
    for chunk in chunks:
        assert chunk.chunk_id == f"testsource_{chunk.index}"


def test_index_zero_based_and_contiguous(settings: Settings) -> None:
    """Chunk indices are zero-based and contiguous."""
    text = " ".join([f"word{i}" for i in range(600)])
    doc = RawDocument(
        source_id="test_source",
        filename="test.txt",
        text=text,
        metadata={},
    )
    with patch("agentrag.ingestion.chunker.AutoTokenizer") as mock_at:
        mock_at.from_pretrained.return_value = make_mock_tokenizer()
        chunks = chunk_document(doc, settings)
    indices = [c.index for c in chunks]
    assert indices == list(range(len(chunks)))
