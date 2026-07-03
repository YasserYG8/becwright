import subprocess

from becwright import cli, git


def _git(root, *args):
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True)


def _init_repo(path):
    _git(path, "init")
    _git(path, "config", "user.email", "t@t.t")
    _git(path, "config", "user.name", "t")
    return path


def _write_rules(root, body):
    bec = root / ".bec"
    bec.mkdir(exist_ok=True)
    (bec / "rules.yaml").write_text(body, encoding="utf-8")


_VALID = """\
rules:
  - id: no-eval
    paths: ["**/*.py"]
    check: "becwright run dangerous_eval"
    severity: blocking
"""

_UNKNOWN_CHECK = """\
rules:
  - id: bad
    paths: ["**/*.py"]
    check: "becwright run not_a_real_check"
"""

_DUPLICATE_IDS = """\
rules:
  - id: twice
    paths: ["**/*.py"]
    check: "becwright run dangerous_eval"
  - id: twice
    paths: ["**/*.js"]
    check: "becwright run dangerous_eval"
"""

_PATHLESS = """\
rules:
  - id: floats-free
    check: "becwright run dangerous_eval"
"""


# --- validate ---

def test_validate_ok(tmp_path, monkeypatch, capsys):
    _init_repo(tmp_path)
    _write_rules(tmp_path, _VALID)
    monkeypatch.chdir(tmp_path)
    assert cli.main(["validate"]) == 0
    assert "1 rule(s) valid" in capsys.readouterr().out


def test_validate_missing_rules_file(tmp_path, monkeypatch, capsys):
    _init_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    assert cli.main(["validate"]) == 2
    assert "becwright init" in capsys.readouterr().err


def test_validate_unknown_builtin_check(tmp_path, monkeypatch, capsys):
    _init_repo(tmp_path)
    _write_rules(tmp_path, _UNKNOWN_CHECK)
    monkeypatch.chdir(tmp_path)
    assert cli.main(["validate"]) == 2
    assert "not_a_real_check" in capsys.readouterr().err


def test_validate_duplicate_ids(tmp_path, monkeypatch, capsys):
    _init_repo(tmp_path)
    _write_rules(tmp_path, _DUPLICATE_IDS)
    monkeypatch.chdir(tmp_path)
    assert cli.main(["validate"]) == 2
    assert "duplicate rule id 'twice'" in capsys.readouterr().err


def test_validate_bad_yaml_exits_2(tmp_path, monkeypatch, capsys):
    _init_repo(tmp_path)
    _write_rules(tmp_path, "rules: [\n")
    monkeypatch.chdir(tmp_path)
    assert cli.main(["validate"]) == 2


def test_validate_warns_on_pathless_rule_but_passes(tmp_path, monkeypatch, capsys):
    _init_repo(tmp_path)
    _write_rules(tmp_path, _PATHLESS)
    monkeypatch.chdir(tmp_path)
    assert cli.main(["validate"]) == 0
    assert "never" in capsys.readouterr().out


# --- doctor ---

def test_doctor_healthy_repo(tmp_path, monkeypatch, capsys):
    _init_repo(tmp_path)
    _write_rules(tmp_path, _VALID)
    git.install_hook(tmp_path)
    monkeypatch.chdir(tmp_path)
    assert cli.main(["doctor"]) == 0
    out = capsys.readouterr().out
    assert "1 rule(s)" in out
    assert "pre-commit hook installed" in out
    assert "All good" in out


def test_doctor_missing_rules_warns(tmp_path, monkeypatch, capsys):
    _init_repo(tmp_path)
    git.install_hook(tmp_path)
    monkeypatch.chdir(tmp_path)
    assert cli.main(["doctor"]) == 0
    assert "becwright init" in capsys.readouterr().out


def test_doctor_unknown_check_fails(tmp_path, monkeypatch, capsys):
    _init_repo(tmp_path)
    _write_rules(tmp_path, _UNKNOWN_CHECK)
    git.install_hook(tmp_path)
    monkeypatch.chdir(tmp_path)
    assert cli.main(["doctor"]) == 2
    assert "not_a_real_check" in capsys.readouterr().out


def test_doctor_missing_hook_warns(tmp_path, monkeypatch, capsys):
    _init_repo(tmp_path)
    _write_rules(tmp_path, _VALID)
    monkeypatch.chdir(tmp_path)
    assert cli.main(["doctor"]) == 0
    assert "becwright install" in capsys.readouterr().out


