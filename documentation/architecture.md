> **English** · [Español](architecture.es.md)

# Architecture

becwright is a small engine that runs **checks** against your files and decides
whether a commit may proceed. It is language-agnostic: it never parses your code
itself — it matches files by path and runs a command.

## Components

| Module | Responsibility |
|---|---|
| `cli.py` | Argparse CLI: `init / list / check / install / uninstall / export / import` |
| `rules.py` | The `Rule` model and loading of `.bec/rules.yaml` |
| `engine.py` | Glob path matching, running checks, deciding pass/fail |
| `git.py` | Repo root, staged files, the native pre-commit hook |
| `checks/` | Built-in checks (one module each) |
| `bundle.py` | Export/import of BECs (the portable `.bec.yaml`) |

The engine ships as an installed package; the repo being watched only contributes
its own `.bec/rules.yaml`. That decoupling is why becwright can be installed once
and used across many repos.

## The check flow

```mermaid
flowchart TD
    A[git commit] --> B["pre-commit hook runs 'becwright check'"]
    B --> C[load .bec/rules.yaml into Rules]
    C --> D[get staged files from git]
    D --> E{for each rule}
    E --> F[match files against rule.paths globs]
    F --> G["run rule.check as a shell command, files on stdin"]
    G --> H{exit code}
    H -->|0| I[PASS]
    H -->|non-zero| J{severity}
    J -->|blocking| K[BLOCK: commit rejected, exit 1]
    J -->|warning| L[WARN: commit allowed]
```

1. A commit triggers the pre-commit hook, which runs `becwright check`.
2. becwright loads the rules from `.bec/rules.yaml`.
3. It asks git for the staged files.
4. For each rule, it filters the files by the rule's `paths` globs and runs the
   rule's `check` command, passing the matching files on stdin.
5. The check's exit code decides the result: `0` passes; non-zero fails.
6. If any **blocking** rule failed, the commit is rejected (exit 1). Warnings are
   printed but never block.

## The check contract

The engine runs `rule.check` as a shell command with `cwd` set to the repo root,
and feeds it the relevant file paths (one per line) on **stdin**. A check:

- reads the file list from stdin,
- prints any violations to stdout (shown under "Found in:"),
- exits **0** if everything is fine, **non-zero** if it found a violation.

Because the contract is just "files on stdin, exit code out", a check can be
written in any language. See [writing-checks.md](writing-checks.md).

## Why it is deterministic

Unlike a note in `CLAUDE.md` that asks an agent to behave, a BEC's check runs
against the real code on every commit and returns pass/fail regardless of who or
what produced the change. The rule carries its *intent* and *why* (the "bound"
part), the check makes it *executable*, and a bundle makes it *portable* — see
[portability.md](portability.md).
