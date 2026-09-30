"""Sleeper trending adds/drops as the waiver timing signal (DECISIONS #130)."""

from __future__ import annotations

import json
import types

import pytest

from core import fetch as F
from fantasy import ask as A
from fantasy import trending as TR
from fantasy import waiver as WV

REAL_LOAD = TR.load                      # before conftest's autouse stub replaces it

ADDS = [{"player_id": "g", "count": 6351247}, {"player_id": "a", "count": 2765504}, {"player_id": "s", "count": 21159}]
DROPS = [{"player_id": "ach", "count": 1028766}, {"player_id": "x", "count": 812}]


def _fake_fetch(tmp_path, fail=()):
    def sleeper_trending(kind, *, cache_dir=None, manifest=None, max_age_s=None, limit=100, **kw):
        if kind in fail:
            raise OSError("blocked")
        p = tmp_path / f"trending_{kind}.json"
        p.write_text(json.dumps(ADDS if kind == "add" else DROPS), encoding="utf-8")
        return p
    return sleeper_trending


def test_load_ranks_both_lists_and_says_which_one_failed(monkeypatch, tmp_path):
    monkeypatch.setattr(F, "sleeper_trending", _fake_fetch(tmp_path))
    tr = REAL_LOAD()
    assert tr["add"]["g"] == 6351247 and tr["rank"]["add"] == {"g": 1, "a": 2, "s": 3}
    assert tr["drop"]["ach"] == 1028766 and tr["rank"]["drop"]["x"] == 2 and tr["note"] is None
    monkeypatch.setattr(F, "sleeper_trending", _fake_fetch(tmp_path, fail=("drop",)))
    tr = REAL_LOAD()
    assert tr["add"] and tr["drop"] == {} and "drops unavailable (OSError)" in tr["note"]


def test_counts_cells_and_lines_read_as_counts_not_probabilities(monkeypatch, tmp_path):
    monkeypatch.setattr(F, "sleeper_trending", _fake_fetch(tmp_path))
    tr = REAL_LOAD()
    assert (TR.fmt_count(6351247), TR.fmt_count(21159), TR.fmt_count(812)) == ("6.4M", "21k", "812")
    assert TR.cell("g", tr) == "6.4M (#1)" and TR.cell("zzz", tr) == "--" and TR.cell("ach", tr, "drop") == "1.0M (#1)"
    assert TR.line("g", tr) == ("Sleeper trending: added in 6.4M Sleeper leagues in the last 24 hours "
                                "(#1 of trending adds, likely gone after this waiver period).")
    assert "dropped in 1.0M" in TR.line("ach", tr) and "likely gone" not in TR.line("ach", tr)
    assert TR.line("zzz", tr) is None
    tr["rank"]["add"]["s"] = 40
    assert "likely gone" not in TR.line("s", tr), "rank 40 is not the top of the list"
    assert TR.likely_gone(["s", "a", "zzz", "g"], tr) == ["g", "a"]


def test_the_fetch_takes_only_add_or_drop():
    with pytest.raises(ValueError):
        F.sleeper_trending("trade", downloader=lambda u, d, t: None)


def _md(trend, **kw):
    view = types.SimpleNamespace(season=2026, week=4)
    gate = types.SimpleNamespace(line=lambda: "LEAGUE DATA GATE: PASS")
    m = types.SimpleNamespace(summary_line=lambda: "inputs")
    info = {"g": {"name": "Ollie Gordon", "team": "MIA", "pos": "RB"},
            "a": {"name": "Braelon Allen", "team": "NYJ", "pos": "RB"},
            "ach": {"name": "De'Von Achane", "team": "MIA", "pos": "RB"}}
    ranked = [{"add": "g", "drop": "ach", "gain": 0.7, "ros_upside": 1.0, "start_weeks": [5]},
              {"add": "a", "drop": "ach", "gain": 0.5, "ros_upside": 1.0, "start_weeks": [5]}]
    return WV.markdown("keefamania", view, "season", ("RB",), {"record": "1-2", "rank": 6, "teams": 10,
                       "contender": True}, gate, ranked, ["ach"], set(), {}, {}, info, {}, True, m, [],
                       scored={"candidates": 80, "improving": 2, "no_cut": [], "no_gain": []}, trend=trend, **kw)


def test_the_waiver_report_shows_the_count_and_who_is_likely_gone(monkeypatch, tmp_path):
    monkeypatch.setattr(F, "sleeper_trending", _fake_fetch(tmp_path))
    md = _md(REAL_LOAD())
    assert "| Adds 24h (Sleeper, all leagues) |" in md and "| 6.4M (#1) |" in md
    assert ("**Likely gone after this waiver period**" in md
            and "Ollie Gordon (MIA, RB) 6.4M adds (#1); Braelon Allen (NYJ, RB) 2.8M adds (#2)" in md)
    assert "this line is only whether you can wait" in md
    assert "| Drops 24h (Sleeper, all leagues) |" in md and "| 1.0M (#1) |" in md, "the bench shows drops"


def test_trending_unavailable_is_said_not_shown_as_nobody_trending():
    md = _md({"add": {}, "drop": {}, "rank": {"add": {}, "drop": {}}, "note": "Sleeper trending adds unavailable"})
    assert "**Trending unavailable this run**" in md and "Likely gone" not in md
    md = _md(None)
    assert "**Trending unavailable this run**" in md


def test_the_player_tool_prints_the_trending_line_and_an_old_snapshot_still_loads(monkeypatch):
    from tests.test_fantasy_ask import _snap
    monkeypatch.setattr(A.EV, "for_sleeper", lambda pids, info, season, manifest=None, team=False: {})
    tr = {"add": {"5": 940059}, "drop": {}, "rank": {"add": {"5": 4}, "drop": {}}, "note": None}
    s = _snap(trending=tr)
    text = A.players(s, ["Puka Nacua"]).text
    assert "Sleeper trending: added in 940k Sleeper leagues in the last 24 hours (#4 of trending adds, likely gone" in text
    assert "Garrett Wilson" not in text
    s2 = _snap(trending={"add": {}, "drop": {}, "rank": {"add": {}, "drop": {}}, "note": "Sleeper trending adds unavailable (OSError)"})
    assert "(Sleeper trending adds unavailable (OSError): whether an add is being claimed" in A.players(s2, ["Puka Nacua"]).text
    from fantasy.snapshot import Snapshot
    old = s.to_json()
    old.pop("trending")
    assert Snapshot.from_json(json.loads(json.dumps(old, default=str))).trending == {}, "a cache from before this field"
