"""Async HTTP client wrapper around httpx for concurrent batch fetching."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import httpx

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class FetchResult:
    url: str
    status_code: int | None
    body: bytes | None
    error: str | None
    elapsed_ms: float | None
    fetched_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def success(self) -> bool:
        return self.error is None and self.status_code is not None


@dataclass(frozen=True)
class BatchSummary:
    results: tuple[FetchResult, ...]

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def succeeded(self) -> int:
        return sum(1 for r in self.results if r.success)

    @property
    def failed(self) -> int:
        return self.total - self.succeeded

    def successful(self) -> list[FetchResult]:
        return [r for r in self.results if r.success]

    def failures(self) -> list[FetchResult]:
        return [r for r in self.results if not r.success]


class AsyncHTTPClient:
    """Fetch multiple URLs concurrently with bounded concurrency and per-URL error isolation."""

    def __init__(
        self,
        *,
        timeout: float = 30.0,
        max_concurrency: int = 10,
        **httpx_kwargs: Any,
    ) -> None:
        self._timeout = httpx.Timeout(timeout)
        self._semaphore = asyncio.Semaphore(max_concurrency)
        self._httpx_kwargs = httpx_kwargs

    async def _fetch_one(self, url: str, client: httpx.AsyncClient) -> FetchResult:
        async with self._semaphore:
            logger.debug("→ fetching %s", url)
            try:
                response = await client.get(url, timeout=self._timeout)
                elapsed = response.elapsed.total_seconds() * 1000
                logger.info("✓ %s  status=%d  elapsed=%.1fms", url, response.status_code, elapsed)
                return FetchResult(
                    url=url,
                    status_code=response.status_code,
                    body=response.content,
                    error=None,
                    elapsed_ms=elapsed,
                )
            except httpx.TimeoutException as exc:
                logger.warning("✗ TIMEOUT %s — %s", url, exc)
                return FetchResult(url=url, status_code=None, body=None, error=f"Timeout: {exc}", elapsed_ms=None)
            except httpx.HTTPStatusError as exc:
                # Only raised when raise_for_status() is called; included for completeness.
                elapsed = exc.response.elapsed.total_seconds() * 1000
                logger.warning("✗ HTTP %d %s — %s", exc.response.status_code, url, exc)
                return FetchResult(
                    url=url,
                    status_code=exc.response.status_code,
                    body=None,
                    error=str(exc),
                    elapsed_ms=elapsed,
                )
            except httpx.RequestError as exc:
                logger.warning("✗ REQUEST_ERROR %s — %s", url, exc)
                return FetchResult(url=url, status_code=None, body=None, error=f"RequestError: {exc}", elapsed_ms=None)
            except Exception as exc:  # noqa: BLE001
                logger.exception("✗ UNEXPECTED %s", url)
                return FetchResult(url=url, status_code=None, body=None, error=f"Unexpected: {exc}", elapsed_ms=None)

    async def fetch_all(self, urls: list[str]) -> BatchSummary:
        """Fetch all URLs concurrently and return a typed BatchSummary.

        Each URL is fetched independently; a failure in one never cancels others.
        """
        async with httpx.AsyncClient(**self._httpx_kwargs) as client:
            results: list[FetchResult] = await asyncio.gather(
                *[self._fetch_one(url, client) for url in urls]
            )

        summary = BatchSummary(results=tuple(results))
        logger.info(
            "batch complete — total=%d  succeeded=%d  failed=%d",
            summary.total,
            summary.succeeded,
            summary.failed,
        )
        return summary


# ---------------------------------------------------------------------------
# Quick demo
# ---------------------------------------------------------------------------

async def _demo() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)-8s %(message)s")

    urls = [
        "https://httpbin.org/status/200",
        "https://httpbin.org/status/404",
        "https://httpbin.org/delay/1",
        "https://httpbin.org/status/500",
        "https://this-domain-does-not-exist.invalid/path",
    ]

    client = AsyncHTTPClient(timeout=5.0, max_concurrency=3)
    summary = await client.fetch_all(urls)

    print(f"\nResults: {summary.succeeded}/{summary.total} succeeded\n")
    for r in summary.results:
        tag = "OK " if r.success else "ERR"
        detail = f"status={r.status_code}  elapsed={r.elapsed_ms:.1f}ms" if r.success else r.error
        print(f"  [{tag}] {r.url}\n        {detail}")


if __name__ == "__main__":
    asyncio.run(_demo())
