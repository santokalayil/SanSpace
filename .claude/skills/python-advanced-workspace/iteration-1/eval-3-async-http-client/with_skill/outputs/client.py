"""Async HTTP client with concurrent batch fetching via asyncio.TaskGroup."""
from __future__ import annotations

import asyncio
import logging
import time
from typing import Self

import httpx

from .models import BatchSummary, FetchResult, FetchStatus

logger = logging.getLogger(__name__)

_DEFAULT_TIMEOUT: float = 10.0
_DEFAULT_MAX_CONNECTIONS: int = 20


class AsyncHttpClient:
    """Async HTTP client wrapper around httpx supporting concurrent batch fetches.

    Handles per-URL failures (timeout, connect error, HTTP error) gracefully —
    they are captured as ``FetchResult`` entries without cancelling other tasks.
    A programming error (client not opened) propagates as
    ``ExceptionGroup[RuntimeError]`` via ``except*``.

    Usage::

        async with AsyncHttpClient(timeout=5.0) as client:
            summary = await client.fetch_all(["https://example.com", ...])
    """

    def __init__(
        self,
        timeout: float = _DEFAULT_TIMEOUT,
        max_connections: int = _DEFAULT_MAX_CONNECTIONS,
        headers: dict[str, str] | None = None,
    ) -> None:
        self._timeout = httpx.Timeout(timeout)
        self._limits = httpx.Limits(
            max_connections=max_connections,
            max_keepalive_connections=max_connections,
        )
        self._base_headers: dict[str, str] = headers if headers is not None else {}
        self._http: httpx.AsyncClient | None = None

    async def __aenter__(self) -> Self:
        self._http = httpx.AsyncClient(
            timeout=self._timeout,
            limits=self._limits,
            headers=self._base_headers,
            follow_redirects=True,
        )
        logger.debug(
            "AsyncHttpClient opened — timeout=%.1fs max_connections=%d",
            self._timeout.read,
            self._limits.max_connections,
        )
        return self

    async def __aexit__(self, *_args: object) -> None:
        if self._http is not None:
            await self._http.aclose()
            self._http = None
        logger.debug("AsyncHttpClient closed")

    def _require_open(self) -> httpx.AsyncClient:
        """Return the underlying client or raise RuntimeError if not opened."""
        if self._http is None:
            raise RuntimeError(
                "AsyncHttpClient is not open. "
                "Use it as: async with AsyncHttpClient() as client: ..."
            )
        return self._http

    async def fetch_one(self, url: str) -> FetchResult:
        """Fetch a single URL and return a FetchResult regardless of outcome.

        All httpx-level failures (timeout, connect, HTTP status) are captured
        and returned as typed ``FetchResult`` values — they do not propagate.

        ``RuntimeError`` from ``_require_open`` is intentionally *not* caught
        here; it escapes the task so ``fetch_all`` can surface it via
        ``except*``.
        """
        client = self._require_open()  # RuntimeError propagates before the try
        start = time.monotonic()
        try:
            response = await client.get(url)
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            return _make_result(url, FetchStatus.TIMEOUT, None, None, str(exc), start)
        except httpx.ConnectError as exc:
            return _make_result(url, FetchStatus.CONNECT_ERROR, None, None, str(exc), start)
        except httpx.HTTPStatusError as exc:
            code = exc.response.status_code
            return _make_result(url, FetchStatus.HTTP_ERROR, code, None, f"HTTP {code}", start)
        except Exception as exc:  # non-httpx runtime surprise
            logger.error("Unexpected error url=%s", url, exc_info=True)
            return _make_result(url, FetchStatus.UNEXPECTED, None, None, repr(exc), start)

        return _make_result(
            url, FetchStatus.SUCCESS, response.status_code, response.text, None, start
        )

    async def fetch_all(self, urls: list[str]) -> BatchSummary:
        """Fetch all URLs concurrently; per-URL failures are captured in results.

        Raises ``ExceptionGroup[RuntimeError]`` (via ``except*``) when the
        client has not been opened — a programming error, not a recoverable one.
        """
        logger.info("Batch fetch starting — %d URL(s)", len(urls))
        tasks: list[asyncio.Task[FetchResult]] = []

        try:
            async with asyncio.TaskGroup() as tg:
                tasks = [tg.create_task(self.fetch_one(url), name=url) for url in urls]
        except* RuntimeError as eg:
            # _require_open() raised before the try-block inside fetch_one,
            # so RuntimeError escapes the task and surfaces here as
            # ExceptionGroup[RuntimeError]. Re-raise — it is a programming error.
            logger.error(
                "Batch aborted — client not opened; %d task(s) raised %s",
                len(eg.exceptions),
                [type(e).__name__ for e in eg.exceptions],
            )
            raise

        results = [task.result() for task in tasks]
        summary = BatchSummary.from_results(results)
        logger.info(
            "Batch complete — total=%d succeeded=%d failed=%d",
            summary.total,
            summary.succeeded,
            summary.failed,
        )
        return summary


# ── Module-level helpers ──────────────────────────────────────────────────────


def _make_result(
    url: str,
    status: FetchStatus,
    status_code: int | None,
    body: str | None,
    error: str | None,
    start: float,
) -> FetchResult:
    """Construct a FetchResult, log it, and return it."""
    result = FetchResult(
        url=url,
        status=status,
        status_code=status_code,
        body=body,
        error=error,
        elapsed_seconds=round(time.monotonic() - start, 4),
    )
    _log_result(result)
    return result


def _log_result(result: FetchResult) -> None:
    """Emit a structured log line at the appropriate level for *result*."""
    elapsed = (
        f"{result.elapsed_seconds:.4f}s"
        if result.elapsed_seconds is not None
        else "n/a"
    )
    match result.status:
        case FetchStatus.SUCCESS:
            logger.info(
                "OK        url=%s status=%d elapsed=%s",
                result.url, result.status_code, elapsed,
            )
        case FetchStatus.HTTP_ERROR:
            logger.warning(
                "HTTP ERR  url=%s status=%d elapsed=%s",
                result.url, result.status_code, elapsed,
            )
        case FetchStatus.TIMEOUT:
            logger.warning("TIMEOUT   url=%s elapsed=%s", result.url, elapsed)
        case FetchStatus.CONNECT_ERROR:
            logger.warning("CONN ERR  url=%s error=%s", result.url, result.error)
        case FetchStatus.UNEXPECTED:
            logger.error("UNEXPECTED url=%s error=%s", result.url, result.error)
