"""Smoke tests for the user repository layer."""

import sys
import tempfile
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from outputs import (
    DuplicateUserError,
    JsonUserRepository,
    User,
    UserNotFoundError,
    UserRepository,
)


def make_repo() -> JsonUserRepository:
    tmp = Path(tempfile.mkdtemp()) / "users.json"
    return JsonUserRepository(tmp)


def test_save_and_get_by_id() -> None:
    repo = make_repo()
    u = User(id=uuid.uuid4(), email="Alice@Example.com", full_name="Alice Smith", roles=["admin"])
    repo.save(u)
    fetched = repo.get_by_id(u.id)
    assert fetched.email == "alice@example.com", "email should be normalised to lowercase"
    assert fetched.full_name == "Alice Smith"
    assert fetched.roles == ["admin"]
    print("PASS: save + get_by_id + email normalisation")


def test_list_all() -> None:
    repo = make_repo()
    u1 = User(id=uuid.uuid4(), email="a@x.com", full_name="A")
    u2 = User(id=uuid.uuid4(), email="b@x.com", full_name="B")
    repo.save(u1)
    repo.save(u2)
    assert len(repo.list_all()) == 2
    print("PASS: list_all count == 2")


def test_get_by_email_case_insensitive() -> None:
    repo = make_repo()
    u = User(id=uuid.uuid4(), email="bob@example.com", full_name="Bob Jones")
    repo.save(u)
    found = repo.get_by_email("BOB@EXAMPLE.COM")
    assert found.full_name == "Bob Jones"
    print("PASS: get_by_email case-insensitive")


def test_exists() -> None:
    repo = make_repo()
    u = User(id=uuid.uuid4(), email="c@x.com", full_name="C")
    repo.save(u)
    assert repo.exists(u.id) is True
    assert repo.exists(uuid.uuid4()) is False
    print("PASS: exists")


def test_get_by_id_not_found() -> None:
    repo = make_repo()
    try:
        repo.get_by_id(uuid.uuid4())
        raise AssertionError("should have raised UserNotFoundError")
    except UserNotFoundError as exc:
        print(f"PASS: UserNotFoundError raised correctly: {exc}")


def test_duplicate_email_raises() -> None:
    repo = make_repo()
    u1 = User(id=uuid.uuid4(), email="shared@x.com", full_name="First")
    u2 = User(id=uuid.uuid4(), email="shared@x.com", full_name="Impostor")
    repo.save(u1)
    try:
        repo.save(u2)
        raise AssertionError("should have raised DuplicateUserError")
    except DuplicateUserError as exc:
        print(f"PASS: DuplicateUserError on duplicate email: {exc}")


def test_update_same_user_allowed() -> None:
    repo = make_repo()
    u = User(id=uuid.uuid4(), email="d@x.com", full_name="Original")
    repo.save(u)
    updated = u.model_copy(update={"full_name": "Updated"})
    repo.save(updated)
    assert repo.get_by_id(u.id).full_name == "Updated"
    print("PASS: update same user (upsert by id)")


def test_delete() -> None:
    repo = make_repo()
    u = User(id=uuid.uuid4(), email="e@x.com", full_name="E")
    repo.save(u)
    repo.delete(u.id)
    assert not repo.exists(u.id)
    print("PASS: delete")


def test_delete_not_found_raises() -> None:
    repo = make_repo()
    try:
        repo.delete(uuid.uuid4())
        raise AssertionError("should have raised UserNotFoundError")
    except UserNotFoundError as exc:
        print(f"PASS: UserNotFoundError on delete missing: {exc}")


def test_extra_forbid() -> None:
    try:
        User(id=uuid.uuid4(), email="f@x.com", full_name="F", unknown_field="bad")  # type: ignore[call-arg]
        raise AssertionError("should have raised")
    except Exception as exc:
        print(f"PASS: extra=forbid rejects unknown fields: {type(exc).__name__}")


def test_frozen() -> None:
    u = User(id=uuid.uuid4(), email="g@x.com", full_name="G")
    try:
        u.email = "mutation@bad.com"  # type: ignore[misc]
        raise AssertionError("should have raised")
    except Exception as exc:
        print(f"PASS: frozen=True prevents mutation: {type(exc).__name__}")


def test_protocol_structural_check() -> None:
    repo: JsonUserRepository = make_repo()
    assert isinstance(repo, UserRepository), "JsonUserRepository must satisfy UserRepository Protocol"
    print("PASS: isinstance check against UserRepository Protocol")


def test_no_roles_defaults_to_none() -> None:
    u = User(id=uuid.uuid4(), email="h@x.com", full_name="H")
    assert u.roles is None
    print("PASS: roles defaults to None")


if __name__ == "__main__":
    test_save_and_get_by_id()
    test_list_all()
    test_get_by_email_case_insensitive()
    test_exists()
    test_get_by_id_not_found()
    test_duplicate_email_raises()
    test_update_same_user_allowed()
    test_delete()
    test_delete_not_found_raises()
    test_extra_forbid()
    test_frozen()
    test_protocol_structural_check()
    test_no_roles_defaults_to_none()
    print("\nAll checks passed.")
