# Mission

## Why This Project Exists

> AgentRAG gives Claude a persistent, private memory over your documents — local, semantic, and zero-config.

AI models like Claude are powerful reasoners — but they are blind to your
private data. Every session starts from zero. Documents, notes, codebases,
research papers, books: none of it is accessible unless you paste it in
manually, which is slow, lossy, and breaks at context limits.

AgentRAG closes that gap. It is a locally-running MCP server that gives Claude
a persistent, semantically-indexed memory over any private data the user brings
in. Claude calls into AgentRAG the same way it calls any other tool — and gets
back the right chunk of information, from the right document, ranked by
relevance.

---

## Target Audience

AgentRAG is built for anyone who works with private data that
Claude has never seen — and who wants AI reasoning over it
without sending that data to the cloud. A minimum of Python
literacy is assumed: users can run `pip install` and edit a
JSON config file.

| User | What they bring | What AgentRAG gives them |
|------|----------------|--------------------------|
| Developer / Engineer | Codebases, API docs, internal wikis | Claude answers questions over real project context, not hallucinated docs |
| Researcher / Academic | PDFs, papers, books, lab notes | Semantic search across a private corpus without uploading to any service |
| Knowledge worker | Reports, contracts, manuals | Query large document collections in plain language |
| Power user / tinkerer | Mixed private data | Full local control over AI memory — no cloud, no vendor |
| Student / Learner | Textbooks, lecture notes, course material | AI-assisted study over their own materials, fully offline |
| Writer / Content creator | Research notes, drafts, references | Query their own writing corpus while drafting |
| Legal / Compliance professional | Contracts, regulations, case files | Sensitive documents stay on-machine, never leave the local environment |
| Data scientist / ML engineer | Experiment logs, model cards, dataset docs | Claude reasons over ML artifacts without external exposure |

---

## Core Goals

1. **Zero-friction ingestion.** A user points AgentRAG at a file or directory.
   One command. The data is chunked, embedded, and stored. No configuration
   beyond a data directory path.

2. **Semantic retrieval, not keyword search.** Queries return the most
   semantically relevant chunks, not just files that contain the search term.
   The user asks a question; AgentRAG finds the answer's location.

3. **Native MCP interface.** Claude calls AgentRAG tools (`ingest_file`,
   `search_documents`, etc.) the same way it calls any MCP server. No custom
   prompting required to activate retrieval.

4. **Fully local by default.** No data leaves the user's machine. Embeddings
   are generated locally via `sentence-transformers`. The vector store (Qdrant)
   runs in-process. No API keys required for core functionality.

5. **Privacy by default.** No telemetry, no analytics, no phone-home. Data
   never leaves the local machine under any default configuration unless the
   user explicitly opts into a future cloud feature.

6. **Distributable as a standard Python package.** Users install AgentRAG with
   `pip install agentrag` or run it zero-install with `uvx agentrag serve`.
   Claude Desktop picks it up via a two-line config addition.

---

## Non-Goals

- **Not a hosted service.** AgentRAG is a local tool. There is no cloud backend,
  no user accounts, no SaaS offering — at least not in the current scope.

- **Not a general LLM framework.** AgentRAG does not wrap LangChain or
  LlamaIndex. It is intentionally narrow: ingest, store, retrieve. Reasoning
  happens in Claude, not in AgentRAG.

- **Not a web scraper (yet).** Phase 1 handles local files only. URL ingestion
  is a future phase and must not leak into earlier implementation.

- **Not a multi-user system.** The current design is single-user, single
  machine. Multi-tenancy is out of scope unless explicitly added to the roadmap.

---

## Design Principles

| Principle | What it means in practice |
|-----------|--------------------------|
| **Local first** | Everything works offline. External APIs are opt-in, never required. |
| **Narrow and correct** | Do one thing well. Ingest. Retrieve. Nothing more. |
| **Transparent to Claude** | Claude should not need special prompting to use AgentRAG. It just works as a tool. |
| **Zero vendor lock-in** | The vector store, embedding model, and LLM are all swappable via config. |
| **60-second onboarding** | A user with Python installed should be running AgentRAG within 60 seconds of reading the README. |
| **Privacy by design** | No telemetry, no analytics, no network calls unless the user explicitly configures one. |

---

## Success Criteria

AgentRAG succeeds when:

- A new user goes from zero to a running MCP server in under 60 seconds.
- Claude retrieves the correct document chunk for a query without any special prompting from the user.
- No private data ever leaves the local machine under any default configuration.
- The full test suite passes with zero failures on a clean install.
- Re-ingesting the same file produces identical results (idempotent).
