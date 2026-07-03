> [English](recipes.md) · **Español**

# Recetas

Reglas y configs para copiar y pegar, para los casos más comunes. Cada regla
va bajo `rules:` en tu `.bec/rules.yaml`; cada archivo de config está completo.

**Cómo recibe su entrada un check:** becwright le pasa la lista de archivos
matcheados por **stdin**, una ruta por línea, con la raíz del repo como
directorio de trabajo. Así, `xargs <herramienta>` sirve de puente a cualquier
herramienta que reciba archivos como argumentos, y las que escanean el
directorio funcionan directo.

> **Una salvedad para herramientas externas:** en un commit normal, los checks
> corren dentro de un snapshot temporal del contenido *staged* (así juzgan
> exactamente lo que el commit va a registrar). Ese snapshot no es un
> repositorio git — usá el modo de escaneo de directorio o de archivos de la
> herramienta (`gitleaks detect --no-git`, `ruff check`, `semgrep scan`), no un
> modo que necesite `.git` (`gitleaks protect`).

## Bloquear secretos (incluido, sin instalar nada)

```yaml
  - id: no-hardcoded-secrets
    intent: >
      Ningún secreto (clave, token, password) puede estar hardcodeado en el
      código.
    why_it_matters: >
      Un secreto en el repo queda en la historia de git para siempre y es
      visible para cualquiera con acceso al código.
    paths: ["**/*"]
    check: "becwright run hardcoded_secrets"
    severity: blocking
```

## Correr gitleaks como check

El check incluido es una red rápida de regex. Si ya confiás en
[gitleaks](https://github.com/gitleaks/gitleaks), apuntá la regla a él — la
regla conserva el *por qué*, gitleaks hace la detección profunda:

```yaml
  - id: no-secrets-gitleaks
    intent: >
      Ningún secreto puede commitearse, según el ruleset completo de gitleaks.
    why_it_matters: >
      Una credencial filtrada en la historia de git queda expuesta para
      siempre, incluso después de un revert.
    paths: ["**/*"]
    check: "gitleaks detect --no-git --redact --exit-code 1"
    severity: blocking
```

## Correr ruff como check

```yaml
  - id: python-passes-ruff
    intent: >
      El código Python debe pasar el ruleset de ruff del equipo antes de
      commitearse.
    why_it_matters: >
      Un lint consistente mantiene los diffs limpios y el review enfocado en la
      lógica, no en el estilo.
    paths: ["**/*.py"]
    check: "xargs ruff check --force-exclude"
    severity: warning
```

## Correr semgrep como check

```yaml
  - id: semgrep-ci-rules
    intent: >
      Los archivos cambiados deben pasar la política semgrep del equipo.
    why_it_matters: >
      Las reglas AST de semgrep atrapan patrones de inyección y de lógica que
      un regex no puede.
    paths: ["**/*.py", "**/*.js", "**/*.ts"]
    check: "xargs semgrep scan --error --quiet --config p/ci"
    severity: blocking
```

La misma forma sirve para cualquier herramienta con código de salida: eslint
(`xargs eslint --no-warn-ignored`), shellcheck (`xargs shellcheck`), hadolint,
tsc, mypy…

## Sin `console.log` / `debugger` (JS/TS)

```yaml
  - id: no-debugger-js
    intent: "No dejar 'debugger;' en el código JavaScript/TypeScript."
    why_it_matters: "Un 'debugger' olvidado detiene la ejecución en producción."
    paths: ["**/*.js", "**/*.ts"]
    check: "becwright run forbid --pattern '\\bdebugger\\b'"
    severity: blocking

  - id: no-console-log-js
    intent: "Evitar 'console.log(...)' fuera del módulo de logging."
    why_it_matters: "Los console.log de debug ensucian la salida en producción."
    paths: ["**/*.js", "**/*.ts"]
    exclude: ["src/lib/logger.ts"]
    check: "becwright run forbid --pattern 'console\\.log\\s*\\('"
    severity: warning
```

## Congelar rutas críticas (p. ej. migraciones aplicadas)

`filename --forbid '.*'` falla ante *cualquier* archivo staged que matchee los
`paths` de la regla — o sea, la regla se lee como "cambiar estos archivos frena
el commit". Ideal para archivos que un agente de IA no debe tocar jamás:

```yaml
  - id: frozen-migrations
    intent: >
      Las migraciones de base de datos ya aplicadas son inmutables; escribí una
      migración nueva en su lugar.
    why_it_matters: >
      Editar una migración aplicada desincroniza todas las bases que ya la
      corrieron.
    paths: ["migrations/**"]
    check: "becwright run filename --forbid '.*'"
    severity: blocking
```

## Forzar un límite de arquitectura

```yaml
  - id: domain-does-not-import-infra
    intent: >
      La capa de dominio no debe importar de la capa de infraestructura.
    why_it_matters: >
      Un dominio que llega a infra ya no puede testearse ni reutilizarse
      aislado; la dependencia debe apuntar hacia adentro.
    paths: ["src/domain/**/*.py"]
    check: "becwright run forbid --pattern 'from app\\.infra|import app\\.infra'"
    severity: blocking
```

## Mensajes de commit convencionales

```yaml
  - id: conventional-commits
    target: commit-msg
    intent: "Los mensajes de commit siguen el formato Conventional Commits."
    why_it_matters: "Un formato consistente mantiene la historia legible y habilita changelogs automáticos."
    check: |-
      becwright run require --pattern '^(build|chore|ci|docs|feat|fix|perf|refactor|revert|style|test)(\(.+\))?!?: '
    severity: blocking
```

## CI: GitHub Actions

`.github/workflows/becwright.yml` — chequea solo los archivos que cambió el
PR, así la deuda preexistente nunca rompe el build:

```yaml
name: becwright
on: pull_request

jobs:
  becwright:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: DataDave-Dev/becwright@v1.0.0
```

Marcalo como check *required* en la protección de rama y las reglas ya no se
pueden saltar con `git commit --no-verify`.

## Framework pre-commit

`.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/DataDave-Dev/becwright
    rev: v1.0.0
    hooks:
      - id: becwright
```

## Husky

`.husky/pre-commit`:

```sh
npx becwright check
```

## Scripts de package.json

```json
{
  "scripts": {
    "bec": "becwright check",
    "bec:all": "becwright check --all"
  },
  "devDependencies": {
    "becwright": "^1.0.0"
  }
}
```

## Claude Code y MCP

```text
/plugin marketplace add DataDave-Dev/becwright
/plugin install becwright@becwright
```

Para cualquier agente con MCP, `becwright mcp` (se instala con
`pipx install "becwright[mcp]"`) expone las reglas como herramientas. Detalles:
[mcp.es.md](mcp.es.md).
