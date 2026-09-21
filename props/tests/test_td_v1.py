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
    qbstarts = pd.DataFrame({"season": [2025], "week": [1], "game_id": ["p"], "team": ["A"],
                             "player_id": ["qb"], "qb_rush_tds": [1], "off_tds": [3]})
    bundled = {"cnt": pri, "played": played_pri, "slots": slots_pri, "tg": tg_pri, "qbstarts": qbstarts}
    cur = {"cnt": pri.iloc[0:0], "played": played_pri.iloc[0:0], "tg": None,
           "qbstarts": None, "season": 2026, "week": 1,
           "actives": pd.DataFrame({"player_id": ["rb", "wr", "qb", "rookie"], "team": "A",
                                    "pos": ["RB", "WR", "QB", "RB"],
                                    "slot": ["RB1", "WR1", "QB1", "RB2"]})}
    return bundled, cur


def test_the_live_entry_point_is_the_composition_the_backtest_calls():
    """No second implementation: anytime_probabilities must equal
    week_shares -> context -> game_detail, the same calls the backtest makes."""
    bundled, cur = _world()
    got = V.anytime_probabilities(bundled, cur, {"A": 24.0})

    ctx = V.context(bundled["tg"], qb_hist=V.qb_history(bundled["qbstarts"], 2026, 1))
    shares, _ = V.week_shares(cur["cnt"], bundled["cnt"], cur["played"], bundled["played"],
                              bundled["slots"], cur["actives"])
    pos = dict(zip(cur["actives"]["player_id"], cur["actives"]["pos"]))
    ids = list(cur["actives"]["player_id"])
    assert V.starter(cur["actives"]) == "qb"
    want = V.game_detail(shares, "A", ids, pos, ctx, 24.0, qb="qb")
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


def test_a_missing_starts_bundle_is_an_error_not_a_silent_team_mix():
    """With qb_beta set, pricing without the starts would quietly fall back to
    the team mix -- the Willis error -- so it raises, and score_game's handler
    falls back to v0 with the failure in the sources table."""
    bundled, cur = _world()
    bundled["qbstarts"] = None
    if V.V1["qb_beta"] is not None:
        with pytest.raises(ValueError):
            V.anytime_probabilities(bundled, cur, {"A": 24.0})


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


# ------------------------------------------------------------ v1.1: cap and the starter's QB-rush rate

def _qb_pbp():
    """Team A, one game: q1 drops back 3 times and scores a QB rush; q2 has one
    dropback; the RB scores a rushing TD. Team B scores a passing TD."""
    cols = ["game_id", "season", "week", "season_type", "posteam", "defteam", "play_type",
            "passer_player_id", "rusher_player_id", "receiver_player_id", "td_player_id", "td_team",
            "touchdown", "rush_touchdown", "pass_touchdown", "yardline_100", "qb_kneel",
            "two_point_attempt"]
    rows = [("g", 2025, 1, "REG", "A", "B", "pass", "q1", None, "w", None, None, 0, 0, 0, 50, 0, 0),
            ("g", 2025, 1, "REG", "A", "B", "pass", "q1", None, "w", None, None, 0, 0, 0, 40, 0, 0),
            ("g", 2025, 1, "REG", "A", "B", "pass", "q1", None, "w", None, None, 0, 0, 0, 30, 0, 0),
            ("g", 2025, 1, "REG", "A", "B", "pass", "q2", None, "w", None, None, 0, 0, 0, 30, 0, 0),
            ("g", 2025, 1, "REG", "A", "B", "run", None, "q1", None, "q1", "A", 1, 1, 0, 8, 0, 0),
            ("g", 2025, 1, "REG", "A", "B", "run", None, "rb", None, "rb", "A", 1, 1, 0, 2, 0, 0),
            ("g", 2025, 1, "REG", "B", "A", "pass", "qb", None, "x", "x", "B", 1, 0, 1, 30, 0, 0)]
    return pd.DataFrame(rows, columns=cols)


def test_qb_starts_names_the_starter_and_counts_his_qb_rush_touchdowns():
    st = V.qb_starts(_qb_pbp(), {"q1", "q2", "qb"}).set_index("team")
    assert st.loc["A", "player_id"] == "q1"          # 4 plays to q2's 1
    assert st.loc["A", "qb_rush_tds"] == 1
    assert st.loc["A", "off_tds"] == 2
    assert st.loc["B", "qb_rush_tds"] == 0 and st.loc["B", "off_tds"] == 1


