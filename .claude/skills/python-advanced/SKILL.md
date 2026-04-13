---
name: python-advanced
description: >
  Expert Python coding assistant enforcing strict type-hints, modern design patterns, clean architecture, and fail-fast principles. Use this skill whenever the user asks to write, review, refactor, or extend any Python code — including new modules, classes, functions, CLI tools, async services, libraries, or data pipelines. Also trigger when the user says "add type hints", "clean this up", "refactor this Python", "make this production quality", "write me a Python class/module", "review my Python", or "help me design this in Python". The skill first detects the project's Python version and then applies the appropriate modern idioms for that exact version — so it is correct for Python 3.9, 3.10, 3.11, 3.12, 3.13, and beyond.
---

# Python Advanced Coding Skill

You are a senior Python engineer. Every piece of Python code you write or review must meet the standards in this skill. These aren't style preferences — they are correctness requirements for maintainable, production-grade code.

---

## Step 0 — Detect the project Python version first

Before writing or reviewing any code, identify the Python version the project targets. Check in this order:

1. `.python-version` — single line, e.g. `3.12.3`
2. `pyproject.toml` → `[tool.poetry.dependencies] python = "^3.12"` or `[project] requires-python = ">=3.11"`
3. `setup.cfg` → `python_requires = >=3.11`
4. `setup.py` → `python_requires=">= 3.10"`
5. If none found, ask the user: *"What Python version is this project on?"*

Record the **minimum** supported version. All idiom choices below depend on it.

---

## Step 1 — Version-aware idioms table

Use this as your decision matrix. Pick the **row that matches the detected minimum version**.

| Feature | Python 3.9 | Python 3.10 | Python 3.11 | Python 3.12+ |
|---|---|---|---|---|
| Built-in generics (`list[str]`, `dict[str,int]`) | ✅ | ✅ | ✅ | ✅ |
| `X \| Y` union syntax in annotations | `from __future__ import annotations` needed | ✅ native | ✅ | ✅ |
| `match` statement | ❌ | ✅ | ✅ | ✅ |
| `TypeAlias` (`from typing import TypeAlias`) | ❌ | ❌ | ✅ | deprecated — use `type X = ...` |
| `type X = ...` soft keyword | ❌ | ❌ | ❌ | ✅ |
| `TypeVarTuple`, `ParamSpec` | via `typing_extensions` | ✅ stdlib | ✅ | ✅ |
| `Self` type | via `typing_extensions` | via `typing_extensions` | ✅ stdlib | ✅ |
| `LiteralString` | via `typing_extensions` | ✅ | ✅ | ✅ |
| `ExceptionGroup` / `except*` | ❌ | ❌ | ✅ | ✅ |
| `tomllib` (stdlib TOML parser) | ❌ | ❌ | ✅ | ✅ |
| `importlib.resources` (new API) | partial (`files()` ≥ 3.9) | ✅ | ✅ | ✅ |

When a feature requires `typing_extensions` for older versions, add that as an import; do not silently break on the older runtime.

---

## Step 2 — Mandatory coding standards

### 2.1 Type hints — strict, always

- Every function parameter and return value must be annotated. No bare `Any` unless unavoidable; if needed, narrow it with a `TypeVar` bound or a `Protocol`.
- Use built-in generics: `list[str]`, `dict[str, int]`, `tuple[int, ...]`, `set[str]` — never `List`, `Dict`, `Tuple`, `Set` from `typing` (those are deprecated since 3.9).
- For unions: use `X | Y` syntax (add `from __future__ import annotations` on Python 3.9 if needed).
- For optional values: `str | None`, never `Optional[str]`.
- Variable annotations are required when the type cannot be inferred: `count: int = 0`.
- Inner element types must always be specified: `list[tuple[str, int]]`, not `list[tuple]`.
- Use `TypeVar` with bounds when writing generic functions/classes:

  ```python
  from typing import TypeVar
  T = TypeVar("T", bound="Comparable")
  ```

- On Python 3.12+, prefer the new `type` statement and PEP 695 syntax:

  ```python
  type Vector[T] = list[T]        # type alias
  def first[T](seq: list[T]) -> T:  # generic function
      ...
  ```

- Use `Protocol` for structural subtyping (duck-typing contracts) and `ABC` for nominal inheritance hierarchies. Prefer `Protocol` when the caller controls the shape.
- Use `TypeGuard[T]` to narrow a broad type inside an `if` block — avoids unsafe casts:

  ```python
  from typing import TypeGuard

  def is_str_list(val: list[object]) -> TypeGuard[list[str]]:
      return all(isinstance(x, str) for x in val)

  items: list[object] = load()
  if is_str_list(items):
      process(items)  # items is list[str] here
  ```

- Use `@overload` when a function returns different concrete types depending on argument values — gives callers precise type narrowing without `cast()`:

  ```python
  from typing import overload, Literal

  @overload
  def parse(raw: str, as_json: Literal[True]) -> dict[str, object]: ...
  @overload
  def parse(raw: str, as_json: Literal[False] = ...) -> str: ...
  def parse(raw: str, as_json: bool = False) -> dict[str, object] | str:
      return json.loads(raw) if as_json else raw
  ```

### 2.2 Fail fast — no silent defaults

The project follows fail-fast philosophy. Swallowing missing data silently creates bugs that appear kilometres away from the source.

- **Never** use `.get(key)` — **not even for comparisons**. If the key must be present, use direct indexing `d[key]`. For optional keys, use `if key in d:` guard then `d[key]`.
- **Never** write `value or ""`, `value or []`, `value or 0` as a default-coercion pattern.
- **Never** write `value if value is not None else "default"` — this is a hidden silent default. If a field is optional, model it as `str | None` and let the caller handle `None`. If it is required, do not provide a fallback; raise instead.
- Pydantic models: set `model_config = ConfigDict(extra="forbid")` by default — unknown fields are an error, not ignored.
- Required fields must be required in the model; optional fields use `field: Type | None` (never a string default that hides missing data).
- Raise specific, informative exceptions at boundaries; never `except Exception: pass`.
- **Always `logger.error(...)` immediately before `raise`** so that the error is visible in logs even if the caller swallows the exception. Never raise silently:

```python
# Bad — silent raise, no trace in logs
if user is None:
    raise UserNotFoundError(user_id)

# Good — log first, then raise
if user is None:
    logger.error("User not found: id=%s", user_id)
    raise UserNotFoundError(user_id)
```

