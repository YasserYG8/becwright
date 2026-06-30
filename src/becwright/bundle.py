from __future__ import annotations

import re
import subprocess
import textwrap
from pathlib import Path

import yaml

from .rules import Rule

BUNDLE_VERSION = 1

_BUILTIN = re.compile(r"^python3?\s+-m\s+becwright\.checks\.(\w+)$")
_PY_PATH = re.compile(r"[\w./-]+\.py")
_ITEM_INDENT = re.compile(r"^([ \t]+)-\s", re.MULTILINE)
_EMPTY_RULES = re.compile(r"^rules:[ \t]*(?:\[[ \t]*\]|\{[ \t]*\})[ \t]*$", re.MULTILINE)


class BundleError(RuntimeError):
    pass


def _clean(value):
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return [v.strip() if isinstance(v, str) else v for v in value]
    return value


def _origin(root: Path) -> str:
    res = subprocess.run(
        ["git", "config", "--get", "remote.origin.url"],
        cwd=root, capture_output=True, text=True,
    )
    return res.stdout.strip() or root.name


def classify_check(command: str, root: Path) -> dict:
    command = command.strip()
    builtin = _BUILTIN.match(command)
    if builtin:
        return {"kind": "builtin", "module": builtin.group(1)}
    for token in _PY_PATH.findall(command):
        candidate = root / token
        if candidate.is_file():
            return {
                "kind": "script",
                "filename": Path(token).name,
                "source": candidate.read_text(encoding="utf-8"),
            }
    return {"kind": "command", "command": command}


def export_bec(rule: Rule, root: Path) -> str:
    rule_fields: dict = {"id": rule.id}
    if rule.intent:
        rule_fields["intent"] = rule.intent
    if rule.why_it_matters:
        rule_fields["why_it_matters"] = rule.why_it_matters
    if rule.rejected_alternatives:
        rule_fields["rejected_alternatives"] = list(rule.rejected_alternatives)
    rule_fields["paths"] = list(rule.paths)
    rule_fields["severity"] = rule.severity

    bundle = {
        "becwright_bec": BUNDLE_VERSION,
        "exported_from": _origin(root),
        "rule": rule_fields,
        "check": classify_check(rule.check, root),
    }
    return yaml.safe_dump(bundle, sort_keys=False, allow_unicode=True)


def parse_bundle(text: str) -> dict:
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as e:
        raise BundleError(f"El bundle no es YAML válido: {e}")
    if not isinstance(data, dict):
        raise BundleError("El bundle está vacío o malformado.")
    if data.get("becwright_bec") != BUNDLE_VERSION:
        raise BundleError(
            f"Versión de bundle no soportada: {data.get('becwright_bec')!r} "
            f"(esperaba {BUNDLE_VERSION})."
        )
    rule = data.get("rule")
    check = data.get("check")
    if not isinstance(rule, dict) or "id" not in rule:
        raise BundleError("El bundle no tiene una regla válida (falta 'rule.id').")
    if not isinstance(check, dict) or "kind" not in check:
        raise BundleError("El bundle no tiene un check válido (falta 'check.kind').")
    required = {"builtin": ("module",), "script": ("filename", "source"), "command": ("command",)}
    kind = check["kind"]
    if kind not in required:
        raise BundleError(f"Tipo de check desconocido: {kind!r}.")
    missing = [f for f in required[kind] if not check.get(f)]
    if missing:
        raise BundleError(f"El check '{kind}' no tiene los campos: {', '.join(missing)}.")
    return data


def materialize(bundle: dict, root: Path) -> dict:
    check = bundle["check"]
    kind = check.get("kind")
    if kind == "builtin":
        command = f"python3 -m becwright.checks.{check['module']}"
    elif kind == "script":
        filename = Path(check["filename"]).name
        dest = root / ".bec" / "checks" / filename
        source = check["source"]
        if dest.exists() and dest.read_text(encoding="utf-8") != source:
            raise BundleError(
                f"Ya existe un check distinto en {dest}. No lo piso; resolvé a mano."
            )
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(source, encoding="utf-8")
        dest.chmod(0o755)
        command = f"python3 .bec/checks/{filename}"
    elif kind == "command":
        command = check["command"]
    else:
        raise BundleError(f"Tipo de check desconocido: {kind!r}")

    rule = bundle["rule"]
    out: dict = {"id": rule["id"]}
    for key in ("intent", "why_it_matters", "rejected_alternatives"):
        if rule.get(key):
            out[key] = _clean(rule[key])
    out["paths"] = rule.get("paths", [])
    out["check"] = command
    out["severity"] = rule.get("severity", "blocking")
    return out


def append_rule(rules_path: Path, rule_dict: dict) -> None:
    dumped = yaml.safe_dump([rule_dict], sort_keys=False, allow_unicode=True)
    if not rules_path.exists():
        rules_path.parent.mkdir(parents=True, exist_ok=True)
        rules_path.write_text("rules:\n" + textwrap.indent(dumped, "  "), encoding="utf-8")
        return
    # Normalize an empty inline list (`rules: []`) so block items can follow it.
    text = _EMPTY_RULES.sub("rules:", rules_path.read_text(encoding="utf-8"), count=1)
    if text and not text.endswith("\n"):
        text += "\n"
    if not re.search(r"^rules:", text, re.MULTILINE):
        text += "rules:\n"
    # Match the indentation the file already uses for list items.
    existing = _ITEM_INDENT.search(text)
    prefix = existing.group(1) if existing else "  "
    rules_path.write_text(text + textwrap.indent(dumped, prefix), encoding="utf-8")
