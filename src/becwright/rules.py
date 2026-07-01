from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

_VALID_SEVERITIES = ("blocking", "warning")


class RulesError(RuntimeError):
    """A `.bec/rules.yaml` that cannot be trusted (bad YAML or an invalid rule).
    Raised instead of letting a typo silently weaken enforcement."""


@dataclass(frozen=True)
class Rule:
    id: str
    paths: tuple[str, ...]
    check: str
    intent: str = ""
    why_it_matters: str = ""
    rejected_alternatives: tuple[str, ...] = ()
    severity: str = "blocking"  # blocking = stops the commit | warning = only warns

    @property
    def is_blocking(self) -> bool:
        return self.severity == "blocking"


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
    return Rule(
        id=raw["id"],
        paths=tuple(raw.get("paths", [])),
        check=raw["check"],
        intent=(raw.get("intent") or "").strip(),
        why_it_matters=(raw.get("why_it_matters") or "").strip(),
        rejected_alternatives=tuple(raw.get("rejected_alternatives", [])),
        severity=severity,
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
    return [_to_rule(r) for r in data["rules"]] if data.get("rules") else []
