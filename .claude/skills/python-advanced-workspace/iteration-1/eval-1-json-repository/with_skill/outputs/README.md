# User Repository Layer

A clean, swappable repository layer for persisting `User` records. The JSON backend can be replaced with Postgres (or any other store) without changing any call sites.

---

## Module structure

```
outputs/
├── __init__.py          # Public re-exports — import from here
├── models.py            # User (Pydantic v2) + UserNotFoundError / DuplicateUserError
├── repository.py        # UserRepository Protocol (the caller-facing contract)
└── json_repository.py   # JsonUserRepository (file-backed implementation)
```

### `models.py`

- **`User`** — immutable Pydantic v2 `BaseModel` (`frozen=True`, `extra="forbid"`).  
  Fields: `id: UUID`, `email: str`, `full_name: str`, `roles: list[str] | None`.  
  Email is normalised to lowercase on construction; missing `@` raises `ValidationError`.

- **`UserNotFoundError(KeyError)`** — raised when a lookup finds no matching record.
- **`DuplicateUserError(ValueError)`** — raised when `save()` detects an email collision with a different user.

### `repository.py`

- **`UserRepository`** — a `@runtime_checkable` `Protocol` that defines the full CRUD surface.  
  Callers type-annotate against this; no import from `json_repository` is needed.  
  Swapping backends is purely a composition-root concern.

### `json_repository.py`

- **`JsonUserRepository`** — satisfies `UserRepository` structurally (no inheritance).  
  Storage: a single JSON file with the shape `{"users": {"<uuid>": {...}}}`.  
  Writes are atomic via a sibling `.tmp` file + `rename`.  
  Private helpers `_load_store`, `_save_store`, `_serialise`, `_deserialise`, and `_assert_email_unowned` keep every public method under 30 lines.

---

## Python 3.12 features used

| Feature | Where |
|---|---|
| `type X = ...` (PEP 695 type alias) | `_RawRecord`, `_UsersTable`, `_Store` in `json_repository.py` |
| `X \| Y` union syntax (native) | `roles: list[str] \| None` in `User` |
| Built-in generics (`list[str]`, `dict[str, ...]`) | throughout — no `List`/`Dict` from `typing` |

---

## Quick start

```python
import uuid
from pathlib import Path
from outputs import JsonUserRepository, User, UserNotFoundError

repo = JsonUserRepository(Path("data/users.json"))

alice = User(
    id=uuid.uuid4(),
    email="alice@example.com",
    full_name="Alice Smith",
    roles=["admin", "editor"],
)
repo.save(alice)

fetched = repo.get_by_id(alice.id)
print(fetched.full_name)          # "Alice Smith"

all_users: list[User] = repo.list_all()

try:
    repo.get_by_id(uuid.uuid4())  # unknown id
except UserNotFoundError as exc:
    print(exc)                    # "No user found with id=<uuid>"
```

---

## Swapping to a Postgres backend

1. Create `pg_repository.py` with a `PgUserRepository` class that implements the same six methods.
2. Change the composition root (e.g. `main.py` or a DI container) to inject `PgUserRepository` instead of `JsonUserRepository`.
3. All call sites that type-annotate with `UserRepository` require **zero changes**.

---

## Design decisions

- **Protocol over ABC** — callers control the shape; structural typing avoids forced inheritance on concrete backends.
- **Fail-fast** — missing users raise immediately with a specific exception; no silent `None` returns or `.get()` defaults.
- **Atomic writes** — the `.tmp` + `rename` pattern prevents a crash mid-write from corrupting the store.
- **`frozen=True`** on `User` — records are value objects; mutations go through `model_copy(update={...})` + `repo.save()`.
- **No concurrency locking** — the JSON backend is single-process; a production Postgres backend would use transactions instead.
