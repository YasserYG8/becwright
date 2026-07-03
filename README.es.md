> [English](README.md) · **Español**

<p align="center">
  <img src="assets/becwright-logo.svg" alt="becwright" width="140" height="140">
</p>

# becwright

[![CI](https://github.com/DataDave-Dev/becwright/actions/workflows/ci.yml/badge.svg)](https://github.com/DataDave-Dev/becwright/actions/workflows/ci.yml)
[![npm](https://img.shields.io/npm/v/becwright?logo=npm)](https://www.npmjs.com/package/becwright)
[![npm downloads](https://img.shields.io/npm/dm/becwright?logo=npm&label=descargas)](https://www.npmjs.com/package/becwright)
[![PyPI](https://img.shields.io/pypi/v/becwright?logo=pypi&logoColor=white)](https://pypi.org/project/becwright/)
[![Versiones de Python](https://img.shields.io/pypi/pyversions/becwright?logo=python&logoColor=white)](https://pypi.org/project/becwright/)
[![Licencia: MIT](https://img.shields.io/badge/licencia-MIT-green)](LICENSE)

**La capa de enforcement para agentes de IA.** <sub>(se pronuncia *bec-ráit* — un "wright" es un artesano, como en *playwright*)</sub>

Reglas que se ejecutan, no notas que se ignoran. Tu `CLAUDE.md` es un *cartel*;
becwright es el *guardia* — corre tus reglas sobre el código y frena el commit
cuando una se rompe, sin importar qué modelo (o persona) lo escribió.

<sub>Determinista, no probabilístico · cualquier lenguaje · sin Python · frena el commit **y** lleva el *por qué*.</sub>

<sub>Dogfooding — cada commit de este repo lo controlan las propias reglas de becwright ([`.bec/rules.yaml`](.bec/rules.yaml)) en CI.</sub>

## Antes / después

Un agente escribe `checkout.py` — una API key hardcodeada, un `eval()` sobre un
string de promo — y deja una nota para *"limpiar esto después."* Nadie lo hace.
Se publica.

Con becwright, el commit no llega a existir:

<p align="center">
  <img src="assets/becwright-demo-animated.svg" alt="becwright frenando un commit en vivo: corre git commit, dos reglas blocking se disparan con su porqué, el commit se detiene" width="640">
</p>

> **Velo vos mismo en 5 segundos** — sin configurar nada, sin git, sin tocar tu
> máquina:
> ```bash
> npx becwright demo        # sin instalar   ·   o: uvx becwright demo · pipx run becwright demo
> ```

## Empezar

Se instala una vez, se configura por proyecto. **Dos pasos y listo.**

```bash
npm install -g becwright    # binario autónomo, sin Python (o: pipx install becwright)
cd tu-proyecto
becwright init              # detecta tu lenguaje, escribe .bec/rules.yaml, instala el hook
```

Listo. A partir de ahora cada `git commit` corre los chequeos solo y frena un
commit que rompa una regla blocking. No volvés a llamar a becwright a mano.

> **¿Cuál instalación?** `npm install -g` para probarlo o para uso individual;
> `npm install --save-dev becwright` para un repo de equipo, así la versión
> queda fijada en `package.json` y el hook lo encuentra en `node_modules/.bin`.

- **¿Código existente con deuda?** `becwright init --baseline` arranca en
  `warning` las reglas que *ya* tienen violaciones (no se frena nada legítimo) y
  en `blocking` las limpias. Limpiá la deuda con el tiempo y graduá cada regla.
- **¿Ya tenés un `CLAUDE.md`?** `becwright init --from-claude-md` convierte las
  prohibiciones que reconoce (secretos, `eval`, `debugger`, `console.log`, …)
  en reglas enforzables. Lo de criterio se queda en `CLAUDE.md`. Se combina con
  `--baseline`.

<details>
<summary>Otras instalaciones: pnpm, pip, local al proyecto →</summary>

```bash
pnpm add -g becwright
pipx install becwright                # o: pip install becwright / uv tool install becwright
npm install --save-dev becwright      # local al proyecto; el hook lo encuentra en node_modules/.bin
```

Por npm/pnpm **no hace falta Python** — viene un binario autónomo por plataforma
(`linux-x64`, `linux-arm64`, `darwin-x64`, `darwin-arm64`, `win32-x64`). En
cualquier otra plataforma, usá `pipx install becwright`.
</details>

### Sentilo frenar, en 90 segundos

La forma más rápida de confiar en un guardia es verlo frenarte una vez:

```bash
cd tu-proyecto && becwright init           # reglas + hook, un comando

echo 'api_key = "AKIAIOSFODNN7EXAMPLE"' >> demo_leak.py
git add demo_leak.py && git commit -m "probar el guardia"
#   BLOCK  no-hardcoded-secrets  (blocking)
#     Why it matters: un secreto en el repo queda en la historia de git para siempre...
#   >>> Commit BLOCKED: a blocking rule was broken.

git reset demo_leak.py && rm demo_leak.py  # deshacer el experimento
git commit -m "..."                        # los commits normales pasan sin más
```

Ese ciclo — violar, ser frenado *con el porqué*, arreglar, commitear — es todo
lo que becwright hace, para siempre, automáticamente.

## Por qué un guardia, no un cartel

Un agente de IA escribe un módulo y deja una nota: *"esto nunca debe loguear
tokens de sesión."* Meses después otro agente lo regenera, nunca lee la nota, y
el token termina en los logs. Nadie se entera hasta que explota en producción.

Un cartel *pide*; un guardia *revisa*. Justo antes de guardar tu trabajo,
becwright corre tus reglas sobre el código: ✅ si todo pasa → el commit entra;
❌ si una regla se rompe → te frena, te dice qué regla es y su *por qué*, y
espera hasta que lo arregles. Una nota en `CLAUDE.md` es **probabilística** —
depende de que el agente lea y obedezca. Una regla becwright es **determinista**
— se ejecuta sobre el código real y da pasa/no-pasa, sin importar qué modelo
hizo el cambio:

| | Nota en CLAUDE.md | Regla becwright |
|---|---|---|
| Qué hace | *Pide* que se respete | *Verifica* que se respetó |
| Depende de | Que el agente la lea y obedezca | Nada — se ejecuta sobre el código |
| Resultado | Probable | Garantizado |
| Analogía | Letrero de "velocidad máxima" | Tope físico en la calle |

Las dos capas son complementarias: `CLAUDE.md` previene (que el 95% salga bien a
la primera), becwright es la red de seguridad para el 5% que se cuela.

<details>
<summary><strong>¿Primera vez con commits y hooks?</strong> — el vocabulario en una caja</summary>

Un **commit** es una foto guardada de tu código en git. Un **hook** es un
pequeño script que git ejecuta solo en un momento determinado — becwright usa el
hook *pre-commit*, que se dispara justo antes de guardar un commit. Nunca lo
corrés a mano; lo hace git.
</details>

## Concepto central: BEC (Bound Executable Constraint)

Una BEC es una constraint con tres propiedades que ningún artefacto actual
tiene juntas:

- **Bound (atada)** — la regla nace ligada a la *intención* y la decisión que
  la creó (el *por qué*), no es una regla suelta sin contexto.
- **Executable (ejecutable)** — lleva un chequeo que corre y devuelve
  pasa/no-pasa, no es prosa que alguien promete respetar.
- **Portable** — puede exportarse de un repo e importarse en otro, como un
  paquete (esto es lo que genera el efecto de red a futuro).

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

Referencia completa de campos: [`documentation/usage.es.md`](documentation/usage.es.md).

## Qué te da

- **Frena el commit, no solo avisa** — `blocking` detiene `git commit`;
  `warning` informa; `advisory` aloja reglas de criterio (p. ej. un revisor LLM)
  que reportan pero nunca bloquean, etiquetadas para que sepas qué está
  garantizado.
- **Cualquier lenguaje** — el motor matchea globs y corre un comando; el
  `forbid` sin código (regex) cubre Python, JS/TS, Go, Rust o lo que sea.
- **Cada regla lleva su porqué**, mostrado en el momento en que se dispara.
- **Reglas portables** — `export` de una BEC a un único `.bec.yaml`, `import`
  en otro repo; los checks custom viajan con su código, tras una puerta de
  confianza.
- **Catálogo offline** — `becwright search` / `add` instalan reglas listas,
  empaquetadas dentro del paquete.
- **Se adapta a tu setup** — hook de git nativo, el framework pre-commit,
  Husky, o una GitHub Action obligatoria que cierra el hueco de `--no-verify`.
- **Listo para agentes de IA** — plugin de Claude Code, `check --json` y un
  servidor MCP para que los agentes consulten y extiendan las reglas.
- **Chico y confiable** — una dependencia (`pyyaml`), sin `eval`/`exec`, con
  dogfooding sobre su propio repo en CI.

## Comandos

| Comando | Qué hace |
|---|---|
| `becwright demo` | Muestra a becwright frenando un commit malo de ejemplo (sin configurar nada, sin git) |
| `becwright init` | Genera un `.bec/rules.yaml` de arranque e instala el hook |
| `becwright init --baseline` | Igual, pero arranca en `warning` las reglas que ya tienen violaciones (adoptar sin frenar) |
| `becwright init --from-claude-md` | Deriva reglas del `CLAUDE.md` del repo (best-effort) |
| `becwright list` | Lista los checks incluidos |
| `becwright check` | Corre las reglas sobre los archivos en staging |
| `becwright check --diff <base>` | Corre las reglas solo sobre los archivos cambiados vs `<base>` (para CI/PR) |
| `becwright why [id]` | Muestra la intención + el por qué de las reglas — la memoria de decisiones del repo (`--json` para agentes) |
| `becwright validate` | Valida `.bec/rules.yaml` sin correr ningún check (para editores y CI) |
| `becwright doctor` | Diagnostica el setup: archivo de reglas, checks, hooks y hook managers |
| `becwright search [texto]` | Lista BECs listas del catálogo incluido |
| `becwright add <nombre>` | Instala una BEC del catálogo en `.bec/rules.yaml` (sin conexión) |
| `becwright install` / `uninstall` | Instala / quita los hooks nativos |
| `becwright export <id>` | Exporta una BEC a un archivo `.bec.yaml` |
| `becwright import <archivo\|URL>` | Importa una BEC de otro repo |

## ¿Ya usás pre-commit o Husky?

becwright se enchufa sin `becwright install`.

**[pre-commit](https://pre-commit.com)** — agregá a `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/DataDave-Dev/becwright
    rev: v1.0.0
    hooks:
      - id: becwright
```

**Husky** (repos JS/TS) — en `.husky/pre-commit`:

```sh
npx becwright check
```

En ambos casos becwright igual lee `.bec/rules.yaml` y frena el commit ante una
regla bloqueante rota. Corré `becwright init` una vez para generar las reglas
(salteá su instalación del hook si otra herramienta lo administra).

## Como check obligatorio de CI (GitHub Action)

El hook de commit vive en la máquina de cada persona — y `git commit
--no-verify` lo saltea. Un **check obligatorio de CI no se puede saltar**:
correr becwright en cada pull request convierte las reglas en infraestructura,
no en una sugerencia.

Agregá `.github/workflows/becwright.yml`:

```yaml
name: becwright
on: pull_request

jobs:
  becwright:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0        # historia completa para que exista el merge-base con la base del PR
      - uses: DataDave-Dev/becwright@v1.0.0
```

Por defecto chequea **solo los archivos que cambió el PR** contra la rama base —
la deuda preexistente nunca rompe el build, así se adopta limpio en un código
grande. Marcá el check como *required* en la protección de rama y las reglas
dejan de ser negociables. Los inputs (`base`, `version`, `python-version`,
`args`) están en la [página del Marketplace](https://github.com/marketplace/actions/becwright);
o salteá la action y corré `becwright check --diff origin/main` desde cualquier
step del workflow.

## Uso con agentes de IA (Claude Code)

becwright es la red determinista para lo que un agente de IA deja pasar. Hay un
plugin de Claude Code para que un agente lo instale y lo maneje por vos:

```text
/plugin marketplace add DataDave-Dev/becwright
/plugin install becwright@becwright
```

Agrega un skill `becwright` y un comando `/becwright`. Ver
[`integrations/claude-code/`](integrations/claude-code/).

Para resultados estructurados, `becwright check --json` imprime un resumen
legible por máquina, y `becwright mcp` (`pipx install "becwright[mcp]"`)
levanta un servidor MCP para que cualquier agente chequee las reglas, proponga
nuevas desde tu `CLAUDE.md` y las previsualice antes de escribirlas. Ver
[`documentation/mcp.es.md`](documentation/mcp.es.md).

La señal se mantiene magra en las dos direcciones: `becwright why --json` le
entrega a un agente las decisiones que no puede violar *antes* de escribir
código, y un commit bloqueado devuelve la única regla que se rompió, su *por
qué* y las líneas exactas — la constraint puntual, no el reglamento entero
releído en el contexto.

## Checks incluidos

Cada check es un módulo que se invoca desde el campo `check`. Funcionan
buscando texto en tus archivos con un patrón — simples y predecibles a
propósito; el verdadero valor está en atar cada regla a su *por qué*. Para
análisis más profundo, apuntá una regla a cualquier herramienta que ya uses
como su check — la regla lleva el *por qué*, la herramienta hace la detección:

```yaml
  - id: no-secrets-gitleaks
    intent: >
      Ningún secreto puede commitearse, según el ruleset completo de gitleaks.
    why_it_matters: >
      Una credencial filtrada en la historia de git queda expuesta para siempre,
      incluso después de un revert.
    paths: ["**/*"]
    check: "gitleaks detect --no-git --redact --exit-code 1"
    severity: blocking

  - id: python-passes-ruff
    intent: "El código Python debe pasar el ruleset de ruff del equipo antes del commit."
    why_it_matters: "Un lint consistente mantiene el review enfocado en la lógica, no en el estilo."
    paths: ["**/*.py"]
    check: "xargs ruff check --force-exclude"
    severity: warning
```

Más patrones listos (semgrep, eslint, rutas congeladas, límites de
arquitectura, CI): **[recetas](documentation/recipes.es.md)**.

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

¿No querés escribir reglas vos mismo? El catálogo viaja **dentro** de becwright
— un comando, sin URL, sin conexión:

```bash
becwright search                 # lista todas las BECs del catálogo
becwright add no-token-in-logs   # instalá una; becwright la muestra primero
```

La lista completa (Python, JS/TS, Go, Rust — más lenguajes
[en camino](https://github.com/DataDave-Dev/becwright/milestone/2)) vive en
[`src/becwright/becs/`](src/becwright/becs/).

## Tu primera regla propia (cualquier lenguaje)

La forma más rápida de escribir una regla —sin escribir código— es el check
`forbid`, que falla si un regex aparece en los archivos:

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
checks más finos, escribí un script en cualquier lenguaje (lee la lista de
archivos por stdin, sale con 0/1) y apuntá `check` a él — ver
[escribir checks](documentation/writing-checks.es.md).

## Compartir BECs entre repos

Una BEC es **portable**: un bundle es un único `.bec.yaml` autocontenido (la
regla + el código del check si es custom).

```bash
becwright export no-token-in-logs -o no-token-in-logs.bec.yaml   # repo de origen
becwright import no-token-in-logs.bec.yaml                       # repo destino (archivo o URL)
```

Al importar, becwright **muestra el código del check y pide confirmación** —
importar una BEC es importar código que se ejecutará en cada commit. Usá
`--yes` en entornos automatizados. Detalles:
[portabilidad](documentation/portability.es.md).

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
Husky.

## Documentación

La documentación completa vive en [`documentation/`](documentation/README.es.md):

- **Recién empezás:** [uso](documentation/usage.es.md) — instalación, los
  comandos, códigos de salida y cómo escribir una regla.
- **Reglas para copiar y pegar** (gitleaks/ruff/semgrep como checks, rutas
  congeladas, límites de arquitectura, CI): [recetas](documentation/recipes.es.md).
- **Querés agregar tu propia regla:** [escribir checks](documentation/writing-checks.es.md).
- **Compartir reglas entre proyectos:** [portabilidad](documentation/portability.es.md).
- **Curiosidad por cómo funciona adentro:** [arquitectura y flujo](documentation/architecture.es.md).
- **Conectarlo a un agente de IA:** [MCP y salida JSON](documentation/mcp.es.md).

## Estabilidad

becwright es **estable** (`1.0`): el esquema de `rules.yaml`, el formato de
bundle, los nombres de los checks, los códigos de salida de la CLI, la forma de
`check --json` y las firmas MCP solo rompen con un bump mayor, con un minor de
aviso de deprecación antes. Fijá una versión en CI y una actualización `1.x`
nunca rompe tus reglas. Contrato completo y política:
[estabilidad y versionado](documentation/stability.es.md).

## Roadmap

becwright es chico a propósito. La dirección a corto plazo vive en los
[milestones](https://github.com/DataDave-Dev/becwright/milestones):
**v1.1** amplía el catálogo a más lenguajes (Ruby, PHP, Java, C#, Shell — cada
uno un [good first issue](https://github.com/DataDave-Dev/becwright/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22)),
**v1.2** mejora la DX de escribir reglas (sintaxis corta de check, JSON Schema
para `rules.yaml`), **v1.3** hace Windows de primera clase.

Deliberadamente **fuera de alcance** para mantenerlo simple y determinista:
análisis basado en AST, suites profundas por lenguaje, y firma criptográfica de
BECs.

## FAQ

**¿Por qué no simplemente Ruff / Black / pre-commit?** Usalos — becwright no
compite con ellos. Black formatea, Ruff lintea, pre-commit *corre* herramientas.
Ninguno te da una *regla atada a su razón* que frene el commit y viaje a otro
repo. becwright es esa capa, y con gusto corre Ruff o gitleaks *como* uno de sus
checks. Otro laburo, el mismo pipeline.

**Es un proyecto joven — ¿por qué confiarle mis commits?** Porque hay muy poco
que confiar: una sola dependencia (`pyyaml`), sin `eval`/`exec`, checks que son
regex simple que leés en menos de un minuto, y licencia MIT. Y se aplica a sí
mismo — los commits del propio becwright pasan por becwright. Si se rompiera,
este repo no buildearía.

**¿Un agente no puede borrar la regla y listo?** Puede — pero borrar una regla es
una línea visible en el diff que el review marca, mientras que ignorar una nota
en `CLAUDE.md` no deja rastro. Un guardia que tenés que sacar a la vista de todos
gana contra un cartel que podés pasar de largo.

**¿No hace esto ya `pre-commit`?** Corre herramientas; no te da una regla que
lleve su *por qué* y viaje entre repos. Incluso podés correr becwright *dentro*
de pre-commit — ver más arriba.

**¿Necesito Python?** No. `npm i -g becwright` instala un binario autónomo;
`pipx install becwright` también funciona.

**¿Funciona en Windows?** En beta. La CLI y el hook corren bajo Git Bash (que
Git para Windows provee), pero Windows todavía no se ejercita en CI — los
huecos conocidos están en
[#31](https://github.com/DataDave-Dev/becwright/issues/31) y el soporte de
primera clase es el milestone v1.3. Hasta entonces, tratá Windows como
best-effort.

**¿Cómo ignoro una línea?** Poné un comentario `becwright: ignore` en ella.

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
