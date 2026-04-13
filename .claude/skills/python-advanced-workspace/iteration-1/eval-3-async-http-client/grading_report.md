# Grading Report — Eval 3: Async HTTP Client

**Task:** Python 3.11 async HTTP client wrapper around httpx — concurrent batch fetching, typed results, graceful per-URL failure handling, structured logging.

---

## WITH SKILL — Score: 9/10

Files: `models.py`, `client.py`, `__init__.py`

### Expectation-by-expectation

| # | Expectation | Result | Evidence |
|---|-------------|--------|----------|
| 1 | `asyncio.TaskGroup`, not `asyncio.gather` | **PASS** | `async with asyncio.TaskGroup() as tg:` — `client.py` line 106 |
| 2 | Pydantic v2 models with `extra="forbid"` and `frozen=True` | **PASS** | `model_config = ConfigDict(extra="forbid", frozen=True)` on both `FetchResult` and `BatchSummary` — `models.py` lines 24–25, 37–38 |
| 3 | `Self` from `typing` for `__aenter__` return | **PASS** | `from typing import Self`; `async def __aenter__(self) -> Self:` — `client.py` lines 7, 50 |
| 4 | Full type annotations — no bare `Any`, no legacy `Optional`/`Dict`/`List` | **PASS** | All annotations use `dict[str, str] \| None`, `list[str]`, `int \| None`. No `Any` import. |
| 5 | Per-URL exception handling, batch not cancelled | **PASS** | `fetch_one` catches `TimeoutException`, `ConnectError`, `HTTPStatusError`, `Exception`; all return `FetchResult` without re-raising |
| 6 | `ExceptionGroup` / `except*` used | **PASS** | `except* RuntimeError as eg:` — `client.py` line 113 |
| 7 | `logging.getLogger(__name__)`, no `print()` | **PASS** | `logger = logging.getLogger(__name__)` — `client.py` line 13; zero `print()` calls |
| 8 | `httpx.AsyncClient` used as async context manager | **FAIL** | `httpx.AsyncClient(...)` is instantiated directly in `__aenter__` and closed via `await self._http.aclose()` in `__aexit__` — never used as `async with httpx.AsyncClient(...) as client:` |
| 9 | `match` statement used | **PASS** | `match result.status:` with five `case` arms — `client.py` lines 160–175 |
| 10 | No `.get()` silent defaults | **PASS** | No `.get()` calls found anywhere |

**Score: 9 / 10**

---

## WITHOUT SKILL — Score: 3/10

File: `client.py` only

### Expectation-by-expectation

| # | Expectation | Result | Evidence |
|---|-------------|--------|----------|
| 1 | `asyncio.TaskGroup`, not `asyncio.gather` | **FAIL** | `await asyncio.gather(*[self._fetch_one(url, client) for url in urls])` — `client.py` line 97 |
| 2 | Pydantic v2 models with `extra="forbid"` and `frozen=True` | **FAIL** | Uses `@dataclass(frozen=True)` from stdlib — not Pydantic; no `extra="forbid"` |
| 3 | `Self` from `typing` for `__aenter__` return | **FAIL** | Class has no `__aenter__` / `__aexit__` — not usable as an async context manager |
| 4 | Full type annotations — no bare `Any` | **FAIL** | `from typing import Any`; `**httpx_kwargs: Any` — `client.py` lines 9, 57 |
| 5 | Per-URL exception handling, batch not cancelled | **PASS** | `_fetch_one` catches `TimeoutException`, `HTTPStatusError`, `RequestError`, and bare `Exception`; all return `FetchResult`. Because nothing propagates, `gather` never cancels siblings. |
| 6 | `ExceptionGroup` / `except*` used | **FAIL** | No `except*` or `ExceptionGroup` anywhere |
| 7 | `logging.getLogger(__name__)`, no `print()` | **FAIL** | `logger = logging.getLogger(__name__)` is correct, but `_demo()` uses `print()` three times — `client.py` lines 118, 122, 124 |
| 8 | `httpx.AsyncClient` used as async context manager | **PASS** | `async with httpx.AsyncClient(**self._httpx_kwargs) as client:` — `client.py` line 95 |
| 9 | `match` statement used | **FAIL** | No `match` statement anywhere |
| 10 | No `.get()` silent defaults | **PASS** | No `.get()` calls found |

