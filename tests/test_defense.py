"""Defense-quality metric (post-v2 item 2): shrinkage and degrade behaviour."""

import polars as pl

from draftkit.defense import allowed_ratio, schedule_strength


def _pa(rows):
    return pl.DataFrame(
        [{"defense": d, "pos": p, "allowed_pg": a, "games": g} for d, p, a, g in rows],
        schema={"defense": pl.Utf8, "pos": pl.Utf8, "allowed_pg": pl.Float64, "games": pl.Int64},
    )


PA = _pa([(f"T{i}", "RB", 20.0, 6) for i in range(8)]
         + [("SOFT", "RB", 30.0, 6), ("TOUGH", "RB", 10.0, 6)])


def test_points_allowed_scores_sleeper_keys_through_the_nflverse_map(monkeypatch):
    """2026-09-10, week 2: build_context died on ColumnNotFoundError("sack").
    points_allowed() is fed Sleeper's scoring_settings and handed the Sleeper
    keys to pl.col. Preseason the frame was empty and it never scored a row.
    Sleeper keys must go through the map; a half-PPR league must score its
    receptions at 0.5; a key nflverse has no column for is dropped."""
    import draftkit.defense as dmod

    wk = pl.DataFrame({
        "season_type": ["REG", "REG", "REG", "REG"],
        "week": [1, 1, 2, 2],
        "position": ["WR", "WR", "WR", "WR"],
        "opponent_team": ["DAL", "DAL", "DAL", "DAL"],
        "receptions": [10.0, 0.0, 10.0, 0.0],
        "receiving_yards": [0.0, 0.0, 0.0, 0.0],
        "receiving_tds": [0.0, 0.0, 0.0, 0.0],
        "passing_yards": [0.0] * 4, "passing_tds": [0.0] * 4,
        "passing_interceptions": [0.0] * 4, "rushing_yards": [0.0] * 4,
        "rushing_tds": [0.0] * 4, "passing_2pt_conversions": [0.0] * 4,
        "rushing_2pt_conversions": [0.0] * 4, "receiving_2pt_conversions": [0.0] * 4,
        "sack_fumbles_lost": [0.0] * 4, "rushing_fumbles_lost": [0.0] * 4,
        "receiving_fumbles_lost": [0.0] * 4, "special_teams_tds": [0.0] * 4,
    })

    class FakeNfl:
        @staticmethod
        def load_player_stats(seasons):
            return wk

    monkeypatch.setitem(__import__("sys").modules, "nflreadpy", FakeNfl)
    sleeper = {"rec": 0.5, "pass_yd": 0.04, "sack": 1.0, "def_td": 6.0, "bonus_rec_te": 1.0}
    pa = dmod.points_allowed(2026, sleeper)
    assert pa is not None
    row = pa.filter((pl.col("defense") == "DAL") & (pl.col("pos") == "WR")).row(0, named=True)
    assert row["allowed_pg"] == 5.0 and row["games"] == 2   # 10 rec x 0.5 per week

    # a column the frame lacks is DATA MISSING, not a crash
    monkeypatch.setitem(__import__("sys").modules, "nflreadpy",
                        type("N", (), {"load_player_stats": staticmethod(lambda s: wk.drop("receptions"))}))
    assert dmod.points_allowed(2026, sleeper) is None


def test_ratio_is_relative_to_league_average_and_shrunk():
    soft = allowed_ratio(PA, "SOFT", "RB", shrink_k=5)
    tough = allowed_ratio(PA, "TOUGH", "RB", shrink_k=5)
    assert soft is not None and tough is not None
    assert soft > 1.0 > tough                      # direction
    raw_soft = 30.0 / float(PA.filter(pl.col("pos") == "RB")["allowed_pg"].mean())
    assert soft < raw_soft                          # shrunk toward 1.0
    # 6 games, k=5 -> weight 6/11; check the exact shrink
    assert abs(soft - (1 + (raw_soft - 1) * 6 / 11)) < 1e-9


def test_early_season_shrinks_harder_than_late():
    early = _pa([(f"T{i}", "RB", 20.0, 2) for i in range(8)] + [("SOFT", "RB", 30.0, 2)])
    late = _pa([(f"T{i}", "RB", 20.0, 12) for i in range(8)] + [("SOFT", "RB", 30.0, 12)])
    assert allowed_ratio(early, "SOFT", "RB", 5) < allowed_ratio(late, "SOFT", "RB", 5)


def test_degrades_to_none_rather_than_a_null_adjustment():
    assert allowed_ratio(None, "SOFT", "RB", 5) is None            # no data at all
    assert allowed_ratio(PA, "NOBODY", "RB", 5) is None            # unknown defense
    assert allowed_ratio(PA, "SOFT", "QB", 5) is None              # position not covered
    one_week = _pa([(f"T{i}", "RB", 20.0, 1) for i in range(9)])
    assert allowed_ratio(one_week, "T0", "RB", 5) is None          # too early


def test_schedule_strength_returns_number_and_opponent_names():
    sched = pl.DataFrame({"team": ["ATL"] * 3, "week": [15, 16, 17],
                          "opp": ["SOFT", "TOUGH", "T0"]})
    val, label = schedule_strength(PA, sched, "ATL", "RB", (15, 16, 17), 5)
    assert val is not None
    assert "wk15 vs SOFT" in label and "wk17 vs T0" in label       # names kept
    lo, _ = schedule_strength(PA, sched, "NOTEAM", "RB", (15, 16, 17), 5)
    assert lo is None
