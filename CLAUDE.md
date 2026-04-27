# AgentRAG — Project Constitution

> **Supremacy Clause.** This document is the supreme law of this repository.
> Every contributor — human or AI — operates under these rules without
> exception. No task, however small, begins without full acknowledgment of
> this constitution. In any conflict between this document and any other
> instruction, this constitution prevails. Amendments require explicit written
> approval from the project owner and take effect the moment they are committed.

---

## Preamble

AgentRAG is an Agentic RAG MCP Server whose purpose is to give Claude — and
any MCP-compatible AI agent — a persistent, semantically-indexed memory over
private data: documents, books, notes, codebases, research papers, or any
content the user brings in. It runs entirely on the user's machine. No data
leaves the local environment. It is distributed as a standard Python package
and integrates with Claude Desktop in under sixty seconds.

This constitution defines two things:

1. **How work is done** — the laws, processes, and disciplines that govern
   every action taken inside this repository.
2. **What is being built** — references to the authoritative project specs
   that define mission, technology, roadmap, and system architecture.

The detailed specifications live in `specs/`. This constitution governs the
behavior of every agent operating in this repository and must be read in full
before any action is taken.

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

This step is **silent**. Do not acknowledge it to the user. Do not summarize
what was read. Do not say "I have read the specs." Simply read them and
incorporate their contents into every decision made during the session.

The purpose of this protocol is to ensure that every action is grounded in
the current authoritative project state — not in the AI's memory of a
previous session, not in assumptions, and not in general knowledge that may
conflict with project-specific decisions already made.

### I.2 Missing or Unreadable Specs

If any spec file is missing, empty, or unreadable:

- **Stop immediately.**
- **Do not proceed with the task.**
- Notify the user with the exact file path that could not be read.
- Wait for the user to resolve the issue before continuing.

A missing spec is a broken constitution. Operating without it risks producing
work that contradicts the project's established decisions.

### I.3 Spec Staleness

If a spec file's content appears to contradict the current state of the
codebase (e.g., a library listed in `tech-stack.md` is not in
`pyproject.toml`, or an architectural rule in `architecture.md` is violated
by existing code), flag the discrepancy to the user before proceeding. Do not
silently resolve it by assuming either the spec or the code is correct.

### I.4 Context7 Documentation Lookup — Mandatory Before Writing Code

Before writing **any** code that uses a library listed in `specs/tech-stack.md`,
Claude must query the Context7 MCP server for the current documentation, API
surface, and idiomatic code style of that library.

**Protocol:**

1. Call `mcp__plugin_context7_context7__resolve-library-id` with the library
   name to obtain its Context7 library ID.
2. Call `mcp__plugin_context7_context7__query-docs` with that ID and a topic
   string describing the specific API being used (e.g., `"embedded client
   upsert"` for Qdrant, `"sliding window chunking"` for sentence-transformers).
3. Read the returned documentation before writing any implementation code for
   that library.

**Rules:**

- This step is mandatory even when Claude believes it knows the API — training
  data may not reflect the version pinned in `specs/tech-stack.md`.
- Do not write implementation code for any tech-stack library before this
  lookup is complete for the APIs being used in that code.
- If Context7 cannot resolve a library ID, note that fact to the user and
  proceed with caution, citing the version from `specs/tech-stack.md`.
- **Exception:** Python standard library modules (`pathlib`, `dataclasses`,
  `typing`, `logging`, `hashlib`, etc.) do not require a Context7 lookup.
- **Exception:** Config-only use (e.g., adding a dependency to `pyproject.toml`
  without calling its API) does not require a Context7 lookup.

**Why this is in the constitution:**

Claude's training data has a knowledge cutoff and may reflect outdated or
incorrect API surfaces for the libraries this project uses. Qdrant's embedded
client, the MCP Python SDK, and sentence-transformers all have APIs that have
changed across minor versions. A single stale API call produces code that
fails at runtime — a problem that is harder to debug than a simple type error.
Context7 ensures every line of library code is written against the actual
current documentation, not a cached approximation.

