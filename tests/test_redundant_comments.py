from becwright.checks.redundant_comments import find_violations


def _write(tmp_path, code):
    f = tmp_path / "m.py"
    f.write_text(code, encoding="utf-8")
    return str(f)


def test_flags_comment_that_restates_code(tmp_path):
    f = _write(tmp_path, "# increment counter\ncounter += increment\n")
    assert len(find_violations([f])) == 1


def test_keeps_why_comment_over_simple_code(tmp_path):
    code = "# Marker so we can later recognize a hook we wrote ourselves.\nmark = 1\n"
    assert find_violations([_write(tmp_path, code)]) == []


def test_ignores_hash_inside_string(tmp_path):
    code = 's = "# increment counter"\ncounter = 1\n'
    assert find_violations([_write(tmp_path, code)]) == []


def test_ignores_pragma_comment(tmp_path):
    code = "x = call()  # type: ignore\n"
    assert find_violations([_write(tmp_path, code)]) == []


def test_ignores_shebang(tmp_path):
    code = "#!/usr/bin/env python3\nx = 1\n"
    assert find_violations([_write(tmp_path, code)]) == []
