# becwright — Claude Code plugin

A Claude Code plugin so any agent session can install and drive becwright — the
enforcement layer for AI coding agents: the deterministic, commit-blocking safety
net that complements `CLAUDE.md`.

## Install

```text
/plugin marketplace add DataDave-Dev/becwright
/plugin install becwright@becwright
```

The first command registers this repo as a marketplace; the second installs the
plugin from it.

## What it provides

- **Skill `becwright`** — teaches the agent what becwright is, how to install it
  (via npm/pnpm — no Python needed — or pipx), how to scaffold rules (including
  `--baseline` for adopting on a dirty repo), and how to read and fix `check`
  output. It also teaches the agent to turn the *deterministic* parts of a
  `CLAUDE.md` into BECs — via `init --from-claude-md` and the MCP loop (propose →
  preview_rule → add_rule) — to enforce commit-message rules, and to use the
  `advisory` tier for judgment rules, while leaving what has no check as prose in
  `CLAUDE.md`. The agent invokes it automatically when you ask for a guardrail, a
  pre-commit check, or a rule that "can't be ignored".
- **Command `/becwright`** — a direct entry point:
  - `/becwright init` — install becwright and scaffold `.bec/rules.yaml` + hooks
    (picks `--from-claude-md` / `--baseline` when they fit the repo)
  - `/becwright check` — run the rules and summarize PASS / WARN / ADVISORY / BLOCK
  - `/becwright add <regex-or-catalog-url>` — add a `forbid` rule or import a BEC
  - `/becwright status` — report install + hook + rule count

The plugin does not bundle becwright itself; it installs the published package
(`becwright` on npm / PyPI) into your project.

## Layout

```
integrations/claude-code/
├── .claude-plugin/plugin.json
├── commands/becwright.md
└── skills/becwright/SKILL.md
```

The marketplace manifest lives at the repo root: `.claude-plugin/marketplace.json`.
