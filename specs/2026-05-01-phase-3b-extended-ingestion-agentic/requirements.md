# Phase 3B — Requirements

> Extended Ingestion & Agentic Retrieval

---

## Scope

This phase transforms AgentRAG from a 7-format ingestion tool into a 20+
format universal ingestion engine with agentic retrieval capabilities. Two
independent workstreams converge:

1. **Extended ingestion** — office, ebook, structured data, web, subtitle,
   and email readers, all registered through a plugin registry.
2. **Agentic retrieval** — Gemini-powered query decomposition, multi-query
   search, and relevance evaluation exposed as MCP tools.

---

## What Is In Scope

- Reader plugin registry (`reader_registry.py`) replacing `reader.py` if/elif
- 9 new file type readers: `.xlsx`, `.pptx`, `.csv`, `.epub`, `.mobi`,
  `.json`, `.yaml/.yml`, `.xml`, `.toml`
- 3 additional readers: `.srt`, `.vtt` (subtitles), `.eml`, `.mbox` (email)
- URL ingestion via `httpx` + BeautifulSoup
- `ingest_url` MCP tool
- `QueryPlan`, `ChunkScore`, `EvaluationReport` domain types
- `query_planner.py` — Gemini-backed query decomposition
- `evaluator.py` — Gemini-backed chunk relevance scoring
- `plan_query`, `search_multi`, `evaluate_chunks` MCP tools
- Integration tests for all new file types and agentic loop
- `scripts/verify_phase3b.sh` exit gate

## What Is NOT In Scope

- Cross-encoder re-ranking (Phase 4)
- Concurrent upsert safety (Phase 4)
- Benchmark scripts (Phase 4)
- Metadata filter hardening (Phase 4)
- Multi-collection / streaming retrieval (Phase 6)
- PyPI distribution / packaging (Phase 5)
- Cloud sync (Phase 7)
- Any changes to `chunker.py`, `embedder.py`, or `store/qdrant.py` unless
  fixing a bug surfaced by new readers

---

## Key Decisions

### D1 — Reader Plugin Registry Over if/elif

The existing `reader.py` dispatches via an if/elif chain. With 20+ file types,
this becomes unmaintainable. A registry pattern is the correct abstraction per
Article IV.5 exception and Article XIV. The registry uses lazy imports to avoid
loading unused optional dependencies at startup.

### D2 — Gemini Free Tier for Agentic Retrieval

Google AI Studio provides a free tier for Gemini 2.0 Flash with generous
quotas. This avoids requiring users to pay for agentic features. The
`google-genai` SDK (not `google-generativeai` — that's the old name) is the
official Python SDK.

### D3 — Graceful Degradation is Non-Negotiable

Both `query_planner.py` and `evaluator.py` must work when:
- `AGENTRAG_GOOGLE_API_KEY` is not set
- Gemini API is unreachable (network, quota, 5xx)
- Gemini returns invalid JSON

In all cases: return a sensible default (single-query plan, 0.5 scores),
never raise, never block the retrieval pipeline.

### D4 — mobi Library Inclusion

`mobi` (0.3.x) is a small library with limited maintenance. Included because
the roadmap commits to it and MOBI is a common ebook format. If it proves
unreliable, we can gate it behind a try/except with an actionable error and
remove it in a future phase.

### D5 — httpx Dual Role

`httpx` is already a dev dependency (test client). For URL ingestion, it
becomes an optional runtime dependency under the `[web]` group. This avoids
adding a second HTTP library.

### D6 — Reader Function Purity

Reader functions are pure: `(Path) -> str`. No state, no side effects, no
internal imports except `agentrag.types` (if needed). This makes them trivially
testable and keeps the dependency graph clean.

### D7 — Agentic Tools Are Thin Delegates

`plan_query`, `search_multi`, `evaluate_chunks` in `tools.py` must each be
≤15 lines of business logic (Article IV.1). All real logic lives in
`query_planner.py`, `evaluator.py`, and `searcher.py`.

---

## Open Risks

### R1 — Gemini API Rate Limits

The free tier has per-minute and per-day rate limits. If a user hammers
`plan_query` + `evaluate_chunks` in a tight loop, they may hit quota. The
graceful degrade path handles this, but the user experience degrades.

**Mitigation:** Document rate limits in README. Consider a local cache for
repeated identical queries in a future phase.

### R2 — mobi Library Stability

`mobi` 0.3.x has not been updated recently. It may not handle all MOBI
variants (DRM, KF8).

**Mitigation:** Catch all exceptions from `mobi`, return actionable error.
If the library is abandoned, replace with a different approach or drop MOBI
support with user approval.

### R3 — MCP SDK Compatibility

The MCP Python SDK (pinned at 1.27.0) must support registering 10 tools
(7 existing + 3 new). No known issue, but the SDK is young and breaking
changes happen.

**Mitigation:** Pin exact version. Test tool registration in integration tests.

### R4 — ebooklib XHTML Parsing

EPUB files contain XHTML chapters that vary in structure. `ebooklib` + 
BeautifulSoup should handle most cases, but malformed EPUBs may produce
empty text.

**Mitigation:** Raise `ValueError` on empty extraction per Article XIV.2
contract. User gets actionable error.

### R5 — Large File Performance

New file types (especially `.xlsx` with many sheets, large EPUBs) may exceed
the 5-second target for files under 1MB. The timeout mechanism
(`AGENTRAG_INGEST_TIMEOUT`) protects against hangs, but may need tuning.

**Mitigation:** Monitor during integration testing. Adjust targets in
Article XII if needed with user approval.

---

## Dependencies (New)

| Library | Version | Group | Purpose |
|---------|---------|-------|---------|
| `openpyxl` | 3.1.x | `[office]` | Excel `.xlsx` reading |
| `python-pptx` | 1.0.x | `[office]` | PowerPoint `.pptx` reading |
| `ebooklib` | 0.18.x | `[ebooks]` | EPUB reading |
| `mobi` | 0.3.x | `[ebooks]` | MOBI reading |
| `PyYAML` | 6.x | runtime | YAML reading |
| `pysrt` | 1.1.x | `[web]` | SRT subtitle parsing |
| `webvtt-py` | 0.5.x | `[web]` | VTT subtitle parsing |
| `httpx` | 0.27.x | `[web]` (runtime) | URL fetching |
| `google-genai` | 1.x | runtime | Gemini API for agentic retrieval |

---

## Test Fixtures Required

| File | Format | Content |
|------|--------|---------|
| `sample.xlsx` | Excel | 2 sheets, header row + 5 data rows each |
| `sample.pptx` | PowerPoint | 3 slides with title + body text |
| `sample.csv` | CSV | Header + 10 rows of sample data |
| `sample.epub` | EPUB | 2 chapters of sample text |
| `sample.json` | JSON | Nested object with arrays |
| `sample.yaml` | YAML | Multi-level config structure |
| `sample.xml` | XML | Simple element tree with text content |
| `sample.toml` | TOML | Config-style key-value structure |
| `sample.srt` | SRT | 5 subtitle entries with timestamps |
| `sample.eml` | Email | Headers + plain text body |
