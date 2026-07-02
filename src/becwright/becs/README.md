# BEC catalog

BECs ready to install in your repo. This catalog **ships inside becwright**, so
you install from it with one command — no URL, works offline. becwright shows
you what a BEC does and asks for confirmation before installing it.

```bash
becwright search            # list every BEC below
becwright add <name>        # install one, e.g. `becwright add no-token-in-logs`
```

| BEC (`becwright add <name>`) | What it does | Severity |
|---|---|---|
| `no-token-in-logs` | Blocks tokens/credentials in log calls | `blocking` |
| `no-hardcoded-secrets` | Blocks keys, tokens and passwords hardcoded in the code | `blocking` |
| `no-debug-remnants` | Blocks forgotten `breakpoint()`, `pdb.set_trace()`, `import pdb` | `blocking` |
| `no-dangerous-eval` | Blocks `eval()` / `exec()` | `blocking` |
| `no-wildcard-imports` | Warns about `from x import *` | `warning` |
| `no-debugger-js` | Blocks `debugger;` in JS/TS | `blocking` |
| `no-console-log-js` | Warns about `console.log(...)` in JS/TS | `warning` |
| `no-debug-go` | Blocks `fmt.Println()` and `panic()` in Go | `blocking` |
| `no-debug-rust` | Blocks `dbg!()` and `println!()` in Rust | `blocking` |
| `no-set-x-left-in` | Blocks `set -x` tracing left enabled in shell scripts | `blocking` |

The Python BECs use `paths: ["src/**/*.py"]`, the JS/TS ones `["**/*.js", "**/*.ts"]`, the Go bundles use `["**/*.go"]`, and the Rust bundles use `["**/*.rs"]`. After installing, adjust `paths` in your `.bec/rules.yaml` if your code lives elsewhere.