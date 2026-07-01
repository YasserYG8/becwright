from becwright import cli


def test_builtin_check_names_includes_known_checks():
    names = cli._builtin_check_names()
    assert "forbid" in names
    assert "hardcoded_secrets" in names
    assert "no_token_in_logs" in names
    assert names == sorted(names)


def test_cmd_list_prints_checks_and_catalog(capsys):
    assert cli.main(["list"]) == 0
    out = capsys.readouterr().out
    assert "forbid" in out
    assert "hardcoded_secrets" in out
    assert "becwright add" in out


def test_every_listed_check_has_a_description():
    for name in cli._builtin_check_names():
        assert name in cli._CHECK_DESCRIPTIONS, f"missing description for {name}"
