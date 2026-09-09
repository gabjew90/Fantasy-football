"""The nine defects the 2026-09-08 end-to-end audit found, pinned.

Each test states the wrong behaviour it forbids, because every one of these
shipped numbers to a real decision and a regression would do it again
silently.
"""

from __future__ import annotations

import pytest

from draftkit.lineup import optimal_lineup
from manager import consensus, marginal
from manager import waiver_brief as wb


# ------------------------------------------------- 1. the clamp survives apply

def _row(pid, season, weekly):
    return {"sleeper_id": pid, "pos": "RB", "name": pid,
            "ros_season": season, "ros": season, "weekly": weekly}


def test_repeated_apply_cannot_walk_a_clamped_ratio_to_its_full_value():
    """apply() mutates the shared roster dicts in place, and waiver_brief and
    lineup_opt both call it on one ctx. Re-deriving the ratio from the
    already-rebased base used to march a clamped row 160 -> 256 -> 300 and
    then stop warning, because by the third call the ratio really was 1.0."""
    con = {"x": {"mean": 300.0, "n": 3, "spread": 5.0, "per_source": {}}}
    ctx = {"roster_players": {1: [_row("x", 100.0, 10.0)]}}
    seen = []
    for _ in range(4):
        consensus.apply(ctx, con)
        r = ctx["roster_players"][1][0]
        seen.append((r["ros_season"], r["weekly"]))
    assert seen == [(160.0, 16.0)] * 4, seen


def test_the_clamp_warning_does_not_evaporate_on_a_second_pass():
    con = {"x": {"mean": 300.0, "n": 3, "spread": 5.0, "per_source": {}}}
    ctx = {"roster_players": {1: [_row("x", 100.0, 10.0)]}}
    first = consensus.apply(ctx, con)[1]
    assert any("clamped" in n for n in first)


def test_an_unclamped_row_is_still_applied_exactly_once():
    con = {"x": {"mean": 120.0, "n": 3, "spread": 5.0, "per_source": {}}}
    ctx = {"roster_players": {1: [_row("x", 100.0, 10.0)]}}
    for _ in range(3):
        consensus.apply(ctx, con)
    r = ctx["roster_players"][1][0]
    assert (r["ros_season"], r["weekly"]) == (120.0, 12.0)


# ----------------------------------------- 4. a source saying zero says something

def test_all_sources_at_zero_zeroes_the_row_rather_than_clamping_it_up():
    """Pearsall: season-ending surgery, every live source at 0, and the board
    kept his August 148.7 because each zero was discarded as no-coverage.
    Clamping 0/148.7 to the 0.60 floor would have been just as wrong."""
    con = {"x": {"mean": 0.0, "n": 3, "spread": 0.0, "per_source": {}}}
    ctx = {"roster_players": {1: [_row("x", 148.7, 9.0)]}}
    _, notes = consensus.apply(ctx, con)
    r = ctx["roster_players"][1][0]
    assert (r["ros_season"], r["ros"], r["weekly"]) == (0.0, 0.0, 0.0)
    assert any("zeroed" in n for n in notes)


def test_one_source_at_zero_is_not_enough_to_zero_a_player():
    con = {"x": {"mean": 0.0, "n": 1, "spread": 0.0, "per_source": {}}}
    ctx = {"roster_players": {1: [_row("x", 148.7, 9.0)]}}
    consensus.apply(ctx, con)
    assert ctx["roster_players"][1][0]["ros_season"] == 148.7


def test_build_counts_a_zero_as_coverage(monkeypatch):
    hi = {str(i): 100.0 + i for i in range(60)}
    zero = dict.fromkeys(hi, 0.0)
    monkeypatch.setattr(consensus, "_sleeper", lambda s, y: (hi, None))
    monkeypatch.setattr(consensus, "_espn", lambda s, y, r, i: (zero, None))
    monkeypatch.setattr(consensus, "_sheet", lambda c: ({}, None))
    ctx = {"cfg": _Cfg(), "state": {"season": "2026"}, "players": {}}
    data, _ = consensus.build(ctx)
    assert data["30"]["n"] == 2, "a source that said zero was dropped as absent"


class _Cfg(dict):
    league_name = "x"

    def path(self, kind):
        return "data/raw"


# --------------------------------------- 6. the header counts contributing sources

def test_a_source_that_matches_nobody_is_flagged_not_counted(monkeypatch):
    hi = {str(i): 100.0 + i for i in range(60)}
    monkeypatch.setattr(consensus, "_sleeper", lambda s, y: (hi, None))
    monkeypatch.setattr(consensus, "_espn", lambda s, y, r, i: ({}, None))
    monkeypatch.setattr(consensus, "_sheet", lambda c: ({}, None))
    ctx = {"cfg": _Cfg(), "state": {"season": "2026"}, "players": {}}
    _, notes = consensus.build(ctx)
    assert any("consensus over 1 live sources" in n for n in notes), notes


# ------------------------------------------------ 3. tradeable ranks free first

def test_a_free_asset_a_rival_wants_is_the_top_trade_chip_not_the_bottom():
    """cost 0 / gain 20 scored (0, -20) and lost to cost 5 / gain 10 at
    (-2.0, -10), so the best chip on the board sorted last."""
    shape = {"slots": {"RB": 1}, "flex": 0}
    mine = [{"sleeper_id": "star", "pos": "RB", "weekly": 20.0, "name": "star"},
            {"sleeper_id": "spare", "pos": "RB", "weekly": 12.0, "name": "spare"}]
    # a rival with nothing at RB: both of mine would improve his lineup, but
    # only `spare` costs me nothing to give up
    others = {"rival": [{"sleeper_id": "r1", "pos": "RB", "weekly": 1.0, "name": "r1"}]}
    ranked = marginal.tradeable(mine, others, shape)
    assert ranked[0]["player"]["sleeper_id"] == "spare", \
        [(r["player"]["name"], r["cost"], r["best_gain"], r["ratio"]) for r in ranked]
    assert ranked[0]["cost"] == 0.0 and ranked[0]["best_gain"] > 0


