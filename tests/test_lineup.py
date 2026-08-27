"""Lineup + early-games briefs (season spec Task 6)."""

import pytest

from draftkit.lineup import lineup_changes, variance_pick, render_lineup_brief

SLOTS = {"QB": 1, "RB": 2, "WR": 2, "TE": 1, "K": 1, "DEF": 1}


def _p(pid, name, pos, weekly, stdev=4.0, team="SFO"):
    return {"sleeper_id": pid, "name": name, "pos": pos, "weekly": weekly,
            "stdev": stdev, "team": team}


ROSTER = [
    _p("q1", "QB A", "QB", 20), _p("r1", "RB A", "RB", 15), _p("r2", "RB B", "RB", 14),
    _p("r3", "RB C", "RB", 12), _p("w1", "WR A", "WR", 13), _p("w2", "WR B", "WR", 11),
    _p("w3", "WR C", "WR", 9), _p("t1", "TE A", "TE", 8), _p("k1", "K A", "K", 7),
    _p("d1", "DEF A", "DEF", 6),
]


def test_lineup_changes_only_diffs():
    current = ["q1", "r1", "r2", "w1", "w2", "t1", "r3", "w3", "k1", "d1"]  # already optimal
    changes, total = lineup_changes(ROSTER, current, SLOTS, flex=2)
    assert changes == []
    # bench the better RB C for WR C in flex -> one suggested swap
    worse = ["q1", "r1", "r2", "w1", "w2", "t1", "w3", "w3", "k1", "d1"]
    changes2, total2 = lineup_changes(ROSTER, worse, SLOTS, flex=2)
    assert any("RB C" in c for c in changes2)


def test_variance_lean_breaks_only_close_calls():
    steady = _p("a", "Steady", "WR", 12.0, stdev=2.0)
    boom = _p("b", "Boom", "WR", 11.0, stdev=8.0)
    # underdog by 12: prefer ceiling in close calls
    assert variance_pick(steady, boom, margin=-12.0, close_gap=2.5)["name"] == "Boom"
    # favorite by 12: prefer floor
    assert variance_pick(steady, boom, margin=12.0, close_gap=2.5)["name"] == "Steady"
    # not a close call (gap 5 > 2.5): projection wins regardless of margin
    far = _p("c", "Far", "WR", 17.0, stdev=9.0)
    assert variance_pick(far, steady, margin=12.0, close_gap=2.5)["name"] == "Far"


def test_brief_orders_inactive_flags_by_kickoff():
    model = {
        "week": 1, "opp_name": "rybryethguy", "my_total": 118.2, "opp_total": 104.9,
        "changes": [], "lean": "favorite — prefer floor in close calls",
        "flags": [
            {"name": "Late Guy", "status": "Questionable", "kick": "2026-09-13 16:25", "backup": "Bench Y"},
            {"name": "Early Guy", "status": "Questionable", "kick": "2026-09-10 20:15", "backup": "Bench X"},
        ],
        "warnings": ["FLEX slot is EMPTY"], "stale": [], "early_teams": [],
    }
    md = render_lineup_brief(model)
    assert md.index("Early Guy") < md.index("Late Guy")  # kickoff order
    assert "FLEX slot is EMPTY" in md and "118.2" in md


def test_swap_pairing_is_position_aware():
    from draftkit.lineup import lineup_changes
    slots = {"QB": 0, "RB": 1, "WR": 1, "TE": 0, "K": 0, "DEF": 0}
    roster = [
        {"sleeper_id": "w1", "name": "Better WR", "pos": "WR", "weekly": 12.0},
        {"sleeper_id": "w2", "name": "Worse WR", "pos": "WR", "weekly": 8.0},
        {"sleeper_id": "r1", "name": "Better RB", "pos": "RB", "weekly": 11.0},
        {"sleeper_id": "r2", "name": "Worse RB", "pos": "RB", "weekly": 9.0},
    ]
    changes, _ = lineup_changes(roster, ["w2", "r2"], slots, flex=0)
    text = " | ".join(changes)
    # WR pairs with WR, RB with RB — never a cross-position negative "gain"
    assert "Better WR over Worse WR" in text and "Better RB over Worse RB" in text
    assert "+-" not in text
