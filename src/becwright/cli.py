from __future__ import annotations

import argparse
import sys
import urllib.error
import urllib.request
from pathlib import Path

from . import __version__, bundle, git
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
        if r.rule.intent:
            print(f"        {DIM}Qué pide:{RESET} {r.rule.intent}")
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


def _cmd_export(args: argparse.Namespace) -> int:
    root = git.repo_root()
    rule = next((r for r in load_rules(root / ".bec" / "rules.yaml") if r.id == args.rule_id), None)
    if rule is None:
        print(f"{RED}No existe una regla con id '{args.rule_id}' en .bec/rules.yaml.{RESET}", file=sys.stderr)
        return 1
    text = bundle.export_bec(rule, root)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
        print(f"{GREEN}BEC '{rule.id}' exportada a {args.output}.{RESET}")
    else:
        sys.stdout.write(text)
    return 0


def _read_source(source: str) -> str:
    if source.startswith(("http://", "https://")):
        with urllib.request.urlopen(source, timeout=15) as resp:
            return resp.read().decode("utf-8")
    return Path(source).read_text(encoding="utf-8")


def _print_bundle_summary(data: dict) -> None:
    rule, check = data["rule"], data["check"]
    print(f"{BOLD}BEC: {rule['id']}{RESET}  {DIM}(desde {data.get('exported_from', '?')}){RESET}")
    if rule.get("intent"):
        print(f"  {DIM}Qué pide:{RESET} {rule['intent'].strip()}")
    if rule.get("why_it_matters"):
        print(f"  {DIM}Por qué importa:{RESET} {rule['why_it_matters'].strip()}")
    kind = check.get("kind")
    print(f"  {DIM}Check:{RESET} {kind}")
    if kind == "script":
        print(f"  {DIM}Código de {check.get('filename')}:{RESET}")
        for line in check.get("source", "").splitlines():
            print(f"      {line}")
    elif kind == "command":
        print(f"  {DIM}Comando:{RESET} {check.get('command')}")


def _cmd_import(args: argparse.Namespace) -> int:
    root = git.repo_root()
    try:
        data = bundle.parse_bundle(_read_source(args.source))
    except (bundle.BundleError, OSError, urllib.error.URLError) as e:
        print(f"{RED}No se pudo importar: {e}{RESET}", file=sys.stderr)
        return 1

    _print_bundle_summary(data)
    if not args.yes:
        print(f"{YELLOW}Importar una BEC instala código que se ejecuta en cada commit.{RESET}")
        if input("¿Instalar esta BEC? [y/N] ").strip().lower() not in ("y", "yes", "s", "si", "sí"):
            print(f"{DIM}Cancelado. No se escribió nada.{RESET}")
            return 1

    rules_path = root / ".bec" / "rules.yaml"
    rule_id = data["rule"]["id"]
    if rule_id in {r.id for r in load_rules(rules_path)}:
        print(f"{RED}Ya existe una regla con id '{rule_id}'. No la dupliqué.{RESET}", file=sys.stderr)
        return 1
    try:
        rule_dict = bundle.materialize(data, root)
    except bundle.BundleError as e:
        print(f"{RED}{e}{RESET}", file=sys.stderr)
        return 1
    bundle.append_rule(rules_path, rule_dict)
    print(f"{GREEN}{BOLD}BEC '{rule_id}' instalada en .bec/rules.yaml.{RESET}")
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

    p_export = sub.add_parser("export", help="exporta una BEC a un archivo .bec.yaml")
    p_export.add_argument("rule_id", help="id de la regla a exportar")
    p_export.add_argument("-o", "--output", help="archivo de salida (por defecto: stdout)")
    p_export.set_defaults(func=_cmd_export)

    p_import = sub.add_parser("import", help="importa una BEC desde un archivo o URL")
    p_import.add_argument("source", help="ruta a un .bec.yaml o URL http(s)")
    p_import.add_argument("--yes", action="store_true", help="instala sin pedir confirmación")
    p_import.set_defaults(func=_cmd_import)
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
