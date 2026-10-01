"""Round 14: last season's defense as the point this season's defense is
shrunk toward (model.opponent_multiplier, prior_table / prior_carry).

carry 0 is the pre-round-14 adjustment, byte for byte; above 0 the target
moves from league average toward last season's own shrunk ratio, and a defense
with no plays yet this season gets the target alone."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

ENGINE = Path(__file__).resolve().parents[1] / "engine" / "scripts"
sys.path.insert(0, str(ENGINE))

import model as M  # noqa: E402


def _tab(rows):
    """rows: (team, metric, n, value, league)."""
    return pd.DataFrame([{"team": t, "posgrp": "ALL", "metric": m, "n": n, "value": v, "league": lg}
                         for t, m, n, v, lg in rows])


CUR = _tab([("PIT", "ypt", 77, 8.221, 7.447), ("PIT", "ypc", 75, 4.56, 4.332)])
LAST = _tab([("PIT", "ypt", 550, 7.10, 7.30), ("PIT", "ypc", 450, 4.00, 4.30),
             ("CLE", "ypt", 560, 8.00, 7.30)])


def _old(tab, team, met, k0=150.0):
    r = tab[(tab.team == team) & (tab.metric == met)].iloc[0]
    w = r.n / (r.n + k0)
    return (1 - w) + (r.value / r.league) * w


def test_carry_zero_is_the_old_adjustment_exactly():
    for met in ("ypt", "ypc"):
        assert M.opponent_multiplier(CUR, "PIT", "ALL", met) == _old(CUR, "PIT", met)
        assert M.opponent_multiplier(CUR, "PIT", "ALL", met, prior_table=LAST, prior_carry=0.0) == _old(CUR, "PIT", met)
    assert M.OPP_PRIOR_CARRY == 0.0, "the shipped default changes only with a measured round-14 verdict"


def test_the_target_moves_toward_last_seasons_shrunk_ratio():
    last = _old(LAST, "PIT", "ypc")                       # a stingy run defense last year: below 1
    w = 75 / (75 + 150)
    for c in (0.5, 1.0):
        target = 1 + c * (last - 1)
        want = target * (1 - w) + (4.56 / 4.332) * w
        assert M.opponent_multiplier(CUR, "PIT", "ALL", "ypc", prior_table=LAST, prior_carry=c) == pytest.approx(want)
    lo = M.opponent_multiplier(CUR, "PIT", "ALL", "ypc", prior_table=LAST, prior_carry=1.0)
    assert lo < _old(CUR, "PIT", "ypc"), "a good run defense last season pulls this season's multiplier down"


def test_no_plays_yet_this_season_gives_the_target_alone():
    empty = CUR.iloc[0:0]
    t = M.opponent_multiplier(empty, "CLE", "ALL", "ypt", prior_table=LAST, prior_carry=0.5)
    assert t == pytest.approx(1 + 0.5 * (_old(LAST, "CLE", "ypt") - 1))
    assert M.opponent_multiplier(CUR, "CLE", "ALL", "ypt", prior_table=LAST, prior_carry=0.5) == pytest.approx(t), \
        "a team missing from this season's table also gets the target"
    assert M.opponent_multiplier(empty, "CLE", "ALL", "ypt") == 1.0, "no prior, no carry: league average"
    assert M.opponent_multiplier(CUR, "NYJ", "ALL", "ypt", prior_table=LAST, prior_carry=1.0) == 1.0, \
        "a team in neither table is league average"
