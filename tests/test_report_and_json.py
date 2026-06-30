import json
import subprocess
from pathlib import Path

from becwright import cli, report
from becwright.rules import Rule
from becwright.engine import evaluate

_SRC = Path(__file__).resolve().parents[1] / "src"


def _git(root, *args):
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True)


def _init_repo(path):
    _git(path, "init")
    _git(path, "config", "user.email", "t@t.t")
    _git(path, "config", "user.name", "t")
    return path


def _rule_yaml(tmp_path):
    check = f'PYTHONPATH="{_SRC}" python -m becwright.checks.forbid --pattern "\\bdebugger\\b"'
    (tmp_path / ".bec").mkdir(parents=True, exist_ok=True)
    (tmp_path / ".bec" / "rules.yaml").write_text(
        "rules:\n  - id: no-dbg\n    intent: no debugger\n    why_it_matters: it halts\n"
        f"    paths: ['**/*.js']\n    check: '{check}'\n    severity: blocking\n",
        encoding="utf-8")


# --- report.gather ---

def test_gather_none_when_no_rules(tmp_path):
    _init_repo(tmp_path)
    rules, files, result = report.gather(tmp_path, all_files=True)
    assert rules == [] and result is None


def test_gather_none_when_no_files(tmp_path):
    _init_repo(tmp_path)
    _rule_yaml(tmp_path)
    rules, files, result = report.gather(tmp_path, all_files=True)
    assert rules and files == [] and result is None


# --- report.payload ---

def test_payload_reports_blocking_violation():
    rule = Rule(id="no-dbg", paths=("**/*.js",), check="false",
                intent="no debugger", why_it_matters="it halts", severity="blocking")
    from becwright.engine import Result, RuleResult
    result = Result(per_rule=[RuleResult(rule=rule, passed=False, output="app.js:1")])
    out = report.payload([rule], ["app.js"], result)
    assert out["blocked"] is True
    assert out["checked_files"] == 1 and out["rule_count"] == 1
    entry = out["results"][0]
    assert entry == {"id": "no-dbg", "severity": "blocking", "passed": False,
                     "intent": "no debugger", "why_it_matters": "it halts", "output": "app.js:1"}


def test_payload_empty_when_no_result():
    out = report.payload([], [], None)
    assert out == {"rule_count": 0, "checked_files": 0, "blocked": False, "results": []}


# --- cli: check --json ---

def test_check_json_blocks_and_is_valid_json(tmp_path, monkeypatch, capsys):
    _init_repo(tmp_path)
    _rule_yaml(tmp_path)
    (tmp_path / "app.js").write_text("  debugger;\n", encoding="utf-8")
    _git(tmp_path, "add", "app.js")
    monkeypatch.chdir(tmp_path)
    rc = cli.main(["check", "--all", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert rc == 1 and data["blocked"] is True
    assert data["results"][0]["id"] == "no-dbg"


def test_check_json_clean_repo(tmp_path, monkeypatch, capsys):
    _init_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    rc = cli.main(["check", "--all", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert rc == 0 and data["blocked"] is False and data["results"] == []
