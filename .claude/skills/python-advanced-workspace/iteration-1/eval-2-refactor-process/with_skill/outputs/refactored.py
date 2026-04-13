"""Invoice record processing utilities."""

import logging
from typing import Any

from pydantic import BaseModel, ConfigDict

logger = logging.getLogger(__name__)


class RawRecord(BaseModel):
    """Unvalidated record from an external data sequence; extra fields are tolerated."""

    model_config = ConfigDict(extra="allow")

    type: str | None = None
    id: str | None = None
    amount: float | None = None


class InvoiceRecord(BaseModel):
    """A validated, positive-amount invoice record."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    amount: float


def process(data: list[dict[str, Any]]) -> list[InvoiceRecord]:
    """Filter *data* to invoices with a strictly positive amount.

    Records missing a ``type`` field, of a type other than ``'invoice'``,
    or without a positive ``amount`` are dropped.  Missing ``id`` values
    fall back to the string ``'unknown'``.

    Args:
        data: Sequence of raw record dicts from an external source.
              Each dict may contain arbitrary extra keys.

    Returns:
        A list of validated :class:`InvoiceRecord` instances.
    """
    invoices: list[InvoiceRecord] = []

    for raw in data:
        record = RawRecord.model_validate(raw)

        match record.type:
            case "invoice":
                if record.amount is None or record.amount <= 0:
                    logger.debug(
                        "Skipping invoice id=%s: non-positive amount=%s",
                        record.id,
                        record.amount,
                    )
                    continue
                invoices.append(
                    InvoiceRecord(
                        id=record.id if record.id is not None else "unknown",
                        amount=record.amount,
                    )
                )
            case _:
                logger.debug("Skipping non-invoice record: type=%s", record.type)

    return invoices
