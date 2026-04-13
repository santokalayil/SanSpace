# async-http-client

Async HTTP client wrapper for Python **3.11+** that fetches multiple URLs
concurrently, handles per-URL failures gracefully, and returns a typed summary.

## Dependencies

```
httpx>=0.27
pydantic>=2.0
```

## Package layout

| File | Purpose |
|---|---|
| `models.py` | Pydantic v2 result types: `FetchStatus`, `FetchResult`, `BatchSummary` |
| `client.py` | `AsyncHttpClient` + private helpers `_make_result`, `_log_result` |
| `__init__.py` | Re-exports the public surface |

## Quick start

```python
import asyncio
import logging
from outputs import AsyncHttpClient

logging.basicConfig(level=logging.INFO)

urls = [
    "https://httpbin.org/get",
    "https://httpbin.org/status/404",
    "https://httpbin.org/delay/15",   # will time out at default 10 s
    "https://does-not-exist.invalid", # connect error
]

async def main() -> None:
    async with AsyncHttpClient(timeout=10.0, max_connections=10) as client:
        summary = await client.fetch_all(urls)

    print(f"total={summary.total}  ok={summary.succeeded}  err={summary.failed}")
    for r in summary.results:
        print(r.status, r.url, r.status_code, r.elapsed_seconds)

asyncio.run(main())
```

## Design decisions

### Per-URL failure isolation
`fetch_one` catches every `httpx` exception class individually and converts
each into a `FetchResult`. They never propagate into `asyncio.TaskGroup`, so
one failing URL cannot cancel the others.

### ExceptionGroup / except*
`_require_open()` is called **before** the `try` block in `fetch_one`, so a
`RuntimeError` (client not opened — a programming error) escapes the task
unhandled. `fetch_all` uses `except* RuntimeError` to intercept and re-raise
the `ExceptionGroup`. This is the idiomatic Python 3.11 pattern: use `except*`
at the TaskGroup boundary for errors that shouldn't be silently swallowed.

### asyncio.TaskGroup (3.11+)
Preferred over `asyncio.gather` for structured concurrency. All tasks are
guaranteed to be awaited before the `async with` block exits, eliminating
the dangling-task bugs that `gather` with `return_exceptions=True` can hide.

### Pydantic v2 models
All result types use `ConfigDict(extra="forbid", frozen=True)` — unknown
fields are an error and models are immutable after construction.

### Self type (stdlib, 3.11+)
`__aenter__` returns `Self` so subclasses work correctly without override.
`BatchSummary.from_results` returns `Self` for the same reason.

### match statement (3.10+)
`_log_result` uses `match result.status` to dispatch log levels, removing an
`if/elif` chain and making each case's intent explicit.
