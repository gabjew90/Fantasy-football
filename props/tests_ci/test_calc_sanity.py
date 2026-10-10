"""props/calc known-answer and sanity tests (props/calc/CLAUDE.md, rules 3-5).

Run in CI on a committed fixture of the real 2022-23 pools
(props/tests_ci/fixtures/calc_pools_2022_2023.json, written by
`python -m props.calc.fixture 2022 2023`), so no download is needed. Tuning
years only: 2024-25 are held out (docs/plans/2026-10-10-parlay-leg-calculator.md)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from props.calc import calc, checks, fixture, odds, rates, settings  # noqa: E402
from props.calc.player import make_pools  # noqa: E402

FIXED = settings.load()["fixed"]
FX = json.loads(fixture.FIXTURE.read_text(encoding="utf-8"))
assert FX["seasons"] == fixture.FIXTURE_SEASONS, "the CI fixture holds other seasons than its name says"
CARRIES, TARGETS = fixture.frames(FX)
POOLS = make_pools(CARRIES, TARGETS, FIXED)


# ------------------------------------------------------------------ rule 3: known answers

def test_odds_known_answers():
    assert round(odds.break_even(1.78) * 100, 1) == 56.2
    assert round(odds.break_even(odds.multiplier_from_american(-125)) * 100, 1) == 55.6


def test_rates_known_answers():
    # yards per carry: (5 - 2 + 0 + 12) / 4
    assert rates.yards_per_carry([5, -2, 0, 12]) == pytest.approx(3.75)
    # catch rate: 3 of 5
    assert rates.catch_rate([1, 0, 1, 1, 0]) == pytest.approx(0.6)
    # yards per target, incompletions as zero (nflverse leaves NaN): (12 + 8 + 30) / 5
    assert rates.yards_per_target([12, np.nan, 8, 30, np.nan], [True, False, True, True, False]) == pytest.approx(10.0)
    # blend: 100 yards on 20 carries toward 4.3 with k = 150 -> (100 + 645) / 170
    assert rates.blend(100, 20, 4.3, 150) == pytest.approx(745 / 170)


def test_rates_fail_loudly_on_missing_values():
    with pytest.raises(checks.DataError):
        rates.yards_per_carry([5, np.nan])
    with pytest.raises(checks.DataError):
        rates.catch_rate([1, np.nan])
    with pytest.raises(checks.DataError):
        rates.yards_per_target([np.nan, 3], [True, False])        # a catch with no yards
    with pytest.raises(checks.DataError):
        rates.blend(10, 2, float("nan"), 150)
    with pytest.raises(checks.DataError):
        rates.yards_per_target([10.0, 5.0], [1.0, np.nan])       # a missing catch flag is not a catch
    with pytest.raises(checks.DataError):
        rates.yards_per_target([np.inf, 0.0], [1, 0])             # infinite yards on a catch


def _rush(ypc):
    d = calc.make_draws("carries", 16, FIXED["sims"], FIXED["seed"])
    return calc.Model("rush_yds", "carries", d, ypc, POOLS["rb_residuals"], 0.15)


def _rec(rate):
    return calc.Model("receptions", "targets", calc.make_draws("targets", 8, FIXED["sims"], FIXED["seed"]), rate)


def _over(model, line, american_over):
    s = calc.solve_workload(model, line, odds.break_even(odds.multiplier_from_american(american_over)))
    assert s.status == "ok"
    return s.value


def test_the_three_sanity_targets_from_the_brief():
    assert _over(_rush(3.97), 64.5, -125) == pytest.approx(19.1, abs=1)
    assert _over(_rush(4.19), 54.5, -127) == pytest.approx(15.6, abs=1)
    assert _over(_rec(0.74), 6.5, -128) == pytest.approx(10.2, abs=1)


# ------------------------------------------------------------------ rule 5: output sanity

def test_league_averages_fall_in_their_plausible_ranges():
    """Computed from the fixture's raw counts, independently of make_pools."""
    rb, other = FX["rb_carry_yards"], FX["other_carries"]
    n_c = sum(rb.values()) + sum(n for n, _ in other.values())
    ypc = (sum(int(k) * v for k, v in rb.items()) + sum(t for _, t in other.values())) / n_c
    tg = FX["targets"] + [[p, None, n, c, y] for p, n, c, y in FX.get("targets_without_depth", [])]
    n_t = sum(t[2] for t in tg)
    catch, ypt = sum(t[3] for t in tg) / n_t, sum(t[4] for t in tg) / n_t
    for value, key in ((ypc, "league_ypc_range"), (catch, "league_catch_rate_range"),
                       (ypt, "league_yards_per_target_range")):
        lo, hi = FIXED[key]
        assert lo <= value <= hi, (key, value)


