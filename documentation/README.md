> **English** · [Español](README.es.md)

# becwright documentation

Documentation for becwright. For the project overview, see the
[main README](../README.md). Every page starts with a plain-language summary and
then goes deeper, so you can stop wherever it stops being useful to you — no
prior background assumed.

**Start here**

- [Usage](usage.md) — install, the commands, and how to write a rule. Read this first.
- [Recipes](recipes.md) — copy-paste rules for common jobs: gitleaks/ruff/semgrep as checks, frozen paths, architecture boundaries, CI, Husky.
- [Writing checks](writing-checks.md) — the no-code `forbid` shortcut, then custom checks in any language.
- [Portability](portability.md) — share a rule between projects with export/import.

**Go deeper**

- [Architecture](architecture.md) — how becwright works inside and the exact check flow.
- [MCP & JSON output](mcp.md) — structured results for AI agents (`check --json`, the MCP server).

**Maintainers**

- [Releasing](releasing.md) — how the npm + PyPI release is built and published.
