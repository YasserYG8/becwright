#!/usr/bin/env python3
"""
bec check  --  El comando principal.

Lee .bec/rules.yaml, para cada regla mira los archivos que le tocan,
corre su chequeo, y:
  - si una regla 'blocking' falla -> sale con error (frena el commit)
  - si una regla 'warning'  falla -> solo avisa (deja pasar)

Uso:
    python3 bec.py check            # revisa archivos en staging (lo que vas a commitear)
    python3 bec.py check --all      # revisa TODO el proyecto
"""
import sys
import re
import subprocess
from pathlib import Path

import yaml  # pip install pyyaml


# ---- colores para la terminal (puro cosmético) ----
RED = "\033[91m"; GREEN = "\033[92m"; YELLOW = "\033[93m"
BOLD = "\033[1m"; DIM = "\033[2m"; RESET = "\033[0m"


def load_rules(repo_root: Path):
    rules_file = repo_root / ".bec" / "rules.yaml"
    if not rules_file.exists():
        print(f"{YELLOW}No hay archivo .bec/rules.yaml. Nada que revisar.{RESET}")
        sys.exit(0)
    with open(rules_file) as f:
        return yaml.safe_load(f).get("rules", [])


def files_to_check(repo_root: Path, check_all: bool):
    """Qué archivos revisar: los que están en staging, o todos."""
    if check_all:
        cmd = ["git", "ls-files"]
    else:
        # archivos que vas a commitear (staged)
        cmd = ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"]
    out = subprocess.run(cmd, cwd=repo_root, capture_output=True, text=True)
    return [line for line in out.stdout.splitlines() if line.strip()]


def _glob_to_regex(pattern: str) -> str:
    """
    Convierte un patrón glob a regex, manejando ** correctamente.
    ** = cero o más carpetas (lo que la gente espera).
    *  = cualquier cosa menos la barra /.
    """
    i = 0
    out = []
    while i < len(pattern):
        c = pattern[i]
        if pattern[i:i+3] == "**/":
            # ** seguido de / : cero o más carpetas
            out.append("(?:.*/)?")
            i += 3
        elif pattern[i:i+2] == "**":
            out.append(".*")
            i += 2
        elif c == "*":
            out.append("[^/]*")
            i += 1
        elif c == ".":
            out.append(r"\.")
            i += 1
        else:
            out.append(re.escape(c))
            i += 1
    return "^" + "".join(out) + "$"


def matches(path: str, patterns: list) -> bool:
    for pat in patterns:
        if re.match(_glob_to_regex(pat), path):
            return True
    return False


def main():
    check_all = "--all" in sys.argv
    repo_root = Path(
        subprocess.run(["git", "rev-parse", "--show-toplevel"],
                       capture_output=True, text=True).stdout.strip()
    )

    rules = load_rules(repo_root)
    all_files = files_to_check(repo_root, check_all)

    if not all_files:
        print(f"{DIM}No hay archivos para revisar.{RESET}")
        sys.exit(0)

    print(f"{BOLD}BEC -- revisando {len(all_files)} archivo(s) contra {len(rules)} regla(s){RESET}\n")

    had_blocking_failure = False

    for rule in rules:
        # qué archivos (de los cambiados) le tocan a esta regla
        relevant = [f for f in all_files if matches(f, rule.get("paths", []))]
        if not relevant:
            continue

        # correr el chequeo de esta regla, pasándole los archivos por stdin
        result = subprocess.run(
            rule["check"], shell=True, cwd=repo_root,
            input="\n".join(relevant), capture_output=True, text=True
        )

        passed = result.returncode == 0
        severity = rule.get("severity", "blocking")

        if passed:
            print(f"  {GREEN}PASA{RESET}  {rule['id']}")
        else:
            if severity == "blocking":
                print(f"  {RED}{BOLD}FRENO{RESET}  {rule['id']}  {RED}(bloqueante){RESET}")
                had_blocking_failure = True
            else:
                print(f"  {YELLOW}AVISO{RESET}  {rule['id']}  {YELLOW}(solo advertencia){RESET}")

            # mostrar el PORQUÉ de la regla -- esto es lo que se pierde hoy
            print(f"        {DIM}Por qué importa:{RESET} {rule.get('why_it_matters','').strip()}")
            # mostrar dónde se rompió
            if result.stdout.strip():
                print(f"        {DIM}Encontrado en:{RESET}")
                for line in result.stdout.strip().splitlines():
                    print(f"        {line}")
            print()

    print()
    if had_blocking_failure:
        print(f"{RED}{BOLD}>>> Commit BLOQUEADO: se rompió al menos una regla de seguridad.{RESET}")
        print(f"{DIM}    Arregla lo de arriba, o si de verdad es intencional, edita .bec/rules.yaml{RESET}")
        sys.exit(1)
    else:
        print(f"{GREEN}{BOLD}>>> Todo bien. Commit permitido.{RESET}")
        sys.exit(0)


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] != "check":
        print("Uso: python3 bec.py check [--all]")
        sys.exit(2)
    main()