def test_a_free_asset_nobody_wants_does_not_jump_the_queue():
    shape = {"slots": {"RB": 1}, "flex": 0}
    mine = [{"sleeper_id": "star", "pos": "RB", "weekly": 20.0, "name": "star"},
            {"sleeper_id": "junk", "pos": "RB", "weekly": 0.5, "name": "junk"}]
    others = {"rival": [{"sleeper_id": "r1", "pos": "RB", "weekly": 15.0, "name": "r1"}]}
    ranked = marginal.tradeable(mine, others, shape)
    assert ranked[-1]["player"]["sleeper_id"] == "junk"


# ------------------------------------------------- 8. non-nested flex is searched

def test_greedy_flex_order_does_not_decide_a_non_nested_lineup():
    """{RB,WR} and {WR,TE} are the same size and neither contains the other,
    so size ordering picks arbitrarily: filling {RB,WR} first scores 23 and
    filling {WR,TE} first scores 25."""
    roster = [{"sleeper_id": "w", "pos": "WR", "weekly": 20.0},
              {"sleeper_id": "r", "pos": "RB", "weekly": 5.0},
              {"sleeper_id": "t", "pos": "TE", "weekly": 3.0}]
    for order in ((("RB", "WR"), ("WR", "TE")), (("WR", "TE"), ("RB", "WR"))):
        got = optimal_lineup(roster, {}, flex_slots=order)
        assert sum(p["weekly"] for p in got) == 25.0, order


def test_the_nested_case_is_unchanged():
    roster = [{"sleeper_id": "a", "pos": "WR", "weekly": 20.0},
              {"sleeper_id": "b", "pos": "RB", "weekly": 15.0},
              {"sleeper_id": "c", "pos": "TE", "weekly": 9.0}]
    got = optimal_lineup(roster, {"WR": 1}, flex=1)
    assert sum(p["weekly"] for p in got) == 35.0


# -------------------------------- 9. an exact tie credits NEITHER player (audit
#                                      finding 9 was a false positive: `second`
#                                      in a tie is the OTHER tied player, not
#                                      the next distinct value, so this was
#                                      always right. Pinned so it stays right.)

def test_two_free_agents_tied_at_the_top_are_both_worth_nothing():
    """Claiming one of two identical free RBs gains you nothing, because the
    other is still sitting there. The gap down to 85.0 only becomes real
    once one of them is gone."""
    pool = [{"sleeper_id": "a", "pos": "RB", "ros": 96.5},
            {"sleeper_id": "b", "pos": "RB", "ros": 96.5},
            {"sleeper_id": "c", "pos": "RB", "ros": 85.0}]
    lv = wb.fa_replacement_levels(pool)
    vals = [wb.value_over_fa(p, lv) for p in pool]
    assert vals == [0.0, 0.0, pytest.approx(-11.5)], vals


def test_a_lone_leader_is_worth_his_gap_to_the_next_man():
    pool = [{"sleeper_id": "a", "pos": "RB", "ros": 96.5},
            {"sleeper_id": "c", "pos": "RB", "ros": 85.0}]
    lv = wb.fa_replacement_levels(pool)
    assert wb.value_over_fa(pool[0], lv) == pytest.approx(11.5)
    assert lv["RB"][2] == "a", "the leader is identified by id, not by value"


# ------------------------------- 2. the matchup adjustment survives the rebase

def test_the_opponent_adjustment_is_not_cancelled_by_the_consensus_rebase():
    """draftkit/briefs.py built the fallback season base as `wk * 16`, and wk
    already carried the matchup multiplier. apply() then divided the
    consensus mean by that base and multiplied weekly back, so the algebra
    collapsed to weekly = mean/16 and two players with identical season
    numbers came out identical no matter who they were playing.

    The base is now base_pts(pid) * 16, which is unadjusted, so the ratio is
    the same for both and their weeklies stay in proportion.
    """
    base_weekly, mean = 10.0, 200.0
    soft, hard = 1.20, 0.85           # opponent-defense multipliers
    con = {"soft": {"mean": mean, "n": 3, "spread": 1.0, "per_source": {}},
           "hard": {"mean": mean, "n": 3, "spread": 1.0, "per_source": {}}}
    ctx = {"roster_players": {1: [
        # ros_season is the UNADJUSTED base_pts * 16 for both, as briefs now
        # builds it; only `weekly` carries the multiplier
        _row("soft", base_weekly * 16, base_weekly * soft),
        _row("hard", base_weekly * 16, base_weekly * hard),
    ]}}
    consensus.apply(ctx, con)
    got = {r["sleeper_id"]: r["weekly"] for r in ctx["roster_players"][1]}
    assert got["soft"] > got["hard"], got
    assert got["soft"] / got["hard"] == pytest.approx(soft / hard, rel=1e-3)


# ---------------------------------- 5. absence is only evidence where we looked

def test_a_reserve_kicker_is_not_deleted_by_a_qb_rb_wr_te_consensus():
    for pos in ("K", "DEF"):
        assert wb._stale_reserve(
            {"active": True, "injury_status": "IR", "position": pos}, {}, "1") is False
