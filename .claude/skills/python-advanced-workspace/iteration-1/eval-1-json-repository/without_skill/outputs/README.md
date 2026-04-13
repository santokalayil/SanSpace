# User JSON Repository

A minimal, swappable persistence layer for `User` records backed by a local JSON file.

## Files

| File | Purpose |
|---|---|
| `models.py` | `User` dataclass (id, email, full_name, roles) |
| `repository.py` | `UserRepository` abstract base class — the stable contract callers depend on |
| `json_repository.py` | `JsonUserRepository` — concrete implementation that reads/writes a JSON file |

## Quick start

```python
from pathlib import Path
from models import User
from json_repository import JsonUserRepository

repo = JsonUserRepository(Path("users.json"))

alice = User.create(email="alice@example.com", full_name="Alice Smith", roles=["admin"])
repo.save(alice)

found = repo.get(alice.id)   # User | None
all_users = repo.list_all()  # list[User]
repo.delete(alice.id)        # True
```

## Swapping backends

Callers only depend on `UserRepository`. To add a Postgres backend:

```python
class PostgresUserRepository(UserRepository):
    def get(self, user_id: UUID) -> User | None: ...
    def list_all(self) -> list[User]: ...
    def save(self, user: User) -> User: ...
    def delete(self, user_id: UUID) -> bool: ...
```

Pass the new implementation wherever `UserRepository` is expected — no caller changes required.

## Notes

- `save()` is an **upsert** (insert or update by `id`).
- The JSON file is created automatically if it does not exist.
- `JsonUserRepository` is **not thread-safe**. Add a `threading.Lock` around `_load`/`_flush` if concurrent writes are needed.
- Requires Python 3.12+.
