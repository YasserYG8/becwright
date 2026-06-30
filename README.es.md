> [English](README.md) · **Español**

# becwright

[![CI](https://github.com/DataDave-Dev/becwright/actions/workflows/ci.yml/badge.svg)](https://github.com/DataDave-Dev/becwright/actions/workflows/ci.yml)

**Reglas que se ejecutan, no notas que se ignoran.**

`becwright` hace cumplir restricciones (constraints) sobre tu código de forma
determinista: en lugar de *pedirle* a un agente de IA que respete una regla
(como hace `CLAUDE.md`, `.cursorrules`, etc. — que el agente puede leer e
ignorar), becwright **verifica el resultado** y frena el commit si la regla
se rompe.

## El problema

Un agente de IA escribe código y deja una nota: *"esto nunca debe loguear
tokens de sesión"*. Esa nota es texto. Tres meses después, otro agente
regenera el módulo, no la lee, y mete el token en los logs. Nadie se entera
hasta que explota en producción.

Las notas son **probabilísticas** (dependen de que el agente lea, entienda y
obedezca). becwright es **determinista**: la regla se ejecuta sobre el código
real y da pasa/no-pasa, sin importar qué agente o modelo hizo el cambio.

| | Nota en CLAUDE.md | Regla becwright |
|---|---|---|
| Qué hace | *Pide* que se respete | *Verifica* que se respetó |
| Depende de | Que el agente la lea y obedezca | Nada — se ejecuta sobre el código |
| Resultado | Probable | Garantizado |
| Analogía | Letrero de "velocidad máxima" | Tope físico en la calle |

Las dos capas son complementarias: CLAUDE.md previene (que el 95% salga bien
a la primera), becwright es la red de seguridad para el 5% que se cuela.

## Concepto central: BEC (Bound Executable Constraint)

Una BEC es una constraint con tres propiedades que ningún artefacto actual
tiene juntas:

- **Bound (atada)** — la regla nace ligada a la *intención* y la decisión que
  la creó (el *por qué*), no es una regla suelta sin contexto.
- **Executable (ejecutable)** — lleva un chequeo que corre y devuelve
  pasa/no-pasa, no es prosa que alguien promete respetar.
- **Portable** — puede exportarse de un repo e importarse en otro, como un
  paquete (esto es lo que genera el efecto de red a futuro).

## Cómo se usa

becwright se instala una vez como herramienta; cada repo solo aporta su propio
`.bec/rules.yaml`.

```bash
# 1. Instalar el motor. Elegí tu ecosistema — sin Python vía npm/pnpm, que
#    traen un binario autónomo:
npm install --save-dev becwright    # o global: npm install -g becwright
pnpm add -D becwright
pipx install becwright              # o: pip install becwright

# 2. En tu repo, generar reglas + instalar el hook
becwright init                      # detecta tu lenguaje, escribe .bec/rules.yaml, instala el hook

# 3. Listo: cada commit corre los chequeos; si una regla blocking falla, frena.
```

Instalado como devDependency, el hook de pre-commit resuelve el binario local
desde `node_modules/.bin`, así funciona sin instalación global. Los paquetes npm
cubren `linux-x64`, `linux-arm64`, `darwin-x64`, `darwin-arm64` y `win32-x64`; en
cualquier otra plataforma usá `pipx install becwright`.

Comandos disponibles:

| Comando | Qué hace |
|---|---|
| `becwright init` | Genera un `.bec/rules.yaml` de arranque e instala el hook |
| `becwright list` | Lista los checks incluidos |
| `becwright check` | Corre las reglas sobre los archivos en staging |
| `becwright install` | Instala el hook `pre-commit` nativo |
| `becwright uninstall` | Quita el hook |
| `becwright export <id>` | Exporta una BEC a un archivo `.bec.yaml` |
| `becwright import <archivo\|URL>` | Importa una BEC de otro repo |

### Uso con agentes de IA (Claude Code)

becwright es la red determinista para lo que un agente de IA deja pasar. Hay un
plugin de Claude Code para que un agente lo instale y lo maneje por vos:

```text
/plugin marketplace add DataDave-Dev/becwright
/plugin install becwright@becwright
```

Agrega un skill `becwright` y un comando `/becwright`. Ver
[`integrations/claude-code/`](integrations/claude-code/).

Una regla en `.bec/rules.yaml`:

```yaml
rules:
  - id: no-token-in-logs
    intent: >
      Los tokens de sesión y credenciales nunca deben llegar a ningún log.
    why_it_matters: >
      Si un token aparece en los logs, cualquiera con acceso a ellos puede
      robar la sesión de un usuario.
    paths: ["src/**/*.py"]
    check: "becwright run no_token_in_logs"
    severity: blocking   # blocking = frena el commit | warning = solo avisa
```

## Checks incluidos

becwright trae chequeos listos para usar. Cada uno es un módulo que se invoca
desde el campo `check`. Son **basados en texto/regex** (no análisis AST), así
que son conservadores y pueden tener casos límite; el valor está en atar cada
regla a su *por qué*.

| Check | Qué detecta | Lenguaje | Severidad sugerida |
|---|---|---|---|
| `forbid` | Cualquier regex que le pases (`--pattern`) | cualquiera | según el caso |
| `no_token_in_logs` | Tokens/credenciales en llamadas a logs | Python | `blocking` |
| `hardcoded_secrets` | Claves AWS, claves privadas, `password = "..."` literales | cualquiera | `blocking` |
| `debug_remnants` | `breakpoint()`, `pdb.set_trace()`, `import pdb` olvidados | Python | `blocking` |
| `dangerous_eval` | Llamadas a `eval()` / `exec()` | cualquiera | `blocking` |
| `wildcard_imports` | `from x import *` | Python | `warning` |

## Cualquier lenguaje

becwright es **agnóstico al lenguaje**: el motor solo filtra archivos por sus
`paths` (globs) y corre el `check` como un comando; nunca asume Python. Podés
vigilar JavaScript, Go, Rust, o lo que sea.

La forma más rápida de escribir una regla para otro lenguaje —sin escribir
código— es el check `forbid`, que falla si un regex aparece en los archivos:

```yaml
rules:
  - id: no-debugger-js
    intent: >
      No dejar 'debugger;' en el código JavaScript/TypeScript.
    why_it_matters: >
      Un 'debugger' olvidado detiene la ejecución y no debería llegar a producción.
    paths: ["**/*.js", "**/*.ts"]
    check: "becwright run forbid --pattern '\\bdebugger\\b'"
    severity: blocking
```

`forbid` acepta `--pattern REGEX`, `--ignore-case` y `--message TEXTO`. Para
checks más finos, escribí tu propio script en el lenguaje que quieras (un
ejecutable que lea la lista de archivos por stdin y salga con código 0/1) y
apuntá `check` a él.

## Compartir BECs entre repos

Una BEC es **portable**: podés sacarla de un repo e instalarla en otro. Un
bundle es un único archivo `.bec.yaml` autocontenido (la regla + el código del
check si es custom).

```bash
# En el repo de origen: exportar una regla a un archivo
becwright export no-token-in-logs -o no-token-in-logs.bec.yaml

# En otro repo: importar (desde archivo o URL http/https)
becwright import no-token-in-logs.bec.yaml
becwright import https://ejemplo.com/no-token-in-logs.bec.yaml
```

Al importar, becwright **muestra el código del check y pide confirmación** antes
de instalarlo: importar una BEC es importar código que se ejecutará en cada
commit. Usá `--yes` para saltar la confirmación en entornos automatizados.

Hay un **catálogo de BECs listas para usar** en [`becs/`](becs/) que podés
importar directo desde su URL cruda.

Los checks built-in (`becwright run *`) viajan con el paquete, así
que el bundle solo guarda su nombre. Un check **custom** (`.bec/checks/foo.py`)
viaja con su código embebido y aterriza en `.bec/checks/` del repo destino.

## Documentación

La documentación técnica vive en [`documentation/`](documentation/README.es.md):
[arquitectura y flujo](documentation/architecture.es.md),
[uso y esquema de reglas](documentation/usage.es.md),
[escribir checks](documentation/writing-checks.es.md), y
[portabilidad](documentation/portability.es.md).

## Estado actual

El **MVP instalable** está construido y verificado end-to-end: motor empaquetado
(`src/becwright/`), CLI (`check` / `install` / `uninstall` / `export` /
`import`), hook de git nativo que frena un commit con un token en un log, checks
incluidos (Python + el genérico `forbid` para cualquier lenguaje), portabilidad
de BECs entre repos, catálogo con BECs de Python y JS/TS, y tests en verde. El
prototipo original queda **archivado** en `prototype/` como referencia.

El trabajo futuro (análisis AST, tooling profundo por lenguaje, firma de
verificaciones) está documentado en el plan del proyecto.
