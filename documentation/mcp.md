# MCP server & JSON output

For AI agents, becwright exposes its results in machine-readable form two ways.

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
