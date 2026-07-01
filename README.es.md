> [English](README.md) · **Español**

<p align="center">
  <img src="assets/becwright-logo.svg" alt="becwright" width="140" height="140">
</p>

# becwright

[![CI](https://github.com/DataDave-Dev/becwright/actions/workflows/ci.yml/badge.svg)](https://github.com/DataDave-Dev/becwright/actions/workflows/ci.yml)
[![npm](https://img.shields.io/npm/v/becwright?logo=npm)](https://www.npmjs.com/package/becwright)
[![PyPI](https://img.shields.io/pypi/v/becwright?logo=pypi&logoColor=white)](https://pypi.org/project/becwright/)

**Reglas que se ejecutan, no notas que se ignoran.**

<p align="center">
  <img src="assets/becwright-demo.svg" alt="becwright frenando un commit que hardcodea un secreto y usa eval" width="640">
</p>

> **Velo en 5 segundos** — sin configurar nada, sin git, sin tocar tu máquina:
> ```bash
> becwright demo                  # después de instalar (ver abajo)
> # sin instalar: npx becwright demo   ·   o: pipx run becwright demo
> ```

`becwright` hace cumplir restricciones (constraints) sobre tu código de forma
determinista: en lugar de *pedirle* a un agente de IA que respete una regla
(como hace `CLAUDE.md`, `.cursorrules`, etc. — que el agente puede leer e
ignorar), becwright **verifica el resultado** y frena el commit si la regla
se rompe.

## En cristiano

¿Primera vez con una herramienta así? La idea entera en tres líneas:

Un **commit** es el momento en que *guardás* tu trabajo en git. becwright es un
guardia parado en esa puerta. Justo antes de guardar, corre tus reglas sobre el
código:

- ✅ si todo pasa → el commit entra;
- ❌ si una regla se rompe → te frena, te dice qué regla es y *por qué* existe,
  y espera hasta que lo arregles.

Una nota en `CLAUDE.md` es un *letrero* que pide a las personas (y a los agentes
de IA) que se porten bien. becwright es el *guardia que revisa*. Un letrero se
puede ignorar; el guardia no.

> **Dos palabras que vas a ver mucho:** un **commit** es una foto guardada de tu
> código en git. Un **hook** es un pequeño script que git ejecuta solo en un
> momento determinado — becwright usa el hook *pre-commit*, que se dispara justo
> antes de guardar un commit. Nunca lo corrés a mano; lo hace git.

El resto de este README va de "solo quiero empezar" hasta el detalle técnico
completo — leé hasta donde necesites.

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

## Características

- **Cumplimiento determinista** — una regla es un chequeo real que corre sobre tu
  código y da pasa/no-pasa, no una nota que un agente puede ignorar.
- **Frena el commit, no solo avisa** — las reglas blocking detienen
  `git commit`; las warning informan sin frenar.
- **Cualquier lenguaje** — el motor matchea globs y corre un comando; usá el
  `forbid` sin código (regex) para Python, JS/TS, Go, Rust o lo que sea.
- **Deriva reglas de tu `CLAUDE.md`** — `becwright init --from-claude-md` convierte
  las prohibiciones que reconoce (secretos, `eval`, `debugger`, `console.log`,
  breakpoints, un límite de líneas por archivo, …) en reglas enforzables; un agente
  de IA puede extenderlo por MCP. Lo de criterio se queda en `CLAUDE.md`.
- **Se adopta en cualquier código** — `--baseline` arranca en `warning` las reglas
  que *ya* tienen violaciones, así un repo legacy no se frena el día uno; graduás
  cada una a blocking a medida que la limpiás.
- **Reglas garantizadas *y* asistidas** — las deterministas `block` con garantía
  al 100%; las de criterio (legibilidad, diseño) viven como `advisory` — informan
  con un revisor tuyo (p. ej. un LLM) pero nunca bloquean, y quedan etiquetadas
  para que siempre sepas qué está garantizado y qué es best-effort.
- **Atada al _por qué_** — cada regla lleva su intención y su razón, que se
  muestran cuando se dispara.
- **Checks incluidos** — `forbid` / `require` (un patrón que *debe* estar) /
  `max_lines` / `filename`, más checks de secretos, `eval`, debug e imports — con
  `exclude:` por regla para silenciar falsos positivos.
- **BECs portables** — `export` de una regla a un `.bec.yaml` e `import` en otro
  repo; los checks custom viajan con su código.
- **Catálogo offline** — `becwright search` / `add` instalan reglas listas sin
  URL, empaquetadas dentro del paquete.
- **Sin Python** — instalá por npm/pnpm como binario autónomo, o por pip/pipx.
- **Se adapta a tu setup** — hook de git nativo, o enchufado al framework
  pre-commit o a Husky.
- **Listo para agentes de IA** — plugin de Claude Code, `check --json` y un
  servidor MCP con tools para que un agente proponga, previsualice y agregue reglas
  desde tu `CLAUDE.md`.
- **Chico y confiable** — dependencias mínimas (`pyyaml`), sin `eval`/`exec`, con
  dogfooding en CI.

## Casos de uso

- **Convertí tu `CLAUDE.md` en guardarraíles** — lo determinista pasa a BECs que no
  se pueden ignorar; lo de criterio se queda como prosa.
- **Adoptá gradualmente en un repo legacy** — `--baseline` avisa sobre la deuda
  existente sin frenar commits, y después apretás a blocking regla por regla.
- **Frenar secretos antes de que entren** — API keys, tokens, claves privadas,
  contraseñas hardcodeadas.
- **Que no queden restos de debug** — `breakpoint()`, `pdb`, `debugger;`,
  `console.log`, `dbg!`, `panic()` olvidados.
- **Prohibir APIs riesgosas / hacer cumplir convenciones** — `eval` / `exec`, un
  límite de líneas por archivo, reglas de nombre de archivo, o cualquier patrón que
  vetes con una regla regex de una línea.
- **Reglas sobre el mensaje del commit** — Conventional Commits, o bloquear líneas
  de atribución de IA, con una regla `target: commit-msg` y el hook `commit-msg`.
- **Proteger código escrito por IA** — la red determinista para lo que un agente
  regenera y olvida.
- **Hacer cumplir convenciones del equipo** — codificá una decisión una vez como
  BEC y compartila entre todos los repos.

## Cómo se usa

becwright se instala una vez; cada proyecto solo agrega un `.bec/rules.yaml`
chico. **Dos pasos y listo.**

**1. Instalar** — una línea:

```bash
npm install -g becwright
```

<details>
<summary>¿Preferís pnpm, pip, o instalación local al proyecto? →</summary>

```bash
pnpm add -g becwright
pipx install becwright                # o: pip install becwright
npm install --save-dev becwright      # local al proyecto; el hook lo encuentra en node_modules/.bin
```

Por npm/pnpm **no hace falta Python** — viene un binario autónomo por plataforma
(`linux-x64`, `linux-arm64`, `darwin-x64`, `darwin-arm64`, `win32-x64`). En
cualquier otra plataforma, usá `pipx install becwright`.
</details>

**2. Configurarlo** — dentro de tu proyecto:

```bash
becwright init   # detecta tu lenguaje, escribe .bec/rules.yaml, instala el hook pre-commit
```

Listo. A partir de ahora cada `git commit` corre los chequeos solo, y frena un
commit que rompa una regla blocking. No volvés a llamar a becwright a mano.

**¿Adoptándolo en un código que ya existe?** Usá `becwright init --baseline`: las
reglas que *ya* tienen violaciones arrancan en `warning` (no se frena nada
legítimo) y las limpias arrancan en `blocking`. Limpiá la deuda con el tiempo y
después graduá cada regla a `blocking`.

**¿Ya tenés un `CLAUDE.md`?** `becwright init --from-claude-md` lo lee y convierte
las prohibiciones que reconoce (secretos, `eval`, `debugger`, `console.log`,
breakpoints, …) en reglas enforzables — la red determinista debajo de la prosa.
Lo de criterio se queda en `CLAUDE.md`. Revisá el resultado; combinalo con
`--baseline` para adoptar en un repo sucio de una.

Instalado como devDependency, el hook de pre-commit resuelve el binario local
desde `node_modules/.bin`, así funciona sin instalación global. Los paquetes npm
cubren `linux-x64`, `linux-arm64`, `darwin-x64`, `darwin-arm64` y `win32-x64`; en
cualquier otra plataforma usá `pipx install becwright`.

Comandos disponibles:

| Comando | Qué hace |
|---|---|
| `becwright demo` | Muestra a becwright frenando un commit malo de ejemplo (sin configurar nada, sin git) |
| `becwright init` | Genera un `.bec/rules.yaml` de arranque e instala el hook |
| `becwright init --baseline` | Igual, pero arranca en `warning` las reglas que ya tienen violaciones (adoptar sin frenar commits) |
| `becwright init --from-claude-md` | Deriva reglas del `CLAUDE.md` del repo (best-effort) |
| `becwright list` | Lista los checks incluidos |
| `becwright check` | Corre las reglas sobre los archivos en staging |
| `becwright search [texto]` | Lista BECs listas del catálogo incluido |
| `becwright add <nombre>` | Instala una BEC del catálogo en `.bec/rules.yaml` (sin conexión) |
| `becwright install` | Instala el hook `pre-commit` nativo |
| `becwright uninstall` | Quita el hook |
| `becwright export <id>` | Exporta una BEC a un archivo `.bec.yaml` |
| `becwright import <archivo\|URL>` | Importa una BEC de otro repo |

### ¿Ya usás pre-commit o Husky?

Si tu repo ya administra los git hooks, becwright se enchufa sin `becwright
install`.

**[pre-commit](https://pre-commit.com)** — agregá esto a `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/DataDave-Dev/becwright
    rev: v0.3.0
    hooks:
      - id: becwright
```

**Husky** (repos JS/TS) — en `.husky/pre-commit`:

```sh
npx becwright check
```

En ambos casos becwright igual lee `.bec/rules.yaml` y frena el commit ante una
regla bloqueante rota. Solo necesitás `becwright init` una vez para generar las
reglas (salteá su instalación del hook si otra herramienta lo administra).

### Uso con agentes de IA (Claude Code)

becwright es la red determinista para lo que un agente de IA deja pasar. Hay un
plugin de Claude Code para que un agente lo instale y lo maneje por vos:

```text
/plugin marketplace add DataDave-Dev/becwright
/plugin install becwright@becwright
```

Agrega un skill `becwright` y un comando `/becwright`. Ver
[`integrations/claude-code/`](integrations/claude-code/).

Para resultados estructurados, `becwright check --json` imprime un resumen
legible por máquina, y `becwright mcp` (instalá el extra `mcp`: `pipx install
"becwright[mcp]"`) levanta un servidor MCP — MCP es una forma estándar de que
las herramientas de IA se conecten a habilidades extra — que expone `check` y
`list_checks` a cualquier agente. Ver [`documentation/mcp.md`](documentation/mcp.md).

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
    exclude: ["src/logging_setup.py"]   # opcional: globs restados de paths
    check: "becwright run no_token_in_logs"
    severity: blocking   # blocking = frena el commit | warning = solo avisa
```

`exclude` resta globs de `paths`, así una sola regla puede cubrir todo un
lenguaje salteando los archivos que solo darían falsos positivos — código
vendored o generado, o la implementación del propio check. Viaja con la regla en
`export` / `import`. Referencia completa de campos:
[`documentation/usage.es.md`](documentation/usage.es.md).

## Cómo se compara becwright

becwright no es un linter ni solo un lanzador de hooks — es la capa que hace que
una *regla* sea portable y esté atada a su razón, y que frena el commit por ella.

| | becwright | pre-commit / Husky | gitleaks / linters | CLAUDE.md / .cursorrules |
|---|:---:|:---:|:---:|:---:|
| Corre un chequeo real | ✅ | ✅ (corre otras herramientas) | ✅ | ❌ prosa |
| Frena el commit | ✅ | ✅ | ✅ | ❌ |
| Lleva el *por qué* (intención) | ✅ | ❌ | ❌ | ⚠️ no se exige |
| Regla portable entre repos | ✅ `export`/`import` | ⚠️ copiar config | ⚠️ | ⚠️ |
| Cualquier lenguaje, sin plugin por herramienta | ✅ `forbid` regex | ⚠️ | ❌ atado a la herramienta | n/a |

becwright los **complementa** en lugar de reemplazarlos: corré gitleaks o un
linter *como* un check de becwright, o agregá becwright *dentro* de pre-commit /
Husky. La diferencia es que una BEC ata la regla a su intención y viaja entre
repos.

## Checks incluidos

becwright trae chequeos listos para usar. Cada uno es un módulo que se invoca
desde el campo `check`. Funcionan **buscando texto** dentro de tus archivos con
un patrón (un *regex* — un patrón de búsqueda de texto, tipo "encontrá esta
palabra exacta"), en vez de entender el código de verdad. Eso los hace simples y
predecibles: pueden pasar por alto casos raros, y el verdadero valor está en
atar cada regla a su *por qué*.

| Check | Qué detecta | Lenguaje | Severidad sugerida |
|---|---|---|---|
| `forbid` | Cualquier regex que le pases (`--pattern`) | cualquiera | según el caso |
| `require` | Un regex (`--pattern`) que *debe* aparecer (p. ej. un header de licencia) | cualquiera | según el caso |
| `max_lines` | Archivos con más de `--max` líneas | cualquiera | `warning` |
| `filename` | Nombres de archivo que matchean `--forbid` o no matchean `--require` | cualquiera | según el caso |
| `no_token_in_logs` | Tokens/credenciales en llamadas a logs | Python | `blocking` |
| `hardcoded_secrets` | Claves AWS, claves privadas, `password = "..."` literales | cualquiera | `blocking` |
| `debug_remnants` | `breakpoint()`, `pdb.set_trace()`, `import pdb` olvidados | Python | `blocking` |
| `dangerous_eval` | Llamadas a `eval()` / `exec()` | cualquiera | `blocking` |
| `conflict_markers` | Marcadores de conflicto de merge olvidados (`<<<<<<<`) | cualquiera | `blocking` |
| `wildcard_imports` | `from x import *` | Python | `warning` |

## Reglas listas para usar (sin escribir nada)

¿No querés escribir reglas vos mismo? El catálogo viaja **dentro** de becwright,
así que instalás una regla con un solo comando — sin URL y sin conexión.
becwright te muestra la regla y después la deja en tu `.bec/rules.yaml`, lista
para usar:

```bash
becwright search                 # lista todas las BECs del catálogo
becwright search secret          # filtrá por una palabra

becwright add no-token-in-logs   # instalá una (Python)
becwright add no-debugger-js     # JavaScript / TypeScript
becwright add no-hardcoded-secrets   # cualquier lenguaje
```

La lista completa (Python, JS/TS, Go, Rust) vive en
[`src/becwright/becs/`](src/becwright/becs/).

## Cualquier lenguaje

becwright es **agnóstico al lenguaje**: el motor solo filtra archivos por sus
`paths` (escritos como *globs* — patrones de archivos como `src/**/*.js`, donde
`*` significa "cualquier nombre" y `**` significa "cualquier carpeta, por más
profunda que esté") y corre el `check` como un comando; nunca asume Python.
Podés vigilar JavaScript, Go, Rust, o lo que sea.

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

Hay un **catálogo de BECs listas para usar** dentro de becwright: corré
`becwright search` para listarlas y `becwright add <nombre>` para instalar una
(también viven en [`src/becwright/becs/`](src/becwright/becs/) para navegarlas).

Los checks built-in (`becwright run *`) viajan con el paquete, así
que el bundle solo guarda su nombre. Un check **custom** (`.bec/checks/foo.py`)
viaja con su código embebido y aterriza en `.bec/checks/` del repo destino.

## Documentación

La documentación completa vive en [`documentation/`](documentation/README.es.md).
Cada página arranca con un resumen en lenguaje simple y después profundiza, así
que empezá donde estés:

- **Recién empezás:** [uso](documentation/usage.es.md) — instalación, los
  comandos y cómo escribir una regla.
- **Querés agregar tu propia regla:** [escribir checks](documentation/writing-checks.es.md)
  — desde el atajo sin código `forbid` hasta un check propio en cualquier lenguaje.
- **Compartir reglas entre proyectos:** [portabilidad](documentation/portability.es.md).
- **Curiosidad por cómo funciona adentro:** [arquitectura y flujo](documentation/architecture.es.md).
- **Conectarlo a un agente de IA:** [MCP y salida JSON](documentation/mcp.es.md).

## Estado actual

becwright está **publicado e instalable en todas las plataformas**: vía npm/pnpm
como binario autónomo (sin Python) y vía pip/pipx. El motor empaquetado
(`src/becwright/`) trae una CLI (`demo` / `init` / `list` / `check` (con
`--json`) / `run` / `install` / `uninstall` / `export` / `import` / `mcp`), un hook de git
nativo, checks incluidos (Python + el genérico `forbid` para cualquier
lenguaje), portabilidad de BECs entre repos, y un catálogo con BECs de Python,
JS/TS, Go y Rust.

Para agentes de IA hay un **plugin de Claude Code** y un **servidor MCP**
(`becwright mcp`), además de la salida estructurada `check --json`. El prototipo
original queda **archivado** en `prototype/` como referencia, y los tests están
en verde.

El trabajo futuro (análisis AST, tooling profundo por lenguaje, firma de
verificaciones) está documentado en el plan del proyecto.

## Roadmap

becwright es chico a propósito. En el horizonte:

- Ampliar el catálogo de `becwright add` con más lenguajes y reglas comunes.
- Una landing page y un set `examples/` más rico.
- Más checks incluidos, guiados por el uso real.

Deliberadamente **fuera de alcance** para mantenerlo simple y determinista:
análisis basado en AST, suites profundas por lenguaje, y firma criptográfica de
BECs.

## FAQ

**¿No hace esto ya `pre-commit`?** `pre-commit` corre herramientas; no te da una
regla que lleve su *por qué* y viaje entre repos. Incluso podés correr becwright
*dentro* de pre-commit — ver más arriba.

**¿Necesito Python?** No. `npm i -g becwright` instala un binario autónomo;
`pipx install becwright` también funciona.

**¿Funciona en Windows?** Sí, vía Git Bash (el hook es un script `sh`, que Git
para Windows provee). La CLI `becwright` en sí es multiplataforma.

**¿Cómo ignoro una línea?** Poné un comentario `becwright: ignore` en ella.

**¿Cómo se pronuncia "becwright" / qué significa?** *bec-wright* — un "wright" es
un artesano/hacedor (como en *playwright*), así que becwright es "el que hace
BECs".

**¿Es seguro importar una BEC?** becwright muestra el código del check y pide
confirmación antes de instalar. Tratá un bundle no confiable como cualquier
script no confiable.

## Contribuir

Las contribuciones son bienvenidas — mirá [CONTRIBUTING.md](CONTRIBUTING.md) y el
[Código de Conducta](CODE_OF_CONDUCT.md). ¿Encontraste un problema de seguridad?
Seguí la [política de seguridad](SECURITY.md). El [changelog](CHANGELOG.md)
registra cada release.

## Licencia

[MIT](LICENSE) © Alonso David De Leon Rodarte
