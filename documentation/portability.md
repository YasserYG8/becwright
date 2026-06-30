> **English** · [Español](portability.es.md)

# Portability: export / import

A BEC is **portable** — you can move it between repos. A bundle is a single
self-contained `.bec.yaml` file.

## Export

```bash
becwright export no-token-in-logs -o no-token-in-logs.bec.yaml
```

Without `-o`, the bundle is written to stdout.

## Import

```bash
becwright import no-token-in-logs.bec.yaml          # from a file
becwright import https://example.com/rule.bec.yaml  # from a URL
```

On import, becwright prints the rule and the check's code, then asks for
confirmation before installing — **importing a BEC means importing code that
runs on every commit**. Use `--yes` to skip the prompt in automation. becwright
refuses to overwrite an existing rule id or a different check file already on
disk.

## Bundle format

```yaml
becwright_bec: 1
exported_from: https://github.com/owner/repo   # provenance (the "bound" part)
rule:
  id: no-token-in-logs
  intent: ...
  why_it_matters: ...
  paths: ["src/**/*.py"]
  severity: blocking
check:
  kind: builtin            # builtin | script | command
  module: no_token_in_logs
```

The new rule is **appended** to the target's `.bec/rules.yaml`, preserving the
existing content (comments and formatting).

## The three check kinds

When you export a rule, its `check` command is classified:

| Kind | When | What travels in the bundle |
|---|---|---|
| `builtin` | `becwright run X [args]` | the module name (and args) |
| `script` | references a repo file, e.g. `.bec/checks/foo.py` | the script's source, embedded |
| `command` | anything else | the raw command string (a warning is shown on import) |

The legacy `python3 -m becwright.checks.X` form is still recognized on import,
so bundles exported by older versions keep working.

A `script` bundle lands its embedded code in `.bec/checks/` of the target repo,
so a custom check travels with its code. A `builtin` bundle only needs the name,
because that code ships with the becwright package.

## Catalog

The [`becs/`](../becs/) directory is a catalog of ready-to-use BECs, importable
directly from their raw URL. It includes Python and JavaScript/TypeScript BECs.
