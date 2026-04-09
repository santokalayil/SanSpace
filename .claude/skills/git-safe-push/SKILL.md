---
name: git-safe-push
description: >
  Safely push changes to a remote GitHub repository with a structured pre-push checklist.
  Use this skill whenever the user says "push to GitHub", "push my changes", "commit and push",
  "make a pull request", "ready to push", "push to remote", "stage and commit", or any similar
  intent to get local changes onto a remote repo. The skill runs a security scan for credentials,
  ensures .env files are gitignored, surfaces stash candidates, stages files one at a time
  (never git add .), and guides the full commit → pull → push flow with your confirmation at
  each step. Trigger this even if the user just says "let's push" or "can you push this for me".
---

# Git Safe Push

A structured, interactive workflow to get your local changes onto a remote repo without accidentally
exposing credentials, leaking .env files, or including work-in-progress you didn't mean to ship.

The flow has **five phases** (plus an optional Python quality check), each requiring your confirmation before proceeding to the next.
Never skip a phase — each one exists because it has caught real problems.

---

## Phase 1 — Situational Awareness

Run these and show a compact summary to the user:

```bash
git status --short
git branch --show-current
git remote -v
git log --oneline -1   # last commit for context
```

Tell the user:
- Which branch they're on, and flag if it's `main` or `master` (see Branch Safety below)
- Which remote will receive the push
- A short list of changed files (modified, new untracked, deleted)

If there is no remote configured, stop and ask the user to set one up:
```bash
git remote add origin <url>
```

---

## Phase 2 — Stash Review

Show the full list of modified and untracked files. Ask:

> "Are there any of these changes you **don't** want in this push — for example, work in progress that
> isn't ready yet? If so, I'll help you stash them before we move on."

If the user identifies files to stash, do it file-by-file:
```bash
git stash push -m "<short description>" -- <file1> <file2>
```
Confirm the stash was created:
```bash
git stash list | head -3
```

If everything looks good, move on.

---

## Phase 3 — .env Safety Check

This phase exists because `.env` files contain real secrets, and once they're in git history they're
very hard to fully remove — even after deletion.

1. Find all `.env*` files in the repo:
```bash
find . -name ".env*" -not -path "./.git/*" | sort
```

2. For each file found, check if it's covered by `.gitignore`:
```bash
git check-ignore -v <filepath>
```

**If a .env file is NOT gitignored:**
- Add it to `.gitignore` immediately:
  ```bash
  echo "<filepath>" >> .gitignore
  ```
- Then check if the file has any content:
  ```bash
  wc -l <filepath>
  cat <filepath>   # or truncate showing first 5 lines only
  ```
- If it has content: **pause and ask the user to review it**. Show the file contents
  (mask any obvious secret values with `***`). Ask: "This .env has content and wasn't gitignored.
  Do you need to rotate any of these values? I've added it to .gitignore now, but if it was
  previously committed, the value is already in git history."
- If it's empty: confirm it's now gitignored and move on.

3. If `.gitignore` was modified in this phase, add it to the files to be staged later.

---

## Phase 4 — Security Scan

Scan every file that would be staged for common credential patterns. The goal is to catch
**actual hardcoded values**, not references to env variables (which are fine).

Run this scan against the candidate files (use `git diff --name-only` for modified tracked files
plus any new untracked files the user wants to include):

```bash
grep -rniE \
  "(api[_-]?key|secret|password|token|bearer|private[_-]?key|access[_-]?key)\s*=\s*['\"][^'\"]{8,}['\"]|\
-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----|AKIA[0-9A-Z]{16}|\
DefaultEndpointsProtocol=https;AccountName=|\
AccountKey=[a-zA-Z0-9+/]{40,}==|\
mongodb(\+srv)?://[^:]+:[^@]+@|\
postgres://[^:]+:[^@]+@|\
mysql://[^:]+:[^@]+@" \
  <files> 2>/dev/null
```

**Interpreting results — what to flag vs. what is safe:**

| Pattern | Safe (skip) | Flag |
|---|---|---|
| `SECRET_KEY = os.environ["SECRET_KEY"]` | ✅ env var reference | — |
| `api_key = "${API_KEY}"` | ✅ template placeholder | — |
| `api_key = "sk-abc123xyz..."` | — | 🚨 hardcoded value |
| `password = "changeme"` or `"todo"` | — | ⚠️ ask user |
| `-----BEGIN PRIVATE KEY-----` | — | 🚨 stop immediately |
| `AKIA[16 caps]` | — | 🚨 AWS key |

For each finding, do NOT automatically remove or modify it. Instead:
- Show the file name, line number, and the flagged line (mask the actual value after the first 4 chars: `sk-ab***`)
- Ask the user: "This looks like a hardcoded credential. Is this intentional, or should this be moved to an environment variable?"

If the user says it's intentional and safe (e.g. a test fixture with a deliberately fake key), accept that and continue.
If the user confirms it's a real secret, help them move it to `.env` and replace the hardcoded value with the appropriate env var lookup before proceeding.

