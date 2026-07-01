from __future__ import annotations

import re
import sys

from ._ignore import is_ignored

# The angle/pipe markers a merge conflict leaves behind. `=======` is omitted on
# purpose: it also appears in legitimate text (e.g. a Markdown heading underline),
# and every real conflict already carries `<<<<<<<` and `>>>>>>>`, so it is caught.
PATTERN = re.compile(r"^(?:<{7}|>{7}|\|{7})(?:\s|$)")


def find_violations(paths: list[str]) -> list[tuple[str, int, str]]:
    violations: list[tuple[str, int, str]] = []
    for path in paths:
        path = path.strip()
        if not path:
            continue
        try:
            with open(path, encoding="utf-8") as f:
                for lineno, line in enumerate(f, start=1):
                    if PATTERN.search(line) and not is_ignored(line):
                        violations.append((path, lineno, line.rstrip()))
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
