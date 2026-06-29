# Bitácora de decisiones

> Registro corto de decisiones importantes y su *por qué*. Lo más nuevo arriba.
> Formato: fecha · decisión · por qué · alternativas descartadas.

## 2026-06-29 · Archivar el prototipo y centrar el proyecto en la documentación

**Decisión:** mover el prototipo funcional (`.bec/` y `src/`) a `prototype/`
con `git mv` (recuperable, no borrado) y establecer la documentación
(`CLAUDE.md` + `docs/`) como el nuevo centro del proyecto.

**Por qué:** se quiere tener *siempre* el contexto del proyecto disponible
entre sesiones, sin depender de re-explicarlo cada vez. El prototipo ya quedó
verificado; conservarlo como referencia recuperable preserva la prueba
ejecutable sin que estorbe el foco documental.

**Alternativas descartadas:**
- *Borrar el prototipo de verdad* → se perdería la única prueba ejecutable del
  concepto, sin commit previo que lo recupere. Irreversible.
- *Documentar dejando el prototipo en la raíz* → mezcla el código funcional con
  el material conceptual; menos claro qué es referencia y qué es activo.

**Nota de contexto:** el prototipo se encontró descomprimido un nivel más
adentro de lo esperado (`becwright/becwright/`); se trabaja en esa raíz real.

## 2026-06-29 · Verificación del prototipo (proof of concept)

**Decisión:** confirmar que el prototipo funciona antes de cualquier cambio.

**Resultado:** con código limpio el chequeo pasa (salida 0); con `session_token`
inyectado en un `logger.info` y archivo en staging, bloquea (salida 1) y señala
la línea exacta. `src/auth.py` quedó restaurado a la versión limpia. El motor
depende de git (`git rev-parse --show-toplevel`), por eso se inicializó el repo.
