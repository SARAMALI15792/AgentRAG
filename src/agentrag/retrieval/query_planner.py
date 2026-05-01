"""Query planner — decomposes queries via Gemini with graceful degrade."""

from __future__ import annotations

import json
import logging

try:
    from google import genai
except ImportError:
    genai = None  # type: ignore[assignment]

from agentrag.config import Settings
from agentrag.types import QueryPlan

logger = logging.getLogger(__name__)

_PROMPT = """\
Decompose the following query into 1 to 4 focused sub-questions that together \
cover the full intent. Return ONLY a JSON array of strings. No explanation.

Query: {query}
"""


def _default_plan(query: str) -> QueryPlan:
    """Fallback: single-item plan with original query."""
    return QueryPlan(original_query=query, sub_queries=[query])


def plan(query: str, settings: Settings) -> QueryPlan:
    """Decompose a query into sub-queries via Gemini. Never raises."""
    if not settings.google_api_key or genai is None:
        return _default_plan(query)

    try:
        client = genai.Client(api_key=settings.google_api_key)
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=_PROMPT.format(query=query),
        )
        sub_queries: list[str] = json.loads(response.text or "")
        if not isinstance(sub_queries, list) or not sub_queries:
            return _default_plan(query)
        return QueryPlan(original_query=query, sub_queries=sub_queries)
    except Exception:
        logger.warning("Query planner degraded for query: %r", query, exc_info=True)
        return _default_plan(query)
