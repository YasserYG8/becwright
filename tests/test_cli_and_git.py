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
    src_posix = _SRC.as_posix()
    check = f'"{sys.executable}" -c "import sys; sys.path.insert(0, \'{src_posix}\'); from becwright.checks.{module} import main; sys.exit(main())"'
    return f'rules:\n  - id: no-debug\n    paths: ["**/*.py"]\n    check: |-\n      {check}\n    severity: blocking\n'


# --- git.py ---

def test_install_hook_roundtrip(tmp_path):
    (tmp_path / ".git").mkdir()
    ok, _ = git.install_hook(tmp_path)
    hook = tmp_path / ".git" / "hooks" / "pre-commit"
    assert ok and hook.exists() and "becwright" in hook.read_text(encoding="utf-8")
    assert git.install_hook(tmp_path)[0] is False  # idempotent
    assert git.uninstall_hook(tmp_path)[0] is True
    assert not hook.exists()


def test_msg_hook_roundtrip(tmp_path):
    (tmp_path / ".git").mkdir()
    ok, _ = git.install_msg_hook(tmp_path)
    hook = tmp_path / ".git" / "hooks" / "commit-msg"
    assert ok and hook.exists() and "check-msg" in hook.read_text(encoding="utf-8")
    assert git.install_msg_hook(tmp_path)[0] is False  # idempotent
    assert git.uninstall_msg_hook(tmp_path)[0] is True
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


def test_print_result_advisory_label(capsys):
    adv = Rule(id="design", paths=("*.py",), check="x", severity="advisory",
               intent="Readable code")
    res = Result(per_rule=[RuleResult(rule=adv, passed=False, output="  looks off")])
    cli._print_result(res)
    out = capsys.readouterr().out
    assert "ADVISORY" in out and "BLOCK" not in out and "looks off" in out


def test_check_advisory_never_blocks(tmp_path, monkeypatch, capsys):
    _init_repo(tmp_path)
    (tmp_path / ".bec").mkdir()
    # `false` always "fails"; an advisory rule must report but not block the commit.
    (tmp_path / ".bec" / "rules.yaml").write_text(
        f"rules:\n  - id: adv\n    paths: ['**/*.py']\n    check: '\"{sys.executable}\" -c \"import sys; sys.exit(1)\"'\n    severity: advisory\n",
        encoding="utf-8")
    (tmp_path / "a.py").write_text("x = 1\n", encoding="utf-8")
    _git(tmp_path, "add", "a.py")
    monkeypatch.chdir(tmp_path)
    assert cli.main(["check"]) == 0
    out = capsys.readouterr().out
    assert "ADVISORY" in out and "All good" in out


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


def test_unknown_builtin_checks_helper(tmp_path):
    rules = [
        Rule(id="ok", paths=("*.py",), check="becwright run debug_remnants"),
        Rule(id="bad", paths=("*.py",), check="becwright run ghost"),
        Rule(id="cmd", paths=("*.py",), check="grep -r TODO ."),  # opaque command, left alone
    ]
    assert cli._unknown_builtin_checks(rules, tmp_path) == [("bad", "ghost")]


def test_check_flags_unknown_builtin_check(tmp_path, monkeypatch, capsys):
    _init_repo(tmp_path)
    (tmp_path / ".bec").mkdir()
    (tmp_path / ".bec" / "rules.yaml").write_text(
        'rules:\n  - id: r1\n    paths: ["**/*.py"]\n'
        "    check: 'becwright run no_such_check'\n    severity: blocking\n", encoding="utf-8")
    (tmp_path / "a.py").write_text("x = 1\n", encoding="utf-8")
    _git(tmp_path, "add", "a.py")
    monkeypatch.chdir(tmp_path)
    assert cli.main(["check"]) == 2
    err = capsys.readouterr().err
    assert "no_such_check" in err and "becwright list" in err


def test_check_does_not_flag_opaque_command(tmp_path, monkeypatch, capsys):
    _init_repo(tmp_path)
    (tmp_path / ".bec").mkdir()
    (tmp_path / ".bec" / "rules.yaml").write_text(
        'rules:\n  - id: r1\n    paths: ["**/*.py"]\n'
        f"    check: '\"{sys.executable}\" -c \"import sys; sys.exit(0)\"'\n    severity: blocking\n", encoding="utf-8")
    (tmp_path / "a.py").write_text("x = 1\n", encoding="utf-8")
    _git(tmp_path, "add", "a.py")
    monkeypatch.chdir(tmp_path)
    assert cli.main(["check"]) == 0
    assert "All good" in capsys.readouterr().out


