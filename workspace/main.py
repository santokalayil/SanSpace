"""
Typer Showcase — a single-file CLI that exercises every major Typer feature.

Run:
    python main.py --help
    python main.py greet Alice
    python main.py process /path/to/file.txt --count 3 --ratio 0.75
    python main.py users --help
    python main.py files --help
    python main.py demo-progress
    python main.py demo-rich
    python main.py demo-password
    python main.py demo-confirm
    python main.py demo-env --help        # uses APP_HOST / APP_PORT env vars
    python main.py demo-abort
    python main.py demo-exit-code
    python main.py old-command            # deprecated
    python main.py easter-egg             # hidden (won't appear in --help)
"""

from __future__ import annotations

import time
import uuid
from enum import Enum
from pathlib import Path
from typing import Annotated, Optional

import typer
from rich import print as rprint
from rich.console import Console
from rich.table import Table

# ─────────────────────────────────────────────
# App-wide version constant
# ─────────────────────────────────────────────
APP_VERSION = "1.0.0"

# ─────────────────────────────────────────────
# Rich console (used throughout)
# ─────────────────────────────────────────────
console = Console()

# ─────────────────────────────────────────────
# Enums / Literals used as CLI choice types
# ─────────────────────────────────────────────
class Color(str, Enum):
    """Terminal colour choices (case-insensitive via case_sensitive=False)."""
    red    = "red"
    green  = "green"
    blue   = "blue"
    yellow = "yellow"


class OutputFormat(str, Enum):
    """Output format choices."""
    json  = "json"
    table = "table"
    plain = "plain"


# ─────────────────────────────────────────────
# Sub-apps  (added to main app via add_typer)
# ─────────────────────────────────────────────
users_app = typer.Typer(
    help="[bold cyan]User management[/bold cyan] sub-commands.",
    rich_markup_mode="rich",
    no_args_is_help=True,
)

files_app = typer.Typer(
    help="[bold cyan]File operations[/bold cyan] sub-commands.",
    rich_markup_mode="rich",
    no_args_is_help=True,
)

# ─────────────────────────────────────────────
# Main application
# ─────────────────────────────────────────────
app = typer.Typer(
    name="typer-showcase",
    help=(
        "[bold green]Typer Showcase[/bold green] — every major feature in one app.\n\n"
        "Run any sub-command with [cyan]--help[/cyan] for details."
    ),
    rich_markup_mode="rich",
    no_args_is_help=True,
    pretty_exceptions_enable=True,
    pretty_exceptions_show_locals=False,
    pretty_exceptions_short=True,
    add_completion=True,
    suggest_commands=True,
)

# Register sub-apps
app.add_typer(users_app, name="users")
app.add_typer(files_app, name="files")


# ─────────────────────────────────────────────
# Shared state (populated by callback)
# ─────────────────────────────────────────────
class State:
    verbose: bool = False


state = State()


# ─────────────────────────────────────────────
# @app.callback — runs before every command
#   • --version with is_eager=True
#   • --verbose shared flag
# ─────────────────────────────────────────────
def _version_callback(value: bool) -> None:
    """Print version then exit cleanly (is_eager stops further processing)."""
    if value:
        typer.echo(f"typer-showcase v{APP_VERSION}")
        raise typer.Exit()


@app.callback()
def main_callback(
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-v", help="Enable verbose output."),
    ] = False,
    version: Annotated[
        Optional[bool],
        typer.Option(
            "--version", "-V",
            help="Show version and exit.",
            callback=_version_callback,
            is_eager=True,          # processed before any other option
            expose_value=False,
        ),
    ] = None,
) -> None:
    """
    [bold]typer-showcase[/bold] — top-level callback.

    Demonstrates [italic]@app.callback()[/italic] with a shared flag and
    an eager [cyan]--version[/cyan] option.
    """
    state.verbose = verbose
    if verbose:
        console.print("[dim]Verbose mode enabled.[/dim]")


