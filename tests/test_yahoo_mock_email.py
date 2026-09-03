"""Yahoo's results email is the only official record of a mock room; the
parser must place every pick on the snake correctly and find our seat."""

from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("yme", ROOT / "scripts" / "yahoo_mock_email.py")
yme = importlib.util.module_from_spec(spec)
spec.loader.exec_module(yme)

EMAIL = """Date: 2026-08-31T22:51:10Z
Message-Id: abc123

*Round by Round results*
------------------------------
*Round 1*
(1) Gabriel - Gibbs, Jahmyr (Det - RB)
(2) SemperFi91 - Robinson, Bijan (Atl - RB)
(3) Carlos - Cook III, James (Buf - RB)

*Round 2*
(1) Carlos - Lamb, CeeDee (Dal - WR)
(2) SemperFi91 - Jacksonville (Jax - DEF)
(3) Gabriel - St. Brown, Amon-Ra (Det - WR)
"""


def test_parse_places_picks_on_the_snake_and_finds_our_seat():
    t = yme.parse_email(EMAIL)
    assert t["teams"] == 3 and t["my_team"] == "1" and t["room"] == "emailabc123"
    by_no = {p["pick_no"]: p for p in t["picks"]}
    assert by_no[1]["name"] == "Jahmyr Gibbs" and by_no[1]["team_id"] == "1"
    assert by_no[3]["name"] == "James Cook III" and by_no[3]["team"] == "BUF"
    # round 2 runs backwards: (1) Carlos is slot 3, pick 4; (3) Gabriel is slot 1, pick 6
    assert by_no[4]["team_id"] == "3" and by_no[4]["name"] == "CeeDee Lamb"
    assert by_no[5]["name"] == "Jacksonville" and by_no[5]["pos"] == "DEF"
    assert by_no[6]["team_id"] == "1" and by_no[6]["name"] == "Amon-Ra St. Brown"
    assert t["managers"]["2"]["nickname"] == "SemperFi91" and t["source"] == "yahoo_email"


def test_display_name_handles_suffixes_and_defenses():
    assert yme.display_name("Cook III, James", "RB") == "James Cook III"
    assert yme.display_name("Etienne Jr., Travis", "RB") == "Travis Etienne Jr."
    assert yme.display_name("New England", "DEF") == "New England"


def test_my_team_label_variants():
    t = yme.parse_email(EMAIL.replace("Gabriel", "My Team"))
    assert t["my_team"] == "1"
