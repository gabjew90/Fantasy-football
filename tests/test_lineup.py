"""Lineup + early-games briefs (season spec Task 6)."""

import pytest

from draftkit.lineup import lineup_changes, render_lineup_brief

# Omnibeta's dedicated slots, named as the fixture they are. Production
# resolves this from the league (draftkit/shape.py); a test may pin it.
OMNIBETA_SLOTS ={"QB": 1, "RB": 2, "WR": 2, "TE": 1, "K": 1, "DEF": 1}


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
    changes, total = lineup_changes(ROSTER, current, OMNIBETA_SLOTS, flex=2)
    assert changes == []
    # bench the better RB C for WR C in flex -> one suggested swap
    worse = ["q1", "r1", "r2", "w1", "w2", "t1", "w3", "w3", "k1", "d1"]
    changes2, total2 = lineup_changes(ROSTER, worse, OMNIBETA_SLOTS, flex=2)
    assert any("RB C" in c for c in changes2)


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


def test_one_flex_league_starts_one_fewer_than_two_flex():
    """Keefamania is nine starters, Omnibeta is ten. The same roster and the
    same code must produce different lineups, or the shape is being ignored."""
    from draftkit.lineup import optimal_lineup
    one = optimal_lineup(ROSTER, OMNIBETA_SLOTS, flex=1)
    two = optimal_lineup(ROSTER, OMNIBETA_SLOTS, flex=2)
    assert len(one) == 9 and len(two) == 10
    assert {p["sleeper_id"] for p in one} < {p["sleeper_id"] for p in two}
    # the tenth body is the best flex-eligible player left over, not a repeat
    extra = ({p["sleeper_id"] for p in two} - {p["sleeper_id"] for p in one}).pop()
    assert extra == "w3"


def test_one_flex_league_starts_one_fewer_than_two_flex():
    """Keefamania is nine starters, Omnibeta is ten. The same roster and the
    same code must produce different lineups, or the shape is being ignored."""
    from draftkit.lineup import optimal_lineup
    one = optimal_lineup(ROSTER, OMNIBETA_SLOTS, flex=1)
    two = optimal_lineup(ROSTER, OMNIBETA_SLOTS, flex=2)
    assert len(one) == 9 and len(two) == 10
    assert {p["sleeper_id"] for p in one} < {p["sleeper_id"] for p in two}
    # the tenth body is the best flex-eligible player left over, not a repeat
    extra = ({p["sleeper_id"] for p in two} - {p["sleeper_id"] for p in one}).pop()
    assert extra == "w3"
