> **English** · [Español](README.es.md)

<p align="center">
  <img src="assets/becwright-logo.svg" alt="becwright" width="140" height="140">
</p>

# becwright

[![CI](https://github.com/DataDave-Dev/becwright/actions/workflows/ci.yml/badge.svg)](https://github.com/DataDave-Dev/becwright/actions/workflows/ci.yml)
[![npm](https://img.shields.io/npm/v/becwright?logo=npm)](https://www.npmjs.com/package/becwright)
[![PyPI](https://img.shields.io/pypi/v/becwright?logo=pypi&logoColor=white)](https://pypi.org/project/becwright/)

**Rules that run, not notes that get ignored.**

<p align="center">
  <img src="assets/becwright-demo.svg" alt="becwright blocking a commit that hardcodes a secret and calls eval" width="640">
</p>

> **See it in 5 seconds** — no setup, no git, nothing on your machine is touched:
> ```bash
> becwright demo                  # after installing (see below)
> # zero-install: npx becwright demo   ·   or: pipx run becwright demo
> ```

`becwright` enforces constraints on your code deterministically: instead of
*asking* an AI agent to respect a rule (the way `CLAUDE.md`, `.cursorrules`,
etc. do — which the agent can read and ignore), becwright **verifies the
result** and blocks the commit if the rule is broken.

## In plain words

New to this kind of tool? Here is the whole idea in three lines:

A **commit** is the moment you *save* your work in git. becwright is a guard
standing at that door. Right before the work is saved, it runs your rules
against the code:

- ✅ everything passes → the commit goes through;
- ❌ a rule is broken → it stops you, names the rule and *why* it exists, and
  waits until you fix it.

A note in `CLAUDE.md` is a *sign* asking people (and AI agents) to behave.
becwright is the *guard that checks*. A sign can be ignored; the guard cannot.

> **Two words you'll see a lot:** a **commit** is a saved snapshot of your code
> in git. A **hook** is a small script git runs automatically at a set moment —
> becwright uses the *pre-commit* hook, which fires just before a commit is
> saved. You never run it by hand; git does.

The rest of this README goes from "just get me started" to the full technical
detail — read as far as you need.

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

You install becwright once; each project only adds a small `.bec/rules.yaml`.
**Two steps and you're done.**

**1. Install** — one line:

```bash
npm install -g becwright
```

<details>
<summary>Prefer pnpm, pip, or a project-local install? →</summary>

```bash
pnpm add -g becwright
pipx install becwright                # or: pip install becwright
npm install --save-dev becwright      # project-local; the hook finds it in node_modules/.bin
```

Via npm/pnpm there's **no Python required** — a self-contained binary ships per
platform (`linux-x64`, `linux-arm64`, `darwin-x64`, `darwin-arm64`, `win32-x64`).
On any other platform, use `pipx install becwright`.
</details>

**2. Set it up** — inside your project:

```bash
becwright init   # detects your language, writes .bec/rules.yaml, installs the pre-commit hook
```

That's it. From now on every `git commit` runs the checks by itself, and stops a
commit that breaks a blocking rule. You never call becwright by hand again.

Available commands:

| Command | What it does |
|---|---|
| `becwright demo` | Show becwright block a sample bad commit (no setup, no git needed) |
| `becwright init` | Scaffold a starter `.bec/rules.yaml` and install the hook |
| `becwright list` | List the built-in checks |
| `becwright check` | Runs the rules over the staged files |
| `becwright install` | Installs the native `pre-commit` hook |
| `becwright uninstall` | Removes the hook |
| `becwright export <id>` | Exports a BEC to a `.bec.yaml` file |
| `becwright import <file\|URL>` | Imports a BEC from another repo |

### Use with AI agents (Claude Code)

becwright is the deterministic net for what an AI agent lets slip. There is a
Claude Code plugin so an agent can install and drive it for you:

```text
/plugin marketplace add DataDave-Dev/becwright
/plugin install becwright@becwright
```

It adds a `becwright` skill and a `/becwright` command. See
[`integrations/claude-code/`](integrations/claude-code/).

For structured results, `becwright check --json` prints a machine-readable
summary, and `becwright mcp` (install the `mcp` extra: `pipx install
"becwright[mcp]"`) runs an MCP server — MCP is a standard way for AI tools to
plug in extra abilities — exposing `check` and `list_checks` to any agent. See
[`documentation/mcp.md`](documentation/mcp.md).

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
    check: "becwright run no_token_in_logs"
    severity: blocking   # blocking = stops the commit | warning = only warns
```

## Included checks

becwright ships ready-to-use checks. Each one is a module invoked from the
`check` field. They work by **searching the text** of your files for a pattern
(a *regex* — a search pattern for text, like "find this exact word"), rather
than truly understanding the code. That keeps them simple and predictable: they
may miss exotic cases, and the real value is in tying each rule to its *why*.

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
    check: "becwright run hardcoded_secrets"
    severity: blocking

  - id: no-debug-remnants
    intent: >
      Debug code (breakpoints, pdb) must not be committed.
    why_it_matters: >
      A forgotten breakpoint hangs the process in production or CI.
    paths: ["src/**/*.py"]
    check: "becwright run debug_remnants"
    severity: blocking

  - id: no-dangerous-eval
    intent: >
      Do not use eval()/exec(), which execute arbitrary code.
    why_it_matters: >
      eval/exec on untrusted input is remote code execution.
    paths: ["src/**/*.py"]
    check: "becwright run dangerous_eval"
    severity: blocking

  - id: no-wildcard-imports
    intent: >
      Avoid 'from x import *', which pollutes the namespace.
    why_it_matters: >
      Wildcard imports hide where each name comes from and break static
      analysis.
    paths: ["src/**/*.py"]
    check: "becwright run wildcard_imports"
    severity: warning
```

## Ready-made rules (no writing required)

Don't want to write rules yourself? Import one from the [catalog](becs/) with a
single command — becwright shows you the rule, then drops it into your
`.bec/rules.yaml`, ready to go:

```bash
# Python
becwright import https://raw.githubusercontent.com/DataDave-Dev/becwright/main/becs/no-token-in-logs.bec.yaml
becwright import https://raw.githubusercontent.com/DataDave-Dev/becwright/main/becs/no-debug-remnants.bec.yaml

# JavaScript / TypeScript
becwright import https://raw.githubusercontent.com/DataDave-Dev/becwright/main/becs/no-debugger-js.bec.yaml
becwright import https://raw.githubusercontent.com/DataDave-Dev/becwright/main/becs/no-console-log-js.bec.yaml

# Any language
becwright import https://raw.githubusercontent.com/DataDave-Dev/becwright/main/becs/no-hardcoded-secrets.bec.yaml
```

The full list (Python, JS/TS, Go, Rust) lives in [`becs/`](becs/).

## Any language

becwright is **language-agnostic**: the engine only filters files by their
`paths` (written as *globs* — file patterns like `src/**/*.js`, where `*` means
"any name" and `**` means "any folder, however deep") and runs the `check` as a
command; it never assumes Python. You can watch JavaScript, Go, Rust, or
anything else.

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
    check: "becwright run forbid --pattern '\\bdebugger\\b'"
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

Built-in checks (`becwright run *`) travel with the package, so
the bundle only stores their name. A **custom** check (`.bec/checks/foo.py`)
travels with its code embedded and lands in `.bec/checks/` of the target repo.

## Documentation

Full docs live in [`documentation/`](documentation/). Each page opens with a
plain-language summary and then goes deeper, so start wherever you are:

- **Just getting started:** [usage](documentation/usage.md) — install, the
  commands, and how to write a rule.
- **Want to add your own rule:** [writing checks](documentation/writing-checks.md)
  — from the no-code `forbid` shortcut to a custom check in any language.
- **Sharing rules between projects:** [portability](documentation/portability.md).
- **Curious how it works inside:** [architecture & flow](documentation/architecture.md).
- **Wiring it to an AI agent:** [MCP & JSON output](documentation/mcp.md).

## Current status

becwright is **published and installable on every platform**: via npm/pnpm as a
self-contained binary (no Python) and via pip/pipx. The packaged engine
(`src/becwright/`) ships a CLI (`demo` / `init` / `list` / `check` (with
`--json`) / `run` / `install` / `uninstall` / `export` / `import` / `mcp`), a native git
hook, built-in checks (Python + the generic `forbid` for any language), BEC
portability between repos, and a catalog with Python, JS/TS, Go and Rust BECs.

For AI agents there is a **Claude Code plugin** and an **MCP server**
(`becwright mcp`) alongside structured `check --json` output. The original
prototype is **archived** under `prototype/` as a reference, and the test suite
is green.

Future work (AST analysis, deep per-language tooling, cryptographic signing of
verifications) is documented in the project plan.
