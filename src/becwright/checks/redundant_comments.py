from __future__ import annotations

import io
import re
import sys
import tokenize

# Short filler words that carry no meaning for the redundancy comparison.
_STOP = {
    "the", "and", "for", "with", "from", "this", "that", "here", "then", "when",
    "each", "only", "not", "but", "its", "was", "are", "use", "via", "into",
}
# Pragmas and machine-readable comments are never style violations.
_PRAGMA = ("type:", "noqa", "pragma", "pylint", "mypy", "ruff", "fmt:", "isort:")

_WORDS = re.compile(r"[A-Za-z]+")


def _significant(text: str) -> tuple[list[str], list[str]]:
    words = _WORDS.findall(text.lower())
    return words, [w for w in words if len(w) >= 3 and w not in _STOP]


def _is_redundant(comment_text: str, code_line: str) -> bool:
    body = comment_text.lstrip("#").strip()
    if not body or body.startswith(_PRAGMA):
        return False
    words, significant = _significant(body)
    # Long comments are prose (the "why"); only short labels can be restatements.
    if not significant or len(words) > 6:
        return False
    code_words = set(_WORDS.findall(code_line.lower()))
    return all(w in code_words for w in significant)


def _next_code_line(lines: list[str], start_row: int) -> str:
    for line in lines[start_row:]:
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            return line
    return ""


def find_violations(paths: list[str]) -> list[tuple[str, int, str]]:
    violations: list[tuple[str, int, str]] = []
    for path in paths:
        path = path.strip()
        if not path:
            continue
        try:
            text = open(path, encoding="utf-8").read()
        except (FileNotFoundError, IsADirectoryError, UnicodeDecodeError):
            continue
        lines = text.splitlines()
        # tokenize so that `#` inside a string is never treated as a comment.
        try:
            tokens = list(tokenize.generate_tokens(io.StringIO(text).readline))
        except (tokenize.TokenError, SyntaxError, IndentationError):
            continue
        for tok in tokens:
            if tok.type != tokenize.COMMENT:
                continue
            row, col = tok.start
            if row == 1 and tok.string.startswith("#!"):
                continue
            line = lines[row - 1]
            before = line[:col]
            code = before if before.strip() else _next_code_line(lines, row)
            if code and _is_redundant(tok.string, code):
                violations.append((path, row, tok.string.strip()))
    return violations


def main() -> int:
    violations = find_violations(sys.stdin.read().splitlines())
    for path, lineno, comment in violations:
        print(f"  {path}:{lineno}")
        print(f"      > {comment}")
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
