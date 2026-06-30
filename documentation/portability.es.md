> [English](portability.md) · **Español**

# Portabilidad: export / import

Una BEC es **portable** — podés moverla entre repos. Un bundle es un único
archivo `.bec.yaml` autocontenido.

## Export

```bash
becwright export no-token-in-logs -o no-token-in-logs.bec.yaml
```

Sin `-o`, el bundle se escribe a stdout.

## Import

```bash
becwright import no-token-in-logs.bec.yaml          # desde un archivo
becwright import https://ejemplo.com/rule.bec.yaml  # desde una URL
```

Al importar, becwright imprime la regla y el código del check, y pide
confirmación antes de instalar — **importar una BEC es importar código que se
ejecuta en cada commit**. Usá `--yes` para saltar la confirmación en automático.
becwright se niega a pisar un id de regla existente o un archivo de check distinto
que ya esté en disco.

## Formato del bundle

```yaml
becwright_bec: 1
exported_from: https://github.com/owner/repo   # provenance (la parte "bound")
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

La regla nueva se **agrega** al `.bec/rules.yaml` del repo destino, preservando
el contenido existente (comentarios y formato).

## Los tres tipos de check

Al exportar una regla, su comando `check` se clasifica:

| Tipo | Cuándo | Qué viaja en el bundle |
|---|---|---|
| `builtin` | `python3 -m becwright.checks.X [args]` | el nombre del módulo (y los args) |
| `script` | referencia un archivo del repo, p.ej. `.bec/checks/foo.py` | el código fuente del script, embebido |
| `command` | cualquier otra cosa | el string crudo del comando (se avisa al importar) |

Un bundle `script` aterriza su código embebido en `.bec/checks/` del repo
destino, así un check propio viaja con su código. Un bundle `builtin` solo
necesita el nombre, porque ese código viene con el paquete becwright.

## Catálogo

El directorio [`becs/`](../becs/) es un catálogo de BECs listas para usar,
importables directo desde su URL cruda. Incluye BECs de Python y JavaScript/TypeScript.
