"""
Tests for Typer showcase — demonstrating typer.testing.CliRunner.
"""
from pathlib import Path

import pytest
from typer.testing import CliRunner

from main import app, APP_VERSION

runner = CliRunner()


# ─── helpers ─────────────────────────────────────────────────────────────────
def invoke(*args: str, input: str | None = None) -> "Result":
    return runner.invoke(app, list(args), input=input, catch_exceptions=False)


# ─── version / callback ───────────────────────────────────────────────────────
def test_version():
    result = invoke("--version")
    assert result.exit_code == 0
    assert APP_VERSION in result.output


def test_help_shows_commands():
    result = invoke("--help")
    assert result.exit_code == 0
    for cmd in ("greet", "process", "multi-value", "demo-progress",
                "demo-rich", "demo-env", "demo-confirm", "demo-abort",
                "demo-exit-code", "old-command"):
        assert cmd in result.output
    # hidden command must NOT appear
    assert "easter-egg" not in result.output


# ─── greet ───────────────────────────────────────────────────────────────────
def test_greet_default():
    result = invoke("greet", "World")
    assert result.exit_code == 0
    assert "World" in result.output


def test_greet_custom_greeting_and_times():
    result = invoke("greet", "Ada", "--greeting", "Hi", "--times", "3")
    assert result.exit_code == 0
    assert result.output.count("Ada") == 3


def test_greet_color_case_insensitive():
    result = invoke("greet", "Bob", "--color", "BLUE")
    assert result.exit_code == 0
    assert "Bob" in result.output


def test_greet_times_clamped_to_max():
    # times max=5; passing 99 is clamped to 5
    result = invoke("greet", "Clamp", "--times", "99")
    assert result.exit_code == 0
    assert result.output.count("Clamp") == 5


# ─── multi-value ─────────────────────────────────────────────────────────────
def test_multi_value():
    result = invoke("multi-value", "foo", "bar", "--tag", "a", "--tag", "b")
    assert result.exit_code == 0
    assert "foo" in result.output
    assert "bar" in result.output
    assert "a" in result.output


# ─── demo-progress ───────────────────────────────────────────────────────────
def test_demo_progress():
    result = invoke("demo-progress", "--steps", "3", "--delay", "0")
    assert result.exit_code == 0
    assert "Done" in result.output


# ─── demo-env ────────────────────────────────────────────────────────────────
def test_demo_env_defaults():
    result = invoke("demo-env")
    assert result.exit_code == 0
    assert "localhost" in result.output
    assert "8080" in result.output


def test_demo_env_custom():
    result = invoke("demo-env", "--host", "127.0.0.1", "--port", "9000")
    assert result.exit_code == 0
    assert "127.0.0.1:9000" in result.output


def test_demo_env_via_envvar(monkeypatch):
    monkeypatch.setenv("APP_HOST", "myserver.local")
    monkeypatch.setenv("APP_PORT", "5432")
    result = invoke("demo-env")
    assert result.exit_code == 0
    assert "myserver.local" in result.output
    assert "5432" in result.output


# ─── demo-confirm ────────────────────────────────────────────────────────────
def test_demo_confirm_force():
    result = invoke("demo-confirm", "--force")
    assert result.exit_code == 0
    assert "demo" in result.output.lower()


def test_demo_confirm_aborts_on_no(monkeypatch):
    result = runner.invoke(app, ["demo-confirm"], input="n\n", catch_exceptions=False)
    assert result.exit_code != 0 or "Aborted" in result.output


# ─── demo-abort ──────────────────────────────────────────────────────────────
def test_demo_abort():
    result = runner.invoke(app, ["demo-abort"], catch_exceptions=False)
    # Typer prints "Aborted!" and exits non-zero
    assert "Aborted" in result.output or result.exit_code != 0


# ─── demo-exit-code ──────────────────────────────────────────────────────────
def test_demo_exit_code_zero():
    result = invoke("demo-exit-code", "0")
    assert result.exit_code == 0


def test_demo_exit_code_nonzero():
    result = runner.invoke(app, ["demo-exit-code", "42"], catch_exceptions=False)
    assert result.exit_code == 42


# ─── deprecated command ──────────────────────────────────────────────────────
def test_old_command_shows_deprecation_warning():
    result = invoke("old-command")
    # Typer prints a DeprecationWarning header
    assert "deprecated" in result.output.lower()


# ─── hidden command still works ──────────────────────────────────────────────
def test_easter_egg_runs():
    result = invoke("easter-egg")
    assert result.exit_code == 0
    assert "Easter egg" in result.output


# ─── users sub-app ───────────────────────────────────────────────────────────
def test_users_help():
    result = invoke("users", "--help")
    assert result.exit_code == 0
    assert "create" in result.output
    assert "list" in result.output
    assert "delete" in result.output


def test_users_create(monkeypatch):
    result = runner.invoke(
        app,
        ["users", "create", "alice", "--email", "alice@example.com"],
        catch_exceptions=False,
    )
    assert result.exit_code == 0
    assert "alice" in result.output


def test_users_list():
    result = invoke("users", "list", "--format", "plain")
    assert result.exit_code == 0
    assert "alice" in result.output


def test_users_delete_with_yes_flag():
    result = invoke("users", "delete", "bob", "--yes")
    assert result.exit_code == 0
    assert "bob" in result.output


# ─── files sub-app ───────────────────────────────────────────────────────────
def test_files_info(tmp_path):
    f = tmp_path / "hello.txt"
    f.write_text("hi")
    result = invoke("files", "info", str(f))
    assert result.exit_code == 0
    assert "hello.txt" in result.output
    assert "True" in result.output  # is file


def test_files_search(tmp_path):
    (tmp_path / "a.py").write_text("")
    (tmp_path / "b.py").write_text("")
    result = invoke("files", "search", str(tmp_path), "--pattern", "*.py")
    assert result.exit_code == 0
    assert "a.py" in result.output
    assert "b.py" in result.output


def test_files_search_nonrecursive(tmp_path):
    (tmp_path / "root.txt").write_text("")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "nested.txt").write_text("")
    result = invoke(
        "files", "search", str(tmp_path),
        "--pattern", "*.txt",
        "--no-recursive",
    )
    assert result.exit_code == 0
    assert "root.txt" in result.output
    assert "nested.txt" not in result.output


# ─── process command (with a real temp file) ─────────────────────────────────
def test_process_basic(tmp_path):
    f = tmp_path / "data.txt"
    f.write_text("sample content")
    result = invoke("process", str(f))
    assert result.exit_code == 0
    assert "data.txt" in result.output


def test_process_missing_file():
    result = runner.invoke(app, ["process", "/nonexistent/file.txt"], catch_exceptions=False)
    assert result.exit_code != 0


def test_process_dry_run(tmp_path):
    f = tmp_path / "data.txt"
    f.write_text("x")
    result = invoke("process", str(f), "--dry-run")
    assert result.exit_code == 0
    assert "DRY-RUN" in result.output


def test_process_table_format(tmp_path):
    f = tmp_path / "data.txt"
    f.write_text("x")
    result = invoke("process", str(f), "--format", "table")
    assert result.exit_code == 0
    assert "Process Summary" in result.output
