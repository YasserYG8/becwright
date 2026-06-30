# Catálogo de BECs

BECs listas para importar a tu repo. Cada una es un bundle autocontenido; al
importar, becwright te muestra qué hace y pide confirmación antes de instalarla.

```bash
becwright import https://raw.githubusercontent.com/DataDave-Dev/becwright/main/becs/<archivo>
```

| BEC | Qué hace | Severidad |
|---|---|---|
| `no-token-in-logs.bec.yaml` | Frena tokens/credenciales en llamadas a logs | `blocking` |
| `no-hardcoded-secrets.bec.yaml` | Frena claves, tokens y contraseñas escritas en el código | `blocking` |
| `no-debug-remnants.bec.yaml` | Frena `breakpoint()`, `pdb.set_trace()`, `import pdb` olvidados | `blocking` |
| `no-dangerous-eval.bec.yaml` | Frena `eval()` / `exec()` | `blocking` |
| `no-wildcard-imports.bec.yaml` | Avisa de `from x import *` | `warning` |

Todas usan `paths: ["src/**/*.py"]` por defecto. Tras importar, ajustá `paths`
en tu `.bec/rules.yaml` si tu código vive en otro lado.
