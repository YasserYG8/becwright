# Stability & versioning

becwright is **stable** (`1.0`). It's dogfooded (its own commits are gated by
becwright), the test suite is green, and it's published on npm and PyPI. Under
[SemVer](https://semver.org) the public contract below only breaks on a major
bump, so a `1.x` upgrade is always safe. If you depend on it in CI, pin a version
anyway (`becwright==1.0.0`, or `npm i -g becwright@1.0.0`).

## The public contract

Stable as of `1.0.0`, changed only on a major bump:

- The `.bec/rules.yaml` schema (rule fields and their meaning).
- The `.bec.yaml` bundle format that `export` / `import` move between repos.
- Built-in check names and their flags.
- CLI commands and their exit codes.
- The `check --json` output shape.
- MCP tool names and signatures.

Everything else (message wording, catalog contents, internal modules) can change
at any time.

Before `1.0.0` the groundwork was: both on-disk formats versioned so a newer file
fails loudly (`schema_version` / `becwright_bec`), the `rules.yaml` field set
frozen and test-locked, exit codes and `check --json` documented and test-locked,
and validation against real repositories.

## Deprecation policy

From `1.0.0` on, nothing in the public contract is removed without a major bump
of notice. When something has to change:

1. It is marked **deprecated** in a minor release — it keeps working and emits a
   warning.
2. It keeps working (still warning) through the rest of that major series.
3. It is removed only in the next **major** release.

So anything valid on `1.0` stays valid across every `1.x`: a breaking change
always crosses a major version, with at least one minor of warning first. Pin a
version in CI and a `1.x` upgrade will never break your rules, bundles, or check
scripts without warning.