def test_needed_workload_rises_as_the_line_rises():
    m = _rush(4.2)
    need = [calc.solve_workload(m, line, 0.56).value for line in (34.5, 44.5, 54.5, 64.5, 74.5, 84.5)]
    assert all(b > a for a, b in zip(need, need[1:])), need
    r = _rec(0.7)
    need = [calc.solve_workload(r, line, 0.56).value for line in (2.5, 3.5, 4.5, 5.5, 6.5, 7.5)]
    assert all(b > a for a, b in zip(need, need[1:])), need


def test_pools_fail_loudly_and_record_thin_groups():
    bad = CARRIES.copy()
    bad.loc[0, "yards"] = np.nan
    with pytest.raises(checks.DataError, match="missing"):
        make_pools(bad, TARGETS, FIXED)
    wild = CARRIES.assign(yards=CARRIES["yards"] + 3)                 # league ypc ~7.4
    with pytest.raises(checks.DataError, match="plausible range"):
        make_pools(wild, TARGETS, FIXED)
    assert POOLS["rb_n"] >= FIXED["min_pool_rb_carries"]
    assert all(np.isfinite(POOLS["rb_residuals"])) and abs(POOLS["rb_residuals"].mean()) < 1e-9


def test_the_priced_week_check():
    ko = {"a": pd.Timestamp("2026-10-01T17:00Z"), "b": pd.Timestamp("2026-10-08T17:00Z")}
    cutoff = pd.Timestamp("2026-10-08T17:00Z")
    checks.kicked_off_before("x", ["a"], ko, cutoff)
    with pytest.raises(checks.DataError, match="at or after the priced week"):
        checks.kicked_off_before("x", ["a", "b"], ko, cutoff)
    with pytest.raises(checks.DataError, match="not on the schedule"):
        checks.kicked_off_before("x", ["zz"], ko, cutoff)


# ------------------------------------------------------------------ pools and build, by hand

def test_make_pools_known_answers():
    c = pd.DataFrame({"yards": [4.0] * 3000 + [5.0] * 3000 + [10.0] * 10, "position": ["RB"] * 6000 + ["WR"] * 10})
    t = pd.DataFrame({"yards": [10.0, 0.0, 6.0, 0.0] * 100, "caught": [True, False, True, False] * 100,
                      "air_yards": [2.0, 3.0, 20.0, 25.0] * 100, "position": ["WR"] * 400})
    # league: ypc (3000*4 + 3000*5 + 100) / 6010; catch 0.5; yards per target (10 + 6) / 4
    fixed = {**FIXED, "league_catch_rate_range": [0.4, 0.8], "league_yards_per_target_range": [3, 9]}
    p = make_pools(c, t, fixed)
    assert p["league_ypc"] == pytest.approx(27100 / 6010)
    assert p["league_catch"] == pytest.approx(0.5) and p["league_ypt"] == pytest.approx(4.0)
    assert p["rb_n"] == 6000 and p["ypc_by_pos"]["RB"] == pytest.approx(4.5) and p["ypc_by_pos"]["WR"] == 10
    assert p["catch_by_pos_bucket"][("WR", "short")] == pytest.approx(0.5)
    assert p["catch_by_pos_bucket"][("WR", "deep")] == pytest.approx(0.5)
    assert p["targets_by_pos_bucket"][("WR", "short")] == 200 and ("WR", "medium") not in p["targets_by_pos_bucket"]
    assert abs(p["rb_residuals"].mean()) < 1e-12 and p["targets_without_depth"] == 0
    with pytest.raises(checks.DataError, match="roster position"):
        make_pools(c.assign(position=[None] + list(c["position"][1:])), t, fixed)


