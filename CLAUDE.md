# becwright — project context

> This file is loaded every session. It is the source of truth for understanding
> what the project is about, what decisions were made, and what is in/out of
> scope. Keep it short and up to date.

## What it is

becwright enforces **constraints on code deterministically**, blocking commits
that violate them. The difference with `CLAUDE.md` / `.cursorrules`: those *ask*
an agent to respect rules (probabilistic, the agent can ignore them); becwright
**verifies the result** by running a real check against the code (guaranteed,
does not depend on the agent).

The two layers are complementary: notes prevent, becwright is the deterministic
safety net for what slips through.

## Core concept: BEC (Bound Executable Constraint)

A constraint with three properties together:

- **Bound** — born tied to the *intent* and the *why* that created it.
- **Executable** — carries a check that runs and returns pass/fail.
- **Portable** — can be exported from one repo and imported into another.

Full detail in [`docs/concepto-bec.md`](docs/concepto-bec.md).

## Repo structure

```
becwright/
├── CLAUDE.md                 # this file: persistent context
├── README.md                 # public conceptual document (English; README.es.md = Spanish)
├── pyproject.toml            # packaging + `becwright` command (setuptools)
├── src/becwright/            # packaged ENGINE (installable, not copied into each repo)
│   ├── cli.py                # argparse: init / list / check / install / uninstall / export / import
│   ├── engine.py             # path matching + runs checks + decides pass/fail
│   ├── rules.py              # Rule model + loading of .bec/rules.yaml
│   ├── bundle.py             # export/import of BECs (the portable bundle)
│   ├── git.py                # repo root, staged files, native hook
│   └── checks/               # included checks (no_token_in_logs, forbid, ...)
├── becs/                     # catalog of importable BECs (.bec.yaml bundles)
├── tests/                    # pytest
├── docs/                     # concept, decisions, status-and-roadmap (Spanish, gitignored)
└── prototype/                # ARCHIVED PROTOTYPE (reference, not built upon without notice)
```

A repo that *adopts* becwright only contributes its own `.bec/rules.yaml`; the
engine comes from the installed package.

## Current status

**MVP (A + B)** and **Phase 1** ("usable by others") done. **Phase 2
(Portability, C)** done: `becwright export` / `import` move a BEC between repos
as a single self-contained `.bec.yaml` (a custom check's code travels embedded),
with a trust gate that shows the code before installing. Commands:
`init / list / check / install / uninstall / export / import`. **Multi-language:** the engine
is agnostic (runs any check on any file); the generic `forbid` check (regex via
`--pattern`) lets you write rules for any language without code, and the catalog
includes Python and JS/TS BECs. Included checks: `forbid` (any language),
`hardcoded_secrets` and `dangerous_eval` (agnostic), and `no_token_in_logs` /
`debug_remnants` / `wildcard_imports` (Python). The original prototype is
**archived** under `prototype/` as a reference. Plan and north star in
[`docs/plan.md`](docs/plan.md); detail in
[`docs/estado-y-roadmap.md`](docs/estado-y-roadmap.md).

## Scope and non-goals

**In:** the MVP A + B (installable CLI + native hook), portability C (export /
import of BECs between repos) and multi-language support (agnostic engine +
`forbid` check); keep documentation and the reference prototype up to date.

**Out (future work, do not touch without asking):** AST analysis, deep
per-language tooling (language-specific check suites, per-language AST),
cryptographic signing/verification of BECs, "improving" the checks' regexes.

## Conventions

- Code and comments **in English**.
- Comments reserved for complex code: if the code is self-explanatory, it is not
  commented. No comments that restate the obvious.
- Python 3.12 target (the current environment has 3.14; note it, do not force).
- Minimal dependencies: only `pyyaml`. Do not add others without asking.
- Do not change the `rules.yaml` format or the `checks/` logic without asking.
- Simplicity and clarity over feature count (this aims to be a standard).
- **Atomic** commits: each commit is a single, complete logical change (leaves
  the tests green). Do not mix unrelated changes in one commit.
- The repo is in English; the human-facing README has a Spanish variant
  (`README.es.md`). `docs/` stays in Spanish and is gitignored.
