> [English](writing-checks.md) · **Español**

# Escribir checks

Un check es la parte **ejecutable** de una BEC — el programita que de verdad
inspecciona tus archivos y dice pasa o falla.

**La mayoría de las veces no escribís código.** Si tu regla es "este texto no
debe aparecer" (una palabra prohibida, un `debugger` olvidado, una función
vetada), usá el check incluido `forbid` y listo — saltá a
[El camino más rápido](#el-camino-más-rápido-forbid). Escribir tu propio check
(el resto de esta página) es solo para casos que `forbid` no puede expresar.

## El contrato

- **Entrada:** la lista de archivos a revisar, una ruta por línea, por **stdin**.
- **Salida:** imprimir las violaciones por stdout (becwright las muestra bajo "Found in:").
- **Código de salida:** `0` = pasa, no-cero = falla.
- **Directorio de trabajo:** la raíz del repo, así las rutas de stdin resuelven directo.

> **Glosario rápido:** *stdin*/*stdout* son los canales de entrada/salida estándar
> por los que un programa lee y escribe. El *código de salida* es el número que
> devuelve un programa al terminar — `0` significa "todo bien", cualquier otro
> significa "encontré un problema". Esa es toda la interfaz: entran archivos,
> salen los problemas, y sale con `0` o no-cero.

## El camino más rápido: `forbid`

Para "este regex no debe aparecer" no hace falta escribir código — usá el check
genérico incluido:

```yaml
  - id: no-debugger-js
    paths: ["**/*.js", "**/*.ts"]
    check: "becwright run forbid --pattern '\\bdebugger\\b'"
    severity: blocking
```

`forbid` acepta `--pattern REGEX`, `--ignore-case` y `--message TEXTO`.

## Checks incluidos

| Check | Detecta | Lenguaje |
|---|---|---|
| `forbid` | cualquier regex que le pases (`--pattern`) | cualquiera |
| `no_token_in_logs` | tokens/credenciales en llamadas a logs | Python |
| `hardcoded_secrets` | claves AWS, claves privadas, `password = "..."` | cualquiera |
| `debug_remnants` | `breakpoint()`, `pdb.set_trace()`, `import pdb` | Python |
| `dangerous_eval` | `eval()` / `exec()` | cualquiera |
| `wildcard_imports` | `from x import *` | Python |
| `redundant_comments` | comentarios que repiten lo obvio del código (heurístico) | Python |

## Un check propio (cualquier lenguaje)

Cualquier ejecutable que cumpla el contrato sirve. Ejemplo en Node, marcando `TODO`:

```js
#!/usr/bin/env node
const fs = require('fs');
const files = fs.readFileSync(0, 'utf8').split('\n').filter(Boolean);
let bad = false;
for (const f of files) {
  fs.readFileSync(f, 'utf8').split('\n').forEach((line, i) => {
    if (line.includes('TODO')) { console.log(`  ${f}:${i + 1}`); bad = true; }
  });
}
process.exit(bad ? 1 : 0);
```

```yaml
  - id: no-todo
    paths: ["**/*.js"]
    check: "node .bec/checks/no_todo.js"
    severity: warning
```

Un check incluido de Python sigue el mismo esqueleto — ver
`src/becwright/checks/dangerous_eval.py`.

## Ignorar una línea

Un falso positivo —un patrón que aparece como texto, no como una violación
real— se puede suprimir con un marcador `becwright: ignore` en un comentario de
esa línea, en cualquier lenguaje:

```py
result = eval(expr)  # becwright: ignore
```

```js
console.log(x);  // becwright: ignore
```

El marcador exime a la línea de todos los checks incluidos.

## La trampa de la auto-referencia

Un check de texto/regex no puede correr sobre su propia fuente: un check que
prohíbe el string `eval(` va a matchear la mismísima línea de su propio código
que define ese patrón. Cuando el check de una regla escanearía su propio archivo,
acotá `paths` para excluirlo — p.ej. usá `src/becwright/*.py` (solo el nivel
superior) en vez de `src/becwright/**/*.py` para saltarte el directorio `checks/`.
Para líneas puntuales, el marcador `becwright: ignore` de arriba es más simple.