# ─────────────────────────────────────────────
# 1. greet — Argument (required) + Option (optional)
# ─────────────────────────────────────────────
@app.command()
def greet(
    name: Annotated[
        str,
        typer.Argument(help="The name to greet."),
    ],
    greeting: Annotated[
        str,
        typer.Option("--greeting", "-g", help="Custom greeting word."),
    ] = "Hello",
    color: Annotated[
        Color,
        typer.Option(
            "--color", "-c",
            help="Colour for the greeting.",
            case_sensitive=False,
            rich_help_panel="Display options",
        ),
    ] = Color.green,
    times: Annotated[
        int,
        typer.Option(
            "--times", "-n",
            help="How many times to greet.",
            min=1,
            max=5,
            clamp=True,
            rich_help_panel="Display options",
            show_default=True,
        ),
    ] = 1,
) -> None:
    """
    Greet [bold]NAME[/bold].

    Demonstrates: [cyan]Argument()[/cyan], [cyan]Option()[/cyan],
    [cyan]Enum[/cyan] choice, [cyan]min/max/clamp[/cyan],
    [cyan]rich_help_panel[/cyan], [cyan]case_sensitive=False[/cyan].
    """
    for _ in range(times):
        styled = typer.style(f"{greeting}, {name}!", fg=color.value, bold=True)
        typer.echo(styled)

    if state.verbose:
        console.print(
            f"[dim]Used color=[cyan]{color.value}[/cyan], "
            f"times=[cyan]{times}[/cyan][/dim]"
        )


# ─────────────────────────────────────────────
# 2. process — Path + float + bool flag + Optional
# ─────────────────────────────────────────────
@app.command()
def process(
    input_file: Annotated[
        Path,
        typer.Argument(
            help="File to process.",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            resolve_path=True,
            metavar="FILE",
        ),
    ],
    count: Annotated[
        int,
        typer.Option("--count", help="Number of iterations.", min=1),
    ] = 1,
    ratio: Annotated[
        float,
        typer.Option("--ratio", help="Processing ratio (0.0–1.0).", min=0.0, max=1.0),
    ] = 1.0,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run/--no-dry-run", help="Simulate without writing."),
    ] = False,
    note: Annotated[
        Optional[str],
        typer.Option("--note", help="Optional annotation."),
    ] = None,
    fmt: Annotated[
        OutputFormat,
        typer.Option("--format", "-f", help="Output format.", rich_help_panel="Output"),
    ] = OutputFormat.plain,
) -> None:
    """
    Process [bold]FILE[/bold].

    Demonstrates: [cyan]Path[/cyan] with validation, [cyan]float[/cyan]
    with min/max, [cyan]bool[/cyan] flag pair ([cyan]--dry-run/--no-dry-run[/cyan]),
    [cyan]Optional[/cyan] option, and [cyan]OutputFormat[/cyan] enum.
    """
    if dry_run:
        typer.secho("[DRY-RUN] ", fg=typer.colors.YELLOW, bold=True, nl=False)

    typer.echo(f"Processing: {input_file}  count={count}  ratio={ratio}")

    if note:
        typer.secho(f"Note: {note}", fg=typer.colors.CYAN)

    if fmt == OutputFormat.table:
        table = Table("Field", "Value", title="Process Summary")
        table.add_row("file",  str(input_file))
        table.add_row("count", str(count))
        table.add_row("ratio", str(ratio))
        table.add_row("dry_run", str(dry_run))
        if note:
            table.add_row("note", note)
        console.print(table)
    elif fmt == OutputFormat.json:
        import json
        rprint(json.dumps({"file": str(input_file), "count": count,
                           "ratio": ratio, "dry_run": dry_run, "note": note},
                          indent=2))


