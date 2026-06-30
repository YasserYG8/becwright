# becwright

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
# 1. Instalar el motor (una vez, global)
pipx install git+<URL-del-repo>     # o, desde una copia local: pipx install .

# 2. En el repo donde querés las reglas, instalar el hook de git
becwright install                   # escribe .git/hooks/pre-commit

# 3. Escribir tus reglas en .bec/rules.yaml (ver ejemplos abajo)
# 4. Listo: cada commit corre los chequeos; si una regla blocking falla, frena.
```

Comandos disponibles:

| Comando | Qué hace |
|---|---|
| `becwright check` | Corre las reglas sobre los archivos en staging |
| `becwright install` | Instala el hook `pre-commit` nativo |
| `becwright uninstall` | Quita el hook |

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
    check: "python3 -m becwright.checks.no_token_in_logs"
    severity: blocking   # blocking = frena el commit | warning = solo avisa
```

## Checks incluidos

becwright trae chequeos listos para usar. Cada uno es un módulo que se invoca
desde el campo `check`. Son **basados en texto/regex** (no análisis AST), así
que son conservadores y pueden tener casos límite; el valor está en atar cada
regla a su *por qué*.

| Check | Qué detecta | Severidad sugerida |
|---|---|---|
| `no_token_in_logs` | Tokens/credenciales en llamadas a logs | `blocking` |
| `hardcoded_secrets` | Claves AWS, claves privadas, `password = "..."` literales | `blocking` |
| `debug_remnants` | `breakpoint()`, `pdb.set_trace()`, `import pdb` olvidados | `blocking` |
| `dangerous_eval` | Llamadas a `eval()` / `exec()` | `blocking` |
| `wildcard_imports` | `from x import *` | `warning` |

Reglas de ejemplo para copiar a tu `.bec/rules.yaml`:

```yaml
rules:
  - id: no-hardcoded-secrets
    intent: >
      Ningún secreto (clave, token, contraseña) debe quedar escrito en el código.
    why_it_matters: >
      Un secreto en el repo queda en el historial de git para siempre y es
      visible para cualquiera con acceso al código.
    paths: ["src/**/*.py"]
    check: "python3 -m becwright.checks.hardcoded_secrets"
    severity: blocking

  - id: no-debug-remnants
    intent: >
      No se commitea código de depuración (breakpoints, pdb).
    why_it_matters: >
      Un breakpoint olvidado cuelga el proceso en producción o en CI.
    paths: ["src/**/*.py"]
    check: "python3 -m becwright.checks.debug_remnants"
    severity: blocking

  - id: no-dangerous-eval
    intent: >
      No usar eval()/exec(), que ejecutan código arbitrario.
    why_it_matters: >
      eval/exec sobre entrada no confiable es ejecución remota de código.
    paths: ["src/**/*.py"]
    check: "python3 -m becwright.checks.dangerous_eval"
    severity: blocking

  - id: no-wildcard-imports
    intent: >
      Evitar 'from x import *', que ensucia el namespace.
    why_it_matters: >
      Los imports wildcard ocultan de dónde viene cada nombre y rompen el
      análisis estático.
    paths: ["src/**/*.py"]
    check: "python3 -m becwright.checks.wildcard_imports"
    severity: warning
```

## Estado actual

El **MVP instalable** está construido y verificado end-to-end: motor empaquetado
(`src/becwright/`), CLI (`check` / `install` / `uninstall`), hook de git nativo
que frena un commit con un token en un log, cinco checks incluidos y tests en
verde. El prototipo original queda **archivado** en `prototype/` como referencia.

- **Plan y norte del proyecto:** [`docs/plan.md`](docs/plan.md)
- **Contexto del proyecto:** [`CLAUDE.md`](CLAUDE.md)
- **El concepto BEC en detalle:** [`docs/concepto-bec.md`](docs/concepto-bec.md)
- **Decisiones tomadas:** [`docs/decisiones.md`](docs/decisiones.md)
- **Estado y roadmap:** [`docs/estado-y-roadmap.md`](docs/estado-y-roadmap.md)

El trabajo futuro (portabilidad / import-export de BECs entre repos, AST,
multi-lenguaje) está documentado en [`docs/plan.md`](docs/plan.md).
