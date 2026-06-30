import asyncio
import subprocess
from pathlib import Path

import pytest

pytest.importorskip("mcp")

from becwright import mcp_server  # noqa: E402

_SRC = Path(__file__).resolve().parents[1] / "src"


def _git(root, *args):
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True)


def _repo_with_rule(path):
    _git(path, "init")
    _git(path, "config", "user.email", "t@t.t")
    _git(path, "config", "user.name", "t")
    check = f'PYTHONPATH="{_SRC}" python -m becwright.checks.forbid --pattern "breakpoint"'
    (path / ".bec").mkdir(parents=True)
    (path / ".bec" / "rules.yaml").write_text(
        "rules:\n  - id: no-bp\n    paths: ['**/*.py']\n"
        f"    check: '{check}'\n    severity: blocking\n", encoding="utf-8")
    return path


def test_tools_registered():
    tools = asyncio.run(mcp_server.mcp.list_tools())
    assert {t.name for t in tools} == {"check", "list_checks"}


def test_list_checks_tool_returns_all_builtins():
    names = [c["name"] for c in mcp_server.list_checks()]
    assert "forbid" in names and "hardcoded_secrets" in names
    assert names == sorted(names)


def test_check_tool_reports_block(tmp_path):
    _repo_with_rule(tmp_path)
    (tmp_path / "a.py").write_text("breakpoint()\n", encoding="utf-8")
    _git(tmp_path, "add", "a.py")
    out = mcp_server.check(all_files=True, path=str(tmp_path))
    assert out["blocked"] is True
    assert out["results"][0]["id"] == "no-bp" and out["results"][0]["passed"] is False


def test_check_tool_clean_repo(tmp_path):
    _repo_with_rule(tmp_path)
    (tmp_path / "ok.py").write_text("x = 1\n", encoding="utf-8")
    _git(tmp_path, "add", "ok.py")
    out = mcp_server.check(all_files=True, path=str(tmp_path))
    assert out["blocked"] is False
