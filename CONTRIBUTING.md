# Contributing to becwright

Thanks for your interest. becwright aims to be a small, sharp standard, so
contributions favor simplicity and clarity over feature count.

## Development setup

```bash
git clone https://github.com/DataDave-Dev/becwright.git
cd becwright
pip install -e ".[dev]"
pytest
```

## Workflow

`main` is protected: changes land via pull request with CI green.

1. Fork the repo and create a branch.
2. Make your change, with tests.
3. Run `pytest` (CI also enforces 80% coverage and runs becwright on itself).
4. Open a pull request.

## Conventions

- **Language:** code, comments and the repo are in English. The human-facing
  README has a Spanish variant (`README.es.md`).
- **Comments:** only for complex code; no comments that restate the obvious.
- **Dependencies:** the runtime depends only on `pyyaml`. Do not add others
  without discussing it first.
- **Atomic commits:** one complete logical change per commit, leaving the tests
  green. Don't mix unrelated changes.
- **Python:** target 3.12.
- Do not change the `rules.yaml` format or the existing `checks/` logic without
  discussing it first.

## Adding a check

A check is an executable that:

- reads a newline-separated file list from **stdin**,
- prints violations to stdout,
- exits **0** (pass) or **non-zero** (fail).

Built-in checks live in `src/becwright/checks/` and follow the shared skeleton
(see `dangerous_eval.py`). For language-agnostic rules, prefer the generic
`forbid` check (just a regex) over writing a new module.

## Adding a catalog BEC

Catalog bundles live in `becs/` as `<id>.bec.yaml`. Always include `intent` and
`why_it_matters` — the *why* is the whole point of a BEC. See the existing
bundles for the format.
