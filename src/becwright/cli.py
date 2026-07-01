from __future__ import annotations

import argparse
import os
import pkgutil
import sys
import urllib.error
import urllib.request
from pathlib import Path

from . import __version__, bundle, catalog, git, report
from .engine import Result
from .rules import RulesError, load_rules

RED = "\033[91m"; GREEN = "\033[92m"; YELLOW = "\033[93m"
BOLD = "\033[1m"; DIM = "\033[2m"; RESET = "\033[0m"


def _colors_enabled() -> bool:
    return not os.environ.get("NO_COLOR") and sys.stdout.isatty()


def _style(text: str, *codes: str) -> str:
    if not _colors_enabled():
        return text
    return f"{''.join(codes)}{text}{RESET}"


def _print_result(result: Result) -> None:
    for r in result.per_rule:
        if r.passed:
            print(f"  {_style('PASS', GREEN)}  {r.rule.id}")
            continue
        if r.rule.is_blocking:
            print(f"  {_style('BLOCK', RED, BOLD)}  {r.rule.id}  {_style('(blocking)', RED)}")
        else:
            print(f"  {_style('WARN', YELLOW)}  {r.rule.id}  {_style('(warning only)', YELLOW)}")
        if r.rule.intent:
            print(f"        {_style('Intent:', DIM)} {r.rule.intent}")
        if r.rule.why_it_matters:
            print(f"        {_style('Why it matters:', DIM)} {r.rule.why_it_matters}")
        if r.output:
            print(f"        {_style('Found in:', DIM)}")
            for line in r.output.splitlines():
                print(f"        {line}")
        print()


def _unknown_builtin_checks(rules, root: Path) -> list[tuple[str, str]]:
    """Rules whose `check` uses the `becwright run <name>` form with a <name> that
    is not a built-in check. Such a rule can never pass — the check exits with an
    error that otherwise reads like a real violation — so it is a config problem,
    not a broken commit. Custom scripts and opaque shell commands are left alone."""
    from . import bundle
    known = set(_builtin_check_names())
    found: list[tuple[str, str]] = []
    for rule in rules:
        info = bundle.classify_check(rule.check, root)
        if info.get("kind") == "builtin" and info["module"] not in known:
            found.append((rule.id, info["module"]))
    return found


def _print_unknown_checks(unknown: list[tuple[str, str]]) -> None:
    print(_style("Config problem in .bec/rules.yaml:", RED, BOLD), file=sys.stderr)
    for rule_id, module in unknown:
        print(_style(f"  rule '{rule_id}' uses check '{module}', "
                     "which is not a built-in check.", RED), file=sys.stderr)
    print(_style("  Run `becwright list` to see valid checks, or point `check:` "
                 "at a custom script path.", DIM), file=sys.stderr)


def _cmd_check(args: argparse.Namespace) -> int:
    root = git.repo_root()
    rules, files, result = report.gather(root, all_files=args.all)

    unknown = _unknown_builtin_checks(rules, root)
    if unknown:
        _print_unknown_checks(unknown)
        return 2

    if args.json:
        import json
        print(json.dumps(report.payload(rules, files, result), indent=2))
        return 1 if (result and result.had_blocking) else 0

    if not rules:
        print(_style("No .bec/rules.yaml with rules. Nothing to check.", YELLOW))
        return 0
    if not files:
        print(_style("No files to check.", DIM))
        return 0

    print(f"{_style(f'BEC -- {len(files)} file(s) against {len(rules)} rule(s)', BOLD)}\n")
    _print_result(result)

    if result.had_blocking:
        print(_style(">>> Commit BLOCKED: a blocking rule was broken.", RED, BOLD))
        print(_style("    Fix the above, or if it is intentional edit .bec/rules.yaml", DIM))
        return 1
    print(_style(">>> All good. Commit allowed.", GREEN, BOLD))
    return 0


def _cmd_install(_: argparse.Namespace) -> int:
    ok, msg = git.install_hook(git.repo_root())
    print(_style(msg, GREEN if ok else YELLOW))
    return 0


