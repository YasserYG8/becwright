from __future__ import annotations

import re
import sys

_AWS_KEY = r"AKIA[0-9A-Z]{16}"
_PRIVATE_KEY = r"-----BEGIN [A-Z ]*PRIVATE KEY-----"
_ASSIGNMENT = (
    r"(password|passwd|secret|api[_-]?key|token|access[_-]?key)"
    r"\s*[:=]\s*['\"][^'\"]{6,}['\"]"
)
PATTERN = re.compile("|".join((_AWS_KEY, _PRIVATE_KEY, _ASSIGNMENT)), re.IGNORECASE)

# Lines whose value reads as a placeholder, not a real secret.
_PLACEHOLDER = re.compile(
    r"os\.environ|getenv|<[^>]*>|\*{3,}|changeme|example|your[_-]|placeholder|dummy|xxxx",
    re.IGNORECASE,
)


def find_violations(paths: list[str]) -> list[tuple[str, int, str]]:
    violations: list[tuple[str, int, str]] = []
    for path in paths:
        path = path.strip()
        if not path:
            continue
        try:
            with open(path, encoding="utf-8") as f:
                for lineno, line in enumerate(f, start=1):
                    if PATTERN.search(line) and not _PLACEHOLDER.search(line):
                        violations.append((path, lineno, line.strip()))
        except (FileNotFoundError, IsADirectoryError, UnicodeDecodeError):
            continue
    return violations


def main() -> int:
    violations = find_violations(sys.stdin.read().splitlines())
    for path, lineno, line in violations:
        print(f"  {path}:{lineno}")
        print(f"      > {line}")
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
