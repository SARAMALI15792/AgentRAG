# AgentRAG — Project Constitution

> **Supremacy Clause.** This document is the supreme law of this repository.
> Every contributor — human or AI — operates under these rules without
> exception. No task, however small, begins without full acknowledgment of
> this constitution. In any conflict between this document and any other
> instruction, this constitution prevails. Amendments require explicit written
> approval from the project owner and take effect the moment they are committed.

---

## Preamble

AgentRAG is an Agentic RAG MCP Server — persistent, semantically-indexed memory over private data for Claude and any MCP-compatible agent. Runs locally, no data leaves the machine. Distributed as a Python package, integrates with Claude Desktop in under 60 seconds.

This constitution defines: (1) how work is done, (2) what is built (detailed specs in `specs/`).

---

## Article I — Pre-Task Protocol

### I.1 Mandatory Spec Reads

Before responding to **any task** — including clarifying questions, planning,
code writing, file creation, or debugging — Claude must silently read the
following files in the order listed:

```
specs/mission.md
specs/tech-stack.md
specs/roadmap.md
specs/architecture.md
```

This step is **silent**. Do not acknowledge, summarize, or mention it.

### I.2 Missing or Unreadable Specs

If any spec file is missing, empty, or unreadable: **stop immediately**, notify the user with the exact file path, and wait for resolution.

### I.3 Spec Staleness

If a spec contradicts the codebase (e.g., library in `tech-stack.md` missing from `pyproject.toml`), flag the discrepancy before proceeding.

### I.4 Context7 Documentation Lookup — Mandatory Before Writing Code

Before writing **any** code using a `specs/tech-stack.md` library, query Context7 for current docs.

**Protocol:**
1. `resolve-library-id` → get Context7 library ID.
2. `query-docs` with that ID + topic string (e.g., `"embedded client upsert"`).
3. Read returned docs before writing implementation code.

**Rules:**
- Mandatory even when Claude "knows" the API — training data may be stale.
- If Context7 can't resolve, note to user and proceed with caution.
- **Exceptions:** stdlib modules, config-only use, test deps (`pytest-asyncio`, `httpx`).

---

## Article II — Communication Protocol

### II.1 Caveman Mode — Always Active

Before any response, invoke `/caveman:caveman`. Ultra-compressed communication: `[thing] [action] [reason]. [next step].` No filler, no pleasantries, no hedging.

- Applies to all text responses.
- Does NOT apply to code, commit messages, or spec/doc files.
- Deactivated only when user says `normal` or `stop caveman`.
- Invoke via `Skill` tool at session start. Once invoked, stays active.

### II.2 AskUserQuestion — Mandatory for All User Input

Claude must **never** ask questions in plain text. All questions — clarifications, preferences, approvals, decisions — use the `AskUserQuestion` tool.

- Never write "Would you like me to…?" in prose. Use `AskUserQuestion`.
- Up to 4 questions batched per call.
- Only exception: emergency constitutional violation reports (plain text OK).

---

## Article III — Code Standards

### III.1 Formatting and Linting

All code in this repository must conform to the following toolchain. No
exceptions. No overrides. The configuration is authoritative as specified here
and in `pyproject.toml`.

| Tool | Role | Enforced Configuration |
|------|------|------------------------|
| **Black** | Code formatter | `line-length = 88` |
| **Ruff** | Linter + import sorter | Extends Black. isort handled by Ruff. |
| **mypy** | Static type checker | `--strict` mode. No suppressions without justification. |

Pre-commit check: `uv run black . && uv run ruff check . && uv run mypy src/`
Must pass with zero errors/warnings before any commit.

### III.2 Type Annotation Policy

Type annotations are not optional and not stylistic. They are a correctness
tool. The following rules are absolute:

- Every **public function** (no leading underscore) must have fully annotated
  parameters and return type, including `-> None` for functions that return
  nothing.
- Every **public method** on any class must be fully annotated, including
  `self` where mypy requires it.
- Every **module-level variable** must be annotated if its type is not
  immediately obvious from the assignment.
- Every **private function or method** (`_foo`) must be annotated wherever the
  type is non-trivial. A trivial type is one a reader can infer in under two
  seconds without looking anything up.
- `Any` is permitted only when genuinely unavoidable (e.g., deserializing
  external JSON of unknown shape). Every use of `Any` must be accompanied by
  an inline comment explaining why it cannot be made more specific.
