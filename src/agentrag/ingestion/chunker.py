"""Text chunker — splits RawDocument into overlapping token-based chunks."""

from __future__ import annotations

import logging

from transformers import AutoTokenizer

from agentrag.config import Settings
from agentrag.types import Chunk, RawDocument

logger = logging.getLogger(__name__)


def chunk_document(doc: RawDocument, settings: Settings) -> list[Chunk]:
    """Split document text into overlapping chunks using token-based sliding window."""
    tokenizer = AutoTokenizer.from_pretrained(settings.embed_model)
    token_ids: list[int] = tokenizer.encode(doc.text)

    chunks: list[Chunk] = []
    start = 0
    index = 0
    char_offset = 0

    while start < len(token_ids):
        end = min(start + settings.chunk_size, len(token_ids))
        chunk_tokens = token_ids[start:end]
        decoded = tokenizer.decode(chunk_tokens, skip_special_tokens=True)
        chunk_text = decoded if isinstance(decoded, str) else " ".join(decoded)

        # Approximate character positions
        start_char = char_offset
        end_char = char_offset + len(chunk_text)

        chunks.append(
            Chunk(
                chunk_id=f"{doc.source_id}_{index}",
                source_id=doc.source_id,
                text=chunk_text,
                start_char=start_char,
                end_char=end_char,
                index=index,
            )
        )

        # Advance by (chunk_size - overlap) tokens
        step = settings.chunk_size - settings.chunk_overlap
        start += step

        # Compute overlap text length to adjust char_offset correctly
        if start < len(token_ids):
            # Decode the overlap region to get its character length
            overlap_start = max(0, start - settings.chunk_overlap)
            overlap_tokens = token_ids[overlap_start:start]
            decoded_overlap = tokenizer.decode(overlap_tokens, skip_special_tokens=True)
            overlap_text = (
                decoded_overlap
                if isinstance(decoded_overlap, str)
                else " ".join(decoded_overlap)
            )
            # Move char_offset forward by step tokens, minus overlap length
            char_offset = start_char + (len(chunk_text) - len(overlap_text))

        index += 1

    return chunks
