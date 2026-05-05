"""Benchmark script — ingests sample corpus, runs 10 queries, logs results.

Not a CI gate. Exits 0 regardless of scores (Article XII.4).
Run with: uv run python scripts/benchmark_retrieval.py
"""

from __future__ import annotations

import logging
import tempfile
import time
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

FIXTURES = Path(__file__).parent.parent / "tests" / "fixtures"

QUERIES = [
    "What is the main topic of this document?",
    "Describe the key concepts covered.",
    "What are the important details mentioned?",
    "Summarize the content in a few words.",
    "What examples are provided in the text?",
    "What technical terms appear in this content?",
    "What is the purpose or goal described?",
    "What data or numbers are mentioned?",
    "What steps or processes are described?",
    "What conclusions can be drawn from this material?",
]


def main() -> None:
    """Ingest fixture files, run 10 queries, log scores and timing."""
    with tempfile.TemporaryDirectory() as tmp:
        from agentrag.config import Settings
        from agentrag.ingestion.pipeline import ingest
        from agentrag.retrieval.searcher import search

        settings = Settings(data_dir=Path(tmp))

        # Ingest text fixtures for a representative corpus
        fixture_files = [
            FIXTURES / "sample.txt",
            FIXTURES / "sample.md",
            FIXTURES / "sample.pdf",
        ]
        logger.info("=== AgentRAG Retrieval Benchmark ===\n")
        logger.info("Ingesting corpus...")
        for path in fixture_files:
            if path.exists():
                result = ingest(path, settings)
                logger.info("  ingested %s → %d chunks", path.name, result.chunk_count)

        logger.info("")

        # Run 10 queries and log results + timing
        for i, query in enumerate(QUERIES, start=1):
            start = time.perf_counter()
            results = search(query, top_k=3, settings=settings)
            elapsed = time.perf_counter() - start

            logger.info("Query %2d [%.3fs]: %s", i, elapsed, query)
            for rank, r in enumerate(results, start=1):
                logger.info(
                    "  #%d score=%.4f file=%-15s chunk=%s",
                    rank,
                    r.score,
                    r.filename,
                    r.chunk_id,
                )
            logger.info("")

        logger.info("=== Benchmark complete ===")


if __name__ == "__main__":
    main()
