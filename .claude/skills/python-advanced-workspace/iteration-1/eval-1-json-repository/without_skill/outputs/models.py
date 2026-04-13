from dataclasses import dataclass, field
from uuid import UUID, uuid4


@dataclass
class User:
    id: UUID
    email: str
    full_name: str
    roles: list[str] = field(default_factory=list)

    @staticmethod
    def create(
        email: str,
        full_name: str,
        roles: list[str] | None = None,
    ) -> "User":
        """Factory that generates a new UUID for the caller."""
        return User(id=uuid4(), email=email, full_name=full_name, roles=roles or [])