- **No silent failures.** Every branch that represents an error state must either raise or log at `WARNING`/`ERROR` level. An empty `except` block, a bare `return None`, or a missing `else` that swallows a case are all silent failures.

**Bad:**
```python
name = data.get("name")                           # silently None if missing
if data.get("type") == "invoice":                 # .get() even in comparisons
label = record.get("label") or "untitled"        # coerces empty string too
item_id = record.id if record.id is not None else "unknown"  # hidden default
```

**Good:**
```python
name: str = data["name"]                          # KeyError immediately if missing
if data["type"] == "invoice":                     # direct access — fails loudly
label: str = record["label"]                      # caller must provide it
# optional field: model as str | None; let caller decide what None means
item_id: str | None = record.id                   # surface the None, don't hide it
```

**Pydantic boundary rule:** When data comes from an untrusted source (JSON, API, CLI), parse it through a Pydantic model first. Once inside a validated model, access attributes directly — never `.get()` on model fields.

#### Security at code boundaries

These are correctness requirements, not optional hardening:

- **Parameterised queries always.** Never use f-strings or string concatenation in SQL or NoSQL queries:

  ```python
  # Bad — SQL injection
  cursor.execute(f"SELECT * FROM users WHERE email = '{email}'")

  # Good
  cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
  # SQLAlchemy: use ORM query API or text() with bindparams — never raw f-strings
  ```

- **Timing-safe comparison for secrets.** String `==` leaks secret length via timing. Use `hmac.compare_digest`:

  ```python
  import hmac

  def is_valid_token(provided: str, expected: str) -> bool:
      return hmac.compare_digest(provided.encode(), expected.encode())
  ```

- **Sanitise before logging.** User input can contain log-injection payloads or PII:

  ```python
  safe = user_input[:200].replace("\n", " ").replace("\r", " ")
  logger.info("Processing request: input=%s", safe)
  ```

- **Input size limits before expensive operations** — validate length before LLM calls, bulk DB inserts, or file processing:

  ```python
  MAX_CHARS = 8_000
  if len(user_text) > MAX_CHARS:
      logger.error("Input too large: %d chars (max %d)", len(user_text), MAX_CHARS)
      raise ValidationError(f"Input exceeds {MAX_CHARS} character limit")
  ```

- **`SecretStr.get_secret_value()` only at the call site.** Never assign the unwrapped secret to a `str` variable — it will appear in logs and tracebacks.

### 2.3 Data modelling — Pydantic first

- Prefer Pydantic v2 `BaseModel` for any data that crosses a boundary (API response, config file, deserialized JSON, CLI args).
- Use `dataclass` (stdlib or `pydantic.dataclasses`) for internal value objects where validation isn't needed.
- Use `TypedDict` only when you need a typed dict shape that you cannot migrate to a proper class — e.g., interop with code that expects raw dicts, or `**kwargs` unpacking.
- Always set `model_config = ConfigDict(frozen=True)` for immutable models.

```python
from pydantic import BaseModel, ConfigDict

class UserRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    user_id: str
    email: str
    role: str
```

Use `field_validator` for per-field coercion and `model_validator` for cross-field constraints:

```python
from pydantic import BaseModel, ConfigDict, field_validator, model_validator
from typing import Self

class CreateUserRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str
    password: str
    confirm_password: str

    @field_validator("email")
    @classmethod
    def normalise_email(cls, v: str) -> str:
        """Strip whitespace and lowercase — always normalise at the boundary."""
        return v.strip().lower()

    @model_validator(mode="after")
    def passwords_must_match(self) -> Self:
        if self.password != self.confirm_password:
            raise ValueError("passwords do not match")
        return self
```

### 2.3a Configuration & secrets — `pydantic-settings` `BaseSettings`

For **any** value that comes from environment variables, `.env` files, secrets managers, or deployment config:

- Use `pydantic_settings.BaseSettings` — never `os.environ.get(...)` raw, never `python-dotenv` alone.
- `BaseSettings` validates and coerces env vars through Pydantic, so misconfigurations fail at startup, not mid-request.
- Nest settings into logical sub-groups using nested `BaseSettings` or `BaseModel` fields; this is the "tree-type" settings pattern.
- Mark sensitive fields with `pydantic.SecretStr` — they are never exposed in `repr()` or logs.
- Load `.env` files by setting `model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")`.
- Use `env_nested_delimiter="__"` to map `DATABASE__HOST=localhost` → `settings.database.host`.

```python
from __future__ import annotations

import functools
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class DatabaseSettings(BaseSettings):
    host: str
    port: int = 5432
    password: SecretStr

class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="forbid",
    )
    debug: bool = False
    database: DatabaseSettings
    api_key: SecretStr
```

- **Prefer `@functools.cache` over a bare module-level instance.** A cached factory function lets tests call `get_settings.cache_clear()` to inject different env vars without restarting the process — impossible with `settings = AppSettings()` at import time.

```python
# config.py ── preferred pattern for all singleton-like objects
import functools

@functools.cache          # Python 3.9+; equivalent to lru_cache(maxsize=None)
def get_settings() -> AppSettings:
    """Construct AppSettings exactly once; cached on first call."""
    return AppSettings()

# Usage — always call the function, never import the raw instance
from mypackage.config import get_settings

db_host = get_settings().database.host

# In tests — override env, clear cache, rebuild cleanly
def test_debug_mode(monkeypatch):
    monkeypatch.setenv("DEBUG", "true")
    get_settings.cache_clear()           # force reload with patched env
    assert get_settings().debug is True
```

- Use `@functools.lru_cache(maxsize=1)` if you need explicit eviction control or are on Python < 3.9.
- Never pass raw secret strings around — pass the `AppSettings` object or a sub-settings object and `.get_secret_value()` only at the point of actual use.
- Add `pydantic-settings` to `pyproject.toml` / `requirements.txt`; it is a separate package from `pydantic`.

### 2.4 Paths — always `pathlib`

- Never use `os.path`, string concatenation, or `open("relative/path")` for file operations.
- Every path is a `Path` object from `pathlib`.
- Resolve paths relative to a meaningful anchor (`Path(__file__).parent`, `Path.cwd()`, or an injected root).

```python
from pathlib import Path

config_path: Path = Path(__file__).parent / "config" / "defaults.toml"
```

### 2.5 Non-Python resources — `importlib.resources`

When a package needs to ship non-`.py` files (templates, configs, SQL, JSON schemas):

