"""Chunk evaluator — scores chunk relevance via Gemini with graceful degrade."""

from __future__ import annotations

import json
import logging
from typing import Any

try:
    from google import genai
except ImportError:
    genai = None  # type: ignore[assignment]

from agentrag.config import Settings
from agentrag.types import ChunkScore, EvaluationReport, SearchResult

logger = logging.getLogger(__name__)

_PROMPT = """\
Score each chunk's relevance to the query. Return ONLY a JSON array where each \
element has: chunk_id (string), score (float 0.0–1.0), reason (one sentence), \
and optionally suggested_query (string) when score < 0.7.

Query: {query}

Chunks:
{chunks}
"""

_DEGRADE_SCORE = 0.5


def _degrade_report(query: str, results: list[SearchResult]) -> EvaluationReport:
    """Fallback: score all chunks at 0.5, sufficient=True."""
    scored = [
        ChunkScore(
            chunk_id=r.chunk_id,
            source_id=r.source_id,
            score=_DEGRADE_SCORE,
            reason="Graceful degrade — Gemini unavailable",
        )
        for r in results
    ]
    return EvaluationReport(
        query=query,
        scored_chunks=scored,
        sufficient=True,
        suggested_queries=[],
    )


def evaluate(
    query: str,
    results: list[SearchResult],
    settings: Settings,
) -> EvaluationReport:
    """Score chunks for relevance to query via Gemini. Never raises."""
    if not results:
        return EvaluationReport(
            query=query,
            scored_chunks=[],
            sufficient=False,
            suggested_queries=[],
        )

    if not settings.google_api_key or genai is None:
        return _degrade_report(query, results)

    chunks_text = "\n".join(f"[{r.chunk_id}] {r.text[:300]}" for r in results)

    try:
        client = genai.Client(api_key=settings.google_api_key)
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=_PROMPT.format(query=query, chunks=chunks_text),
        )
        raw: Any = json.loads(response.text or "[]")
        if not isinstance(raw, list):
            return _degrade_report(query, results)

        result_map = {r.chunk_id: r for r in results}
        scored: list[ChunkScore] = []
        suggested: list[str] = []

        for item in raw:
            chunk_id = str(item.get("chunk_id", ""))
            raw_score = float(item.get("score", _DEGRADE_SCORE))
            score = max(0.0, min(1.0, raw_score))
            reason = str(item.get("reason", ""))
            src = result_map.get(chunk_id)
            scored.append(
                ChunkScore(
                    chunk_id=chunk_id,
                    source_id=src.source_id if src else "",
                    score=score,
                    reason=reason,
                )
            )
            if score < 0.7 and item.get("suggested_query"):
                suggested.append(str(item["suggested_query"]))

        sufficient = any(cs.score >= 0.7 for cs in scored)
        return EvaluationReport(
            query=query,
            scored_chunks=scored,
            sufficient=sufficient,
            suggested_queries=suggested,
        )
    except Exception:
        logger.warning("Evaluator degraded for query: %r", query, exc_info=True)
        return _degrade_report(query, results)
