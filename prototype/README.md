# Prototipo archivado

Esta carpeta contiene el **prototipo funcional original** de becwright,
conservado como **referencia recuperable**. No se construye encima de él sin
avisar (ver [`../CLAUDE.md`](../CLAUDE.md)).

- `.bec/rules.yaml` — formato de reglas BEC.
- `.bec/becwright.py` — motor que lee reglas, corre chequeos y frena/deja pasar.
- `.bec/checks/no_token_in_logs.py` — chequeo de ejemplo (token en logs).
- `src/auth.py` — código de ejemplo para probar.

**Nota:** el motor espera rutas relativas (`.bec/...`, `src/...`) desde la raíz
git del repo. Tras archivarlo bajo `prototype/`, esas rutas ya no resuelven
desde la raíz `becwright/`. Queda como referencia ilustrativa; volver a hacerlo
ejecutable es parte del roadmap en
[`../docs/estado-y-roadmap.md`](../docs/estado-y-roadmap.md).
