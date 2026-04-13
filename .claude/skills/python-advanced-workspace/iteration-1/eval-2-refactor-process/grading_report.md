# Grading Report — eval-2-refactor-process

**Task:** Refactor a nested-if invoice-filtering function using Python 3.10+ idioms.  
**Graded:** 2025-04-11

---

## WITH SKILL — Score: 6 / 8

**File:** `with_skill/outputs/refactored.py`

| # | Expectation | Result | Evidence |
|---|-------------|--------|----------|
| 1 | `match` statement replaces nested `if` chains | ✅ PASS | `match record.type: case "invoice": … case _:` on lines 50–60 |
| 2 | TypedDict or Pydantic model for item shape | ✅ PASS | `RawRecord(BaseModel)` + `InvoiceRecord(BaseModel)` defined; all field access via model attributes |
| 3 | No `.get()` calls anywhere | ✅ PASS | Zero `.get()` calls; all access is through validated Pydantic model attributes |
| 4 | No `or 'unknown'` or similar silent coercions | ❌ FAIL | `id=record.id if record.id is not None else "unknown"` — semantically identical to `or 'unknown'`; the docstring even documents the fallback, making it an intentional silent coercion rather than a fail-fast design |
| 5 | Full type hints on all functions/variables, modern syntax | ✅ PASS | `def process(data: list[dict[str, Any]]) -> list[InvoiceRecord]`, `invoices: list[InvoiceRecord]`, `type: str \| None`, `amount: float \| None` all use modern union syntax |
| 6 | Split into multiple focused functions | ❌ FAIL | Only one top-level function `process()` exists; no helpers such as `_build_invoice_record()`, `_is_valid_invoice()`, or `_parse_raw_record()` are extracted |
| 7 | `logging.getLogger(__name__)` present, no `print()` | ✅ PASS | `logger = logging.getLogger(__name__)` at module level; two `.debug()` call sites; no `print()` |
| 8 | PEP8 clean, descriptive names, no single-letter vars | ✅ PASS | `raw`, `record`, `invoices` are all descriptive; no `r`, `d`, or similar abbreviations |

**Missed expectations:** #4 (silent 'unknown' fallback), #6 (no function decomposition).

---

## WITHOUT SKILL — Score: 1 / 8

**File:** `without_skill/outputs/refactored.py`

| # | Expectation | Result | Evidence |
|---|-------------|--------|----------|
| 1 | `match` statement replaces nested `if` chains | ❌ FAIL | Uses `if item.get("type") != "invoice": continue` — a guard clause rewrite, not a `match` statement |
| 2 | TypedDict or Pydantic model for item shape | ❌ FAIL | Still operates on raw `dict[str, Any]`; no type model defined |
| 3 | No `.get()` calls anywhere | ❌ FAIL | Three `.get()` calls: `item.get("type")`, `item.get("amount")`, `item.get("id")` |
| 4 | No `or 'unknown'` or similar silent coercions | ❌ FAIL | `item.get("id") or "unknown"` is verbatim from the original code |
| 5 | Full type hints on all functions/variables, modern syntax | ❌ FAIL | Function signature is typed but `result = []` lacks annotation; return type `list[dict[str, Any]]` is imprecise (should be a named model); no variable-level annotations |
| 6 | Split into multiple focused functions | ❌ FAIL | Single monolithic function, unchanged structure from the original |
| 7 | `logging.getLogger(__name__)` present, no `print()` | ❌ FAIL | No `import logging`, no logger; no observability at all |
| 8 | PEP8 clean, descriptive names, no single-letter vars | ✅ PASS | `result`, `item`, `amount` are acceptable names; no single-letter vars; formatting is clean |

**Missed expectations:** #1, #2, #3, #4, #5, #6, #7.

---

## Comparative Summary

| Expectation | WITH SKILL | WITHOUT SKILL |
|---|---|---|
| 1 — `match` statement | ✅ | ❌ |
| 2 — Pydantic / TypedDict | ✅ | ❌ |
| 3 — No `.get()` | ✅ | ❌ |
| 4 — No silent coercions | ❌ | ❌ |
| 5 — Full type hints | ✅ | ❌ |
| 6 — Multiple functions | ❌ | ❌ |
| 7 — Logging | ✅ | ❌ |
| 8 — PEP8 / naming | ✅ | ✅ |
| **Score** | **6 / 8** | **1 / 8** |

The skill-guided solution demonstrates mastery of the structural and typing expectations — Pydantic models, `match`, no raw dict access, modern type annotation syntax, and proper logging. Its two failures (#4 and #6) are related: by keeping a single `process()` function, there is no natural place to enforce fail-fast behaviour on the `id` field; a helper like `_validate_id(value: str | None) -> str` would make the coercion explicit and testable, and extraction of that helper would simultaneously satisfy #6.

The no-skill solution essentially performs a mild stylistic cleanup (removes one level of nesting via guard clauses) but leaves the core structure, paradigm, and idioms unchanged from the original, satisfying only naming conventions.

---

## Eval Improvement Suggestions

1. **Tighten expectation #4 wording.** The current phrasing "no `or 'unknown'` or similar silent coercions" is ambiguous about ternary-style fallbacks. Rewrite as: *"Any missing required field must raise a `ValueError` or be surfaced via a Pydantic `ValidationError`; no silent default substitution for `id`."*

2. **Add a negative test case for expectation #6.** The current check is binary (functions: yes/no). Add: *"Must define at least two distinct functions, one of which is a predicate or constructor helper (e.g., `_is_valid_invoice(record: RawRecord) -> bool`)."* This forces decomposition rather than rewarding a single well-structured function.

3. **Add an expectation for exception / validation surface.** Neither solution raises on truly invalid input (e.g., `amount` being a string). A useful addition: *"Invalid records must raise `pydantic.ValidationError` or be logged at WARNING level with the offending value."*

4. **Add a testability expectation.** Require at least one unit test or doctest to verify the function, which would naturally push toward smaller composable helpers (reinforcing #6).

5. **Clarify `match` usage scope.** Currently the with-skill solution wraps the entire loop body in a single `match`. Consider requiring that `match` also pattern-match on `amount` range (e.g., `case {"amount": float(a) if a > 0}` structural matching) to fully demonstrate Python 3.10 structural pattern matching rather than a simple type-switch.
