# Servidor MCP y salida JSON

**¿Para quién es esta página?** Para quien quiera conectar becwright a una
herramienta de IA o a un script. Si solo querés que becwright cuide tus commits,
no necesitás nada de esto — la instalación normal ya lo hace. Seguí leyendo solo
si querés que un agente de IA (u otro programa) *lea* los resultados de becwright.

becwright expone sus resultados en formato legible por máquina de dos maneras:
una salida JSON para scripts y un servidor MCP para agentes de IA. (MCP — Model
Context Protocol — es un enchufe estándar para darles habilidades extra a las
herramientas de IA.)

## `becwright check --json`

Igual que `becwright check`, pero imprime un resumen JSON en vez de texto con
color, consumible sin parsear. El código de salida no cambia (1 si falló una
regla blocking, si no 0).

```json
{
  "rule_count": 3,
  "checked_files": 1,
  "blocked": true,
  "results": [
    {
      "id": "no-debugger-js",
      "severity": "blocking",
      "passed": false,
      "intent": "Do not leave 'debugger;' in JavaScript/TypeScript code.",
      "why_it_matters": "A forgotten 'debugger' halts execution ...",
      "output": "app.js:1\n      > function f(){ debugger; }"
    }
  ]
}
```

No necesita dependencias extra y funciona también desde el binario autónomo.

## Servidor MCP

`becwright mcp` levanta un servidor [Model Context
Protocol](https://modelcontextprotocol.io) sobre stdio, así cualquier agente
compatible con MCP (Claude, Cursor, Windsurf, …) obtiene becwright como tools
estructuradas.

Requiere el extra opcional `mcp`:

```bash
pipx install "becwright[mcp]"     # o: pip install "becwright[mcp]"
```

### Tools

| Tool | Argumentos | Devuelve |
|---|---|---|
| `check` | `all_files` (bool), `path` (dir del repo, opcional) | el mismo resumen que `check --json` |
| `list_checks` | — | los checks built-in como `{name, description}` |
| `preview_rule` | `check`, `paths`, `exclude` (opcional), `all_files`, `path` | `{matched_files, passed, output, note}` — un dry-run sin escribir la regla |
| `propose_rules_from_claude_md` | `path` (dir del repo, opcional) | `{rules, unmapped_hint}` — las reglas que becwright deriva del CLAUDE.md del repo |
| `add_rule` | `id`, `check`, `paths`, `intent`, `why_it_matters`, `severity`, `exclude`, `confirm`, `path` | escribe una regla en `.bec/rules.yaml` — preview salvo `confirm=true` |

**`propose_rules_from_claude_md`** devuelve las reglas que becwright puede derivar
determinísticamente de la prosa (cada una con la frase que la disparó) — el *punto
de partida* del agente. **`preview_rule`** deja que el agente *valide* una regla
antes de escribirla: dado un `check` candidato y sus `paths`, corre el check contra
el repo e informa cuántos archivos seleccionan los globs, si la regla pasaría y qué
marca — detectando una regla que no matchea nada o que nombra un check inexistente.

**`add_rule`** persiste una regla validada. **Nunca escribe a ciegas**: con
`confirm=false` (el default) devuelve un preview de lo que escribiría; solo
`confirm=true` la escribe. Por seguridad acepta **solo checks built-in**
(`becwright run <name>`) — una regla con un comando shell arbitrario corre en cada
commit, así que esas van por el `becwright import` del CLI, que le muestra el
código a un humano.

Juntas definen el reparto: becwright garantiza la *ejecución*; el agente hace la
*traducción*, arrancando de `propose_rules_from_claude_md`, usando `list_checks`
como vocabulario, extendiendo con reglas para lo que el extractor no captó, usando
`preview_rule` para chequear cada una, y `add_rule` (confirmado) para persistir.
Lo de criterio se queda en `CLAUDE.md`.

### Configuración del cliente

Apuntá la config MCP de tu agente al comando:

```json
{
  "mcpServers": {
    "becwright": {
      "command": "becwright",
      "args": ["mcp"]
    }
  }
}
```

El servidor MCP viaja solo con el paquete de Python (no está en el binario de
npm). Para uso de CLI/hook sin Python, seguí usando la instalación por npm.
