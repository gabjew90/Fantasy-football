"""The bet journal (props/journal.py, DECISIONS #142): logged with the four
checklist answers, graded by the Tuesday settle run with settle's own rules,
summarised on the scorecard apart from the model's record."""

from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

import pandas as pd
import pytest

PROPS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROPS))

import journal as J  # noqa: E402
import settle  # noqa: E402

NOW = dt.datetime(2026, 10, 3, 21, 0, tzinfo=dt.timezone.utc)
WHY = dict(change="targets fell to 12% with Collins back", implies="4.5 needs ~6.3 targets",
           fails="HOU trails and throws 45 times")


@pytest.fixture
def root(tmp_path, monkeypatch):
    monkeypatch.setattr(J, "JOURNAL_ROOT", tmp_path / "journal")
    return tmp_path / "journal"


def _stats(rows):
    df = pd.DataFrame(rows)
    df["_name"] = df.player_display_name.map(settle.norm_name)
    df["_loose"] = df.player_display_name.map(settle.loose_key)
    for c in ("receptions", "receiving_yards", "rushing_yards", "passing_yards", "_anytime_td"):
        if c not in df:
            df[c] = 0
    return df


def test_an_entry_needs_all_three_checklist_answers():
    e = J.make_entry("Dalton Schultz", "catches", "under", 4.5, -141, team="hou", season=2026, week=4, now=NOW, **WHY)
    assert e["market"] == "player_receptions" and e["team"] == "HOU" and e["status"] == "open"
    with pytest.raises(ValueError, match="--fails is required"):
        J.make_entry("X", "catches", "over", 3.5, -110, season=2026, week=4,
                     change="a", implies="b", fails=" ")
    with pytest.raises(ValueError, match="American odds"):
        J.make_entry("X", "catches", "over", 3.5, 1.9, season=2026, week=4, **WHY)
    with pytest.raises(ValueError, match="unknown market"):
        J.make_entry("X", "tackles", "over", 3.5, -110, season=2026, week=4, **WHY)
    td = J.make_entry("X", "td", "yes", None, 150, season=2026, week=4, **WHY)
    assert td["line"] is None and td["market"] == "player_anytime_td"


def test_add_writes_one_line_and_refuses_a_bet_without_its_reasons(root, capsys):
    rc = J.main(["add", "Dalton Schultz", "catches", "under", "4.5", "-141", "--team", "HOU", "--season", "2026",
                 "--week", "4", "--change", WHY["change"], "--implies", WHY["implies"], "--fails", WHY["fails"]])
    assert rc == 0 and len(J.read(2026)) == 1
    raw = (root / "2026.jsonl").read_bytes()
    assert b"\r\n" not in raw and json.loads(raw.decode().strip())["player"] == "Dalton Schultz"
    with pytest.raises(SystemExit):
        J.main(["add", "X", "catches", "over", "3.5", "-110", "--season", "2026", "--week", "4",
                "--change", "a", "--implies", "b"])   # argparse: --fails missing
    assert len(J.read(2026)) == 1