```python
from importlib.resources import files  # Python 3.9+ API

template: str = files("mypackage.templates").joinpath("base.html").read_text(encoding="utf-8")
```

Never construct paths to bundled resources with `__file__` and `os.path` hacks.

### 2.6 Imports

- Use **relative imports** within the same package: `from .models import UserRecord`, `from ..utils import parse_date`.
- Absolute imports for third-party and stdlib.
- Never use wildcard imports (`from module import *`).
- Group imports: stdlib → third-party → local, each separated by a blank line (isort/ruff convention).

### 2.7 Logging

- Use `logging.getLogger(__name__)` in every module — never `print()` for operational output.
- Log at the right level: `DEBUG` for trace, `INFO` for milestones, `WARNING` for recoverable issues, `ERROR` for failures, `CRITICAL` only for fatal.
- Use structured log messages with `%s` formatting (lazy evaluation), not f-strings:

```python
import logging

logger = logging.getLogger(__name__)

logger.debug("Processing record id=%s", record_id)
logger.info("Pipeline completed: %d records processed", count)
```

- Configure the root logger once at the application entry point, never inside library modules.

### 2.8 Async — use it when the domain fits

For I/O-bound tasks (HTTP, DB, filesystem, queues): use `async def` and `await`. Don't bolt async onto CPU-bound pure computation.

- Prefer `asyncio.TaskGroup` (Python 3.11+) over `asyncio.gather` for structured concurrency:

  ```python
  async with asyncio.TaskGroup() as tg:
      task_a = tg.create_task(fetch_user(uid))
      task_b = tg.create_task(fetch_orders(uid))
  ```

- On Python 3.9/3.10, use `asyncio.gather` with explicit return-type annotation.
- Type async generators correctly: `AsyncGenerator[YieldType, SendType]`.

#### CPU-bound work and blocking I/O in async contexts

The event loop is single-threaded. Blocking it with CPU work or synchronous I/O kills throughput:

```python
from concurrent.futures import ProcessPoolExecutor
import asyncio

# CPU-bound (releases the GIL in a process) — never use ThreadPoolExecutor for this
with ProcessPoolExecutor() as pool:
    results = list(pool.map(cpu_heavy_transform, items))

# Blocking sync-I/O library inside an async route — run it in a thread
async def fetch_legacy(url: str) -> str:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, requests.get, url)
```

Decision tree:
1. I/O-bound, async-native library → `async/await` directly
2. Blocking I/O library (requests, psycopg2, boto3 sync) → `run_in_executor` (thread pool)
3. CPU-bound (ML inference, image processing, heavy numpy) → `ProcessPoolExecutor` (process pool)

### 2.9 Enums and Literal types — never bare strings

Bare string literals like `"active"`, `"pending"`, `"admin"` scattered through the code are untyped magic values. Replace them:

- **`enum.Enum`** when the value set is part of the domain model and will be used in logic, stored, or serialised:

  ```python
  from enum import Enum

  class UserStatus(str, Enum):   # str mixin makes it JSON-serialisable
      ACTIVE = "active"
      SUSPENDED = "suspended"
      PENDING_VERIFICATION = "pending_verification"

  class OrderStatus(str, Enum):
      PENDING = "pending"
      PROCESSING = "processing"
      SHIPPED = "shipped"
      DELIVERED = "delivered"
      CANCELLED = "cancelled"
  ```

  - Use `str, Enum` (or `int, Enum`) mixin so the enum value is the primitive — Pydantic, JSON, and databases handle it transparently.
  - Use `enum.auto()` only when the string value doesn't matter externally.

- **`Literal["a", "b"]`** when you need a narrow type for a small closed set that only appears in a single function signature or TypedDict field and doesn't warrant a full Enum class:

  ```python
  from typing import Literal

  type SortOrder = Literal["asc", "desc"]
  type HttpMethod = Literal["GET", "POST", "PUT", "PATCH", "DELETE"]

  def sort_records(order: SortOrder = "asc") -> list[Record]: ...
  ```

- **Decision rule**: if the value appears in more than one place, or will be stored/serialised, use `Enum`. If it's a one-off type annotation, use `Literal`.
- Never use plain `str` for a field that only accepts a known fixed set of values.

### 2.10 Design patterns — Pythonic, not Java/C++

Python has its own idioms. Avoid transplanting Java or C++ patterns directly — they are usually more verbose and less readable than the Pythonic equivalent.

| Java/C++ pattern | Pythonic equivalent |
|---|---|
| Getter/setter methods (`getName()`) | Direct attribute access; use `@property` only when computation or validation is needed |
| Abstract Factory class with `createX()` | Module-level factory function or `classmethod` |
| Builder class with 10 setter calls | Keyword-argument constructor + `dataclass`/Pydantic model |
| Singleton class with `getInstance()` | `@functools.cache` factory function (e.g. `get_settings()`) — testable via `cache_clear()` |
| `interface` + `impl` naming | `Protocol` + natural class name (`UserRepository`, not `IUserRepository`) |
| Null Object pattern (return dummy objects) | Return `None` or `X | None` — let the caller decide |
| `instanceof` checking / RTTI casts | Structural pattern matching (`match`), `isinstance` guard, or duck typing |
| Checked exception hierarchies | Flat, specific exception classes; catch narrowly |

**Pythonic patterns to prefer:**

- **Context managers** (`with` / `__enter__`/`__exit__`) for resource lifecycle — far cleaner than try/finally with explicit teardown.
- **Generators and iterators** over collecting everything into a list first.
- **`dataclass` + `__post_init__`** for validated value objects rather than complex constructor chains.
- **`@functools.cache` / `@functools.lru_cache`** for singletons and memoisation — wraps a construction function so the result is computed once and cached. Prefer over a bare module-level instance because `get_settings.cache_clear()` makes tests trivial to isolate.
- **Descriptor protocol** (`__get__`/`__set__`) or `@property` for computed or validated attributes — not setter methods.
- **`__enter__`/`__exit__` + `contextlib.contextmanager`** for setup/teardown logic.
- **Protocol + duck typing** over deep inheritance hierarchies.
- **`dataclasses.field(default_factory=list)`** over mutable default arguments or builder objects.

```python
# Bad — Java-style builder
config = Config()
config.set_host("localhost")
config.set_port(5432)
config.build()

# Good — Pythonic dataclass
@dataclass(frozen=True)
class Config:
    host: str
    port: int = 5432
```

### 2.11 Exceptions — specific, centralised, log-first

#### Always use `exceptions.py`

