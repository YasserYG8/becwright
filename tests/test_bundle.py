import subprocess
import sys
from pathlib import Path

import pytest

from becwright import bundle, cli
from becwright.engine import evaluate
from becwright.rules import Rule, load_rules

_SRC = Path(__file__).resolve().parents[1] / "src"

CUSTOM_CHECK = """#!/usr/bin/env python3
import sys
bad = []
for path in sys.stdin.read().splitlines():
    path = path.strip()
    if not path:
        continue
    try:
        with open(path, encoding="utf-8") as f:
            for n, line in enumerate(f, 1):
                if "XXX" in line:
                    bad.append((path, n))
    except OSError:
        pass
for path, n in bad:
    print(f"  {path}:{n}")
sys.exit(1 if bad else 0)
"""


def _git(root, *args):
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True)


def _init_repo(path):
    path.mkdir(parents=True, exist_ok=True)
    _git(path, "init")
    _git(path, "config", "user.email", "t@t.t")
    _git(path, "config", "user.name", "t")
    return path


# --- classify_check ---

def test_classify_builtin(tmp_path):
    out = bundle.classify_check("becwright run debug_remnants", tmp_path)
    assert out == {"kind": "builtin", "module": "debug_remnants"}


def test_classify_builtin_legacy_form(tmp_path):
    out = bundle.classify_check("python3 -m becwright.checks.debug_remnants", tmp_path)
    assert out == {"kind": "builtin", "module": "debug_remnants"}


def test_classify_script_embeds_source(tmp_path):
    script = tmp_path / ".bec" / "checks" / "foo.py"
    script.parent.mkdir(parents=True)
    script.write_text(CUSTOM_CHECK, encoding="utf-8")
    out = bundle.classify_check("python3 .bec/checks/foo.py", tmp_path)
    assert out["kind"] == "script"
    assert out["filename"] == "foo.py"
    assert out["source"] == CUSTOM_CHECK


def test_classify_opaque_command(tmp_path):
    out = bundle.classify_check("grep -r TODO src/", tmp_path)
    assert out == {"kind": "command", "command": "grep -r TODO src/"}


def test_classify_builtin_with_args(tmp_path):
    out = bundle.classify_check(
        r"becwright run forbid --pattern '\bdebugger\b'", tmp_path)
    assert out == {"kind": "builtin", "module": "forbid",
                   "args": r"--pattern '\bdebugger\b'"}


def test_classify_builtin_legacy_form_with_args(tmp_path):
    out = bundle.classify_check(
        r"python3 -m becwright.checks.forbid --pattern '\bdebugger\b'", tmp_path)
    assert out == {"kind": "builtin", "module": "forbid",
                   "args": r"--pattern '\bdebugger\b'"}


def test_materialize_builtin_with_args(tmp_path):
    data = {"rule": {"id": "r", "paths": ["*.js"], "severity": "blocking"},
            "check": {"kind": "builtin", "module": "forbid", "args": r"--pattern '\bx\b'"}}
    rd = bundle.materialize(data, tmp_path)
    assert rd["check"] == r"becwright run forbid --pattern '\bx\b'"


def test_roundtrip_builtin_args_preserved(tmp_path):
    rule = Rule(id="no-dbg", paths=("**/*.js",),
                check=r"becwright run forbid --pattern '\bdebugger\b'",
                severity="blocking")
    data = bundle.parse_bundle(bundle.export_bec(rule, tmp_path))
    assert data["check"]["args"] == r"--pattern '\bdebugger\b'"
    assert bundle.materialize(data, tmp_path)["check"] == rule.check


def test_legacy_check_materializes_to_new_form(tmp_path):
    rule = Rule(id="no-dbg", paths=("**/*.py",),
                check="python3 -m becwright.checks.debug_remnants",
                severity="blocking")
    data = bundle.parse_bundle(bundle.export_bec(rule, tmp_path))
    assert bundle.materialize(data, tmp_path)["check"] == "becwright run debug_remnants"


def test_catalog_bundles_are_valid(tmp_path):
    becs = Path(__file__).resolve().parents[1] / "becs"
    files = list(becs.glob("*.bec.yaml"))
    assert files, "no hay bundles en becs/"
    for f in files:
        data = bundle.parse_bundle(f.read_text(encoding="utf-8"))
        rd = bundle.materialize(data, tmp_path)
        assert rd["check"].startswith("becwright run ")


# --- export / parse ---

def test_export_builtin_roundtrips_through_parse(tmp_path):
    rule = Rule(id="no-debug", paths=("src/**/*.py",),
                check="python3 -m becwright.checks.debug_remnants",
                intent="No breakpoints", severity="blocking")
    data = bundle.parse_bundle(bundle.export_bec(rule, tmp_path))
    assert data["rule"]["id"] == "no-debug"
    assert data["check"] == {"kind": "builtin", "module": "debug_remnants"}