- `# type: ignore` is forbidden unless accompanied by an inline comment
  identifying the exact mypy error being suppressed and the reason suppression
  is the only viable option. Vague `# type: ignore` comments will be treated
  as a code review failure.
- Generic types must be fully parameterized: `list[str]`, not `list`;
  `dict[str, Any]`, not `dict`; `Optional[str]` may be written as `str | None`
  (preferred in Python 3.10+).

### III.3 Comment and Documentation Policy

Comments and docstrings are allowed and encouraged when they add genuine
clarity. They must be **short and precise** — one line maximum per comment,
one-line summary for docstrings. Verbosity is the only violation.

Rules:

- **Docstrings** on every public and private function, method, and class:
  one-line summary sentence only. No parameter lists repeated in prose.
  No multi-paragraph explanations. If a function needs more than one sentence
  to describe, the function needs refactoring.
- **Inline comments** are permitted on any line or block where the intent is
  not immediately obvious from the code alone. Keep them short and precise —
  one line, no trailing essays. Both WHAT and WHY are valid subjects when
  the name alone leaves ambiguity.
- **No task-tracking in source comments.** Comments like "added for issue #42",
  "TODO: fix this later", "used by the ingest flow" are forbidden. That
  information belongs in commit messages, PR descriptions, and issue trackers —
  not in source files that outlive the context they were written in.
- **No commented-out code.** If code is removed, it is removed. Git preserves
  history. Commented-out code is archaeology that rots in place.
- **No multi-line comment blocks.** If a concept requires a paragraph, it
  belongs in the spec or a PR description — not in source. One line per
  comment. No exceptions.

### III.4 Testing Discipline — Test-Driven Development

Test-Driven Development is **mandatory** in this repository. This is not a
preference. It is a constitutional requirement. The workflow is:

1. Write a failing test that precisely specifies the desired behavior.
2. Run the test and confirm it fails for the right reason.
3. Write the minimum implementation to make the test pass.
4. Run the test and confirm it passes.
5. Refactor if needed. Re-run. Still green.
6. Only then is the task considered complete.

Additional testing rules:

- Every public function must have at minimum one unit test covering its primary
  behavior, and additional tests for each distinct edge case or error path.
- Unit tests live in `tests/unit/`. They test a single unit in isolation.
  External dependencies (Qdrant, file system, network) are mocked.
- Integration tests live in `tests/integration/`. They test the interaction
  between real components. They may touch the file system and a local Qdrant
  instance, but never a network service.
- `pytest` is the only permitted test runner. The `unittest` module is not
  permitted anywhere in the test suite.
- A task is **not complete** until `pytest` exits with zero failures and zero
  errors. Passing tests with skips is acceptable only if the skip reason is
  documented and approved.
- Coverage is measured but not gated to a specific percentage. Coverage reports
  exist to reveal gaps — not to gamify metric achievement.
- **TYPE_CHECKING guard for test fixtures.** `tests/conftest.py` uses
  `if TYPE_CHECKING:` blocks for all imports of `agentrag.*` types. At
  runtime, these types are imported inside the fixture function body (deferred
  import). This pattern prevents import-time circular dependency errors during
  pytest collection. All future conftest additions must follow this pattern.
- **`numpy` must be an explicit dev dependency.** Test fixtures use
  `numpy` directly (e.g., `np.zeros` for deterministic mock vectors). Do not
  rely on `numpy` being a transitive dependency of `sentence-transformers` —
  declare it explicitly in `pyproject.toml` under `[project.optional-dependencies]`
  `dev`. If `numpy` is missing from dev deps, add it before writing any test
  fixture that constructs vectors.

### III.5 Commit Convention