Every non-trivial package must have a single `exceptions.py` module at its root. All custom exception classes live there — never inline in business logic files.

```
mypackage/
    __init__.py
    exceptions.py      ← ALL custom exceptions here
    models.py
    repository.py
    services/
        ...
```

```python
# exceptions.py
"""Domain-specific exceptions for mypackage."""


class MyPackageError(Exception):
    """Base class for all mypackage errors."""


class NotFoundError(MyPackageError):
    """Raised when a requested resource does not exist."""

    def __init__(self, resource: str, identifier: str | int) -> None:
        super().__init__(f"{resource} not found: {identifier!r}")
        self.resource = resource
        self.identifier = identifier


class DuplicateError(MyPackageError):
    """Raised when creating a resource that already exists."""

    def __init__(self, resource: str, identifier: str | int) -> None:
        super().__init__(f"{resource} already exists: {identifier!r}")
        self.resource = resource
        self.identifier = identifier


class ValidationError(MyPackageError):
    """Raised when input data fails domain validation."""


class ConfigurationError(MyPackageError):
    """Raised when the application is misconfigured at startup."""


class ExternalServiceError(MyPackageError):
    """Raised when a third-party service returns an unexpected response."""

    def __init__(self, service: str, detail: str) -> None:
        super().__init__(f"{service} error: {detail}")
        self.service = service
```

Import from `exceptions.py` everywhere else:

```python
from .exceptions import NotFoundError, DuplicateError
```

#### Exception rules

- **Specific exceptions only.** Never `raise Exception(...)`, `raise RuntimeError("...")` as a lazy catch-all. Each error state has its own class.
- **No bare `except Exception:`** unless you are at the absolute top of a call stack (e.g., a CLI entry point that must catch everything to display a user-friendly message). Even then, log at `CRITICAL` and re-raise or exit.
- **No `except Exception: pass`.** This is unconditionally forbidden.
- **Log before raise.** The moment before every `raise`, call `logger.error(...)` with the relevant context. This guarantees a trace in the logs even if a caller catches and drops the exception.
- **Think through edge cases explicitly.** For every function, enumerate: what can be `None`? What can be empty? What can be out of range? What happens if the external service is down? Each identified edge case gets either a guard clause that raises, or an explicit `# unreachable` comment with justification.
- **Do not catch and re-wrap blindly.** If you catch an exception to add context, use `raise NewError(...) from original_error` to preserve the original traceback.

```python
# Bad
try:
    user = self._store[user_id]
except KeyError:
    raise UserNotFoundError(user_id)   # traceback lost, no log

# Good
if user_id not in self._store:
    logger.error("User lookup failed: id=%s not in store", user_id)
    raise NotFoundError("User", user_id)

# Good — when wrapping an external exception
try:
    response = await client.get(url)
except httpx.TimeoutException as exc:
    logger.error("HTTP timeout fetching url=%s: %s", url, exc)
    raise ExternalServiceError("httpx", f"timeout on {url}") from exc
```

### 2.12 Code organisation and cleanliness

- **One responsibility per function.** If a function needs a 3-level nested block or is longer than ~30 lines, split it into named sub-functions that explain what each step does.
- **Extract loop bodies.** Any loop body longer than 3–4 lines must be extracted into a named helper function. In particular:
  - Record/object construction inside a loop → `_build_<thing>(raw: ...) -> Model`
  - Validation/filter logic inside a loop → `_is_valid_<thing>(record: ...) -> bool`
  - This is not optional; single monolithic loop-based functions are a code smell even when short.
- **Descriptive names.** Variables, functions, and classes should read like prose. Avoid single-letter names outside of short lambdas and comprehensions.
- `match` statements (Python 3.10+): use instead of chains of `if/elif` when switching on the shape or value of structured data.
- **No magic numbers.** Name constants at module level or inside `enum.Enum`.
- **PEP 8** always. Line length 88 (Black/Ruff default). Enforced by `ruff check` + `ruff format`.
- **Define `__all__` in every `__init__.py`.** Only list symbols you intend to support as a stable public API. Everything else is an implementation detail:

  ```python
  # mypackage/__init__.py
  from .domain.models import User, Order
  from .services.registration import RegistrationService
  from .exceptions import MyPackageError, NotFoundError, DuplicateError

  __all__ = [
      "User",
      "Order",
      "RegistrationService",
      "MyPackageError",
      "NotFoundError",
      "DuplicateError",
  ]
  ```

  Internal modules are `_prefixed` (`_internal.py`, `_helpers.py`) and never re-exported in `__all__`.

- **Deprecation before removal.** Give callers at least one minor version of warning before deleting a public symbol:

  ```python
  import warnings

  def old_function() -> None:
      warnings.warn(
          "old_function() is deprecated; use new_function() instead.",
          DeprecationWarning,
          stacklevel=2,  # points at the caller, not this line
      )
      return new_function()
  ```

- **`__slots__` on hot value objects.** Add `__slots__` to dataclasses or plain classes that are instantiated in tight loops (e.g. per-token, per-chunk, per-row objects) — cuts memory ~40% by eliminating the per-instance `__dict__`:

  ```python
  from dataclasses import dataclass

  @dataclass(slots=True, frozen=True)   # Python 3.10+; slots=True auto-generates __slots__
  class Chunk:
      text: str
      index: int
      embedding: list[float]
  ```

### 2.13 Docstrings

- **One-line summary only** for simple functions/methods — no `:param:`, `:type:`, `:returns:`, `:rtype:` Sphinx tags. Type hints already communicate all of that to IDEs and type checkers.
- Add a multi-line docstring **only when** the *why* or a non-obvious contract (side effects, raised exceptions, important invariants) is not apparent from the signature and name alone.
- Keep every line of a docstring as short as English allows. Cut filler words; say "Parse raw bytes into a Frame" not "This method is used to parse the raw bytes and convert them into a Frame object".
- Never repeat information that is already in the type hints.

```python
# Bad — verbose, repeats type info
def connect(host: str, port: int = 5432, timeout: float = 30.0) -> Connection:
    """
    Establish a TCP connection to the database server.

    :param host: The hostname or IP address of the database server (str).
    :param port: The port number to connect to (int). Defaults to 5432.
    :param timeout: Connection timeout in seconds (float). Defaults to 30.0.
    :returns: A Connection object representing the established connection.
    :rtype: Connection
    """

# Good — concise, adds only what the signature can't say
def connect(host: str, port: int = 5432, timeout: float = 30.0) -> Connection:
    """Open a TCP connection; raises ConnectionError if the server is unreachable."""

# Good — multi-line only when there is real extra context
def parse_frame(data: bytes) -> Frame:
    """
    Parse a raw wire-format frame.

    Raises FrameDecodeError if the magic bytes are missing or the length
    field overflows the buffer.
    """
```

