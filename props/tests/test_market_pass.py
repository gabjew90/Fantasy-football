"""Round 16: the market's fitted pass volume at MARKET_PASS_WEIGHT, carries
untouched (model.market_pass_volume, model.team_spread_from_home)."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

ENGINE = Path(__file__).resolve().parents[1] / "engine" / "scripts"
sys.path.insert(0, str(ENGINE))

import model as M  # noqa: E402

FIT = {"plays": {"intercept": 47.8, "per_spread_pt": 0.146, "per_total_pt": 0.2005},
       "pass_rate": {"intercept": 0.371, "per_spread_pt": -0.0022, "per_total_pt": 0.00377}}


def test_the_home_spread_converts_to_positive_is_favoured():
    # the scorer's home spread: NEGATIVE = home favoured (implied home points = (total - hs) / 2)
    assert M.team_spread_from_home(-7.0, is_home=True) == 7.0, "a 7-point home favourite"
    assert M.team_spread_from_home(-7.0, is_home=False) == -7.0, "its opponent, a 7-point underdog"
    fav = M.market_pass_volume(M.team_spread_from_home(-7.0, True), 44.5, FIT, 33.0, 26.0, 1.0)[0]
    dog = M.market_pass_volume(M.team_spread_from_home(-7.0, False), 44.5, FIT, 33.0, 26.0, 1.0)[0]
    assert dog > fav, "the underdog is fitted to throw more than the favourite"


def test_weight_zero_and_no_fit_are_the_history_and_carries_never_move():
    assert M.market_pass_volume(3.0, 44.5, FIT, 33.0, 26.0, 0.0) == (33.0, 26.0)
    assert M.market_pass_volume(3.0, 44.5, {}, 33.0, 26.0, 0.25) == (33.0, 26.0)
    for w in (0.25, 0.5, 1.0):
        assert M.market_pass_volume(-6.0, 41.0, FIT, 38.0, 22.0, w)[1] == 22.0


def test_the_weight_blends_linearly_toward_the_fitted_targets():
    full = M.market_pass_volume(0.0, 44.5, FIT, 33.0, 26.0, 1.0)[0]
    quarter = M.market_pass_volume(0.0, 44.5, FIT, 33.0, 26.0, 0.25)[0]
    assert quarter == pytest.approx(0.75 * 33.0 + 0.25 * full)


def test_the_shipped_weight_and_the_scorer_reads_it():
    assert M.MARKET_PASS_WEIGHT == 0.25
    src = (ENGINE / "score_game.py").read_text(encoding="utf-8")
    assert re.search(r"MODEL\.market_pass_volume\(\s*MODEL\.team_spread_from_home\(hs, t == HOME\)", src)
    assert "MODEL.MARKET_PASS_WEIGHT)" in src


def test_the_bundled_priors_carry_the_market_fit():
    P = json.loads((ENGINE.parent / "resources" / "priors_2025_params.json").read_text(encoding="utf-8"))
    fit = P["market_env_fit"]
    assert fit["pass_rate"]["per_spread_pt"] < 0, "favourites (positive spread) throw less"
