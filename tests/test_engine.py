from becwright.engine import matches


def test_double_star_covers_zero_dirs():
    assert matches("src/auth.py", ("src/**/*.py",))


def test_double_star_covers_several_dirs():
    assert matches("src/handlers/admin/users.py", ("src/handlers/**/*.py",))


def test_single_star_does_not_cross_slash():
    assert not matches("src/sub/auth.py", ("src/*.py",))


def test_does_not_match_other_extension():
    assert not matches("src/auth.txt", ("src/**/*.py",))


def test_matches_when_any_pattern_hits():
    assert matches("README.md", ("src/**/*.py", "*.md"))
