> **English** · [Español](usage.es.md)

# Usage

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

## Commands

| Command | Description |
|---|---|
| `becwright init` | Scaffold a starter `.bec/rules.yaml` and install the hook |
| `becwright check` | Run rules over the staged files |
| `becwright check --all` | Run rules over the whole repo (`git ls-files`) |
| `becwright install` | Install the pre-commit hook |
| `becwright uninstall` | Remove the hook |
| `becwright export <id> [-o file]` | Export a rule to a `.bec.yaml` bundle |
| `becwright import <source> [--yes]` | Import a BEC from a file or http(s) URL |

Exit codes: `0` pass · `1` a blocking rule failed · `2` not a git repo / usage error.

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
    check: "python3 -m becwright.checks.no_token_in_logs"
    severity: blocking          # blocking (stops commit) | warning (only warns)
```

### Fields

| Field | Required | Meaning |
|---|---|---|
| `id` | yes | Unique rule id |
| `paths` | yes | Glob patterns (see below) |
| `check` | yes | Shell command to run (the executable check) |
| `intent` | no | What the rule enforces |
| `why_it_matters` | no | Why it matters; printed when the rule fails |
| `rejected_alternatives` | no | Context: approaches that were dismissed |
| `severity` | no | `blocking` (default) or `warning` |

### Globs

- `*` matches anything except `/`.
- `**` matches across directories.
- e.g. `src/**/*.py` matches `src/a.py` and `src/x/y/z.py`; `src/*.py` matches
  only the top level.

## Pre-made rules

becwright ships a [catalog](../becs/) of ready-to-use BECs you can import:

```bash
becwright import https://raw.githubusercontent.com/DataDave-Dev/becwright/main/becs/no-debugger-js.bec.yaml
```
