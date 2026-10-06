"""The scoreboard (reports/scoreboard.md) on worlds with a known answer, before any real run."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "engine" / "scripts"))
sys.path.insert(0, str(ROOT / "tools"))

import model as M  # noqa: E402
import scoreboard as SB  # noqa: E402


def _world(noise, seed=0, team_effect=0.0, n_teams=32, weeks=range(2, 19), seasons=(2022, 2023)):
    """Receivers whose catches beat a stand-in line with a known chance `truth`; the
    run's conditional chance is truth plus `noise` (0 = right by construction)."""
    rng = np.random.default_rng(seed)
    nrng = np.random.default_rng([seed, 1])     # the noise on its own stream: every noise level
    rows = []                                   # sees the same games and outcomes
    for s in seasons:
        tfx = {t: rng.normal(0, team_effect) for t in range(n_teams)}
        for t in range(n_teams):
            for w in weeks:
                for p in range(3):
                    truth = float(np.clip(0.5 + rng.normal(0, 0.15) + tfx[t], 0.05, 0.95))
                    y = float(rng.uniform() < truth)
                    pc = float(np.clip(truth + nrng.normal(0, noise), 0.01, 0.99)) if noise else truth
                    rows.append({"season": s, "team": f"T{t}", "week": w, "gsis_id": f"{t}_{p}",
                                 "game_id": f"{s}_{w}_{t // 2}", "mean_tgt": 6.0, "L_rec": 4.5,
                                 "act_receptions": 5.0 if y else 4.0, "pc_rec": pc, "pu_rec": 0.5,
                                 "rush_pop": False, "mean_car_model": 0.0})
    return pd.DataFrame(rows)


def test_a_sharper_conversion_wins_and_a_noisy_one_loses():
    truth, noisy = _world(0.0), _world(0.15)
    c = SB.compare(noisy, truth, "game", reps=400)["receptions"]
    assert c["logloss_c"]["gain"] < 0 and c["logloss_c"]["ci"][1] < 0, "the noisy chance is clearly worse"
    assert c["brier_c"]["gain"] < 0 and c["move_points_c"] > 5
    same = SB.compare(truth, truth, "game", reps=200)["receptions"]
    assert same["logloss_c"]["gain"] == 0 and same["move_points_c"] == 0
    assert SB.single(truth)["receptions"]["brier_c"] < SB.single(noisy)["receptions"]["brier_c"]


def test_a_comparison_is_on_one_frozen_cohort_and_guards_block_when_evidence_is_missing():
    """Outside review 2026-10-06: the candidate is scored on the reference's player-games
    (not its own eligibility intersected), and a guard market that is absent, thin or
    non-finite blocks the verdict instead of passing."""
    ref, cand = _world(0.0), _world(0.05)
    cand.loc[cand.index[:40], "mean_tgt"] = 2.0          # the candidate's own projections drop 40 rows
    c = SB.compare(cand, ref, "game", reps=200)
    assert c["receptions"]["n"] == len(ref), "scored on the reference's cohort, all of it"
    short = cand.drop(cand.index[:5])
    try:
        SB.compare(short, ref, "game", reps=200)
        raise AssertionError("a candidate missing player-games must be refused")
    except ValueError as e:
        assert "same cohort" in str(e)
    flipped = cand.copy()
    flipped.loc[flipped.index[0], "act_receptions"] = 9.0 - flipped.loc[flipped.index[0], "act_receptions"]
    try:
        SB.compare(flipped, ref, "game", reps=200)
        raise AssertionError("different outcomes must be refused")
    except ValueError as e:
        assert "outcomes" in str(e)
    v = SB.guard_verdict(c, "receptions")
    assert v["status"] == "blocked" and "QB passing yards" in v["missing"], "absent markets block"
    full = {mk: {"n": 500, "logloss_c": {"relative": 0.0}} for mk in SB.MARKETS}
    assert SB.guard_verdict(full, "receptions")["status"] == "pass"
    worse = {**full, "receiving yards": {"n": 500, "logloss_c": {"relative": -0.01}}}
    assert SB.guard_verdict(worse, "receptions")["status"] == "fail"
    thin = {**full, "QB passing yards": {"n": 50, "logloss_c": {"relative": 0.0}}}
    assert SB.guard_verdict(thin, "receptions")["thin"] == ["QB passing yards"]
    nan = {**full, "rushing yards": {"n": 500, "logloss_c": {"relative": float("nan")}}}
    assert SB.guard_verdict(nan, "receptions")["status"] == "blocked"
    assert SB.guard_verdict(full, None, "logloss_c")["status"] == "pass", "no target: every market guards"


