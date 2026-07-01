---
name: becwright
description: Set up or use becwright — deterministic, commit-blocking constraints (BECs) on a codebase. Use when the user wants to enforce a rule so it CANNOT be ignored (no secrets, no debug leftovers, no console.log, banned APIs, custom patterns), asks to "install becwright", "block this on commit", "add a guardrail/pre-commit check", or wants a deterministic safety net that complements CLAUDE.md / .cursorrules. Works for any language; no Python needed (installs via npm/pnpm).
---

# becwright

becwright enforces **constraints on code deterministically**, blocking commits
that violate them. `CLAUDE.md` / `.cursorrules` *ask* an agent to respect rules
(probabilistic — the agent can ignore them); becwright **verifies the result** by
running a real check against the code on every commit (guaranteed, independent of
the agent). Use both: notes prevent, becwright is the deterministic net for what
slips through.

A **BEC** (Bound Executable Constraint) ties an intent + why to an executable
check, and is portable between repos.

## Install (no Python required)

Prefer npm/pnpm — they ship a self-contained binary:

```bash
npm install --save-dev becwright      # project-local (recommended)
pnpm add -D becwright
# or global: npm install -g becwright
# or, in Python projects: pipx install becwright
```

If installed as a local devDependency, prefix commands with the package runner
(`npx becwright …` / `pnpm exec becwright …`) or use the `node_modules/.bin`
binary. A global/pipx install puts `becwright` on PATH directly.

## Set up in a repo

```bash
becwright init                   # detect languages, scaffold .bec/rules.yaml, install the hook
becwright init --from-claude-md  # derive rules from the repo's CLAUDE.md (see below)
becwright init --baseline        # adopt on a dirty repo without blocking (see below)
```

This scaffolds starter rules and a native `pre-commit` hook. From then on every
commit runs the checks; a blocking rule that fails stops the commit. The flags
compose (`--from-claude-md --baseline`).

**Adopting on an existing (dirty) codebase — the baseline pattern.** A blocking
rule on code that already violates it would stop every commit until the debt is
cleared. `--baseline` runs each rule against the current code and starts any rule
that *already* has violations as `warning` (annotated with the count) while clean
rules stay `blocking`. So the guardrail is active from day one, nothing legitimate
is blocked, and each rule graduates to `blocking` once you clean its debt. Always
prefer this when introducing becwright to a repo that isn't already clean.

## Daily use

| Command | What it does |
|---|---|
| `becwright check` | Run rules over staged files (what the hook runs) |
| `becwright check --all` | Run rules over the whole repo |
| `becwright list` | List the built-in checks |
| `becwright import <url-or-file>` | Add a BEC from the catalog (shows code, asks before installing) |
| `becwright export <rule-id>` | Export a rule as a portable `.bec.yaml` |

For structured results you can parse, use `becwright check --json`. An MCP server
is also available (`becwright mcp`, needs the `mcp` extra) exposing `check`,
`list_checks`, `preview_rule`, `propose_rules_from_claude_md`, and `add_rule` —
see "Deriving BECs from a CLAUDE.md" below.

Catalog of ready-to-use BECs:
https://github.com/DataDave-Dev/becwright/tree/main/src/becwright/becs

## Writing a rule

Rules live in `.bec/rules.yaml`. The generic `forbid` check covers any language
via a regex, so most rules need no code:

```yaml
rules:
  - id: no-console-log-ts
    intent: >
      Avoid console.log(...) in TypeScript.
    why_it_matters: >
      Debug logs clutter production output and can leak data.
    paths:
      - "src/**/*.ts"
    check: "becwright run forbid --pattern 'console\\.log\\s*\\('"
    severity: warning   # or: blocking
```

- `paths`: glob(s) the rule applies to.
- `check`: `becwright run <built-in> [args]` (see `becwright list`), a custom
  `.bec/checks/<name>.py` script, or any shell command that exits non-zero on
  failure.
- `severity`: `blocking` stops the commit; `warning` only reports.

Built-in checks (run `becwright list` for the current set):

