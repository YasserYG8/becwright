# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Declared **Beta** maturity (`Development Status :: 4 - Beta` classifier) and a
  public **Stability & versioning** section in the README: what the `1.0.0`
  contract covers (`rules.yaml` schema, `.bec.yaml` bundle format, check names,
  CLI commands and exit codes, `check --json` shape, MCP signatures) and the
  exit criteria to reach it.
- `.bec/rules.yaml` now carries an optional `schema_version` (absent means `1`,
  so existing files keep working). `becwright init` stamps it, and the engine
  refuses a file stamped newer than it understands — with a clear "upgrade
  becwright" error — instead of risking a silent misparse. (The `.bec.yaml`
  export bundle was already versioned via `becwright_bec`.)
- **Froze the `.bec/rules.yaml` field set** as of `schema_version 1`: the nine
  rule fields (`id`, `paths`, `check`, `exclude`, `intent`, `why_it_matters`,
  `rejected_alternatives`, `severity`, `target`) are now test-locked, so from
  `1.0.0` on a field only changes under the deprecation policy. This completes the
  groundwork on the path to 1.0.0.

### Fixed
- `becwright init --from-claude-md` no longer misreads a per-*function* line count
  as a per-*file* cap. A phrase like "~50 lines per function, ~800 per file" used
  to derive `max_lines --max 50` (flagging nearly every file); the file-cap
  matcher now refuses to bridge across a comma or another number, so an ambiguous
  soft guideline derives no cap instead of a wrong one. (Surfaced field-testing a
  real Python repo.)

### Documentation
- Documented becwright's **stable contract** in `documentation/usage.md`: the CLI
  exit codes (`0` pass · `1` a blocking rule failed · `2` config/usage problem)
  and the `check --json` output shape, both now locked by tests so a change is a
  deliberate break rather than a silent drift.
- Stated a **deprecation policy** for `1.0.0` on (README + `documentation/releasing.md`):
  anything in the public contract is deprecated with a warning for at least one
  minor and removed only in the next major, so no `1.x` upgrade breaks a rule
  file, bundle, or check script without notice.

## [0.4.0] — 2026-07-01

### Added
- **`advisory` severity.** The honest home for judgment rules whose check isn't
  deterministic (e.g. an LLM reviewer): it reports, labelled `ADVISORY (best-effort,
  not a guarantee)`, but never blocks — so `blocking`/`warning` stay 100% guarantees
  and you always know which findings are guaranteed vs assisted. becwright supplies
  the tier; the reviewer is your own check command (no LLM dependency in becwright).
- **Commit-message rules.** A rule with `target: commit-msg` checks the commit
  message instead of the files; `becwright init` now installs a `commit-msg` hook
  alongside `pre-commit`, and `becwright check-msg <file>` runs those rules.
  `--from-claude-md` maps "conventional commits" and "no AI attribution" phrases
  into ready-made commit-msg rules.
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

[Unreleased]: https://github.com/DataDave-Dev/becwright/compare/v0.4.0...HEAD
[0.4.0]: https://github.com/DataDave-Dev/becwright/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/DataDave-Dev/becwright/compare/v0.2.2...v0.3.0
[0.2.2]: https://github.com/DataDave-Dev/becwright/compare/v0.2.1...v0.2.2
[0.2.1]: https://github.com/DataDave-Dev/becwright/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/DataDave-Dev/becwright/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/DataDave-Dev/becwright/releases/tag/v0.1.0
