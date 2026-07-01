from __future__ import annotations

from pathlib import Path

from . import git
from .engine import Result, evaluate
from .rules import Rule, load_rules


def gather(
    root: Path, *, all_files: bool = False, diff_base: str | None = None
) -> tuple[list[Rule], list[str], Result | None]:
    """Load rules, find the files to check and evaluate them. The result is None
    when there is nothing to check (no rules or no files)."""
    rules = load_rules(root / ".bec" / "rules.yaml")
    files = git.files_to_check(root, all_files=all_files, diff_base=diff_base)
    if not rules or not files:
        return rules, files, None
    # `--all` and `--diff` inspect the working tree (in CI the checkout already is
    # the committed content); the pre-commit path checks the staged content, which
    # is what the commit will actually record.
    if all_files or diff_base:
        return rules, files, evaluate(rules, files, root)
    with git.staged_worktree(root, files) as staged_root:
        return rules, files, evaluate(rules, files, staged_root)


def rule_record(rule: Rule) -> dict:
    """A rule's *Bound* half — its intent, reason and the decision behind it — as a
    serializable record. Shared by `becwright why --json` and any agent that wants
    the decisions it must not violate *before* writing code, not only when a commit
    fails."""
    return {
        "id": rule.id,
        "severity": rule.severity,
        "target": rule.target,
        "intent": rule.intent or None,
        "why_it_matters": rule.why_it_matters or None,
        "rejected_alternatives": list(rule.rejected_alternatives),
        "paths": list(rule.paths),
        "exclude": list(rule.exclude),
        "check": rule.check,
    }


def payload(rules: list[Rule], files: list[str], result: Result | None) -> dict:
    """Build a JSON-serializable summary shared by `check --json` and the MCP server."""
    results = []
    if result is not None:
        for r in result.per_rule:
            results.append({
                "id": r.rule.id,
                "severity": r.rule.severity,
                "passed": r.passed,
                "intent": r.rule.intent or None,
                "why_it_matters": r.rule.why_it_matters or None,
                "output": r.output or None,
            })
    return {
        "rule_count": len(rules),
        "checked_files": len(files),
        "blocked": result.had_blocking if result else False,
        "results": results,
    }
