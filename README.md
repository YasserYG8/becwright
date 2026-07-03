> **English** · [Español](README.es.md)

<p align="center">
  <img src="assets/becwright-logo.svg" alt="becwright" width="140" height="140">
</p>

# becwright

[![CI](https://github.com/DataDave-Dev/becwright/actions/workflows/ci.yml/badge.svg)](https://github.com/DataDave-Dev/becwright/actions/workflows/ci.yml)
[![npm](https://img.shields.io/npm/v/becwright?logo=npm)](https://www.npmjs.com/package/becwright)
[![npm downloads](https://img.shields.io/npm/dm/becwright?logo=npm&label=downloads)](https://www.npmjs.com/package/becwright)
[![PyPI](https://img.shields.io/pypi/v/becwright?logo=pypi&logoColor=white)](https://pypi.org/project/becwright/)
[![Python versions](https://img.shields.io/pypi/pyversions/becwright?logo=python&logoColor=white)](https://pypi.org/project/becwright/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

**The enforcement layer for AI coding agents.** <sub>(*bec-wright* — a "wright" is a maker, as in *playwright*)</sub>

Rules that run, not notes that get ignored. Your `CLAUDE.md` is a *sign*;
becwright is the *guard* — it runs your rules against the code and blocks the
commit when one breaks, no matter which model (or person) wrote it.

<sub>Deterministic, not probabilistic · any language · no Python required · blocks the commit **and** carries the *why*.</sub>

<sub>Dogfooded — every commit to this repo is gated by becwright's own [`.bec/rules.yaml`](.bec/rules.yaml) in CI.</sub>

## Before / after

Your agent writes `checkout.py` — a hardcoded API key, an `eval()` on a promo
string — and leaves a note to *"clean this up later."* Nobody does. It ships.

With becwright, the commit never happens:

<p align="center">
  <img src="assets/becwright-demo-animated.svg" alt="becwright blocking a commit live: git commit runs, two blocking rules fire with their why, the commit is stopped" width="640">
</p>

> **See it yourself in 5 seconds** — no setup, no git, nothing on your machine is
> touched:
> ```bash
> npx becwright demo        # zero-install   ·   or: uvx becwright demo · pipx run becwright demo
> ```

## Get started

Install once, set up per project. **Two steps and you're done.**

```bash
npm install -g becwright    # self-contained binary, no Python (or: pipx install becwright)
cd your-project
becwright init              # detects your language, writes .bec/rules.yaml, installs the hook
```

That's it. From now on every `git commit` runs the checks by itself and stops a
commit that breaks a blocking rule. You never call becwright by hand again.

> **Which install?** `npm install -g` to try it out or for solo use;
> `npm install --save-dev becwright` for a team repo, so the version is pinned
> in `package.json` and the hook finds it in `node_modules/.bin`.

- **Existing codebase with debt?** `becwright init --baseline` starts
  already-violated rules as `warning` (nothing legitimate is blocked) and clean
  rules as `blocking`. Fix the debt over time, then graduate each rule.
- **Already have a `CLAUDE.md`?** `becwright init --from-claude-md` turns the
  prohibitions it recognizes (secrets, `eval`, `debugger`, `console.log`, …)
  into enforceable rules. Judgment-based guidance stays in `CLAUDE.md`.
  Composes with `--baseline`.

<details>
<summary>Other installs: pnpm, pip, project-local →</summary>

```bash
pnpm add -g becwright
pipx install becwright                # or: pip install becwright / uv tool install becwright
npm install --save-dev becwright      # project-local; the hook finds it in node_modules/.bin
```

Via npm/pnpm there's **no Python required** — a self-contained binary ships per
platform (`linux-x64`, `linux-arm64`, `darwin-x64`, `darwin-arm64`, `win32-x64`).
On any other platform, use `pipx install becwright`.
</details>

### Feel it block, in 90 seconds

The fastest way to trust a guard is to watch it stop you once:

```bash
cd your-project && becwright init          # rules + hook, one command

echo 'api_key = "AKIAIOSFODNN7EXAMPLE"' >> demo_leak.py
git add demo_leak.py && git commit -m "test the guard"
#   BLOCK  no-hardcoded-secrets  (blocking)
#     Why it matters: a secret in the repo stays in git history forever...
#   >>> Commit BLOCKED: a blocking rule was broken.

git reset demo_leak.py && rm demo_leak.py  # undo the experiment
git commit -m "..."                        # normal commits just pass
```

That loop — violate, get blocked *with the why*, fix, commit — is everything
becwright does, forever, automatically.

## Why a guard, not a sign

An AI agent writes a module and notes *"this must never log session tokens."*
Months later another agent regenerates it, never reads the note, and the token
lands in the logs. Nobody notices until it blows up in production.

A sign *asks*; a guard *checks*. Right before your work is saved, becwright runs
your rules against the code: ✅ everything passes → the commit goes through;
❌ a rule is broken → it stops you, names the rule and its *why*, and waits until
you fix it. A `CLAUDE.md` note is **probabilistic** — it depends on the agent
reading and obeying. A becwright rule is **deterministic** — it runs against the
real code and returns pass/fail, no matter which model made the change:

| | Note in CLAUDE.md | becwright rule |
|---|---|---|
| What it does | *Asks* to be respected | *Verifies* it was respected |
| Depends on | The agent reading and obeying | Nothing — it runs against the code |
| Result | Likely | Guaranteed |
| Analogy | A "speed limit" sign | A physical bump in the road |

The two layers are complementary: `CLAUDE.md` prevents (so 95% comes out right the
first time), becwright is the safety net for the 5% that slips through.

<details>
<summary><strong>New to commits and hooks?</strong> — the vocabulary in one box</summary>

A **commit** is a saved snapshot of your code in git. A **hook** is a small
script git runs automatically at a set moment — becwright uses the *pre-commit*
hook, which fires just before a commit is saved. You never run it by hand; git
does.
</details>

## Core concept: BEC (Bound Executable Constraint)

A BEC is a constraint with three properties that no current artifact has
together:

- **Bound** — the rule is born tied to the *intent* and the decision that
  created it (the *why*); it is not a loose rule without context.
- **Executable** — it carries a check that runs and returns pass/fail; it is not
  prose someone promises to respect.
- **Portable** — it can be exported from one repo and imported into another,
  like a package (this is what creates the network effect over time).

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
    exclude: ["src/logging_setup.py"]   # optional: globs carved out of paths
    check: "becwright run no_token_in_logs"
    severity: blocking   # blocking = stops the commit | warning = only warns
```

Full field reference: [`documentation/usage.md`](documentation/usage.md).

## What you get

- **Blocks the commit, not just warns** — `blocking` stops `git commit`;
  `warning` informs; `advisory` hosts judgment rules (e.g. an LLM reviewer)
  that report but never block, labelled so you know what's guaranteed.
- **Any language** — the engine matches file globs and runs a command; the
  no-code `forbid` regex covers Python, JS/TS, Go, Rust, or anything else.
- **Every rule carries its why**, shown the moment it fires.
- **Portable rules** — `export` a BEC to a single `.bec.yaml`, `import` it in
  another repo; custom checks travel with their code, behind a trust gate.
- **Offline catalog** — `becwright search` / `add` install ready-made rules,
  shipped inside the package.
- **Fits your setup** — native git hook, the pre-commit framework, Husky, or a
  required GitHub Action that closes the `--no-verify` gap.
- **AI-agent ready** — Claude Code plugin, `check --json`, and an MCP server so
  agents can query and extend the rules.
- **Tiny & trustworthy** — one dependency (`pyyaml`), no `eval`/`exec`,
  dogfooded on its own repo in CI.

## Commands

| Command | What it does |
|---|---|
| `becwright demo` | Show becwright block a sample bad commit (no setup, no git needed) |
| `becwright init` | Scaffold a starter `.bec/rules.yaml` and install the hook |
| `becwright init --baseline` | Same, but start already-violated rules as `warning` (adopt without blocking) |
| `becwright init --from-claude-md` | Derive rules from the repo's `CLAUDE.md` (best-effort) |
| `becwright list` | List the built-in checks |
| `becwright check` | Runs the rules over the staged files |
| `becwright check --diff <base>` | Runs the rules over only the files changed vs `<base>` (for CI/PR) |
| `becwright why [id]` | Shows the intent + why behind the rules — the repo's decision memory (`--json` for agents) |
| `becwright validate` | Validates `.bec/rules.yaml` without running any check (for editors and CI) |
| `becwright doctor` | Diagnoses the setup: rules file, checks, hooks and hook managers |
| `becwright search [query]` | Lists ready-made BECs from the built-in catalog |
| `becwright add <name>` | Installs a catalog BEC into `.bec/rules.yaml` (offline) |
| `becwright install` / `uninstall` | Installs / removes the native hooks |
| `becwright export <id>` | Exports a BEC to a `.bec.yaml` file |
| `becwright import <file\|URL>` | Imports a BEC from another repo |

## Already using pre-commit or Husky?

becwright plugs in without `becwright install`.

**[pre-commit](https://pre-commit.com)** — add to `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/DataDave-Dev/becwright
    rev: v1.0.0
    hooks:
      - id: becwright
```

**Husky** (JS/TS repos) — in `.husky/pre-commit`:

```sh
npx becwright check
```

Either way becwright still reads `.bec/rules.yaml` and blocks the commit on a
broken blocking rule. Run `becwright init` once to scaffold the rules —
it detects Husky, the pre-commit framework, or a custom `core.hooksPath`, skips
its own hook, and prints the exact line to add instead.

## As a required CI check (GitHub Action)

The commit hook lives on each developer's machine — and `git commit --no-verify`
skips it. A **required CI check cannot be skipped**: running becwright on every
pull request makes the rules infrastructure, not a suggestion.

Add `.github/workflows/becwright.yml`:

```yaml
name: becwright
on: pull_request

jobs:
  becwright:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0        # full history so the merge-base with the PR base exists
      - uses: DataDave-Dev/becwright@v1.0.0
```

By default it checks **only the files the PR changed** against the base branch —
pre-existing debt never fails the build, so it adopts cleanly on a large
codebase. Make the check *required* in branch protection and the rules become
non-negotiable. Inputs (`base`, `version`, `python-version`, `args`) are on the
[Marketplace page](https://github.com/marketplace/actions/becwright); or skip
the action and run `becwright check --diff origin/main` from any workflow step.

## Use with AI agents (Claude Code)

becwright is the deterministic net for what an AI agent lets slip. There is a
Claude Code plugin so an agent can install and drive it for you:

```text
/plugin marketplace add DataDave-Dev/becwright
/plugin install becwright@becwright
```

It adds a `becwright` skill and a `/becwright` command. See
[`integrations/claude-code/`](integrations/claude-code/).

For structured results, `becwright check --json` prints a machine-readable
summary, and `becwright mcp` (`pipx install "becwright[mcp]"`) runs an MCP
server so any agent can check the rules, propose new ones from your
`CLAUDE.md`, and preview them before writing. See
[`documentation/mcp.md`](documentation/mcp.md).

The signal stays lean in both directions: `becwright why --json` hands an agent
the decisions it must not violate *before* it writes code, and a blocked commit
returns the one rule that broke, its *why*, and the exact lines — the specific
constraint, not the whole style guide re-read into context.

## Included checks

Each check is a module invoked from the `check` field. They work by searching
the text of your files for a pattern — simple and predictable on purpose; the
real value is in tying each rule to its *why*. For deeper analysis, point a
rule at any tool you already trust as its check — the rule carries the *why*,
the tool does the detection:

```yaml
  - id: no-secrets-gitleaks
    intent: >
      No secret may ever be committed, as judged by gitleaks' full ruleset.
    why_it_matters: >
      A leaked credential in git history is exposed forever, even after a revert.
    paths: ["**/*"]
    check: "gitleaks detect --no-git --redact --exit-code 1"
    severity: blocking

  - id: python-passes-ruff
    intent: "Python code must pass the team's ruff ruleset before commit."
    why_it_matters: "Consistent lint keeps review focused on logic, not style."
    paths: ["**/*.py"]
    check: "xargs ruff check --force-exclude"
    severity: warning
```

More ready-made patterns (semgrep, eslint, frozen paths, architecture
boundaries, CI): **[recipes](documentation/recipes.md)**.

| Check | What it detects | Language | Suggested severity |
|---|---|---|---|
| `forbid` | Any regex you pass (`--pattern`) | any | depends on the case |
| `require` | A regex (`--pattern`) that *must* appear (e.g. a license header) | any | depends on the case |
| `max_lines` | Files longer than `--max` lines | any | `warning` |
| `filename` | File names matching `--forbid` or not matching `--require` | any | depends on the case |
| `no_token_in_logs` | Tokens/credentials in log calls | Python | `blocking` |
| `hardcoded_secrets` | AWS keys, private keys, `password = "..."` literals | any | `blocking` |
| `debug_remnants` | Forgotten `breakpoint()`, `pdb.set_trace()`, `import pdb` | Python | `blocking` |
| `dangerous_eval` | `eval()` / `exec()` calls | any | `blocking` |
| `conflict_markers` | Leftover git merge conflict markers (`<<<<<<<`) | any | `blocking` |
| `wildcard_imports` | `from x import *` | Python | `warning` |

Don't want to write rules yourself? The catalog ships **inside** becwright —
one command, no URL, works offline:

```bash
becwright search                 # list every BEC in the catalog
becwright add no-token-in-logs   # install one; becwright shows it first
```

The full list (Python, JS/TS, Go, Rust — more languages
[in progress](https://github.com/DataDave-Dev/becwright/milestone/2)) lives in
[`src/becwright/becs/`](src/becwright/becs/).

## Your first custom rule (any language)

The fastest way to write a rule — without writing code — is the `forbid` check,
which fails if a regex appears in the files:

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
finer checks, write a script in any language (reads the file list from stdin,
exits 0/1) and point `check` at it — see
[writing checks](documentation/writing-checks.md).

## Sharing BECs between repos

A BEC is **portable**: a bundle is a single self-contained `.bec.yaml` (the
rule + the check's code if it is custom).

```bash
becwright export no-token-in-logs -o no-token-in-logs.bec.yaml   # source repo
becwright import no-token-in-logs.bec.yaml                       # target repo (file or URL)
```

On import, becwright **shows the check's code and asks for confirmation** —
importing a BEC is importing code that will run on every commit. Use `--yes`
in automated environments. Details:
[portability](documentation/portability.md).

## How becwright compares

becwright is not a linter and not just a hook runner — it is the layer that makes
a *rule* portable and bound to its reason, and blocks the commit on it.

| | becwright | pre-commit / Husky | gitleaks / linters | CLAUDE.md / .cursorrules |
|---|:---:|:---:|:---:|:---:|
| Runs a real check | ✅ | ✅ (runs other tools) | ✅ | ❌ prose |
| Blocks the commit | ✅ | ✅ | ✅ | ❌ |
| Carries the *why* (intent) | ✅ | ❌ | ❌ | ⚠️ not enforced |
| Portable rule between repos | ✅ `export`/`import` | ⚠️ copy config | ⚠️ | ⚠️ |
| Any language, no per-tool plugin | ✅ `forbid` regex | ⚠️ | ❌ tool-specific | n/a |

becwright **complements** these rather than replacing them: run gitleaks or a
linter *as* a becwright check, or add becwright *inside* pre-commit / Husky.

## Documentation

Full docs live in [`documentation/`](documentation/):

- **Just getting started:** [usage](documentation/usage.md) — install, the
  commands, exit codes, and how to write a rule.
- **Copy-paste rules for common jobs** (gitleaks/ruff/semgrep as checks, frozen
  paths, architecture boundaries, CI): [recipes](documentation/recipes.md).
- **Want to add your own rule:** [writing checks](documentation/writing-checks.md).
- **Sharing rules between projects:** [portability](documentation/portability.md).
- **Curious how it works inside:** [architecture & flow](documentation/architecture.md).
- **Wiring it to an AI agent:** [MCP & JSON output](documentation/mcp.md).

## Stability

becwright is **stable** (`1.0`): the `rules.yaml` schema, bundle format, check
names, CLI exit codes, `check --json` shape and MCP signatures only break on a
major bump, with a one-minor deprecation notice first. Pin a version in CI and
a `1.x` upgrade never breaks your rules. Full contract and policy:
[stability & versioning](documentation/stability.md).

## Roadmap

becwright is intentionally small. The near-term direction lives in the
[milestones](https://github.com/DataDave-Dev/becwright/milestones):
**v1.1** grows the catalog to more languages (Ruby, PHP, Java, C#, Shell — each
a [good first issue](https://github.com/DataDave-Dev/becwright/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22)),
**v1.2** improves rule-writing DX (short check syntax, a JSON Schema for
`rules.yaml`), **v1.3** makes Windows first-class.

Deliberately **out of scope** to stay simple and deterministic: AST-based
analysis, deep per-language tool suites, and cryptographic signing of BECs.

## FAQ

**Why not just Ruff / Black / pre-commit?** Use them — becwright doesn't compete
with them. Black formats, Ruff lints, pre-commit *runs* tools. None of them hand
you a *rule bound to its reason* that blocks the commit and travels to another
repo. becwright is that layer, and it will happily run Ruff or gitleaks *as* one
of its checks. Different job, same pipeline.

**It's a young project — why trust it on my commits?** Because there's very
little to trust: one dependency (`pyyaml`), no `eval`/`exec`, checks that are
plain regex you can read in under a minute, and an MIT license. And it's
dogfooded — becwright's own commits are gated by becwright. If it broke, this
repo wouldn't build.

**Can an agent just delete the rule?** It can — but deleting a rule is a visible
line in the diff that review flags, whereas ignoring a note in `CLAUDE.md` leaves
no trace at all. A guard you have to remove on camera beats a sign you can walk
past.

**Doesn't `pre-commit` already do this?** It runs tools; it doesn't give you a
rule that carries its *why* and travels between repos. You can even run becwright
*inside* pre-commit — see [above](#already-using-pre-commit-or-husky).

**Do I need Python?** No. `npm i -g becwright` installs a self-contained binary;
`pipx install becwright` also works.

**Does it work on Windows?** In beta. The CLI and hook run under Git Bash
(which Git for Windows provides), but Windows is not yet exercised in CI —
known gaps are tracked in
[#31](https://github.com/DataDave-Dev/becwright/issues/31) and first-class
support is the v1.3 milestone. Until then, treat Windows as best-effort.

**How do I ignore a single line?** Add a `becwright: ignore` comment on it.

**Is it safe to import a BEC?** becwright shows the check's code and asks for
confirmation before installing. Treat an untrusted bundle like any untrusted
script.

## Contributing

Contributions are welcome — see [CONTRIBUTING.md](CONTRIBUTING.md) and the
[Code of Conduct](CODE_OF_CONDUCT.md). Found a security issue? Please follow the
[security policy](SECURITY.md). The [changelog](CHANGELOG.md) tracks every
release.

## License

[MIT](LICENSE) © Alonso David De Leon Rodarte
