> **English** · [Español](usage.es.md)

# Usage

**In short:** install becwright once, run `becwright init` inside your project,
and from then on every time you save your work (a *commit*) it checks your code
against your rules and stops the commit if a blocking rule is broken. That's the
whole loop — the rest of this page is the detail.

## Install

```bash
pipx install becwright      # or: pip install becwright
```

## Set up a repo

```bash
cd your-repo
becwright init              # scaffolds .bec/rules.yaml (language-aware) and installs the hook
```

`init` detects whether the repo has Python or JS/TS files and writes a starter
`.bec/rules.yaml` with matching rules, then installs the pre-commit hook. Review
the generated rules and run `becwright check --all` to see the current state.

From then on, every `git commit` runs the checks. (You can also set up by hand:
`becwright install` plus a `.bec/rules.yaml` you write yourself.)

> **Adopting on an existing codebase?** Run `becwright init --baseline`. It runs
> the starter rules against your current code and starts any rule that *already*
> has violations as `warning` instead of `blocking`, so becwright never blocks a
> commit on pre-existing debt. Clean rules stay `blocking` — a guardrail from day
> one. Each downgraded rule is annotated with its violation count; clean the debt
> over time, then flip it back to `blocking`.

## Commands

| Command | Description |
|---|---|
| `becwright demo` | Show becwright block a sample bad commit (no setup, no git needed) |
| `becwright init` | Scaffold a starter `.bec/rules.yaml` and install the hook |
| `becwright init --baseline` | Same, but start already-violated rules as `warning` (adopt on a dirty codebase without blocking) |
| `becwright list` | List the built-in checks |
| `becwright check` | Run rules over the staged files |
| `becwright check --all` | Run rules over the whole repo (`git ls-files`) |
| `becwright install` | Install the pre-commit hook |
| `becwright uninstall` | Remove the hook |
| `becwright export <id> [-o file]` | Export a rule to a `.bec.yaml` bundle |
| `becwright import <source> [--yes]` | Import a BEC from a file or http(s) URL |

> **"Staged files"?** When you run `git add`, the files you picked are *staged* —
> queued for the next commit. `becwright check` looks only at those by default
> (the exact set the commit will create), which is why it's fast. Use
> `--all` to scan the whole project instead.

Exit codes (the number a command returns when it ends; `0` means success):
`0` pass · `1` a blocking rule failed · `2` not a git repo / usage error.

## The rules file: `.bec/rules.yaml`

```yaml
rules:
  - id: no-token-in-logs        # unique identifier
    intent: >                   # what the rule asks for (the "bound" part)
      Session tokens must never reach any log.
    why_it_matters: >           # why it exists (shown when the rule fails)
      A token in the logs lets anyone steal a session.
    rejected_alternatives:      # optional: approaches considered and dropped
      - "Redact at log time -> too easy to bypass"
    paths:                      # glob patterns of files this rule applies to
      - "src/**/*.py"
    exclude:                    # optional: globs carved out of `paths`
      - "src/logging_setup.py"  #   (e.g. the check's own implementation)
    check: "becwright run no_token_in_logs"
    severity: blocking          # blocking (stops commit) | warning (only warns)
```

### Fields

| Field | Required | Meaning |
|---|---|---|
| `id` | yes | Unique rule id |
| `paths` | yes | Glob patterns (see below) |
| `check` | yes | Shell command to run (the executable check) |
| `exclude` | no | Globs subtracted from `paths` (see below) |
| `intent` | no | What the rule enforces |
| `why_it_matters` | no | Why it matters; printed when the rule fails |
| `rejected_alternatives` | no | Context: approaches that were dismissed |
| `severity` | no | `blocking` (default) or `warning` |

### Globs

- `*` matches anything except `/`.
- `**` matches across directories.
- e.g. `src/**/*.py` matches `src/a.py` and `src/x/y/z.py`; `src/*.py` matches
  only the top level.

### Excluding files

`exclude` carves globs out of `paths`, so one rule can cover a whole language
while skipping files that would only produce false positives — vendored code,
generated files, or the check's own implementation. A file matched by both
`paths` and `exclude` is skipped.

```yaml
  - id: no-console-log
    paths:
      - "**/*.ts"
    exclude:
      - "lib/logger.ts"   # the logger legitimately wraps console.log
    check: "becwright run forbid --pattern 'console\\.log'"
    severity: warning
```

`exclude` travels with the rule through `export` / `import`, so the carve-out is
portable with the BEC.

## Pre-made rules

becwright ships a [catalog](../src/becwright/becs/) of ready-to-use BECs inside
the package — install from it with one command, no URL, works offline:

```bash
becwright search              # list the catalog
becwright add no-debugger-js  # install one
```
