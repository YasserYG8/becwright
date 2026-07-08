> **English** · [Español](recipes.es.md)

# Recipes

Copy-paste rules and configs for the most common jobs. Every rule below goes
under `rules:` in your `.bec/rules.yaml`; every config file is complete.

**How a check gets its input:** becwright feeds the matched file list to the
check on **stdin**, one path per line, with the repo root as working directory.
So `xargs <tool>` bridges to any tool that takes file arguments, and tools that
scan the working directory just work.

> **One caveat for external tools:** on a normal commit, checks run inside a
> temporary snapshot of the *staged* content (so they judge exactly what the
> commit will record). That snapshot is not a git repository — use a tool's
> directory- or file-scanning mode (`gitleaks detect --no-git`, `ruff check`,
> `semgrep scan`), not a mode that needs `.git` (`gitleaks protect`).

## Block secrets (built-in, zero install)

```yaml
  - id: no-hardcoded-secrets
    intent: >
      No secret (key, token, password) may be hardcoded in the code.
    why_it_matters: >
      A secret in the repo stays in git history forever and is visible to
      anyone with access to the code.
    paths: ["**/*"]
    check: "becwright run hardcoded_secrets"
    severity: blocking
```

## Run gitleaks as the check

The built-in check is a fast regex net. If you already trust
[gitleaks](https://github.com/gitleaks/gitleaks), point the rule at it — the
rule keeps the *why*, gitleaks does the deep detection:

```yaml
  - id: no-secrets-gitleaks
    intent: >
      No secret may ever be committed, as judged by gitleaks' full ruleset.
    why_it_matters: >
      A leaked credential in git history is exposed forever, even after a
      revert.
    paths: ["**/*"]
    check: "gitleaks detect --no-git --redact --exit-code 1"
    severity: blocking
```

## Run ruff as the check

```yaml
  - id: python-passes-ruff
    intent: >
      Python code must pass the team's ruff ruleset before it is committed.
    why_it_matters: >
      Consistent lint keeps diffs clean and review focused on logic, not style.
    paths: ["**/*.py"]
    check: "xargs ruff check --force-exclude"
    severity: warning
```

## Run semgrep as the check

```yaml
  - id: semgrep-ci-rules
    intent: >
      Changed files must pass the team's semgrep policy.
    why_it_matters: >
      Semgrep's AST rules catch injection and logic patterns a regex cannot.
    paths: ["**/*.py", "**/*.js", "**/*.ts"]
    check: "xargs semgrep scan --error --quiet --config p/ci"
    severity: blocking
```

The same shape works for any tool with an exit code: eslint
(`xargs eslint --no-warn-ignored`), shellcheck (`xargs shellcheck`),
hadolint, tsc, mypy…

## No `console.log` / `debugger` (JS/TS)

```yaml
  - id: no-debugger-js
    intent: "Do not leave 'debugger;' in JavaScript/TypeScript code."
    why_it_matters: "A forgotten 'debugger' halts execution in production."
    paths: ["**/*.js", "**/*.ts"]
    check: "becwright run forbid --pattern '\\bdebugger\\b'"
    severity: blocking

  - id: no-console-log-js
    intent: "Avoid 'console.log(...)' outside the logger module."
    why_it_matters: "Debug console.log statements clutter production output."
    paths: ["**/*.js", "**/*.ts"]
    exclude: ["src/lib/logger.ts"]
    check: "becwright run forbid --pattern 'console\\.log\\s*\\('"
    severity: warning
```

## Freeze critical paths (e.g. applied migrations)

`filename --forbid '.*'` fails on *any* staged file the rule's `paths` match —
so the rule reads as "changing these files blocks the commit". Ideal for files
an AI agent must never touch:

```yaml
  - id: frozen-migrations
    intent: >
      Applied database migrations are immutable; write a new migration instead.
    why_it_matters: >
      Editing an applied migration desynchronizes every database that already
      ran it.
    paths: ["migrations/**"]
    check: "becwright run filename --forbid '.*'"
    severity: blocking
```

## Enforce an architecture boundary

```yaml
  - id: domain-does-not-import-infra
    intent: >
      The domain layer must not import from the infrastructure layer.
    why_it_matters: >
      Domain code that reaches into infra can no longer be tested or reused in
      isolation; the dependency must point inward.
    paths: ["src/domain/**/*.py"]
    check: "becwright run forbid --pattern 'from app\\.infra|import app\\.infra'"
    severity: blocking
```

## Conventional commit messages

```yaml
  - id: conventional-commits
    target: commit-msg
    intent: "Commit messages follow the Conventional Commits format."
    why_it_matters: "A consistent format keeps history readable and enables automated changelogs."
    check: |-
      becwright run require --pattern '^(build|chore|ci|docs|feat|fix|perf|refactor|revert|style|test)(\(.+\))?!?: '
    severity: blocking
```

## CI: GitHub Actions

`.github/workflows/becwright.yml` — checks only the files the PR changed, so
pre-existing debt never fails the build:

```yaml
name: becwright
on: pull_request

jobs:
  becwright:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: DataDave-Dev/becwright@v1.0.0
```

Make it a *required* check in branch protection and the rules can no longer be
skipped with `git commit --no-verify`.

## CI: Docker & GitLab CI (or generic environments)

For CI environments that support Docker containers (such as GitLab CI or Jenkins), or to run checks without installing Python locally, you can use the official Docker image.

Run the container by mounting your repository root as a volume:

```sh
docker run --rm -v "$PWD:/repo" -w /repo ghcr.io/datadave-dev/becwright check --diff origin/main
```

### GitLab CI Integration

Add the following job to your `.gitlab-ci.yml`:

```yaml
becwright:
  stage: test
  image:
    name: ghcr.io/datadave-dev/becwright:latest
    entrypoint: [""]
  script:
    - becwright check --diff origin/main
```

## pre-commit framework

`.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/DataDave-Dev/becwright
    rev: v1.0.0
    hooks:
      - id: becwright
```

## Husky

`.husky/pre-commit`:

```sh
npx becwright check
```

## package.json scripts

```json
{
  "scripts": {
    "bec": "becwright check",
    "bec:all": "becwright check --all"
  },
  "devDependencies": {
    "becwright": "^1.0.0"
  }
}
```

## Claude Code and MCP

```text
/plugin marketplace add DataDave-Dev/becwright
/plugin install becwright@becwright
```

For any MCP-capable agent, `becwright mcp` (install with
`pipx install "becwright[mcp]"`) exposes the rules as tools. Details:
[mcp.md](mcp.md).
