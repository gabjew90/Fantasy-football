"""Round 22: a player's in-season share counts only the weeks every KEY
teammate active this week also played (model.coactive_weeks, model.key_share,
the scorer and harness wiring)."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ENGINE = Path(__file__).resolve().parents[1] / "engine" / "scripts"
sys.path.insert(0, str(ENGINE))

import model as M  # noqa: E402


def test_coactive_weeks_keeps_only_weeks_every_key_mate_played():
    # HOU 2026: Schultz active weeks 1-3, Collins active week 1 only
    assert M.coactive_weeks([1, 2, 3], [[1]]) == [1]
    assert M.coactive_weeks([1, 2, 3], [[1, 3], [3]]) == [3], "every key mate, not any"
    assert M.coactive_weeks([1, 2, 3], []) == [1, 2, 3], "no key mates: every week kept"
    assert M.coactive_weeks([2, 3], [[1]]) == [], "never played together: no in-season share evidence"


def test_key_share_prefers_the_prior_then_the_season_then_zero():
    assert M.key_share(0.25, 10, 37) == 0.25, "prior-season share decides when he has one"
    assert abs(M.key_share(float("nan"), 10, 40) - 0.25) < 1e-12, "no prior: in-season share"
    assert M.key_share(None, None, None) == 0.0
    assert M.key_share(None, 3, 0) == 0.0, "no team volume: not key"


def test_off_by_default_until_the_harness_says_otherwise():
    # the thresholds are filled only after the pre-registered harness run
    # (reports/returning_teammate.md); None is the pre-round-21 model
    for v in (M.KEY_TEAMMATE_TS, M.KEY_TEAMMATE_RS):
        assert v is None or 0.0 < v < 1.0


def test_scorer_and_harness_share_the_same_rule():
    sg = (ENGINE / "score_game.py").read_text(encoding="utf-8")
    bt = (ENGINE / "backtest.py").read_text(encoding="utf-8")
    for src, name in ((sg, "score_game"), (bt, "backtest")):
        assert "M.coactive_weeks(" in src or "MODEL.coactive_weeks(" in src, name
        assert "key_share(" in src, name
    # the harness never reads a feature cache built without the filter
    assert re.search(r'key \+= f"_kt\{kt_ts\}-\{kt_rs\}"', bt)
    # baseline A stays on the raw full-window shares
    assert "shareA = tr.raw_ts" in bt and "test_act.raw_rs" in bt
