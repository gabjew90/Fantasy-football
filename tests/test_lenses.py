"""Three-lens scoreboard (season spec Task 7; league-scoped since 2026-08-31)."""

from draftkit.config import Config
from draftkit.lenses import load_lenses, scoreboard_md, spearman


def test_spearman_identity_and_reversal():
    assert spearman([1, 2, 3, 4], [1, 2, 3, 4]) == 1.0
    assert spearman([1, 2, 3, 4], [4, 3, 2, 1]) == -1.0


def test_scoreboard_renders_all_teams():
    cfg = Config.load()                       # omnibeta carries the lenses block
    lenses = load_lenses(cfg)
    assert len(lenses) == 12
    actual = {t: 100.0 - i for i, t in enumerate(lenses)}  # our-board order = reality
    md = scoreboard_md(actual, cfg)
    assert md.count("|") > 12 * 5
    assert "our board: **+1.00**" in md


def test_scoreboard_needs_data():
    cfg = Config.load()
    assert "not enough" in scoreboard_md({"farmerjamal": 100.0}, cfg)


def test_scoreboard_without_a_league_block_is_off_not_borrowed():
    md = scoreboard_md({"a": 1.0, "b": 2.0, "c": 3.0}, cfg=None)
    assert "off for this league" in md
