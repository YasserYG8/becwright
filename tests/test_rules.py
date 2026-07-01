import pytest

from becwright.rules import RulesError, load_rules


def _write(tmp_path, text):
    path = tmp_path / "rules.yaml"
    path.write_text(text, encoding="utf-8")
    return path


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
