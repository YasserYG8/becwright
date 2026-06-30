# BEC catalog

BECs ready to import into your repo. Each one is a self-contained bundle; on
import, becwright shows you what it does and asks for confirmation before
installing it.

```bash
becwright import https://raw.githubusercontent.com/DataDave-Dev/becwright/main/becs/<file>
```

| BEC | What it does | Severity |
|---|---|---|
| `no-token-in-logs.bec.yaml` | Blocks tokens/credentials in log calls | `blocking` |
| `no-hardcoded-secrets.bec.yaml` | Blocks keys, tokens and passwords hardcoded in the code | `blocking` |
| `no-debug-remnants.bec.yaml` | Blocks forgotten `breakpoint()`, `pdb.set_trace()`, `import pdb` | `blocking` |
| `no-dangerous-eval.bec.yaml` | Blocks `eval()` / `exec()` | `blocking` |
| `no-wildcard-imports.bec.yaml` | Warns about `from x import *` | `warning` |
| `no-debugger-js.bec.yaml` | Blocks `debugger;` in JS/TS | `blocking` |
| `no-console-log-js.bec.yaml` | Warns about `console.log(...)` in JS/TS | `warning` |
| `no-debug-go.bec.yaml` | Blocks `fmt.Println()` and `panic()` in Go | `blocking` |
| `no-debug-rust.bec.yaml` | Blocks `dbg!()` and `println!()` in Rust | `blocking` |

The Python BECs use `paths: ["src/**/*.py"]`, the JS/TS ones `["**/*.js", "**/*.ts"]`, the Go bundles use `["**/*.go"]`, and the Rust bundles use `["**/*.rs"]`. After importing, adjust `paths` in your `.bec/rules.yaml` if your code lives elsewhere.