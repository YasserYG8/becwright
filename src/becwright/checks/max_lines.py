from __future__ import annotations

import argparse
import sys


def find_violations(paths: list[str], max_lines: int) -> list[tuple[str, int]]:
    """Files whose line count exceeds `max_lines`, as (path, line_count)."""
    violations: list[tuple[str, int]] = []
    for path in paths:
        path = path.strip()
        if not path:
            continue
        try:
            with open(path, encoding="utf-8") as f:
                count = sum(1 for _ in f)
        except (FileNotFoundError, IsADirectoryError, UnicodeDecodeError):
            continue
        if count > max_lines:
            violations.append((path, count))
    return violations


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="becwright.checks.max_lines",
        description="Fails if a file exceeds a maximum number of lines.",
    )
    parser.add_argument("--max", type=int, required=True, dest="max_lines",
                        help="maximum lines allowed per file")
    args = parser.parse_args(argv)
    if args.max_lines <= 0:
        print("--max must be a positive integer", file=sys.stderr)
        return 2

    violations = find_violations(sys.stdin.read().splitlines(), args.max_lines)
    for path, count in violations:
        print(f"  {path}: {count} lines (max {args.max_lines})")
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
