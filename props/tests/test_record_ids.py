"""DECISIONS #224: a book line joins to the engine's player by ID, and the IDs reach the record.

Sleeper names each line's player by its own id and carries his nflverse gsis id; the engine
matched by name alone, and so did settle. These pin the match rule and that every link of the
capture path keeps the ids."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ENGINE = Path(__file__).resolve().parents[1] / "engine" / "scripts"
sys.path.insert(0, str(ENGINE))
sys.path.insert(0, str(ENGINE.parents[1]))

pytest.importorskip("pandas")


@pytest.fixture
def sg():
    import score_game as SG
    return SG


def _tables(sg, names):
    """name_by_gsis, name_by_norm, loose_by_key as score_game builds them."""
    by_gsis = {g: n for n, g in names.items() if sg.clean_gsis(g)}
    by_norm = {sg.norm_name(n): n for n in names}
    loose = {}
    for n in names:
        loose.setdefault(sg.name_key_loose(n), n)
    return by_gsis, by_norm, loose


def test_clean_gsis_keeps_a_real_id_and_drops_anything_else(sg):
    assert sg.clean_gsis(" 00-0039361 ") == "00-0039361"
    assert sg.clean_gsis(None) is None and sg.clean_gsis("") is None and sg.clean_gsis("4984") is None


def test_the_line_joins_by_id_when_it_has_one(sg):
    t = _tables(sg, {"Bucky Irving": "00-0039361", "Kenny Gainwell": "00-0036919"})
    # Sleeper spells him "Kenneth"; the id finds him whatever the spelling
    assert sg.match_line_player("Kenneth Gainwell", "00-0036919", *t) == ("Kenny Gainwell", "gsis")
    assert sg.match_line_player("Bucky Irving", "00-0039361", *t) == ("Bucky Irving", "gsis")


def test_no_id_or_an_id_not_ours_falls_back_to_the_name(sg):
    t = _tables(sg, {"Bucky Irving": "00-0039361"})
    assert sg.match_line_player("Bucky Irving", None, *t) == ("Bucky Irving", "name")
    assert sg.match_line_player("Bucky Irving", "00-0011111", *t) == ("Bucky Irving", "name")
    assert sg.match_line_player("Nobody Here", None, *t) == (None, None)


def test_an_id_and_a_name_that_point_at_two_players_trust_neither(sg):
    t = _tables(sg, {"Bucky Irving": "00-0039361", "Sean Tucker": "00-0039999"})
    assert sg.match_line_player("Bucky Irving", "00-0039999", *t) == (None, "id/name conflict")


def test_the_weekly_roster_maps_sleeper_ids_to_gsis_and_drops_a_contested_one(sg):
    import pandas as pd
    ros = pd.DataFrame({"sleeper_id": [12504.0, 12504.0, 9484.0, None, 777.0, 777.0],
                        "gsis_id": ["00-0040142", "00-0040142", "00-0038996", "00-0011111", "00-0000001",
                                    "00-0000002"]})
    assert sg.sleeper_gsis_map(ros) == {"12504": "00-0040142", "9484": "00-0038996"}
    assert sg.sleeper_gsis_map(pd.DataFrame({"gsis_id": ["00-0040142"]})) == {}


def test_every_link_of_the_capture_path_keeps_the_ids():
    src = (ENGINE / "score_game.py").read_text(encoding="utf-8")
    assert '"gsis_id": SLEEPER_TO_GSIS.get(str(m_["subject_id"])) or clean_gsis(pinfo.get("gsis_id"))' in src
    assert '"sleeper_id": o.get("sleeper_id"), "gsis_id": o.get("gsis_id")' in src, "the line archive"
    assert src.count("gsis_id=gsis_by_name.get(nm)") == 2, "yards/count rows and anytime-TD rows"
    import record_run
    import settle
    assert {"gsis_id", "sleeper_id", "join_how"} <= set(record_run.PRED_FIELDS)
    assert {"gsis_id", "sleeper_id"} <= set(settle.SETTLED_FIELDS)