def test_the_bettable_filter_and_zero_volume_rows():
    w = _world(0.0)
    w.loc[w.index[:100], "mean_tgt"] = 2.0
    w.loc[w.index[100:150], "pc_rec"] = np.nan          # zero actual targets: no conditional chance
    assert SB.single(w)["receptions"]["n"] == len(w) - 150


def test_team_season_clustering_is_wider_when_teams_carry_the_effect():
    """A change that acts on a team all season: team-season resampling gives an honest,
    wider interval than game resampling."""
    a = _world(0.0, seed=1, team_effect=0.15)
    b = a.copy()
    rng = np.random.default_rng(2)
    shift = {t: rng.normal(0, 0.08) for t in b.team.unique()}
    b["pc_rec"] = np.clip(b.pc_rec + b.team.map(shift), 0.01, 0.99)
    g = SB.compare(b, a, "game", reps=600)["receptions"]["logloss_c"]["ci"]
    t = SB.compare(b, a, "team-season", reps=600)["receptions"]["logloss_c"]["ci"]
    assert (t[1] - t[0]) > 1.2 * (g[1] - g[0])


def test_the_spread_check_recovers_a_known_ratio():
    rng = np.random.default_rng(4)
    rows = []
    for g in range(300):
        proj = rng.uniform(4, 9)
        for w in range(2, 10):                                  # one stable stretch each
            rows.append({"season": 2023, "gsis_id": f"p{g}", "team": "T", "week": w, "mean_tgt": proj,
                         "act_targets": proj + rng.normal(0, 3.3), "sd_tgt": 3.9})
    st = SB.stable_stretches(pd.DataFrame(rows), "mean_tgt", "act_targets", "sd_tgt")
    assert len(st) == 300 and set(st.n) == {8}
    tab = SB.spread_table(st, [(3, 99)])
    assert abs(tab[0]["ratio"] - 3.3 / 3.9) < 0.04 and tab[0]["reading"] == "model too wide"


def test_a_stretch_breaks_on_a_qb_change_or_a_role_change():
    rows = [{"season": 2023, "gsis_id": "p", "team": "T", "week": w, "mean_tgt": (6.0 if w < 9 else 10.0),
             "act_targets": 6.0, "sd_tgt": 2.0} for w in range(2, 15)]
    d = pd.DataFrame(rows)
    st = SB.stable_stretches(d, "mean_tgt", "act_targets", "sd_tgt")
    assert list(st.n) == [7, 6], "role jump at week 9 splits it"
    opening = {(2023, "T", w): ("A" if w < 6 else "B") for w in range(2, 15)}
    st2 = SB.stable_stretches(d, "mean_tgt", "act_targets", "sd_tgt", opening=opening)
    assert list(st2.n) == [4, 6], "a QB change at week 6 splits it too (the 3-game piece is too short)"


def test_a_what_if_volume_brings_its_own_spread():
    """When the user sets a player's volume, the spread follows the new average: the
    sampler's SD at 4 and at 10 expected targets matches the Dirichlet-multinomial on a
    negative-binomial team total (law of total variance)."""
    mu, r, conc = 34.0, 30.0, 40.0
    for exp_t in (4.0, 10.0):
        p = exp_t / mu
        out, _ = M.simulate_team_game(np.random.default_rng(9), 200_000, mu, r, {"a": p, "b": 0.3},
                                      {"a": 0.65, "b": 0.65}, {"a": 8.0, "b": 8.0}, 1.065,
                                      width={"share_conc_targets": conc}, return_targets=False)
        _out, _tt, tg = M.simulate_team_game(np.random.default_rng(9), 200_000, mu, r, {"a": p, "b": 0.3},
                                             {"a": 0.65, "b": 0.65}, {"a": 8.0, "b": 8.0}, 1.065,
                                             width={"share_conc_targets": conc}, return_targets=True)
        var_n = mu + mu ** 2 / r
        e_n2 = var_n + mu ** 2
        var_t = p * (1 - p) * (e_n2 + conc * mu) / (1 + conc) + p ** 2 * var_n
        assert abs(tg["a"].mean() - exp_t) < 0.05
        assert abs(tg["a"].std() - np.sqrt(var_t)) < 0.05, (exp_t, tg["a"].std(), np.sqrt(var_t))