def _bundle(carries, targets, games, pools, season=2026):
    from props.calc import player
    b = object.__new__(player.Bundle)
    b.seasons, b.fixed = [season - 2, season - 1, season], FIXED
    b.carries, b.targets, b.games = carries, targets, games
    b.snap_share = pd.DataFrame(columns=["game_id", "gsis_id", "offense_pct"])
    b.schedule = pd.DataFrame([dict(game_id=f"{season}_{w:02d}_A_B", season=season, week=w, home_team="B",
                                    away_team="A", home_score=np.nan, away_score=np.nan, home_qb_id=None,
                                    away_qb_id=None, home_qb_name=None, away_qb_name=None,
                                    kickoff_utc=(pd.Timestamp(f"{season}-09-07T17:00:00Z")
                                                 + pd.Timedelta(days=7 * (w - 1))).isoformat())
                               for w in range(1, 7)])
    b._kickoffs = None
    b._week_starts = {}
    b._roster_pos = pd.DataFrame([{"season": season, "week": 1, "gsis_id": "rb1", "position": "RB"},
                                  {"season": season, "week": 1, "gsis_id": "new", "position": "RB"}])
    b.position = {}
    b._pools = {(season, FIXED["pool_seasons"]): pools}
    return b


def _hand_pools():
    return {"rb_residuals": np.array([-1.0, 0.0, 1.0]), "rb_n": 6000, "ypc_by_pos": {"RB": 4.0},
            "carries_by_pos": {"RB": 6000}, "catch_by_pos_bucket": {("RB", "short"): 0.8, ("RB", "deep"): 0.4},
            "targets_by_pos_bucket": {("RB", "short"): 5000, ("RB", "deep"): 50},
            "league_ypc": 4.4, "league_catch": 0.66, "league_ypt": 7.3, "targets_without_depth": 0}


def _games_rows(n):
    return pd.DataFrame([dict(game_id=f"2026_{w:02d}_A_B", season=2026, week=w, team="A", gsis_id="rb1",
                              carries=10, rush_yds=50.0, targets=2, receptions=2, rec_yds=10.0, completions=0,
                              pass_yds=0.0) for w in range(1, n + 1)])


def test_build_blends_by_hand_and_ignores_the_priced_week():
    from props.calc import player
    games = _games_rows(5)                                    # weeks 1-5; week 5 is the priced week
    car = pd.DataFrame([dict(game_id=g, season=2026, week=w, gsis_id="rb1", yards=5.0)
                        for g, w in zip(games["game_id"], games["week"]) for _ in range(10)])
    b = _bundle(car, pd.DataFrame(columns=["game_id", "season", "week", "gsis_id", "yards", "caught", "air_yards"]),
                games, _hand_pools())
    pl = player.build(b, "rb1", "Rb One", "A", 2026, 5, {"k_ypc": 150, "k_catch": 60}, FIXED, "rush_yds")
    # 40 carries at 5.0 from weeks 1-4 (week 5 excluded), toward 4.0 with k = 150: (200 + 600) / 190
    assert pl.rates["ypc"].own_n == 40 and pl.rates["ypc"].blended == pytest.approx(800 / 190)
    assert "rush_yds" not in pl.not_enough and len(pl.window) == 4


def test_build_reports_not_enough_data_instead_of_crashing():
    from props.calc import player
    empty_c = pd.DataFrame(columns=["game_id", "season", "week", "gsis_id", "yards"])
    empty_t = pd.DataFrame(columns=["game_id", "season", "week", "gsis_id", "yards", "caught", "air_yards"])
    b = _bundle(empty_c, empty_t, _games_rows(0).reindex(columns=_games_rows(1).columns), _hand_pools())
    tuned = {"k_ypc": 150, "k_catch": 60}
    for market in ("rush_yds", "receptions"):                 # a player with no history at all
        pl = player.build(b, "new", "New Guy", "A", 2026, 1, tuned, FIXED, market)
        assert market in pl.not_enough and "needs" in " ".join(pl.not_enough[market])
        with pytest.raises(checks.DataError, match="not enough data"):
            player.model(pl, market, {"carry_r": 16, "day_sd": 0.15, "target_r": 8}, FIXED)
    # enough targets of his own, but one deep and the RB deep pool holds only 50: not enough data
    games = _games_rows(4)
    tg = pd.DataFrame([dict(game_id=g, season=2026, week=w, gsis_id="rb1", yards=5.0, caught=True,
                            air_yards=20.0 if i == 0 and w == 1 else 1.0)
                       for g, w in zip(games["game_id"], games["week"]) for i in range(6)])
    b = _bundle(empty_c, tg, games, _hand_pools())
    pl = player.build(b, "rb1", "Rb One", "A", 2026, 5, tuned, FIXED, "receptions")
    assert any("depth deep" in w for w in pl.not_enough["receptions"])


