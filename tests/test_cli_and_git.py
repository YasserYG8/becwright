import subprocess
import sys
from pathlib import Path

import pytest

from becwright import cli, git
from becwright.engine import Result, RuleResult
from becwright.rules import Rule

_SRC = Path(__file__).resolve().parents[1] / "src"


def _git(root, *args):
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True)


def _init_repo(tmp_path):
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "t@t.t")
    _git(tmp_path, "config", "user.name", "t")
    return tmp_path


def _rules_yaml(module):
    check = f'PYTHONPATH="{_SRC}" "{sys.executable}" -m becwright.checks.{module}'
    return f'rules:\n  - id: no-debug\n    paths: ["**/*.py"]\n    check: \'{check}\'\n    severity: blocking\n'


# --- git.py ---

def test_install_hook_roundtrip(tmp_path):
    (tmp_path / ".git").mkdir()
    ok, _ = git.install_hook(tmp_path)
    hook = tmp_path / ".git" / "hooks" / "pre-commit"
    assert ok and hook.exists() and "becwright" in hook.read_text(encoding="utf-8")
    assert git.install_hook(tmp_path)[0] is False  # idempotent
    assert git.uninstall_hook(tmp_path)[0] is True
    assert not hook.exists()


def test_install_refuses_foreign_hook(tmp_path):
    hooks = tmp_path / ".git" / "hooks"
    hooks.mkdir(parents=True)
    (hooks / "pre-commit").write_text("#!/bin/sh\necho hi\n", encoding="utf-8")
    assert git.install_hook(tmp_path)[0] is False
    assert git.uninstall_hook(tmp_path)[0] is False


def test_uninstall_when_no_hook(tmp_path):
    (tmp_path / ".git").mkdir()
    assert git.uninstall_hook(tmp_path)[0] is False


