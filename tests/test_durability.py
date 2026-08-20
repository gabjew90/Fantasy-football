import polars as pl

from draftkit.dataset import build_durability


def _weekly(rows):
    return pl.DataFrame(rows, schema={"player_id": pl.Utf8, "season": pl.Int64})


def test_ironman_gets_16():
    # played 17, 17, 17 -> 0 missed -> exp 16
    rows = [{"player_id": "a", "season": s} for s in (2023, 2024, 2025) for _ in range(17)]
    d = build_durability(_weekly(rows), seasons=(2023, 2024, 2025))
    assert d.filter(pl.col("gsis_id") == "a")["exp_games"][0] == 16.0


def test_average_missed_subtracted():
    # played 17, 11, 14 -> missed 0, 6, 3 -> avg 3 -> exp 13
    rows = (
        [{"player_id": "b", "season": 2023} for _ in range(17)]
        + [{"player_id": "b", "season": 2024} for _ in range(11)]
        + [{"player_id": "b", "season": 2025} for _ in range(14)]
    )
    d = build_durability(_weekly(rows), seasons=(2023, 2024, 2025))
    assert d.filter(pl.col("gsis_id") == "b")["exp_games"][0] == 13.0


def test_floor_at_12():
    # played 5, 5, 5 -> avg missed 12 -> 16-12=4 -> floored to 12
    rows = [{"player_id": "c", "season": s} for s in (2023, 2024, 2025) for _ in range(5)]
    d = build_durability(_weekly(rows), seasons=(2023, 2024, 2025))
    assert d.filter(pl.col("gsis_id") == "c")["exp_games"][0] == 12.0


def test_partial_history_averages_only_played_seasons():
    # entered league 2025, played 17 -> avg missed 0 -> 16
    rows = [{"player_id": "d", "season": 2025} for _ in range(17)]
    d = build_durability(_weekly(rows), seasons=(2023, 2024, 2025))
    assert d.filter(pl.col("gsis_id") == "d")["exp_games"][0] == 16.0