def _cmd_uninstall(_: argparse.Namespace) -> int:
    ok, msg = git.uninstall_hook(git.repo_root())
    print(_style(msg, GREEN if ok else YELLOW))
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
        print(_style(f"Unknown built-in check: {args.module}", RED), file=sys.stderr)
        return 2
    from importlib import import_module
    # Forward any args to the check through sys.argv: checks that take options
    # (e.g. forbid --pattern) read sys.argv[1:]; the rest just ignore it.
    sys.argv = [f"becwright run {args.module}", *args.args]
    return import_module(f"becwright.checks.{args.module}").main()


def _cmd_mcp(_: argparse.Namespace) -> int:
    try:
        from .mcp_server import serve
    except ImportError:
        print(_style("The MCP server needs the 'mcp' extra.", RED), file=sys.stderr)
        print(_style('    pipx install "becwright[mcp]"   (or: pip install "becwright[mcp]")', DIM),
              file=sys.stderr)
        return 2
    serve()
    return 0


def _cmd_list(_: argparse.Namespace) -> int:
    print(f"{_style('Built-in checks', BOLD)} {_style('(use as: becwright run <name>)', DIM)}")
    for name in _builtin_check_names():
        desc = _CHECK_DESCRIPTIONS.get(name, "")
        line = f"  {_style(name, GREEN)}"
        if desc:
            line += f"  {_style(desc, DIM)}"
        print(line)
    print(_style("\nReady-to-use BECs from the catalog: "
                 "`becwright search` to list, `becwright add <name>` to install.", DIM))
    return 0


_SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build", ".tox"}
_EXT_LANG = {
    ".py": "python",
    ".js": "js",
    ".ts": "ts",
    ".go": "go",
    ".rs": "rust",
}


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

    return [lang for lang in ("python", "js", "ts", "go", "rust") if lang in found]


def _starter_rules(langs: list[str]) -> list[dict]:
    source_globs = [
        g
        for lang, g in (
            ("python", "**/*.py"),
            ("js", "**/*.js"),
            ("ts", "**/*.ts"),
            ("go", "**/*.go"),
            ("rust", "**/*.rs"),
        )
        if lang in langs
    ]

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

    if "go" in langs:
        rules.append(dict(
            id="no-debug-go", paths=["**/*.go"], severity="blocking",
            check=r"becwright run forbid --pattern 'fmt\.Println\s*\(|panic\s*\('",
            intent="Do not leave debug output or panic calls in Go code.",
            why="Debug statements and unexpected panic calls should not reach production."))

    if "rust" in langs:
        rules.append(dict(
            id="no-debug-rust", paths=["**/*.rs"], severity="blocking",
            check=r"becwright run forbid --pattern 'dbg!\s*\(|println!\s*\('",
            intent="Do not leave debug output in Rust code.",
            why="Debug macros and leftover println! calls should not reach production."))

    return rules


def _render_rules_yaml(rules: list[dict]) -> str:
    header = (
        "# becwright rules - generated by `becwright init`. Tune them to your repo.\n"
        "# More rules: `becwright search` to list the catalog, `becwright add <name>` to install.\n"
        "# Docs: https://github.com/DataDave-Dev/becwright/tree/main/documentation\n"
    )
    if not rules:
        return header + "rules: []\n"
    blocks = []
    for r in rules:
        paths = "\n".join(f'      - "{p}"' for p in r["paths"])
        note = f"  # {r['note']}\n" if r.get("note") else ""
        exclude = ""
        if r.get("exclude"):
            lines = "\n".join(f'      - "{p}"' for p in r["exclude"])
            exclude = f"    exclude:\n{lines}\n"
        blocks.append(
            f"{note}"
            f"  - id: {r['id']}\n"
            f"    intent: >\n      {r['intent']}\n"
            f"    why_it_matters: >\n      {r['why']}\n"
            f"    paths:\n{paths}\n"
            f"{exclude}"
            f"    check: {r['check']}\n"
            f"    severity: {r['severity']}\n"
        )
    return header + "rules:\n" + "\n".join(blocks)


