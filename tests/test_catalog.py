import subprocess

import pytest

from becwright import catalog, cli


def _git(root, *args):
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True)


def _repo(tmp_path):
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "t@t.t")
    _git(tmp_path, "config", "user.name", "t")
    return tmp_path


# --- catalog module ---

def test_catalog_lists_shipped_becs():
    names = catalog.catalog_names()
    assert "no-token-in-logs" in names
    assert "no-console-log-js" in names
    assert all(not n.endswith(".bec.yaml") for n in names)


def test_read_bec_returns_a_valid_bundle():
    text = catalog.read_bec("no-token-in-logs")
    assert "becwright_bec" in text


def test_read_unknown_bec_raises():
    with pytest.raises(catalog.CatalogError, match="No BEC named"):
        catalog.read_bec("does-not-exist")


# --- search subcommand ---

def test_search_lists_all(capsys):
    assert cli.main(["search"]) == 0
    assert "no-token-in-logs" in capsys.readouterr().out


def test_search_filters_by_substring(capsys):
    assert cli.main(["search", "console"]) == 0
    out = capsys.readouterr().out
    assert "no-console-log-js" in out and "no-token-in-logs" not in out


def test_search_no_match(capsys):
    assert cli.main(["search", "zzzz"]) == 0
    assert "No catalog BEC" in capsys.readouterr().out


# --- add subcommand ---

def test_add_installs_from_catalog(tmp_path, monkeypatch, capsys):
    _repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    assert cli.main(["add", "no-token-in-logs", "--yes"]) == 0
    rules = (tmp_path / ".bec" / "rules.yaml").read_text(encoding="utf-8")
    assert "no-token-in-logs" in rules
    assert "installed" in capsys.readouterr().out


def test_add_refuses_duplicate(tmp_path, monkeypatch):
    _repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    assert cli.main(["add", "no-token-in-logs", "--yes"]) == 0
    assert cli.main(["add", "no-token-in-logs", "--yes"]) == 1


def test_add_unknown_name(tmp_path, monkeypatch, capsys):
    _repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    assert cli.main(["add", "nope", "--yes"]) == 1
    assert "No BEC named" in capsys.readouterr().err