def test_the_fixture_rebuilds_the_summarised_counts_exactly():
    rb = FX["rb_carry_yards"]
    assert POOLS["rb_n"] == sum(rb.values())
    assert POOLS["ypc_by_pos"]["RB"] == pytest.approx(sum(int(k) * v for k, v in rb.items()) / sum(rb.values()))
    for pos, (n, total) in FX["other_carries"].items():
        assert POOLS["carries_by_pos"][pos] == n and POOLS["ypc_by_pos"][pos] == pytest.approx(total / n)
    n_all = sum(t[2] for t in FX["targets"]) + sum(t[1] for t in FX.get("targets_without_depth", []))
    caught = sum(t[3] for t in FX["targets"]) + sum(t[2] for t in FX.get("targets_without_depth", []))
    yards = sum(t[4] for t in FX["targets"]) + sum(t[3] for t in FX.get("targets_without_depth", []))
    assert POOLS["league_catch"] == pytest.approx(caught / n_all)
    assert POOLS["league_ypt"] == pytest.approx(yards / n_all)
    for pos, bk, n, c, _ in FX["targets"]:
        assert POOLS["targets_by_pos_bucket"][(pos, bk)] == n
        assert POOLS["catch_by_pos_bucket"][(pos, bk)] == pytest.approx(c / n)


def test_a_leak_into_his_games_is_caught_by_kickoff_time():
    from props.calc import player
    games = _games_rows(4)
    games.loc[3, "game_id"] = "2026_05_A_B"           # a week-5 game mislabelled as week 4
    car = pd.DataFrame([dict(game_id=g, season=2026, week=w, gsis_id="rb1", yards=5.0)
                        for g, w in zip(games["game_id"], games["week"]) for _ in range(10)])
    b = _bundle(car, pd.DataFrame(columns=["game_id", "season", "week", "gsis_id", "yards", "caught", "air_yards"]),
                games, _hand_pools())
    with pytest.raises(checks.DataError, match="at or after the priced week"):
        player.build(b, "rb1", "Rb One", "A", 2026, 5, {"k_ypc": 150, "k_catch": 60}, FIXED, "rush_yds")


def test_find_player_refuses_when_a_namesake_is_set_aside():
    from props.calc import player
    b = object.__new__(player.Bundle)
    b.rosters = pd.DataFrame([
        {"season": 2026, "week": 5, "team": t, "full_name": "Mike Williams", "gsis_id": g, "status": "ACT",
         "position": "WR"} for t, g in (("NYJ", "a"), ("PIT", "b"), ("LAC", "b"))])
    with pytest.raises(player.NotFound, match="two teams"):
        player.find_player(b, "Mike Williams", 2026, None, 5)
    assert player.find_player(b, "Mike Williams", 2026, "NYJ", 5)[0] == "a"     # the team settles it
    with pytest.raises(player.NotFound, match="two teams"):
        player.find_player(b, "M. Williams", 2026, None, 5)                    # abbreviated: refused too
    with pytest.raises(player.NotFound, match="no 2026 roster"):
        player.find_player(b, "Mike Williams", 2026, None, 2)


def test_the_fixture_summariser_known_answers():
    c = pd.DataFrame({"yards": [3.0, 3.0, -1.0, 12.0, 5.0], "position": ["RB", "RB", "RB", "WR", "WR"]})
    t = pd.DataFrame({"yards": [10.0, 0.0, 30.0, 4.0], "caught": [True, False, True, True],
                      "air_yards": [2.0, 7.0, 20.0, np.nan], "position": ["WR", "WR", "WR", "TE"]})
    fx = fixture.summarise_frames(c, t, FIXED, [2022, 2023])
    assert fx["rb_carry_yards"] == {"-1": 1, "3": 2}
    assert fx["other_carries"] == {"WR": [2, 17.0]}
    assert sorted(fx["targets"]) == [["WR", "deep", 1, 1, 30.0], ["WR", "medium", 1, 0, 0.0],
                                     ["WR", "short", 1, 1, 10.0]]
    assert fx["targets_without_depth"] == [["TE", 1, 1, 4.0]]


def test_build_refuses_other_fixed_settings_than_its_pools():
    from props.calc import player
    b = _bundle(pd.DataFrame(columns=["game_id", "season", "week", "gsis_id", "yards"]),
                pd.DataFrame(columns=["game_id", "season", "week", "gsis_id", "yards", "caught", "air_yards"]),
                _games_rows(1), _hand_pools())
    with pytest.raises(checks.DataError, match="other fixed settings"):
        player.build(b, "rb1", "Rb One", "A", 2026, 2, {"k_ypc": 150, "k_catch": 60},
                     {**FIXED, "depth_short_below": 6}, "receptions")
