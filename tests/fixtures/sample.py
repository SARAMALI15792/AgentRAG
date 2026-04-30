"""Sample Python module used as a test fixture for AgentRAG ingestion."""

from __future__ import annotations


def chunk_text(text: str, size: int, overlap: int) -> list[str]:
    """Split text into overlapping chunks of the given token size."""
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = min(start + size, len(words))
        chunks.append(" ".join(words[start:end]))
        if end == len(words):
            break
        start += size - overlap
    return chunks


def embed_chunks(chunks: list[str], model_name: str) -> list[list[float]]:
    """Generate embeddings for a list of text chunks using a local model."""
    # In production this calls sentence-transformers
    return [[0.0] * 384 for _ in chunks]


def compute_source_id(file_path: str) -> str:
    """Compute a stable 16-character hex identifier for a file path."""
    import hashlib

    return hashlib.sha256(file_path.encode()).hexdigest()[:16]


def merge_results(
    results_a: list[dict[str, float]],
    results_b: list[dict[str, float]],
) -> list[dict[str, float]]:
    """Merge two ranked result lists, deduplicating by chunk_id."""
    seen: set[str] = set()
    merged = []
    for result in results_a + results_b:
        cid = result.get("chunk_id", "")
        if cid not in seen:
            seen.add(cid)
            merged.append(result)
    return sorted(merged, key=lambda r: r.get("score", 0.0), reverse=True)
