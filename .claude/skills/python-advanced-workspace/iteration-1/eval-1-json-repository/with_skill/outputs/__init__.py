"""User repository layer — public surface.

Import from here to stay decoupled from internal module layout:

    from outputs import User, UserRepository, JsonUserRepository
    from outputs import UserNotFoundError, DuplicateUserError
"""

from .json_repository import JsonUserRepository
from .models import DuplicateUserError, User, UserNotFoundError
from .repository import UserRepository

__all__ = [
    "User",
    "UserNotFoundError",
    "DuplicateUserError",
    "UserRepository",
    "JsonUserRepository",
]
