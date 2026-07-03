import json
from pathlib import Path

import pytest
import yaml

from becwright import cli

_SCHEMA_PATH = Path(__file__).resolve().parents[1] / "schema" / "rules.schema.json"
_REPO_RULES = Path(__file__).resolve().parents[1] / ".bec" / "rules.yaml"

jsonschema = pytest.importorskip("jsonschema")


def _schema():
    return json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))


def _validate(data):
    jsonschema.validate(data, _schema())


def test_schema_is_valid_jsonschema():
    jsonschema.Draft7Validator.check_schema(_schema())


def test_valid_rules_file_passes():
    _validate({
        "schema_version": 1,
        "rules": [{
            "id": "no-token-in-logs",
            "intent": "Tokens must never reach a log.",
            "why_it_matters": "A token in the logs lets anyone steal a session.",
            "rejected_alternatives": ["Redact at log time -> too easy to bypass"],
            "paths": ["src/**/*.py"],
            "exclude": ["src/logging_setup.py"],
            "check": "becwright run no_token_in_logs",
            "severity": "blocking",
        }],
    })


def test_commit_msg_rule_needs_no_paths():
    _validate({
        "rules": [{
            "id": "conventional-commits",
            "target": "commit-msg",
            "check": "becwright run require --pattern '^feat'",
        }],
    })


def test_typoed_field_fails():
    with pytest.raises(jsonschema.ValidationError):
        _validate({
            "rules": [{
                "id": "x", "check": "true",
                "pathss": ["**/*.py"],  # the typo the schema exists to catch
            }],
        })


def test_invalid_severity_fails():
    with pytest.raises(jsonschema.ValidationError):
        _validate({"rules": [{"id": "x", "check": "true", "severity": "blockng"}]})


def test_missing_check_fails():
    with pytest.raises(jsonschema.ValidationError):
        _validate({"rules": [{"id": "x", "paths": ["**/*.py"]}]})


def test_generated_init_output_validates():
    rendered = cli._render_rules_yaml(cli._starter_rules(["python", "ts"]))
    assert rendered.startswith("# yaml-language-server: $schema=")
    _validate(yaml.safe_load(rendered))


def test_this_repos_rules_validate():
    _validate(yaml.safe_load(_REPO_RULES.read_text(encoding="utf-8")))
