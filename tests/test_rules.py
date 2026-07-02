import dataclasses

import pytest

from becwright.rules import RULES_SCHEMA_VERSION, Rule, RulesError, load_rules


def _write(tmp_path, text):
    path = tmp_path / "rules.yaml"
    path.write_text(text, encoding="utf-8")
    return path


# The `.bec/rules.yaml` field set is frozen as of schema_version 1: from 1.0.0 on,
# a field is only added/removed under the deprecation policy (README). This test
# makes a change to the set a deliberate, reviewed break rather than an accident.
_FROZEN_RULE_FIELDS = {
    "id", "paths", "check", "exclude", "intent",
    "why_it_matters", "rejected_alternatives", "severity", "target",
}


def test_rule_field_set_is_frozen():
    assert {f.name for f in dataclasses.fields(Rule)} == _FROZEN_RULE_FIELDS


def test_missing_file_returns_empty(tmp_path):
    assert load_rules(tmp_path / "nope.yaml") == []


def test_loads_valid_rules(tmp_path):
    path = _write(tmp_path, 'rules:\n  - id: r1\n    check: "true"\n    severity: warning\n')
    rules = load_rules(path)
    assert len(rules) == 1 and rules[0].is_blocking is False


def test_invalid_severity_raises(tmp_path):
    path = _write(tmp_path, 'rules:\n  - id: r1\n    check: "true"\n    severity: blockign\n')
    with pytest.raises(RulesError, match="invalid severity"):
        load_rules(path)


def test_invalid_yaml_raises_friendly_error(tmp_path):
    path = _write(tmp_path, "rules:\n  - id: r1\n   check: bad-indent\n")
    with pytest.raises(RulesError, match="invalid YAML"):
        load_rules(path)


def test_missing_required_field_raises(tmp_path):
    path = _write(tmp_path, "rules:\n  - id: r1\n")
    with pytest.raises(RulesError, match="'check'"):
        load_rules(path)


def test_non_list_rules_raises(tmp_path):
    path = _write(tmp_path, "rules: not-a-list\n")
    with pytest.raises(RulesError, match="'rules:' list"):
        load_rules(path)


def test_loads_exclude(tmp_path):
    path = _write(
        tmp_path,
        'rules:\n  - id: r1\n    check: "true"\n    paths: ["**/*.py"]\n'
        '    exclude: ["lib/logger.py"]\n',
    )
    assert load_rules(path)[0].exclude == ("lib/logger.py",)


def test_exclude_defaults_empty(tmp_path):
    path = _write(tmp_path, 'rules:\n  - id: r1\n    check: "true"\n')
    assert load_rules(path)[0].exclude == ()


def test_loads_commit_msg_target(tmp_path):
    path = _write(tmp_path, 'rules:\n  - id: r1\n    check: "true"\n    target: commit-msg\n')
    assert load_rules(path)[0].target == "commit-msg"


def test_target_defaults_to_files(tmp_path):
    path = _write(tmp_path, 'rules:\n  - id: r1\n    check: "true"\n')
    assert load_rules(path)[0].target == "files"


def test_invalid_target_raises(tmp_path):
    path = _write(tmp_path, 'rules:\n  - id: r1\n    check: "true"\n    target: mensaje\n')
    with pytest.raises(RulesError, match="invalid target"):
        load_rules(path)


def test_loads_advisory_severity(tmp_path):
    path = _write(tmp_path, 'rules:\n  - id: r1\n    check: "true"\n    severity: advisory\n')
    rule = load_rules(path)[0]
    assert rule.is_advisory is True and rule.is_blocking is False


def test_absent_schema_version_loads(tmp_path):
    path = _write(tmp_path, 'rules:\n  - id: r1\n    check: "true"\n')
    assert len(load_rules(path)) == 1


def test_current_schema_version_loads(tmp_path):
    path = _write(
        tmp_path,
        f'schema_version: {RULES_SCHEMA_VERSION}\nrules:\n  - id: r1\n    check: "true"\n',
    )
    assert len(load_rules(path)) == 1


def test_newer_schema_version_raises(tmp_path):
    path = _write(
        tmp_path,
        f'schema_version: {RULES_SCHEMA_VERSION + 1}\nrules:\n  - id: r1\n    check: "true"\n',
    )
    with pytest.raises(RulesError, match="newer"):
        load_rules(path)


def test_non_integer_schema_version_raises(tmp_path):
    path = _write(tmp_path, 'schema_version: one\nrules:\n  - id: r1\n    check: "true"\n')
    with pytest.raises(RulesError, match="schema_version"):
        load_rules(path)


def test_non_positive_schema_version_raises(tmp_path):
    path = _write(tmp_path, 'schema_version: 0\nrules:\n  - id: r1\n    check: "true"\n')
    with pytest.raises(RulesError, match="schema_version"):
        load_rules(path)