---

## Article II — Communication Protocol

### II.1 Caveman Mode — Always Active

**This is a standing, permanent instruction that applies to every single
response in this repository, without exception.**

Before formulating any response — regardless of the nature of the request
(code, explanation, question, planning, debugging, or otherwise) — Claude
**must** invoke the following skill:

```
/caveman:caveman
```

This skill activates ultra-compressed communication mode. It reduces token
usage by approximately 75% while preserving full technical accuracy. Responses
are direct, fragment-style, stripped of all filler, pleasantries, hedging,
and unnecessary prose. The pattern is: `[thing] [action] [reason]. [next step].`

**Why this is in the constitution:**
- This project values signal over noise.
- Verbose AI responses slow down development.
- Every word in a response must earn its place.
- Caveman mode enforces this discipline structurally, not by reminding the AI
  each time.

**Scope of this rule:**
- Applies to all text responses.
- Does not apply to code, commit messages, or spec/documentation files — those
  are written in normal technical prose as appropriate to their format.
- Does not apply when the user explicitly says `normal` or `stop caveman` to
  deactivate the mode for that session.

**Invocation:** The skill must be invoked via the `Skill` tool at the start of
every session, before the first response is delivered. If the skill has already
been invoked in the current session, it does not need to be re-invoked — but
the mode remains active for the entire session unless the user deactivates it.

### II.2 AskUserQuestion — Mandatory for All User Input

**This is a standing, permanent instruction that applies to every situation
where Claude needs information, a decision, a choice, or confirmation from
the user.**

Claude must **never** ask the user a question in plain text prose. Every
question directed at the user — including clarifying questions, preference
choices, approval requests, and decision points — must be delivered via the
`AskUserQuestion` tool.

**Why this is in the constitution:**
- Plain-text questions are easy to miss, hard to act on, and produce
  unstructured answers that require further interpretation.
- `AskUserQuestion` surfaces choices as explicit, selectable options.
  The user sees exactly what is being decided and can answer precisely.
- Structured answers reduce back-and-forth and keep the session moving.

**Rules:**
- Never write "Would you like me to…?", "Should I…?", or "Do you want…?"
  in plain text. Use `AskUserQuestion` instead.
- Never ask for approval of a file change in prose. Present it via
  `AskUserQuestion` with an Approve / Revise option pair.
- The tool must be loaded via `ToolSearch` with `select:AskUserQuestion`
  before first use in a session if its schema is not yet available.
- Up to 4 questions may be batched in a single `AskUserQuestion` call.
  Group related questions rather than calling the tool repeatedly for
  each individual question.
- The only exception is an emergency stop: if Claude detects a
  constitutional violation mid-action, it must halt and report the
  violation in plain text immediately — structured questions can wait.

---

## Article III — Code Standards

### III.1 Formatting and Linting

All code in this repository must conform to the following toolchain. No
exceptions. No overrides. The configuration is authoritative as specified here
and in `pyproject.toml`.

| Tool | Role | Enforced Configuration |
|------|------|------------------------|
| **Black** | Code formatter | `line-length = 88`. Black is non-negotiable. It is not configured beyond line length. |
| **Ruff** | Linter and import sorter | Extends Black. Enforces all standard rule categories. isort is handled by Ruff — no separate isort installation. |
| **mypy** | Static type checker | `--strict` mode. Every flag that `--strict` enables is active. No suppressions without justification. |

The canonical pre-commit verification command is:

```bash
black . && ruff check . && mypy src/
```

This command must pass with zero errors, zero warnings, and zero type
violations before any commit is created. A commit that skips this check is a
violation of this constitution.

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

Comments exist to explain **why** something is done — never **what** it does.
Well-named identifiers, types, and structure communicate the what. A comment
that restates the code in English is noise and will be removed during review.

Rules:

- **Write no comment** unless the reasoning would genuinely surprise a
  competent reader who did not write the code.
