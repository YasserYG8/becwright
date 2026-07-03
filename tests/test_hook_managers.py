import subprocess

from becwright import cli


def _git(root, *args):
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True)


def _init_repo(path):
    _git(path, "init")
    _git(path, "config", "user.email", "t@t.t")
    _git(path, "config", "user.name", "t")
    return path


def _native_hook(root):
    return root / ".git" / "hooks" / "pre-commit"


# --- init ---

def test_init_plain_repo_installs_native_hook(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    (tmp_path / "a.py").write_text("x = 1\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    assert cli.main(["init"]) == 0
    assert _native_hook(tmp_path).exists()


def test_init_with_husky_skips_native_hook(tmp_path, monkeypatch, capsys):
    _init_repo(tmp_path)
    (tmp_path / "a.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / ".husky").mkdir()
    monkeypatch.chdir(tmp_path)
    assert cli.main(["init"]) == 0
    out = capsys.readouterr().out
    assert not _native_hook(tmp_path).exists()
    assert "npx becwright check" in out
    assert (tmp_path / ".bec" / "rules.yaml").exists()  # rules still scaffolded


def test_init_with_precommit_config_skips_native_hook(tmp_path, monkeypatch, capsys):
    _init_repo(tmp_path)
    (tmp_path / "a.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / ".pre-commit-config.yaml").write_text("repos: []\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    assert cli.main(["init"]) == 0
    out = capsys.readouterr().out
    assert not _native_hook(tmp_path).exists()
    assert ".pre-commit-config.yaml" in out
    assert "id: becwright" in out


def test_init_with_hooks_path_override_skips_native_hook(tmp_path, monkeypatch, capsys):
    _init_repo(tmp_path)
    (tmp_path / "a.py").write_text("x = 1\n", encoding="utf-8")
    _git(tmp_path, "config", "core.hooksPath", ".custom-hooks")
    monkeypatch.chdir(tmp_path)
    assert cli.main(["init"]) == 0
    out = capsys.readouterr().out
    assert not _native_hook(tmp_path).exists()
    assert "core.hooksPath" in out


# --- install ---

def test_install_refuses_under_hooks_path_override(tmp_path, monkeypatch, capsys):
    _init_repo(tmp_path)
    _git(tmp_path, "config", "core.hooksPath", ".husky/_")
    (tmp_path / ".husky").mkdir()
    monkeypatch.chdir(tmp_path)
    assert cli.main(["install"]) == 2
    assert not _native_hook(tmp_path).exists()
    assert "never run" in capsys.readouterr().err


def test_install_proceeds_with_precommit_config_but_warns(tmp_path, monkeypatch, capsys):
    _init_repo(tmp_path)
    (tmp_path / ".pre-commit-config.yaml").write_text("repos: []\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    assert cli.main(["install"]) == 0
    out = capsys.readouterr().out
    assert _native_hook(tmp_path).exists()
    assert "pre-commit framework" in out


def test_install_plain_repo_stays_quietly_native(tmp_path, monkeypatch, capsys):
    _init_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    assert cli.main(["install"]) == 0
    assert _native_hook(tmp_path).exists()
    assert "Note:" not in capsys.readouterr().out