def test_grading_uses_settles_rules_and_leaves_unknown_names_open(root):
    rows = [J.make_entry("Dalton Schultz", "catches", "under", 4.5, -141, team="HOU", season=2026, week=4, **WHY),
            J.make_entry("Nico Collins", "rec_yds", "over", 73.5, -127, team="HOU", season=2026, week=4, **WHY),
            J.make_entry("Woody Marks", "catches", "over", 1.0, -150, team="HOU", season=2026, week=4, **WHY),
            J.make_entry("Ghost Player", "catches", "over", 2.5, -110, team="HOU", season=2026, week=4, **WHY),
            J.make_entry("Xavier Hutchinson", "catches", "over", 2.5, -135, team="HOU", season=2026, week=4, **WHY),
            J.make_entry("Jake Ferguson", "catches", "over", 3.5, -120, team="DAL", season=2026, week=5, **WHY)]
    J.write(2026, rows)
    stats = _stats([
        dict(week=4, team="HOU", player_display_name="Dalton Schultz", player_name="D.Schultz", receptions=3),
        dict(week=4, team="HOU", player_display_name="Nico Collins", player_name="N.Collins", receiving_yards=91),
        dict(week=4, team="HOU", player_display_name="Woody Marks", player_name="W.Marks", receptions=1),
        dict(week=3, team="HOU", player_display_name="Xavier Hutchinson", player_name="X.Hutchinson", receptions=4)])
    c = J.grade(2026, stats=stats, now=NOW)
    by = {r["player"]: r for r in J.read(2026)}
    assert by["Dalton Schultz"]["won"] is True and by["Dalton Schultz"]["pnl_per_100"] == pytest.approx(70.92, abs=0.01)
    assert by["Nico Collins"]["won"] is True and by["Nico Collins"]["actual"] == 91
    assert by["Woody Marks"]["status"] == "void" and by["Woody Marks"]["result"] == "push"
    assert by["Xavier Hutchinson"]["status"] == "check", \
        "absent from the week: did not play OR played for zero -- never guessed"
    assert by["Ghost Player"]["status"] == "open", "an unresolved name stays open, never graded as a loss"
    assert by["Jake Ferguson"]["status"] == "open", "week 5 has no stats yet"
    assert c == {"graded": 2, "void": 1, "check": 1, "unjoined": 1, "unplayed": 1, "open_left": 2}
    # resolve by hand from the box score: he played and caught nothing -> the Over loses
    r = J.resolve(2026, by["Xavier Hutchinson"]["id"], actual=0, now=NOW)
    assert r["status"] == "graded" and r["won"] is False and r["pnl_per_100"] == -100.0
    with pytest.raises(ValueError, match="exactly one"):
        J.resolve(2026, by["Jake Ferguson"]["id"])


def test_nothing_open_means_no_download_and_no_file(root):
    assert J.grade(2026, stats=None) == {"graded": 0, "void": 0, "check": 0, "unjoined": 0, "unplayed": 0,
                                         "open_left": 0}
    assert not (root / "2026.jsonl").exists()


def test_the_scorecard_section_reports_the_record_against_break_even(root):
    assert "No bets logged yet" in "\n".join(J.summary_md(2026))
    won = J.make_entry("A", "catches", "under", 4.5, -125, season=2026, week=4, **WHY)
    won.update(status="graded", won=True, pnl_per_100=80.0)
    lost = J.make_entry("B", "rec_yds", "over", 40.5, -125, season=2026, week=4, **WHY)
    lost.update(status="graded", won=False, pnl_per_100=-100.0)
    J.write(2026, [won, lost, J.make_entry("C", "catches", "over", 2.5, -110, season=2026, week=5, **WHY)])
    md = "\n".join(J.summary_md(2026))
    assert "3 bets logged: 2 graded, 0 void (push or did not play), 1 open" in md
    assert "| 2 | 1 | 50% | 56% | -10.0 |" in md, "break-even at -125 is 55.6%"
    assert J.breakeven(-125) == pytest.approx(0.5556, abs=1e-4) and J.breakeven(150) == pytest.approx(0.4)


def test_a_yardage_bet_without_a_line_is_refused_plainly():
    with pytest.raises(ValueError, match="needs its line"):
        J.make_entry("X", "catches", "over", None, -110, season=2026, week=4, **WHY)


def test_the_journal_lives_beside_the_record_so_tests_never_read_the_real_one(tmp_path, monkeypatch):
    import persist
    monkeypatch.setattr(J, "JOURNAL_ROOT", None)
    monkeypatch.delenv("PROPS_JOURNAL_ROOT", raising=False)
    monkeypatch.setattr(persist, "RECORD_ROOT", tmp_path / "record")
    assert J.journal_path(2026) == tmp_path / "journal" / "2026.jsonl"
