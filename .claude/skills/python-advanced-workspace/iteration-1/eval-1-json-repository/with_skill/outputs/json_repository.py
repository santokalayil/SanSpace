"""JSON-file-backed implementation of :class:`UserRepository`.

Storage layout (``users.json``):

.. code-block:: json

    {
      "users": {
        "<uuid-string>": {
          "id": "<uuid-string>",
          "email": "alice@example.com",
          "full_name": "Alice Smith",
          "roles": ["admin"]
        }
      }
    }

Writes are atomic: data is written to a sibling ``.tmp`` file and then
renamed over the destination, preventing half-written files on crash.
"""

import json
import logging
from pathlib import Path
from uuid import UUID

from pydantic import ValidationError

from .models import DuplicateUserError, User, UserNotFoundError

logger = logging.getLogger(__name__)

# ── Python 3.12 type aliases (PEP 695) ──────────────────────────────────────
type _RawRecord = dict[str, object]
type _UsersTable = dict[str, _RawRecord]   # keyed by UUID string
type _Store = dict[str, _UsersTable]        # top-level file structure


# ── Private I/O helpers ──────────────────────────────────────────────────────


def _load_store(file_path: Path) -> _Store:
    """Read and parse the JSON store from *file_path*.

    Returns an empty store structure when the file does not yet exist.

    Raises:
        ValueError: if the file exists but contains malformed JSON or an
            unexpected top-level structure.
    """
    if not file_path.exists():
        logger.debug("Store file absent, returning empty store: %s", file_path)
        return {"users": {}}

    raw = file_path.read_text(encoding="utf-8")

    try:
        data: object = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Malformed JSON in store file {file_path}: {exc}"
        ) from exc

    if not isinstance(data, dict) or "users" not in data:
        raise ValueError(
            f"Store file {file_path} must contain a top-level 'users' object."
        )

    return data  # type: ignore[return-value]


def _save_store(file_path: Path, store: _Store) -> None:
    """Atomically write *store* to *file_path* as indented JSON.

    Creates parent directories as needed.  Uses a sibling ``.tmp`` file
    and an atomic ``rename`` to avoid partially-written data on crash.
    """
    file_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = file_path.with_suffix(".tmp")

    try:
        tmp_path.write_text(
            json.dumps(store, indent=2, default=str),
            encoding="utf-8",
        )
        tmp_path.replace(file_path)
    except Exception:
        tmp_path.unlink(missing_ok=True)
        raise

    logger.debug("Store persisted to %s", file_path)


# ── Serialisation helpers ────────────────────────────────────────────────────


def _serialise(user: User) -> _RawRecord:
    """Convert a :class:`User` to a JSON-compatible plain dict."""
    return user.model_dump(mode="json")


def _deserialise(record: _RawRecord) -> User:
    """Reconstruct a :class:`User` from a raw dict.

    Raises:
        pydantic.ValidationError: if the record fails schema validation.
    """
    return User.model_validate(record)


# ── Repository implementation ────────────────────────────────────────────────


class JsonUserRepository:
    """File-backed implementation of the :class:`UserRepository` protocol.

    Parameters
    ----------
    file_path:
        Path to the JSON data file.  The file and any parent directories are
        created automatically on the first write.

    Example
    -------
    .. code-block:: python

        from pathlib import Path
        from outputs import JsonUserRepository, User
        import uuid

        repo = JsonUserRepository(Path("data/users.json"))
        user = User(id=uuid.uuid4(), email="alice@example.com", full_name="Alice")
        repo.save(user)
        fetched = repo.get_by_id(user.id)
    """

    def __init__(self, file_path: Path) -> None:
        self._file_path: Path = file_path
        logger.info(
            "JsonUserRepository initialised with store at %s", file_path
        )

    # ── Read operations ──────────────────────────────────────────────────────

    def get_by_id(self, user_id: UUID) -> User:
        """Return the user matching *user_id*.

        Raises:
            UserNotFoundError: if no such user is stored.
        """
        store = _load_store(self._file_path)
        users = store["users"]
        key = str(user_id)

        if key not in users:
            raise UserNotFoundError(user_id)

        logger.debug("get_by_id hit: id=%s", user_id)
        return _deserialise(users[key])

    def get_by_email(self, email: str) -> User:
        """Return the user whose email matches *email* (case-insensitive).

        Raises:
            UserNotFoundError: if no matching user is found.
        """
        normalised = email.lower()
        store = _load_store(self._file_path)

        for record in store["users"].values():
            if record.get("email") == normalised:
                logger.debug("get_by_email hit: email=%s", normalised)
                return _deserialise(record)

        # No match found — synthesise a sentinel UUID purely for the error.
        raise UserNotFoundError(_sentinel_uuid_for_email(normalised))

    def list_all(self) -> list[User]:
        """Return every stored user (unordered)."""
        store = _load_store(self._file_path)
        users = [_deserialise(rec) for rec in store["users"].values()]
        logger.debug("list_all: %d user(s) returned", len(users))
        return users

    def exists(self, user_id: UUID) -> bool:
        """Return ``True`` if a user with *user_id* is present."""
        store = _load_store(self._file_path)
        return str(user_id) in store["users"]

    # ── Write operations ─────────────────────────────────────────────────────

    def save(self, user: User) -> None:
        """Persist *user*, inserting or replacing the record by ``user.id``.

        Raises:
            DuplicateUserError: if a *different* user already owns ``user.email``.
        """
        store = _load_store(self._file_path)
        users = store["users"]
        key = str(user.id)

        _assert_email_unowned(users, user)

        users[key] = _serialise(user)
        _save_store(self._file_path, store)
        logger.info("save: upserted user id=%s email=%s", user.id, user.email)

    def delete(self, user_id: UUID) -> None:
        """Remove the user identified by *user_id*.

        Raises:
            UserNotFoundError: if no such user exists.
        """
        store = _load_store(self._file_path)
        users = store["users"]
        key = str(user_id)

        if key not in users:
            raise UserNotFoundError(user_id)

        del users[key]
        _save_store(self._file_path, store)
        logger.info("delete: removed user id=%s", user_id)


# ── Module-level guard helpers (keep methods < 30 lines) ────────────────────


def _assert_email_unowned(users: _UsersTable, incoming: User) -> None:
    """Raise :class:`DuplicateUserError` if *incoming.email* is already taken
    by a *different* user.

    Owning the email yourself (same id) is allowed (update path).
    """
    for existing_key, record in users.items():
        if record.get("email") == incoming.email and existing_key != str(incoming.id):
            raise DuplicateUserError("email", incoming.email)


def _sentinel_uuid_for_email(email: str) -> UUID:
    """Return a deterministic UUID derived from *email* for error context.

    Uses UUID5 (namespace + name) so the value is reproducible and carries
    the email's identity without storing anything.
    """
    import uuid

    return uuid.uuid5(uuid.NAMESPACE_URL, f"mailto:{email}")
