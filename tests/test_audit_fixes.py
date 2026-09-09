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
    """lineup_opt calls apply() after waiver_brief has already run it, and it
    RENDERS the notes it gets back. A per-row guard that skipped silently
    would hand it a clean bill of health for a lineup holding clamped rows,
    so the warning has to describe the data rather than the mutation."""
    con = {"x": {"mean": 300.0, "n": 3, "spread": 5.0, "per_source": {}}}
    ctx = {"roster_players": {1: [_row("x", 100.0, 10.0)]}}
    for pass_no in (1, 2, 3):
        notes = consensus.apply(ctx, con)[1]
        assert any("clamped" in n for n in notes), f"pass {pass_no}: {notes}"
        assert any(n.startswith("⚠") for n in notes), f"pass {pass_no} not visible"


def test_a_clean_roster_never_reports_a_clamp():
    con = {"x": {"mean": 120.0, "n": 3, "spread": 5.0, "per_source": {}}}
    ctx = {"roster_players": {1: [_row("x", 100.0, 10.0)]}}
    for _ in range(3):
        assert not any("clamped" in n for n in consensus.apply(ctx, con)[1])


def test_an_unclamped_row_is_still_applied_exactly_once():
    con = {"x": {"mean": 120.0, "n": 3, "spread": 5.0, "per_source": {}}}
    ctx = {"roster_players": {1: [_row("x", 100.0, 10.0)]}}
    for _ in range(3):
        consensus.apply(ctx, con)
    r = ctx["roster_players"][1][0]
    assert (r["ros_season"], r["weekly"]) == (120.0, 12.0)


# -------------------------- 4. zero vs absent (fix attempted, then REVERTED:
#                               these sources encode 'unpriced' as 0, so a zero
#                               is not an opinion. See consensus.build.)

def test_a_consensus_at_nothing_zeroes_the_row_rather_than_clamping_it_up():
    """When the sources do price a player at nothing, that is a fact about
    him and must not be clamped up to 60% of a stale August number. Reachable
    only when every source carries a real near-zero price -- an unpriced row
    is excluded from the blend, see the comment in consensus.build."""
    con = {"x": {"mean": 0.4, "n": 3, "spread": 0.2, "per_source": {}}}
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


def test_an_unpriced_zero_does_not_drag_the_mean(monkeypatch):
    """Counting zeroes as opinions was tried on 2026-09-08 and reverted. The
    FantasyPros sheet writes proj_pts 0 for board players it has not priced:
    Josh Jacobs sits at 0 with an ADP of 37.2, and blending it took him from
    110.3 to 73.5 along with Kamara, Conner, Pacheco, Njoku and Charbonnet."""
    hi = {str(i): 100.0 + i for i in range(60)}
    zero = dict.fromkeys(hi, 0.0)
    monkeypatch.setattr(consensus, "_sleeper", lambda s, y: (hi, None))
    monkeypatch.setattr(consensus, "_espn", lambda s, y, r, i: (zero, None))
    ctx = {"cfg": _Cfg(), "state": {"season": "2026"}, "players": {}}
    data, _ = consensus.build(ctx)
    assert data["30"]["n"] == 1
    assert data["30"]["mean"] == 130.0, "an unpriced row was blended in"


class _Cfg(dict):
    league_name = "x"

    def path(self, kind):
        return "data/raw"


# --------------------------------------- 6. the header counts contributing sources

def test_a_source_that_matches_nobody_is_flagged_not_counted(monkeypatch):
    hi = {str(i): 100.0 + i for i in range(60)}
    monkeypatch.setattr(consensus, "_sleeper", lambda s, y: (hi, None))
    monkeypatch.setattr(consensus, "_espn", lambda s, y, r, i: ({}, None))
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


# ------------------------------- 2026-09-09 review: the degrade paths themselves

def test_a_total_projection_outage_is_visible_in_the_brief(monkeypatch):
    """consensus emits "DATA MISSING: no projection source reachable", which
    does not start with the warning glyph. waiver_brief and lineup_opt both
    filtered con_notes on that glyph alone, so a complete outage rendered a
    brief with no warning while it ran on nothing."""
    monkeypatch.setattr(consensus, "_sources", lambda c, sc, se, ix: (
        ("sleeper", ({}, "down")), ("espn", ({}, "down"))))
    ctx = {"cfg": _Cfg(), "state": {"season": "2026"}, "players": {}}
    data, notes = consensus.build(ctx)
    assert data == {}
    surfaced = [n for n in notes
                if n.startswith("⚠") or n.startswith("DATA MISSING")]
    assert surfaced, f"nothing would reach the reader: {notes}"


def test_the_pid_error_handler_does_not_itself_throw():
    """Building the message with p.items() raised AttributeError for a str,
    int or list -- an error about the error, replacing the one that named the
    actual bad row."""
    for bad in (None, "abc", 7, [1, 2], {"pos": "RB"}, {"pos": "RB", "x": {1, 2}}):
        with pytest.raises(KeyError, match="sleeper_id"):
            marginal._pid(bad)


# ------------------------------------------ 2026-09-09: tradeable ranks on surplus

def test_tradeable_ranks_the_biggest_misallocation_first_not_the_best_ratio():
    """cost 10 / gain 20 is ratio 2.0 but surplus +10; cost 100 / gain 150 is
    ratio 1.5 but surplus +50. The first look is asking where a trade can
    CREATE the most value, and that is the +50, not the 2.0."""
    shape = {"slots": {"RB": 1, "WR": 1}, "flex": 0}
    mine = [{"sleeper_id": "cheap", "pos": "RB", "weekly": 30.0, "name": "cheap"},
            {"sleeper_id": "rb_bk", "pos": "RB", "weekly": 20.0, "name": "rb_bk"},
            {"sleeper_id": "big", "pos": "WR", "weekly": 200.0, "name": "big"},
            {"sleeper_id": "wr_bk", "pos": "WR", "weekly": 100.0, "name": "wr_bk"}]
    # rival needs both: an RB at 10 (cheap gains him 20) and a WR at 50 (big gains 150)
    others = {"rival": [{"sleeper_id": "r_rb", "pos": "RB", "weekly": 10.0, "name": "r_rb"},
                        {"sleeper_id": "r_wr", "pos": "WR", "weekly": 50.0, "name": "r_wr"}]}
    ranked = marginal.tradeable(mine, others, shape)
    by_id = {r["player"]["sleeper_id"]: r for r in ranked}
    assert by_id["cheap"]["surplus"] == 10.0 and by_id["cheap"]["ratio"] == 2.0
    assert by_id["big"]["surplus"] == 50.0 and by_id["big"]["ratio"] == 1.5
    order = [r["player"]["sleeper_id"] for r in ranked if r["buyers"] > 0]
    assert order.index("big") < order.index("cheap"), \
        [(r["player"]["name"], r["surplus"], r["ratio"]) for r in ranked]


def test_surplus_is_gain_minus_cost_and_carried_on_every_row():
    shape = {"slots": {"RB": 1}, "flex": 0}
    mine = [{"sleeper_id": "star", "pos": "RB", "weekly": 20.0, "name": "star"},
            {"sleeper_id": "spare", "pos": "RB", "weekly": 12.0, "name": "spare"}]
    others = {"rival": [{"sleeper_id": "r1", "pos": "RB", "weekly": 1.0, "name": "r1"}]}
    for r in marginal.tradeable(mine, others, shape):
        assert r["surplus"] == round(r["best_gain"] - r["cost"], 1), r
