> [English](usage.md) · **Español**

# Uso

**En corto:** instalá becwright una vez, corré `becwright init` dentro de tu
proyecto, y a partir de ahí cada vez que guardás tu trabajo (un *commit*) revisa
tu código contra tus reglas y frena el commit si se rompe una regla blocking.
Ese es todo el ciclo — el resto de esta página es el detalle.

## Instalación

```bash
pipx install becwright      # o: pip install becwright
```

## Configurar un repo

```bash
cd tu-repo
becwright init              # genera .bec/rules.yaml (según el lenguaje) e instala el hook
```

`init` detecta si el repo tiene archivos Python o JS/TS y escribe un
`.bec/rules.yaml` de arranque con reglas acordes, y luego instala el hook
pre-commit. Revisá las reglas generadas y corré `becwright check --all` para ver
el estado actual.

A partir de ahí, cada `git commit` corre los checks. (También podés configurarlo
a mano: `becwright install` más un `.bec/rules.yaml` que escribas vos.)

> **¿Adoptándolo en un código que ya existe?** Corré `becwright init --baseline`.
> Corre las reglas de arranque contra tu código actual y arranca en `warning`
> (en vez de `blocking`) toda regla que *ya* tiene violaciones, así becwright
> nunca frena un commit por deuda preexistente. Las reglas limpias quedan
> `blocking` — guardarraíl desde el día uno. Cada regla degradada queda anotada
> con su conteo de violaciones; limpiá la deuda con el tiempo y volvela a
> `blocking`.

> **¿Ya tenés un `CLAUDE.md` (o similar)?** Corré `becwright init --from-claude-md`.
> Escanea el archivo buscando prohibiciones que reconoce — secretos, `eval`,
> `debugger`, `console.log`, breakpoints, imports con `*`, tokens en logs — y
> convierte cada una en una regla enforzable, informando qué frase la disparó.
> También detecta un límite de líneas por archivo ("archivos < 800 líneas" →
> `max_lines`), ignorando reglas de largo de función que no puede enforzar. Es
> best-effort y según el lenguaje, así que **revisá el resultado**; lo de criterio
> (arquitectura, naming, inmutabilidad) no tiene check determinista y se queda en
> `CLAUDE.md`. Combinalo con `--baseline` para adoptar en un repo sucio de una.

## Comandos

| Comando | Descripción |
|---|---|
| `becwright demo` | Muestra a becwright frenando un commit malo de ejemplo (sin configurar nada, sin git) |
| `becwright init` | Genera un `.bec/rules.yaml` de arranque e instala el hook |
| `becwright init --baseline` | Igual, pero arranca en `warning` las reglas que ya tienen violaciones (adoptar en un código sucio sin frenar commits) |
| `becwright init --from-claude-md` | Deriva reglas del `CLAUDE.md` del repo (best-effort; mapea prohibiciones conocidas a checks) |
| `becwright list` | Lista los checks incluidos |
| `becwright check` | Corre las reglas sobre los archivos en staging |
| `becwright check --all` | Corre las reglas sobre todo el repo (`git ls-files`) |
| `becwright install` | Instala el hook pre-commit |
| `becwright uninstall` | Quita el hook |
| `becwright export <id> [-o archivo]` | Exporta una regla a un bundle `.bec.yaml` |
| `becwright import <fuente> [--yes]` | Importa una BEC de un archivo o URL http(s) |

> **¿"Archivos en staging"?** Cuando corrés `git add`, los archivos que elegís
> quedan *en staging* — en la fila para el próximo commit. `becwright check` mira
> solo esos por defecto (justo lo que el commit va a crear), por eso es rápido.
> Usá `--all` para escanear todo el proyecto.

Códigos de salida (el número que devuelve un comando al terminar; `0` significa
éxito): `0` pasa · `1` falló una regla blocking · `2` no es un repo git / error
de uso.

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
    exclude:                    # opcional: globs restados de `paths`
      - "src/logging_setup.py"  #   (p.ej. la implementación del propio check)
    check: "becwright run no_token_in_logs"
    severity: blocking          # blocking (frena el commit) | warning (solo avisa)
```

### Campos

| Campo | Requerido | Significado |
|---|---|---|
| `id` | sí | Id único de la regla |
| `paths` | sí | Globs (ver abajo) |
| `check` | sí | Comando de shell a correr (el check ejecutable) |
| `exclude` | no | Globs restados de `paths` (ver abajo) |
| `intent` | no | Qué hace cumplir la regla |
| `why_it_matters` | no | Por qué importa; se imprime cuando la regla falla |
| `rejected_alternatives` | no | Contexto: enfoques descartados |
| `severity` | no | `blocking` (por defecto) o `warning` |

### Globs

- `*` matchea cualquier cosa menos `/`.
- `**` matchea a través de directorios.
- p.ej. `src/**/*.py` matchea `src/a.py` y `src/x/y/z.py`; `src/*.py` matchea
  solo el nivel superior.

### Excluir archivos

`exclude` recorta globs de `paths`, así una sola regla puede cubrir todo un
lenguaje salteando archivos que solo darían falsos positivos — código vendored,
archivos generados, o la implementación del propio check. Un archivo que matchea
tanto `paths` como `exclude` se saltea.

```yaml
  - id: no-console-log
    paths:
      - "**/*.ts"
    exclude:
      - "lib/logger.ts"   # el logger envuelve console.log de forma legítima
    check: "becwright run forbid --pattern 'console\\.log'"
    severity: warning
```

`exclude` viaja con la regla en `export` / `import`, así que el recorte es
portable junto con la BEC.

## Reglas listas para usar

becwright trae un [catálogo](../src/becwright/becs/) de BECs listas dentro del
paquete — instalás desde él con un comando, sin URL y sin conexión:

```bash
becwright search              # lista el catálogo
becwright add no-debugger-js  # instalá una
```
