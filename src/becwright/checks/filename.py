from __future__ import annotations

import argparse
import os
import re
import sys


def find_violations(paths: list[str], forbid: str | None = None,
                    require: str | None = None, flags: int = 0) -> list[tuple[str, str]]:
    """File paths whose base name matches `forbid` or fails to match `require`, as
    (path, reason). Operates purely on the path — no file is opened."""
    forbid_rx = re.compile(forbid, flags) if forbid else None
    require_rx = re.compile(require, flags) if require else None
    violations: list[tuple[str, str]] = []
    for path in paths:
        path = path.strip()
        if not path:
            continue
        name = os.path.basename(path)
        if forbid_rx and forbid_rx.search(name):
            violations.append((path, f"name matches forbidden pattern: {forbid}"))
        elif require_rx and not require_rx.search(name):
            violations.append((path, f"name does not match required pattern: {require}"))
    return violations


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="becwright.checks.filename",
        description="Fails on file names that match --forbid or do not match --require.",
    )
    parser.add_argument("--forbid", help="regex a file name must not match")
    parser.add_argument("--require", help="regex a file name must match")
    parser.add_argument("--ignore-case", action="store_true", help="ignore case")
    args = parser.parse_args(argv)
    if not args.forbid and not args.require:
        print("give at least one of --forbid or --require", file=sys.stderr)
        return 2

    try:
        violations = find_violations(
            sys.stdin.read().splitlines(),
            args.forbid, args.require,
            re.IGNORECASE if args.ignore_case else 0,
        )
    except re.error as e:
        print(f"invalid pattern: {e}", file=sys.stderr)
        return 2

    for path, reason in violations:
        print(f"  {path}")
        print(f"      > {reason}")
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
