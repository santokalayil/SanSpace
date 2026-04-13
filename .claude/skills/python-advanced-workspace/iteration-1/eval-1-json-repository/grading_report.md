# Grading Report — Eval 1: JSON User Repository

**Task:** Python 3.12 repository layer for reading/writing User records to a JSON file, swappable backend, clean separation.  
**Date graded:** 2026-04-11

---

## Solution A — `with_skill` (Advanced Python skill applied)

### Files reviewed
- `models.py` — domain model + custom exceptions
- `repository.py` — Protocol interface
- `json_repository.py` — JSON-backed implementation
- `__init__.py` — package public surface
- `_smoke_test.py` — verification tests

---

### Assertion-by-assertion evaluation

#### Assertion 1 — Uses `Protocol` (not ABC) for the repository interface
**PASS**

```python
# repository.py
from typing import Protocol, runtime_checkable
...
@runtime_checkable
class UserRepository(Protocol):
    ...
```

Protocol-based structural subtyping — no `ABC`, no `abstractmethod`. `@runtime_checkable` correctly added to support `isinstance()` checks.

---

#### Assertion 2 — Pydantic v2 with `extra="forbid"` and `frozen=True`
**PASS**

```python
# models.py
from pydantic import BaseModel, ConfigDict, field_validator

class User(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    id: UUID
    email: str
    full_name: str
    roles: list[str] | None = None
```

Both `extra="forbid"` and `frozen=True` are present. Uses `ConfigDict` (Pydantic v2 style, not the v1 inner `Config` class). Bonus: `field_validator` normalises email to lowercase.

---

#### Assertion 3 — `pathlib.Path`, no `os.path` anywhere
**PASS**

```python
# json_repository.py
from pathlib import Path
...
if not file_path.exists():
file_path.read_text(encoding="utf-8")
file_path.parent.mkdir(parents=True, exist_ok=True)
tmp_path = file_path.with_suffix(".tmp")
tmp_path.replace(file_path)
```

No `os.path` or `open()` calls anywhere in the package. Uses `Path.read_text`, `Path.write_text`, `Path.replace`, and `Path.with_suffix`.

---

#### Assertion 4 — No silent `.get()` defaults
**FAIL (minor)**

```python
# json_repository.py — get_by_email
for record in store["users"].values():
    if record.get("email") == normalised:   # <-- silent None if key absent

# json_repository.py — _assert_email_unowned
if record.get("email") == incoming.email and existing_key != str(incoming.id):  # <-- same
```

Two uses of `.get("email")` without a default parameter and without an explicit `None` guard. If a record in the file were missing the `email` key (manual edits, schema migration), the comparison would silently return `False` rather than raising an error, causing missed duplicate detection or missed email lookups. The records are _guaranteed_ to contain `email` because they are written via `user.model_dump(mode="json")`, so this is unlikely to cause a real bug — but it technically violates the assertion. A strict implementation would use `record["email"]` directly and let a `KeyError` propagate, or guard explicitly.

---

#### Assertion 5 — Full type annotations in Python 3.12 syntax; no `Optional`/`Dict`/`List`/`Tuple` from `typing`
**PASS**

```python
# models.py
roles: list[str] | None = None

# repository.py
def list_all(self) -> list[User]: ...
def get_by_id(self, user_id: UUID) -> User: ...

# json_repository.py (PEP 695 type aliases — see assertion 10)
type _RawRecord = dict[str, object]
type _UsersTable = dict[str, _RawRecord]
type _Store = dict[str, _UsersTable]
```

No imports from `typing` of `Optional`, `Dict`, `List`, or `Tuple`. All annotations use native Python 3.10+ union syntax and built-in generic aliases. Every defined function/method has parameter and return type annotations.

---

#### Assertion 6 — `logging.getLogger(__name__)`; no `print()`
**PASS** _(production code; smoke test prints are test-only)_

```python
# models.py
logger = logging.getLogger(__name__)

# json_repository.py
logger = logging.getLogger(__name__)
...
logger.debug("Store file absent, returning empty store: %s", file_path)
logger.debug("get_by_id hit: id=%s", user_id)
logger.info("save: upserted user id=%s email=%s", user.id, user.email)
logger.info("delete: removed user id=%s", user_id)
```

Production modules use `logger.debug` and `logger.info` throughout. The `_smoke_test.py` file uses `print()`, but that is explicitly a test script, not part of the library surface.

---

#### Assertion 7 — Relative imports within the package
**PASS**

