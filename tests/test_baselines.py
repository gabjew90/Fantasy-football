"""Streaming-derived replacement baselines (draftkit/baselines.py).

The operator itself is blocked on ownership data — see the module docstring.
These cover the parts that are decidable now, including the two input bugs
that made the first run produce a confident wrong answer.
"""

import polars as pl
import pytest

from draftkit import baselines as B


def wkrow(player, pos, week, fpts):
    return {"player": player, "pos": pos, "week": week, "fpts": float(fpts)}


# ---------- waiver friction ----------

def test_waiver_k_by_type():
    assert B.waiver_k("faab") == 2
    assert B.waiver_k("rolling_list") == 3
    assert B.waiver_k("rolling_priority") == 3


def test_unknown_waiver_type_is_pessimistic():
    """Assuming you always land your first choice is the failure mode that
    inflates VORP, so an unknown waiver type must not get the optimistic k."""
    assert B.waiver_k(None) == 3
    assert B.waiver_k("something new") == 3
    assert B.waiver_k(None) >= B.waiver_k("faab")


# ---------- rostered counts ----------

def _board():
    # 6 picks' worth of draft, but 8 players carry an ADP inside pick 6 --
    # exactly the shape that broke the first run (ADP is a mean over drafts,
    # so "ADP <= last pick" describes a bigger set than the draft can hold)
    return [{"pos": "QB", "adp": 1.0}, {"pos": "RB", "adp": 2.0},
            {"pos": "RB", "adp": 3.0}, {"pos": "WR", "adp": 4.0},
            {"pos": "WR", "adp": 5.0}, {"pos": "TE", "adp": 5.5},
            {"pos": "QB", "adp": 5.8}, {"pos": "QB", "adp": 6.0}]


def test_rostered_counts_takes_the_top_n_by_adp():
    got = B.rostered_counts(_board(), teams=2, rounds=3)   # 6 picks
    assert sum(got.values()) == 6
    assert got["QB"] == 1          # not 3: only one QB is inside the top 6
    assert got["RB"] == 2
    assert got["WR"] == 2
    assert got["TE"] == 1


def test_rostered_counts_never_exceeds_the_draft():
    """Regression: counting everyone with ADP inside the last pick put 28
    quarterbacks in a 10-team 1-QB league and pushed the residual pool down to
    QB29, which then measured streaming as worthless."""
    board = [{"pos": "QB", "adp": float(i)} for i in range(1, 30)]
    got = B.rostered_counts(board, teams=10, rounds=15)
    assert sum(got.values()) == 29        # fewer players than picks: all count
    got2 = B.rostered_counts(board, teams=2, rounds=2)
    assert sum(got2.values()) == 4


def test_rostered_counts_ignores_players_without_adp():
    board = [{"pos": "RB", "adp": 1.0}, {"pos": "WR", "adp": None}]
    assert B.rostered_counts(board, teams=2, rounds=3) == {"RB": 1}


# ---------- rank mapping ----------

def test_rank_for_season_total_finds_the_nearest_rank():
    wk = pl.DataFrame([wkrow("a", "TE", 1, 100), wkrow("b", "TE", 1, 60),
                       wkrow("c", "TE", 1, 20)])
    assert B.rank_for_season_total(wk, "TE", 95.0) == 1
    assert B.rank_for_season_total(wk, "TE", 55.0) == 2
    assert B.rank_for_season_total(wk, "TE", 0.0) == 3


def test_rank_for_season_total_on_an_empty_position():
    wk = pl.DataFrame([wkrow("a", "TE", 1, 10.0)])
    assert B.rank_for_season_total(wk, "QB", 50.0) is None


# ---------- weekly_points ----------

def test_weekly_points_drops_week_18_and_beyond():
    raw = pl.DataFrame([
        {"player_display_name": "a", "position": "QB", "week": 17, "x": 1.0},
        {"player_display_name": "a", "position": "QB", "week": 18, "x": 1.0},
        {"player_display_name": "a", "position": "QB", "week": 21, "x": 1.0},
    ])
    out = B.weekly_points(raw, (pl.col("x") * 2.0).alias("fpts"))
    assert out["week"].to_list() == [17]


def test_weekly_points_drops_positions_the_operator_cannot_score():
    """nflverse carries no kicking or team-defense columns, so a kicker would
    score exactly 0.0 and the operator would 'derive' a K2 baseline."""
    raw = pl.DataFrame([
        {"player_display_name": "a", "position": "QB", "week": 1, "x": 5.0},
        {"player_display_name": "k", "position": "K", "week": 1, "x": 0.0},
    ])
    out = B.weekly_points(raw, (pl.col("x")).alias("fpts"))
    assert out["pos"].to_list() == ["QB"]
    assert "K" not in B.STREAMABLE and "DEF" not in B.STREAMABLE


