import subprocess
from pathlib import Path

from becwright import cli
from becwright.rules import load_rules

_SRC = Path(__file__).resolve().parents[1] / "src"


def _git(root, *args):
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True)


def _init_repo(path):
    _git(path, "init")
    _git(path, "config", "user.email", "t@t.t")
    _git(path, "config", "user.name", "t")
    return path


# --- detection ---

def test_detect_languages_skips_noise_dirs(tmp_path):
    (tmp_path / "a.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "b.ts").write_text("const x = 1\n", encoding="utf-8")
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "c.js").write_text("//\n", encoding="utf-8")
    assert cli._detect_languages(tmp_path) == ["python", "ts"]


def test_detect_languages_none(tmp_path):
    (tmp_path / "README.md").write_text("# hi\n", encoding="utf-8")
    assert cli._detect_languages(tmp_path) == []

def test_detect_languages_go(tmp_path):
    (tmp_path / "main.go").write_text("package main\n", encoding="utf-8")

    assert cli._detect_languages(tmp_path) == ["go"]


def test_detect_languages_rust(tmp_path):
    (tmp_path / "main.rs").write_text("fn main() {}\n", encoding="utf-8")

    assert cli._detect_languages(tmp_path) == ["rust"]

# --- starter rules ---

def test_starter_rules_python():
    ids = [r["id"] for r in cli._starter_rules(["python"])]
    assert ids == ["no-hardcoded-secrets", "no-debug-remnants", "no-dangerous-eval"]


def test_starter_rules_js():
    ids = [r["id"] for r in cli._starter_rules(["js"])]
    assert ids == ["no-hardcoded-secrets", "no-debugger-js", "no-console-log-js"]

def test_starter_rules_go():
    rules = cli._starter_rules(["go"])

    assert [rule["id"] for rule in rules] == [
        "no-hardcoded-secrets",
        "no-debug-go",
    ]

    secrets_rule = rules[0]
    debug_rule = rules[1]

    assert secrets_rule["paths"] == ["**/*.go"]
    assert debug_rule["paths"] == ["**/*.go"]
    assert debug_rule["severity"] == "blocking"
    assert debug_rule["check"] == (
        r"becwright run forbid --pattern 'fmt\.Println\s*\(|panic\s*\('"
    )


def test_starter_rules_rust():
    rules = cli._starter_rules(["rust"])

    assert [rule["id"] for rule in rules] == [
        "no-hardcoded-secrets",
        "no-debug-rust",
    ]

    secrets_rule = rules[0]
    debug_rule = rules[1]

    assert secrets_rule["paths"] == ["**/*.rs"]
    assert debug_rule["paths"] == ["**/*.rs"]
    assert debug_rule["severity"] == "blocking"
    assert debug_rule["check"] == (
        r"becwright run forbid --pattern 'dbg!\s*\(|println!\s*\('"
    )

def test_starter_rules_empty():
    assert cli._starter_rules([]) == []


# --- rendering ---

def test_render_yaml_parses_go_and_rust_forbid_rules(tmp_path):
    rules_path = tmp_path / "rules.yaml"

    rules_path.write_text(
        cli._render_rules_yaml(cli._starter_rules(["go", "rust"])),
        encoding="utf-8",
    )

    rules = load_rules(rules_path)
    rule_ids = {rule.id for rule in rules}

    assert rule_ids == {
        "no-hardcoded-secrets",
        "no-debug-go",
        "no-debug-rust",
    }

def test_render_yaml_parses_and_keeps_forbid(tmp_path):
    p = tmp_path / "rules.yaml"
    p.write_text(cli._render_rules_yaml(cli._starter_rules(["js"])), encoding="utf-8")
    rules = load_rules(p)
    assert {r.id for r in rules} == {"no-hardcoded-secrets", "no-debugger-js", "no-console-log-js"}
    dbg = next(r for r in rules if r.id == "no-debugger-js")
    assert r"--pattern '\bdebugger\b'" in dbg.check


def test_render_empty_is_valid(tmp_path):
    p = tmp_path / "rules.yaml"
    p.write_text(cli._render_rules_yaml([]), encoding="utf-8")
    assert load_rules(p) == []