def test_doctor_foreign_hook_warns(tmp_path, monkeypatch, capsys):
    _init_repo(tmp_path)
    _write_rules(tmp_path, _VALID)
    hooks = tmp_path / ".git" / "hooks"
    hooks.mkdir(parents=True, exist_ok=True)
    (hooks / "pre-commit").write_text("#!/bin/sh\necho hi\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    assert cli.main(["doctor"]) == 0
    assert "non-becwright" in capsys.readouterr().out


def test_doctor_hooks_path_override_warns(tmp_path, monkeypatch, capsys):
    _init_repo(tmp_path)
    _write_rules(tmp_path, _VALID)
    _git(tmp_path, "config", "core.hooksPath", ".custom-hooks")
    monkeypatch.chdir(tmp_path)
    assert cli.main(["doctor"]) == 0
    assert "core.hooksPath" in capsys.readouterr().out


def test_doctor_husky_with_becwright_is_ok(tmp_path, monkeypatch, capsys):
    _init_repo(tmp_path)
    _write_rules(tmp_path, _VALID)
    _git(tmp_path, "config", "core.hooksPath", ".husky/_")
    husky = tmp_path / ".husky"
    husky.mkdir()
    (husky / "pre-commit").write_text("npx becwright check\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    assert cli.main(["doctor"]) == 0
    assert "Husky runs becwright" in capsys.readouterr().out


def test_doctor_husky_without_becwright_warns(tmp_path, monkeypatch, capsys):
    _init_repo(tmp_path)
    _write_rules(tmp_path, _VALID)
    _git(tmp_path, "config", "core.hooksPath", ".husky/_")
    husky = tmp_path / ".husky"
    husky.mkdir()
    (husky / "pre-commit").write_text("npm test\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    assert cli.main(["doctor"]) == 0
    assert "npx becwright check" in capsys.readouterr().out


def test_doctor_precommit_framework_with_becwright_is_ok(tmp_path, monkeypatch, capsys):
    _init_repo(tmp_path)
    _write_rules(tmp_path, _VALID)
    hooks = tmp_path / ".git" / "hooks"
    hooks.mkdir(parents=True, exist_ok=True)
    (hooks / "pre-commit").write_text("#!/bin/sh\n# by pre-commit\n", encoding="utf-8")
    (tmp_path / ".pre-commit-config.yaml").write_text(
        "repos:\n  - repo: https://github.com/DataDave-Dev/becwright\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    assert cli.main(["doctor"]) == 0
    assert "pre-commit framework runs becwright" in capsys.readouterr().out


def test_doctor_commit_msg_rules_without_hook_warns(tmp_path, monkeypatch, capsys):
    _init_repo(tmp_path)
    _write_rules(tmp_path, """\
rules:
  - id: conv-commits
    target: commit-msg
    check: "becwright run require --pattern '^feat'"
""")
    git.install_hook(tmp_path)
    monkeypatch.chdir(tmp_path)
    assert cli.main(["doctor"]) == 0
    assert "commit-msg" in capsys.readouterr().out


def test_doctor_outside_git_repo(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert cli.main(["doctor"]) == 2


# --- git.py helpers ---

def test_hook_state(tmp_path):
    (tmp_path / ".git").mkdir()
    assert git.hook_state(tmp_path) == "missing"
    git.install_hook(tmp_path)
    assert git.hook_state(tmp_path) == "becwright"
    hook = tmp_path / ".git" / "hooks" / "pre-commit"
    hook.write_text("#!/bin/sh\necho custom\n", encoding="utf-8")
    assert git.hook_state(tmp_path) == "foreign"


def test_hooks_path_override(tmp_path):
    _init_repo(tmp_path)
    assert git.hooks_path_override(tmp_path) is None
    _git(tmp_path, "config", "core.hooksPath", ".husky/_")
    assert git.hooks_path_override(tmp_path) == ".husky/_"


def test_hook_manager(tmp_path):
    assert git.hook_manager(tmp_path) is None
    (tmp_path / ".pre-commit-config.yaml").write_text("repos: []\n", encoding="utf-8")
    assert git.hook_manager(tmp_path) == "pre-commit"
    (tmp_path / ".husky").mkdir()
    assert git.hook_manager(tmp_path) == "husky"  # husky wins when both exist
