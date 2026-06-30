from becwright.checks.no_token_in_logs import find_violations


def test_detects_token_in_log(tmp_path):
    f = tmp_path / "auth.py"
    f.write_text('logger.info("session_token=" + token)\n', encoding="utf-8")
    violations = find_violations([str(f)])
    assert len(violations) == 1
    assert violations[0][0] == str(f)


def test_clean_code_does_not_fire(tmp_path):
    f = tmp_path / "auth.py"
    f.write_text('logger.info("usuario autenticado")\n', encoding="utf-8")
    assert find_violations([str(f)]) == []


def test_missing_file_is_ignored():
    assert find_violations(["no/such.py"]) == []