```python
# repository.py
from .models import DuplicateUserError, User, UserNotFoundError

# json_repository.py
from .models import DuplicateUserError, User, UserNotFoundError

# __init__.py
from .json_repository import JsonUserRepository
from .models import DuplicateUserError, User, UserNotFoundError
from .repository import UserRepository
```

Every intra-package import uses the `.module` relative form throughout.

---

#### Assertion 8 — Functions/methods focused and ≤ 30 lines each
**PASS**

Methods are short and purposeful. Large operations are factored into named helpers:

- `_load_store` (~20 lines) — file I/O + validation
- `_save_store` (~15 lines) — atomic write
- `_assert_email_unowned` (~8 lines) — duplicate guard, extracted to keep `save` short
- `get_by_id`, `delete`, `save`, `list_all`, `exists` — each ≤ 12 lines
- `_sentinel_uuid_for_email` — 6 lines

No method exceeds 30 lines.

---

#### Assertion 9 — Custom exceptions on not-found and duplicate cases
**PASS**

```python
# models.py
class UserNotFoundError(KeyError):
    def __init__(self, user_id: UUID) -> None: ...

class DuplicateUserError(ValueError):
    def __init__(self, field: str, value: str) -> None: ...
```

```python
# json_repository.py
if key not in users:
    raise UserNotFoundError(user_id)   # get_by_id

raise DuplicateUserError("email", incoming.email)   # _assert_email_unowned

if key not in users:
    raise UserNotFoundError(user_id)   # delete
```

Both custom exceptions are well-defined with typed attributes and override `__str__`. They are raised at every not-found/duplicate path — never swallowed as bare `KeyError` or `ValueError`.

---

#### Assertion 10 — Python 3.12 `type X = ...` syntax OR PEP 695 generics
**PASS**

```python
# json_repository.py
type _RawRecord = dict[str, object]
type _UsersTable = dict[str, _RawRecord]   # keyed by UUID string
type _Store = dict[str, _UsersTable]        # top-level file structure
```

Three PEP 695 `type` statement aliases are used, providing internal type safety without runtime overhead and documenting the JSON schema structure precisely.

---

### `with_skill` Score: **9 / 10**

| # | Assertion | Result |
|---|-----------|--------|
| 1 | Protocol (not ABC) | ✅ PASS |
| 2 | Pydantic v2 `extra="forbid"` + `frozen=True` | ✅ PASS |
| 3 | `pathlib.Path`, no `os.path` | ✅ PASS |
| 4 | No silent `.get()` defaults | ❌ FAIL |
| 5 | Full Python 3.12 type annotations | ✅ PASS |
| 6 | `logging.getLogger(__name__)`, no `print()` | ✅ PASS |
| 7 | Relative imports within package | ✅ PASS |
| 8 | Methods ≤ 30 lines | ✅ PASS |
| 9 | Custom exceptions for not-found/duplicate | ✅ PASS |
| 10 | `type X = ...` / PEP 695 generics | ✅ PASS |

---

---

## Solution B — `without_skill` (Plain code, no guidelines)

### Files reviewed
- `models.py` — dataclass model
- `repository.py` — ABC-based interface
- `json_repository.py` — JSON-backed implementation

---

### Assertion-by-assertion evaluation

#### Assertion 1 — Uses `Protocol` (not ABC) for the repository interface
**FAIL**

```python
# repository.py
from abc import ABC, abstractmethod
...
class UserRepository(ABC):
    @abstractmethod
    def get(self, user_id: UUID) -> User | None: ...
```

Uses `ABC` with `@abstractmethod`. Callers must explicitly subclass `UserRepository`, creating tight coupling. There is no way to verify structural compatibility without inheritance.

---

#### Assertion 2 — Pydantic v2 with `extra="forbid"` and `frozen=True`
**FAIL**

```python
# models.py
from dataclasses import dataclass, field
from uuid import UUID, uuid4

@dataclass
class User:
    id: UUID
    email: str
    full_name: str
    roles: list[str] = field(default_factory=list)
```

No Pydantic. Uses `@dataclass` — no input validation, no schema enforcement (`extra="forbid"` has no equivalent here), and the model is mutable (no `frozen=True`). Extra fields from a corrupt JSON file would silently cause a `TypeError` from the `User()` constructor rather than a validation error.

---

#### Assertion 3 — `pathlib.Path`, no `os.path` anywhere
**PASS**