**Score: 3 / 10**

---

## Comparative Summary

| Expectation | WITH SKILL | WITHOUT SKILL |
|-------------|:-----------:|:-------------:|
| 1. `asyncio.TaskGroup` | ✅ | ❌ |
| 2. Pydantic v2 + config | ✅ | ❌ |
| 3. `Self` on `__aenter__` | ✅ | ❌ |
| 4. No bare `Any` / legacy generics | ✅ | ❌ |
| 5. Per-URL failure isolation | ✅ | ✅ |
| 6. `except*` / ExceptionGroup | ✅ | ❌ |
| 7. Logger only, no `print()` | ✅ | ❌ |
| 8. httpx.AsyncClient as ctx manager | ❌ | ✅ |
| 9. `match` statement | ✅ | ❌ |
| 10. No `.get()` silent defaults | ✅ | ✅ |
| **Total** | **9 / 10** | **3 / 10** |

The skill-guided solution is architecturally superior: it targets Python 3.11 specifically (TaskGroup, except*, match), uses Pydantic v2 with strict model config, maintains a proper async context manager class with `Self`, and keeps structured logging completely free of `print()`. The without-skill solution is a competent Python 3.9-era solution — it gets the happy path right and isolates per-URL errors correctly, but misses every Python 3.11-specific feature.

The single failure for the skill solution (expectation 8) is a design trade-off: `httpx.AsyncClient` is managed by the outer `AsyncHttpClient` context manager rather than via its own `async with`. This is arguably cleaner (one context manager for the user, longer-lived connection pool), but the expectation checked for the idiomatic `async with httpx.AsyncClient(...)` usage.

---

## Eval Improvement Suggestions

### Expectation 8 — Ambiguous phrasing
The expectation "httpx.AsyncClient used as async context manager" is underspecified. The with-skill solution *wraps* the httpx client in its own context manager lifecycle, which is a valid and arguably better production pattern (keeps the connection pool alive across multiple `fetch_all` calls). The grader should clarify whether the intent is:
- (a) `async with httpx.AsyncClient(...)` syntax must appear in the code, or
- (b) the httpx client's lifecycle must be properly managed (either via `async with` or `__aenter__`/`aclose()`)

If (b), with-skill passes. Recommend rewording to: *"httpx.AsyncClient lifecycle is properly managed via async context manager protocol (either `async with httpx.AsyncClient()` or explicit `__aenter__`/`aclose()`)"*.

### Expectation 5 vs 6 — Overlap and tension
Expectations 5 and 6 interact in a subtle way. TaskGroup (expectation 1) by default cancels all sibling tasks when one raises — so satisfying expectation 1 naively would break expectation 5. The with-skill solution resolves this correctly by catching all per-URL errors inside `fetch_one` so nothing escapes into TaskGroup, while using `except*` only for the programming-error (not-opened) case. Consider adding an assertion: *"TaskGroup is used AND per-URL errors do not propagate — i.e., exception handling is inside each task, not wrapping the TaskGroup"*. This would catch a naive implementation that catches exceptions around the whole `async with asyncio.TaskGroup()` block.

### Expectation 4 — Precision around `Any`
`**kwargs: Any` is a common stdlib/typing idiom for forwarding arbitrary keyword args to an external library. The without-skill solution uses it specifically for `**httpx_kwargs`. Consider whether this use is acceptable or whether the assertion should carve out pass-through kwargs patterns. A stricter reading: implementations should define explicit parameters instead of a catch-all `**kwargs`.

### Additional assertion candidates
The following properties appear in the with-skill solution but are not tested, and would further differentiate between a fully Python-3.11-idiomatic solution and a generic one:
- **`str | None` union syntax** rather than `Optional[str]` (partially covered by #4, but could be explicit)
- **`FetchStatus` as `str, enum.Enum`** — typed enum rather than free strings or booleans for outcome classification
- **`from_results` classmethod returning `Self`** — tests whether `Self` is used beyond just `__aenter__`
- **`follow_redirects=True` explicitly set** — production readiness check
