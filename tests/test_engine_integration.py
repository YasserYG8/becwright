import sys
from pathlib import Path

from becwright.engine import evaluate, evaluate_message
from becwright.rules import Rule

_SRC = Path(__file__).resolve().parents[1] / "src"


def _check_cmd(module: str) -> str:
    src_posix = _SRC.as_posix()
    return f'"{sys.executable}" -c "import sys; sys.path.insert(0, \'{src_posix}\'); from becwright.checks.{module} import main; sys.exit(main())"'


def _rule() -> Rule:
    return Rule(
        id="no-debug",
        paths=("**/*.py",),
        check=_check_cmd("debug_remnants"),
        severity="blocking",
    )


def test_evaluate_blocks_on_violation(tmp_path):
    (tmp_path / "bad.py").write_text("breakpoint()\n", encoding="utf-8")
    result = evaluate([_rule()], ["bad.py"], tmp_path)
    assert len(result.per_rule) == 1
    assert result.per_rule[0].passed is False
    assert result.had_blocking is True
    assert "bad.py" in result.per_rule[0].output


def test_evaluate_passes_clean_code(tmp_path):
    (tmp_path / "ok.py").write_text("x = compute()\n", encoding="utf-8")
    result = evaluate([_rule()], ["ok.py"], tmp_path)
    assert result.per_rule[0].passed is True
    assert result.had_blocking is False


def test_evaluate_skips_rule_with_no_matching_files(tmp_path):
    (tmp_path / "note.txt").write_text("breakpoint()\n", encoding="utf-8")
    result = evaluate([_rule()], ["note.txt"], tmp_path)
    assert result.per_rule == []


def _rule_excluding(*globs: str) -> Rule:
    return Rule(
        id="no-debug",
        paths=("**/*.py",),
        exclude=globs,
        check=_check_cmd("debug_remnants"),
        severity="blocking",
    )


def test_evaluate_carves_out_excluded_file(tmp_path):
    # The excluded file is the only match, so the rule has nothing left to run on.
    (tmp_path / "logger.py").write_text("breakpoint()\n", encoding="utf-8")
    result = evaluate([_rule_excluding("logger.py")], ["logger.py"], tmp_path)
    assert result.per_rule == []


def test_evaluate_exclude_keeps_checking_other_files(tmp_path):
    (tmp_path / "logger.py").write_text("breakpoint()\n", encoding="utf-8")
    (tmp_path / "app.py").write_text("breakpoint()\n", encoding="utf-8")
    result = evaluate([_rule_excluding("logger.py")], ["logger.py", "app.py"], tmp_path)
    assert result.had_blocking is True
    assert "app.py" in result.per_rule[0].output
    assert "logger.py" not in result.per_rule[0].output


def _msg_rule(pattern: str) -> Rule:
    check = f'{_check_cmd("require")} --pattern "{pattern}"'
    return Rule(id="conv", paths=(), target="commit-msg", check=check, severity="blocking")


def test_evaluate_message_blocks_when_pattern_missing(tmp_path):
    msg = tmp_path / "MSG"
    msg.write_text("update stuff\n", encoding="utf-8")
    result = evaluate_message([_msg_rule("^(feat|fix): ")], str(msg), tmp_path)
    assert result.per_rule[0].passed is False and result.had_blocking is True


def test_evaluate_message_passes_good_message(tmp_path):
    msg = tmp_path / "MSG"
    msg.write_text("feat: add the thing\n", encoding="utf-8")
    result = evaluate_message([_msg_rule("^(feat|fix): ")], str(msg), tmp_path)
    assert result.per_rule[0].passed is True


def test_evaluate_message_ignores_file_rules(tmp_path):
    file_rule = Rule(id="f", paths=("**/*.py",), check="false", severity="blocking")
    assert evaluate_message([file_rule], "MSG", tmp_path).per_rule == []


def test_evaluate_ignores_commit_msg_rules(tmp_path):
    (tmp_path / "a.py").write_text("x = 1\n", encoding="utf-8")
    msg_rule = Rule(id="conv", paths=("**/*.py",), target="commit-msg",
                    check="false", severity="blocking")
    assert evaluate([msg_rule], ["a.py"], tmp_path).per_rule == []


def test_evaluate_times_out_a_hung_check(tmp_path, monkeypatch):
    monkeypatch.setenv("BECWRIGHT_CHECK_TIMEOUT", "0.3")
    (tmp_path / "a.py").write_text("x = 1\n", encoding="utf-8")
    check = f'"{sys.executable}" -c "import time; time.sleep(5)"'
    hung = Rule(id="hangs", paths=("**/*.py",), check=check, severity="blocking")
    result = evaluate([hung], ["a.py"], tmp_path)
    assert result.per_rule[0].passed is False
    assert "timed out" in result.per_rule[0].output
    assert result.had_blocking is True


def test_evaluate_captures_both_stdout_and_stderr(tmp_path):
    (tmp_path / "a.py").write_text("x = 1\n", encoding="utf-8")
    check = f'"{sys.executable}" -c "import sys; print(\'out_msg\'); print(\'err_msg\', file=sys.stderr); sys.exit(1)"'
    rule = Rule(id="both", paths=("**/*.py",), check=check, severity="blocking")
    result = evaluate([rule], ["a.py"], tmp_path)
    assert result.per_rule[0].passed is False
    assert "out_msg" in result.per_rule[0].output
    assert "err_msg" in result.per_rule[0].output

