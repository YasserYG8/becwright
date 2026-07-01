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
