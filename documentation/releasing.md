# Releasing

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
   - builds and smoke-tests the binary on all five platforms,
   - stages each binary into its `@becwright/<target>` package
     (`npm/stage.mjs`),
   - sets every npm package version from the tag (`npm/set-version.mjs`),
   - publishes the platform packages first, then the launcher,
   - builds and publishes the Python package to PyPI.

## Notes

- Platform packages are published before the launcher so the launcher's
  `optionalDependencies` resolve immediately.
- `npm publish` is not idempotent: re-running for an already-published version
  fails. Bump the version to re-release.
- To test binary builds without releasing, run the **Build binaries** workflow
  manually (`workflow_dispatch`).