def test_parse_rejects_bad_version():
    with pytest.raises(bundle.BundleError):
        bundle.parse_bundle("becwright_bec: 99\nrule: {id: x}\ncheck: {kind: command}\n")


def test_parse_rejects_garbage():
    with pytest.raises(bundle.BundleError):
        bundle.parse_bundle("not a bundle")


# --- materialize / append ---

def test_materialize_builtin_command(tmp_path):
    data = {"rule": {"id": "r", "paths": ["*.py"], "severity": "blocking"},
            "check": {"kind": "builtin", "module": "debug_remnants"}}
    rule_dict = bundle.materialize(data, tmp_path)
    assert rule_dict["check"] == "becwright run debug_remnants"


def test_materialize_script_writes_file(tmp_path):
    data = {"rule": {"id": "no-xxx", "paths": ["**/*.py"], "severity": "blocking"},
            "check": {"kind": "script", "filename": "no_xxx.py", "source": CUSTOM_CHECK}}
    rule_dict = bundle.materialize(data, tmp_path)
    dest = tmp_path / ".bec" / "checks" / "no_xxx.py"
    assert dest.read_text(encoding="utf-8") == CUSTOM_CHECK
    assert rule_dict["check"] == "python3 .bec/checks/no_xxx.py"


def test_materialize_script_conflict_raises(tmp_path):
    dest = tmp_path / ".bec" / "checks" / "no_xxx.py"
    dest.parent.mkdir(parents=True)
    dest.write_text("# different content\n", encoding="utf-8")
    data = {"rule": {"id": "no-xxx", "paths": ["**/*.py"], "severity": "blocking"},
            "check": {"kind": "script", "filename": "no_xxx.py", "source": CUSTOM_CHECK}}
    with pytest.raises(bundle.BundleError):
        bundle.materialize(data, tmp_path)


def test_materialize_strips_metadata_whitespace(tmp_path):
    data = {"rule": {"id": "r", "intent": "text\n\n", "why_it_matters": "  why now  ",
                     "rejected_alternatives": ["a\n", " b "], "paths": ["*.py"],
                     "severity": "blocking"},
            "check": {"kind": "builtin", "module": "debug_remnants"}}
    rd = bundle.materialize(data, tmp_path)
    assert rd["intent"] == "text"
    assert rd["why_it_matters"] == "why now"
    assert rd["rejected_alternatives"] == ["a", "b"]


def test_append_rule_creates_and_preserves(tmp_path):
    rules_path = tmp_path / ".bec" / "rules.yaml"
    rules_path.parent.mkdir(parents=True)
    rules_path.write_text("# my rules\nrules:\n  - id: first\n    paths: ['*.py']\n"
                          "    check: 'true'\n    severity: warning\n", encoding="utf-8")
    bundle.append_rule(rules_path, {"id": "second", "paths": ["*.py"],
                                    "check": "false", "severity": "blocking"})
    text = rules_path.read_text(encoding="utf-8")
    assert "# my rules" in text and "id: first" in text and "id: second" in text
    ids = {r.id for r in load_rules(rules_path)}
    assert ids == {"first", "second"}


def test_append_rule_matches_four_space_indent(tmp_path):
    rules_path = tmp_path / "rules.yaml"
    rules_path.write_text("rules:\n    - id: first\n      paths: ['*.py']\n"
                          "      check: 'true'\n      severity: warning\n", encoding="utf-8")
    bundle.append_rule(rules_path, {"id": "second", "paths": ["*.py"],
                                    "check": "false", "severity": "blocking"})
    assert {r.id for r in load_rules(rules_path)} == {"first", "second"}


@pytest.mark.parametrize("empty", ["rules: []\n", "rules: {}\n"])
def test_append_rule_handles_empty_inline_list(tmp_path, empty):
    rules_path = tmp_path / "rules.yaml"
    rules_path.write_text(empty, encoding="utf-8")
    bundle.append_rule(rules_path, {"id": "only", "paths": ["*.py"],
                                    "check": "false", "severity": "blocking"})
    assert {r.id for r in load_rules(rules_path)} == {"only"}


@pytest.mark.parametrize("text", [
    "becwright_bec: 1\nrule: {id: r}\ncheck: {kind: script, filename: x.py}\n",
    "becwright_bec: 1\nrule: {id: r}\ncheck: {kind: builtin}\n",
    "becwright_bec: 1\nrule: {id: r}\ncheck: {kind: weird}\n",
])
def test_parse_rejects_malformed_check(text):
    with pytest.raises(bundle.BundleError):
        bundle.parse_bundle(text)


# --- round trips through evaluate ---