def _apply_baseline(root: Path, rules: list[dict]) -> list[tuple[str, int]]:
    """Downgrade to `warning` any starter rule that already has violations in the
    current code, so adopting becwright never blocks a commit on pre-existing debt.
    Clean rules stay `blocking` (a guardrail from day one). Returns the (id, count)
    pairs that were downgraded so the caller can report the adoption ramp."""
    from .engine import evaluate
    from .rules import Rule

    files = git.files_to_check(root, all_files=True)
    if not files:
        return []
    rule_objs = [
        Rule(id=r["id"], paths=tuple(r["paths"]), check=r["check"], severity=r["severity"])
        for r in rules
    ]
    by_id = {rr.rule.id: rr for rr in evaluate(rule_objs, files, root).per_rule}
    downgraded: list[tuple[str, int]] = []
    for r in rules:
        result = by_id.get(r["id"])
        if result and not result.passed:
            count = sum(1 for line in result.output.splitlines() if line.strip()) or 1
            r["severity"] = "warning"
            r["note"] = (f"baseline: {count} pre-existing violation(s) on adoption; "
                         "graduate to blocking once clean")
            downgraded.append((r["id"], count))
    return downgraded


def _print_baseline(rules: list[dict], downgraded: list[tuple[str, int]]) -> None:
    if not downgraded:
        print(_style("Baseline: clean repo — every rule starts as blocking.", GREEN))
        return
    blocking = len(rules) - len(downgraded)
    print(_style("Baseline:", BOLD),
          f"{blocking} rule(s) blocking, {len(downgraded)} started as warning "
          "so adoption never blocks a commit on pre-existing debt:")
    for rule_id, count in downgraded:
        print(f"  {_style('warning', YELLOW)}  {rule_id}  "
              f"{_style(f'({count} pre-existing)', DIM)}")
    print(_style("  Clean each up, then flip it to 'blocking' in .bec/rules.yaml.", DIM))


def _cmd_init(args: argparse.Namespace) -> int:
    root = git.repo_root()
    rules_path = root / ".bec" / "rules.yaml"
    if rules_path.exists() and not args.force:
        print(_style(f"{rules_path} already exists. Use --force to overwrite.", YELLOW))
        return 1
    langs = _detect_languages(root)
    rules = _starter_rules(langs)
    downgraded = _apply_baseline(root, rules) if args.baseline else []
    rules_path.parent.mkdir(parents=True, exist_ok=True)
    rules_path.write_text(_render_rules_yaml(rules), encoding="utf-8")

    detected = ", ".join(langs) if langs else "none"
    print(f"{_style(f'Created {rules_path}', GREEN)} "
          f"{_style(f'({len(rules)} starter rule(s); languages: {detected})', DIM)}")
    if args.baseline:
        _print_baseline(rules, downgraded)
    ok, msg = git.install_hook(root)
    print(_style(msg, GREEN if ok else YELLOW))
    print()
    print(_style("Next steps:", BOLD))
    print(f"  1. {_style('Look at your rules:', DIM)}      .bec/rules.yaml")
    print(f"  2. {_style('See the current state:', DIM)}   becwright check --all")
    print(f"  3. {_style('Just commit as usual', DIM)} — becwright runs automatically.")
    return 0


_DEMO_FILENAME = "checkout.py"
_DEMO_CODE = (
    "def charge(card, amount):\n"
    '    api_key = "x7Kp2mQ9vT4nB8wL"   # secret hardcoded in the code\n'
    "    rule = get_promo_rule(card)\n"
    "    discount = eval(rule)                              # runs whatever the promo string says\n"  # becwright: ignore  (demo sample, not real eval)
    "    return run_charge(card, amount - discount, api_key)\n"
)


