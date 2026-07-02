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
> `max_lines`), ignorando reglas de largo de función que no puede enforzar. Una
> frase amplia como "seguir buenas prácticas" se expande al set determinista de
> higiene (sin secretos, `eval`, restos de debug ni marcadores de conflicto), y
> frases como "conventional commits" o "sin atribución de IA" se vuelven reglas
> `commit-msg`. Es
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

### Códigos de salida

El número que devuelve un comando al terminar. Forman parte del contrato estable
de becwright — scripts y CI pueden depender de ellos:

| Código | Significado |
|---|---|
| `0` | Pasó — ninguna regla blocking falló (o no había nada que revisar). |
| `1` | Falló una regla **blocking**. Es la señal que frena un commit. Un hallazgo `warning`/`advisory` por sí solo **no** activa esto. |
| `2` | Un problema a corregir antes de que becwright pueda juzgar: no es un repo git, un `.bec/rules.yaml` malformado/no confiable, una regla que apunta a un check integrado inexistente, o un error de uso. |

### `check --json`

`becwright check --json` imprime un objeto JSON y sigue usando los códigos de
salida de arriba (`1` cuando bloquea). La forma es estable:

```json
{
  "rule_count": 2,
  "checked_files": 5,
  "blocked": true,
  "results": [
    {
      "id": "no-token-in-logs",
      "severity": "blocking",
      "passed": false,
      "intent": "Los tokens de sesión nunca deben llegar a ningún log.",
      "why_it_matters": "Un token en los logs deja robar una sesión.",
      "output": "src/app.py:12: token=..."
    }
  ]
}
```

`intent`, `why_it_matters` y `output` son `null` cuando faltan. `results` está
vacío cuando no había nada que evaluar.

## El archivo de reglas: `.bec/rules.yaml`

```yaml
schema_version: 1               # versión de formato opcional; ausente = 1
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
| `paths` | sí* | Globs (ver abajo); no hace falta en reglas `commit-msg` |
| `check` | sí | Comando de shell a correr (el check ejecutable) |
| `exclude` | no | Globs restados de `paths` (ver abajo) |
| `intent` | no | Qué hace cumplir la regla |
| `why_it_matters` | no | Por qué importa; se imprime cuando la regla falla |
| `rejected_alternatives` | no | Contexto: enfoques descartados |
| `severity` | no | `blocking` (por defecto), `warning` o `advisory` (ver abajo) |
| `target` | no | `files` (por defecto) o `commit-msg` (ver abajo) |

**`schema_version`** es una clave opcional de nivel superior (no un campo de
regla). Sella la versión de formato del archivo; cuando falta se trata como `1`,
así que los archivos existentes siguen funcionando. `becwright init` la escribe,
y becwright rechaza un archivo sellado con una versión *más nueva* de la que
entiende — pidiéndote actualizar — en vez de mal-interpretarlo. Rara vez la tocas
a mano.

> **Conjunto de campos estable.** Los nueve campos de arriba están congelados
> desde `schema_version 1`. Desde `1.0.0`, un campo solo se añade o quita bajo la
> [política de deprecación](stability.es.md) (deprecado
> con un warning durante al menos un minor, quitado solo en el siguiente major),
> así que un archivo de reglas válido hoy sigue válido en toda la línea `1.x`.

**Severidad — garantizado vs asistido.** `blocking` y `warning` son para checks
*deterministas*: el mismo código siempre da el mismo veredicto, así que una regla
`blocking` es una **garantía al 100%**. `advisory` es el hogar honesto de las
reglas de *criterio* cuyo check no es determinista — p. ej. una que llama a un LLM
para revisar legibilidad o diseño. Una regla `advisory` **informa pero nunca
bloquea**, y aparece etiquetada `ADVISORY (best-effort, not a guarantee)`, así
siempre sabés qué hallazgos están garantizados y cuáles son asistidos. becwright
aporta el tier; el revisor es un check tuyo (apuntalo a la herramienta que quieras),
así que no hay dependencia de LLM dentro de becwright.

### Globs

- `*` matchea cualquier cosa menos `/`.
- `**` matchea a través de directorios.
- p.ej. `src/**/*.py` matchea `src/a.py` y `src/x/y/z.py`; `src/*.py` matchea
  solo el nivel superior.

### Reglas sobre el mensaje del commit (`target: commit-msg`)

Una regla con `target: commit-msg` revisa el **mensaje del commit** en vez de los
archivos (`becwright init` instala un hook `commit-msg` además del `pre-commit`).
No necesita `paths`; el mensaje se le pasa al check, así que los checks genéricos
`require` / `forbid` funcionan sobre él. Dos ejemplos que `--from-claude-md` puede
generar (a partir de frases como "conventional commits" / "sin atribución de IA"):

```yaml
  - id: conventional-commits
    target: commit-msg
    check: |-
      becwright run require --pattern '^(feat|fix|docs|refactor|test|chore|ci|perf|build|style|revert)(\(.+\))?!?: '
    severity: blocking
  - id: no-ai-attribution
    target: commit-msg
    check: |-
      becwright run forbid --ignore-case --pattern 'co-authored-by:.*(claude|anthropic|gpt|copilot)|generated with.*(claude|chatgpt|copilot)'
    severity: blocking
```

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