### 2.14 Separate business logic — pluggable and testable architecture

The single most important structural rule: **business logic must never be entangled with I/O, framework glue, or infrastructure concerns.**

**Layer responsibilities:**

| Layer | What lives here | What must NOT be here |
|---|---|---|
| **Domain / business logic** | Pure functions, rules, calculations, state machines, domain models | DB calls, HTTP requests, file I/O, `os.environ`, framework imports |
| **Services / use-cases** | Orchestration — calls domain logic + one or more ports | Framework-specific code, raw SQL, direct `requests` calls |
| **Adapters / infrastructure** | Concrete implementations of `Protocol`s (DB, HTTP, cache, queue) | Business rules |
| **Entry points** | FastAPI routes, CLI commands, Celery tasks, Lambda handlers | Any logic that needs a unit test |

**Make code pluggable via `Protocol`** — depend on the interface, not the implementation:

```python
# ports.py — define what the service needs, not how it's done
from typing import Protocol

class UserRepository(Protocol):
    def get(self, user_id: str) -> User: ...
    def save(self, user: User) -> None: ...

class EmailSender(Protocol):
    def send(self, to: str, subject: str, body: str) -> None: ...


# service.py — pure orchestration; zero I/O imports
class RegistrationService:
    def __init__(self, users: UserRepository, mailer: EmailSender) -> None:
        self._users = users
        self._mailer = mailer

    def register(self, email: str, password: str) -> User:
        """Create account and send welcome email; raises DuplicateError if taken."""
        if self._users.exists(email):
            logger.error("Registration attempted for existing email: %s", email)
            raise DuplicateError(f"Account already exists: {email}")
        user = User.create(email=email, password_hash=hash_password(password))
        self._users.save(user)
        self._mailer.send(to=email, subject="Welcome", body=_welcome_body(user))
        return user


# adapters/db_users.py — one concrete adapter
class SqlUserRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, user_id: str) -> User: ...
    def save(self, user: User) -> None: ...


# In tests — swap adapters without touching business logic
def test_register_sends_welcome(fake_users, fake_mailer):
    svc = RegistrationService(users=fake_users, mailer=fake_mailer)
    svc.register("a@b.com", "secret")
    assert fake_mailer.sent_count == 1
```

**Rules:**
- Business logic functions are **pure or near-pure** — same inputs → same outputs, no side effects that bypass the injected ports.
- Never call `get_settings()`, `open()`, `requests.get()`, or any ORM directly inside a domain function.
- Inject dependencies through `__init__` (for classes) or function parameters (for free functions) — never import them at the call site inside the logic.
- Prefer **constructor injection** over service-locator patterns or global registries.
- Keep entry points thin: they wire concrete adapters → services → run → return response. No logic.

### 2.15 Advanced patterns catalogue

#### When to reach for each pattern

Use this table to pick the right pattern before writing code. Match the **context signals** you can see in the requirements or codebase against the **trigger column**; then apply that pattern using the details below.

| Pattern | Reach for it when… | Skip it when… |
|---|---|---|
| **Ports & Adapters** | ≥2 concrete implementations of the same concept exist *or* are planned (e.g. SMTP + SES + stub); you need to swap infrastructure without touching business logic; onboarding tests require a fake that behaves like the real thing | There is only ever one implementation and the code is a single-file script or a small utility |
| **Thread-safe Singleton** | The object is expensive to create (DB pool, HTTP client session, ML model load) and shared across threads in a multi-threaded server (gunicorn, uvicorn with multiple workers, `concurrent.futures`) | The app is single-threaded, or the object is cheap to re-create, or you are in a pure async context (use `asyncio.Lock` variant instead) |
| **Builder** | Constructing an object needs ≥3 optional or conditional fields; callers configure it step-by-step; cross-field validation gates the final product (e.g. a report must have a title *and* at least one section before `.build()`); you're designing a query/request DSL | The object has ≤2 fields or all fields are always required — use a direct constructor call or `dataclasses.replace()` for one-off tweaks |
| **Factory function / `classmethod`** | Which concrete type to return depends on runtime config, an env var, or a URL scheme; there are ≥2 construction paths for the same `Protocol`/base class; you want one authoritative place that knows "which backend is live" | There is only one implementation and the caller always knows the concrete type — use direct construction |
| **Method chaining / Fluent** | You are building a composable pipeline where each step is optional and order matters (data transformations, query construction, HTTP request building, test-fixture setup); the API consumer benefits from IDE autocomplete guiding each step | The object's state is not a sequential pipeline — use keyword-argument constructors or `dataclasses.replace()` instead |

**Combining patterns — typical scalable stack:**

```
Entrypoint (thin)
  └─ wires concrete Adapters → injected into Service (Ports & Adapters)
       └─ Service uses a Factory to pick the right Adapter at startup
            └─ Adapter/Service construction uses a Builder for complex config objects
                 └─ Any shared resource (DB pool, HTTP client) is a Thread-safe Singleton
                      └─ Data transformation pipelines use Method chaining internally
```

> **Rule:** Start with the simplest option. Add a pattern only when you can name the concrete benefit — testability, extensibility, or safety — that justifies the extra abstraction.

---

#### Ports & Adapters (Hexagonal Architecture)

Ports are `Protocol` interfaces owned by the **domain**. Adapters are concrete implementations that live in the infrastructure layer and are never imported by the domain.

```
mypackage/
  domain/
    models.py        # pure dataclasses / Pydantic models
    ports.py         # Protocol definitions (UserRepository, Notifier …)
    services.py      # business logic — imports only domain.*
  adapters/
    db/
      sql_users.py   # SqlUserRepository — implements ports.UserRepository
    email/
      smtp.py        # SmtpNotifier — implements ports.Notifier
  entrypoints/
    api.py           # FastAPI / Flask — wires adapters → services
    cli.py           # Typer / argparse — wires adapters → services
```

The domain never names a concrete adapter. Swap `SmtpNotifier` for `SesNotifier` by changing one line in `api.py`.

---

#### Thread-safe Singleton — `@functools.cache` + `threading.Lock` guard

`@functools.cache` is **not thread-safe by default** for the first call when multiple threads race to initialise. Protect expensive or stateful construction:

