# Releasing

> **Maintainers only.** This page is about publishing a new version of becwright
> to npm and PyPI. If you're *using* becwright, you never need this — install it
> with the commands in the [README](../README.md) and you're set.

becwright ships through three channels from a single GitHub release:

- **PyPI** — the Python package (`pip` / `pipx`).
- **npm** — a launcher package (`becwright`) plus five `os`/`cpu`-gated platform
  packages (`@becwright/<target>`) that each carry a prebuilt binary, so users
  without Python can install it.

## One-time setup

- **PyPI**: configured via Trusted Publishing (OIDC), no token stored. See the
  `pypi` job in [`.github/workflows/release.yml`](../.github/workflows/release.yml).
- **npm**:
  - Create the `@becwright` scope/org on npm and ensure the account also owns the
    unscoped `becwright` name.
  - Add an automation access token as the `NPM_TOKEN` repository secret.

## Cutting a release

1. Bump the version in `pyproject.toml` (the npm versions are derived from the
   git tag at publish time, so they don't need editing).
2. Commit, then create a **GitHub release** whose tag is `vX.Y.Z` (must match
   `pyproject.toml`).
3. Publishing the release triggers `release.yml`, which:
   - builds and smoke-tests the binary on all platforms (macOS as a universal2 binary),
   - stages each binary into its `@becwright/<target>` package
     (`npm/stage.mjs`),
   - sets every npm package version from the tag (`npm/set-version.mjs`),
   - publishes the platform packages first, then the launcher,
   - builds and publishes the Python package to PyPI.

## Compatibility (from 1.0.0 on)

Once `1.0.0` ships, the public contract (the `rules.yaml` schema, the `.bec.yaml`
bundle format, built-in check names and flags, CLI commands and exit codes, the
`check --json` shape, and MCP tool signatures) follows a **one-minor-of-notice
deprecation policy**:

- Never remove or break anything in the contract inside a minor or patch.
- To retire something, mark it **deprecated** in a minor (it keeps working and
  warns), then remove it only in the **next major**.
- A change that would break a `1.x` rule file, bundle, or check script belongs in
  a major bump, not a minor.

See the [stability & versioning doc](stability.md)
for the user-facing statement.

## Notes

- Platform packages are published before the launcher so the launcher's
  `optionalDependencies` resolve immediately.
- `npm publish` is not idempotent: re-running for an already-published version
  fails. Bump the version to re-release.
- To test binary builds without releasing, run the **Build binaries** workflow
  manually (`workflow_dispatch`).
