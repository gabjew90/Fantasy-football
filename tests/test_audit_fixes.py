"""The nine defects the 2026-09-08 end-to-end audit found, pinned.

(Findings 3, 5 and 9 pinned manager.marginal and manager.waiver_brief, retired
with the cron stack on 2026-10-08, DECISIONS #212; their tests went with them.)

Each test states the wrong behaviour it forbids, because every one of these
shipped numbers to a real decision and a regression would do it again
silently.
"""

from __future__ import annotations

import pytest

from draftkit.lineup import optimal_lineup
from manager import consensus


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


