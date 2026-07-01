from __future__ import annotations

from pathlib import Path

from . import git
from .engine import Result, evaluate
from .rules import Rule, load_rules


def gather(root: Path, *, all_files: bool) -> tuple[list[Rule], list[str], Result | None]:
    """Load rules, find the files to check and evaluate them. The result is None
    when there is nothing to check (no rules or no files)."""
    rules = load_rules(root / ".bec" / "rules.yaml")
    files = git.files_to_check(root, all_files=all_files)
    if not rules or not files:
        return rules, files, None
    # `--all` inspects the working tree on purpose; the pre-commit path checks the
    # staged content, which is what the commit will actually record.
    if all_files:
        return rules, files, evaluate(rules, files, root)
    with git.staged_worktree(root, files) as staged_root:
        return rules, files, evaluate(rules, files, staged_root)


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
