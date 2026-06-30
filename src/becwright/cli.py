from __future__ import annotations

import argparse
import sys

from . import __version__, git
from .engine import Result, evaluate
from .rules import load_rules

RED = "\033[91m"; GREEN = "\033[92m"; YELLOW = "\033[93m"
BOLD = "\033[1m"; DIM = "\033[2m"; RESET = "\033[0m"


def _print_result(result: Result) -> None:
    for r in result.per_rule:
        if r.passed:
            print(f"  {GREEN}PASA{RESET}  {r.rule.id}")
            continue
        if r.rule.is_blocking:
            print(f"  {RED}{BOLD}FRENO{RESET}  {r.rule.id}  {RED}(bloqueante){RESET}")
        else:
            print(f"  {YELLOW}AVISO{RESET}  {r.rule.id}  {YELLOW}(solo advertencia){RESET}")
        if r.rule.why_it_matters:
            print(f"        {DIM}Por qué importa:{RESET} {r.rule.why_it_matters}")
        if r.output:
            print(f"        {DIM}Encontrado en:{RESET}")
            for line in r.output.splitlines():
                print(f"        {line}")
        print()


def _cmd_check(args: argparse.Namespace) -> int:
    root = git.repo_root()
    rules = load_rules(root / ".bec" / "rules.yaml")
    if not rules:
        print(f"{YELLOW}No hay .bec/rules.yaml con reglas. Nada que revisar.{RESET}")
        return 0

    files = git.files_to_check(root, all_files=args.all)
    if not files:
        print(f"{DIM}No hay archivos para revisar.{RESET}")
        return 0

    print(f"{BOLD}BEC -- {len(files)} archivo(s) contra {len(rules)} regla(s){RESET}\n")
    result = evaluate(rules, files, root)
    _print_result(result)

    if result.had_blocking:
        print(f"{RED}{BOLD}>>> Commit BLOQUEADO: se rompió una regla bloqueante.{RESET}")
        print(f"{DIM}    Arreglá lo de arriba, o si es intencional editá .bec/rules.yaml{RESET}")
        return 1
    print(f"{GREEN}{BOLD}>>> Todo bien. Commit permitido.{RESET}")
    return 0


def _cmd_install(_: argparse.Namespace) -> int:
    ok, msg = git.install_hook(git.repo_root())
    print((GREEN if ok else YELLOW) + msg + RESET)
    return 0


def _cmd_uninstall(_: argparse.Namespace) -> int:
    ok, msg = git.uninstall_hook(git.repo_root())
    print((GREEN if ok else YELLOW) + msg + RESET)
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="becwright",
        description="Hace cumplir BECs (Bound Executable Constraints) sobre el código.",
    )
    parser.add_argument("--version", action="version", version=f"becwright {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p_check = sub.add_parser("check", help="revisa el código contra las reglas")
    p_check.add_argument("--all", action="store_true", help="revisa todo el repo, no solo staging")
    p_check.set_defaults(func=_cmd_check)

    sub.add_parser("install", help="instala el hook pre-commit").set_defaults(func=_cmd_install)
    sub.add_parser("uninstall", help="quita el hook pre-commit").set_defaults(func=_cmd_uninstall)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        return args.func(args)
    except git.NotAGitRepo as e:
        print(f"{RED}{e}{RESET}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