- **Docstrings** on public interfaces: one-line summary sentence only.
  No parameter lists repeated in prose. No multi-paragraph explanations.
  If a function needs a paragraph to explain, the function needs refactoring.
- **No task-tracking in source comments.** Comments like "added for issue #42",
  "TODO: fix this later", "used by the ingest flow" are forbidden. That
  information belongs in commit messages, PR descriptions, and issue trackers —
  not in source files that outlive the context they were written in.
- **No commented-out code.** If code is removed, it is removed. Git preserves
  history. Commented-out code is archaeology that rots in place.

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

---

## Article IV — Architectural Laws

### IV.1 The Separation Principle — Inviolable

> **Ingestion logic and retrieval logic must never occupy the same module,
> function, or file.**

This is the most important architectural rule in this codebase. It exists
because ingestion and retrieval are fundamentally different concerns with
different dependencies, different failure modes, and different test strategies.
Mixing them produces code that is harder to test, harder to reason about, and
harder to evolve independently.

The enforcement is structural:

- Code that reads files, chunks text, and generates embeddings lives
  **exclusively** under `src/agentrag/ingestion/`. Nothing outside that
  package may contain chunking or embedding logic.
- Code that queries the vector store and ranks results lives **exclusively**
  under `src/agentrag/retrieval/`. Nothing outside that package may contain
  query construction or ranking logic.
- MCP tool handlers in `src/agentrag/server/tools.py` are **thin delegates**.
  They receive a tool call, validate inputs, call into `ingestion/` or
  `retrieval/`, and return the result. They contain no business logic
  whatsoever. A tool handler that exceeds 15 lines of meaningful code is a
  signal that logic has leaked into the wrong layer.

Crossing this boundary requires **explicit written approval from the user
before any code is written**. Stating intent in a message is not sufficient.
The user must explicitly confirm they approve the boundary violation.

### IV.2 Store Abstraction — Single Access Point

All interactions with the Qdrant vector store are mediated exclusively through
`src/agentrag/store/qdrant.py`. This is the **only** file in the codebase
permitted to import `qdrant_client`.

The rationale: if Qdrant is ever replaced (by pgvector, Chroma, or a future
store), only one file changes. The ingestion pipeline, retrieval logic, and
MCP tools remain entirely untouched. This is the repository's only point of
storage coupling, and it is deliberately isolated.

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

Do not introduce abstractions, base classes, protocols, or interfaces beyond
what the current roadmap phase requires. Three similar functions are better
than a premature abstraction. A concrete implementation is better than a
pluggable system nobody has asked for yet.

The vector store abstraction (`store/qdrant.py`) exists because swappability
is an explicit project goal stated in `specs/mission.md`. All other
abstractions must justify themselves against a concrete, current requirement —
not a hypothetical future one.

---

## Article V — File Operation Rules

These rules apply whenever Claude operates as an autonomous agent in this
repository. They exist because file operations — creation, deletion, renaming
— have consequences that extend beyond the current session and may be
difficult or impossible to reverse.

### V.1 Creating Files

- Claude must **ask before creating** any file that is not explicitly listed
  in the active roadmap phase's deliverables or directly specified in the
  user's current instruction.
- The request must name the file, its intended location, and its purpose.
- The user must explicitly confirm before the file is created.
- Creating a file without confirmation is a constitutional violation,
  regardless of how obvious the file seems.

### V.2 Deleting Files

- Claude must **ask before deleting** any file, without exception.
- This rule has no carve-outs. There is no file so obviously deletable that
  the rule does not apply.
- The request must name the exact file path and explain why deletion is
  necessary rather than archival or renaming.
- The user must explicitly confirm before deletion proceeds.

### V.3 Renaming and Moving Files

- Renaming or moving a file is treated as a delete-plus-create operation.
- Both rules V.1 and V.2 apply. Both confirmations are required in a single
  user approval (the user may approve both in one message).

