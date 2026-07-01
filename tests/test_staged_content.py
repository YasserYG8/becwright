import subprocess
import sys
from pathlib import Path

from becwright import cli

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


def _setup(tmp_path):
    _init_repo(tmp_path)
    (tmp_path / ".bec").mkdir()
    (tmp_path / ".bec" / "rules.yaml").write_text(_rules_yaml("debug_remnants"), encoding="utf-8")


def test_check_uses_staged_content_not_working_tree(tmp_path, monkeypatch, capsys):
    # Staged version is clean; an unstaged edit adds a violation. The commit will
    # record the clean staged blob, so the check must PASS.
    _setup(tmp_path)
    (tmp_path / "app.py").write_text("x = 1\n", encoding="utf-8")
    _git(tmp_path, "add", "app.py")
    (tmp_path / "app.py").write_text("breakpoint()\n", encoding="utf-8")  # unstaged
    monkeypatch.chdir(tmp_path)
    assert cli.main(["check"]) == 0
    assert "All good" in capsys.readouterr().out


def test_check_blocks_on_staged_violation_hidden_by_clean_working_tree(tmp_path, monkeypatch, capsys):
    # The reverse: the violation is staged, a later unstaged edit cleans it. The
    # commit would still record the bad staged blob, so the check must BLOCK.
    _setup(tmp_path)
    (tmp_path / "app.py").write_text("breakpoint()\n", encoding="utf-8")
    _git(tmp_path, "add", "app.py")
    (tmp_path / "app.py").write_text("x = 1\n", encoding="utf-8")  # unstaged clean-up
    monkeypatch.chdir(tmp_path)
    assert cli.main(["check"]) == 1
    assert "Commit BLOCKED" in capsys.readouterr().out
