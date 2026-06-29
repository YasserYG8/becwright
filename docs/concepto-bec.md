# Concepto: BEC (Bound Executable Constraint)

## El problema que resuelve

Un agente de IA escribe código y deja una nota: *"esto nunca debe loguear
tokens de sesión"*. Esa nota es **texto**. Meses después, otro agente regenera
el módulo, no la lee, y mete el token en los logs. Nadie se entera hasta que
explota en producción.

Las notas (`CLAUDE.md`, `.cursorrules`, comentarios) son **probabilísticas**:
dependen de que el agente lea, entienda y obedezca. becwright es
**determinista**: la regla se ejecuta sobre el código real y da pasa/no-pasa,
sin importar qué agente o modelo hizo el cambio.

| | Nota en CLAUDE.md | Regla becwright |
|---|---|---|
| Qué hace | *Pide* que se respete | *Verifica* que se respetó |
| Depende de | Que el agente la lea y obedezca | Nada — se ejecuta sobre el código |
| Resultado | Probable | Garantizado |
| Analogía | Letrero de "velocidad máxima" | Tope físico en la calle |

## Las tres propiedades de una BEC

Una BEC es una constraint con tres propiedades que ningún artefacto actual
tiene **juntas**:

### Bound (atada)
La regla nace ligada a la *intención* y la decisión que la creó (el *por qué*),
no es una regla suelta sin contexto. En el formato actual esto vive en los
campos `intent`, `why_it_matters` y `rejected_alternatives` de cada regla.

### Executable (ejecutable)
Lleva un chequeo que corre y devuelve pasa/no-pasa (código de salida 0 o 1),
no es prosa que alguien promete respetar. En el formato actual es el campo
`check` que apunta a un script.

### Portable
Puede exportarse de un repo e importarse en otro, como un paquete. Esto es lo
que genera el efecto de red a futuro (aún no implementado — ver
[estado-y-roadmap.md](estado-y-roadmap.md)).

## Cómo se materializa hoy (en el prototipo)

Una regla en `prototype/.bec/rules.yaml` se ve así:

```yaml
- id: no-token-in-logs
  intent: >
    Los tokens de sesión y credenciales nunca deben llegar a ningún log.
  why_it_matters: >
    Si un token aparece en los logs, cualquiera con acceso a los logs
    puede robar la sesión de un usuario.
  rejected_alternatives:
    - "Redactar el token al escribir el log -> muy fácil de saltarse"
  paths:
    - "src/**/*.py"
  check: "python3 .bec/checks/no_token_in_logs.py"
  severity: blocking   # blocking = frena el commit | warning = solo avisa
```

El motor (`becwright.py`) lee las reglas, filtra los archivos que le tocan a
cada una por sus `paths`, corre el `check`, y según `severity` frena (salida 1)
o solo avisa.
