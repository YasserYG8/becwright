from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

# blocking = stops the commit | warning = deterministic finding, does not block |
# advisory = best-effort / non-deterministic (e.g. an LLM reviewer); reports, never blocks
_VALID_SEVERITIES = ("blocking", "warning", "advisory")
_VALID_TARGETS = ("files", "commit-msg")

# The `.bec/rules.yaml` format version. Absent means 1 (files predating the
# field). The engine refuses a file stamped newer than it understands instead of
# risking a silent misparse; migration between versions is added when a v2 exists.
RULES_SCHEMA_VERSION = 1


class RulesError(RuntimeError):
    """A `.bec/rules.yaml` that cannot be trusted (bad YAML or an invalid rule).
    Raised instead of letting a typo silently weaken enforcement."""


@dataclass(frozen=True)
class Rule:
    id: str
    paths: tuple[str, ...]
    check: str
    exclude: tuple[str, ...] = ()  # globs carved out of `paths` (vendored code, generated files, the check's own implementation)
    intent: str = ""
    why_it_matters: str = ""
    rejected_alternatives: tuple[str, ...] = ()
    severity: str = "blocking"  # blocking = stops the commit | warning = only warns
    target: str = "files"  # files = the changed files | commit-msg = the commit message

    @property
    def is_blocking(self) -> bool:
        return self.severity == "blocking"

    @property
    def is_advisory(self) -> bool:
        return self.severity == "advisory"


def _to_rule(raw: dict) -> Rule:
    if not isinstance(raw, dict):
        raise RulesError(f"each rule must be a mapping, got {type(raw).__name__}.")
    for field in ("id", "check"):
        if not raw.get(field):
            raise RulesError(f"a rule is missing the required field '{field}'.")
    severity = raw.get("severity", "blocking")
    if severity not in _VALID_SEVERITIES:
        raise RulesError(
            f"rule '{raw['id']}': invalid severity {severity!r} "
            f"(use one of: {', '.join(_VALID_SEVERITIES)})."
        )
    target = raw.get("target", "files")
    if target not in _VALID_TARGETS:
        raise RulesError(
            f"rule '{raw['id']}': invalid target {target!r} "
            f"(use one of: {', '.join(_VALID_TARGETS)})."
        )
    return Rule(
        id=raw["id"],
        paths=tuple(raw.get("paths", [])),
        check=raw["check"],
        exclude=tuple(raw.get("exclude", [])),
        intent=(raw.get("intent") or "").strip(),
        why_it_matters=(raw.get("why_it_matters") or "").strip(),
        rejected_alternatives=tuple(raw.get("rejected_alternatives", [])),
        severity=severity,
        target=target,
    )


def load_rules(rules_path: Path) -> list[Rule]:
    if not rules_path.exists():
        return []
    try:
        data = yaml.safe_load(rules_path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as e:
        raise RulesError(f"{rules_path}: invalid YAML ({e}).")
    if not isinstance(data, dict) or not isinstance(data.get("rules", []), list):
        raise RulesError(f"{rules_path}: expected a top-level 'rules:' list.")
    _check_schema_version(data.get("schema_version"), rules_path)
    return [_to_rule(r) for r in data["rules"]] if data.get("rules") else []


def _check_schema_version(value, rules_path: Path) -> None:
    if value is None:
        return
    # bool is an int subclass; a YAML `true` is not a valid version.
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise RulesError(
            f"{rules_path}: schema_version must be a positive integer, got {value!r}."
        )
    if value > RULES_SCHEMA_VERSION:
        raise RulesError(
            f"{rules_path}: schema_version {value} is newer than this becwright "
            f"understands (max {RULES_SCHEMA_VERSION}); upgrade becwright."
        )
