"""Domain models for the user repository layer."""

import logging
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator

logger = logging.getLogger(__name__)


class User(BaseModel):
    """Immutable domain model representing a stored user record."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: UUID
    email: str
    full_name: str
    roles: list[str] | None = None

    @field_validator("email")
    @classmethod
    def _validate_email(cls, value: str) -> str:
        """Reject obviously invalid email strings at model construction time."""
        if "@" not in value:
            raise ValueError(f"Invalid email address: {value!r}")
        return value.lower()


class UserNotFoundError(KeyError):
    """Raised when a requested user does not exist in the repository."""

    def __init__(self, user_id: UUID) -> None:
        super().__init__(str(user_id))
        self.user_id: UUID = user_id

    def __str__(self) -> str:
        return f"No user found with id={self.user_id}"


class DuplicateUserError(ValueError):
    """Raised when saving a user whose email is already owned by a different user."""

    def __init__(self, field: str, value: str) -> None:
        super().__init__(f"A user with {field}={value!r} already exists.")
        self.field: str = field
        self.value: str = value
