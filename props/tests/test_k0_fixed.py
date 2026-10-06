"""Round 17: fixed shrinkage constants for yards per target and catch rate
over build_priors.py's per-season fit (model.K0_FIXED, model.k0_rates)."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ENGINE = Path(__file__).resolve().parents[1] / "engine" / "scripts"
sys.path.insert(0, str(ENGINE))

import model as M  # noqa: E402


def test_the_fixed_constants_replace_only_the_rates_they_name():
    fitted = {"target_share": 80, "catch_rate": 320, "ypt": 640, "rush_share": 40, "ypc": 80}
    out = M.k0_rates(fitted)
    assert out["ypt"] == 80 and out["catch_rate"] == 40, "the unstable fits are replaced"
    assert out["target_share"] == 80, "round 18: target share fixed too"
    assert out["rush_share"] == 40 and out["ypc"] == 80, "the rest are the fit"
    assert fitted["ypt"] == 640, "the priors' dict is not mutated"


def test_an_explicit_override_wins_and_keeps_the_other_shipped_constants():
    """Outside review 2026-10-06: overriding rush_share alone used to restore the fitted
    receiving constants (640/320/320) instead of the shipped 80/40/80."""
    fitted = {"ypt": 640, "catch_rate": 320, "target_share": 320, "rush_share": 40}
    out = M.k0_rates(fitted, override={"rush_share": 20.0})
    assert out["rush_share"] == 20.0
    assert (out["ypt"], out["catch_rate"], out["target_share"]) == (80, 40, 80), "the rest stay shipped"
    assert M.k0_rates(fitted, override={"ypt": 20.0})["ypt"] == 20.0
    assert M.k0_rates(fitted, override={}) == M.k0_rates(fitted), "an empty override is the shipped set"
    assert M.k0_rates(fitted, fit_only=True)["ypt"] == 640, "the named ablation: the per-season fit alone"
    assert M.k0_rates(None)["ypt"] == M.K0_FIXED["ypt"], "no fit: DEFAULT_K0, then the fixed constants"


def test_the_shipped_constants_and_both_call_sites():
    assert M.K0_FIXED == {"ypt": 80, "catch_rate": 40, "target_share": 80}
    sg = (ENGINE / "score_game.py").read_text(encoding="utf-8")
    bt = (ENGINE / "backtest.py").read_text(encoding="utf-8")
    assert re.search(r"K0R = MODEL\.k0_rates\(P\.get\(\"k0_per_rate\"", sg), "the scorer applies K0_FIXED"
    assert re.search(r"K0R = M\.k0_rates\(P0\.get\(\"k0_per_rate\"", bt), "the harness applies it too"


def test_the_goal_line_constant_follows_a_fixed_share_constant():
    out = M.k0_rates({"target_share": 20, "i10_target_share": 2, "ypt": 160, "catch_rate": 40})
    assert out["target_share"] == 80 and out["i10_target_share"] == 8, "2 x 80/20, as build_priors would"
    same = M.k0_rates({"target_share": 80, "i10_target_share": 5, "ypt": 160, "catch_rate": 40})
    assert same["i10_target_share"] == 5, "this season's fit (80 -> 5) is unchanged"
    assert M.k0_rates({"target_share": 20, "i10_target_share": 2}, override={"ypt": 40.0})["i10_target_share"] == 8, \
        "a partial override keeps the fixed target share, so its goal-line constant follows"
    assert M.k0_rates({"target_share": 20, "i10_target_share": 2}, fit_only=True)["i10_target_share"] == 2



def test_the_harness_applies_the_scorers_new_team_cap():
    """Outside review 2026-10-06 (finding 4): the scorer caps a carried-over prior for a
    player on a new team (blended_rate new_team); the harness now passes it too."""
    bt = (ENGINE / "backtest.py").read_text(encoding="utf-8")
    assert re.search(r"cur_rate=cur, cur_den=cur_n, scale_role=scale_role, new_team=new_team\)", bt)
    assert "--no-new-team-cap" in bt, "the ablation stays reachable"
    a = M.blended_rate(0.30, 400, 0.15, 80, cur_rate=0.20, cur_den=60)[0]
    b = M.blended_rate(0.30, 400, 0.15, 80, cur_rate=0.20, cur_den=60, new_team=True)[0]
    assert round(a, 5) == 0.24286 and round(b, 5) == 0.21429, "the review's worked example"
