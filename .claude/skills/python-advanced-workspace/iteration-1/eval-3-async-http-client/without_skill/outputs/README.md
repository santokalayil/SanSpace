# async-http-client

Async HTTP client wrapper around [httpx](https://www.python-httpx.org/) that fetches multiple URLs concurrently and returns a typed summary.

## Requirements

- Python 3.11+
- `httpx`

```
pip install httpx
```

## Usage

```python
import asyncio
from client import AsyncHTTPClient

async def main():
    client = AsyncHTTPClient(timeout=10.0, max_concurrency=5)
    summary = await client.fetch_all([
        "https://example.com",
        "https://httpbin.org/status/404",
        "https://this-does-not-exist.invalid/",
    ])

    print(f"{summary.succeeded}/{summary.total} succeeded")

    for result in summary.results:
        if result.success:
            print(f"OK   {result.url}  ({result.status_code}, {result.elapsed_ms:.0f}ms)")
        else:
            print(f"FAIL {result.url}  — {result.error}")

asyncio.run(main())
```

## Design notes

| Concern | Approach |
|---|---|
| Concurrency | `asyncio.gather` over all URLs; `asyncio.Semaphore` caps simultaneous in-flight requests |
| Error isolation | Each URL is fetched in its own `try/except`; one failure never cancels others |
| Typed results | `FetchResult` (frozen dataclass) and `BatchSummary` (frozen dataclass); no `dict` blobs |
| Logging | `logging` at DEBUG/INFO/WARNING — nothing printed directly |
| httpx parity | Constructor `**httpx_kwargs` passes through to `httpx.AsyncClient` (headers, proxies, etc.) |

## Running the demo

```
python client.py
```

Hits a handful of httpbin.org endpoints (including deliberate 404/500/connection errors) and prints a summary.
