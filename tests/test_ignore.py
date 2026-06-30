from becwright.checks import dangerous_eval, debug_remnants, forbid
from becwright.checks._ignore import is_ignored


def test_is_ignored_recognizes_markers():
    assert is_ignored("eval(x)  # becwright: ignore")
    assert is_ignored("eval(x)  // becwright: ignore")
    assert is_ignored("eval(x)  /* BECWRIGHT: IGNORE */")
    assert not is_ignored("eval(x)  # a normal comment")


def test_check_skips_ignored_line(tmp_path):
    f = tmp_path / "a.py"
    f.write_text("eval(a)\nexec(b)  # becwright: ignore\n", encoding="utf-8")
    v = dangerous_eval.find_violations([str(f)])
    assert len(v) == 1 and v[0][1] == 1


def test_all_ignored_means_no_violations(tmp_path):
    f = tmp_path / "a.js"
    f.write_text("debugger;  // becwright: ignore\n", encoding="utf-8")
    assert debug_remnants.find_violations([str(f)]) == []


def test_forbid_honors_directive(tmp_path):
    f = tmp_path / "a.txt"
    f.write_text("TODO now\nTODO later  # becwright: ignore\n", encoding="utf-8")
    v = forbid.find_violations([str(f)], "TODO")
    assert len(v) == 1 and v[0][1] == 1
