from __future__ import annotations

import argparse
import re
import sys


def find_violations(paths: list[str], pattern: str, flags: int = 0) -> list[str]:
    """Files where `pattern` never appears (the inverse of `forbid`)."""
    rx = re.compile(pattern, flags)
    missing: list[str] = []
    for path in paths:
        path = path.strip()
        if not path:
            continue
        try:
            with open(path, encoding="utf-8") as f:
                present = any(rx.search(line) for line in f)
        except (FileNotFoundError, IsADirectoryError, UnicodeDecodeError):
            continue
        if not present:
            missing.append(path)
    return missing


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="becwright.checks.require",
        description="Fails if a regex pattern is missing from a file.",
    )
    parser.add_argument("--pattern", required=True, help="regex that must appear")
    parser.add_argument("--ignore-case", action="store_true", help="ignore case")
    parser.add_argument("--message", default="", help="note to show if there are matches")
    args = parser.parse_args(argv)

    try:
        missing = find_violations(
            sys.stdin.read().splitlines(),
            args.pattern,
            re.IGNORECASE if args.ignore_case else 0,
        )
    except re.error as e:
        print(f"invalid pattern: {e}", file=sys.stderr)
        return 2

    if args.message and missing:
        print(f"  {args.message}")
    for path in missing:
        print(f"  {path}")
        print(f"      > required pattern not found: {args.pattern}")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