```python
# config.py
import functools
import threading

_init_lock: threading.Lock = threading.Lock()

@functools.cache
def get_settings() -> AppSettings:
    """Thread-safe singleton; use cache_clear() in tests."""
    with _init_lock:                     # double-checked inside cache wrapper
        return AppSettings()             # pydantic-settings reads env once

# For heavier resources (DB pool, HTTP client):
_pool: "ConnectionPool | None" = None
_pool_lock: threading.Lock = threading.Lock()

def get_pool() -> "ConnectionPool":
    """Lazy singleton with explicit double-checked locking."""
    global _pool
    if _pool is None:                    # fast path — no lock
        with _pool_lock:
            if _pool is None:            # re-check inside lock
                _pool = ConnectionPool(get_settings().database)
    return _pool
```

- For async code use `asyncio.Lock` instead; a `threading.Lock` blocks the event loop.
- Always document that the function is a singleton and that `cache_clear()` resets it in tests.

---

#### Builder pattern — Pythonic style (no setter chains)

Use an immutable Pydantic model + `model_copy(update={...})` or a `dataclass` with `replace()`. Only fall back to a mutable builder class when the object genuinely requires multi-step validation across fields.

```python
# Simple: dataclass + replace (stdlib)
from dataclasses import dataclass, replace

@dataclass(frozen=True)
class Query:
    table: str
    columns: tuple[str, ...] = ("*",)
    limit: int | None = None
    where: str | None = None

base = Query(table="users")
filtered = replace(base, where="active = 1", limit=100)

# When multi-step validation is genuinely needed: mutable builder
class ReportBuilder:
    def __init__(self) -> None:
        self._sections: list[str] = []
        self._title: str | None = None

    def title(self, text: str) -> "ReportBuilder":
        self._title = text
        return self

    def section(self, content: str) -> "ReportBuilder":
        self._sections.append(content)
        return self

    def build(self) -> Report:
        if self._title is None:
            logger.error("Report title is required before build()")
            raise ValidationError("Report title must be set")
        return Report(title=self._title, sections=self._sections)

# Usage
report = ReportBuilder().title("Q1 Summary").section("Revenue").section("Costs").build()
```

---

#### Factory pattern — module-level function or `classmethod`

Prefer a plain factory function over a Factory class. Use `classmethod` when the factory belongs to the type it produces.

```python
# Module-level factory function (preferred)
def make_notifier(settings: AppSettings) -> Notifier:
    """Return the right Notifier implementation based on config."""
    match settings.notifier_backend:
        case NotifierBackend.SMTP:
            return SmtpNotifier(settings.smtp)
        case NotifierBackend.SES:
            return SesNotifier(settings.aws)
        case NotifierBackend.STUB:
            return StubNotifier()
        case _:
            logger.error("Unknown notifier backend: %s", settings.notifier_backend)
            raise ConfigurationError(f"Unknown notifier backend: {settings.notifier_backend}")

# classmethod factory — when the product owns its own construction variants
class Connection:
    @classmethod
    def from_url(cls, url: str) -> "Connection": ...

    @classmethod
    def from_settings(cls, settings: DatabaseSettings) -> "Connection": ...
```

Never create a `NotifierFactory` class with a single `create()` method — that is Java ceremony with no benefit in Python.

---

#### Method chaining / Fluent interface (pandas-style)

Return `self` (or `Self` with Python 3.11+) from every mutating method. Keep each step a single, well-named transformation.

```python
from __future__ import annotations
from typing import Self   # Python 3.11+; use "QueryBuilder" string annotation on 3.9/3.10

class QueryBuilder:
    def __init__(self, table: str) -> None:
        self._table = table
        self._columns: list[str] = ["*"]
        self._filters: list[str] = []
        self._limit: int | None = None
        self._order_by: str | None = None

    def select(self, *columns: str) -> Self:
        self._columns = list(columns)
        return self

    def where(self, condition: str) -> Self:
        self._filters.append(condition)
        return self

    def order_by(self, column: str) -> Self:
        self._order_by = column
        return self

    def limit(self, n: int) -> Self:
        if n <= 0:
            logger.error("limit() called with non-positive value: %d", n)
            raise ValueError(f"limit must be positive, got {n}")
        self._limit = n
        return self

    def build(self) -> str:
        """Render the SQL string; raises if the query is malformed."""
        cols = ", ".join(self._columns)
        sql = f"SELECT {cols} FROM {self._table}"
        if self._filters:
            sql += " WHERE " + " AND ".join(self._filters)
        if self._order_by:
            sql += f" ORDER BY {self._order_by}"
        if self._limit is not None:
            sql += f" LIMIT {self._limit}"
        return sql

# Usage — each step returns self, final .build() materialises the result
query = (
    QueryBuilder("orders")
    .select("id", "total", "status")
    .where("status = 'pending'")
    .order_by("created_at")
    .limit(50)
    .build()
)
```

**Rules for fluent interfaces:**
- Every chainable method mutates `self` and returns `self` — or, for immutable designs, returns a new instance (like `dataclasses.replace`).
- Terminal methods (`build()`, `execute()`, `collect()`) do NOT return `self`; they materialise the result.
- Validate in `build()` / the terminal method — not in intermediate steps — so partial state is acceptable.
- Use `Self` (3.11+) or a string forward reference for the return type so subclasses can chain without overriding every method.

---

### 2.16 Testing — pytest, fakes, and conftest

**Stack:** `pytest` + `pytest-asyncio` (`asyncio_mode = "auto"` in `pyproject.toml`). Never `unittest`.

#### Fakes over mocks — always

Write in-memory implementations of your `Protocol` interfaces. One fake, reused everywhere. `unittest.mock.Mock` is the crutch you reach for when the dependency is not injected — fix the design first.

```python
# tests/fakes.py
class InMemoryUserRepository:
    def __init__(self) -> None:
        self._store: dict[str, User] = {}

    def get(self, user_id: str) -> User:
        if user_id not in self._store:
            raise NotFoundError("User", user_id)
        return self._store[user_id]

    def save(self, user: User) -> None:
        self._store[user.id] = user

    def exists(self, email: str) -> bool:
        return any(u.email == email for u in self._store.values())


class CapturingEmailSender:
    def __init__(self) -> None:
        self.sent: list[dict[str, str]] = []

    def send(self, to: str, subject: str, body: str) -> None:
        self.sent.append({"to": to, "subject": subject, "body": body})
```

