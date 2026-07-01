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


def _repo(path):
    _git(path, "init")
    _git(path, "config", "user.email", "t@t.t")
    _git(path, "config", "user.name", "t")
    return path


def test_tools_registered():
    tools = asyncio.run(mcp_server.mcp.list_tools())
    assert {t.name for t in tools} == {
        "check", "list_checks", "list_rules", "preview_rule",
        "propose_rules_from_claude_md", "add_rule",
    }


def test_list_checks_tool_returns_all_builtins():
    names = [c["name"] for c in mcp_server.list_checks()]
    assert "forbid" in names and "hardcoded_secrets" in names
    assert names == sorted(names)


def test_list_rules_tool_returns_decision_records(tmp_path):
    _repo_with_rule(tmp_path)
    records = mcp_server.list_rules(path=str(tmp_path))
    assert [r["id"] for r in records] == ["no-bp"]
    assert records[0]["severity"] == "blocking" and "check" in records[0]


def test_list_rules_tool_empty_when_no_rules(tmp_path):
    _repo(tmp_path)
    assert mcp_server.list_rules(path=str(tmp_path)) == []


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


def test_preview_rule_reports_violations(tmp_path):
    _repo(tmp_path)
    (tmp_path / "a.py").write_text("breakpoint()\n", encoding="utf-8")
    _git(tmp_path, "add", "a.py")
    out = mcp_server.preview_rule(
        check=f'PYTHONPATH="{_SRC}" python -m becwright.checks.forbid --pattern breakpoint',
        paths=["**/*.py"], all_files=True, path=str(tmp_path))
    assert out["matched_files"] == 1 and out["passed"] is False
    assert "a.py" in out["output"] and out["note"] is None


def test_preview_rule_passes_clean(tmp_path):
    _repo(tmp_path)
    (tmp_path / "a.py").write_text("x = 1\n", encoding="utf-8")
    _git(tmp_path, "add", "a.py")
    out = mcp_server.preview_rule(
        check=f'PYTHONPATH="{_SRC}" python -m becwright.checks.forbid --pattern breakpoint',
        paths=["**/*.py"], path=str(tmp_path))
    assert out["passed"] is True and out["matched_files"] == 1


def test_preview_rule_warns_on_no_match(tmp_path):
    _repo(tmp_path)
    (tmp_path / "a.py").write_text("x = 1\n", encoding="utf-8")
    _git(tmp_path, "add", "a.py")
    out = mcp_server.preview_rule(check="becwright run forbid --pattern x",
                                  paths=["**/*.rs"], path=str(tmp_path))
    assert out["matched_files"] == 0 and "matches no files" in out["note"]


def test_preview_rule_flags_unknown_check(tmp_path):
    _repo(tmp_path)
    (tmp_path / "a.py").write_text("x = 1\n", encoding="utf-8")
    _git(tmp_path, "add", "a.py")
    out = mcp_server.preview_rule(check="becwright run ghost_check",
                                  paths=["**/*.py"], path=str(tmp_path))
    assert out["passed"] is False and "not a built-in check" in out["note"]


def test_propose_rules_from_claude_md(tmp_path):
    _repo(tmp_path)
    (tmp_path / "svc.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "CLAUDE.md").write_text(
        "Never hardcode secrets. Keep files under 800 lines.\n", encoding="utf-8")
    out = mcp_server.propose_rules_from_claude_md(path=str(tmp_path))
    ids = {r["id"] for r in out["rules"]}
    assert "no-hardcoded-secrets" in ids and "max-file-lines" in ids
    assert all(r["matched"] for r in out["rules"])   # each rule keeps its trigger phrase
    assert "unmapped_hint" in out


def test_propose_rules_without_claude_md(tmp_path):
    _repo(tmp_path)
    (tmp_path / "a.py").write_text("x = 1\n", encoding="utf-8")
    out = mcp_server.propose_rules_from_claude_md(path=str(tmp_path))
    assert out["rules"] == [] and "No CLAUDE.md" in out["note"]


def test_add_rule_preview_does_not_write(tmp_path):
    _repo(tmp_path)
    out = mcp_server.add_rule(id="no-dbg", check="becwright run debug_remnants",
                              paths=["**/*.py"], path=str(tmp_path))
    assert out["ok"] is False and out["pending_confirmation"] is True
    assert out["rule"]["id"] == "no-dbg"
    assert not (tmp_path / ".bec" / "rules.yaml").exists()


def test_add_rule_confirm_writes(tmp_path):
    from becwright.rules import load_rules
    _repo(tmp_path)
    out = mcp_server.add_rule(id="no-dbg", check="becwright run debug_remnants",
                              paths=["**/*.py"], intent="No breakpoints",
                              confirm=True, path=str(tmp_path))
    assert out["ok"] is True and out["rule_id"] == "no-dbg"
    rules = load_rules(tmp_path / ".bec" / "rules.yaml")
    assert [r.id for r in rules] == ["no-dbg"] and rules[0].intent == "No breakpoints"


def test_add_rule_rejects_duplicate_id(tmp_path):
    _repo(tmp_path)
    mcp_server.add_rule(id="no-dbg", check="becwright run debug_remnants",
                        paths=["**/*.py"], confirm=True, path=str(tmp_path))
    out = mcp_server.add_rule(id="no-dbg", check="becwright run dangerous_eval",
                              paths=["**/*.py"], confirm=True, path=str(tmp_path))
    assert out["ok"] is False and "already exists" in out["error"]


def test_add_rule_accepts_advisory_severity(tmp_path):
    from becwright.rules import load_rules
    _repo(tmp_path)
    out = mcp_server.add_rule(id="adv", check="becwright run debug_remnants",
                              paths=["**/*.py"], severity="advisory",
                              confirm=True, path=str(tmp_path))
    assert out["ok"] is True
    assert load_rules(tmp_path / ".bec" / "rules.yaml")[0].is_advisory is True


def test_add_rule_rejects_non_builtin_check(tmp_path):
    _repo(tmp_path)
    out = mcp_server.add_rule(id="grep-todo", check="grep -r TODO .",
                              paths=["**/*.py"], confirm=True, path=str(tmp_path))
    assert out["ok"] is False and "built-in" in out["error"]
    assert not (tmp_path / ".bec" / "rules.yaml").exists()


def test_add_rule_rejects_unknown_builtin(tmp_path):
    _repo(tmp_path)
    out = mcp_server.add_rule(id="ghost", check="becwright run ghost_check",
                              paths=["**/*.py"], confirm=True, path=str(tmp_path))
    assert out["ok"] is False and "not a built-in check" in out["error"]


def test_add_rule_rejects_empty_paths_and_bad_severity(tmp_path):
    _repo(tmp_path)
    assert mcp_server.add_rule(id="r", check="becwright run debug_remnants",
                               paths=[], path=str(tmp_path))["ok"] is False
    assert mcp_server.add_rule(id="r", check="becwright run debug_remnants",
                               paths=["**/*.py"], severity="bloqueante",
                               path=str(tmp_path))["ok"] is False
