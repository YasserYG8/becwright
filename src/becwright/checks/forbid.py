from __future__ import annotations

import argparse
import re
import sys


def find_violations(paths: list[str], pattern: str, flags: int = 0) -> list[tuple[str, int, str]]:
    rx = re.compile(pattern, flags)
    violations: list[tuple[str, int, str]] = []
    for path in paths:
        path = path.strip()
        if not path:
            continue
        try:
            with open(path, encoding="utf-8") as f:
                for lineno, line in enumerate(f, start=1):
                    if rx.search(line):
                        violations.append((path, lineno, line.strip()))
        except (FileNotFoundError, IsADirectoryError, UnicodeDecodeError):
            continue
    return violations


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="becwright.checks.forbid",
        description="Falla si un patrón regex aparece en los archivos.",
    )
    parser.add_argument("--pattern", required=True, help="regex prohibido")
    parser.add_argument("--ignore-case", action="store_true", help="ignora mayúsculas/minúsculas")
    parser.add_argument("--message", default="", help="nota a mostrar si hay coincidencias")
    args = parser.parse_args(argv)

    try:
        violations = find_violations(
            sys.stdin.read().splitlines(),
            args.pattern,
            re.IGNORECASE if args.ignore_case else 0,
        )
    except re.error as e:
        print(f"patrón inválido: {e}", file=sys.stderr)
        return 2

    if args.message and violations:
        print(f"  {args.message}")
    for path, lineno, line in violations:
        print(f"  {path}:{lineno}")
        print(f"      > {line}")
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
