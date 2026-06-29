# Estado y roadmap

## Estado actual (2026-06-29)

- **Prototipo:** funcional y verificado, ahora **archivado** en `prototype/`.
  Demuestra el concepto end-to-end: detecta un token en un log y frena el
  commit con código de salida 1.
- **Foco activo:** documentación de contexto persistente (este conjunto de
  docs + `CLAUDE.md`). No se están añadiendo features.
- **Repo git:** inicializado. Aún **sin commits**.

### Nota sobre correr el prototipo archivado

El motor (`prototype/.bec/becwright.py`) calcula la raíz con
`git rev-parse --show-toplevel` y espera rutas relativas como `.bec/...` y
`src/...` desde esa raíz. Tras el archivado, la raíz git es `becwright/`, así
que esas rutas ya no resuelven directamente. El prototipo queda como
**referencia ilustrativa**; volver a hacerlo ejecutable como herramienta real
es parte del roadmap (empaquetado / instalación).

## Plan original de producto (en pausa, retomable)

Estos eran los pasos para convertir el prototipo en herramienta instalable.
Quedan documentados para retomarlos cuando se decida:

1. **Verificar el prototipo** — ✅ hecho.
2. **Hook de git** — instalar un `pre-commit` que corra el chequeo solo, más
   `becwright install` / `becwright uninstall`. *(Pendiente.)*
3. **Empaquetar como CLI** — `pyproject.toml` con entry point para `pip install
   -e .` y comando `becwright` global, envolviendo la lógica existente sin
   cambiarla. *(Pendiente.)*

## Trabajo futuro (fuera de alcance actual)

Limitaciones conocidas del prototipo, a abordar solo cuando se pida:

- Los checks usan patrones de texto (regex), no análisis del árbol de sintaxis
  (AST). Da falsos positivos/negativos en casos límite.
- Solo Python. El concepto es agnóstico al lenguaje; el prototipo no.
- No se registra ni firma el bloque de "verificación" (quién corrió el chequeo,
  cuándo).
- No hay mecanismo de importar/exportar BECs entre repos (la propiedad
  *portable* del concepto aún no está implementada).
