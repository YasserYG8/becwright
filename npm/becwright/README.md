# becwright

Deterministically enforces constraints (**BECs** — Bound Executable Constraints)
on your code, blocking commits that violate them. Unlike `CLAUDE.md` or
`.cursorrules`, which *ask* an agent to respect rules, becwright **verifies the
result** by running a real check against the code.

This npm package ships a self-contained binary, so **no Python is required**. The
right binary for your platform is installed automatically as an optional
dependency (the same model used by esbuild and ruff).

## Install

```bash
# project-local (recommended)
npm install --save-dev becwright
pnpm add -D becwright

# or global
npm install -g becwright
```

## Usage

```bash
becwright init       # scaffold .bec/rules.yaml and install the git hook
becwright list       # show the built-in checks
becwright check      # check staged files (runs automatically on commit)
becwright import <url-or-file>   # add a BEC from the catalog
```

When installed as a devDependency, the generated pre-commit hook resolves the
local binary from `node_modules/.bin`, so it works without a global install.

## Supported platforms

`linux-x64`, `linux-arm64`, `darwin-arm64`, `win32-x64`. Intel macOS: use `pipx install becwright`.

On other platforms, install via [pipx](https://pipx.pypa.io): `pipx install becwright`.

## Links

- Source & docs: https://github.com/DataDave-Dev/becwright
- BEC catalog: https://github.com/DataDave-Dev/becwright/tree/main/becs