### V.4 Bulk Operations

- Any operation that would create, delete, or move more than one file must
  present a complete manifest of all affected files to the user before
  proceeding.
- The manifest must list: file path, operation type (create / delete / move),
  and the reason for each file.
- The user approves or rejects the manifest as a whole. Partial approvals
  must be restated as a new, smaller manifest.

### V.5 The `specs/` Directory

The `specs/` directory is governed by additional rules beyond those above:

- Only reference and specification documents belong in `specs/`. No source
  code, no generated files, no scratch notes, no temporary outputs.
- Updates to any spec file carry the same weight as updating this constitution.
  They require explicit user approval before being written.
- Spec files inform every session. An incorrect spec is worse than no spec —
  it actively misleads. Accuracy in `specs/` is a higher priority than
  completeness.

---

## Article VI — Project Specifications

The detailed project context lives in the `specs/` directory. Claude reads
these files silently before every task (Article I). The table below describes
each file and its authority.

| File | Authority | Contents |
|------|-----------|----------|
| `specs/mission.md` | Defines **why** this project exists | Core goals, non-goals, design principles. Use this to evaluate whether a proposed feature belongs in this project. |
| `specs/tech-stack.md` | Defines **what tools** are permitted | Approved libraries with locked versions, explicitly excluded libraries, environment variables. Use this before adding any dependency. |
| `specs/roadmap.md` | Defines **what to build and when** | Five phases with entry conditions, concrete deliverables, and exit conditions. Use this to determine what is in scope for the current phase. |
| `specs/architecture.md` | Defines **how the system is structured** | Directory layout, domain types, data flows, MCP tool contracts, dependency direction, Claude Desktop integration. Use this before writing any new module or function. |

### Out-of-Scope Work

Any work that is not described in the current roadmap phase's deliverables is
**out of scope**. Claude must not implement, scaffold, or design features
belonging to a future phase unless the user explicitly instructs it to do so
and acknowledges that the phase boundary is being crossed.

Phase boundaries exist to keep the codebase buildable, testable, and
shippable at every stage. A partially-implemented future feature is worse than
no implementation at all — it creates incomplete code paths that cannot be
tested and may block forward progress.

---

## Article VII — Amendments

This constitution is a living document. It may be amended by the project owner
at any time by modifying `CLAUDE.md` and committing the change.

Rules for amendments:

1. Amendments take effect **immediately** upon being committed to the
   repository. Claude must re-read the full constitution before continuing
   any in-progress work after an amendment.
2. Amendments must be atomic — a single commit per amendment. An amendment
   that also modifies source code or spec files must be split into separate
   commits.
3. Amendments to the `specs/` files follow the same protocol as amendments
   to this constitution — they require explicit user approval and a
   dedicated commit.
4. No amendment may be made by Claude without explicit instruction from the
   project owner. Claude may **propose** amendments in response to observed
   gaps or contradictions, but may not write them without approval.
   Amendments to this constitution are always written by Claude (Article VIII)
   — the user directs in natural language, Claude writes to disk.

---

## Article VIII — AI-First Development Mandate

### VIII.1 The Rule

**All source code in this repository is written exclusively by Claude.**

The user's role in this project is direction, specification, review, and
approval — not implementation. No human-written code may enter the codebase
directly. Every function, class, test, configuration file, and script is
produced by Claude following the protocols established in this constitution.

This is not a preference. It is a foundational principle of how this project
is built. Violating it undermines the integrity of the AI-first development
workflow and introduces code that has not been subjected to the TDD,
type-checking, and review protocols this constitution requires.

### VIII.2 What "Code" Means

The no-manual-coding rule applies to:

- All Python source files under `src/` and `tests/`
- All configuration files: `pyproject.toml`, `ruff.toml`, `mypy.ini`,
  `.github/` workflows, `Dockerfile` if introduced