If there are **no findings**, say so clearly and move on.

---

## Phase 4b — Python Code Quality Check (only if .py files are staged)

If any of the files to be staged are `.py` files, run this check before staging. It catches issues
that would be embarrassing to push — the kind of thing a code reviewer would flag immediately.

### Type hints

Look at every function and method in the changed `.py` files. Check for:
- Missing parameter type annotations
- Missing return type annotations (including `-> None` on void functions)
- Use of bare `dict`, `list`, `tuple` instead of the typed forms (`dict[str, Any]`, `list[str]`, etc.)
- Missing `Optional[X]` / `X | None` on parameters that can be `None`

Show a short list of violations grouped by file and line number. If there are any, ask:
> "These functions are missing type hints. Do you want me to add them before we commit?"

If the user says yes, add them inline. If they say no, note it and continue — don't block the push.

### Code quality scan

Run `ruff` if available (it's fast and covers most best-practice rules):
```bash
ruff check <python files> --select E,W,F,B,C,N --output-format concise
```

If `ruff` is not installed, fall back to:
```bash
python -m py_compile <file>   # at minimum, catch syntax errors
```

Show any errors or warnings to the user. For serious issues (syntax errors, undefined names,
unused imports in production code), ask if they want them fixed before committing.
For style-only warnings, give a quick summary and let the user decide.

### Tests

Look for a test suite in the repo (common locations: `tests/`, `test/`, files matching `test_*.py`):
```bash
find . -name "test_*.py" -o -name "*_test.py" | grep -v '.git' | head -10
```

If tests exist, ask:
> "There are tests in this repo. Want me to run them before we commit to make sure nothing's broken?"

If the user says yes, run them:
```bash
python -m pytest --tb=short -q   # if pytest is available
# or
python -m unittest discover -q   # fallback
```

If any tests fail, show the failure summary and stop — don't proceed to staging until the user
has either fixed the failures or explicitly accepts the risk ("push anyway").

If all tests pass, confirm it and move on.

---

## Phase 5 — Stage, Commit, and Push

### 5a. Choose files to stage

Show the full list of changed files (`git status --short`) and ask:
> "Which of these files do you want to include in this commit? I'll list them and we'll add them one by one."

Stage each file explicitly — never use `git add .`:
```bash
git add <file1>
git add <file2>
# ... and so on
```

After staging, show a summary:
```bash
git diff --cached --stat
```

Let the user confirm this is what they want before writing the commit message.

### 5b. Commit

Suggest a commit message based on the staged changes. Keep it **short and scannable** — a good
commit message headline should fit in ~50 characters and make sense in a `git log --oneline` list.

Rules:
- Format: `<type>: <what changed>` — one line, no period at the end
- Types: `feat`, `fix`, `docs`, `chore`, `refactor`, `test`
- Be specific about *what*, not *how* (e.g. `docs: add langfuse tracing notes` not `docs: update documentation files`)
- No filler words: avoid "add support for", "implement", "update", "change" as the only verb
- If the change genuinely needs more context, add a blank line + body paragraph — but the headline stays ≤50 chars

**Bad:** `chore: made some updates to the files and fixed a few things`
**Good:** `fix: remove hardcoded Cosmos DB key from config.py`

Ask the user to confirm or modify the message, then commit:
```bash
git commit -m "<confirmed message>"
```

### 5c. Sync with remote

Pull with rebase to avoid a merge commit if the remote has diverged:
```bash
git pull --rebase origin <branch>
```

If this produces conflicts, stop and help the user resolve them before pushing.

### 5d. Push

```bash
git push origin <branch>
```

After a successful push, confirm with the remote URL and commit SHA:
```bash
git log --oneline -1
```

---

## Branch Safety

If the current branch is `main` or `master`:
- Warn the user: "You're about to push directly to `<main/master>`. Is that intentional?"
- Offer to create a feature branch and push there instead:
  ```bash
  git checkout -b feature/<name>
  git push origin feature/<name>
  ```
- If the user confirms they want to push to main, proceed — don't block them.

---

## Guardrails Summary (what this skill will never do)

- Never run `git add .` — always stage file by file
- Never force-push (`--force`) unless the user explicitly asks and explains why
- Never modify or delete files to "fix" a security finding without the user's explicit confirmation
- Never proceed to staging if a `.env` file was found unignored and not yet reviewed
- Never push if a private key (`-----BEGIN PRIVATE KEY-----`) is found in staged content

---

## Notes for edge cases

- **Binary files**: skip security scanning for `.png`, `.jpg`, `.pdf`, etc.
- **Large files** (>1MB): flag them and ask if the user intended to include them in git (not LFS)
- **No commits yet** (brand new repo): use `git commit` normally, skip the pull/rebase step
- **SSH vs HTTPS**: just run with whatever remote is configured — don't change transport
- **.env.example files**: these are intentionally public and should NOT be treated as secrets
  (their purpose is to document required env var names without real values)