def test_qb_history_is_strictly_before_the_week_and_inside_the_window():
    st = pd.DataFrame({"season": [2021, 2022, 2025, 2026, 2026], "week": [1, 1, 1, 1, 2],
                       "player_id": "q", "team": "A", "qb_rush_tds": 1, "off_tds": 3})
    h = V.qb_history(st, 2026, 2, window=3)
    assert sorted(zip(h["season"], h["week"])) == [(2025, 1), (2026, 1)]


def test_the_starter_is_the_highest_active_quarterback_on_the_depth_chart():
    act = pd.DataFrame({"player_id": ["b", "a", "r"], "pos": ["QB", "QB", "RB"],
                        "slot": ["QB2", "QB1", "RB1"]})
    assert V.starter(act) == "a"
    assert V.starter(act[act["player_id"] != "a"]) == "b"      # QB1 inactive
    assert V.starter(act[act["pos"] != "QB"]) is None


def test_the_team_mix_is_unchanged_without_qb_beta_and_the_starter_rate_replaces_it_with():
    bundled, _ = _world()
    ctx = V.context(bundled["tg"])
    team = V.game_mix(ctx, "A", qb="qb", beta=None)
    assert team.sum() == pytest.approx(1.0)
    qh = pd.DataFrame({"player_id": ["qb"], "team": "A", "qb_rush_tds": [6], "off_tds": [20]})
    ctx = V.context(bundled["tg"], qb_hist=qh)
    m = V.game_mix(ctx, "A", qb="qb", beta=10.0)
    assert m.sum() == pytest.approx(1.0)
    assert m["qb_rush"] == pytest.approx((6 + 10 * ctx["qb_league"]) / 30)
    # the other channels keep their team proportions
    rest, rest0 = m.drop("qb_rush"), team.drop("qb_rush")
    assert (rest / rest.sum()).to_numpy() == pytest.approx((rest0 / rest0.sum()).to_numpy())
    # an unknown starter gets the league fraction
    assert V.game_mix(ctx, "A", qb="nobody", beta=10.0)["qb_rush"] == pytest.approx(ctx["qb_league"])


def test_game_q_is_per_td_of_game_shares_and_game_mix():
    """The backtest computes q as per_td(game_shares, game_mix) so the
    reallocation is not repeated per QB setting; that must be game_q."""
    bundled, cur = _world()
    qh = pd.DataFrame({"player_id": ["qb"], "team": "A", "qb_rush_tds": [3], "off_tds": [20]})
    ctx = V.context(bundled["tg"], qb_hist=qh)
    shares, _ = V.week_shares(cur["cnt"], bundled["cnt"], cur["played"], bundled["played"],
                              bundled["slots"], cur["actives"])
    pos = dict(zip(cur["actives"]["player_id"], cur["actives"]["pos"]))
    ids = list(cur["actives"]["player_id"])
    for cap, beta in ((0.99, None), (0.997, 20.0)):
        a = V.game_q(shares, "A", ids, pos, ctx, cap=cap, qb="qb", beta=beta)
        b = V.per_td(V.game_shares(shares, "A", ids, pos, cap=cap),
                     V.game_mix(ctx, "A", "qb", beta)).clip(upper=0.999)
        assert a.to_numpy() == pytest.approx(b.to_numpy())


def test_the_cap_bounds_total_share():
    bundled, cur = _world()
    shares, _ = V.week_shares(cur["cnt"], bundled["cnt"], cur["played"], bundled["played"],
                              bundled["slots"], cur["actives"])
    pos = dict(zip(cur["actives"]["player_id"], cur["actives"]["pos"]))
    ids = list(cur["actives"]["player_id"])
    for cap in (0.99, 0.997):
        m = V.game_shares(shares, "A", ids, pos, cap=cap)
        assert (m.sum() <= cap + 1e-9).all()


def test_the_bundled_quarterback_starts_cover_the_window():
    b = V.load_bundled(ENGINE.parent / "resources", 2025)
    st = b["qbstarts"]
    assert st is not None
    assert sorted(st["season"].unique()) == list(range(2025 - V.V1["qb_window"] + 1, 2026))
    assert not st.duplicated(["game_id", "team"]).any()   # one starter per team-game