```python
# json_repository.py
from pathlib import Path
...
self._path = Path(path)
if not self._path.exists():
    self._path.parent.mkdir(parents=True, exist_ok=True)
    self._path.write_text("[]", encoding="utf-8")
```

`pathlib.Path` is used consistently. No `os.path` usage anywhere.

---

#### Assertion 4 — No silent `.get()` defaults
**FAIL**

```python
# json_repository.py — _to_user
@staticmethod
def _to_user(record: dict) -> User:
    return User(
        id=UUID(record["id"]),
        email=record["email"],
        full_name=record["full_name"],
        roles=record.get("roles", []),   # <-- silent default []
    )
```

`record.get("roles", [])` silently defaults to an empty list if the `roles` key is absent. If the stored JSON has a missing `roles` field (e.g., from a different schema version or manual edit), this would hydrate a `User` with `roles=[]` without any warning, log entry, or error — hiding data corruption.

---

#### Assertion 5 — Full type annotations in Python 3.12 syntax; no `Optional`/`Dict`/`List`/`Tuple` from `typing`
**FAIL**

No prohibited `typing` imports are present, which is positive. However the annotations are incomplete:

```python
# json_repository.py
def _load(self) -> dict[str, dict]:        # inner dict unparameterised
def _flush(self, records: dict[str, dict]) -> None:   # inner dict unparameterised
def _to_user(record: dict) -> User:        # bare dict, no key/value types
def _from_user(user: User) -> dict:        # bare dict, no key/value types
def __init__(self, path: Path | str) -> None:   # acceptable (-> None ok to omit per convention)
```

```python
# models.py
def create(...) -> "User":                 # string-quoted forward ref (unnecessary in 3.12)
```

`dict` without type parameters is used in four distinct places. The assertion requires _full_ type annotations; bare `dict` does not meet this standard. Additionally, `"User"` as a forward reference string is unnecessary in Python 3.12, where `from __future__ import annotations` or direct references both work. The annotation coverage is incomplete.

---

#### Assertion 6 — `logging.getLogger(__name__)`; no `print()`
**FAIL**

No `import logging` appears in any file. No `logger = logging.getLogger(__name__)`. No log calls of any kind. The implementation is entirely silent: no indication of initialisation, reads, writes, or errors in any structured log stream.

---

#### Assertion 7 — Relative imports within the package
**FAIL**

```python
# repository.py
from models import User            # absolute — breaks when package is installed

# json_repository.py
from models import User
from repository import UserRepository    # absolute — same issue
```

All intra-package imports are absolute. This breaks if the package is imported from outside its own directory (e.g., after `pip install`, or when running tests from a different working directory). Relative imports (`from .models import ...`) are the correct form inside a package.

---

#### Assertion 8 — Functions/methods focused and ≤ 30 lines each
**PASS**

All methods are short. The longest is `__init__` at 4 lines. `_load`, `_flush`, `_to_user`, `_from_user`, and the CRUD methods are all under 10 lines. No method violates the 30-line limit.

---

#### Assertion 9 — Custom exceptions on not-found and duplicate cases
**FAIL**

```python
# json_repository.py
def get(self, user_id: UUID) -> User | None:
    record = self._load().get(str(user_id))
    return self._to_user(record) if record is not None else None   # returns None

def delete(self, user_id: UUID) -> bool:
    ...
    if key not in records:
        return False     # returns False, not exception
```

No custom exception classes are defined anywhere. `get` returns `None` on miss and `delete` returns `False`. This forces callers to check return values rather than handling typed exceptions, which is fragile (callers can ignore `None` or `False`). There is also no DuplicateUserError check in `save` — duplicate emails are silently overwritten.

---

#### Assertion 10 — Python 3.12 `type X = ...` syntax OR PEP 695 generics
**FAIL**

No `type X = ...` statements appear anywhere. No PEP 695 generic syntax is used. The code does not leverage any Python 3.12-specific typing features.

---

### `without_skill` Score: **2 / 10**

| # | Assertion | Result |
|---|-----------|--------|
| 1 | Protocol (not ABC) | ❌ FAIL |
| 2 | Pydantic v2 `extra="forbid"` + `frozen=True` | ❌ FAIL |
| 3 | `pathlib.Path`, no `os.path` | ✅ PASS |
| 4 | No silent `.get()` defaults | ❌ FAIL |
| 5 | Full Python 3.12 type annotations | ❌ FAIL |
| 6 | `logging.getLogger(__name__)`, no `print()` | ❌ FAIL |
| 7 | Relative imports within package | ❌ FAIL |
| 8 | Methods ≤ 30 lines | ✅ PASS |
| 9 | Custom exceptions for not-found/duplicate | ❌ FAIL |
| 10 | `type X = ...` / PEP 695 generics | ❌ FAIL |

