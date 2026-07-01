import io

from becwright.checks import conflict_markers, filename, max_lines, require


def _write(tmp_path, name, text):
    f = tmp_path / name
    f.write_text(text, encoding="utf-8")
    return str(f)


# --- max_lines ---

def test_max_lines_flags_files_over_cap(tmp_path):
    big = _write(tmp_path, "big.py", "\n".join(f"x{i} = {i}" for i in range(60)) + "\n")
    small = _write(tmp_path, "small.py", "x = 1\n")
    v = max_lines.find_violations([big, small], 50)
    assert v == [(big, 60)]


def test_max_lines_boundary_is_inclusive(tmp_path):
    exact = _write(tmp_path, "exact.py", "".join("a\n" for _ in range(50)))
    assert max_lines.find_violations([exact], 50) == []


def test_max_lines_skips_unreadable(tmp_path):
    assert max_lines.find_violations(["nope.py", ""], 10) == []


def test_max_lines_main(tmp_path, monkeypatch, capsys):
    big = _write(tmp_path, "big.py", "a\n" * 30)
    monkeypatch.setattr("sys.stdin", io.StringIO(big + "\n"))
    assert max_lines.main(["--max", "10"]) == 1
    assert "30 lines (max 10)" in capsys.readouterr().out


def test_max_lines_main_rejects_non_positive(monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO(""))
    assert max_lines.main(["--max", "0"]) == 2


# --- require ---

def test_require_flags_files_missing_pattern(tmp_path):
    with_header = _write(tmp_path, "a.py", "# SPDX-License-Identifier: MIT\nx = 1\n")
    without = _write(tmp_path, "b.py", "x = 1\n")
    missing = require.find_violations([with_header, without], "SPDX-License-Identifier")
    assert missing == [without]


def test_require_main_reports_missing(tmp_path, monkeypatch, capsys):
    f = _write(tmp_path, "b.py", "x = 1\n")
    monkeypatch.setattr("sys.stdin", io.StringIO(f + "\n"))
    assert require.main(["--pattern", "LICENSE", "--message", "add a header"]) == 1
    out = capsys.readouterr().out
    assert "add a header" in out and "required pattern not found" in out


def test_require_main_clean_exits_zero(tmp_path, monkeypatch):
    f = _write(tmp_path, "a.py", "LICENSE: MIT\n")
    monkeypatch.setattr("sys.stdin", io.StringIO(f + "\n"))
    assert require.main(["--pattern", "LICENSE"]) == 0


def test_require_main_invalid_pattern_exits_two(monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO(""))
    assert require.main(["--pattern", "("]) == 2


# --- filename ---

def test_filename_forbid_matches_basename(tmp_path):
    bad = _write(tmp_path, "constantes.ts", "x\n")
    ok = _write(tmp_path, "constants.ts", "x\n")
    v = filename.find_violations([bad, ok], forbid=r"constantes")
    assert len(v) == 1 and v[0][0] == bad


def test_filename_require_convention(tmp_path):
    kebab = _write(tmp_path, "user-card.ts", "x\n")
    pascal = _write(tmp_path, "UserCard.ts", "x\n")
    v = filename.find_violations([kebab, pascal], require=r"^[a-z0-9-]+\.[a-z]+$")
    assert len(v) == 1 and v[0][0] == pascal


def test_filename_opens_no_files():
    # Paths need not exist: the check only inspects the name.
    assert filename.find_violations(["src/BadName.ts"], forbid=r"[A-Z]")


def test_filename_main_needs_a_pattern(monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO(""))
    assert filename.main([]) == 2


def test_filename_main_flags_and_exits_one(tmp_path, monkeypatch, capsys):
    bad = _write(tmp_path, "tipos.ts", "x\n")
    monkeypatch.setattr("sys.stdin", io.StringIO(bad + "\n"))
    assert filename.main(["--forbid", "tipos"]) == 1
    assert "forbidden pattern" in capsys.readouterr().out


# --- conflict_markers ---

def test_conflict_markers_flags_angle_markers(tmp_path):
    f = _write(tmp_path, "a.py", "x = 1\n<<<<<<< HEAD\ny = 2\n>>>>>>> branch\n")
    v = conflict_markers.find_violations([f])
    assert {ln for _p, ln, _l in v} == {2, 4}


def test_conflict_markers_ignores_markdown_underline(tmp_path):
    # `=======` is a legit Markdown h1 underline; only angle/pipe markers are flagged.
    f = _write(tmp_path, "r.md", "Title\n=======\nbody\n")
    assert conflict_markers.find_violations([f]) == []


def test_conflict_markers_main(tmp_path, monkeypatch, capsys):
    f = _write(tmp_path, "a.py", "||||||| base\n")
    monkeypatch.setattr("sys.stdin", io.StringIO(f + "\n"))
    assert conflict_markers.main() == 1
    assert f in capsys.readouterr().out