def test_roundtrip_script_blocks_via_evaluate(tmp_path, monkeypatch):
    src = _init_repo(tmp_path / "a")
    check = src / ".bec" / "checks" / "no_xxx.py"
    check.parent.mkdir(parents=True)
    check.write_text(CUSTOM_CHECK, encoding="utf-8")
    rule = Rule(id="no-xxx", paths=("**/*.py",), check="python3 .bec/checks/no_xxx.py",
                intent="No XXX markers", severity="blocking")
    text = bundle.export_bec(rule, src)

    dst = _init_repo(tmp_path / "b")
    data = bundle.parse_bundle(text)
    rule_dict = bundle.materialize(data, dst)
    bundle.append_rule(dst / ".bec" / "rules.yaml", rule_dict)

    assert (dst / ".bec" / "checks" / "no_xxx.py").exists()
    (dst / "bad.py").write_text("y = 1  # XXX fix me\n", encoding="utf-8")
    rules = load_rules(dst / ".bec" / "rules.yaml")
    result = evaluate(rules, ["bad.py"], dst)
    assert result.had_blocking is True


def test_roundtrip_builtin_via_evaluate(tmp_path, monkeypatch):
    monkeypatch.setenv("PYTHONPATH", str(_SRC))
    dst = _init_repo(tmp_path / "b")
    data = {"becwright_bec": 1, "exported_from": "x",
            "rule": {"id": "no-debug", "paths": ["**/*.py"], "severity": "blocking"},
            "check": {"kind": "builtin", "module": "debug_remnants"}}
    bundle.append_rule(dst / ".bec" / "rules.yaml", bundle.materialize(data, dst))
    (dst / "bad.py").write_text("breakpoint()\n", encoding="utf-8")
    rules = load_rules(dst / ".bec" / "rules.yaml")
    assert evaluate(rules, ["bad.py"], dst).had_blocking is True


# --- cli import/export ---

def test_cli_export_to_stdout(tmp_path, monkeypatch, capsys):
    repo = _init_repo(tmp_path / "a")
    (repo / ".bec").mkdir()
    (repo / ".bec" / "rules.yaml").write_text(
        "rules:\n  - id: no-debug\n    paths: ['**/*.py']\n"
        "    check: 'python3 -m becwright.checks.debug_remnants'\n    severity: blocking\n",
        encoding="utf-8")
    monkeypatch.chdir(repo)
    assert cli.main(["export", "no-debug"]) == 0
    assert "becwright_bec:" in capsys.readouterr().out


def test_cli_export_unknown_id(tmp_path, monkeypatch):
    repo = _init_repo(tmp_path / "a")
    (repo / ".bec").mkdir()
    (repo / ".bec" / "rules.yaml").write_text("rules: []\n", encoding="utf-8")
    monkeypatch.chdir(repo)
    assert cli.main(["export", "nope"]) == 1


def _bundle_file(tmp_path):
    text = ("becwright_bec: 1\nexported_from: x\n"
            "rule:\n  id: no-debug\n  paths: ['**/*.py']\n  severity: blocking\n"
            "check:\n  kind: builtin\n  module: debug_remnants\n")
    f = tmp_path / "x.bec.yaml"
    f.write_text(text, encoding="utf-8")
    return f


def test_cli_import_yes_installs(tmp_path, monkeypatch):
    f = _bundle_file(tmp_path)
    repo = _init_repo(tmp_path / "b")
    monkeypatch.chdir(repo)
    assert cli.main(["import", str(f), "--yes"]) == 0
    assert "no-debug" in {r.id for r in load_rules(repo / ".bec" / "rules.yaml")}


def test_cli_import_rejects_duplicate_id(tmp_path, monkeypatch):
    f = _bundle_file(tmp_path)
    repo = _init_repo(tmp_path / "b")
    (repo / ".bec").mkdir()
    (repo / ".bec" / "rules.yaml").write_text(
        "rules:\n  - id: no-debug\n    paths: ['*.py']\n    check: 'true'\n    severity: blocking\n",
        encoding="utf-8")
    monkeypatch.chdir(repo)
    assert cli.main(["import", str(f), "--yes"]) == 1


def test_cli_import_trust_gate_aborts(tmp_path, monkeypatch):
    f = _bundle_file(tmp_path)
    repo = _init_repo(tmp_path / "b")
    monkeypatch.chdir(repo)
    monkeypatch.setattr("builtins.input", lambda *_: "n")
    assert cli.main(["import", str(f)]) == 1
    assert not (repo / ".bec" / "rules.yaml").exists()


def test_cli_import_from_url(tmp_path, monkeypatch):
    text = _bundle_file(tmp_path).read_text(encoding="utf-8")

    class _Resp:
        def read(self):
            return text.encode("utf-8")

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    monkeypatch.setattr(cli.urllib.request, "urlopen", lambda *a, **k: _Resp())
    repo = _init_repo(tmp_path / "b")
    monkeypatch.chdir(repo)
    assert cli.main(["import", "https://example.com/x.bec.yaml", "--yes"]) == 0
    assert "no-debug" in {r.id for r in load_rules(repo / ".bec" / "rules.yaml")}
