> [English](usage.md) · **Español**

# Uso

## Instalación

```bash
pipx install becwright      # o: pip install becwright
```

## Configurar un repo

```bash
cd tu-repo
becwright install           # escribe .git/hooks/pre-commit
# creá .bec/rules.yaml (ver abajo)
```

A partir de ahí, cada `git commit` corre los checks.

## Comandos

| Comando | Descripción |
|---|---|
| `becwright check` | Corre las reglas sobre los archivos en staging |
| `becwright check --all` | Corre las reglas sobre todo el repo (`git ls-files`) |
| `becwright install` | Instala el hook pre-commit |
| `becwright uninstall` | Quita el hook |
| `becwright export <id> [-o archivo]` | Exporta una regla a un bundle `.bec.yaml` |
| `becwright import <fuente> [--yes]` | Importa una BEC de un archivo o URL http(s) |

Códigos de salida: `0` pasa · `1` falló una regla blocking · `2` no es un repo git / error de uso.

## El archivo de reglas: `.bec/rules.yaml`

```yaml
rules:
  - id: no-token-in-logs        # identificador único
    intent: >                   # qué pide la regla (la parte "bound")
      Los tokens de sesión nunca deben llegar a ningún log.
    why_it_matters: >           # por qué existe (se muestra cuando la regla falla)
      Un token en los logs deja que cualquiera robe una sesión.
    rejected_alternatives:      # opcional: enfoques considerados y descartados
      - "Redactar al loguear -> demasiado fácil de saltarse"
    paths:                      # globs de los archivos a los que aplica la regla
      - "src/**/*.py"
    check: "python3 -m becwright.checks.no_token_in_logs"
    severity: blocking          # blocking (frena el commit) | warning (solo avisa)
```

### Campos

| Campo | Requerido | Significado |
|---|---|---|
| `id` | sí | Id único de la regla |
| `paths` | sí | Globs (ver abajo) |
| `check` | sí | Comando de shell a correr (el check ejecutable) |
| `intent` | no | Qué hace cumplir la regla |
| `why_it_matters` | no | Por qué importa; se imprime cuando la regla falla |
| `rejected_alternatives` | no | Contexto: enfoques descartados |
| `severity` | no | `blocking` (por defecto) o `warning` |

### Globs

- `*` matchea cualquier cosa menos `/`.
- `**` matchea a través de directorios.
- p.ej. `src/**/*.py` matchea `src/a.py` y `src/x/y/z.py`; `src/*.py` matchea
  solo el nivel superior.

## Reglas listas para usar

becwright trae un [catálogo](../becs/) de BECs listas que podés importar:

```bash
becwright import https://raw.githubusercontent.com/DataDave-Dev/becwright/main/becs/no-debugger-js.bec.yaml
```