All commits in this repository follow the
[Conventional Commits](https://www.conventionalcommits.org/) specification.

Permitted type prefixes:

| Prefix | Use for |
|--------|---------|
| `feat:` | New functionality |
| `fix:` | Bug corrections |
| `chore:` | Tooling, config, dependency updates |
| `test:` | Adding or modifying tests |
| `docs:` | Documentation and spec changes |
| `refactor:` | Code changes that neither add features nor fix bugs |

Rules:
- Subject line: ≤ 50 characters. Imperative mood. No trailing period.
- Body: included only when the reasoning behind the change is not obvious from
  the subject line. The body explains **why**, not **what**.
- `--no-verify` is never used. Pre-commit hooks exist for a reason. If a hook
  fails, investigate and fix the underlying issue — do not bypass it.
- Amending published commits is not permitted. Create a new commit.

### III.6 Development Package Manager — `uv`

This project uses `uv` as the sole development package manager. All tool
invocations during development and CI must go through `uv`.

| Operation | Command |
|-----------|---------|
| Install all deps (incl. dev) | `uv pip install -e ".[dev]"` |
| Run any tool | `uv run <tool> <args>` |
| Run tests | `uv run pytest --tb=short` |
| Run formatter | `uv run black .` |
| Run linter | `uv run ruff check .` |
| Run type checker | `uv run mypy --strict src/` |
| Create venv | `uv venv` |

Rules:
- Never invoke `pip install` directly — always `uv pip install`.
- Never invoke `python -m pytest` or bare `pytest` — always `uv run pytest`.
- The pre-commit hook detects the `.venv` directory and calls tools via the
  venv's `Scripts/` (Windows) or `bin/` (Unix) path directly — this is
  correct and must not be changed.
- `uv.lock` is committed and must be kept in sync with `pyproject.toml`.
  Run `uv lock` after any dependency change.

**Why this is in the constitution:**
`uv` is 10–100× faster than `pip` and produces reproducible installs via
`uv.lock`. Using bare `pip` or `python -m` bypasses the lock file and risks
subtle version divergence between local and CI environments.

### III.7 Post-Implementation Code Review — Mandatory

After writing any implementation code that will be committed, Claude must
invoke the `coderabbit:code-review` skill before staging or committing.

**Protocol:**

1. Complete the implementation and ensure `pytest` is green (Article III.4).
2. Run `uv run black . && uv run ruff check . && uv run mypy --strict src/` and fix all issues.
3. Invoke the `coderabbit:code-review` skill on the changed files.
4. Resolve all **blocking** issues (bugs, logic errors, security, broken
   contracts) before committing. No exceptions.
5. For **non-blocking** issues (style suggestions, minor improvements): either
   fix them or document the decision not to in the commit body.
6. Only after step 4 is satisfied may the commit be staged and pushed.

**Scope:**

- Applies to all Python source files under `src/` and `tests/`.
- Applies after completing each deliverable listed in the active roadmap phase,
  not after every individual file change.
- Does not apply to spec-only changes (`specs/`, `CLAUDE.md`) — those are
  reviewed by the user, not by CodeRabbit.

**Why this is in the constitution:**

TDD (Article III.4) verifies that code does what the tests specify. CodeRabbit
catches what tests cannot: architectural drift, subtle logic bugs, missed edge
cases, security issues, and patterns that will cause pain later. Both gates
must pass. One does not substitute for the other.

---

## Article IV — Architectural Laws

### IV.1 The Separation Principle — Inviolable

> **Ingestion logic and retrieval logic must never occupy the same module,
> function, or file.**

Enforcement:

- Chunking/embedding logic lives **exclusively** in `src/agentrag/ingestion/`.
- Query/ranking logic lives **exclusively** in `src/agentrag/retrieval/`.
- `server/tools.py` handlers are **thin delegates** (≤15 lines of business logic). Exceeding 15 lines → extract to `store/`, `ingestion/`, or `retrieval/`.
- Crossing this boundary requires **explicit written user approval** before any code is written.

### IV.2 Store Abstraction — Single Access Point

All Qdrant interactions go through `src/agentrag/store/qdrant.py` exclusively. This is the **only** file permitted to import `qdrant_client`. If Qdrant is replaced, only this file changes.

### IV.3 Configuration Centralization

All runtime parameters — data directory, embedding model, chunk size, chunk
overlap, server port, transport mode — are defined in one place:
`src/agentrag/config.py` as a `pydantic-settings` `Settings` dataclass.

Rules:
- No magic strings in any module other than `config.py`.
- No hardcoded file paths anywhere in the codebase.
- No environment variable reads outside of `config.py`.
- Any new configuration parameter must be added to `config.py` and to the
  environment variable table in `specs/tech-stack.md` simultaneously.

### IV.4 Dependency Direction

Dependencies in this codebase flow in one direction only. The diagram below
is authoritative:

```
cli.py
  └─▶ ingestion/pipeline.py
  └─▶ server/app.py

server/tools.py
  └─▶ ingestion/pipeline.py
  └─▶ retrieval/searcher.py
  └─▶ store/qdrant.py

retrieval/searcher.py
  └─▶ store/qdrant.py
  └─▶ ingestion/embedder.py   (for query embedding only)

ingestion/pipeline.py
  └─▶ ingestion/reader.py
  └─▶ ingestion/chunker.py
  └─▶ ingestion/embedder.py
  └─▶ store/qdrant.py

store/qdrant.py
  └─▶ (external: qdrant_client only)
```

**Forbidden imports** (any of the following is a constitutional violation):

- `store/` importing from `ingestion/` or `retrieval/` or `server/`
- `retrieval/` importing from `ingestion/` (except `embedder.py` for query embedding)
- `retrieval/` importing from `server/`
- `ingestion/` importing from `retrieval/` or `server/`
- Any two modules at the same layer importing from each other (circular imports)

### IV.5 No Premature Abstraction

No abstractions beyond what the current phase requires. Concrete > pluggable. Only justified exceptions: `store/qdrant.py` (swappability goal in `specs/mission.md`) and reader registry (Article XIV, 15+ file types).

### IV.6 Reader Plugin Registry

All file readers must register through `src/agentrag/ingestion/reader_registry.py`.
See Article XIV for the full specification. This rule takes effect starting
Phase 3B. Until then, the existing `if/elif` chain in `reader.py` remains
valid for Tier 1 readers.

---

## Article V — File Operation Rules

### V.1 Creating Files

Claude must **ask before creating** any file not in the active phase's deliverables or user's instruction. Name the file, location, and purpose. User must confirm.

### V.2 Deleting Files

Claude must **ask before deleting** any file, without exception. Name the path and explain why deletion (not archival/rename). User must confirm.

### V.3 Renaming and Moving Files

Treated as delete-plus-create. Both V.1 and V.2 apply. User may approve both in one message.

### V.4 Bulk Operations

Operations affecting multiple files require a manifest (file path, operation, reason) presented to the user. User approves/rejects as a whole.

### V.5 The `specs/` Directory

- Only reference/specification documents. No source code, generated files, or scratch notes.
- Updates carry same weight as constitution amendments — require explicit user approval.
- Accuracy > completeness. An incorrect spec actively misleads.

**Phase execution subdirectories:** `specs/{YYYY-MM-DD}-{phase-slug}/` with `plan.md`, `requirements.md`, `validation.md`. Created during replan, immutable during implementation, authoritative over `specs/roadmap.md` for that phase.

---

## Article VI — Project Specifications

Detailed context lives in `specs/`. Claude reads these silently before every task (Article I).

| File | Authority | Contents |
|------|-----------|----------|
| `specs/mission.md` | **Why** this project exists | Goals, non-goals, design principles |
| `specs/tech-stack.md` | **What tools** are permitted | Approved libraries, excluded libraries, env vars |
| `specs/roadmap.md` | **What to build and when** | Eight phases with entry/exit conditions and deliverables |
| `specs/architecture.md` | **How** the system is structured | Directory layout, types, data flows, MCP contracts |

### Out-of-Scope Work

Work not in the current phase's deliverables is **out of scope**. No implementing future-phase features unless user explicitly approves the boundary crossing.

---

## Article VII — Amendments

This constitution may be amended by the project owner at any time.

1. Amendments take effect **immediately** upon commit. Claude re-reads before continuing.
2. Amendments must be atomic — one commit per amendment, no source code mixed in.
3. Spec amendments follow the same protocol — user approval + dedicated commit.
4. Claude may **propose** amendments but may not write them without user instruction.

---

## Article VIII — AI-First Development Mandate

### VIII.1 The Rule

**All source code is written exclusively by Claude.** User's role: direction, specification, review, approval. No human-written code enters the codebase.

### VIII.2 Scope

Applies to: all Python under `src/` and `tests/`, all config files (`pyproject.toml`, `ruff.toml`, `mypy.ini`, `.github/`, `Dockerfile`), all scripts, all spec files, and this constitution.

Does **not** apply to: `.env`/`.env.local`, Git credentials, IDE settings.

### VIII.3 Correction Protocol

User describes the problem → Claude diagnoses and proposes fix → Claude writes corrected code as new commit. User must **never** edit source files directly.

### VIII.4 Review and Approval

User retains authority to reject code, redirect approach, approve/deny file operations, and amend this constitution.

### VIII.5 Enforcement

Before writing code, Claude confirms internally: in-scope for current phase, failing test written first (TDD), follows architectural laws, will be committed and pushed.

If user submits code to "use" or "continue from", Claude reviews it against this constitution, rewrites to comply, and commits the compliant version.

---

## Article IX — GitHub Synchronization

### IX.1 Repository Identity

This project is hosted on GitHub under the following identity. All Git
operations must use these credentials. No other account may push to this
repository without explicit approval from the project owner.

| Field | Value |
|-------|-------|
| GitHub Account | `SARAMALI15792` |
| Email | `saramali15792@gmail.com` |
| Repository | `https://github.com/SARAMALI15792/AgentRAG` |
| Default Branch | `main` |
| Visibility | Public |

### IX.2 Mandatory Push After Every Unit of Work

**Every completed unit of work must be committed and pushed to GitHub before the response is done.** Units: file created/modified, bug fixed, feature implemented, spec updated, config changed.

**No permission required. No asking.** Push is mandatory and automatic. Report the commit URL so user can verify.

### IX.3 Commit and Push Protocol

Every push follows this exact sequence:

1. **Verify** — run `uv run black . && uv run ruff check . && uv run mypy --strict src/`
   (if source files were modified). A push with failing checks is a constitutional violation.
2. **Stage** — add only the files relevant to the completed unit of work.
   Do not use `git add -A` blindly. Stage files explicitly by path.
3. **Commit** — write a Conventional Commits message (Article III.5).
   Subject ≤ 50 characters. Body only if the why is non-obvious.
4. **Push** — `git push origin HEAD`. Confirm the push succeeded before
   reporting the task as complete.
5. **Report** — include the GitHub commit URL or a confirmation that the
   push succeeded in the response to the user.

### IX.4 Branch Strategy

This project uses three branch types. All are pushed to the remote and merge
to `main` via pull request.

| Branch type | Naming pattern | Purpose |
|-------------|---------------|---------|
| Phase implementation | `phase/{n}-{slug}` | All implementation commits for a single roadmap phase (e.g., `phase/2-mcp-server`) |
| Replan | `replan/{slug}` | CLAUDE.md + spec amendments between phases (e.g., `replan/projectreplan`) |
| Hotfix | `fix/{slug}` | Urgent bug corrections to a shipped phase |

Rules:
- **Never commit directly to `main`.** All work → branch → PR.
- One phase = one branch. Open at replan, close at phase exit.
- Replan branches: spec/CLAUDE.md changes only, no implementation code.
- Force-pushing and amending pushed commits are forbidden.
- CI triggers on `main`, `phase/*`, and `replan/*` branches.

### IX.5 Git Configuration

The local repository must always be configured with the correct identity.
Claude must verify this is set before the first commit in any session:

```bash
git config user.name "SARAMALI15792"
git config user.email "saramali15792@gmail.com"
```

If these values are not set, set them before staging anything.

---

## Article X — Enforcement

### X.1 Self-Audit

Before delivering any response that includes code, Claude must internally
verify:

- [ ] Caveman mode is active (Article II).
- [ ] Specs were read at session start (Article I).
- [ ] All new code passes `black`, `ruff`, and `mypy --strict` mentally (Article III).
- [ ] Tests were written before implementation (Article III.4).
- [ ] No file was created or deleted without approval (Article V).
- [ ] No business logic leaked into `server/tools.py` (Article IV.1).
- [ ] No ingestion logic appears in `retrieval/` or vice versa (Article IV.1).
- [ ] No new dependency was added without appearing in `specs/tech-stack.md` (Article IV.3).
- [ ] No human-written code entered the codebase (Article VIII).
- [ ] `coderabbit:code-review` run and all blocking issues resolved (Article III.7).
- [ ] Phase verify script passes (Article XI).
- [ ] Performance targets not regressed (Article XII).
- [ ] All errors are actionable — no bare exceptions or generic messages (Article XIII).
- [ ] New readers registered via plugin registry, not hardcoded (Article XIV).
- [ ] Changes committed and pushed to `github.com/SARAMALI15792/AgentRAG` (Article IX).

### X.2 Violations

If Claude detects that it has violated any article of this constitution:

1. Stop the current action immediately.
2. Acknowledge the violation explicitly to the user.
3. Describe what was done incorrectly and which article was violated.
4. Propose a corrective action and wait for user approval before proceeding.

Self-detected violations are not failures — they are the constitution working
as intended. The failure would be continuing after detecting a violation.

---

## Article XI — Phase Exit Gates — Mandatory Verification

### XI.1 The Rule

**No phase may be declared complete without its verify script exiting 0.**

Every roadmap phase (3B, 3C, 4, 5, 6, 7, 8) has a dedicated exit gate script
in `scripts/verify_phase{N}.sh`. This script is the authoritative arbiter of
phase completion — not human judgment, not passing tests alone, not "it looks
done."

### XI.2 Verify Script Requirements

Every verify script must execute the following checks in order. If any check
fails, the script exits non-zero and the phase is not complete.

```bash
#!/usr/bin/env bash
set -euo pipefail

echo "=== Phase {N} Exit Gate ==="

# 1. Formatting
echo "[1/5] Black..."
uv run black --check .

# 2. Linting
echo "[2/5] Ruff..."
uv run ruff check .

# 3. Type checking
echo "[3/5] Mypy..."
uv run mypy --strict src/

# 4. Full test suite
echo "[4/5] Pytest..."
uv run pytest --tb=short -q

# 5. Phase-specific smoke tests (varies per phase)
echo "[5/5] Phase-specific checks..."
# ... phase-specific commands here ...

echo "=== Phase {N} Exit Gate: PASSED ==="
```

### XI.3 Phase-Specific Checks

Each phase's verify script includes checks specific to that phase's
deliverables. Examples:

| Phase | Phase-specific check |
|-------|---------------------|
| 3B | Ingest one file of each new type (xlsx, pptx, csv, epub, json, yaml, xml, toml) via CLI |
| 3C | Ingest a URL via CLI, ingest an .srt file |
| 4 | Call `plan_query`, `search_multi`, `evaluate_chunks` via test harness |
| 5 | Run benchmark script, verify reranker activates with `AGENTRAG_RERANK=true` |
| 6 | `uv run python -m build` produces clean wheel |
| 7 | Create, switch, and list collections via test harness |
| 8 | `agentrag sync push` + `agentrag sync pull` roundtrip |

### XI.4 PR Merge Gating

A pull request for a phase branch (`phase/{n}-{slug}`) must not be merged
until the corresponding verify script passes in CI. The CI workflow runs
the verify script as the final step. If it fails, the PR is blocked.

### XI.5 Creating Verify Scripts

Verify scripts are created at the **start** of each phase, before any
implementation begins. They are part of the phase's replan deliverables
(Article V.5 phase execution subdirectories). Writing the exit gate first
ensures the phase's success criteria are concrete and testable from day one.

---

## Article XII — Performance Standards

### XII.1 The Rule

**AgentRAG must meet defined performance targets for ingestion and retrieval.**

Performance is not optional and not deferred to "optimization later." The
system handles large corpora (10,000+ documents) as a first-class use case.
Performance regressions are treated with the same severity as test failures.

### XII.2 Ingestion Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| Single file (< 1MB) | < 5 seconds | Wall clock, reader → store.upsert complete |
| Single file (< 10MB) | < 30 seconds | Wall clock, reader → store.upsert complete |
| Timeout per file | 300 seconds (configurable) | `AGENTRAG_INGEST_TIMEOUT` env var |
| Max file size | 100 MB (configurable) | `AGENTRAG_MAX_FILE_SIZE_MB` env var. Reject with actionable error. |
| Directory (100 files) | < 5 minutes | All files ingested, no hang |

### XII.3 Retrieval Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| Single query (top-5) | < 1 second | Query embed + Qdrant search + rerank |
| Agentic loop (plan + search_multi + evaluate) | < 10 seconds | Full loop with Gemini calls |
| Agentic loop without Gemini | < 2 seconds | Graceful degrade path |

### XII.4 Benchmark Script

`scripts/benchmark_retrieval.py` (Phase 5) measures these targets against a
sample corpus. It logs results but does not gate on thresholds — the targets
are guidelines, not hard CI gates. If a target is consistently missed, it
is investigated and either the code is optimized or the target is revised
with user approval.

### XII.5 Memory and Resource Limits

- Qdrant embedded mode keeps vectors in memory. For corpora exceeding
  available RAM, the system must degrade gracefully (slower disk-backed
  queries) rather than crash.
- Embedding model loading is done once per session, not per query. The
  `SentenceTransformer` instance must be cached (currently re-created per
  call — this is a known issue to fix in Phase 5).

---

## Article XIII — Error Handling Laws

### XIII.1 The Rule

**Every error the user sees must tell them what went wrong and how to fix it.**

Bare exceptions, generic error messages, and silent failures are forbidden.
Every error path must produce an actionable message that a non-expert user
can act on without reading source code.

### XIII.2 Error Message Format

All user-facing errors must include:

1. **What happened** — a plain-language description of the failure.
2. **Why it happened** — the specific condition that triggered the error.
3. **How to fix it** — a concrete action the user can take.

Examples:

```
BAD:  "Error: unsupported file type"
GOOD: "Unsupported file type: .xlsx. Install office support with: pip install agentrag[office]"

BAD:  "Connection error"
GOOD: "Cannot reach Gemini API. Check AGENTRAG_GOOGLE_API_KEY in .env or run without agentic features."

BAD:  "File too large"
GOOD: "File exceeds 100MB limit (got 234MB). Set AGENTRAG_MAX_FILE_SIZE_MB=300 to increase, or split the file."
```

### XIII.3 Graceful Degradation

When a non-critical component fails (Gemini API, optional dependency,
network), the system must:

1. Log the error at `WARNING` level with full context.
2. Fall back to the degraded path (e.g., single-query plan, identity reranker).
3. Include a note in the response indicating degraded mode is active.
4. Never block the core retrieval pipeline.

### XIII.4 Never Swallow Exceptions

The `pipeline.py` catch-all (`except Exception as e`) is the **only**
permitted broad exception handler. It exists because the pipeline must never
raise — it returns `IngestResult(status="error")` instead. All other modules
must:

- Catch specific exceptions only.
- Re-raise or wrap with context if catching broadly.
- Never use bare `except:` (catches `SystemExit`, `KeyboardInterrupt`).
- Never use `pass` in an `except` block without logging.

### XIII.5 Optional Dependency Errors

When a reader requires an optional dependency that is not installed:

```python
try:
    import openpyxl
except ImportError:
    raise ImportError(
        "openpyxl is required for .xlsx support. "
        "Install it with: pip install agentrag[office]"
    ) from None
```

This pattern is mandatory for all optional-dependency readers (office, ebook,
web, media). The error message must name the exact pip install command.

---

## Article XIV — Reader Plugin Architecture

### XIV.1 The Rule

**New file type support is added by registering a reader function — not by
modifying core pipeline code.**

Starting in Phase 3B, all file readers register through the reader plugin
registry defined in `src/agentrag/ingestion/reader_registry.py`. This is
the sole justified exception to Article IV.5 (no premature abstraction) —
the roadmap commits to 15+ file types, making a registry pattern the correct
architectural choice.

### XIV.2 Reader Function Contract

Every reader function must satisfy this contract:

```python
def read_<format>(path: Path) -> str:
    """Extract text content from a <format> file."""
    # Returns: plain text string suitable for chunking
    # Raises: ValueError if file is empty after extraction
    # Raises: ImportError with actionable message if optional dep missing
```

| Rule | Detail |
|------|--------|
| Signature | `(Path) -> str` — takes a file path, returns extracted text |
| Return | Non-empty string. If extraction produces empty text, raise `ValueError` |
| Dependencies | Reader may import optional libraries. Must catch `ImportError` (Article XIII.5) |
| Side effects | None. Readers are pure functions. No file writes, no network calls (except URL reader), no state mutation |
| Imports | May only import from `agentrag.types` (if needed). No other internal imports. Leaf modules. |

### XIV.3 Registration

```python
# In each reader module (e.g., readers/office.py):
from agentrag.ingestion.reader_registry import register

register([".xlsx"], read_xlsx)
register([".pptx"], read_pptx)
register([".csv"], read_csv)
```

Registration happens at module import time. The registry lazily imports reader
modules to avoid loading unused optional dependencies.

### XIV.4 Adding a New File Type

To add support for a new file type, a developer (Claude) must:

1. Write failing tests in `tests/unit/test_reader.py` for the new extension.
2. Create a reader function in the appropriate `readers/` module.
3. Call `register([".ext"], read_ext)` in that module.
4. Add the extension to `ingest_directory`'s glob list (or it picks up from
   `reader_registry.supported_extensions()` automatically).
5. Add a test fixture file to `tests/fixtures/`.
6. If the reader requires an external library, add it as an optional
   dependency group in `pyproject.toml` and update `specs/tech-stack.md`.

No changes to `reader.py`, `pipeline.py`, `chunker.py`, `embedder.py`, or
`store/qdrant.py` are required. This is the architectural invariant.