def _demo_result(file_path: Path, display_name: str) -> Result:
    from .checks import dangerous_eval, hardcoded_secrets
    from .engine import RuleResult
    from .rules import Rule

    pairs = [
        (Rule(
            id="no-hardcoded-secrets", paths=("*.py",), check="becwright run hardcoded_secrets",
            severity="blocking",
            intent="No secret (key, token, password) should be hardcoded.",
            why_it_matters="A secret in the code stays in git history forever, for anyone with repo access."),
         hardcoded_secrets),
        (Rule(
            id="no-dangerous-eval", paths=("*.py",), check="becwright run dangerous_eval",
            severity="blocking",
            intent="Avoid eval/exec, which run arbitrary code.",
            why_it_matters="eval on untrusted input is a remote-code-execution hole."),
         dangerous_eval),
    ]
    per_rule = []
    for rule, module in pairs:
        violations = module.find_violations([str(file_path)])
        output = "\n".join(f"  {display_name}:{ln}\n      > {text}" for _p, ln, text in violations)
        per_rule.append(RuleResult(rule=rule, passed=not violations, output=output))
    return Result(per_rule=per_rule)


def _cmd_demo(_: argparse.Namespace) -> int:
    import shutil
    import tempfile

    print(f"{_style('becwright demo', BOLD)} "
          f"{_style('— a safe sandbox. Nothing in your project is created or changed.', DIM)}\n")
    print(_style("Pretend someone is about to commit this file:", DIM))
    print(f"  {_style(_DEMO_FILENAME, BOLD)}")
    for line in _DEMO_CODE.splitlines():
        print(f"      {line}")
    print()

    tmp = Path(tempfile.mkdtemp(prefix="becwright-demo-"))
    try:
        demo_file = tmp / _DEMO_FILENAME
        demo_file.write_text(_DEMO_CODE, encoding="utf-8")
        result = _demo_result(demo_file, _DEMO_FILENAME)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print(f"{_style('BEC -- 1 file(s) against 2 rule(s)', BOLD)}\n")
    _print_result(result)
    print(_style(">>> Commit BLOCKED: becwright caught it before it shipped.", RED, BOLD))
    print()
    print(_style("That's the whole idea. To protect your own repo, run this inside it:", DIM))
    print(f"    {_style('becwright init', GREEN)}   "
          f"{_style('# detects your languages, adds starter rules, installs the hook', DIM)}")
    return 0


def _cmd_export(args: argparse.Namespace) -> int:
    root = git.repo_root()
    rule = next((r for r in load_rules(root / ".bec" / "rules.yaml") if r.id == args.rule_id), None)
    if rule is None:
        print(_style(f"No rule with id '{args.rule_id}' in .bec/rules.yaml.", RED), file=sys.stderr)
        return 1
    text = bundle.export_bec(rule, root)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
        print(_style(f"BEC '{rule.id}' exported to {args.output}.", GREEN))
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
    rule_id = rule["id"]
    exported_from = data.get("exported_from", "?")
    print(f"{_style(f'BEC: {rule_id}', BOLD)}  {_style(f'(from {exported_from})', DIM)}")
    if rule.get("intent"):
        print(f"  {_style('Intent:', DIM)} {rule['intent'].strip()}")
    if rule.get("why_it_matters"):
        print(f"  {_style('Why it matters:', DIM)} {rule['why_it_matters'].strip()}")
    kind = check.get("kind")
    print(f"  {_style('Check:', DIM)} {kind}")
    if kind == "script":
        filename = check.get("filename")
        print(f"  {_style(f'Code of {filename}:', DIM)}")
        for line in check.get("source", "").splitlines():
            print(f"      {line}")
    elif kind == "command":
        print(f"  {_style('Command:', DIM)} {check.get('command')}")


