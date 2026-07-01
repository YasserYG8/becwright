# MCP server & JSON output

**Who is this page for?** People wiring becwright into an AI tool or a script.
If you just want becwright to guard your commits, you don't need any of this —
the normal install already does that. Read on only if you want an AI agent (or
some other program) to *read* becwright's results.

becwright exposes its results in machine-readable form two ways: a JSON output
for scripts, and an MCP server for AI agents. (MCP — Model Context Protocol — is
a standard plug for giving AI tools extra abilities.)

## `becwright check --json`

Same as `becwright check`, but prints a JSON summary instead of colored text and
is consumable without parsing. Exit code is unchanged (1 if a blocking rule
failed, else 0).

```json
{
  "rule_count": 3,
  "checked_files": 1,
  "blocked": true,
  "results": [
    {
      "id": "no-debugger-js",
      "severity": "blocking",
      "passed": false,
      "intent": "Do not leave 'debugger;' in JavaScript/TypeScript code.",
      "why_it_matters": "A forgotten 'debugger' halts execution ...",
      "output": "app.js:1\n      > function f(){ debugger; }"
    }
  ]
}
```

This needs no extra dependency and works from the standalone binary too.

## MCP server

`becwright mcp` runs a [Model Context Protocol](https://modelcontextprotocol.io)
server over stdio, so any MCP-capable agent (Claude, Cursor, Windsurf, …) gets
becwright as structured tools.

It requires the optional `mcp` extra:

```bash
pipx install "becwright[mcp]"     # or: pip install "becwright[mcp]"
```

### Tools

| Tool | Arguments | Returns |
|---|---|---|
| `check` | `all_files` (bool), `path` (optional repo dir) | the same summary as `check --json` |
| `list_checks` | — | the built-in checks as `{name, description}` |
| `preview_rule` | `check`, `paths`, `exclude` (optional), `all_files`, `path` | `{matched_files, passed, output, note}` — a dry-run without writing the rule |

**`preview_rule`** lets an agent *validate a rule before writing it*. Given a
candidate `check` and `paths`, it runs the check against the repo and reports how
many files the globs select, whether the rule would pass, and what it flags —
catching a rule that matches nothing or names an unknown check. This is the
deterministic floor an agent builds on when translating a `CLAUDE.md` into BECs:
becwright guarantees the *execution*; the agent does the *translation*, using
`list_checks` as its vocabulary and `preview_rule` to check its work.

### Client configuration

Point your agent's MCP config at the command:

```json
{
  "mcpServers": {
    "becwright": {
      "command": "becwright",
      "args": ["mcp"]
    }
  }
}
```

The MCP server ships only with the Python package (it is not in the npm binary).
For CLI/hook usage without Python, keep using the npm install.
