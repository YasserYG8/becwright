from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


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
    return Rule(
        id=raw["id"],
        paths=tuple(raw.get("paths", [])),
        check=raw["check"],
        intent=(raw.get("intent") or "").strip(),
        why_it_matters=(raw.get("why_it_matters") or "").strip(),
        rejected_alternatives=tuple(raw.get("rejected_alternatives", [])),
        severity=raw.get("severity", "blocking"),
    )


def load_rules(rules_path: Path) -> list[Rule]:
    if not rules_path.exists():
        return []
    data = yaml.safe_load(rules_path.read_text(encoding="utf-8")) or {}
    return [_to_rule(r) for r in data.get("rules", [])]
