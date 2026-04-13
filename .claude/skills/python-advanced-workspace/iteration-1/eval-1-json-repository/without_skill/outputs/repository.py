from abc import ABC, abstractmethod
from uuid import UUID

from models import User


class UserRepository(ABC):
    """Abstract interface for User persistence.

    Swap implementations (JSON, Postgres, in-memory) without touching callers.
    Every method is synchronous; add an AsyncUserRepository sibling if needed.
    """

    @abstractmethod
    def get(self, user_id: UUID) -> User | None:
        """Return the User with the given id, or None if not found."""

    @abstractmethod
    def list_all(self) -> list[User]:
        """Return all stored users."""

    @abstractmethod
    def save(self, user: User) -> User:
        """Insert or update a user (upsert by id). Returns the saved user."""

    @abstractmethod
    def delete(self, user_id: UUID) -> bool:
        """Delete the user. Returns True if it existed, False otherwise."""
