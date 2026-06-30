> **English** · [Español](README.es.md)

# becwright

**Rules that run, not notes that get ignored.**

`becwright` enforces constraints on your code deterministically: instead of
*asking* an AI agent to respect a rule (the way `CLAUDE.md`, `.cursorrules`,
etc. do — which the agent can read and ignore), becwright **verifies the
result** and blocks the commit if the rule is broken.

## The problem

An AI agent writes code and leaves a note: *"this must never log session
tokens"*. That note is text. Three months later, another agent regenerates the
module, doesn't read it, and drops the token into the logs. Nobody notices
until it blows up in production.

Notes are **probabilistic** (they depend on the agent reading, understanding and
obeying). becwright is **deterministic**: the rule runs against the real code
and returns pass/fail, no matter which agent or model made the change.

| | Note in CLAUDE.md | becwright rule |
|---|---|---|
| What it does | *Asks* to be respected | *Verifies* it was respected |
| Depends on | The agent reading and obeying | Nothing — it runs against the code |
| Result | Likely | Guaranteed |
| Analogy | A "speed limit" sign | A physical bump in the road |

The two layers are complementary: CLAUDE.md prevents (so 95% comes out right the
first time), becwright is the safety net for the 5% that slips through.

## Core concept: BEC (Bound Executable Constraint)

A BEC is a constraint with three properties that no current artifact has
together:

- **Bound** — the rule is born tied to the *intent* and the decision that
  created it (the *why*); it is not a loose rule without context.
- **Executable** — it carries a check that runs and returns pass/fail; it is not
  prose someone promises to respect.
- **Portable** — it can be exported from one repo and imported into another,
  like a package (this is what creates the network effect over time).

## How to use it

becwright is installed once as a tool; each repo only contributes its own
`.bec/rules.yaml`.

```bash
# 1. Install the engine (once, global)
pipx install git+https://github.com/DataDave-Dev/becwright.git   # or local: pipx install .

# 2. In the repo where you want the rules, install the git hook
becwright install                   # writes .git/hooks/pre-commit

# 3. Write your rules in .bec/rules.yaml (see examples below)
# 4. Done: each commit runs the checks; if a blocking rule fails, it stops.
```

Available commands:

| Command | What it does |
|---|---|
| `becwright check` | Runs the rules over the staged files |
| `becwright install` | Installs the native `pre-commit` hook |
| `becwright uninstall` | Removes the hook |
| `becwright export <id>` | Exports a BEC to a `.bec.yaml` file |
| `becwright import <file\|URL>` | Imports a BEC from another repo |

A rule in `.bec/rules.yaml`:

```yaml
rules:
  - id: no-token-in-logs
    intent: >
      Session tokens and credentials must never reach any log.
    why_it_matters: >
      If a token shows up in the logs, anyone with access to them can steal a
      user's session.
    paths: ["src/**/*.py"]
    check: "python3 -m becwright.checks.no_token_in_logs"
    severity: blocking   # blocking = stops the commit | warning = only warns
```

## Included checks

becwright ships ready-to-use checks. Each one is a module invoked from the
`check` field. They are **text/regex based** (no AST analysis), so they are
conservative and may have edge cases; the value is in tying each rule to its
*why*.

| Check | What it detects | Language | Suggested severity |
|---|---|---|---|
| `forbid` | Any regex you pass (`--pattern`) | any | depends on the case |
| `no_token_in_logs` | Tokens/credentials in log calls | Python | `blocking` |
| `hardcoded_secrets` | AWS keys, private keys, `password = "..."` literals | any | `blocking` |
| `debug_remnants` | Forgotten `breakpoint()`, `pdb.set_trace()`, `import pdb` | Python | `blocking` |
| `dangerous_eval` | `eval()` / `exec()` calls | any | `blocking` |
| `wildcard_imports` | `from x import *` | Python | `warning` |

Example rules to copy into your `.bec/rules.yaml`:

```yaml
rules:
  - id: no-hardcoded-secrets
    intent: >
      No secret (key, token, password) should be hardcoded in the code.
    why_it_matters: >
      A secret in the repo stays in git history forever and is visible to
      anyone with access to the code.
    paths: ["src/**/*.py"]
    check: "python3 -m becwright.checks.hardcoded_secrets"
    severity: blocking

  - id: no-debug-remnants
    intent: >
      Debug code (breakpoints, pdb) must not be committed.
    why_it_matters: >
      A forgotten breakpoint hangs the process in production or CI.
    paths: ["src/**/*.py"]
    check: "python3 -m becwright.checks.debug_remnants"
    severity: blocking

  - id: no-dangerous-eval
    intent: >
      Do not use eval()/exec(), which execute arbitrary code.
    why_it_matters: >
      eval/exec on untrusted input is remote code execution.
    paths: ["src/**/*.py"]
    check: "python3 -m becwright.checks.dangerous_eval"
    severity: blocking

  - id: no-wildcard-imports
    intent: >
      Avoid 'from x import *', which pollutes the namespace.
    why_it_matters: >
      Wildcard imports hide where each name comes from and break static
      analysis.
    paths: ["src/**/*.py"]
    check: "python3 -m becwright.checks.wildcard_imports"
    severity: warning
```

## Any language

becwright is **language-agnostic**: the engine only filters files by their
`paths` (globs) and runs the `check` as a command; it never assumes Python. You
can watch JavaScript, Go, Rust, or anything else.

The fastest way to write a rule for another language —without writing code— is
the `forbid` check, which fails if a regex appears in the files:

```yaml
rules:
  - id: no-debugger-js
    intent: >
      Do not leave 'debugger;' in JavaScript/TypeScript code.
    why_it_matters: >
      A forgotten 'debugger' halts execution and should not reach production.
    paths: ["**/*.js", "**/*.ts"]
    check: "python3 -m becwright.checks.forbid --pattern '\\bdebugger\\b'"
    severity: blocking
```

`forbid` accepts `--pattern REGEX`, `--ignore-case` and `--message TEXT`. For
finer checks, write your own script in whatever language you want (an executable
that reads the file list from stdin and exits with code 0/1) and point `check`
at it.

## Sharing BECs between repos

A BEC is **portable**: you can take it out of one repo and install it in
another. A bundle is a single self-contained `.bec.yaml` file (the rule + the
check's code if it is custom).

```bash
# In the source repo: export a rule to a file
becwright export no-token-in-logs -o no-token-in-logs.bec.yaml

# In another repo: import it (from a file or an http/https URL)
becwright import no-token-in-logs.bec.yaml
becwright import https://example.com/no-token-in-logs.bec.yaml
```

On import, becwright **shows the check's code and asks for confirmation** before
installing it: importing a BEC is importing code that will run on every commit.
Use `--yes` to skip the confirmation in automated environments.

There is a **catalog of ready-to-use BECs** in [`becs/`](becs/) that you can
import directly from their raw URL.

Built-in checks (`python3 -m becwright.checks.*`) travel with the package, so
the bundle only stores their name. A **custom** check (`.bec/checks/foo.py`)
travels with its code embedded and lands in `.bec/checks/` of the target repo.

## Current status

The **installable MVP** is built and verified end-to-end: packaged engine
(`src/becwright/`), CLI (`check` / `install` / `uninstall` / `export` /
`import`), native git hook that blocks a commit with a token in a log, included
checks (Python + the generic `forbid` for any language), BEC portability between
repos, a catalog with Python and JS/TS BECs, and a green test suite. The original
prototype is **archived** under `prototype/` as a reference.

Future work (AST analysis, deep per-language tooling, cryptographic signing of
verifications) is documented in the project plan.
