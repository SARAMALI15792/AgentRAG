# Phase 5 — Distribution: Requirements

## Scope

Make AgentRAG installable as a standard Python package and verifiable as a
zero-install tool via `uvx`. Lay the foundation for PyPI publication without
performing the live publish (deferred to after Phase 7).

---

## Decisions

### PyPI Publish — Deferred to Post-Phase 7

**Decision:** The `git tag v0.1.0` push that triggers the CI publish job is
deferred until Phase 7 (Cloud Sync) is complete. v0.1.0 will represent the
full initial feature set.

**Rationale:** Publishing an incomplete package risks confusion for early
adopters. Phase 7 adds cloud sync — a planned v0.1.0 capability per mission.md.
Shipping a package without it and later releasing v0.1.1 creates fragmentation.

**What Phase 5 does instead:** Builds the wheel, validates the CI workflow
exists and is syntactically correct, and confirms `uvx` works from a local
wheel. All the infrastructure is ready; only the tag push is deferred.

---

### Package Metadata

| Field | Value |
|-------|-------|
| `name` | `agentrag` |
| `version` | `0.1.0` |
| `license` | MIT |
| `Homepage` | `https://github.com/SARAMALI15792/AgentRAG` |
| `Repository` | `https://github.com/SARAMALI15792/AgentRAG` |
| `Issues` | `https://github.com/SARAMALI15792/AgentRAG/issues` |
| `requires-python` | `>=3.12` |

**Classifiers (required):**
```
"License :: OSI Approved :: MIT License"
"Programming Language :: Python :: 3"
"Programming Language :: Python :: 3.12"
"Programming Language :: Python :: 3.13"
"Operating System :: OS Independent"
"Topic :: Scientific/Engineering :: Artificial Intelligence"
"Topic :: Software Development :: Libraries :: Python Modules"
```

---

### Entry Point

```toml
[project.scripts]
agentrag = "agentrag.cli:app"
```

Verified Claude Desktop config (stdio transport, `uvx` form):

```json
{
  "mcpServers": {
    "agentrag": {
      "command": "uvx",
      "args": ["agentrag", "serve", "--data-dir", "~/.agentrag"]
    }
  }
}
```

---

### CI — Python Version Matrix

The test job matrix expands to `["3.12", "3.13"]`. Both versions must pass
all existing tests before Phase 5 can exit.

**Note on 3.13 compatibility:** `sentence-transformers` and `qdrant-client`
must both support Python 3.13 at the time of implementation. If a transitive
dependency blocks 3.13, document the blocker and pin a compatible version.

---

### CI — Publish Workflow

A `publish` job is added to CI, triggered on `v*` tag push. The job uses a
`PYPI_TOKEN` GitHub Actions secret (not yet configured — set at publish time).
The job must be syntactically valid and pass `actionlint` or equivalent.
A comment in the workflow marks it as "pending Phase 7 completion."

---

### README.md Scope

The README is the primary user-facing document. It must:

- Be correct: every command shown must work on a clean install.
- Be complete: covers install, config, Claude Desktop setup, all tools, all
  file types, all env vars.
- Be concise: no marketing copy. Users are technical (see mission.md audience).

Sections required:
1. One-sentence description
2. 60-second quickstart
3. Claude Desktop integration (pip and uvx forms)
4. CLI reference (flags + env vars table)
5. MCP tools reference (all 10 tools, one-line each)
6. Supported file types (table with optional deps)
7. Optional: Development setup (for contributors)

---

### CHANGELOG.md Scope

Format: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) — `## [0.1.0] - Unreleased`.

Sections:
- **Added** — list all shipped features grouped by phase (Phase 1 through Phase 5)

No "Changed", "Fixed", or "Removed" sections needed for v0.1.0 (first release).

---

## Out of Scope

- Actual PyPI publish (deferred post-Phase 7).
- Docker image or containerized distribution.
- Windows installer / MSI packaging.
- Conda package.
- Any new MCP tools or ingestion features.
- Performance improvements (Phase 5 is packaging only).