# ─────────────────────────────────────────────
# 3. multi-value — list[str]
# ─────────────────────────────────────────────
@app.command(name="multi-value")
def multi_value(
    tags: Annotated[
        list[str],
        typer.Option("--tag", "-t", help="Tags to apply (repeat for multiple)."),
    ] = [],
    items: Annotated[
        list[str],
        typer.Argument(help="Items to process (space-separated)."),
    ] = [],
) -> None:
    """
    Process items with optional tags.

    Demonstrates: [cyan]list[str][/cyan] for multi-value [bold]Argument[/bold]
    and [bold]Option[/bold].

    Example:
        [dim]python main.py multi-value foo bar baz --tag alpha --tag beta[/dim]
    """
    table = Table("Item", "Tags", title="Multi-value demo")
    for item in items:
        table.add_row(item, ", ".join(tags) if tags else "[dim]none[/dim]")
    console.print(table)


# ─────────────────────────────────────────────
# 4. demo-progress — typer.progressbar
# ─────────────────────────────────────────────
@app.command(name="demo-progress")
def demo_progress(
    steps: Annotated[int, typer.Option("--steps", min=1, max=100)] = 20,
    delay: Annotated[float, typer.Option("--delay", help="Seconds between steps.", min=0.0)] = 0.05,
) -> None:
    """
    Fake work loop with a progress bar.

    Demonstrates: [cyan]typer.progressbar()[/cyan].
    """
    typer.echo("Starting work…")
    with typer.progressbar(range(steps), label="Processing", length=steps) as progress:
        for _ in progress:
            time.sleep(delay)
    typer.secho("Done!", fg=typer.colors.GREEN, bold=True)


# ─────────────────────────────────────────────
# 5. demo-rich — Rich Console / Table / styled print
# ─────────────────────────────────────────────
@app.command(name="demo-rich")
def demo_rich() -> None:
    """
    Show off Rich output primitives.

    Demonstrates: [cyan]rich.Console[/cyan], [cyan]rich.Table[/cyan],
    [cyan]rprint()[/cyan], [cyan]typer.secho()[/cyan], [cyan]typer.style()[/cyan].
    """
    # typer.style / typer.echo
    typer.echo(typer.style("typer.style()  →  bold+underline", bold=True, underline=True))

    # typer.secho shorthand
    typer.secho("typer.secho()  →  blue text", fg=typer.colors.BLUE)

    # Rich print
    rprint("[bold magenta]rich print()[/bold magenta] — native Rich markup")

    # Rich table
    table = Table("Library", "Purpose", title="[cyan]Rich Demo Table[/cyan]")
    table.add_row("typer",   "[green]CLI framework[/green]")
    table.add_row("click",   "[yellow]Low-level CLI[/yellow]")
    table.add_row("rich",    "[magenta]Terminal formatting[/magenta]")
    console.print(table)

    # Highlight a panel
    from rich.panel import Panel
    console.print(Panel("[bold]🎉 Rich is fully integrated with Typer![/bold]",
                        style="bold green"))


# ─────────────────────────────────────────────
# 6. demo-password — prompt + hide_input + confirmation
# ─────────────────────────────────────────────
@app.command(name="demo-password")
def demo_password(
    username: Annotated[
        str,
        typer.Option("--username", "-u", prompt="Enter username", help="Your username."),
    ] = "",
    password: Annotated[
        str,
        typer.Option(
            "--password", "-p",
            prompt="Enter password",
            confirmation_prompt="Confirm password",
            hide_input=True,
            help="Your password (hidden).",
        ),
    ] = "",
) -> None:
    """
    Prompt for credentials without echoing the password.

    Demonstrates: [cyan]prompt=str[/cyan], [cyan]hide_input=True[/cyan],
    [cyan]confirmation_prompt=True[/cyan].
    """
    typer.secho(f"✓ Hello, {username}! Password received (length={len(password)}).",
                fg=typer.colors.GREEN)


