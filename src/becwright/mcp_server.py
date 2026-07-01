"""MCP server exposing becwright to AI agents as structured tools.

Only imported when running `becwright mcp`, so the `mcp` dependency stays optional
(install the `mcp` extra). The tools are thin wrappers over the same logic the CLI
uses, returning JSON-serializable results instead of human text.
"""
from __future__ import annotations

from pathlib import Path

from mcp.server.fastmcp import FastMCP

from . import git, report
from .cli import (
    _CHECK_DESCRIPTIONS,
    _builtin_check_names,
    _detect_languages,
    _read_claude_md,
    _rules_from_claude_md,
)

mcp = FastMCP("becwright")


@mcp.tool()
def check(all_files: bool = False, path: str | None = None) -> dict:
    """Run becwright's rules and return structured results.

    Args:
        all_files: check the whole repo instead of only staged files.
        path: a directory inside the target git repo (defaults to the cwd).

    Returns a summary with rule_count, checked_files, a `blocked` flag and a
    per-rule list of {id, severity, passed, intent, why_it_matters, output}.
    """
    root = git.repo_root(Path(path) if path else None)
    rules, files, result = report.gather(root, all_files=all_files)
    return report.payload(rules, files, result)


@mcp.tool()
def list_checks() -> list[dict]:
    """List becwright's built-in checks as {name, description}."""
    return [
        {"name": name, "description": _CHECK_DESCRIPTIONS.get(name, "")}
        for name in _builtin_check_names()
    ]


@mcp.tool()
def preview_rule(check: str, paths: list[str], exclude: list[str] | None = None,
                 all_files: bool = True, path: str | None = None) -> dict:
    """Dry-run a candidate rule without writing it to `.bec/rules.yaml`.

    Runs `check` against the files selected by `paths` (minus `exclude`) in the
    target repo and reports whether it would pass and what it flags — so an agent
    can validate a rule it translated from a CLAUDE.md before committing to it.

    Args:
        check: the check command, e.g. "becwright run max_lines --max 800".
        paths: glob patterns the rule would apply to.
        exclude: globs carved out of `paths` (optional).
        all_files: preview against the whole repo (default) or only staged files.
        path: a directory inside the target git repo (defaults to the cwd).

    Returns {matched_files, passed, output, note}: `matched_files` is how many
    files the globs select; `note` flags an empty match or an unknown check.
    """
    from .cli import _unknown_builtin_checks
    from .engine import evaluate, matches
    from .rules import Rule

    root = git.repo_root(Path(path) if path else None)
    rule = Rule(id="preview", paths=tuple(paths), check=check,
                exclude=tuple(exclude or ()), severity="warning")

    files = git.files_to_check(root, all_files=all_files)
    relevant = [f for f in files if matches(f, rule.paths) and not matches(f, rule.exclude)]

    unknown = _unknown_builtin_checks([rule], root)
    if unknown:
        return {"matched_files": len(relevant), "passed": False, "output": "",
                "note": f"'{unknown[0][1]}' is not a built-in check — call list_checks."}
    if not relevant:
        return {"matched_files": 0, "passed": True, "output": "",
                "note": "This rule matches no files — check the paths globs."}

    result = evaluate([rule], relevant, root)
    outcome = result.per_rule[0]
    return {"matched_files": len(relevant), "passed": outcome.passed,
            "output": outcome.output or "", "note": None}


_UNMAPPED_HINT = (
    "These are the rules becwright can derive deterministically from the prose. "
    "Read the rest of the CLAUDE.md and add rules for prohibitions it missed, "
    "using list_checks as the vocabulary and preview_rule to validate each one. "
    "Judgment-based guidance (architecture, naming quality, immutability) has no "
    "deterministic check and should stay in CLAUDE.md."
)


@mcp.tool()
def propose_rules_from_claude_md(path: str | None = None) -> dict:
    """Read the repo's CLAUDE.md and return the rules becwright can deterministically
    derive from it — the agent's starting point before extending them by reading the
    rest of the prose.

    Args:
        path: a directory inside the target git repo (defaults to the cwd).

    Returns {rules, unmapped_hint}, where each rule is {id, check, paths, severity,
    intent, why_it_matters, matched} and `matched` is the phrase that triggered it.
    If there is no CLAUDE.md, returns {rules: [], note: ...}.
    """
    root = git.repo_root(Path(path) if path else None)
    text = _read_claude_md(root)
    if text is None:
        return {"rules": [], "note": "No CLAUDE.md at the repo root."}
    rules = [
        {
            "id": rule["id"],
            "check": rule["check"],
            "paths": rule["paths"],
            "severity": rule["severity"],
            "intent": rule.get("intent", ""),
            "why_it_matters": rule.get("why", ""),
            "matched": trigger,
        }
        for rule, trigger in _rules_from_claude_md(text, _detect_languages(root))
    ]
    return {"rules": rules, "unmapped_hint": _UNMAPPED_HINT}


def serve() -> None:
    mcp.run()
