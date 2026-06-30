---
description: Install, set up, or run becwright — deterministic commit-blocking constraints (BECs) on this repo
argument-hint: "[init | check | add <pattern-or-catalog-url> | status]"
allowed-tools: Bash, Read, Edit, Write
---

Use the **becwright** skill. The user invoked `/becwright` with arguments:
`$ARGUMENTS`.

Interpret the argument and act:

- **(empty) or `init`** — Ensure becwright is installed (prefer `npm install
  --save-dev becwright`, or `pipx install becwright` in a Python project), run
  `becwright init`, then show and briefly explain the generated `.bec/rules.yaml`.
- **`check`** — Run `becwright check --all` and summarize PASS / WARN / BLOCK. For
  any BLOCK, point to the offending `file:line` and propose a fix.
- **`add <thing>`** — If `<thing>` is an http(s) URL or a `.bec.yaml` path, run
  `becwright import <thing>`. Otherwise treat it as a regex and add a `forbid`
  rule to `.bec/rules.yaml` (ask for the target `paths` and `severity` first).
- **`status`** — Report whether becwright is installed, whether the pre-commit
  hook exists, and how many rules are in `.bec/rules.yaml`.

If becwright is not yet installed, install it first. If the current directory is
not a git repository, say so before running `becwright init`.
