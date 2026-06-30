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
            print(f"  {GREEN}PASS{RESET}  {r.rule.id}")
            continue
        if r.rule.is_blocking:
            print(f"  {RED}{BOLD}BLOCK{RESET}  {r.rule.id}  {RED}(blocking){RESET}")
        else:
            print(f"  {YELLOW}WARN{RESET}  {r.rule.id}  {YELLOW}(warning only){RESET}")
        if r.rule.intent:
            print(f"        {DIM}Intent:{RESET} {r.rule.intent}")
        if r.rule.why_it_matters:
            print(f"        {DIM}Why it matters:{RESET} {r.rule.why_it_matters}")
        if r.output:
            print(f"        {DIM}Found in:{RESET}")
            for line in r.output.splitlines():
                print(f"        {line}")
        print()


def _cmd_check(args: argparse.Namespace) -> int:
    root = git.repo_root()
    rules = load_rules(root / ".bec" / "rules.yaml")
    if not rules:
        print(f"{YELLOW}No .bec/rules.yaml with rules. Nothing to check.{RESET}")
        return 0

    files = git.files_to_check(root, all_files=args.all)
    if not files:
        print(f"{DIM}No files to check.{RESET}")
        return 0

    print(f"{BOLD}BEC -- {len(files)} file(s) against {len(rules)} rule(s){RESET}\n")
    result = evaluate(rules, files, root)
    _print_result(result)

    if result.had_blocking:
        print(f"{RED}{BOLD}>>> Commit BLOCKED: a blocking rule was broken.{RESET}")
        print(f"{DIM}    Fix the above, or if it is intentional edit .bec/rules.yaml{RESET}")
        return 1
    print(f"{GREEN}{BOLD}>>> All good. Commit allowed.{RESET}")
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
        print(f"{RED}No rule with id '{args.rule_id}' in .bec/rules.yaml.{RESET}", file=sys.stderr)
        return 1
    text = bundle.export_bec(rule, root)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
        print(f"{GREEN}BEC '{rule.id}' exported to {args.output}.{RESET}")
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
    print(f"{BOLD}BEC: {rule['id']}{RESET}  {DIM}(from {data.get('exported_from', '?')}){RESET}")
    if rule.get("intent"):
        print(f"  {DIM}Intent:{RESET} {rule['intent'].strip()}")
    if rule.get("why_it_matters"):
        print(f"  {DIM}Why it matters:{RESET} {rule['why_it_matters'].strip()}")
    kind = check.get("kind")
    print(f"  {DIM}Check:{RESET} {kind}")
    if kind == "script":
        print(f"  {DIM}Code of {check.get('filename')}:{RESET}")
        for line in check.get("source", "").splitlines():
            print(f"      {line}")
    elif kind == "command":
        print(f"  {DIM}Command:{RESET} {check.get('command')}")


def _cmd_import(args: argparse.Namespace) -> int:
    root = git.repo_root()
    try:
        data = bundle.parse_bundle(_read_source(args.source))
    except (bundle.BundleError, OSError, urllib.error.URLError) as e:
        print(f"{RED}Could not import: {e}{RESET}", file=sys.stderr)
        return 1

    _print_bundle_summary(data)
    if not args.yes:
        print(f"{YELLOW}Importing a BEC installs code that runs on every commit.{RESET}")
        if input("Install this BEC? [y/N] ").strip().lower() not in ("y", "yes"):
            print(f"{DIM}Cancelled. Nothing was written.{RESET}")
            return 1

    rules_path = root / ".bec" / "rules.yaml"
    rule_id = data["rule"]["id"]
    if rule_id in {r.id for r in load_rules(rules_path)}:
        print(f"{RED}A rule with id '{rule_id}' already exists. Not duplicating it.{RESET}", file=sys.stderr)
        return 1
    try:
        rule_dict = bundle.materialize(data, root)
    except bundle.BundleError as e:
        print(f"{RED}{e}{RESET}", file=sys.stderr)
        return 1
    bundle.append_rule(rules_path, rule_dict)
    print(f"{GREEN}{BOLD}BEC '{rule_id}' installed in .bec/rules.yaml.{RESET}")
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="becwright",
        description="Enforces BECs (Bound Executable Constraints) on your code.",
    )
    parser.add_argument("--version", action="version", version=f"becwright {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p_check = sub.add_parser("check", help="check the code against the rules")
    p_check.add_argument("--all", action="store_true", help="check the whole repo, not just staging")
    p_check.set_defaults(func=_cmd_check)

    sub.add_parser("install", help="install the pre-commit hook").set_defaults(func=_cmd_install)
    sub.add_parser("uninstall", help="remove the pre-commit hook").set_defaults(func=_cmd_uninstall)

    p_export = sub.add_parser("export", help="export a BEC to a .bec.yaml file")
    p_export.add_argument("rule_id", help="id of the rule to export")
    p_export.add_argument("-o", "--output", help="output file (default: stdout)")
    p_export.set_defaults(func=_cmd_export)

    p_import = sub.add_parser("import", help="import a BEC from a file or URL")
    p_import.add_argument("source", help="path to a .bec.yaml or http(s) URL")
    p_import.add_argument("--yes", action="store_true", help="install without asking for confirmation")
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
