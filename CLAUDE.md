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
├── docs/
│   ├── concepto-bec.md       # la idea de BEC en detalle
│   ├── decisiones.md         # bitácora de decisiones (ADR-lite)
│   └── estado-y-roadmap.md   # estado actual + plan + trabajo futuro
└── prototype/                # PROTOTIPO ARCHIVADO (referencia, no se construye encima sin avisar)
    ├── .bec/
    │   ├── rules.yaml         # formato de reglas (id, intent, why, paths, check, severity)
    │   ├── becwright.py       # motor: lee reglas, corre chequeos, frena o deja pasar
    │   └── checks/
    │       └── no_token_in_logs.py
    └── src/auth.py            # código de ejemplo
```

## Estado actual

Prototipo funcional **verificado** (detecta y frena un commit con un token en
un log) y luego **archivado** en `prototype/`. El foco actual del proyecto es
la **documentación de contexto**, no añadir features. Ver
[`docs/estado-y-roadmap.md`](docs/estado-y-roadmap.md).

## Alcance y no-objetivos

**Dentro:** documentar concepto, decisiones y estado; conservar el prototipo
como referencia recuperable.

**Fuera (trabajo futuro, no tocar sin pedirlo):** análisis AST, soporte
multi-lenguaje, importar/exportar BECs entre repos, firma de verificaciones,
"mejorar" el regex de los checks.

## Convenciones

- Código y comentarios **en español**.
- Python 3.12 objetivo (el entorno actual tiene 3.14; anotarlo, no forzar).
- Dependencias mínimas: solo `pyyaml`. No agregar otras sin preguntar.
- No cambiar el formato de `rules.yaml` ni la lógica de `checks/` sin preguntar.
- Simplicidad y claridad por encima de cantidad de features (esto aspira a ser
  un estándar).
