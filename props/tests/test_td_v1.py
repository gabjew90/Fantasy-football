"""anytime_td_v1: the one implementation the scorer prices from and the
backtest scores.

These pin the properties that make "the number validated is the number
priced" true: the live entry point is exactly the composition of the shared
functions the backtest calls, the active list excludes players ruled out
before kickoff, total share never exceeds the whole, and a prior season
bundled as raw inputs round-trips through the loader unchanged.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ENGINE = Path(__file__).resolve().parents[1] / "engine" / "scripts"
sys.path.insert(0, str(ENGINE))

pd = pytest.importorskip("pandas")
import td_model as T  # noqa: E402
import td_v1 as V  # noqa: E402

CH = list(T.OFFENSIVE)


def _cnt(rows):
    return pd.DataFrame(rows, columns=["season", "week", "game_id", "team", "player_id", *CH])


def _played(rows):
    return pd.DataFrame(rows, columns=["season", "week", "game_id", "team", "player_id", "pos"])


def _tg(rows):
    """team-games: (game_id, season, week, team, points, implied, *channel counts)."""
    d = pd.DataFrame(rows, columns=["game_id", "season", "week", "team", "points", "implied",
                                    *CH, "dst_other"])
    d["off_tds"] = d[CH].sum(axis=1)
    d["tds"] = d["off_tds"] + d["dst_other"]
    d["dst"] = d["dst_other"]
    return d


def _world():
    """A prior season and one current week for team A: an RB1, a WR1, a QB."""
    # "rb2" held the RB2 slot last season and has since left, so the RB2 slot
    # has a league share for the rookie to inherit (real data always does)
    pri = _cnt([(2025, 1, "p", "A", "rb", 0, 6, 20, 1, 1),
                (2025, 1, "p", "A", "rb2", 0, 1, 6, 0, 1),
                (2025, 1, "p", "A", "wr", 0, 0, 0, 6, 8),
                (2025, 1, "p", "A", "qb", 4, 0, 0, 0, 0)])
    played_pri = _played([(2025, 1, "p", "A", "rb", "RB"), (2025, 1, "p", "A", "rb2", "RB"),
                          (2025, 1, "p", "A", "wr", "WR"), (2025, 1, "p", "A", "qb", "QB")])
    slots_pri = pd.DataFrame({"season": 2025, "week": 1, "team": "A",
                              "player_id": ["rb", "rb2", "wr", "qb"],
                              "slot": ["RB1", "RB2", "WR1", "QB1"]})
    tg_pri = _tg([("p", 2025, 1, "A", 24, 23.0, 0, 2, 0, 1, 0, 0)])
    bundled = {"cnt": pri, "played": played_pri, "slots": slots_pri, "tg": tg_pri}
    cur = {"cnt": pri.iloc[0:0], "played": played_pri.iloc[0:0], "tg": None,
           "actives": pd.DataFrame({"player_id": ["rb", "wr", "qb", "rookie"], "team": "A",
                                    "pos": ["RB", "WR", "QB", "RB"],
                                    "slot": ["RB1", "WR1", "QB1", "RB2"]})}
    return bundled, cur


def test_the_live_entry_point_is_the_composition_the_backtest_calls():
    """No second implementation: anytime_probabilities must equal
    week_shares -> context -> game_detail, the same calls the backtest makes."""
    bundled, cur = _world()
    got = V.anytime_probabilities(bundled, cur, {"A": 24.0})

    ctx = V.context(bundled["tg"])
    shares, _ = V.week_shares(cur["cnt"], bundled["cnt"], cur["played"], bundled["played"],
                              bundled["slots"], cur["actives"])
    pos = dict(zip(cur["actives"]["player_id"], cur["actives"]["pos"]))
    ids = list(cur["actives"]["player_id"])
    want = V.game_detail(shares, "A", ids, pos, ctx, 24.0)
    assert got["p"].to_numpy() == pytest.approx(want["p"].to_numpy())
    assert got["q"].to_numpy() == pytest.approx(want["q"].to_numpy())


def test_total_share_never_exceeds_the_whole_and_a_rookie_is_not_zero():
    """The 0.99 cap keeps an 'other'; the scaled slot prior means a no-history
    player is not priced at zero (the ~20 catastrophic misses it removed)."""
    bundled, cur = _world()
    d = V.anytime_probabilities(bundled, cur, {"A": 24.0})
    assert d["q"].sum() <= 0.99 + 1e-9
    assert d.loc["rookie", "p"] > 0
    assert d.loc["rb", "p"] > d.loc["rookie", "p"]


def test_the_team_mean_follows_the_frozen_layer_1_spec():
    bundled, cur = _world()
    d = V.anytime_probabilities(bundled, cur, {"A": 30.0})
    ctx = V.context(bundled["tg"])
    mu = 30.0 * ctx["ratio_off"] * (30.0 / ctx["ref"]) ** V.V1["gamma"]
    assert d["mu"].iloc[0] == pytest.approx(mu, rel=1e-6)


def test_no_implied_total_prices_nobody_rather_than_guessing():
    bundled, cur = _world()
    assert V.anytime_probabilities(bundled, cur, {"A": float("nan")}).empty
    assert V.anytime_probabilities(bundled, cur, {"A": None}).empty


def test_players_ruled_out_before_kickoff_are_not_active():
    """Live, the game-day active list does not exist yet; the injury report's
    Out and Doubtful are the part of it that does."""
    ros = pd.DataFrame({"season": 2026, "week": [2, 2, 2], "team": "A",
                        "position": ["RB", "WR", "QB"], "status": "ACT",
                        "gsis_id": ["rb", "wr", "qb"], "pfr_id": ["r", "w", "q"]})
    inj = pd.DataFrame({"season": 2026, "week": [2], "gsis_id": ["wr"], "report_status": ["Out"]})
    games = pd.DataFrame({"season": [2026], "game_type": ["REG"], "week": [2], "game_id": ["g"],
                          "gameday": ["2026-09-20"], "gametime": ["13:00"],
                          "home_team": ["A"], "away_team": ["B"]})
    empty_pbp = pd.DataFrame(columns=["season", "week"])
    snaps = pd.DataFrame(columns=["season", "week", "game_type", "offense_snaps", "position",
                                  "game_id", "team", "pfr_player_id"])
    dc = pd.DataFrame({"season": [2026], "club_code": ["A"], "week": [2], "gsis_id": ["rb"],
                       "position": ["RB"], "depth_team": [1], "formation": ["Offense"],
                       "depth_position": ["RB"]})
    cur = V.current_inputs(empty_pbp, ros, snaps, dc, games, inj, 2026, 2)
    assert set(cur["actives"]["player_id"]) == {"rb", "qb"}


def test_the_bundled_prior_season_exists_and_round_trips():
    """score_game prices 2026 from the 2025 bundle; a missing or truncated
    file would silently drop every anytime price to the v0 fallback."""
    res = ENGINE.parent / "resources"
    b = V.load_bundled(res, 2025)
    assert len(b["tg"]) == 544                       # 272 games x 2 teams
    assert set(CH) <= set(b["cnt"].columns)
    assert b["played"]["player_id"].notna().all()
    assert set(b["slots"]["slot"]) >= {"QB1", "RB1", "WR1", "TE1"}
