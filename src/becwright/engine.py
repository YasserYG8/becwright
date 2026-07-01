from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from .rules import Rule

# A check runs on every commit and may carry imported (third-party) code. Cap it
# so a hung or runaway check can never freeze the commit. Override for slow
# whole-repo runs via BECWRIGHT_CHECK_TIMEOUT (seconds; 0 disables the cap).
_DEFAULT_TIMEOUT = 30.0


def _check_timeout() -> float | None:
    raw = os.environ.get("BECWRIGHT_CHECK_TIMEOUT")
    if raw is None:
        return _DEFAULT_TIMEOUT
    try:
        value = float(raw)
    except ValueError:
        return _DEFAULT_TIMEOUT
    return None if value <= 0 else value


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


@lru_cache(maxsize=None)
def _compiled_glob(pattern: str) -> re.Pattern[str]:
    return re.compile(_glob_to_regex(pattern))


def matches(path: str, patterns: tuple[str, ...]) -> bool:
    # `check --all` runs this for every (file, pattern) pair; caching the
    # compiled regex avoids rebuilding it on each call.
    return any(_compiled_glob(p).match(path) for p in patterns)


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
        try:
            proc = subprocess.run(
                rule.check, shell=True, cwd=root,
                input="\n".join(relevant), capture_output=True, text=True,
                timeout=_check_timeout(),
            )
        except subprocess.TimeoutExpired:
            results.append(RuleResult(
                rule=rule, passed=False,
                output=f"check timed out after {_check_timeout():g}s (its command hung)",
            ))
            continue
        output = proc.stdout.strip() or proc.stderr.strip()
        results.append(
            RuleResult(rule=rule, passed=proc.returncode == 0, output=output)
        )
    return Result(per_rule=results)
