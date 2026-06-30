# Servidor MCP y salida JSON

Para agentes de IA, becwright expone sus resultados en formato legible por
máquina de dos maneras.

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
