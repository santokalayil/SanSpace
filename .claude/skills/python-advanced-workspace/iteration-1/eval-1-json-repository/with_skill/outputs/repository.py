"""Abstract repository contract for User persistence.

Callers depend *only* on this Protocol.  Swapping the JSON backend for
Postgres (or any other store) requires no changes outside this module and
the application's composition root.
"""

from typing import Protocol, runtime_checkable
from uuid import UUID

from .models import DuplicateUserError, User, UserNotFoundError

__all__ = ["UserRepository"]


@runtime_checkable
class UserRepository(Protocol):
    """Structural contract for all User storage backends.

    Any class that implements these methods satisfies the protocol via
    structural subtyping — no explicit inheritance required.

    Exceptions listed in each docstring are part of the contract; callers
    may rely on them regardless of which backend is in use.
    """

    def get_by_id(self, user_id: UUID) -> User:
        """Return the :class:`User` identified by *user_id*.

        Raises:
            UserNotFoundError: if no user with that id exists.
        """
        ...

    def get_by_email(self, email: str) -> User:
        """Return the :class:`User` whose email matches *email*.

        Comparison is case-insensitive.

        Raises:
            UserNotFoundError: if no matching user is found.
        """
        ...

    def list_all(self) -> list[User]:
        """Return every :class:`User` in this repository (unordered)."""
        ...

    def save(self, user: User) -> None:
        """Persist *user*, inserting or replacing the record by ``user.id``.

        Raises:
            DuplicateUserError: if a *different* user already owns ``user.email``.
        """
        ...

    def delete(self, user_id: UUID) -> None:
        """Remove the user identified by *user_id*.

        Raises:
            UserNotFoundError: if no such user exists.
        """
        ...

    def exists(self, user_id: UUID) -> bool:
        """Return ``True`` if a user with *user_id* is present."""
        ...


# Silence "imported but unused" linters — these are re-exported as part of
# the public interface so callers need not import from models directly.
_ = (DuplicateUserError, UserNotFoundError)
