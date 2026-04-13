# Refactoring Notes — `process()`

## Python version
Target: **3.10** — native `X | Y` unions and `match` statement used throughout; no `from __future__ import annotations` required.

---

## What changed and why

### 1. Type annotations added everywhere
The original had none. Every parameter and return value is now annotated using built-in generics (`list[dict[str, Any]]`, `list[InvoiceRecord]`), with `X | Y` union syntax native to 3.10. `Optional[...]` and `Dict`/`List` from `typing` are deprecated since 3.9 and not used.

### 2. Pydantic models at the data boundary
The function receives raw external data (dicts of unknown shape). This is a data-boundary crossing, so the skill requires Pydantic.

- **`RawRecord`** (`extra="allow"`) — validates/coerces the incoming dict into a typed object. Unknown keys are tolerated since the docs are silent about them.
- **`InvoiceRecord`** (`extra="forbid"`, `frozen=True`) — the clean, immutable output type. Callers get a typed object instead of a raw dict; `extra="forbid"` ensures no junk slips through, `frozen=True` makes it safe from mutation.

### 3. Silent `.get()` and `value or fallback` removed
The original had three violations of the fail-fast rule:

| Original | Problem | Fix |
|---|---|---|
| `item.get('type') == 'invoice'` | silent `None` default if key absent | Pydantic field `type: str \| None = None` — explicit model |
| `item.get('amount')` | truthy-check loses `0` vs `None` distinction | Pydantic field `amount: float \| None = None`; checked with `is None` |
| `item.get('id') or 'unknown'` | coerces empty string `""` to `'unknown'` unintentionally | `record.id if record.id is not None else "unknown"` — explicit `None` check only |

### 4. Triple-nested `if` replaced with `match` + flat guard
The original used three levels of nesting to combine type-check, presence-check, and value-check. The `match` statement (Python 3.10+) cleanly dispatches on `record.type`, and a flat `if` guard inside the `"invoice"` case handles the amount validation. Each branch has one responsibility.

### 5. Structured logging added
The original dropped non-matching records silently with no observability. `logging.getLogger(__name__)` is now used (no `print()`), with `DEBUG`-level messages so production code can surface unexpected data without noise.

---

## Skill checklist result

| Check | Status |
|---|---|
| Python 3.10 idioms | ✅ `X \| Y`, `match` used |
| Full type annotations | ✅ |
| No `Dict`/`List`/`Optional` | ✅ |
| No silent `.get()` defaults | ✅ Pydantic handles input boundary |
| No `value or fallback` coercion | ✅ explicit `is not None` check |
| Pydantic at data boundary | ✅ `RawRecord.model_validate(raw)` |
| `extra="forbid"` on output model | ✅ |
| `frozen=True` on immutable model | ✅ |
| `logging.getLogger(__name__)` | ✅ |
| No `print()` | ✅ |
| Function ≤ ~30 lines | ✅ |
| `match` statement used | ✅ |
