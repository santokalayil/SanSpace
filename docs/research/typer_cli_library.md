# Research: Typer — Building CLI Applications in Python

## Summary

**Typer** is a Python library for building CLI applications using standard type hints. Written by Sebastián Ramírez (author of FastAPI), it wraps [Click](https://click.palletsprojects.com/) and adds automatic type conversion, shell completion, Rich-formatted help/errors, and zero-boilerplate argument parsing. You declare function parameters with Python type hints; Typer converts them to CLI arguments and options automatically.

- **Package**: `typer`
- **Version researched**: `0.24.1` (released 2026-02-21, latest stable)
- **Python requirement**: ≥ 3.10 (3.9 dropped in 0.24.0; 3.8 dropped in 0.21.0)
- **License**: MIT
- **Author**: Sebastián Ramírez / FastAPI org
- **Engine**: Click ≥ 8.2.1
- **Install**: `pip install typer`
- **Includes**: Rich (formatted output/errors), shellingham (shell detection) — no extras needed
- **Note**: `typer-slim` and `typer-cli` wrapper packages are discontinued as of 0.24.1; use only `typer`

---

## Sources

| Source | URL |
|--------|-----|
| PyPI | https://pypi.org/project/typer/ |
| GitHub | https://github.com/fastapi/typer |
| Official docs | https://typer.tiangolo.com |
| Reference: Typer class | https://typer.tiangolo.com/reference/typer/ |
| Reference: Parameters | https://typer.tiangolo.com/reference/parameters/ |
| Tutorial: First steps | https://typer.tiangolo.com/tutorial/first-steps/ |
| Tutorial: Commands | https://typer.tiangolo.com/tutorial/commands/ |
| Tutorial: Options/Help | https://typer.tiangolo.com/tutorial/options/help/ |
| Tutorial: Printing/Colors | https://typer.tiangolo.com/tutorial/printing/ |
| Tutorial: Terminating | https://typer.tiangolo.com/tutorial/terminating/ |
| Tutorial: Enum choices | https://typer.tiangolo.com/tutorial/parameter-types/enum/ |
| Tutorial: Path | https://typer.tiangolo.com/tutorial/parameter-types/path/ |
| Tutorial: Subcommands | https://typer.tiangolo.com/tutorial/subcommands/add-typer/ |
| Tutorial: Testing | https://typer.tiangolo.com/tutorial/testing/ |
| Release notes | https://typer.tiangolo.com/release-notes/ |
| Source (params.py) | `repos/typer/typer/params.py` (cloned @ tag 0.24.1) |

---

## Latest Version

**`0.24.1`** — released 2026-02-21

```bash
pip install typer            # latest
pip install "typer==0.24.1"  # pinned
```

### Recent Breaking Changes (summary)

| Version | Change |
|---------|--------|
| 0.24.0 | Dropped Python 3.9 |
| 0.23.0 | `pretty_exceptions_show_locals` now defaults to `False` |
| 0.22.0 | `typer-slim` became a full wrapper (requires rich+shellingham) |
| 0.21.0 | Dropped Python 3.8 |
| 0.14.0 | `add_typer()` no longer infers group name from callback function name — must set `name=` explicitly |
| 0.11.0 | Dropped Click 7 support — Click 8+ required |
| 0.15.1 | `shell_complete` deprecated in `Argument()`/`Option()` — use `autocompletion=` |

---

## API Surface

### Installation and imports

```python
pip install typer
```

```python
import typer
from typer import Typer, Argument, Option
from typer.testing import CliRunner        # for tests
from pathlib import Path
from enum import Enum
from typing import Annotated, Optional
```

### Disable Rich (env var)

```bash
TYPER_USE_RICH=0 python your_script.py
```

---

### `typer.run()` — single-command shortcut

```python
def main(name: str):
    print(f"Hello {name}")

if __name__ == "__main__":
    typer.run(main)
```

Usage: `python script.py World` → `Hello World`

---

### `typer.Typer()` — application constructor

```python
app = typer.Typer(
    *,
    name=None,                          # app name shown in help
    invoke_without_command=False,       # run callback even with no subcommand
    no_args_is_help=False,              # show help when no args provided
    chain=False,                        # allow chaining subcommands
    subcommand_metavar=None,
    result_callback=None,
    context_settings=None,
    callback=None,
    help=None,                          # top-level help text
    epilog=None,
    short_help=None,
    options_metavar="[OPTIONS]",
    add_help_option=True,
    hidden=False,
    deprecated=False,
    add_completion=True,                # adds --install-completion / --show-completion
    rich_markup_mode=None,              # None | "rich" | "markdown"
    rich_help_panel=None,
    suggest_commands=True,              # typo correction suggestions (since 0.20.0)
    pretty_exceptions_enable=True,
    pretty_exceptions_show_locals=False,  # set True to show locals in tracebacks
    pretty_exceptions_short=True,
)
```

---

### `@app.command()` — register a subcommand

```python
@app.command(
    name=None,              # override function name as command name
    help=None,              # override docstring as help text
    epilog=None,
    short_help=None,
    context_settings=None,
    add_help_option=True,
    no_args_is_help=False,
    hidden=False,
    deprecated=False,
    rich_help_panel=None,
)
def my_command(name: str):
    ...
```

- Command name defaults to function name (underscores → dashes: `do_thing` → `do-thing`)
- Help text defaults to the function's docstring

---

### `@app.callback()` — shared options for all subcommands

Same parameters as `@app.command()` minus `name`. The decorated function runs before any subcommand.

```python
@app.callback()
def main(verbose: bool = False):
    if verbose:
        typer.echo("Verbose mode on")
```

---

### `app.add_typer()` — nest a sub-app as a command group

```python
users_app = typer.Typer()
app.add_typer(users_app, name="users")   # name= is REQUIRED (not inferred since 0.14.0)
```

Full signature accepts the same params as `Typer()` plus `typer_instance` as first positional arg.

---

### `typer.Argument()` — positional CLI argument

**Preferred modern syntax (Annotated):**
```python
def command(
    name: Annotated[str, typer.Argument(help="The name to greet")] = "World",
):
```

**Full signature:**
```python
typer.Argument(
    default=...,              # ... = required; provide value = optional with that default
    *,
    callback=None,            # Callable — extra logic on value
    metavar=None,             # custom display name in help (default: uppercased param name)
    expose_value=True,
    is_eager=False,
    envvar=None,              # str | list[str] — read from environment variable
    autocompletion=None,      # Callable → list of completion items
    default_factory=None,     # Callable[[], Any] — dynamic default (e.g. lambda: [])
    parser=None,              # Callable[[str], Any] — custom type parser
    click_type=None,          # click.ParamType — raw Click type
    show_default=True,        # bool | str — show/hide/customize default in help
    show_choices=True,
    show_envvar=True,
    help=None,                # str — help text shown in --help
    hidden=False,
    case_sensitive=True,      # for Enum choices
    min=None, max=None, clamp=False,   # numeric range validation
    formats=None,             # list[str] — datetime format strings
    mode=None,                # file open mode
    encoding=None, errors="strict", lazy=None, atomic=False,
    exists=False,             # Path: file/dir must exist
    file_okay=True,           # Path: allow files
    dir_okay=True,            # Path: allow directories
    writable=False, readable=True,
    resolve_path=False,
    allow_dash=False,
    path_type=None,
    rich_help_panel=None,
)
```

---

### `typer.Option()` — named CLI option (`--flag`)

**Preferred modern syntax (Annotated):**
```python
def command(
    name: Annotated[str, typer.Option(help="The name")] = "World",
    count: Annotated[int, typer.Option("--count", "-c", help="Repetitions")] = 1,
):
```

**Full signature** (extends Argument with prompt/password/flag features):
```python
typer.Option(
    default=...,              # ... = required; value = optional with default
    *param_decls,             # positional strings: "--name", "-n" (aliases)
    # All Argument params apply here, plus:
    prompt=False,             # True | str — show interactive prompt if not provided
    confirmation_prompt=False,  # ask to confirm (for passwords)
    prompt_required=True,
    hide_input=False,         # mask input (for passwords)
    count=False,              # int counter: -v -v -v → 3
    allow_from_autoenv=True,
    # is_flag and flag_value are legacy/compat params
)
```

---

### Parameter type system

| Python type hint | CLI behaviour |
|-----------------|---------------|
| `str` | String value |
| `int` | Integer, validated |
| `float` | Float, validated |
| `bool` (Option) | Auto `--flag / --no-flag` toggle pair |
| `bool` (Argument) | Accepts `True` or `False` as string |
| `Optional[X]` / `X \| None` | Optional, defaults to `None` |
| `list[str]` | Repeatable: `--opt a --opt b` |
| `pathlib.Path` | Path string, with optional validation |
| `typer.FileText` | Opens text file for reading |
| `typer.FileTextWrite` | Opens text file for writing |
| `typer.FileBinaryRead` | Opens binary file for reading |
| `typer.FileBinaryWrite` | Opens binary file for writing |
| `class E(str, Enum)` | Restricted to enum values (choices) |
| `Literal["a", "b", "c"]` | Restricted to listed values |
| `datetime.datetime` | Parsed ISO-8601 string (configurable via `formats=`) |
| `uuid.UUID` | Parsed UUID string |
| `tuple[X, Y]` | Fixed-length multi-value |

---

### Output and colors

**Recommended: use Rich directly**
```python
from rich import print                      # drop-in colored replacement for print()
from rich.console import Console

console = Console()
err_console = Console(stderr=True)

console.print("[bold green]Success![/bold green]")
err_console.print("[red]Error![/red]")
```

**Legacy Click-style (still works):**
```python
typer.echo("plain text")                    # = click.echo; handles bytes/str
typer.echo(f"msg", err=True)               # print to stderr

styled = typer.style("text", fg=typer.colors.GREEN, bold=True)
typer.echo(styled)

typer.secho("styled + echo", fg=typer.colors.BLUE)  # style + echo in one call
```

---

### Terminating

```python
raise typer.Exit()           # clean exit, code=0
raise typer.Exit(code=1)     # error exit
raise typer.Abort()          # prints "Aborted!" and exits with non-zero
```

---

### Testing with `CliRunner`

```python
from typer.testing import CliRunner
import app_module

runner = CliRunner()

def test_basic():
    result = runner.invoke(app_module.app, ["--name", "Alice"])
    assert result.exit_code == 0
    assert "Alice" in result.output

def test_prompt():
    result = runner.invoke(app_module.app, [], input="Alice\n")
    assert result.exit_code == 0

def test_error():
    result = runner.invoke(app_module.app, ["--bad-flag"])
    assert result.exit_code != 0
```

`result` attributes: `.exit_code`, `.output` (stdout+stderr combined by default), `.stdout`, `.stderr`, `.exception`

---

## Docs vs Code Mismatches

**No mismatches found.**

The reference documentation at `/reference/parameters/` and `/reference/typer/` exactly reflect the source signatures in `typer/params.py` v0.24.1. The `@overload` variants in source (for `parser=` and `click_type=` specialisations) are an implementation detail and do not change the effective public API.

**One important deprecation to be aware of:**

| Pattern | Status | Notes |
|---------|--------|-------|
| `name: str = typer.Option(default="x", help="...")` | **Deprecated** | Old-style; still works but may be removed in future |
| `name: Annotated[str, typer.Option(help="...")] = "x"` | **Preferred** | New canonical style since 0.9.0 |
| `shell_complete=` in `Argument()`/`Option()` | **Deprecated** (since 0.15.1) | Use `autocompletion=` instead |

---

## Implementation

### Example 1 — Single command script

```python
# greet.py
import typer
from typing import Annotated

def main(
    name: Annotated[str, typer.Argument(help="Name to greet")],
    count: Annotated[int, typer.Option("--count", "-c", help="How many times")] = 1,
    shout: Annotated[bool, typer.Option(help="UPPERCASE output")] = False,
):
    """Greet a person."""
    message = f"Hello, {name}!"
    if shout:
        message = message.upper()
    for _ in range(count):
        typer.echo(message)

if __name__ == "__main__":
    typer.run(main)
```

```bash
python greet.py --help
python greet.py Alice --count 3 --shout
```

---

### Example 2 — Multi-command app

```python
# app.py
import typer
from typing import Annotated

app = typer.Typer(help="My CLI tool")

@app.command()
def create(name: Annotated[str, typer.Argument(help="Item name")]):
    """Create a new item."""
    typer.echo(f"Creating: {name}")

@app.command()
def delete(
    name: Annotated[str, typer.Argument(help="Item name")],
    force: Annotated[bool, typer.Option("--force", "-f")] = False,
):
    """Delete an item."""
    if not force:
        typer.confirm(f"Delete '{name}'?", abort=True)
    typer.echo(f"Deleted: {name}")

if __name__ == "__main__":
    app()
```

```bash
python app.py create foo
python app.py delete foo --force
```

---

### Example 3 — Subcommand groups with `add_typer`

```python
# main.py
import typer

app = typer.Typer()
users_app = typer.Typer()
items_app = typer.Typer()

app.add_typer(users_app, name="users", help="Manage users")
app.add_typer(items_app, name="items", help="Manage items")

@users_app.command("list")
def users_list():
    typer.echo("Listing users")

@users_app.command("create")
def users_create(name: str):
    typer.echo(f"Creating user: {name}")

@items_app.command("list")
def items_list():
    typer.echo("Listing items")

if __name__ == "__main__":
    app()
```

```bash
python main.py users list
python main.py users create Alice
python main.py items list
```

---

### Example 4 — Enum choices

```python
import typer
from enum import Enum
from typing import Annotated

class Color(str, Enum):
    red = "red"
    green = "green"
    blue = "blue"

app = typer.Typer()

@app.command()
def paint(
    color: Annotated[Color, typer.Option(case_sensitive=False)] = Color.red,
):
    """Paint something."""
    typer.echo(f"Painting with {color.value}")

if __name__ == "__main__":
    app()
```

```bash
python paint.py --color green
python paint.py --color GREEN    # case_sensitive=False allows this
```

---

### Example 5 — Path validation

```python
import typer
from pathlib import Path
from typing import Annotated

app = typer.Typer()

@app.command()
def process(
    config: Annotated[
        Path,
        typer.Option(
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            resolve_path=True,
            help="Config file path",
        ),
    ],
):
    """Process a config file."""
    typer.echo(f"Processing: {config}")

if __name__ == "__main__":
    app()
```

---

### Example 6 — Password prompt

```python
import typer
from typing import Annotated

app = typer.Typer()

@app.command()
def login(
    username: Annotated[str, typer.Option(prompt=True)],
    password: Annotated[str, typer.Option(prompt=True, hide_input=True, confirmation_prompt=True)],
):
    typer.echo(f"Logged in as {username}")

if __name__ == "__main__":
    app()
```

---

### Example 7 — Shared callback options (verbose flag)

```python
import typer
from typing import Annotated

app = typer.Typer()
state = {"verbose": False}

@app.callback()
def main(verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False):
    """My App."""
    state["verbose"] = verbose

@app.command()
def run():
    if state["verbose"]:
        typer.echo("Running verbosely...")
    typer.echo("Done.")

if __name__ == "__main__":
    app()
```

---

### Example 8 — Rich output

```python
import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer()
console = Console()

@app.command()
def show():
    table = Table("Name", "Status")
    table.add_row("alice", "[green]active[/green]")
    table.add_row("bob", "[red]inactive[/red]")
    console.print(table)

if __name__ == "__main__":
    app()
```

---

### Example 9 — Testing

```python
# test_app.py
from typer.testing import CliRunner
from myapp import app   # your Typer app

runner = CliRunner()

def test_create():
    result = runner.invoke(app, ["create", "Alice"])
    assert result.exit_code == 0
    assert "Alice" in result.output

def test_missing_arg():
    result = runner.invoke(app, ["create"])
    assert result.exit_code != 0

def test_prompt():
    result = runner.invoke(app, ["login"], input="alice\nsecret\nsecret\n")
    assert result.exit_code == 0
    assert "alice" in result.output
```

---

### Complete public API (`typer.__init__` exports)

**From Click (re-exported):**
`Abort`, `BadParameter`, `Exit`, `clear`, `confirm`, `echo_via_pager`, `edit`, `getchar`, `pause`, `progressbar`, `prompt`, `secho`, `style`, `unstyle`, `echo`, `format_filename`, `get_app_dir`, `get_binary_stream`, `get_text_stream`, `open_file`, `get_terminal_size`

**From Typer internals:**
`colors`, `Typer`, `launch`, `run`, `CallbackParam`, `Context`, `FileBinaryRead`, `FileBinaryWrite`, `FileText`, `FileTextWrite`, `Argument`, `Option`

---

## How to Validate

```bash
# 1. Install
pip install typer

# 2. Run help on any example
python greet.py --help
python app.py --help
python app.py create --help

# 3. Run the examples with args
python greet.py Alice --count 2
python app.py create Widget

# 4. Run tests (requires pytest)
pip install pytest
pytest test_app.py -v

# 5. Check shell completion
python app.py --install-completion    # install to current shell
python app.py --show-completion       # show completion script

# 6. Check version
python -c "import typer; print(typer.__version__)"

# 7. Disable Rich for plain output (CI / testing)
TYPER_USE_RICH=0 python app.py --help
```

---

## Recommended Next Steps

| Topic | URL |
|-------|-----|
| Context: pass data between commands | https://typer.tiangolo.com/tutorial/commands/context/ |
| Autocompletion for custom values | https://typer.tiangolo.com/tutorial/options/autocompletion/ |
| Progress bars | https://typer.tiangolo.com/tutorial/progressbar/ |
| App directory (config/data files) | https://typer.tiangolo.com/tutorial/app-dir/ |
| One file per command pattern | https://typer.tiangolo.com/tutorial/one-file-per-command/ |
| Building a distributable package | https://typer.tiangolo.com/tutorial/package/ |
| Custom parameter types | https://typer.tiangolo.com/tutorial/parameter-types/custom-types/ |
| Multiple values (list/tuple params) | https://typer.tiangolo.com/tutorial/multiple-values/ |
| Rich Markdown in help text | https://typer.tiangolo.com/tutorial/commands/help/#rich-markdown-and-markup |
| Using Click directly (advanced) | https://click.palletsprojects.com/en/8.x/ |