# ---------- the operator ----------

def _season():
    """Two rostered studs, three waiver options with distinguishable form."""
    rows = []
    for w in range(1, 18):
        rows += [wkrow("stud1", "QB", w, 25.0), wkrow("stud2", "QB", w, 22.0)]
        rows += [wkrow("hot", "QB", w, 18.0 if w >= 3 else 2.0),
                 wkrow("mid", "QB", w, 10.0),
                 wkrow("cold", "QB", w, 4.0)]
    return pl.DataFrame(rows)


def test_operator_refuses_to_guess_the_waiver_pool():
    with pytest.raises(B.OwnershipUnavailable):
        B.streaming_ppg(_season(), "QB", {}, k=1)


def test_operator_picks_the_kth_best_by_recent_form():
    held = {w: {"stud1", "stud2"} for w in range(1, 18)}
    wk = _season()
    assert B.streaming_ppg(wk, "QB", held, k=1) == pytest.approx(18.0)
    assert B.streaming_ppg(wk, "QB", held, k=2) == pytest.approx(10.0)
    assert B.streaming_ppg(wk, "QB", held, k=3) == pytest.approx(4.0)


def test_higher_k_never_returns_more_than_lower_k():
    """The order statistic is the whole friction model: k=3 must be a weaker
    result than k=1, or the parameter is not doing what it claims."""
    held = {w: {"stud1", "stud2"} for w in range(1, 18)}
    wk = _season()
    vals = [B.streaming_ppg(wk, "QB", held, k=kk) for kk in (1, 2, 3)]
    assert vals == sorted(vals, reverse=True)


def test_rostered_players_are_never_streamed():
    held = {w: {"stud1", "stud2"} for w in range(1, 18)}
    # if the held set leaked, k=1 would return the 25.0 stud
    assert B.streaming_ppg(_season(), "QB", held, k=1) < 25.0


def test_inactive_players_are_not_streamed():
    """Only players who actually appear in week w can be started, and knowing
    that is ex ante -- inactives are published before lineups lock."""
    rows = []
    for w in range(1, 18):
        rows.append(wkrow("mid", "QB", w, 10.0))
        if w != 9:                       # "hot" sits out week 9
            rows.append(wkrow("hot", "QB", w, 20.0))
    wk = pl.DataFrame(rows)
    held = {w: set() for w in range(1, 18)}
    got = B.streaming_ppg(wk, "QB", held, k=1)
    # 12 weeks of "hot" at 20 and week 9 falling back to "mid" at 10
    assert got == pytest.approx((20.0 * 12 + 10.0) / 13)


# ---------- floor ----------

def test_floor_lets_streaming_tighten_but_never_loosen():
    wk = pl.DataFrame([wkrow(f"q{i}", "QB", w, 20.0 - i)
                       for i in range(12) for w in range(1, 18)])
    held = {w: {"q0", "q1"} for w in range(1, 18)}
    # streaming returns q2 (18.0 ppg), whose season total ranks 3rd
    got = B.derive(wk, {"QB": held}, k=1, format_baselines={"QB": 10})
    assert got["QB"]["streaming_rank"] == 3
    assert got["QB"]["baseline"] == 3, "a better waiver pool must raise replacement"

    deep = B.derive(wk, {"QB": held}, k=1, format_baselines={"QB": 2})
    assert deep["QB"]["baseline"] == 2, "the format baseline is a hard ceiling"


def test_no_ownership_leaves_the_format_baseline_standing():
    wk = pl.DataFrame([wkrow("a", "QB", 1, 10.0)])
    got = B.derive(wk, {}, k=3, format_baselines={"QB": 10, "TE": 11})
    assert got["QB"]["baseline"] == 10
    assert got["TE"]["baseline"] == 11
    assert "no ownership data" in got["QB"]["why"]


# ---------- ownership loader ----------

def test_held_from_ownership_applies_the_threshold():
    rows = [{"player": "a", "week": "3", "pct_rostered": "91"},
            {"player": "b", "week": "3", "pct_rostered": "12"},
            {"player": "c", "week": "4", "pct_rostered": "55"}]
    got = B.held_from_ownership(rows, {"a": "QB", "b": "QB", "c": "TE"})
    assert got == {"QB": {3: {"a"}}, "TE": {4: {"c"}}}


def test_held_from_ownership_skips_unparseable_rows():
    rows = [{"player": "a", "week": "x", "pct_rostered": "91"},
            {"player": "b", "week": "3", "pct_rostered": ""},
            {"player": "c", "week": "3", "pct_rostered": "99"}]
    got = B.held_from_ownership(rows, {"a": "QB", "b": "QB", "c": "QB"})
    assert got == {"QB": {3: {"c"}}}
