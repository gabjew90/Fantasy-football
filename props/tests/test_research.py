"""props-v1.29 research columns (scripts/research.py): what a line implies, last
game's usage against earlier weeks, and the receiving role-shift flag."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ENGINE = Path(__file__).resolve().parents[1] / "engine" / "scripts"
sys.path.insert(0, str(ENGINE))

import model as M  # noqa: E402
import research as RS  # noqa: E402


def _p_over(targets, line, stat="receptions", team=34.0, share=0.2, cr=0.7, ypt=8.0):
    s = targets / team
    out, _ = M.simulate_team_game(np.random.default_rng(RS.SEED), RS.N_SEARCH, team, 30.0, {"p": s}, {"p": cr},
                                  {"p": ypt}, 1.06, other_bucket=True)
    return float((out["p"][0 if stat == "receptions" else 1] > line).mean())


def test_the_implied_targets_make_the_line_a_coin_flip():
    imp, proj = RS.implied_targets(4.5, "receptions", 34.0, 30.0, 0.2, 0.7, 8.0, 1.06)
    assert abs(proj - 6.8) < 1e-9, "projected targets = team targets x share"
    assert imp is not None and 5.0 < imp < 9.5
    assert abs(_p_over(imp, 4.5) - 0.5) < 0.03, "at the implied workload the Over is ~50%"


def test_a_higher_line_implies_more_targets():
    lo, _ = RS.implied_targets(3.5, "receptions", 34.0, 30.0, 0.2, 0.7, 8.0, 1.06)
    hi, _ = RS.implied_targets(5.5, "receptions", 34.0, 30.0, 0.2, 0.7, 8.0, 1.06)
    yds, _ = RS.implied_targets(60.5, "rec_yards", 34.0, 30.0, 0.2, 0.7, 8.0, 1.06)
    assert lo < hi and yds is not None


def test_a_line_outside_the_search_says_so_instead_of_guessing():
    imp, proj = RS.implied_targets(40.5, "receptions", 34.0, 30.0, 0.2, 0.7, 8.0, 1.06)
    assert imp is None and proj > 0


def test_the_search_never_touches_the_global_random_state():
    np.random.seed(1)
    before = np.random.random()
    np.random.seed(1)
    RS.implied_targets(4.5, "receptions", 34.0, 30.0, 0.2, 0.7, 8.0, 1.06)
    assert np.random.random() == before


def test_usage_change_needs_three_weeks_and_compares_the_last_with_the_rest():
    assert RS.usage_change([(1, 0.6, 0.2, 0.0), (2, 0.6, 0.2, 0.0)]) is None
    u = RS.usage_change([(1, 0.60, 0.20, 0.0), (2, 0.70, 0.20, 0.0), (3, 0.85, 0.21, 0.0)])
    assert u["week"] == 3 and abs(u["snap_base"] - 0.65) < 1e-12 and abs(u["ts_base"] - 0.20) < 1e-12


def test_the_role_flag_is_the_pre_registered_rule():
    up = RS.usage_change([(1, 0.60, 0.20, 0.0), (2, 0.60, 0.20, 0.0), (3, 0.80, 0.21, 0.0)])
    assert RS.role_flag(up, 3)[0] == "role up", "snaps +20 pts, targets +1 pt"
    assert RS.role_flag(up, 4) is None, "last week must be the week before this one"
    caught_up = RS.usage_change([(1, 0.60, 0.20, 0.0), (2, 0.60, 0.20, 0.0), (3, 0.80, 0.26, 0.0)])
    assert RS.role_flag(caught_up, 3) is None, "targets already followed the snaps"
    down = RS.usage_change([(1, 0.80, 0.20, 0.0), (2, 0.80, 0.20, 0.0), (3, 0.60, 0.19, 0.0)])
    assert RS.role_flag(down, 3)[0] == "role down"
    assert RS.role_flag(None, 3) is None


def test_the_scorers_research_block_never_draws_from_the_pricing_stream():
    """score_game prices every line from ONE sequential generator (`rng`); a draw
    from it in the research block would shift every recorded p_model. The
    block must reach randomness only through research.py's own generators."""
    src = (ENGINE / "score_game.py").read_text(encoding="utf-8")
    block = src[src.index("# ---------- 8a. research columns"):src.index("# ---------- 8b/9. report")]
    assert "rng" not in block and "random" not in block
    assert "pd.DataFrame(rows)" in block, "research rows come from this run's lines, not the prior-log merge"
    assert "ASSUME_OUT" in block, "no implied-workload search inside an 'if he's out' scenario run"


def test_backfield_jobs_compare_the_last_game_with_earlier_weeks():
    assert RS.backfield_jobs([(1, 0.6, 0.1, 0.5, 1, 2), (2, 0.6, 0.1, 0.5, 1, 2)]) is None
    b = RS.backfield_jobs([(1, 0.60, 0.30, 1.0, 2, 2), (2, 0.70, 0.10, float("nan"), 0, 0),
                           (3, 0.55, 0.00, 0.0, 0, 1)])
    assert b["week"] == 3 and abs(b["early_base"] - 0.65) < 1e-12 and abs(b["passdown_base"] - 0.20) < 1e-12
    assert b["i5_base"] == 1.0, "a week with no team inside-5 carry says nothing about his share"
    assert (b["i5_n"], b["i5_team"]) == (0, 1)


def test_the_role_flag_never_claims_an_adjustment_the_snap_rule_skips():
    u = RS.usage_change([(1, 0.03, 0.02, 0.0), (2, 0.03, 0.02, 0.0), (3, 0.30, 0.03, 0.0)])
    assert RS.role_flag(u, 3) is None, "earlier snaps under 5%: model.snap_react does not act, so no flag"
    assert M.snap_react(0.02, 0.30, 0.03, 0.5) == 0.02
