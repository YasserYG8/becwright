"""MCP server exposing becwright to AI agents as structured tools.

Only imported when running `becwright mcp`, so the `mcp` dependency stays optional
(install the `mcp` extra). The tools are thin wrappers over the same logic the CLI
uses, returning JSON-serializable results instead of human text.
"""
from __future__ import annotations

from pathlib import Path

from mcp.server.fastmcp import FastMCP

from . import git, report
from .cli import _CHECK_DESCRIPTIONS, _builtin_check_names

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


def serve() -> None:
    mcp.run()
