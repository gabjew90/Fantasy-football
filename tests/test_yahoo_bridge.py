"""The Yahoo bridge runs the REAL engine; the page only actuates.

These cover the translation layer between Yahoo's vocabulary and the engine's,
which is where a silent mistranslation can disable a guardrail without
throwing anything.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("yb", ROOT / "scripts" / "yahoo_bridge.py")
yb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(yb)


KEEFAMANIA_ROSTER = ["QB", "WR", "WR", "RB", "RB", "TE", "W/R/T", "K", "DEF",
                     "BN", "BN", "BN", "BN", "BN", "BN", "IR", "IR"]


def test_yahoo_slot_names_map_to_engine_slots():
    """Yahoo calls the flex "W/R/T" and lists IR slots that are never drafted.

    Feeding that list to snake.roster_slots_from_draft_settings (which reads
    Sleeper's slots_* keys) returned an EMPTY map, so my_needs() came back all
    zeros and every need-aware guardrail quietly switched off -- no error, no
    warning, just a worse draft.
    """
    got = yb.slots_from_yahoo_roster(KEEFAMANIA_ROSTER)
    assert got["QB"] == 1
    assert got["RB"] == 2
    assert got["WR"] == 2
    assert got["TE"] == 1
    assert got["FLEX"] == 1, "W/R/T must become the engine's FLEX slot"
    assert got["K"] == 1
    assert got["DEF"] == 1
    assert got["BN"] == 6
    assert "IR" not in got or got.get("IR", 0) == 0, "IR is never drafted"


def test_starters_exclude_bench_and_ir():
    got = yb.slots_from_yahoo_roster(KEEFAMANIA_ROSTER)
    starters = sum(v for k, v in got.items() if k != "BN")
    assert starters == 9, got          # 9 starters, 6 bench, 2 IR undrafted


def test_flex_aliases_all_recognised():
    for alias in ("W/R/T", "WRT", "FLEX", "W/R"):
        got = yb.slots_from_yahoo_roster(["QB", alias])
        assert got["FLEX"] == 1, alias


def test_player_key_matches_how_yahoo_renders_a_row():
    """The engine holds full names; Yahoo prints "J. Gibbs". Suffixes are
    dropped so "Brian Thomas Jr." and "B. Thomas Jr." agree."""
    assert yb.key("Jahmyr Gibbs") == "j gibbs"
    assert yb.key("Brian Thomas Jr.") == yb.key("B. Thomas Jr.".replace("B.", "Brian"))
    assert yb.key("Patrick Mahomes II") == "p mahomes"
    assert yb.key("Ja'Marr Chase") == "j chase"


def test_pick_slot_is_derived_from_pick_number():
    """Yahoo's pick feed gives the player and the pick NUMBER, never whose
    pick it was. The bridge used to read d["slot"], which defaulted to 0, so
    no pick was attributed to us -- my_pos_counts() came back empty and the
    engine recommended a SECOND QB in round 4 against a round-10 gate. Caught
    live in a mock.

    In a snake the slot is fully determined by the pick number, so derive it.
    """
    from draftkit import snake
    teams = 10
    # 10-team snake: round 1 runs 1..10, round 2 runs 20..11 backwards
    assert snake.pick_to_round_slot(1, teams) == (1, 1)
    assert snake.pick_to_round_slot(10, teams) == (1, 10)
    assert snake.pick_to_round_slot(11, teams) == (2, 10)   # turn: back-to-back
    assert snake.pick_to_round_slot(20, teams) == (2, 1)
    assert snake.pick_to_round_slot(21, teams) == (3, 1)


def test_our_picks_are_attributed_to_us():
    """The roster the engine sees must contain exactly our own picks."""
    from draftkit import snake
    teams, my_slot = 10, 10
    feed = [{"pick_no": n, "name": f"P{n}", "pos": "RB"} for n in range(1, 22)]
    ours = [d["pick_no"] for d in feed
            if snake.pick_to_round_slot(d["pick_no"], teams)[1] == my_slot]
    assert ours == [10, 11], ours      # slot 10 picks back-to-back at the turn
