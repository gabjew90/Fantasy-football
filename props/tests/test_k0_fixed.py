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


def test_an_explicit_override_wins_and_an_empty_one_is_the_fit():
    fitted = {"ypt": 160, "catch_rate": 40}
    assert M.k0_rates(fitted, override={})["ypt"] == 160, "override {} = the per-season fit, as before round 17"
    assert M.k0_rates(fitted, override={"ypt": 20.0})["ypt"] == 20.0
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
    assert M.k0_rates({"target_share": 20, "i10_target_share": 2}, override={"ypt": 40.0})["i10_target_share"] == 2

