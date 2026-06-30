import sys
from pathlib import Path

from becwright.engine import evaluate
from becwright.rules import Rule

_SRC = Path(__file__).resolve().parents[1] / "src"


def _check_cmd(module: str) -> str:
    return f'PYTHONPATH="{_SRC}" "{sys.executable}" -m becwright.checks.{module}'


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