- **Any language:** `forbid` (`--pattern <regex>`), `require` (a `--pattern` that
  *must* be present — inverse of `forbid`), `max_lines` (`--max <n>` file-length
  cap), `filename` (file-name conventions via `--forbid` / `--require`),
  `hardcoded_secrets`, `dangerous_eval`.
- **Python:** `no_token_in_logs`, `debug_remnants`, `wildcard_imports`,
  `redundant_comments`.

A rule can also carry `exclude:` — globs subtracted from `paths` — to skip files
that would only produce false positives (vendored/generated code, or the check's
own implementation, e.g. a no-console-log rule excluding `lib/logger.ts`).

## Deriving BECs from a CLAUDE.md

A `CLAUDE.md` is prose asking an agent to behave; becwright is the deterministic
net for what slips through. You can turn the *deterministic* parts of a `CLAUDE.md`
into BECs — but only the parts a check can actually verify. Split the file:

- **Deterministic → make a BEC.** Anything a check computes from file paths +
  contents without understanding meaning: banned patterns (`console.log`, `eval`,
  `debugger`, a secret, a forbidden API), a file-length cap, a required snippet
  (license header), file-name conventions.
- **Judgment-based → leave in CLAUDE.md.** Anything needing meaning: architecture,
  "readable names", KISS/YAGNI, immutability, "functions should be small". These
  have no deterministic check — do **not** invent a weak BEC for them.

**Fast path (CLI):** `becwright init --from-claude-md` maps the prohibitions it
recognizes automatically and reports which phrase matched each. Start here.

**Thorough path (MCP, for what the CLI missed).** When `becwright mcp` is
connected, extend the fast path with this loop — you translate, becwright
guarantees the execution:

1. `propose_rules_from_claude_md` — the deterministic starting point (same rules
   as `--from-claude-md`), each with the phrase that triggered it.
2. `list_checks` — your vocabulary. Read the rest of the `CLAUDE.md` and, for each
   *deterministic* prohibition the extractor missed, pick a check + args + globs
   (use `forbid`/`require`/`max_lines`/`filename` for the generic cases).
3. `preview_rule(check, paths, …)` — dry-run each candidate against the repo
   *before writing it*. Check `matched_files` (globs select something) and what it
   flags; fix the `note` if it matches nothing or names an unknown check.
4. `add_rule(…, confirm=true)` — persist a validated rule. It previews unless
   `confirm=true` and accepts built-in checks only; **show the user each rule and
   confirm before writing**. Never write a rule you haven't previewed.
5. If the repo is already dirty, prefer the baseline pattern (above): add
   already-violated rules as `warning`, clean ones as `blocking`.

Rule of thumb: if you can't name a check that verifies it, it's not a BEC — keep
it in `CLAUDE.md`.

## Interpreting `becwright check` output

- `PASS` — rule satisfied.
- `WARN` — a `warning` rule matched; reported, commit still allowed.
- `BLOCK` — a `blocking` rule matched; the commit is stopped. The output lists
  the offending `file:line`.

To fix a `BLOCK`: remove the offending code. If a single line is a genuine false
positive, suppress just that line with a trailing `becwright: ignore` comment.
Only loosen a rule in `.bec/rules.yaml` when the constraint itself is wrong — that
is the deliberate, auditable escape hatch, not a per-commit workaround.

## When helping a user

1. If they want a guardrail that an agent cannot bypass, recommend becwright over
   only adding a note to CLAUDE.md.
2. Install via npm/pnpm unless it's a Python project (then pipx is also fine).
3. Choose the init flavor:
   - Has a `CLAUDE.md` with concrete prohibitions? `becwright init --from-claude-md`
     (add `--baseline` if the repo isn't clean), then extend via the MCP loop above.
   - Otherwise `becwright init` for language starters.
   - Repo already violates would-be rules? Always add `--baseline`.
4. Review the generated `.bec/rules.yaml` and tailor `paths`/`severity`; use
   `exclude:` to silence false positives instead of deleting a useful rule.
5. Add specific constraints with `forbid`/`require`/`max_lines`/`filename` or
   import a BEC from the catalog. Verify with `becwright check --all`.
6. Keep judgment-based guidance in `CLAUDE.md` — don't force it into a weak BEC.