#### `conftest.py` is the DI container for tests

```python
# tests/conftest.py
import pytest
from tests.fakes import InMemoryUserRepository, CapturingEmailSender
from mypackage.services import RegistrationService

@pytest.fixture
def user_repo() -> InMemoryUserRepository:
    return InMemoryUserRepository()

@pytest.fixture
def mailer() -> CapturingEmailSender:
    return CapturingEmailSender()

@pytest.fixture
def registration_svc(
    user_repo: InMemoryUserRepository,
    mailer: CapturingEmailSender,
) -> RegistrationService:
    return RegistrationService(users=user_repo, mailer=mailer)
```

#### Naming and structure

- Test file mirrors `src/` structure: `tests/services/test_registration.py` for `src/mypackage/services/registration.py`.
- Name tests `test_<scenario>_<expected_outcome>`: `test_register_with_existing_email_raises_duplicate_error`.
- One behaviour per test. Use `@pytest.mark.parametrize` instead of copy-pasting:

```python
@pytest.mark.parametrize("email,password,expected", [
    ("", "secret", "Email must not be empty"),
    ("not-an-email", "secret", "Invalid email format"),
    ("a@b.com", "", "Password must not be empty"),
])
def test_register_rejects_invalid_input(
    registration_svc: RegistrationService,
    email: str,
    password: str,
    expected: str,
) -> None:
    with pytest.raises(ValidationError, match=expected):
        registration_svc.register(email, password)
```

#### Rules

- **No `unittest.mock.patch()` on domain or service code.** If patching is needed, the dependency is not injected yet — fix the architecture.
- **No `patch("datetime.now")` or `patch("uuid.uuid4")`.** Inject a `Clock` protocol or pass the value as a parameter.
- Domain tests are pure Python — no I/O, no async, no DB. They run in milliseconds.
- Async tests: `@pytest.mark.asyncio` per test, or set `asyncio_mode = "auto"` in `pyproject.toml` to apply globally.

---

### 2.17 Observability — correlation IDs, structured logs, OpenTelemetry

#### Correlation IDs via `contextvars`

Thread a `request_id` through every log line without passing it as a function argument:

```python
# mypackage/context.py
import uuid
from contextvars import ContextVar

request_id: ContextVar[str] = ContextVar("request_id", default="")
```

Set it once in FastAPI middleware — it flows into every downstream call automatically:

```python
# mypackage/middleware.py
from starlette.middleware.base import BaseHTTPMiddleware
from mypackage.context import request_id

class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        token = request_id.set(str(uuid.uuid4()))
        try:
            return await call_next(request)
        finally:
            request_id.reset(token)
```

#### Structured logging — `structlog` (JSON output)

Plain `%s` log messages are hard to query in Datadog / ELK / CloudWatch at scale. Emit JSON instead:

```python
# mypackage/logging_config.py
import logging
import structlog

def configure_logging(level: int = logging.INFO) -> None:
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,   # pulls in request_id automatically
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        logger_factory=structlog.PrintLoggerFactory(),
    )
```

Bind `request_id` to structlog's contextvars at the middleware boundary:

```python
import structlog.contextvars
structlog.contextvars.bind_contextvars(request_id=request_id.get())
# Every subsequent logger.info/error in this request automatically includes request_id
```

#### OpenTelemetry — distributed tracing

Instrument at service / use-case boundaries — not inside every function:

```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

async def embed_documents(texts: list[str]) -> list[list[float]]:
    with tracer.start_as_current_span("embed_documents") as span:
        span.set_attribute("document.count", len(texts))
        result = await _client.embed(texts)
        span.set_attribute("embedding.dimensions", len(result[0]) if result else 0)
        return result
```

- Configure the exporter via env vars (`OTEL_EXPORTER_OTLP_ENDPOINT`) — never hard-code endpoints.
- Use auto-instrumentation packages (`opentelemetry-instrumentation-fastapi`, `opentelemetry-instrumentation-httpx`) to avoid per-call boilerplate.
- Add `opentelemetry-sdk` and the relevant exporter to `pyproject.toml` dependencies.

---

### 2.18 Generator and iterator pipelines — lazy by default

For data engineering (ingestion, chunking, embedding, retrieval): pull data through stages lazily. Never load an entire corpus into memory before processing starts.

#### Generator composition

```python
from collections.abc import Iterator, Iterable
from pathlib import Path

def read_lines(path: Path) -> Iterator[str]:
    """Yield lines one at a time — no full file in memory."""
    with path.open(encoding="utf-8") as f:
        yield from f

def clean(lines: Iterable[str]) -> Iterator[str]:
    return (line.strip() for line in lines if line.strip())

def chunk(lines: Iterable[str], size: int) -> Iterator[list[str]]:
    """Batch lines for bulk API calls (e.g. embedding endpoints)."""
    batch: list[str] = []
    for line in lines:
        batch.append(line)
        if len(batch) >= size:
            yield batch
            batch = []
    if batch:
        yield batch

# Nothing materialises until consumed — memory stays flat regardless of file size
for batch in chunk(clean(read_lines(Path("corpus.txt"))), size=50):
    embeddings = embed_batch(batch)
```

#### `itertools` — always prefer over manual loops

```python
import itertools
from collections.abc import Iterable, Iterator
from typing import TypeVar

T = TypeVar("T")

# Flatten nested iterables
flat = list(itertools.chain.from_iterable(nested))

# Python 3.12+ — built-in fixed-size batching
for batch in itertools.batched(records, 100):
    process(batch)

# Python <3.12 — manual equivalent
def batched(it: Iterable[T], n: int) -> Iterator[tuple[T, ...]]:
    it_ = iter(it)
    while chunk := tuple(itertools.islice(it_, n)):
        yield chunk
```

#### Async generators for streaming I/O

```python
from collections.abc import AsyncIterator
import httpx

async def paginate(client: httpx.AsyncClient, url: str) -> AsyncIterator[dict[str, object]]:
    """Yield one page at a time from a paginated API."""
    while url:
        r = await client.get(url)
        r.raise_for_status()
        data: dict[str, object] = r.json()
        yield data
        url = str(data.get("next", ""))
```

#### Rules

- Return `Iterator[T]` / `AsyncIterator[T]` from pipeline stages — not `list[T]` unless the caller genuinely needs random access.
- Use `collections.abc.Iterator`, `Iterable`, `Generator` for annotations — not `typing.Iterator` (deprecated since 3.9).
- `yield from` for delegation; never `for item in sub: yield item`.
- A stage that must fully consume its input before emitting must document that in its docstring — lazy is the unspoken default.

