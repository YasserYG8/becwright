import io
import re

from becwright.checks import forbid


def _write(tmp_path, code):
    f = tmp_path / "app.js"
    f.write_text(code, encoding="utf-8")
    return str(f)


def test_find_violations_matches(tmp_path):
    f = _write(tmp_path, "x = 1;\nconsole.log('y');\n")
    v = forbid.find_violations([f], r"console\.log\s*\(")
    assert len(v) == 1 and v[0][1] == 2


def test_find_violations_clean(tmp_path):
    f = _write(tmp_path, "const x = 1;\n")
    assert forbid.find_violations([f], r"\bdebugger\b") == []


def test_find_violations_ignore_case(tmp_path):
    f = _write(tmp_path, "TODO: fix\n")
    assert forbid.find_violations([f], "todo", re.IGNORECASE)
    assert forbid.find_violations([f], "todo") == []


def test_missing_file_ignored():
    assert forbid.find_violations(["no/such.js"], "x") == []


def test_main_flags_and_exits_one(tmp_path, monkeypatch, capsys):
    f = _write(tmp_path, "  debugger;\n")
    monkeypatch.setattr("sys.stdin", io.StringIO(f + "\n"))
    rc = forbid.main(["--pattern", r"\bdebugger\b"])
    assert rc == 1 and f in capsys.readouterr().out


def test_main_clean_exits_zero(tmp_path, monkeypatch):
    f = _write(tmp_path, "const x = 1;\n")
    monkeypatch.setattr("sys.stdin", io.StringIO(f + "\n"))
    assert forbid.main(["--pattern", r"\bdebugger\b"]) == 0


def test_main_message_printed(tmp_path, monkeypatch, capsys):
    f = _write(tmp_path, "debugger;\n")
    monkeypatch.setattr("sys.stdin", io.StringIO(f + "\n"))
    forbid.main(["--pattern", r"\bdebugger\b", "--message", "sacá el debugger"])
    assert "sacá el debugger" in capsys.readouterr().out


def test_main_invalid_pattern_exits_two(monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO(""))
    assert forbid.main(["--pattern", "("]) == 2
