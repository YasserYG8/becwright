# becwright — contexto del proyecto

> Este archivo se carga en cada sesión. Es la fuente de verdad para entender
> de qué va el proyecto, qué decisiones se tomaron y qué está dentro/fuera de
> alcance. Mantenlo corto y actualizado.

## Qué es

becwright hace cumplir **restricciones (constraints) sobre el código de forma
determinista**, frenando commits que las violan. La diferencia con
`CLAUDE.md` / `.cursorrules`: esos *piden* a un agente que respete reglas
(probabilístico, el agente puede ignorarlas); becwright **verifica el
resultado** ejecutando un chequeo real sobre el código (garantizado, no
depende del agente).

Las dos capas son complementarias: las notas previenen, becwright es la red
de seguridad determinista para lo que se cuela.

## Concepto central: BEC (Bound Executable Constraint)

Una constraint con tres propiedades juntas:

- **Bound (atada)** — nace ligada a la *intención* y el *por qué* que la creó.
- **Executable (ejecutable)** — lleva un chequeo que corre y da pasa/no-pasa.
- **Portable** — puede exportarse de un repo e importarse en otro.

Detalle completo en [`docs/concepto-bec.md`](docs/concepto-bec.md).

## Estructura del repo

```
becwright/
├── CLAUDE.md                 # este archivo: contexto persistente
├── README.md                 # documento conceptual público
├── pyproject.toml            # empaquetado + comando `becwright` (setuptools)
├── src/becwright/            # MOTOR empaquetado (instalable, no se copia a cada repo)
│   ├── cli.py                # argparse: check / install / uninstall
│   ├── engine.py             # matching de paths + corre checks + decide pasa/no-pasa
│   ├── rules.py              # modelo Regla + carga de .bec/rules.yaml
│   ├── git.py                # raíz del repo, archivos staged, hook nativo
│   └── checks/               # checks incluidos (no_token_in_logs, ...)
├── tests/                    # pytest
├── docs/                     # concepto, decisiones, estado-y-roadmap
└── prototype/                # PROTOTIPO ARCHIVADO (referencia, no se construye encima sin avisar)
```

El repo que *adopta* becwright solo aporta su propio `.bec/rules.yaml`; el motor
viene del paquete instalado.

## Estado actual

Construyendo el **MVP instalable (A + B)**: motor empaquetado en
`src/becwright/` con comando `becwright` (check / install / uninstall) y hook de
git nativo. Verificado end-to-end (el hook frena un commit con token). El
prototipo original queda **archivado** en `prototype/` como referencia. Ver
[`docs/estado-y-roadmap.md`](docs/estado-y-roadmap.md).

## Alcance y no-objetivos

**Dentro:** el MVP A + B (CLI instalable + hook nativo); mantener documentación
y prototipo de referencia al día.

**Fuera (trabajo futuro, no tocar sin pedirlo):** portabilidad / importar-exportar
BECs entre repos (C), análisis AST, soporte multi-lenguaje, firma de
verificaciones, "mejorar" el regex de los checks.

## Convenciones

- Código y comentarios **en ingles**.
- Comentarios reservados para código complejo: si el código se entiende solo,
  no se comenta. Nada de comentarios que repiten lo obvio.
- Python 3.12 objetivo (el entorno actual tiene 3.14; anotarlo, no forzar).
- Dependencias mínimas: solo `pyyaml`. No agregar otras sin preguntar.
- No cambiar el formato de `rules.yaml` ni la lógica de `checks/` sin preguntar.
- Simplicidad y claridad por encima de cantidad de features (esto aspira a ser
  un estándar).
- Commits **atómicos**: cada commit es un solo cambio lógico y completo (deja
  los tests en verde). No mezclar cambios sin relación en un mismo commit.
