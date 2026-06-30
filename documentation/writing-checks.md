> **English** · [Español](writing-checks.es.md)

# Writing checks

A check is the **executable** part of a BEC. becwright runs it and trusts its
exit code.

## The contract

- **Input:** the list of files to check, one path per line, on **stdin**.
- **Output:** print violations to stdout (becwright shows them under "Found in:").
- **Exit code:** `0` = pass, non-zero = fail.
- **Working directory:** the repo root, so paths from stdin resolve directly.

## The fastest path: `forbid`

For "this regex must not appear", you don't need to write code — use the built-in
generic check:

```yaml
  - id: no-debugger-js
    paths: ["**/*.js", "**/*.ts"]
    check: "becwright run forbid --pattern '\\bdebugger\\b'"
    severity: blocking
```

`forbid` accepts `--pattern REGEX`, `--ignore-case` and `--message TEXT`.

## Built-in checks

| Check | Detects | Language |
|---|---|---|
| `forbid` | any regex you pass (`--pattern`) | any |
| `no_token_in_logs` | tokens/credentials in log calls | Python |
| `hardcoded_secrets` | AWS keys, private keys, `password = "..."` | any |
| `debug_remnants` | `breakpoint()`, `pdb.set_trace()`, `import pdb` | Python |
| `dangerous_eval` | `eval()` / `exec()` | any |
| `wildcard_imports` | `from x import *` | Python |

## A custom check (any language)

Any executable that follows the contract works. Example in Node, flagging `TODO`:

```js
#!/usr/bin/env node
const fs = require('fs');
const files = fs.readFileSync(0, 'utf8').split('\n').filter(Boolean);
let bad = false;
for (const f of files) {
  fs.readFileSync(f, 'utf8').split('\n').forEach((line, i) => {
    if (line.includes('TODO')) { console.log(`  ${f}:${i + 1}`); bad = true; }
  });
}
process.exit(bad ? 1 : 0);
```

```yaml
  - id: no-todo
    paths: ["**/*.js"]
    check: "node .bec/checks/no_todo.js"
    severity: warning
```

A built-in Python check follows the same skeleton — see
`src/becwright/checks/dangerous_eval.py`.

## Ignoring a line

A false positive — a pattern that appears as text, not as a real violation — can
be suppressed with a `becwright: ignore` marker in a comment on that line, in any
language:

```py
result = eval(expr)  # becwright: ignore
```

```js
console.log(x);  // becwright: ignore
```

The marker exempts the line from every built-in check.

## The self-reference caveat

A text/regex check cannot run over its own source: a check that forbids the
string `eval(` will match the very line in its own code that defines that
pattern. When a rule's check would scan the check's own file, scope `paths` to
exclude it — e.g. use `src/becwright/*.py` (top level only) instead of
`src/becwright/**/*.py` to skip the `checks/` directory. For individual lines,
the `becwright: ignore` marker above is simpler.
