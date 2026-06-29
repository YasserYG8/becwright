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

## Estado actual

El prototipo funcional (proof of concept) ya **fue verificado**: detecta y
frena un commit que mete un token en un log. Ahora está **archivado** en
[`prototype/`](prototype/) como referencia, y el foco del proyecto está en la
documentación de contexto.

- **Contexto del proyecto:** [`CLAUDE.md`](CLAUDE.md)
- **El concepto BEC en detalle:** [`docs/concepto-bec.md`](docs/concepto-bec.md)
- **Decisiones tomadas:** [`docs/decisiones.md`](docs/decisiones.md)
- **Estado y roadmap:** [`docs/estado-y-roadmap.md`](docs/estado-y-roadmap.md)
- **Prototipo archivado:** [`prototype/`](prototype/)

Las limitaciones conocidas y el trabajo futuro (hook de git, empaquetado como
CLI, AST, multi-lenguaje, import/export de BECs) están documentados en
[`docs/estado-y-roadmap.md`](docs/estado-y-roadmap.md).
