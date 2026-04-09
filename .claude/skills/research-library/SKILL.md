---
name: research-library
description: |
  Research any technology, library, tool, or framework before implementing a feature — without relying on LLM training memory which may be outdated. Covers Python packages, npm modules, Docker Compose setups, CLIs, SaaS SDKs (e.g. Langfuse, OpenTelemetry, Qdrant), and anything else with docs and source code. Trigger this skill whenever a user says "research X", "how do I use X", "implement a feature using X", "find latest version of X", "verify if X works with Y", "set up X with Docker", or "show me how to integrate X" — even if they don't say "research". Always prefer primary sources: llms.txt, official docs, PyPI/npm metadata, GitHub source code. Never rely on LLM memory alone.
---

# research-library

This skill performs thorough, source-grounded research on any technology before writing code. The core principle: **never trust LLM training memory** — it may describe APIs, Docker images, or default configs that changed months ago. Instead, every claim must be backed by a fetched primary source.

---

## Phase 0 — Clarify scope

Before fetching anything, ask (or infer from context) the answers to these:

1. **What technology/library/tool** are we researching? (e.g., `langfuse`, `langchain`, `qdrant-client`, Docker Compose for X)
2. **What functionality** should we implement? (e.g., "trace LLM calls", "run self-hosted via Docker", "upload documents for RAG")
3. **Any version pin?** If the user hasn't specified, always research the **latest stable version**.
4. **Which deployment mode?** (local Docker, cloud SaaS, hosted SDK, CLI install, etc.)

---

## Phase 1 — Discover latest version

Always determine the latest version before reading any docs, because old docs may describe outdated APIs.

- **Python packages:** Query `https://pypi.org/pypi/<package-name>/json` → read `.info.version` and `.info.project_urls` for docs/source.
- **npm packages:** Query `https://registry.npmjs.org/<package-name>/latest` → read `version` and `homepage`.
- **Docker images:** Check the official Docker Hub page (`https://hub.docker.com/r/<image>/tags`) or the project's GitHub releases for latest tag. **Never assume `latest` tag is current — always confirm the actual version tag.**
- **GitHub repos (non-packaged tools):** Check `/releases/latest` to get the most recent tag.

Record: package name, latest version, release date, homepage, source repo URL.

---

## Phase 2 — Fetch documentation (priority order)

Fetch from primary sources in this order — stop when you have enough context for the implementation:

1. **`llms.txt` / `llms-full.txt`** — Check the repo root and the docs root for these files. If present, read them first; they contain curated, LLM-friendly summaries intended for exactly this use case.
2. **README.md** — From the repo root. Focus on the quickstart, install section, and any environment/config requirements.
3. **Official docs site** — From the project URL (e.g., `docs.langfuse.com`, `qdrant.tech/documentation`). Fetch the pages relevant to the feature being implemented.
4. **Changelog / CHANGELOG.md / GitHub releases** — Check for breaking changes in recent versions. This is the most reliable way to catch "it worked in v1 but changed in v2" surprises.
5. **Docker Compose / self-hosting guide** — If the user needs a local or self-hosted setup, locate the official `docker-compose.yml` (not a community copy) and configuration reference. Many tools publish example compose files in their docs or repo.

If the **Context7 MCP server** is available, use it to fetch authoritative documentation via its `resolve-library-id` and `get-library-docs` tools before falling back to raw HTTP fetches.

---

## Phase 3 — Fetch and inspect source code

Documentation sometimes lags behind the code. Always cross-check:

### 3a — Sync the local repo clone in `repos/`

Before reading any source, ensure the local copy is at the latest state:

1. **Check `repos/` for an existing clone** — scan for a directory whose name matches the repo (e.g., `repos/langfuse`, `repos/qdrant`, `repos/a2a-python`).
2. **If the repo already exists:** run `git -C repos/<name> fetch --tags --prune` followed by `git -C repos/<name> pull --rebase` (or `git -C repos/<name> reset --hard origin/HEAD` if the working tree is dirty) to bring it fully up to date.
3. **If the repo does not exist:** clone it with `--depth 1` (or `--branch <version-tag>` using the tag found in Phase 1) into `repos/<name>`.
4. **Confirm the HEAD commit and tag:** run `git -C repos/<name> describe --tags --abbrev=0` and verify it matches the latest version discovered in Phase 1. If there is a mismatch, checkout the correct tag: `git -C repos/<name> checkout tags/<version-tag> --detach`.

