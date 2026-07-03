> **English** · [Español](usage.es.md)

# Usage

**In short:** install becwright once, run `becwright init` inside your project,
and from then on every time you save your work (a *commit*) it checks your code
against your rules and stops the commit if a blocking rule is broken. That's the
whole loop — the rest of this page is the detail.

## Install

```bash
pipx install becwright      # or: pip install becwright / uv tool install becwright
```

(Or without Python at all: `npm install -g becwright` ships a self-contained
binary per platform.)

## Set up a repo

```bash
cd your-repo
becwright init              # scaffolds .bec/rules.yaml (language-aware) and installs the hook
```

`init` detects whether the repo has Python or JS/TS files and writes a starter
`.bec/rules.yaml` with matching rules, then installs the pre-commit hook. If a
hook manager already owns the hooks (Husky, the pre-commit framework, or a
custom `core.hooksPath`), `init` skips its own hook and prints the exact line
to add to that manager instead. Review the generated rules and run
`becwright check --all` to see the current state.

From then on, every `git commit` runs the checks. (You can also set up by hand:
`becwright install` plus a `.bec/rules.yaml` you write yourself.)

> **Adopting on an existing codebase?** Run `becwright init --baseline`. It runs
> the starter rules against your current code and starts any rule that *already*
> has violations as `warning` instead of `blocking`, so becwright never blocks a
> commit on pre-existing debt. Clean rules stay `blocking` — a guardrail from day
> one. Each downgraded rule is annotated with its violation count; clean the debt
> over time, then flip it back to `blocking`.

> **Already have a `CLAUDE.md` (or similar)?** Run `becwright init --from-claude-md`.
> It scans the file for prohibitions it recognizes — secrets, `eval`, `debugger`,
> `console.log`, breakpoints, wildcard imports, tokens in logs — and turns each
> into an enforceable rule, reporting which phrase matched. It also picks up a
> per-file line cap ("files under 800 lines" → `max_lines`), ignoring
> function-length rules it can't enforce. A broad phrase like "follow good
> practices" expands to the deterministic hygiene set (no secrets, `eval`, debug
> leftovers, or merge-conflict markers), and phrases like "conventional commits"
> or "no AI attribution" become `commit-msg` rules. This is best-effort and
> language-aware,
> so **review the result**; judgment-based guidance (architecture, naming,
> immutability) has no deterministic check and stays in `CLAUDE.md`. Combine with
> `--baseline` to adopt on a dirty repo in one step.

## Commands

| Command | Description |
|---|---|
| `becwright demo` | Show becwright block a sample bad commit (no setup, no git needed) |
| `becwright init` | Scaffold a starter `.bec/rules.yaml` and install the hook |
| `becwright init --baseline` | Same, but start already-violated rules as `warning` (adopt on a dirty codebase without blocking) |
| `becwright init --from-claude-md` | Derive rules from the repo's `CLAUDE.md` (best-effort; maps known prohibitions to checks) |
| `becwright list` | List the built-in checks |
| `becwright check` | Run rules over the staged files |
| `becwright check --all` | Run rules over the whole repo (`git ls-files`) |
| `becwright validate` | Validate `.bec/rules.yaml` — YAML, duplicate ids, unknown checks — without running anything |
| `becwright doctor` | Diagnose the setup: rules file, checks, hooks, and hook managers (Husky, pre-commit) |
| `becwright install` | Install the pre-commit hook |
| `becwright uninstall` | Remove the hook |
| `becwright export <id> [-o file]` | Export a rule to a `.bec.yaml` bundle |
| `becwright import <source> [--yes]` | Import a BEC from a file or http(s) URL |

> **"Staged files"?** When you run `git add`, the files you picked are *staged* —
> queued for the next commit. `becwright check` looks only at those by default
> (the exact set the commit will create), which is why it's fast. Use
> `--all` to scan the whole project instead.

### Exit codes

The number a command returns when it ends. These are part of becwright's stable
contract — scripts and CI can rely on them:

| Code | Meaning |
|---|---|
| `0` | Passed — no blocking rule failed (or there was nothing to check). |
| `1` | A **blocking** rule failed. This is the signal that stops a commit. A `warning`/`advisory` finding alone does **not** set this. |
| `2` | A problem to fix before becwright can judge: not a git repository, a malformed/untrusted `.bec/rules.yaml`, a rule pointing at a non-existent built-in check, or a usage error. |

### `check --json`

`becwright check --json` prints one JSON object and still uses the exit codes
above (`1` when blocked). The shape is stable:

