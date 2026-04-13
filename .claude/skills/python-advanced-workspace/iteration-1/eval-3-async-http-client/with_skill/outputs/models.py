"""Typed result models for the async HTTP client."""
from __future__ import annotations

import enum
from typing import Self

from pydantic import BaseModel, ConfigDict


class FetchStatus(str, enum.Enum):
    """Outcome classification for a single URL fetch attempt."""

    SUCCESS = "success"
    HTTP_ERROR = "http_error"        # 4xx / 5xx response
    CONNECT_ERROR = "connect_error"  # DNS, TLS, or port unreachable
    TIMEOUT = "timeout"              # request exceeded the configured timeout
    UNEXPECTED = "unexpected"        # non-httpx runtime / programming error


class FetchResult(BaseModel):
    """Immutable record of a single URL fetch attempt."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    url: str
    status: FetchStatus
    status_code: int | None
    body: str | None
    error: str | None
    elapsed_seconds: float | None


class BatchSummary(BaseModel):
    """Aggregated outcome for a concurrent batch of URL fetches."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    total: int
    succeeded: int
    failed: int
    results: list[FetchResult]

    @classmethod
    def from_results(cls, results: list[FetchResult]) -> Self:
        """Compute aggregated counts from a list of FetchResult instances."""
        succeeded = sum(1 for r in results if r.status is FetchStatus.SUCCESS)
        return cls(
            total=len(results),
            succeeded=succeeded,
            failed=len(results) - succeeded,
            results=results,
        )
