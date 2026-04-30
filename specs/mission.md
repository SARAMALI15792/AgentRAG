# Mission

## Why This Project Exists

> AgentRAG gives Claude a persistent, private memory over your documents — local, semantic, and zero-config.

AI models like Claude are powerful reasoners — but they are blind to your
private data. Every session starts from zero. Documents, notes, codebases,
research papers, books, spreadsheets, presentations, emails, web pages: none
of it is accessible unless you paste it in manually, which is slow, lossy,
and breaks at context limits.

AgentRAG closes that gap. It is a locally-running MCP server that gives Claude
a persistent, semantically-indexed memory over any private data the user brings
in — regardless of format. Claude calls into AgentRAG the same way it calls
any other tool — and gets back the right chunk of information, from the right
document, ranked by relevance.

---

## Target Audience

AgentRAG is built for anyone who works with private data that
Claude has never seen — and who wants AI reasoning over it
without sending that data to the cloud. A minimum of Python
literacy is assumed: users can run `pip install` and edit a
JSON config file.

| User | What they bring | What AgentRAG gives them |
|------|----------------|--------------------------|
| Developer / Engineer | Codebases, API docs, internal wikis, notebooks | Claude answers questions over real project context, not hallucinated docs |
| Researcher / Academic | PDFs, papers, books (EPUB/MOBI), lab notes | Semantic search across a private corpus without uploading to any service |
| Knowledge worker | Reports, contracts, manuals, spreadsheets, presentations | Query large document collections in plain language |
| Power user / tinkerer | Mixed private data in any format | Full local control over AI memory — no cloud, no vendor |
| Student / Learner | Textbooks (EPUB), lecture notes, course material, video subtitles | AI-assisted study over their own materials, fully offline |
| Writer / Content creator | Research notes, drafts, references, web clippings | Query their own writing corpus while drafting |
| Legal / Compliance professional | Contracts, regulations, case files, emails | Sensitive documents stay on-machine, never leave the local environment |
| Data scientist / ML engineer | Experiment logs, model cards, dataset docs, YAML configs, notebooks | Claude reasons over ML artifacts without external exposure |
| Business analyst | Excel spreadsheets, CSV data, PowerPoint decks, JSON/XML reports | Semantic search over structured business data |

---

## Core Goals

1. **Universal ingestion.** AgentRAG ingests any file the user throws at it —
   documents, books, code, spreadsheets, presentations, structured data, web
   pages, emails, subtitles. One command, any format. Unsupported formats fail
   with an actionable error, never silently.

2. **Semantic retrieval, not keyword search.** Queries return the most
   semantically relevant chunks, not just files that contain the search term.
   The user asks a question; AgentRAG finds the answer's location.

3. **Agentic retrieval.** Claude doesn't just search once — it decomposes
   complex queries, searches multiple angles, evaluates whether results are
   sufficient, and re-searches if needed. All through native MCP tool calls.

4. **Native MCP interface.** Claude calls AgentRAG tools (`ingest_file`,
   `search_documents`, `plan_query`, etc.) the same way it calls any MCP
   server. No custom prompting required to activate retrieval.

5. **Fully local by default.** No data leaves the user's machine. Embeddings
   are generated locally via `sentence-transformers`. The vector store (Qdrant)
   runs in-process. No API keys required for core functionality.

6. **Privacy by default.** No telemetry, no analytics, no phone-home. Data
   never leaves the local machine under any default configuration unless the
   user explicitly opts into cloud sync (Phase 8).

7. **Distributable as a standard Python package.** Users install AgentRAG with
   `pip install agentrag` or run it zero-install with `uvx agentrag serve`.
   Claude Desktop picks it up via a two-line config addition. Optional
   dependency groups (`agentrag[office]`, `agentrag[ebooks]`, `agentrag[all]`)
   keep the base install lightweight.

8. **Workspace isolation.** Users maintain separate knowledge bases (one per
   project, client, or topic) via named Qdrant collections. Data from one
   workspace never leaks into another.

---

## Non-Goals

- **Not a hosted service.** AgentRAG is a local tool. There is no cloud backend,
  no user accounts, no SaaS offering — at least not in the current scope.

- **Not a general LLM framework.** AgentRAG does not wrap LangChain or
  LlamaIndex. It is intentionally narrow: ingest, store, retrieve. Reasoning
  happens in Claude, not in AgentRAG.

- **Not a multi-user system.** The current design is single-user, single
  machine. Multi-tenancy is out of scope unless explicitly added to the roadmap.

- **Not a file converter.** AgentRAG extracts text for semantic indexing. It
  does not convert between formats, render documents, or preserve formatting.

---

## Design Principles

| Principle | What it means in practice |
|-----------|--------------------------|
| **Local first** | Everything works offline. External APIs are opt-in, never required. |
| **Universal and correct** | Ingest any format the user has. Fail clearly on unsupported ones. |
| **Transparent to Claude** | Claude should not need special prompting to use AgentRAG. It just works as a tool. |
| **Zero vendor lock-in** | The vector store, embedding model, and LLM are all swappable via config. |
| **60-second onboarding** | A user with Python installed should be running AgentRAG within 60 seconds of reading the README. |
| **Privacy by design** | No telemetry, no analytics, no network calls unless the user explicitly configures one. |
| **Performance-aware** | Ingestion and retrieval must meet defined performance targets (Article XI). Large files and corpora are first-class use cases. |
| **Extensible by design** | New file types are added by registering a reader function — no changes to core pipeline code (Article IV.6). |
| **Actionable errors** | Every error the user sees must tell them what went wrong and how to fix it (Article XII). |

---

## Success Criteria

AgentRAG succeeds when:

- A new user goes from zero to a running MCP server in under 60 seconds.
- Claude retrieves the correct document chunk for a query without any special prompting from the user.
- No private data ever leaves the local machine under any default configuration.
- The full test suite passes with zero failures on a clean install.
- Re-ingesting the same file produces identical results (idempotent).
- Any file type the user has can be ingested — or fails with an error that names the missing dependency.
- Agentic retrieval (plan → search → evaluate → re-search) completes a complex query in under 10 seconds.
- A user with 10,000 documents can search their corpus with sub-second latency.