def test_the_standin_check_joins_on_name_team_and_week():
    import standin_check as SC
    R = pd.DataFrame({"week": [3, 3, 4], "team": ["DAL", "DAL", "DAL"], "gsis_id": ["a", "b", "a"],
                      "L_rec": [5.5, 3.5, 4.5], "L_yds": [60.5, 30.5, 55.5]})
    posted = pd.DataFrame({"week": [3, 3, 4], "player": ["CeeDee Lamb", "Jake Ferguson", "CeeDee Lamb"],
                           "team": ["DAL"] * 3, "market": ["player_receptions", "player_reception_yds",
                                                           "player_reception_yds"],
                           "line": [6.5, 35.5, 70.5]})
    posted["key"] = posted.player.map(SC.norm_name)
    J = SC.join(R, posted, {"a": "CeeDee Lamb", "b": "Jake Ferguson"})
    got = {(r.player, r.market): r.gap for r in J.itertuples()}
    assert got == {("CeeDee Lamb", "player_receptions"): -1.0, ("Jake Ferguson", "player_reception_yds"): -5.0,
                   ("CeeDee Lamb", "player_reception_yds"): -15.0}
    s = SC.summary(J)
    assert s["player_reception_yds"]["within"] == 0.5 and s["player_receptions"]["within"] == 1.0


def test_round_30_picks_follow_the_registered_rule():
    import round30_select as R30
    base = {"eff_sd_rush": 0.3, "catch_conc": None, "catch_shape_mult": None}
    grid = [dict(base), {**base, "catch_conc": 100.0}, {**base, "catch_conc": 50.0}]
    noise = {0: 0.12, 1: 0.0, 2: 0.11}                 # catch_conc 100 is right by construction
    frames = [_world(noise[i], seed=20) for i in range(3)]
    v, i, table, move = R30.pick(grid, frames, "catch_conc", "receptions", {"eff_sd_rush": 0.3, "catch_shape_mult": None})
    assert v == 100.0 and i == 1 and move >= 1.0
    flat = [_world(0.0, seed=20) for _ in range(3)]   # identical frames: a tie keeps shipped
    v2, i2, _t, _m = R30.pick(grid, flat, "catch_conc", "receptions", {"eff_sd_rush": 0.3, "catch_shape_mult": None})
    assert v2 is None and i2 == 0


def test_round_31_never_narrows_past_the_real_spread():
    import round31_select as R31
    rows = [{"cfg": {"share_conc_targets": 40.0, "team_r_mult": None}, "ratios": [0.83, 0.88, 0.84]},
            {"cfg": {"share_conc_targets": 80.0, "team_r_mult": None}, "ratios": [0.95, 0.97, 0.96]},
            {"cfg": {"share_conc_targets": 120.0, "team_r_mult": 2.5}, "ratios": [1.01, 1.00, 0.99]},
            {"cfg": {"share_conc_targets": 80.0, "team_r_mult": 1.5}, "ratios": [0.955, 0.975, 0.96]}]
    pick = R31.choose(rows)
    assert pick["cfg"] == {"share_conc_targets": 80.0, "team_r_mult": None}, \
        "1.01 is past the upper bound; 80/1.5 ties 80 alone, which moves fewer knobs"
    assert R31.choose([{"cfg": {}, "ratios": [1.1, 1.2, 1.0]}]) is None


def test_the_decision_zone_is_scored_and_signs_must_agree():
    truth, noisy = _world(0.0, seed=30), _world(0.15, seed=30)
    c = SB.compare(noisy, truth, "game", reps=300)["receptions"]
    z = c["zone_c"]
    assert 0 < z["share"] < 1 and z["n"] < c["n"], "only cases whose reference chance is 15-85%"
    assert z["logloss"] < 0 and z["brier"] < 0 and z["agree"], "a noisier forecast loses in the zone too"


def test_the_combined_line_counts_pass_catching_backs_and_99_uses_10k():
    R = pd.DataFrame({"rush_pop": [True, True, True], "mean_car_model": [4.3, 12.0, 3.0],
                      "mean_tgt": [4.0, 1.0, 2.0]})
    assert SB.bettable(R, "rr").tolist() == [True, True, False], "touches, not carries alone"
    assert SB.bettable(R, "rb").tolist() == [False, True, False]


def test_exact_and_sampled_receptions_runs_are_never_compared():
    ref, cand = _world(0.0), _world(0.0)
    cand["pc_rec_exact"] = 1.0
    try:
        SB.compare(cand, ref, "game", reps=100)
        raise AssertionError("mixed scoring methods must be refused")
    except ValueError as e:
        assert "exactly" in str(e)


def test_a_capped_and_an_uncapped_harness_run_are_never_compared():
    ref, cand = _world(0.0), _world(0.0)
    cand["new_team_cap"] = True
    try:
        SB.compare(cand, ref, "game", reps=100)
        raise AssertionError("mixed harness versions must be refused")
    except ValueError as e:
        assert "different harnesses" in str(e)
    ref["new_team_cap"] = True
    assert SB.compare(cand, ref, "game", reps=100)["receptions"]["n"] == len(ref)
