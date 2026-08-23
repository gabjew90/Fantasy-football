"""Three-lens scoreboard (season spec Task 7)."""

from draftkit.lenses import LENSES, scoreboard_md, spearman


def test_spearman_identity_and_reversal():
    assert spearman([1, 2, 3, 4], [1, 2, 3, 4]) == 1.0
    assert spearman([1, 2, 3, 4], [4, 3, 2, 1]) == -1.0


def test_scoreboard_renders_all_teams():
    actual = {t: 100.0 - i for i, t in enumerate(LENSES)}  # our-board order = reality
    md = scoreboard_md(actual)
    assert md.count("|") > 12 * 5
    assert "our board: **+1.00**" in md


def test_scoreboard_needs_data():
    assert "not enough" in scoreboard_md({"farmerjamal": 100.0})
