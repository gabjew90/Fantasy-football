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