# ─────────────────────────────────────────────
# 7. demo-env — envvar binding + default_factory
# ─────────────────────────────────────────────
@app.command(name="demo-env")
def demo_env(
    request_id: Annotated[
        str,
        typer.Option(
            "--request-id",
            default_factory=lambda: str(uuid.uuid4()),
            help="Auto-generated UUID request ID ([cyan]default_factory[/cyan]).",
            show_default=False,
        ),
    ],
    host: Annotated[
        str,
        typer.Option(
            "--host",
            envvar="APP_HOST",
            help="Server host. Reads [cyan]APP_HOST[/cyan] env var.",
            show_envvar=True,
        ),
    ] = "localhost",
    port: Annotated[
        int,
        typer.Option(
            "--port",
            envvar="APP_PORT",
            help="Server port. Reads [cyan]APP_PORT[/cyan] env var.",
            show_envvar=True,
            min=1,
            max=65535,
        ),
    ] = 8080,
) -> None:
    """
    Connect to a server (fake).

    Demonstrates: [cyan]envvar[/cyan] binding, [cyan]show_envvar=True[/cyan],
    [cyan]default_factory[/cyan] for dynamic defaults.
    """
    console.print(
        f"[bold]Connecting to[/bold] [cyan]{host}:{port}[/cyan] "
        f"[dim](request-id: {request_id})[/dim]"
    )


# ─────────────────────────────────────────────
# 8. demo-confirm — typer.confirm + typer.Abort
# ─────────────────────────────────────────────
@app.command(name="demo-confirm")
def demo_confirm(
    force: Annotated[
        bool,
        typer.Option("--force/--no-force", "-f/-F", help="Skip confirmation prompt."),
    ] = False,
) -> None:
    """
    Destructive action that requires confirmation.

    Demonstrates: [cyan]typer.confirm()[/cyan], [cyan]raise typer.Abort()[/cyan].
    """
    if not force:
        confirmed = typer.confirm("⚠️  This will delete everything. Are you sure?")
        if not confirmed:
            raise typer.Abort()

    typer.secho("Deleting everything… (just kidding, it's a demo).",
                fg=typer.colors.RED, bold=True)


# ─────────────────────────────────────────────
# 9. demo-abort — explicit Abort
# ─────────────────────────────────────────────
@app.command(name="demo-abort")
def demo_abort() -> None:
    """
    Raises [cyan]typer.Abort()[/cyan] unconditionally.

    Demonstrates: [cyan]raise typer.Abort()[/cyan].
    """
    typer.echo("About to abort…")
    raise typer.Abort()


# ─────────────────────────────────────────────
# 10. demo-exit-code — raise typer.Exit(code)
# ─────────────────────────────────────────────
@app.command(name="demo-exit-code")
def demo_exit_code(
    code: Annotated[int, typer.Argument(help="Exit code to return.")] = 1,
) -> None:
    """
    Exit with a specific exit code.

    Demonstrates: [cyan]raise typer.Exit(code=N)[/cyan].
    """
    typer.echo(f"Exiting with code {code}.")
    raise typer.Exit(code=code)


# ─────────────────────────────────────────────
# 11. old-command — deprecated=True
# ─────────────────────────────────────────────
@app.command(name="old-command", deprecated=True)
def old_command() -> None:
    """
    This command is [bold red]deprecated[/bold red].

    Use [cyan]greet[/cyan] instead.

    Demonstrates: [cyan]deprecated=True[/cyan] on a command.
    """
    typer.secho("You called the deprecated command!", fg=typer.colors.YELLOW)


# ─────────────────────────────────────────────
# 12. easter-egg — hidden=True
# ─────────────────────────────────────────────
@app.command(name="easter-egg", hidden=True)
def easter_egg() -> None:
    """
    A hidden command (not shown in --help).

    Demonstrates: [cyan]hidden=True[/cyan] on a command.
    """
    rprint(
        "[bold yellow]🐣  You found the Easter egg![/bold yellow]\n"
        "[dim]This command is hidden — it won't appear in the main --help.[/dim]"
    )


# ─────────────────────────────────────────────
# users sub-app commands
# ─────────────────────────────────────────────
@users_app.callback()
def users_callback() -> None:
    """Manage application users."""


