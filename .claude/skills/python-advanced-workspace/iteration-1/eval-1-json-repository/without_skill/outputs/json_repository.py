import json
from pathlib import Path
from uuid import UUID

from models import User
from repository import UserRepository


class JsonUserRepository(UserRepository):
    """Stores users as a JSON array in a local file.

    The file is read and written on every operation — intentionally simple.
    For high-frequency workloads consider an in-memory cache or switch to
    a proper database backend while keeping callers unchanged.

    Not thread-safe. If concurrent writes are needed, add a threading.Lock
    around _load / _flush or use a process-safe lock file.
    """

    def __init__(self, path: Path | str) -> None:
        self._path = Path(path)
        if not self._path.exists():
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._path.write_text("[]", encoding="utf-8")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load(self) -> dict[str, dict]:
        """Read the file and return a id-keyed dict for O(1) lookups."""
        raw: list[dict] = json.loads(self._path.read_text(encoding="utf-8"))
        return {record["id"]: record for record in raw}

    def _flush(self, records: dict[str, dict]) -> None:
        """Write the records back to disk as a pretty-printed JSON array."""
        self._path.write_text(
            json.dumps(list(records.values()), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    @staticmethod
    def _to_user(record: dict) -> User:
        return User(
            id=UUID(record["id"]),
            email=record["email"],
            full_name=record["full_name"],
            roles=record.get("roles", []),
        )

    @staticmethod
    def _from_user(user: User) -> dict:
        return {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "roles": user.roles,
        }

    # ------------------------------------------------------------------
    # UserRepository interface
    # ------------------------------------------------------------------

    def get(self, user_id: UUID) -> User | None:
        record = self._load().get(str(user_id))
        return self._to_user(record) if record is not None else None

    def list_all(self) -> list[User]:
        return [self._to_user(r) for r in self._load().values()]

    def save(self, user: User) -> User:
        records = self._load()
        records[str(user.id)] = self._from_user(user)
        self._flush(records)
        return user

    def delete(self, user_id: UUID) -> bool:
        records = self._load()
        key = str(user_id)
        if key not in records:
            return False
        del records[key]
        self._flush(records)
        return True
