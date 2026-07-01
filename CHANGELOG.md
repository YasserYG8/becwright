# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- `conflict_markers` check: fails on leftover git merge conflict markers
  (`<<<<<<<`, `>>>>>>>`, `|||||||`).
- `becwright init --from-claude-md` expands a broad "good practices" / "buenas
  prácticas" phrase into the deterministic code-hygiene rule set (no secrets,
  `eval`, debug leftovers, or conflict markers), language-aware and de-duplicated.

## [0.3.0] — 2026-07-01

### Added
- `becwright add <name>` and `becwright search [query]`: install ready-made BECs
  from a catalog that now ships **inside** the package — no URL, works offline.
- `.pre-commit-hooks.yaml`: use becwright through the
  [pre-commit](https://pre-commit.com) framework, plus Husky setup in the README.
- Per-rule `exclude:` globs, subtracted from `paths`, so one rule can cover a
  whole language while skipping vendored/generated files or the check's own
  implementation. Travels with the rule through `export` / `import`.
- `becwright init --baseline`: start already-violated rules as `warning` and
  clean ones as `blocking`, so becwright can be adopted on a dirty codebase
  without blocking commits on pre-existing debt.
- `becwright init --from-claude-md`: derive rules from the repo's `CLAUDE.md`,
  mapping recognized prohibitions (secrets, `eval`, `debugger`, `console.log`,
  breakpoints, wildcard imports, tokens in logs) to enforceable checks and
  reporting which phrase matched each. Also picks up a per-file line cap
  ("files under 800 lines" → `max_lines`), ignoring function-length rules it
  can't enforce. Judgment-based guidance is left for `CLAUDE.md`. Composes with
  `--baseline`.
- Three language-agnostic checks that cover common `CLAUDE.md` rules without an
  AST: `max_lines` (file length cap via `--max`), `require` (a regex that must be
  present — the inverse of `forbid`), and `filename` (file-name conventions via
  `--forbid` / `--require`, matched against the base name).
- MCP tool `preview_rule`: dry-run a candidate rule (`check` + `paths`) against
  the repo without writing it, returning matched-file count, pass/fail, and what
  it flags — so an agent can validate a rule it translated from a `CLAUDE.md`
  before committing to it.
- MCP tool `propose_rules_from_claude_md`: returns the rules becwright can derive
  deterministically from the repo's `CLAUDE.md` (each with the phrase that
  triggered it) plus a hint to extend them — the agent's starting point.
- MCP tool `add_rule`: persists a rule to `.bec/rules.yaml`, but never blindly —
  it previews unless `confirm=true`, and accepts built-in checks only (arbitrary
  shell commands must go through the CLI `import`, which shows the code first).
- The Claude Code skill/plugin now teaches deriving BECs from a `CLAUDE.md`: the
  `--from-claude-md` / `--baseline` init flavors and the MCP authoring loop
  (`propose_rules_from_claude_md` → `preview_rule` → `add_rule`), keeping
  judgment-based guidance in `CLAUDE.md`.

### Changed
- The pre-commit path now checks the **staged content** of files, not the
  working tree, so the result always matches what the commit will record.
- Compiled glob patterns are cached (`check --all` is faster on large repos).
- CI also runs on Python 3.14.

### Fixed
- A hung or runaway check can no longer freeze a commit: each check has a
  timeout (30s, override with `BECWRIGHT_CHECK_TIMEOUT`, `0` disables).
- A misspelled `severity` or malformed `.bec/rules.yaml` now fails with a clear
  error instead of silently downgrading a rule or dumping a raw traceback.
- A rule pointing `check:` at a `becwright run <name>` that isn't a built-in check
  now reports a config problem (exit 2) naming the rule and check, instead of
  looking like a real violation that blocks the commit.

## [0.2.2] — 2026-06-30

### Added
- Distribution polish for discoverability: aligned npm/PyPI descriptions and
  keywords, social preview image, layered beginner-friendly documentation.

### Fixed
- `--no-color` / `NO_COLOR` is honored in CLI output.

## [0.2.1] — 2026-06-29

### Added
- Claude Code plugin and MCP server (`becwright mcp`) for AI-agent integration.

## [0.2.0] — 2026-06-29

### Added
- Portability: `becwright export` / `import` move a BEC between repos as a single
  self-contained `.bec.yaml`, with a trust gate that shows the check's code
  before installing it.
- Multi-language support via the language-agnostic engine and the generic
  `forbid` check.

## [0.1.0] — 2026-06-29

### Added
- Initial release: the `becwright` CLI (`init`, `check`, `install`,
  `uninstall`, `list`, `run`), the native pre-commit hook, and the first
  built-in checks.

[Unreleased]: https://github.com/DataDave-Dev/becwright/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/DataDave-Dev/becwright/compare/v0.2.2...v0.3.0
[0.2.2]: https://github.com/DataDave-Dev/becwright/compare/v0.2.1...v0.2.2
[0.2.1]: https://github.com/DataDave-Dev/becwright/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/DataDave-Dev/becwright/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/DataDave-Dev/becwright/releases/tag/v0.1.0