@users_app.command(name="create")
def users_create(
    username: Annotated[str, typer.Argument(help="Username to create.")],
    email: Annotated[str, typer.Option("--email", "-e", prompt="Email address")],
    admin: Annotated[bool, typer.Option("--admin/--no-admin", help="Grant admin rights.")] = False,
) -> None:
    """
    Create a new user.

    Demonstrates: [cyan]app.add_typer()[/cyan] sub-group, nested [cyan]prompt[/cyan].
    """
    role = "[bold red]admin[/bold red]" if admin else "regular"
    console.print(
        f"[green]✓[/green] Created {role} user [bold]{username}[/bold] <{email}>"
    )


@users_app.command(name="list")
def users_list(
    fmt: Annotated[
        OutputFormat,
        typer.Option("--format", "-f", help="Output format."),
    ] = OutputFormat.table,
    limit: Annotated[int, typer.Option("--limit", min=1, max=1000)] = 10,
) -> None:
    """List users (fake data)."""
    fake_users = [
        ("alice",  "alice@example.com",  True),
        ("bob",    "bob@example.com",    False),
        ("charlie","charlie@example.com",False),
    ][:limit]

    if fmt == OutputFormat.table:
        table = Table("Username", "Email", "Admin", title="Users")
        for u, e, a in fake_users:
            table.add_row(u, e, "[red]yes[/red]" if a else "no")
        console.print(table)
    else:
        for u, e, a in fake_users:
            typer.echo(f"{u}\t{e}\t{'admin' if a else 'user'}")


@users_app.command(name="delete")
def users_delete(
    username: Annotated[str, typer.Argument(help="Username to delete.")],
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip confirmation.")] = False,
) -> None:
    """Delete a user."""
    if not yes:
        typer.confirm(f"Delete user '{username}'?", abort=True)
    typer.secho(f"Deleted user '{username}'.", fg=typer.colors.RED)


# ─────────────────────────────────────────────
# files sub-app commands
# ─────────────────────────────────────────────
@files_app.callback()
def files_callback() -> None:
    """Perform file operations."""


@files_app.command(name="info")
def files_info(
    path: Annotated[
        Path,
        typer.Argument(
            help="File or directory to inspect.",
            exists=True,
            resolve_path=True,
        ),
    ],
) -> None:
    """
    Show metadata for a path.

    Demonstrates: [cyan]Path[/cyan] with [cyan]exists=True[/cyan] in a sub-app.
    """
    table = Table("Property", "Value", title=f"[cyan]{path.name}[/cyan]")
    table.add_row("absolute path", str(path))
    table.add_row("is file",       str(path.is_file()))
    table.add_row("is dir",        str(path.is_dir()))
    if path.is_file():
        table.add_row("size (bytes)", str(path.stat().st_size))
    console.print(table)


@files_app.command(name="search")
def files_search(
    directory: Annotated[
        Path,
        typer.Argument(exists=True, dir_okay=True, file_okay=False, resolve_path=True),
    ],
    pattern: Annotated[str, typer.Option("--pattern", "-p", help="Glob pattern.")] = "*",
    recursive: Annotated[bool, typer.Option("--recursive/--no-recursive")] = True,
) -> None:
    """
    Search for files matching a glob pattern.

    Demonstrates: [cyan]dir_okay=True, file_okay=False[/cyan] Path constraint,
    [cyan]bool[/cyan] flag pair.
    """
    glob_fn = directory.rglob if recursive else directory.glob
    matches = list(glob_fn(pattern))

    if not matches:
        typer.secho("No files found.", fg=typer.colors.YELLOW)
        return

    table = Table("Path", "Size", title=f"Search: {pattern}")
    for m in matches[:50]:  # cap at 50 results
        size = str(m.stat().st_size) + " B" if m.is_file() else "[dim]dir[/dim]"
        table.add_row(str(m.relative_to(directory)), size)
    if len(matches) > 50:
        table.add_row("…", f"[dim]+{len(matches)-50} more[/dim]")
    console.print(table)


# ─────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────
if __name__ == "__main__":
    app()
