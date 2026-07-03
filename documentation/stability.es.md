# Estabilidad y versionado

becwright es **estable** (`1.0`). Se usa a sí mismo (sus propios commits pasan
por becwright), la suite de tests está en verde y está publicado en npm y PyPI.
Bajo [SemVer](https://semver.org) el contrato público de abajo solo rompe con un
bump mayor, así que actualizar dentro de `1.x` siempre es seguro. Si dependés de
él en CI, fijá una versión igualmente (`becwright==1.0.0`, o
`npm i -g becwright@1.0.0`).

## El contrato público

Estable desde `1.0.0`, cambia solo con un bump mayor:

- El esquema de `.bec/rules.yaml` (los campos de una regla y su significado).
- El formato de bundle `.bec.yaml` que `export` / `import` mueven entre repos.
- Los nombres de los checks incluidos y sus flags.
- Los comandos de la CLI y sus códigos de salida.
- La forma de la salida `check --json`.
- Los nombres y firmas de las herramientas MCP.

Todo lo demás (el texto de los mensajes, el contenido del catálogo, los módulos
internos) puede cambiar en cualquier momento.

## Soporte de plataformas

Linux y macOS tienen soporte completo y se ejercitan en CI. **Windows está en
beta**: la CLI y el hook corren bajo Git Bash (que Git para Windows provee),
pero Windows todavía no es parte de la matriz de CI y hay huecos conocidos
([#31](https://github.com/DataDave-Dev/becwright/issues/31)). El soporte de
primera clase es el milestone v1.3.

Antes de `1.0.0` la base fue: los dos formatos en disco versionados para que un
archivo más nuevo falle fuerte (`schema_version` / `becwright_bec`), el conjunto
de campos de `rules.yaml` congelado y fijado por tests, los códigos de salida y
`check --json` documentados y fijados por tests, y validación contra repos reales.

## Política de deprecación

Desde `1.0.0`, nada del contrato público se quita sin un major de aviso de por
medio. Cuando algo tiene que cambiar:

1. Se marca como **deprecado** en una release menor — sigue funcionando y emite
   un warning.
2. Sigue funcionando (con el warning) durante el resto de esa serie mayor.
3. Se quita solo en la siguiente release **mayor**.

Así, lo que es válido en `1.0` sigue válido en cada `1.x`: un cambio que rompe
compatibilidad siempre cruza una versión mayor, con al menos un minor de aviso
antes. Fijá una versión en CI y una actualización dentro de `1.x` nunca romperá
tus reglas, bundles ni scripts de check sin avisar.