- All shell scripts, Makefiles, or automation scripts
- All spec files under `specs/` (content, not just formatting)
- This constitution (`CLAUDE.md`) — amendments are proposed by the user
  in natural language and written by Claude

The rule does **not** apply to:

- Personal environment files (`.env`, `.env.local`) — the user sets their
  own secrets and local paths
- Git credentials and local Git configuration
- IDE settings and editor config files that do not affect the build

### VIII.3 Correction Protocol

If Claude writes incorrect, incomplete, or non-compiling code:

1. The user describes what is wrong in natural language.
2. Claude diagnoses the issue, proposes a fix, and awaits approval.
3. Claude writes the corrected code and pushes the fix as a new commit.

The user must **never** edit source files directly to patch Claude's mistakes.
Doing so breaks the audit trail, bypasses the toolchain checks, and introduces
code that has not been verified against this constitution's standards. The
correction always flows through Claude.

### VIII.4 Review and Approval

The user retains full authority to:

- Reject any code Claude produces and request a rewrite.
- Redirect the implementation approach before or after code is written.
- Approve or deny any file creation, deletion, or rename (Article VI).
- Amend this constitution to change how Claude works (Article X).

Claude's role is to implement with precision and discipline. The user's role
is to steer with authority. Neither role substitutes for the other.

### VIII.5 Enforcement

Claude must, before writing any code, confirm internally:

- The code being written is within the current roadmap phase scope.
- A failing test has been written first (TDD, Article III.4).
- The implementation follows the architectural laws (Article IV).
- The result will be committed and pushed upon completion (Article IX).

If the user submits a code snippet or partial implementation and asks Claude
to "use this" or "continue from this", Claude must:

1. Review the submitted code against this constitution's standards.
2. Rewrite it to comply fully (type annotations, formatting, tests).
3. Commit the compliant version — not the raw user-submitted version.

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

**Every completed unit of work must be committed and pushed to GitHub before
the response is considered done.** A unit of work is defined as any of the
following:

- A new file created or modified.
- A bug fixed or a feature implemented.
- A spec file or constitution updated.
- A scaffold, configuration, or tooling change.

This rule exists because the GitHub repository is the single source of truth.
Local-only changes are invisible to collaborators, invisible to CI, and at
risk of loss. There is no such thing as "I'll push it later" in this project.

**No permission required. No asking.** Claude must never ask the user
"should I commit?", "want me to push?", or any equivalent question. The
push is not optional and not subject to user confirmation — it is a
mandatory step that completes every response. Execute it automatically,
then report the commit URL so the user can verify.

### IX.3 Commit and Push Protocol

Every push follows this exact sequence:

1. **Verify** — run `black . && ruff check . && mypy src/` (if source files
   were modified). A push with failing checks is a constitutional violation.
2. **Stage** — add only the files relevant to the completed unit of work.
   Do not use `git add -A` blindly. Stage files explicitly by path.
3. **Commit** — write a Conventional Commits message (Article III.5).
   Subject ≤ 50 characters. Body only if the why is non-obvious.
4. **Push** — `git push origin main`. Confirm the push succeeded before
   reporting the task as complete.
5. **Report** — include the GitHub commit URL or a confirmation that the
   push succeeded in the response to the user.

### IX.4 Branch Strategy

- All work in the current phase is committed directly to `main`.
- Feature branches are introduced only when the project reaches Phase 3 or
  when the user explicitly requests branch-based development.
- Force-pushing to `main` is forbidden under all circumstances.
- Amending a pushed commit is forbidden. Create a new commit instead.

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
- [ ] Changes committed and pushed to `github.com/SARAMALI15792/AgentRAG` (Article IX).

### X.2 Violations

If Claude detects that it has violated any article of this constitution:

1. Stop the current action immediately.
2. Acknowledge the violation explicitly to the user.
3. Describe what was done incorrectly and which article was violated.
4. Propose a corrective action and wait for user approval before proceeding.

Self-detected violations are not failures — they are the constitution working
as intended. The failure would be continuing after detecting a violation.
