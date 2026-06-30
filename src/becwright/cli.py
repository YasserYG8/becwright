from __future__ import annotations

import argparse
import pkgutil
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


_CHECK_DESCRIPTIONS = {
    "forbid": "fail if a regex (--pattern) appears in the files (any language)",
    "no_token_in_logs": "tokens or credentials in log calls (Python)",
    "hardcoded_secrets": "AWS keys, private keys, hardcoded password literals (any language)",
    "debug_remnants": "leftover debugger / pdb statements (Python)",
    "dangerous_eval": "eval / exec calls (any language)",
    "wildcard_imports": "wildcard star imports (Python)",
    "redundant_comments": "comments that restate the obvious code (Python, heuristic)",
}


def _builtin_check_names() -> list[str]:
    from . import checks
    return sorted(m.name for m in pkgutil.iter_modules(checks.__path__) if not m.name.startswith("_"))


def _cmd_run(args: argparse.Namespace) -> int:
    if args.module not in _builtin_check_names():
        print(f"{RED}Unknown built-in check: {args.module}{RESET}", file=sys.stderr)
        return 2
    from importlib import import_module
    # Forward any args to the check through sys.argv: checks that take options
    # (e.g. forbid --pattern) read sys.argv[1:]; the rest just ignore it.
    sys.argv = [f"becwright run {args.module}", *args.args]
    return import_module(f"becwright.checks.{args.module}").main()


def _cmd_list(_: argparse.Namespace) -> int:
    print(f"{BOLD}Built-in checks{RESET} {DIM}(use as: becwright run <name>){RESET}")
    for name in _builtin_check_names():
        desc = _CHECK_DESCRIPTIONS.get(name, "")
        line = f"  {GREEN}{name}{RESET}"
        if desc:
            line += f"  {DIM}{desc}{RESET}"
        print(line)
    print(f"\n{DIM}Catalog of ready-to-use BECs: "
          f"https://github.com/DataDave-Dev/becwright/tree/main/becs{RESET}")
    return 0


_SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build", ".tox"}
_EXT_LANG = {".py": "python", ".js": "js", ".ts": "ts"}


def _detect_languages(root: Path) -> list[str]:
    found: set[str] = set()
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in _SKIP_DIRS for part in path.relative_to(root).parts):
            continue
        lang = _EXT_LANG.get(path.suffix)
        if lang:
            found.add(lang)
    return [lang for lang in ("python", "js", "ts") if lang in found]


def _starter_rules(langs: list[str]) -> list[dict]:
    source_globs = [g for lang, g in (("python", "**/*.py"), ("js", "**/*.js"), ("ts", "**/*.ts")) if lang in langs]
    rules: list[dict] = []
    if source_globs:
        rules.append(dict(
            id="no-hardcoded-secrets", paths=source_globs, severity="blocking",
            check="becwright run hardcoded_secrets",
            intent="No secret (key, token, password) should be hardcoded in the code.",
            why="A secret in the repo stays in git history forever and is visible to anyone with access to the code."))
    if "python" in langs:
        rules.append(dict(
            id="no-debug-remnants", paths=["**/*.py"], severity="blocking",
            check="becwright run debug_remnants",
            intent="Debug code (breakpoints, pdb) must not be committed.",
            why="A forgotten breakpoint hangs the process in production or CI."))
        rules.append(dict(
            id="no-dangerous-eval", paths=["**/*.py"], severity="blocking",
            check="becwright run dangerous_eval",
            intent="Avoid eval and exec, which run arbitrary code.",
            why="Dynamic eval/exec on untrusted input is remote code execution."))
    if "js" in langs or "ts" in langs:
        js_globs = [g for g in source_globs if g.endswith((".js", ".ts"))]
        rules.append(dict(
            id="no-debugger-js", paths=js_globs, severity="blocking",
            check="becwright run forbid --pattern '\\bdebugger\\b'",
            intent="Do not leave 'debugger;' in JavaScript/TypeScript code.",
            why="A forgotten 'debugger' halts execution and should not reach production."))
        rules.append(dict(
            id="no-console-log-js", paths=js_globs, severity="warning",
            check="becwright run forbid --pattern 'console\\.log\\s*\\('",
            intent="Avoid 'console.log(...)' in JavaScript/TypeScript code.",
            why="Debug console.log statements clutter production output."))
    return rules


def _render_rules_yaml(rules: list[dict]) -> str:
    header = (
        "# becwright rules - generated by `becwright init`. Tune them to your repo.\n"
        "# Catalog: https://github.com/DataDave-Dev/becwright/tree/main/becs\n"
        "# Docs: https://github.com/DataDave-Dev/becwright/tree/main/documentation\n"
    )
    if not rules:
        return header + "rules: []\n"
    blocks = []
    for r in rules:
        paths = "\n".join(f'      - "{p}"' for p in r["paths"])
        blocks.append(
            f"  - id: {r['id']}\n"
            f"    intent: >\n      {r['intent']}\n"
            f"    why_it_matters: >\n      {r['why']}\n"
            f"    paths:\n{paths}\n"
            f"    check: {r['check']}\n"
            f"    severity: {r['severity']}\n"
        )
    return header + "rules:\n" + "\n".join(blocks)


def _cmd_init(args: argparse.Namespace) -> int:
    root = git.repo_root()
    rules_path = root / ".bec" / "rules.yaml"
    if rules_path.exists() and not args.force:
        print(f"{YELLOW}{rules_path} already exists. Use --force to overwrite.{RESET}")
        return 1
    langs = _detect_languages(root)
    rules = _starter_rules(langs)
    rules_path.parent.mkdir(parents=True, exist_ok=True)
    rules_path.write_text(_render_rules_yaml(rules), encoding="utf-8")

    detected = ", ".join(langs) if langs else "none"
    print(f"{GREEN}Created {rules_path}{RESET} {DIM}({len(rules)} starter rule(s); languages: {detected}){RESET}")
    ok, msg = git.install_hook(root)
    print((GREEN if ok else YELLOW) + msg + RESET)
    print(f"{DIM}Review your rules, then run `becwright check --all` to see the current state.{RESET}")
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

    p_init = sub.add_parser("init", help="scaffold a starter .bec/rules.yaml and install the hook")
    p_init.add_argument("--force", action="store_true", help="overwrite an existing .bec/rules.yaml")
    p_init.set_defaults(func=_cmd_init)

    p_run = sub.add_parser("run", help="run a built-in check against files on stdin (used inside rules)")
    p_run.add_argument("module", help="built-in check name (see `becwright list`)")
    p_run.add_argument("args", nargs=argparse.REMAINDER, help="arguments forwarded to the check")
    p_run.set_defaults(func=_cmd_run)

    sub.add_parser("list", help="list the built-in checks").set_defaults(func=_cmd_list)
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