```json
{
  "rule_count": 2,
  "checked_files": 5,
  "blocked": true,
  "results": [
    {
      "id": "no-token-in-logs",
      "severity": "blocking",
      "passed": false,
      "intent": "Session tokens must never reach any log.",
      "why_it_matters": "A token in the logs lets anyone steal a session.",
      "output": "src/app.py:12: token=..."
    }
  ]
}
```

`intent`, `why_it_matters` and `output` are `null` when absent. `results` is
empty when there was nothing to evaluate.

## The rules file: `.bec/rules.yaml`

```yaml
schema_version: 1               # optional format version; absent means 1
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
| `paths` | yes* | Glob patterns (see below); not needed for `commit-msg` rules |
| `check` | yes | Shell command to run (the executable check) |
| `exclude` | no | Globs subtracted from `paths` (see below) |
| `intent` | no | What the rule enforces |
| `why_it_matters` | no | Why it matters; printed when the rule fails |
| `rejected_alternatives` | no | Context: approaches that were dismissed |
| `severity` | no | `blocking` (default), `warning`, or `advisory` (see below) |
| `target` | no | `files` (default) or `commit-msg` (see below) |

**`schema_version`** is an optional top-level key (not a rule field). It stamps
the format version of the file; when absent it is treated as `1`, so existing
files keep working. `becwright init` writes it, and becwright refuses a file
stamped a *newer* version than it understands — telling you to upgrade — rather
than misreading it. You rarely touch it by hand.

> **Stable field set.** The nine fields above are frozen as of `schema_version 1`.
> From `1.0.0` on, a field is only added or removed under the
> [deprecation policy](stability.md) (deprecated with a
> warning for at least one minor, removed only in the next major), so a rules file
> that is valid today stays valid across the whole `1.x` line.

**Severity — guaranteed vs assisted.** `blocking` and `warning` are for
*deterministic* checks: the same code always gives the same verdict, so a
`blocking` rule is a **100% guarantee**. `advisory` is the honest home for
*judgment* rules whose check isn't deterministic — e.g. one that calls an LLM to
review readability or design. An `advisory` rule **reports but never blocks**, and
shows up labelled `ADVISORY (best-effort, not a guarantee)`, so you always know
which findings are guaranteed and which are assisted. becwright supplies the tier;
the reviewer is your own check command (point it at whatever tool you like), so
there is no LLM dependency in becwright itself.

### Globs

- `*` matches anything except `/`.
- `**` matches across directories.
- e.g. `src/**/*.py` matches `src/a.py` and `src/x/y/z.py`; `src/*.py` matches
  only the top level.

### Commit message rules (`target: commit-msg`)

A rule with `target: commit-msg` checks the **commit message** instead of the
changed files (`becwright init` installs a `commit-msg` hook alongside the
`pre-commit` one). It needs no `paths`; the message is fed to the check, so the
generic `require` / `forbid` checks work on it. Two examples `--from-claude-md`
can generate for you (from phrases like "conventional commits" / "no AI
attribution"):

```yaml
  - id: conventional-commits
    target: commit-msg
    check: |-
      becwright run require --pattern '^(feat|fix|docs|refactor|test|chore|ci|perf|build|style|revert)(\(.+\))?!?: '
    severity: blocking
  - id: no-ai-attribution
    target: commit-msg
    check: |-
      becwright run forbid --ignore-case --pattern 'co-authored-by:.*(claude|anthropic|gpt|copilot)|generated with.*(claude|chatgpt|copilot)'
    severity: blocking
```

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

## Performance and limits

Honest notes on how the engine runs, so you can predict its behavior:

- **One process per rule.** Each rule's `check` runs as its own subprocess over
  the matched files. On the normal commit path (a handful of staged files) this
  is instantaneous. `becwright check --all` on a very large repo with many
  rules pays one process start per rule — fast in practice, but not designed as
  a whole-monorepo scanner. In CI, prefer `check --diff <base>`, which only
  looks at what the PR changed.
- **A hung check cannot freeze your commit.** Every check is capped at 30
  seconds; override with the `BECWRIGHT_CHECK_TIMEOUT` environment variable
  (seconds; `0` disables the cap) for slow whole-repo runs.
- **One `.bec/rules.yaml` per repository**, at the root. There is no
  per-package rules file for monorepos yet — scope rules to packages with
  `paths`/`exclude` globs instead (e.g. `paths: ["packages/api/**/*.ts"]`).
- **Checks judge the staged content.** On commit, checks run against a snapshot
  of what the commit will actually record — not your working tree, which may
  hold unstaged edits. See the note in [recipes](recipes.md) if a check wraps
  an external tool that expects a git repository.