def test_main_install_uninstall(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    assert cli.main(["install"]) == 0
    hooks = tmp_path / ".git" / "hooks"
    assert (hooks / "pre-commit").exists() and (hooks / "commit-msg").exists()
    assert cli.main(["uninstall"]) == 0
    assert not (hooks / "pre-commit").exists() and not (hooks / "commit-msg").exists()


def test_check_msg_blocks_bad_message(tmp_path, monkeypatch, capsys):
    _init_repo(tmp_path)
    (tmp_path / ".bec").mkdir()
    (tmp_path / ".bec" / "rules.yaml").write_text(
        "rules:\n  - id: conv\n    target: commit-msg\n"
        "    check: 'becwright run require --pattern \"^(feat|fix): \"'\n    severity: blocking\n",
        encoding="utf-8")
    msg = tmp_path / "MSG"
    msg.write_text("update stuff\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    assert cli.main(["check-msg", str(msg)]) == 1
    assert "Commit BLOCKED" in capsys.readouterr().out


def test_check_msg_passes_good_message(tmp_path, monkeypatch, capsys):
    _init_repo(tmp_path)
    (tmp_path / ".bec").mkdir()
    (tmp_path / ".bec" / "rules.yaml").write_text(
        "rules:\n  - id: conv\n    target: commit-msg\n"
        "    check: 'becwright run require --pattern \"^(feat|fix): \"'\n    severity: blocking\n",
        encoding="utf-8")
    msg = tmp_path / "MSG"
    msg.write_text("feat: add the thing\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    assert cli.main(["check-msg", str(msg)]) == 0
    assert "message OK" in capsys.readouterr().out


def test_check_msg_no_message_rules_is_noop(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    (tmp_path / ".bec").mkdir()
    (tmp_path / ".bec" / "rules.yaml").write_text(
        f"rules:\n  - id: f\n    paths: ['**/*.py']\n    check: '\"{sys.executable}\" -c \"import sys; sys.exit(0)\"'\n    severity: blocking\n",
        encoding="utf-8")
    msg = tmp_path / "MSG"
    msg.write_text("anything\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    assert cli.main(["check-msg", str(msg)]) == 0


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


# --- diff mode (CI / PR): only the files a branch changed ---

def _current_branch(root):
    return subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=root, capture_output=True, text=True,
    ).stdout.strip()


def _branch_with_change(tmp_path):
    """Base commit with old.py, then a `feature` branch adding new.py. Returns the
    base branch name to diff against."""
    _init_repo(tmp_path)
    (tmp_path / "old.py").write_text("x = 1\n", encoding="utf-8")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-m", "base")
    base = _current_branch(tmp_path)
    _git(tmp_path, "checkout", "-b", "feature")
    return base


def test_files_to_check_diff_base_returns_only_changed(tmp_path):
    base = _branch_with_change(tmp_path)
    (tmp_path / "new.py").write_text("y = 2\n", encoding="utf-8")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-m", "feature")
    assert git.files_to_check(tmp_path, diff_base=base) == ["new.py"]


def test_files_to_check_diff_base_unknown_ref_raises(tmp_path):
    _init_repo(tmp_path)
    (tmp_path / "a.py").write_text("x = 1\n", encoding="utf-8")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-m", "c")
    with pytest.raises(git.GitError):
        git.files_to_check(tmp_path, diff_base="origin/does-not-exist")


def test_check_diff_blocks_on_changed_file(tmp_path, monkeypatch, capsys):
    base = _branch_with_change(tmp_path)
    (tmp_path / ".bec").mkdir()
    (tmp_path / ".bec" / "rules.yaml").write_text(_rules_yaml("debug_remnants"), encoding="utf-8")
    (tmp_path / "bad.py").write_text("breakpoint()\n", encoding="utf-8")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-m", "feature")
    monkeypatch.chdir(tmp_path)
    assert cli.main(["check", "--diff", base]) == 1
    assert "Commit BLOCKED" in capsys.readouterr().out


def test_check_diff_ignores_violation_outside_the_diff(tmp_path, monkeypatch, capsys):
    # A pre-existing violation on the base must not fail CI: --diff only checks what
    # the branch actually changed, so a clean change passes regardless of old debt.
    _init_repo(tmp_path)
    (tmp_path / ".bec").mkdir()
    (tmp_path / ".bec" / "rules.yaml").write_text(_rules_yaml("debug_remnants"), encoding="utf-8")
    (tmp_path / "legacy.py").write_text("breakpoint()\n", encoding="utf-8")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-m", "base")
    base = _current_branch(tmp_path)
    _git(tmp_path, "checkout", "-b", "feature")
    (tmp_path / "feature.py").write_text("z = 3\n", encoding="utf-8")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-m", "feature")
    monkeypatch.chdir(tmp_path)
    assert cli.main(["check", "--diff", base]) == 0
    assert "All good" in capsys.readouterr().out


def test_check_all_and_diff_are_mutually_exclusive():
    with pytest.raises(SystemExit):
        cli.main(["check", "--all", "--diff", "main"])


# --- the why subcommand (decision memory) ---

_WHY_RULES = """\
rules:
  - id: no-eval
    intent: "Avoid eval and exec."
    why_it_matters: "Arbitrary code execution is a security hole."
    rejected_alternatives:
      - "sandboxing eval"
    paths: ["**/*.py"]
    exclude: ["tests/**"]
    check: "becwright run dangerous_eval"
    severity: blocking
  - id: conv
    target: commit-msg
    intent: "Use Conventional Commits."
    check: 'becwright run require --pattern "^feat: "'
    severity: warning
"""


def _write_why_rules(tmp_path):
    (tmp_path / ".bec").mkdir()
    (tmp_path / ".bec" / "rules.yaml").write_text(_WHY_RULES, encoding="utf-8")


def test_why_lists_all_rules(tmp_path, monkeypatch, capsys):
    _init_repo(tmp_path)
    _write_why_rules(tmp_path)
    monkeypatch.chdir(tmp_path)
    assert cli.main(["why"]) == 0
    out = capsys.readouterr().out
    assert "no-eval" in out and "conv" in out
    assert "Avoid eval and exec." in out


def test_why_detail_shows_full_record(tmp_path, monkeypatch, capsys):
    _init_repo(tmp_path)
    _write_why_rules(tmp_path)
    monkeypatch.chdir(tmp_path)
    assert cli.main(["why", "no-eval"]) == 0
    out = capsys.readouterr().out
    assert "Intent:" in out and "Why it matters:" in out
    assert "Rejected alternatives:" in out and "sandboxing eval" in out
    assert "dangerous_eval" in out and "tests/**" in out


def test_why_commit_msg_rule_applies_to_message(tmp_path, monkeypatch, capsys):
    _init_repo(tmp_path)
    _write_why_rules(tmp_path)
    monkeypatch.chdir(tmp_path)
    assert cli.main(["why", "conv"]) == 0
    assert "the commit message" in capsys.readouterr().out


def test_why_unknown_id_returns_1_and_lists_ids(tmp_path, monkeypatch, capsys):
    _init_repo(tmp_path)
    _write_why_rules(tmp_path)
    monkeypatch.chdir(tmp_path)
    assert cli.main(["why", "ghost"]) == 1
    err = capsys.readouterr().err
    assert "ghost" in err and "no-eval" in err


def test_why_json_lists_all(tmp_path, monkeypatch, capsys):
    import json
    _init_repo(tmp_path)
    _write_why_rules(tmp_path)
    monkeypatch.chdir(tmp_path)
    assert cli.main(["why", "--json"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert [r["id"] for r in data["rules"]] == ["no-eval", "conv"]
    assert data["rules"][0]["why_it_matters"].startswith("Arbitrary code execution")


def test_why_json_single_rule(tmp_path, monkeypatch, capsys):
    import json
    _init_repo(tmp_path)
    _write_why_rules(tmp_path)
    monkeypatch.chdir(tmp_path)
    assert cli.main(["why", "no-eval", "--json"]) == 0
    rec = json.loads(capsys.readouterr().out)
    assert rec["id"] == "no-eval" and rec["rejected_alternatives"] == ["sandboxing eval"]


def test_why_no_rules_is_friendly(tmp_path, monkeypatch, capsys):
    _init_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    assert cli.main(["why"]) == 0
    assert "No .bec/rules.yaml" in capsys.readouterr().out


# --- the mcp subcommand ---

def test_mcp_subcommand_without_extra(monkeypatch):
    # Simulate the 'mcp' extra not being installed: force the import to fail.
    monkeypatch.setitem(sys.modules, "becwright.mcp_server", None)
    assert cli.main(["mcp"]) == 2