def test_render_yaml_stamps_schema_version(tmp_path):
    from becwright.rules import RULES_SCHEMA_VERSION

    for rules in ([], cli._starter_rules(["python"])):
        text = cli._render_rules_yaml(rules)
        assert f"schema_version: {RULES_SCHEMA_VERSION}" in text
        p = tmp_path / "rules.yaml"
        p.write_text(text, encoding="utf-8")
        load_rules(p)  # round-trips without raising


def test_render_yaml_emits_exclude(tmp_path):
    rules = [{"id": "no-log", "intent": "x", "why": "y", "paths": ["**/*.ts"],
              "exclude": ["lib/logger.ts"], "check": "true", "severity": "warning"}]
    p = tmp_path / "rules.yaml"
    p.write_text(cli._render_rules_yaml(rules), encoding="utf-8")
    assert load_rules(p)[0].exclude == ("lib/logger.ts",)


# --- the init command ---

def test_init_creates_rules_and_hook(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    (tmp_path / "a.py").write_text("x = 1\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    assert cli.main(["init"]) == 0
    rules_path = tmp_path / ".bec" / "rules.yaml"
    assert "no-debug-remnants" in {r.id for r in load_rules(rules_path)}
    assert (tmp_path / ".git" / "hooks" / "pre-commit").exists()


def test_init_prints_next_steps(tmp_path, monkeypatch, capsys):
    _init_repo(tmp_path)
    (tmp_path / "a.py").write_text("x = 1\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    assert cli.main(["init"]) == 0
    out = capsys.readouterr().out
    assert "Next steps" in out and "becwright check --all" in out


def test_init_refuses_existing(tmp_path, monkeypatch, capsys):
    _init_repo(tmp_path)
    (tmp_path / ".bec").mkdir()
    rules_path = tmp_path / ".bec" / "rules.yaml"
    rules_path.write_text("rules: []\n", encoding="utf-8")
    monkeypatch.setenv("NO_COLOR", "1")
    monkeypatch.setattr(cli.sys.stdout, "isatty", lambda: True)
    monkeypatch.chdir(tmp_path)
    assert cli.main(["init"]) == 1
    assert rules_path.read_text(encoding="utf-8") == "rules: []\n"
    assert "\033[" not in capsys.readouterr().out


def test_init_force_overwrites(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    (tmp_path / "a.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / ".bec").mkdir()
    (tmp_path / ".bec" / "rules.yaml").write_text("rules: []\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    assert cli.main(["init", "--force"]) == 0
    assert load_rules(tmp_path / ".bec" / "rules.yaml")


def test_init_generated_rule_blocks_via_check(tmp_path, monkeypatch):
    monkeypatch.setenv("PYTHONPATH", str(_SRC))
    _init_repo(tmp_path)
    (tmp_path / "app.js").write_text("function f(){ debugger; }\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    assert cli.main(["init"]) == 0
    _git(tmp_path, "add", "app.js")
    assert cli.main(["check", "--all"]) == 1


# --- baseline adoption ---

def test_init_baseline_downgrades_dirty_rules_only(tmp_path, monkeypatch):
    monkeypatch.setenv("PYTHONPATH", str(_SRC))
    _init_repo(tmp_path)
    (tmp_path / "app.py").write_text("breakpoint()\n", encoding="utf-8")   # trips no-debug-remnants
    (tmp_path / "clean.py").write_text("x = 1\n", encoding="utf-8")
    _git(tmp_path, "add", "app.py", "clean.py")
    monkeypatch.chdir(tmp_path)
    assert cli.main(["init", "--baseline"]) == 0
    rules = {r.id: r for r in load_rules(tmp_path / ".bec" / "rules.yaml")}
    assert rules["no-debug-remnants"].severity == "warning"      # dirty -> warning
    assert rules["no-hardcoded-secrets"].severity == "blocking"  # clean -> stays blocking


def test_init_baseline_writes_note_and_summary(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("PYTHONPATH", str(_SRC))
    _init_repo(tmp_path)
    (tmp_path / "app.py").write_text("breakpoint()\n", encoding="utf-8")
    _git(tmp_path, "add", "app.py")
    monkeypatch.chdir(tmp_path)
    assert cli.main(["init", "--baseline"]) == 0
    out = capsys.readouterr().out
    assert "started as warning" in out and "no-debug-remnants" in out
    assert "graduate to blocking" in (tmp_path / ".bec" / "rules.yaml").read_text(encoding="utf-8")


def test_init_baseline_clean_repo_keeps_all_blocking(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("PYTHONPATH", str(_SRC))
    _init_repo(tmp_path)
    (tmp_path / "clean.py").write_text("x = 1\n", encoding="utf-8")
    _git(tmp_path, "add", "clean.py")
    monkeypatch.chdir(tmp_path)
    assert cli.main(["init", "--baseline"]) == 0
    rules = load_rules(tmp_path / ".bec" / "rules.yaml")
    assert rules and all(r.is_blocking for r in rules)
    assert "clean repo" in capsys.readouterr().out


def test_init_without_baseline_keeps_default_severity(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    (tmp_path / "app.py").write_text("breakpoint()\n", encoding="utf-8")
    _git(tmp_path, "add", "app.py")
    monkeypatch.chdir(tmp_path)
    assert cli.main(["init"]) == 0
    rules = {r.id: r for r in load_rules(tmp_path / ".bec" / "rules.yaml")}
    assert rules["no-debug-remnants"].severity == "blocking"


# --- deriving rules from CLAUDE.md ---

def test_read_claude_md_finds_and_misses(tmp_path):
    assert cli._read_claude_md(tmp_path) is None
    (tmp_path / "CLAUDE.md").write_text("no secrets\n", encoding="utf-8")
    assert cli._read_claude_md(tmp_path) == "no secrets\n"


def test_rules_from_claude_md_maps_signals_by_language():
    text = "Never hardcode secrets. No console.log in the code. Avoid debugger."
    ids = {r["id"] for r, _ in cli._rules_from_claude_md(text, ["ts"])}
    assert ids == {"no-hardcoded-secrets", "no-console-log-js", "no-debugger-js"}


def test_rules_from_claude_md_gates_python_only_signals():
    text = "Do not leave breakpoint() or pdb; avoid import * as well."
    assert cli._rules_from_claude_md(text, ["ts"]) == []   # no Python detected
    py = {r["id"] for r, _ in cli._rules_from_claude_md(text, ["python"])}
    assert py == {"no-debug-remnants", "no-wildcard-imports"}


def test_rules_from_claude_md_no_enforceable_signals():
    assert cli._rules_from_claude_md("Keep functions small and cohesive.", ["python"]) == []


def test_init_from_claude_md_creates_derived_rules(tmp_path, monkeypatch, capsys):
    _init_repo(tmp_path)
    (tmp_path / "app.ts").write_text("const x = 1\n", encoding="utf-8")
    (tmp_path / "CLAUDE.md").write_text(
        "# Rules\n- Never hardcode secrets or API keys.\n- No console.log in shipped code.\n",
        encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    assert cli.main(["init", "--from-claude-md"]) == 0
    ids = {r.id for r in load_rules(tmp_path / ".bec" / "rules.yaml")}
    assert ids == {"no-hardcoded-secrets", "no-console-log-js"}
    out = capsys.readouterr().out
    assert "From CLAUDE.md" in out and "matched:" in out


def test_init_from_claude_md_without_file(tmp_path, monkeypatch, capsys):
    _init_repo(tmp_path)
    (tmp_path / "a.py").write_text("x = 1\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    assert cli.main(["init", "--from-claude-md"]) == 1
    assert "No CLAUDE.md" in capsys.readouterr().out
    assert not (tmp_path / ".bec" / "rules.yaml").exists()


def test_init_from_claude_md_no_signals_writes_nothing(tmp_path, monkeypatch, capsys):
    _init_repo(tmp_path)
    (tmp_path / "a.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "CLAUDE.md").write_text("Keep it simple. Prefer small functions.\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    assert cli.main(["init", "--from-claude-md"]) == 1
    assert "nothing I can enforce" in capsys.readouterr().out
    assert not (tmp_path / ".bec" / "rules.yaml").exists()


def test_max_lines_cap_extracts_file_cap():
    assert cli._max_lines_cap("Files are focused (< 800 lines).") == 800
    assert cli._max_lines_cap("Máximo 300 líneas por archivo.") == 300
    assert cli._max_lines_cap("800 lines per file max") == 800


def test_max_lines_cap_ignores_function_length():
    # No file/module anchor -> not a file cap (function length needs an AST anyway).
    assert cli._max_lines_cap("Functions must be under 50 lines.") is None


def test_max_lines_cap_out_of_range():
    assert cli._max_lines_cap("keep files under 40 lines") is None      # below 50
    assert cli._max_lines_cap("files must not exceed 9000 lines") is None  # above 5000


def test_rules_from_claude_md_maps_file_line_cap():
    text = "Keep files under 800 lines. Never hardcode secrets."
    by_id = {r["id"]: r for r, _ in cli._rules_from_claude_md(text, ["python"])}
    assert "max-file-lines" in by_id
    assert by_id["max-file-lines"]["check"] == "becwright run max_lines --max 800"
    assert by_id["max-file-lines"]["severity"] == "warning"


def test_rules_from_claude_md_good_practices_expands_hygiene():
    derived = cli._rules_from_claude_md("Always follow good practices.", ["python", "ts"])
    ids = {r["id"] for r, _ in derived}
    assert {"no-hardcoded-secrets", "no-dangerous-eval", "no-debug-remnants",
            "no-debugger-js", "no-console-log-js", "no-conflict-markers"} <= ids
    # opinionated/narrow signals are not pulled in by the broad phrase
    assert "no-wildcard-imports" not in ids and "no-token-in-logs" not in ids


def test_rules_from_claude_md_conflict_markers_on_explicit_mention():
    ids = {r["id"] for r, _ in cli._rules_from_claude_md(
        "Never commit merge conflict markers.", ["python"])}
    assert ids == {"no-conflict-markers"}


def test_rules_from_claude_md_maps_commit_message_rules():
    text = "Use conventional commits. No AI attribution in commit messages."
    by_id = {r["id"]: r for r, _ in cli._rules_from_claude_md(text, ["python"])}
    assert by_id["conventional-commits"]["target"] == "commit-msg"
    assert by_id["no-ai-attribution"]["target"] == "commit-msg"
    assert "paths" not in by_id["conventional-commits"]


def test_render_yaml_emits_commit_msg_rule(tmp_path):
    rules = [{"id": "conv", "intent": "x", "why": "y", "target": "commit-msg",
              "check": "becwright run require --pattern '^feat'", "severity": "blocking"}]
    p = tmp_path / "rules.yaml"
    p.write_text(cli._render_rules_yaml(rules), encoding="utf-8")
    loaded = load_rules(p)
    assert loaded[0].target == "commit-msg" and loaded[0].paths == ()


def test_rules_from_claude_md_good_practices_keeps_specific_trigger():
    # a specific mention wins the trigger label, and the rule is not duplicated
    derived = cli._rules_from_claude_md(
        "No hardcoded secrets. Follow good practices.", ["python"])
    secrets = [(r, t) for r, t in derived if r["id"] == "no-hardcoded-secrets"]
    assert len(secrets) == 1 and secrets[0][1] == "hardcod"


def test_init_from_claude_md_composes_with_baseline(tmp_path, monkeypatch):
    monkeypatch.setenv("PYTHONPATH", str(_SRC))
    _init_repo(tmp_path)
    (tmp_path / "app.py").write_text("breakpoint()\n", encoding="utf-8")
    (tmp_path / "CLAUDE.md").write_text(
        "No breakpoint or pdb left in code. Never hardcode secrets.\n", encoding="utf-8")
    _git(tmp_path, "add", "app.py")
    monkeypatch.chdir(tmp_path)
    assert cli.main(["init", "--from-claude-md", "--baseline"]) == 0
    rules = {r.id: r for r in load_rules(tmp_path / ".bec" / "rules.yaml")}
    assert "no-debug-remnants" in rules and "no-hardcoded-secrets" in rules
    assert rules["no-debug-remnants"].severity == "warning"    # dirty -> warning
    assert rules["no-hardcoded-secrets"].severity == "blocking"  # clean -> blocking