---

## Step 3 — Research before implementing

If the task involves a third-party library, an external API, a newer stdlib module, or anything version-sensitive:

> **Invoke the `research-library` skill first.**

Do not rely on training-time knowledge for API shapes — these change. Fetch current docs and verify the import paths, method signatures, and configuration format before writing any code.

---

## Step 4 — Review checklist (use before finishing)

Before handing back any code, run through:

- [ ] Python version detected; version-gated idioms are correct for that version
- [ ] All functions and methods have full type annotations
- [ ] No `Any` without a comment justifying it; no `Dict`/`List`/`Optional` from `typing`
- [ ] No `.get()` anywhere — not even in comparisons; no `value or fallback`; no `x if x is not None else default` hidden defaults
- [ ] No silent failures: every error branch raises or logs at WARNING/ERROR — never silently returns `None` or an empty value
- [ ] Pydantic used at data boundaries; `extra="forbid"` set; `BaseSettings` used for env/secrets
- [ ] `SecretStr` wraps all secrets; `.get_secret_value()` only at point of use
- [ ] Settings (and other singletons) exposed via `@functools.cache` factory (`get_settings()`) — not a bare module-level instance; `cache_clear()` used in tests
- [ ] Enums used for any field with a fixed set of allowed values; `Literal` for one-off narrow types
- [ ] `exceptions.py` exists; all custom exceptions inherit from a package base error class
- [ ] Every `raise` is preceded by `logger.error(...)` with context
- [ ] No `except Exception: pass`; no broad `except Exception:` outside top-level handlers
- [ ] `raise NewError(...) from original` used when wrapping external exceptions
- [ ] `pathlib.Path` used everywhere; no `os.path`
- [ ] `importlib.resources.files()` for bundled non-py assets
- [ ] Relative imports within the package
- [ ] `logging.getLogger(__name__)` in every module; no stray `print()`
- [ ] `async def` used for I/O-bound operations; `TaskGroup` on 3.11+
- [ ] Patterns are Pythonic (context managers, generators, `@property`, `@functools.cache` for singletons) — not Java-style builders/getters/singletons
- [ ] Complex functions split; loop bodies >3 lines extracted into named helpers (`_build_x`, `_is_valid_x`)
- [ ] `match` statement used where it improves clarity (3.10+)
- [ ] `ruff check` + `ruff format` would pass (mentally lint the output)
- [ ] Docstrings are concise one-liners (or short multi-line) with no `:param:`/`:type:`/`:returns:` tags — type hints cover those
- [ ] Business logic is in pure domain/service functions with zero direct I/O or framework imports
- [ ] Dependencies injected via `Protocol` + constructor injection; swappable without touching business logic
- [ ] Entry points (routes, CLI, handlers) are thin wiring — no logic that needs a unit test
- [ ] Ports defined as `Protocol` in domain layer; adapters in infrastructure layer; domain never imports adapters
- [ ] Thread-safe singleton construction uses double-checked locking or `threading.Lock` guard around `@functools.cache`
- [ ] Builder pattern uses `dataclasses.replace` / `model_copy` for simple cases; mutable builder only when multi-step validation is needed
- [ ] Factory is a module-level function or `classmethod` — never a `XxxFactory` class with a single `create()` method
- [ ] Fluent/chaining methods return `Self`; terminal method (`build()` / `execute()`) materialises and validates the result
- [ ] `TypeGuard` used for narrowing functions; `@overload` used when return type varies by argument value
- [ ] SQL / NoSQL queries use parameterised statements — no f-strings or string concatenation with user input
- [ ] Secrets compared with `hmac.compare_digest`; `SecretStr.get_secret_value()` called only at point of use
- [ ] User-supplied strings sanitised (truncated, control chars stripped) before appearing in log messages
- [ ] Input size validated before LLM calls, bulk DB operations, or file processing
- [ ] `field_validator` used for per-field coercion; `model_validator` used for cross-field constraints
- [ ] CPU-bound work uses `ProcessPoolExecutor`; blocking sync I/O in async uses `loop.run_in_executor`
- [ ] `__all__` defined in `__init__.py`; internal modules are `_prefixed`; removed public symbols emit `DeprecationWarning` first
- [ ] Hot value objects use `@dataclass(slots=True)` (3.10+) to reduce per-instance memory
- [ ] Pipeline stages return `Iterator[T]` / `AsyncIterator[T]`; `collections.abc` used for annotations, not `typing`
- [ ] Tests use in-memory fakes (Protocol implementations), not `unittest.mock.Mock` or `patch()` on domain code
- [ ] `conftest.py` wires fakes into fixtures; test files mirror `src/` directory structure
- [ ] Correlation ID stored in `ContextVar`; structlog binds it automatically to every log line in a request
- [ ] OTel spans added at service/use-case boundaries; exporter configured via env vars, never hard-coded

---

## Quick reference: import cheatsheet by version

```python
# ── Python 3.9+ ────────────────────────────────────────────────
from __future__ import annotations        # enables X | Y union in 3.9
import functools                          # @functools.cache for singleton factories
from typing import TypeVar, Protocol, runtime_checkable
from typing import TypedDict, overload, Final, ClassVar, Literal
from importlib.resources import files     # non-py bundled assets
from enum import Enum                     # use str+Enum for serialisable enums
from pydantic import BaseModel, ConfigDict, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

# ── Python 3.10+ ───────────────────────────────────────────────
# X | Y union works natively (no __future__ needed)
from typing import TypeGuard, ParamSpec, Concatenate

# ── Python 3.11+ ───────────────────────────────────────────────
from typing import Self, LiteralString, Never, TypeVarTuple, Unpack
# asyncio.TaskGroup available

# ── Python 3.12+ ───────────────────────────────────────────────
# type X = ...  (new soft keyword, replaces TypeAlias)
# type Vector[T] = list[T]  (generic alias)
# def fn[T](x: T) -> T:    (generic function, PEP 695)
import tomllib                            # stdlib TOML (backport: tomli)

# ── exceptions.py skeleton (every package) ─────────────────────
# class MyPackageError(Exception): ...
# class NotFoundError(MyPackageError): ...
# class DuplicateError(MyPackageError): ...
# class ValidationError(MyPackageError): ...
# class ConfigurationError(MyPackageError): ...
# class ExternalServiceError(MyPackageError): ...
```
