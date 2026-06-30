from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .rules import Rule


def _glob_to_regex(pattern: str) -> str:
    # `**/` = zero or more dirs; `**` = anything; `*` = anything but `/`.
    i = 0
    out: list[str] = []
    while i < len(pattern):
        if pattern[i:i + 3] == "**/":
            out.append("(?:.*/)?")
            i += 3
        elif pattern[i:i + 2] == "**":
            out.append(".*")
            i += 2
        elif pattern[i] == "*":
            out.append("[^/]*")
            i += 1
        elif pattern[i] == ".":
            out.append(r"\.")
            i += 1
        else:
            out.append(re.escape(pattern[i]))
            i += 1
    return "^" + "".join(out) + "$"


def matches(path: str, patterns: tuple[str, ...]) -> bool:
    return any(re.match(_glob_to_regex(p), path) for p in patterns)


@dataclass(frozen=True)
class RuleResult:
    rule: Rule
    passed: bool
    output: str  # check stdout: the violations it found


@dataclass(frozen=True)
class Result:
    per_rule: list[RuleResult]

    @property
    def had_blocking(self) -> bool:
        return any(not r.passed and r.rule.is_blocking for r in self.per_rule)


def evaluate(rules: list[Rule], files: list[str], root: Path) -> Result:
    results: list[RuleResult] = []
    for rule in rules:
        relevant = [f for f in files if matches(f, rule.paths)]
        if not relevant:
            continue
        proc = subprocess.run(
            rule.check, shell=True, cwd=root,
            input="\n".join(relevant), capture_output=True, text=True,
        )
        output = proc.stdout.strip() or proc.stderr.strip()
        results.append(
            RuleResult(rule=rule, passed=proc.returncode == 0, output=output)
        )
    return Result(per_rule=results)