---

---

## Comparative Summary

| Criterion | with_skill | without_skill |
|-----------|-----------|---------------|
| **Total score** | **9 / 10** | **2 / 10** |
| Repository interface | Protocol (structural) | ABC (nominal, tight coupling) |
| Domain model | Pydantic v2, immutable, validated | dataclass, mutable, unvalidated |
| Swappability | Any class structurally matching the Protocol works | Must explicitly subclass ABC |
| Error handling | Custom typed exceptions; all error paths raise | `None` / `bool` return values; no exceptions |
| Logging | `logging.getLogger(__name__)` at debug + info levels | None whatsoever |
| Import style | Relative (package-safe) | Absolute (breaks outside cwd) |
| Persistence safety | Atomic write (tmp + rename) | Direct overwrite (data loss on crash) |
| Python 3.12 features | PEP 695 `type` aliases, full annotations | No 3.12-specific features |
| Type annotation quality | Complete, fully parameterised | Incomplete, bare `dict` used |
| One marginal issue | `.get("email")` used for comparison (benign in practice) | n/a |

**`with_skill` is the significantly stronger solution.** It satisfies 9 of 10 assertions and demonstrates production-quality Python 3.12 idioms: Protocol-based interfaces for zero-coupling swappability, Pydantic v2 validation, atomic file writes, PEP 695 type aliases, structured logging, custom domain exceptions, and complete type annotation coverage.

**`without_skill` passes only 2 of 10 assertions** — `pathlib.Path` usage and short methods. The output is functional (reads/writes JSON correctly) but falls short across every dimension that matters for production code: no validation, no typed error surface, no logging, broken import style, silent data-loss scenarios, and tight ABC coupling.

---

## Additional Observations Not Covered by the 10 Assertions

### with_skill extras
- **Atomic writes** (`tmp_path.replace(file_path)`): prevents half-written files on crash — excellent production practice not required by assertions.
- **`_sentinel_uuid_for_email`**: uses `uuid.uuid5` to generate a deterministic error UUID for missing-email errors, giving meaningful context without revealing state.
- **Email normalisation at model construction** via `field_validator`: enforces lowercase constraint at the boundary, preventing duplicates that differ only in case from persisting.
- **`__all__` in `__init__.py`**: clean public API surface, restricts accidental re-export.
- **`_smoke_test.py`**: six runnable tests covering the full CRUD cycle, email normalisation, and both exception types — demonstrates the interface works end-to-end.

### without_skill extras
- **`User.create()` factory method**: generates a UUID automatically for callers — good DX affordance not present in the with_skill solution.
- **Thread-safety disclaimer in docstring**: honest documentation of known limitations.
- **Simpler API contract**: `get` → `User | None` and `delete` → `bool` may suit simple scripts where exception handling is considered heavy. This is a deliberate design choice, but it conflicts with the stated expectation of custom exceptions.

---

## Eval Improvement Suggestions

1. **Assert #4 is ambiguous** — distinguish between `.get(key)` used as a _value_ (silent default) vs. `.get(key)` used in a comparison (where None is a valid comparison result). With_skill's usage is logically safe but technically fails the literal assertion. Consider rewording to: _"No `.get()` call that silently consumes a fallback value for downstream use; lookup for comparison is permitted."_

2. **Assert #5 should specify "all public functions/methods must have return annotations"** to make it unambiguous that bare `dict` and missing `-> None` annotations are failures.

3. **Add an assertion for mutability**: the task asks for a model that could be replaced by a Postgres backend. Immutable models (Pydantic `frozen=True`) avoid accidental in-place mutation bugs and map cleanly to Postgres row objects. This is implicitly tested by assertion 2 but could be broken out.

4. **Add an assertion for atomic persistence**: silently overwriting a file while writing is a data-integrity bug that affects production deployments. A `tmp + rename` pattern (or equivalent) is absent in without_skill. The eval currently does not penalise this.

5. **Add an assertion for swappability verification**: require that `isinstance(JsonUserRepository(...), UserRepository)` evaluates to `True` (which works with `@runtime_checkable` Protocol but fails with ABC unless explicitly subclassed). This would sharply distinguish Protocol from ABC.
