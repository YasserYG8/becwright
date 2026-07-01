# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- `becwright add <name>` and `becwright search [query]`: install ready-made BECs
  from a catalog that now ships **inside** the package — no URL, works offline.
- `.pre-commit-hooks.yaml`: use becwright through the
  [pre-commit](https://pre-commit.com) framework, plus Husky setup in the README.

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

[Unreleased]: https://github.com/DataDave-Dev/becwright/compare/v0.2.2...HEAD
[0.2.2]: https://github.com/DataDave-Dev/becwright/compare/v0.2.1...v0.2.2
[0.2.1]: https://github.com/DataDave-Dev/becwright/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/DataDave-Dev/becwright/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/DataDave-Dev/becwright/releases/tag/v0.1.0
