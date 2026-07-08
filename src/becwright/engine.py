from __future__ import annotations

import os
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor
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


def _run_check(rule: Rule, stdin: str, root: Path) -> RuleResult:
    try:
        proc = subprocess.run(
            rule.check, shell=True, cwd=root,
            input=stdin, capture_output=True, text=True,
            timeout=_check_timeout(),
        )
    except subprocess.TimeoutExpired:
        return RuleResult(
            rule=rule, passed=False,
            output=f"check timed out after {_check_timeout():g}s (its command hung)",
        )
    outputs = [proc.stdout.strip(), proc.stderr.strip()]
    output = "\n".join(o for o in outputs if o).strip()
    return RuleResult(rule=rule, passed=proc.returncode == 0, output=output)


def evaluate(rules: list[Rule], files: list[str], root: Path) -> Result:
    tasks: list[tuple[Rule, str]] = []
    for rule in rules:
        if rule.target != "files":
            continue
        relevant = [
            f for f in files
            if matches(f, rule.paths) and not matches(f, rule.exclude)
        ]
        if not relevant:
            continue
        tasks.append((rule, "\n".join(relevant)))

    with ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(_run_check, rule, stdin, root)
            for rule, stdin in tasks
        ]
        results = [f.result() for f in futures]
    return Result(per_rule=results)


def evaluate_message(rules: list[Rule], message_path: str, root: Path) -> Result:
    """Run the `commit-msg` rules against the commit message. The message file
    path is fed to each check on stdin, exactly like a source file, so the generic
    `forbid` / `require` checks work on the message with no special casing."""
    tasks = [
        rule for rule in rules
        if rule.target == "commit-msg"
    ]
    with ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(_run_check, rule, message_path, root)
            for rule in tasks
        ]
        results = [f.result() for f in futures]
    return Result(per_rule=results)