def _install_bundle(root: Path, text: str, *, assume_yes: bool) -> int:
    try:
        data = bundle.parse_bundle(text)
    except bundle.BundleError as e:
        print(_style(f"Could not install: {e}", RED), file=sys.stderr)
        return 1

    _print_bundle_summary(data)
    if not assume_yes:
        print(_style("Installing a BEC adds code that runs on every commit.", YELLOW))
        if input("Install this BEC? [y/N] ").strip().lower() not in ("y", "yes"):
            print(_style("Cancelled. Nothing was written.", DIM))
            return 1

    rules_path = root / ".bec" / "rules.yaml"
    rule_id = data["rule"]["id"]
    if rule_id in {r.id for r in load_rules(rules_path)}:
        print(_style(f"A rule with id '{rule_id}' already exists. Not duplicating it.", RED), file=sys.stderr)
        return 1
    try:
        rule_dict = bundle.materialize(data, root)
    except bundle.BundleError as e:
        print(_style(str(e), RED), file=sys.stderr)
        return 1
    bundle.append_rule(rules_path, rule_dict)
    print(_style(f"BEC '{rule_id}' installed in .bec/rules.yaml.", GREEN, BOLD))
    return 0


def _cmd_import(args: argparse.Namespace) -> int:
    root = git.repo_root()
    try:
        text = _read_source(args.source)
    except (OSError, urllib.error.URLError) as e:
        print(_style(f"Could not read '{args.source}': {e}", RED), file=sys.stderr)
        return 1
    return _install_bundle(root, text, assume_yes=args.yes)


def _cmd_add(args: argparse.Namespace) -> int:
    root = git.repo_root()
    try:
        text = catalog.read_bec(args.name)
    except catalog.CatalogError as e:
        print(_style(str(e), RED), file=sys.stderr)
        return 1
    return _install_bundle(root, text, assume_yes=args.yes)


def _cmd_search(args: argparse.Namespace) -> int:
    query = (args.query or "").lower()
    names = [n for n in catalog.catalog_names() if query in n.lower()]
    if not names:
        target = f" matching '{args.query}'" if query else ""
        print(_style(f"No catalog BEC{target}.", YELLOW))
        return 0
    print(f"{_style('Catalog BECs', BOLD)} {_style('(install with: becwright add <name>)', DIM)}")
    for name in names:
        intent = ""
        try:
            data = bundle.parse_bundle(catalog.read_bec(name))
            intent = " ".join((data["rule"].get("intent") or "").split())
        except bundle.BundleError:
            pass
        line = f"  {_style(name, GREEN)}"
        if intent:
            line += f"  {_style(intent, DIM)}"
        print(line)
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
    p_check.add_argument("--json", action="store_true", help="output results as JSON")
    p_check.set_defaults(func=_cmd_check)

    p_init = sub.add_parser("init", help="scaffold a starter .bec/rules.yaml and install the hook")
    p_init.add_argument("--force", action="store_true", help="overwrite an existing .bec/rules.yaml")
    p_init.add_argument("--baseline", action="store_true",
                        help="start rules that already have violations as warning (adopt on dirty code without blocking)")
    p_init.set_defaults(func=_cmd_init)

    p_run = sub.add_parser("run", help="run a built-in check against files on stdin (used inside rules)")
    p_run.add_argument("module", help="built-in check name (see `becwright list`)")
    p_run.add_argument("args", nargs=argparse.REMAINDER, help="arguments forwarded to the check")
    p_run.set_defaults(func=_cmd_run)

    sub.add_parser("demo", help="see becwright block a sample bad commit (no setup, no git needed)").set_defaults(func=_cmd_demo)
    sub.add_parser("list", help="list the built-in checks").set_defaults(func=_cmd_list)
    sub.add_parser("mcp", help="run the MCP server for AI agents (needs the 'mcp' extra)").set_defaults(func=_cmd_mcp)
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

    p_add = sub.add_parser("add", help="install a BEC from the built-in catalog (see `becwright search`)")
    p_add.add_argument("name", help="catalog BEC name")
    p_add.add_argument("--yes", action="store_true", help="install without asking for confirmation")
    p_add.set_defaults(func=_cmd_add)

    p_search = sub.add_parser("search", help="list BECs available in the built-in catalog")
    p_search.add_argument("query", nargs="?", default="", help="optional substring to filter by")
    p_search.set_defaults(func=_cmd_search)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        return args.func(args)
    except (git.NotAGitRepo, RulesError) as e:
        print(_style(str(e), RED), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
