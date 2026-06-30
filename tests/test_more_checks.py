import io

import pytest

from becwright.checks import (
    dangerous_eval,
    debug_remnants,
    hardcoded_secrets,
    wildcard_imports,
)

_ALL = (hardcoded_secrets, debug_remnants, dangerous_eval, wildcard_imports)


def _write(tmp_path, code):
    f = tmp_path / "m.py"
    f.write_text(code, encoding="utf-8")
    return str(f)


def test_secrets_flag_aws_key(tmp_path):
    f = _write(tmp_path, 'key = "AKIA1234567890ABCDEF"\n')
    assert len(hardcoded_secrets.find_violations([f])) == 1


def test_secrets_flag_assigned_literal(tmp_path):
    f = _write(tmp_path, 'password = "hunter2supersecret"\n')
    assert len(hardcoded_secrets.find_violations([f])) == 1


def test_secrets_ignore_env_lookup(tmp_path):
    f = _write(tmp_path, 'api_key = os.environ["API_KEY"]\n')
    assert hardcoded_secrets.find_violations([f]) == []


def test_secrets_ignore_placeholder(tmp_path):
    f = _write(tmp_path, 'password = "changeme"\n')
    assert hardcoded_secrets.find_violations([f]) == []


def test_debug_flags_breakpoint(tmp_path):
    f = _write(tmp_path, "x = 1\nbreakpoint()\n")
    assert len(debug_remnants.find_violations([f])) == 1


def test_debug_flags_pdb_set_trace(tmp_path):
    f = _write(tmp_path, "import pdb; pdb.set_trace()\n")
    assert len(debug_remnants.find_violations([f])) >= 1


def test_debug_clean_code_passes(tmp_path):
    f = _write(tmp_path, "x = compute()\nreturn x\n")
    assert debug_remnants.find_violations([f]) == []


def test_eval_flags_call(tmp_path):
    f = _write(tmp_path, "result = eval(user_input)\n")
    assert len(dangerous_eval.find_violations([f])) == 1


def test_eval_clean_code_passes(tmp_path):
    f = _write(tmp_path, "result = evaluate(user_input)\n")
    assert dangerous_eval.find_violations([f]) == []


def test_wildcard_flags_star_import(tmp_path):
    f = _write(tmp_path, "from os.path import *\n")
    assert len(wildcard_imports.find_violations([f])) == 1


def test_wildcard_explicit_import_passes(tmp_path):
    f = _write(tmp_path, "from os.path import join, exists\n")
    assert wildcard_imports.find_violations([f]) == []


def test_missing_file_is_ignored(tmp_path):
    assert hardcoded_secrets.find_violations(["no/such.py"]) == []
    assert debug_remnants.find_violations(["no/such.py"]) == []
    assert dangerous_eval.find_violations(["no/such.py"]) == []
    assert wildcard_imports.find_violations(["no/such.py"]) == []


_MAIN_CASES = [
    (hardcoded_secrets, 'password = "hunter2supersecret"\n'),
    (debug_remnants, "breakpoint()\n"),
    (dangerous_eval, "eval(payload)\n"),
    (wildcard_imports, "from os import *\n"),
]


@pytest.mark.parametrize("mod, code", _MAIN_CASES)
def test_main_reports_and_exits_one(mod, code, tmp_path, monkeypatch, capsys):
    f = _write(tmp_path, code)
    monkeypatch.setattr("sys.stdin", io.StringIO(f + "\n"))
    rc = mod.main()
    assert rc == 1
    assert f in capsys.readouterr().out


@pytest.mark.parametrize("mod", _ALL)
def test_main_clean_exits_zero(mod, tmp_path, monkeypatch):
    f = _write(tmp_path, "value = compute()\n")
    monkeypatch.setattr("sys.stdin", io.StringIO(f + "\n"))
    assert mod.main() == 0
