#!/usr/bin/env python3
"""
Chequeo: ningún token o credencial debe ir a un log.

Recibe por stdin la lista de archivos a revisar (uno por línea).
Devuelve:
  - código de salida 0  -> todo bien (pasa)
  - código de salida 1  -> encontró una violación (no pasa)
Imprime las violaciones encontradas para que el humano (o el agente) las vea.

Esta es una versión simple basada en patrones de texto. En la vida real
se usaría análisis del árbol de sintaxis (AST) para ser más preciso,
pero esto ya demuestra el principio: el chequeo MIRA EL CÓDIGO REAL,
no confía en que nadie haya leído una nota.
"""
import sys
import re

# Palabras que indican que algo es un token / credencial sensible
SENSITIVE = r"(token|password|passwd|secret|api[_-]?key|credential|session[_-]?id)"

# Llamadas que mandan algo a un log
LOG_CALL = r"(log\.|logger\.|logging\.|print\s*\()"

# Patrón combinado: una llamada de log que en la misma línea menciona algo sensible
PATTERN = re.compile(LOG_CALL + r"[^\n]*" + SENSITIVE, re.IGNORECASE)

violations = []

for path in sys.stdin.read().splitlines():
    path = path.strip()
    if not path:
        continue
    try:
        with open(path, "r", encoding="utf-8") as f:
            for lineno, line in enumerate(f, start=1):
                if PATTERN.search(line):
                    violations.append((path, lineno, line.strip()))
    except (FileNotFoundError, IsADirectoryError):
        continue

if violations:
    for path, lineno, line in violations:
        print(f"  {path}:{lineno}")
        print(f"      > {line}")
    sys.exit(1)   # NO PASA -> esto es lo que frena el commit

sys.exit(0)       # pasa