> **Always resolve the repo against the exact version tag from Phase 1** — never rely on whatever happened to be checked out last.

### 3b — Cross-compare documentation vs. code at the same version

Before writing any research notes, perform an explicit doc-vs-code alignment check:

1. Note the **docs version** (from the docs page header, changelog entry, or README version badge).
2. Note the **code version** (git tag/commit confirmed in 3a).
3. If these differ, **re-fetch the docs** for the code version (e.g., use the versioned docs URL or the relevant git-tagged README/changelog). Do not mix docs from one version with code from another.

### 3c — Source inspection

4. For each function/class/method used in the feature, locate the actual implementation in source.
5. Compare the documented interface (parameter names, return types, raised exceptions) against the implementation.
6. Look for anything in source that docs don't mention: newly added parameters, removed kwargs, config env-var names.
7. Check the `examples/` or `cookbook/` directory in the repo — these are often more up-to-date than narrative docs.

---

## Phase 4 — Surface mismatches

Report any divergence between docs and code. Examples of what to look for:

| Mismatch type | What to check |
|---|---|
| Method removed or renamed | Grep source for documented method name |
| Parameter added/removed | Compare function signature in source vs docs |
| Different import path | Confirm actual module path in `__init__.py` |
| Config env-var renamed | Check actual env-var names in source/Docker config |
| Docker image tag or port change | Confirm in official `docker-compose.yml` |
| Default values changed | Check source default values vs docs |

Flag every mismatch clearly in the output: what the docs say, what the code actually does, and the source file + line number.

---

## Phase 5 — Produce the implementation

Only after Phases 1–4, write the implementation:

- Use the API as confirmed in source code (not docs alone).
- For Docker-based tools: produce a `docker-compose.yml` using the **exact version tag** found in Phase 1, not `latest`.
- For Python/npm packages: pin to the exact version discovered.
- For environment variables and configs: use the names found in source, not docs (they may differ).
- Provide a minimal runnable example that can be copy-pasted and tested.

---

## Phase 6 — Validate locally (if feasible)

If the environment supports it:

- Run the minimal example and capture output or errors.
- For Docker setups: `docker compose up -d`, wait for health checks, then run the example.
- Report what worked, what failed, and proposed fixes for any failures.
- If local validation isn't possible (no Docker, no network, etc.), state that clearly and explain how the user can validate manually.

---

## Output format

Produce a `research_report.md` at the path the user requests (or `./research_report.md` if unspecified):

```
# Research: <Technology> — <Feature>

## Summary
One paragraph summarizing what was researched, what was found, and key caveats.

## Sources
- PyPI / npm metadata: <version, release date, URL>
- Docs fetched: <list of URLs / local paths>
- Source repo: <URL @ tag/commit>
- llms.txt: <found / not found>

## Latest version
<version, release date, any breaking changes since common previous version>

## API surface (for this feature)
<List of key classes/functions/config used, with confirmed signatures>

## Docs vs code mismatches
<Table or bullets: documented behavior, actual behavior, source file + line>
(If none found: "No mismatches detected.")

## Implementation
<Complete, runnable code / docker-compose.yml / config>

## How to validate
<Step-by-step: install/run commands to verify the implementation works>

## Recommended next steps
<Optional: links to open issues, suggested PR, migration notes>
```

---

## Tool usage guidance

| Need | Tool to use |
|---|---|
| Fetch docs / llms.txt | Context7 MCP `get-library-docs` if available, else HTTP GET |
| Latest version | PyPI JSON API / npm registry / GitHub releases |
| Check existing local clone | `ls repos/` or `file_search repos/**` |
| Update existing clone | `git -C repos/<name> fetch --tags --prune && git -C repos/<name> pull --rebase` |
| Clone fresh | `git clone --depth 1 --branch <tag> <url> repos/<name>` |
| Confirm correct tag | `git -C repos/<name> describe --tags --abbrev=0` |
| Inspect source | grep / read files from `repos/<name>/` |
| Docker Compose | HTTP GET official compose file from repo or docs |
| Run example | Terminal / Docker |

---

## Important constraints

- Never write code based only on LLM memory. If you can't fetch a source to confirm an API, say so explicitly and mark the code as "unverified — confirm before using".
- When multiple sources disagree (docs vs code vs example), prefer **source code**, then **examples directory**, then **docs**.
- Always record the exact URLs and version tags used so the research is reproducible.
- If a tool like Langfuse has both a **cloud SaaS** and a **self-hosted (Docker) mode**, research both and clearly document the differences.
