"""guardrails.position_max: the host's per-position roster cap (rooms
10797402 and 10798461, 2026-09-05: Yahoo refused a seventh back and the
driver lost the clock finding out)."""

from draftkit.tracker import Tracker


def _t(position_max):
    t = object.__new__(Tracker)
    t.qb2_round, t.te2_fall = 10, 12
    t.position_max = position_max
    return t


def test_a_full_position_is_refused_and_an_open_one_is_not():
    t = _t({"RB": 6, "WR": 6})
    assert not t._pos_allowed("RB", 13, {"RB": 6}, 3, False)
    assert t._pos_allowed("RB", 13, {"RB": 5}, 3, False)
    assert t._pos_allowed("WR", 13, {"RB": 6, "WR": 5}, 3, False)
    assert not t._pos_allowed("WR", 13, {"WR": 6}, 3, False)


def test_no_cap_configured_changes_nothing():
    t = _t({})
    assert t._pos_allowed("RB", 13, {"RB": 9}, 3, False)
    u = object.__new__(Tracker)          # a tracker built without the attribute at all
    u.qb2_round, u.te2_fall = 10, 12
    assert u._pos_allowed("RB", 13, {"RB": 9}, 3, False)


def test_the_league_file_carries_the_measured_back_cap():
    from draftkit.config import Config
    g = Config.load(league="keefamania").get("guardrails") or {}
    assert int((g.get("position_max") or {}).get("RB", 0)) == 6


def test_the_room_caps_write_over_the_yaml_caps():
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
    from yahoo_bridge import merge_position_caps
    assert merge_position_caps({"RB": 6, "WR": 6}, {"RB": "6", "WR": "8", "TE": "4", "OFF": "4"}) == {"RB": 6, "WR": 8, "TE": 4, "OFF": 4}
    assert merge_position_caps({"RB": 6}, None) == {"RB": 6}
    assert merge_position_caps(None, {"RB": "x", "WR": "8"}) == {"WR": 8}


def test_earliest_round_keeps_a_position_out_until_its_round():
    """guardrails.earliest_round (DECISIONS #67): QB from round 4, TE from
    round 3; nothing else changes."""
    t = _t({})
    t.position_earliest_round = {"QB": 4, "TE": 3}
    assert not t._pos_allowed("QB", 3, {}, 12, False)
    assert t._pos_allowed("QB", 4, {}, 11, False)
    assert not t._pos_allowed("TE", 2, {}, 13, False)
    assert t._pos_allowed("TE", 3, {}, 12, False)
    assert t._pos_allowed("RB", 1, {}, 14, False)