def test_repo_root_and_files_to_check(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    (tmp_path / "a.py").write_text("x = 1\n", encoding="utf-8")
    _git(tmp_path, "add", "a.py")
    monkeypatch.chdir(tmp_path)
    root = git.repo_root()
    assert Path(root).samefile(tmp_path)
    assert "a.py" in git.files_to_check(root, all_files=False)
    assert "a.py" in git.files_to_check(root, all_files=True)


def test_repo_root_outside_repo(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(git.NotAGitRepo):
        git.repo_root()


# --- cli.py ---

def test_version_exits_zero():
    with pytest.raises(SystemExit) as e:
        cli.main(["--version"])
    assert e.value.code == 0


def test_print_result_shows_intent_why_and_pass(capsys):
    failing = Rule(id="r1", paths=("*.py",), check="false", intent="No secrets",
                   why_it_matters="they leak", severity="blocking")
    passing = Rule(id="r2", paths=("*.py",), check="true")
    res = Result(per_rule=[
        RuleResult(rule=failing, passed=False, output="  a.py:1\n      > bad"),
        RuleResult(rule=passing, passed=True, output=""),
    ])
    cli._print_result(res)
    out = capsys.readouterr().out
    assert "BLOCK" in out and "Intent:" in out and "Why it matters:" in out
    assert "a.py:1" in out and "PASS" in out


def test_print_result_omits_ansi_when_no_color_is_set(monkeypatch, capsys):
    monkeypatch.setenv("NO_COLOR", "1")
    monkeypatch.setattr(cli.sys.stdout, "isatty", lambda: True)
    rule = Rule(id="r1", paths=("*.py",), check="false", severity="blocking")
    res = Result(per_rule=[RuleResult(rule=rule, passed=False, output="")])

    cli._print_result(res)

    assert "\033[" not in capsys.readouterr().out


def test_print_result_omits_ansi_when_stdout_is_not_tty(monkeypatch, capsys):
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.setattr(cli.sys.stdout, "isatty", lambda: False)
    rule = Rule(id="r1", paths=("*.py",), check="true")
    res = Result(per_rule=[RuleResult(rule=rule, passed=True, output="")])

    cli._print_result(res)

    assert "\033[" not in capsys.readouterr().out


def test_empty_no_color_value_keeps_ansi_for_tty(monkeypatch):
    monkeypatch.setenv("NO_COLOR", "")
    monkeypatch.setattr(cli.sys.stdout, "isatty", lambda: True)

    assert "\033[" in cli._style("PASS", cli.GREEN)


def test_check_no_rules(tmp_path, monkeypatch, capsys):
    _init_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    assert cli.main(["check"]) == 0
    assert "Nothing to check" in capsys.readouterr().out


def test_check_no_staged_files(tmp_path, monkeypatch, capsys):
    _init_repo(tmp_path)
    (tmp_path / ".bec").mkdir()
    (tmp_path / ".bec" / "rules.yaml").write_text(_rules_yaml("debug_remnants"), encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    assert cli.main(["check"]) == 0
    assert "No files" in capsys.readouterr().out


def test_check_blocks_on_violation(tmp_path, monkeypatch, capsys):
    _init_repo(tmp_path)
    (tmp_path / ".bec").mkdir()
    (tmp_path / ".bec" / "rules.yaml").write_text(_rules_yaml("debug_remnants"), encoding="utf-8")
    (tmp_path / "bad.py").write_text("breakpoint()\n", encoding="utf-8")
    _git(tmp_path, "add", "bad.py")
    monkeypatch.chdir(tmp_path)
    assert cli.main(["check"]) == 1
    assert "Commit BLOCKED" in capsys.readouterr().out


def test_check_passes_clean(tmp_path, monkeypatch, capsys):
    _init_repo(tmp_path)
    (tmp_path / ".bec").mkdir()
    (tmp_path / ".bec" / "rules.yaml").write_text(_rules_yaml("debug_remnants"), encoding="utf-8")
    (tmp_path / "ok.py").write_text("x = 1\n", encoding="utf-8")
    _git(tmp_path, "add", "ok.py")
    monkeypatch.chdir(tmp_path)
    assert cli.main(["check"]) == 0
    assert "All good" in capsys.readouterr().out


def test_check_reports_invalid_rules_file_cleanly(tmp_path, monkeypatch, capsys):
    _init_repo(tmp_path)
    (tmp_path / ".bec").mkdir()
    (tmp_path / ".bec" / "rules.yaml").write_text(
        'rules:\n  - id: r1\n    check: "true"\n    severity: bloqueante\n', encoding="utf-8")
    (tmp_path / "a.py").write_text("x = 1\n", encoding="utf-8")
    _git(tmp_path, "add", "a.py")
    monkeypatch.chdir(tmp_path)
    assert cli.main(["check"]) == 2
    assert "invalid severity" in capsys.readouterr().err


def test_main_install_uninstall(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    assert cli.main(["install"]) == 0
    assert (tmp_path / ".git" / "hooks" / "pre-commit").exists()
    assert cli.main(["uninstall"]) == 0


def test_main_outside_repo_returns_2(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert cli.main(["install"]) == 2


# --- the run subcommand ---

def test_run_forwards_pattern_and_blocks(tmp_path, monkeypatch, capsys):
    import io
    f = tmp_path / "app.js"
    f.write_text("  debugger;\n", encoding="utf-8")
    monkeypatch.setattr("sys.stdin", io.StringIO(str(f) + "\n"))
    assert cli.main(["run", "forbid", "--pattern", r"\bdebugger\b"]) == 1
    assert str(f) in capsys.readouterr().out


def test_run_no_arg_check_reads_stdin(tmp_path, monkeypatch):
    import io
    f = tmp_path / "bad.py"
    f.write_text("breakpoint()\n", encoding="utf-8")
    monkeypatch.setattr("sys.stdin", io.StringIO(str(f) + "\n"))
    assert cli.main(["run", "debug_remnants"]) == 1


def test_run_unknown_check_returns_2(monkeypatch):
    import io
    monkeypatch.setattr("sys.stdin", io.StringIO(""))
    assert cli.main(["run", "nope_check"]) == 2


# --- the demo subcommand ---

def test_demo_blocks_with_both_rules(tmp_path, monkeypatch, capsys):
    # No git repo and no .bec here: demo must work anywhere, with zero setup.
    monkeypatch.chdir(tmp_path)
    assert cli.main(["demo"]) == 0
    out = capsys.readouterr().out
    assert "Commit BLOCKED" in out
    assert "no-hardcoded-secrets" in out and "no-dangerous-eval" in out
    assert "becwright init" in out


def test_demo_does_not_touch_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cli.main(["demo"])
    assert list(tmp_path.iterdir()) == []  # the sandbox is temporary and cleaned up


def test_demo_result_flags_both_violations(tmp_path):
    demo_file = tmp_path / cli._DEMO_FILENAME
    demo_file.write_text(cli._DEMO_CODE, encoding="utf-8")
    res = cli._demo_result(demo_file, cli._DEMO_FILENAME)
    assert [r.passed for r in res.per_rule] == [False, False]
    assert res.had_blocking


# --- the mcp subcommand ---

def test_mcp_subcommand_without_extra(monkeypatch):
    # Simulate the 'mcp' extra not being installed: force the import to fail.
    monkeypatch.setitem(sys.modules, "becwright.mcp_server", None)
    assert cli.main(["mcp"]) == 2
