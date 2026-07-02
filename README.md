> **English** · [Español](README.es.md)

<p align="center">
  <img src="assets/becwright-logo.svg" alt="becwright" width="140" height="140">
</p>

# becwright

[![CI](https://github.com/DataDave-Dev/becwright/actions/workflows/ci.yml/badge.svg)](https://github.com/DataDave-Dev/becwright/actions/workflows/ci.yml)
[![npm](https://img.shields.io/npm/v/becwright?logo=npm)](https://www.npmjs.com/package/becwright)
[![PyPI](https://img.shields.io/pypi/v/becwright?logo=pypi&logoColor=white)](https://pypi.org/project/becwright/)

**The enforcement layer for AI coding agents.**

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
  <img src="assets/becwright-demo.svg" alt="becwright blocking a commit that hardcodes a secret and calls eval" width="640">
</p>

> **See it yourself in 5 seconds** — no setup, no git, nothing on your machine is
> touched:
> ```bash
> npx becwright demo        # zero-install   ·   or: pipx run becwright demo
> ```

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
does. The rest of this README goes from "just get me started" to the full
technical detail — read as far as you need.
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

## Features

- **Deterministic enforcement** — a rule is a real check that runs against your
  code and returns pass/fail, not a note an agent may ignore.
- **Blocks the commit, not just warns** — blocking rules stop `git commit`;
  warnings inform without blocking.
- **Any language** — the engine matches file globs and runs a command; use the
  no-code `forbid` regex for Python, JS/TS, Go, Rust, or anything else.
- **Derive rules from your `CLAUDE.md`** — `becwright init --from-claude-md` turns
  the prohibitions it recognizes (secrets, `eval`, `debugger`, `console.log`,
  breakpoints, a file line cap, …) into enforceable rules; an AI agent can extend
  that over MCP. Judgment-based guidance stays in `CLAUDE.md`.
- **Adopt on any codebase** — `--baseline` starts rules that *already* have
  violations as warnings, so a legacy repo isn't blocked on day one; graduate each
  to blocking as you clean it.
- **Guaranteed *and* assisted rules** — deterministic rules `block` with a 100%
  guarantee; judgment rules (readability, design) live as `advisory` — they report
  via your own reviewer check (e.g. an LLM) but never block, and are labelled so
  you always know which findings are guaranteed vs best-effort.
- **Bound to the _why_** — every rule carries its intent and reason, shown when
  it fires.
- **Batteries-included checks** — `forbid` / `require` (a pattern that must be
  present) / `max_lines` / `filename`, plus secret, `eval`, debug and import
  checks — with per-rule `exclude:` to silence false positives.
- **Portable BECs** — `export` a rule to a single `.bec.yaml` and `import` it
  into another repo; custom checks travel with their code.
- **Offline catalog** — `becwright search` / `add` install ready-made rules with
  no URL, shipped inside the package.
- **No Python required** — install via npm/pnpm as a self-contained binary, or
  via pip/pipx.
- **Fits your setup** — native git hook, or plug into the pre-commit framework or
  Husky.
- **Can't be skipped** — a GitHub Action runs becwright on every PR (only the
  files it changed), so a required check enforces the rules even when the local
  hook is bypassed with `--no-verify`.
- **AI-agent ready** — Claude Code plugin, `check --json`, and an MCP server whose
  tools let an agent propose, preview and add rules from your `CLAUDE.md`.
- **Tiny & trustworthy** — small, dependency-light (`pyyaml`), no `eval`/`exec`,
  dogfooded in CI.

## Use cases

- **Turn your `CLAUDE.md` into guardrails** — the deterministic parts become BECs
  that can't be ignored; the judgment calls stay as prose.
- **Adopt gradually on a legacy repo** — `--baseline` warns on existing debt
  without blocking commits, then tighten to blocking rule by rule.
- **Stop secrets before they land** — API keys, tokens, private keys, hardcoded
  passwords.
- **Keep debug leftovers out** — `breakpoint()`, `pdb`, `debugger;`,
  `console.log`, `dbg!`, stray `panic()`.
- **Ban risky APIs / enforce conventions** — `eval` / `exec`, a file-length cap,
  file-name rules, or any pattern you forbid with a one-line regex rule.
- **Enforce commit-message rules** — Conventional Commits, or block AI attribution
  trailers, via a `target: commit-msg` rule and the `commit-msg` hook.
- **Guard AI-written code** — the deterministic net for what an agent regenerates
  and forgets.
- **Enforce team conventions** — encode a decision once as a BEC and share it
  across every repo.

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

**Adopting on an existing codebase?** Use `becwright init --baseline`: rules that
*already* have violations start as `warning` (nothing legitimate is blocked)
while clean rules start as `blocking`. Fix the debt over time, then graduate each
rule to `blocking`.

**Already have a `CLAUDE.md`?** `becwright init --from-claude-md` reads it and
turns the prohibitions it recognizes (secrets, `eval`, `debugger`, `console.log`,
breakpoints, …) into enforceable rules — the deterministic safety net under the
prose. Judgment-based guidance stays in `CLAUDE.md`. Review the result; combine
with `--baseline` to adopt on a dirty repo in one step.

Available commands:

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
| `becwright search [query]` | Lists ready-made BECs from the built-in catalog |
| `becwright add <name>` | Installs a catalog BEC into `.bec/rules.yaml` (offline) |
| `becwright install` | Installs the native `pre-commit` hook |
| `becwright uninstall` | Removes the hook |
| `becwright export <id>` | Exports a BEC to a `.bec.yaml` file |
| `becwright import <file\|URL>` | Imports a BEC from another repo |

### Already using pre-commit or Husky?

If your repo already manages git hooks, becwright plugs in without `becwright
install`.

**[pre-commit](https://pre-commit.com)** — add this to `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/DataDave-Dev/becwright
    rev: v0.3.0
    hooks:
      - id: becwright
```

**Husky** (JS/TS repos) — in `.husky/pre-commit`:

```sh
npx becwright check
```

Either way becwright still reads `.bec/rules.yaml` and blocks the commit on a
broken blocking rule. You only need `becwright init` once to scaffold the rules
(skip its hook install if another tool owns the hook).

### As a required CI check (GitHub Action)

The commit hook is the first line of defense, but it lives on each developer's
machine — and `git commit --no-verify` skips it. A **required CI check cannot be
skipped**. Running becwright on every pull request turns the rules into
infrastructure of the pipeline, not a local convenience that an agent (or a
human) can bypass.

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
      - uses: DataDave-Dev/becwright@main   # pin to a released tag once available
```

By default it checks **only the files the PR changed** against the base branch —
pre-existing debt on the rest of the repo never fails the build, so you can adopt
it on a large codebase without a red wall. Make the check *required* in your
branch-protection rules and the rules become non-negotiable.

Inputs (all optional):

| Input | Default | What it does |
|---|---|---|
| `base` | PR base branch | Git ref to diff against; only files changed vs it are checked |
| `version` | `becwright` | pip specifier to install (e.g. `becwright==0.4.0`) |
| `python-version` | `3.x` | Python used to run becwright |
| `args` | *empty* | Extra args appended to `becwright check` |

> Set `fetch-depth: 0` on the checkout so the merge-base with the PR base exists;
> a shallow clone makes the base ref unreachable and the check fails loudly rather
> than passing on an empty file list.

Prefer to run it yourself? `becwright check --diff origin/main` does the same
thing from any workflow step, no action needed.

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
plug in extra abilities — exposing `check`, `list_checks` and `list_rules` to any
agent. See [`documentation/mcp.md`](documentation/mcp.md).

Better yet, an agent can read the rules *before* it writes code: `becwright why
--json` hands it the decisions it must not violate (each rule's intent and the
reason behind it), so it steers clear of a broken commit instead of discovering
the rule only when the commit is blocked. The `.bec/rules.yaml` catalog becomes
the repo's queryable decision memory.

Either way the signal stays lean. A blocked commit returns the one rule that
broke, its *why*, and the exact lines — the agent fixes precisely that instead of
re-reading the whole style guide into context. The usual advice is "give the
model more context"; becwright inverts it — you hand it the specific constraint it
broke, checked deterministically, not the entire rulebook. Fewer tokens, tighter
loop, and the guarantee doesn't depend on the model having read anything at all.

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

`exclude` subtracts globs from `paths`, so one rule can cover a whole language
while skipping the files that would only produce false positives — vendored or
generated code, or the check's own implementation. It travels with the rule
through `export` / `import`. Full field reference:
[`documentation/usage.md`](documentation/usage.md).

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
linter *as* a becwright check, or add becwright *inside* pre-commit / Husky. The
difference is that a BEC binds the rule to its intent and travels between repos.

## Included checks

becwright ships ready-to-use checks. Each one is a module invoked from the
`check` field. They work by **searching the text** of your files for a pattern
(a *regex* — a search pattern for text, like "find this exact word"), rather
than truly understanding the code. That keeps them simple and predictable: they
may miss exotic cases, and the real value is in tying each rule to its *why*.

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

Don't want to write rules yourself? The catalog ships **inside** becwright, so
you can install a rule with one command — no URL, works offline. becwright shows
you the rule, then drops it into your `.bec/rules.yaml`, ready to go:

```bash
becwright search                 # list every BEC in the catalog
becwright search secret          # filter by a word

becwright add no-token-in-logs   # install one (Python)
becwright add no-debugger-js     # JavaScript / TypeScript
becwright add no-hardcoded-secrets   # any language
```

The full list (Python, JS/TS, Go, Rust) lives in
[`src/becwright/becs/`](src/becwright/becs/).

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

There is a **catalog of ready-to-use BECs** shipped inside becwright: run
`becwright search` to list them and `becwright add <name>` to install one (they
also live in [`src/becwright/becs/`](src/becwright/becs/) for browsing).

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

## Stability & versioning

becwright is **Beta**. It's dogfooded (its own commits are gated by becwright),
the test suite is green, and it's published on npm and PyPI — but it is still
`0.x`, so under [SemVer](https://semver.org) a minor release *may* change the
public contract. If you depend on it in CI, pin a version
(`becwright==0.4.0`, or `npm i -g becwright@0.4.0`).

**The public contract** — the surface that becomes stable at `1.0.0` and only
changes on a major bump after that:

- The `.bec/rules.yaml` schema (rule fields and their meaning).
- The `.bec.yaml` bundle format that `export` / `import` move between repos.
- Built-in check names and their flags.
- CLI commands and their exit codes.
- The `check --json` output shape.
- MCP tool names and signatures.

Everything else (message wording, catalog contents, internal modules) can change
at any time.

**The path to 1.0.0** — ship it once we're confident the contract above won't
need a breaking change. All the groundwork is now in place:

- [x] Version both on-disk formats so a newer file fails loudly instead of
      misparsing — the `.bec.yaml` bundle (`becwright_bec`) and `.bec/rules.yaml`
      (`schema_version`).
- [x] Freeze the `rules.yaml` field set — the nine fields are stable and test-locked.
- [x] Document and stabilize CLI exit codes and the `check --json` shape.
- [x] State a deprecation policy (below).
- [x] Validate on real repositories beyond this one.

**Deprecation policy** — from `1.0.0` on, nothing in the public contract is
removed without a major bump of notice. When something has to change:

1. It is marked **deprecated** in a minor release — it keeps working and emits a
   warning.
2. It keeps working (still warning) through the rest of that major series.
3. It is removed only in the next **major** release.

So anything valid on `1.0` stays valid across every `1.x`: a breaking change
always crosses a major version, with at least one minor of warning first. Pin a
version in CI and a `1.x` upgrade will never break your rules, bundles, or check
scripts without warning.

## Roadmap

becwright is intentionally small. On the horizon:

- Grow the `becwright add` catalog with more languages and common rules.
- A landing page and a richer `examples/` set.
- More built-in checks, driven by real usage.

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

**Does it work on Windows?** Yes, via Git Bash (the git hook is a `sh` script,
which Git for Windows provides). The `becwright` CLI itself is cross-platform.

**How do I ignore a single line?** Add a `becwright: ignore` comment on it.

**How is "becwright" pronounced / what does it mean?** *bec-wright* — a "wright"
is a maker (as in *playwright*), so becwright is "the one who makes BECs".

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
