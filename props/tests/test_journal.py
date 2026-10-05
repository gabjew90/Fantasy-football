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
           fails="HOU trails and throws 45 times", angle="return")


@pytest.fixture
def root(tmp_path, monkeypatch):
    import persist
    monkeypatch.setattr(J, "JOURNAL_ROOT", tmp_path / "journal")
    monkeypatch.setattr(persist, "RECORD_ROOT", tmp_path / "record")     # no real line archive
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
                     change="a", implies="b", fails=" ", angle="role")
    with pytest.raises(ValueError, match="American odds"):
        J.make_entry("X", "catches", "over", 3.5, 1.9, season=2026, week=4, **WHY)
    with pytest.raises(ValueError, match="unknown market"):
        J.make_entry("X", "tackles", "over", 3.5, -110, season=2026, week=4, **WHY)
    td = J.make_entry("X", "td", "yes", None, 150, season=2026, week=4, **WHY)
    assert td["line"] is None and td["market"] == "player_anytime_td"


def test_add_writes_one_line_and_refuses_a_bet_without_its_reasons(root, capsys):
    rc = J.main(["add", "Dalton Schultz", "catches", "under", "4.5", "-141", "--team", "HOU", "--season", "2026",
                 "--week", "4", "--angle", "return", "--change", WHY["change"], "--implies", WHY["implies"], "--fails", WHY["fails"]])
    assert rc == 0 and len(J.read(2026)) == 1
    raw = (root / "2026.jsonl").read_bytes()
    assert b"\r\n" not in raw and json.loads(raw.decode().strip())["player"] == "Dalton Schultz"
    with pytest.raises(SystemExit):
        J.main(["add", "X", "catches", "over", "3.5", "-110", "--season", "2026", "--week", "4",
                "--angle", "role", "--change", "a", "--implies", "b"])   # argparse: --fails missing
    with pytest.raises(SystemExit):
        J.main(["add", "X", "catches", "over", "3.5", "-110", "--season", "2026", "--week", "4",
                "--change", "a", "--implies", "b", "--fails", "c"])   # argparse: --angle missing
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
    assert c == {"graded": 2, "void": 1, "check": 1, "unjoined": 1, "unplayed": 1, "open_left": 2,
                 "late_lines": 0}
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


def test_late_line_value_against_the_last_quote_before_kickoff():
    bet = J.make_entry("Dalton Schultz", "catches", "under", 4.5, -141, team="HOU", season=2026, week=4, **WHY)
    q = lambda point, price, at, side="Under": {"bookmaker": "sleeper", "market": "player_receptions",
                                               "outcome": side, "player": "Dalton Schultz", "point": point,
                                               "price_american": price, "retrieved_at_utc": at, "season": 2026,
                                               "week": 4, "commence_time": "2026-10-04T17:00:00+00:00"}
    archive = [q(4.5, -141, "2026-10-03T20:00:00Z"), q(4.0, -125, "2026-10-04T14:00:00Z"),
               q(3.5, -120, "2026-10-04T18:00:00Z"),          # after kickoff: ignored
               q(4.0, -110, "2026-10-04T15:00:00Z", side="Over")]  # the other side: ignored
    ll = J.late_line(bet, archive)
    assert ll["late_line"] == 4.0 and ll["late_price"] == -125 and ll["clv_points"] == 0.5, \
        "an Under bought at 4.5 that closed 4.0 beat the late line by half a catch"
    same = J.late_line(bet, [q(4.5, -160, "2026-10-04T14:00:00Z")])
    assert same["clv_points"] == 0 and same["clv_price"] > 0, "same line, the late price costs more: value"
    assert J.late_line(bet, []) is None


def test_the_summary_leads_with_late_line_value(root):
    a = J.make_entry("A", "catches", "under", 4.5, -125, season=2026, week=4, **WHY)
    a.update(late_line=4.0, late_price=-125, clv_points=0.5)
    b = J.make_entry("B", "catches", "over", 2.5, -125, season=2026, week=4, **WHY)
    b.update(late_line=2.5, late_price=-125, clv_points=0.0)
    J.write(2026, [a, b])
    md = "\n".join(J.summary_md(2026))
    assert "**Late-line value, the first number to watch:** 1 of 2 bets got a better number" in md
    assert "1 tied" in md and "| 4 -125 (+0.5) |" in md


def test_a_td_bet_finds_its_late_yes_quote():
    bet = J.make_entry("X", "td", "yes", None, 150, season=2026, week=4, **WHY)
    q = {"bookmaker": "sleeper", "market": "player_anytime_td", "outcome": "Yes", "player": "X", "point": None,
         "price_american": 130, "retrieved_at_utc": "2026-10-04T14:00:00Z", "season": 2026, "week": 4,
         "commence_time": "2026-10-04T17:00:00+00:00"}
    ll = J.late_line(bet, [q])
    assert ll["late_price"] == 130 and ll["clv_price"] > 0, "bought at +150, late +130: the price moved your way"


def test_the_angle_is_required_at_log_time_and_splits_the_summary(root):
    with pytest.raises(ValueError, match="--angle is required"):
        J.make_entry("X", "catches", "over", 3.5, -110, season=2026, week=4,
                     **{**WHY, "angle": "hunch"})
    a = J.make_entry("A", "catches", "under", 4.5, -125, season=2026, week=4, **{**WHY, "angle": "injury"})
    a.update(status="graded", won=True, pnl_per_100=80.0, clv_points=0.5)
    b = J.make_entry("B", "catches", "over", 2.5, -125, season=2026, week=4, **{**WHY, "angle": "injury"})
    b.update(status="graded", won=False, pnl_per_100=-100.0, clv_points=0.0)
    c = J.make_entry("C", "rec_yds", "over", 40.5, -110, season=2026, week=5, **{**WHY, "angle": "role"})
    old = J.make_entry("D", "catches", "over", 1.5, -150, season=2026, week=3, **WHY)
    old.pop("angle")                                    # a row logged before angles existed
    J.write(2026, [a, b, c, old])
    md = "\n".join(J.summary_md(2026))
    assert "| injury redistribution | 2 | 2 | 1 | 50% | 56% | -10.0 | 1 of 2 |" in md
    assert "| role change | 1 | 0 | 0 | — | — | — | — |" in md
    assert "| untagged | 1 |" in md and "| teammate returning |" not in md
    assert "| 4 | A | under 4.5 catches | injury redistribution | -125 |" in md


def test_a_scenario_bet_keeps_its_assumption_and_both_chances(root):
    e = J.make_entry("Woody Marks", "rush_yds", "under", 33.5, -125, team="HOU", season=2026, week=4,
                     assumption=["Woody Marks: carries=9"], over_board="37%", over_scenario=0.30,
                     pays_if="Over above 11.2 carries; Under at 9.2 or fewer", **WHY)
    assert e["assumption"] == "Woody Marks: carries=9" and e["pays_if"].startswith("Over above 11.2")
    assert e["p_board"] == pytest.approx(0.63) and e["p_scenario"] == pytest.approx(0.70), \
        "an Under's chance is one minus the Over the table shows"
    plain = J.make_entry("X", "catches", "over", 3.5, -110, season=2026, week=4, **WHY)
    assert "assumption" not in plain and "p_scenario" not in plain, "a bet with no scenario carries no fields"
    for loose in ({"over_scenario": "60%"}, {"over_board": "40%"}, {"pays_if": "Over above 5 targets"}):
        with pytest.raises(ValueError, match="add the --assumption"):
            J.make_entry("X", "catches", "over", 3.5, -110, season=2026, week=4, **loose, **WHY)
    with pytest.raises(ValueError, match="not an --assume rule"):
        J.make_entry("X", "catches", "over", 3.5, -110, season=2026, week=4,
                     assumption=["Woody Marks carries 14"], **WHY)
    both = J.make_entry("X", "catches", "over", 3.5, -110, season=2026, week=4,
                        assumption=["HOU: pass=-3", "X: targets=8"], **WHY)
    assert both["assumption"] == "HOU: pass=-3; X: targets=8"
    with pytest.raises(ValueError, match="not adjusted by a scenario"):
        J.make_entry("X", "td", "yes", None, 150, season=2026, week=4, assumption=["X: targets=8"], **WHY)
    with pytest.raises(ValueError, match="not a chance"):
        J.make_entry("X", "catches", "over", 3.5, -110, season=2026, week=4, assumption=["X: targets=8"],
                     over_scenario="lots", **WHY)
    e.update(status="graded", won=True, pnl_per_100=80.0, clv_points=0.5)
    J.write(2026, [e, plain])
    md = "\n".join(J.summary_md(2026))
    assert "| 1 | 1 | 63% | 70% | 100% (1 of 1) | 1 of 1 |" in md
    assert "| Woody Marks: carries=9 (70% vs board 63%) |" in md
    plain_row = next(ln for ln in md.splitlines() if ln.startswith("| 4 | X |"))
    assert plain_row.endswith(f"| {WHY['change']} | — |"), plain_row


def test_the_cli_takes_the_scenario_fields(root):
    rc = J.main(["add", "Woody Marks", "rush_yds", "over", "33.5", "-130", "--team", "HOU", "--season", "2026",
                 "--week", "4", "--angle", "return", "--change", "a", "--implies", "b", "--fails", "c",
                 "--assumption", "Woody Marks: carries=14", "--over-board", "37%", "--over-scenario", "70%",
                 "--pays-if", "Over above 11.2 carries; Under at 9.2 or fewer"])
    r = J.read(2026)[0]
    assert rc == 0 and r["p_scenario"] == pytest.approx(0.70) and r["p_board"] == pytest.approx(0.37)


def test_a_power_play_is_one_all_or_nothing_entry_with_graded_legs(root):
    assert J.leg_price(5, 100, 5) == -122, "20x over five legs is 1.82x a leg"
    with pytest.raises(ValueError, match="positive stake"):
        J.leg_price(5, 4, 2)
    legs = [("Dalton Schultz", "rec_yds", "under", 40.5, "HOU", "return"),
            ("Tyler Allgeier", "rush_yds", "under", 21.5, "ARI")]
    rows = J.make_power_play(legs, stake=5, payout=15, angle="role", why="role reads", season=2026, week=4,
                             after_kickoff=True)
    assert len({r["entry_id"] for r in rows}) == 1 and [r["angle"] for r in rows] == ["return", "role"]
    assert all(r["price"] == J.leg_price(5, 15, 2) and r["after_kickoff"] for r in rows)
    with pytest.raises(ValueError, match="at least two legs"):
        J.make_power_play(legs[:1], stake=5, payout=10, angle="role", why="x", season=2026, week=4)
    rows[0].update(status="graded", won=True)
    rows[1].update(status="graded", won=False)
    J.write(2026, rows)
    md = "\n".join(J.summary_md(2026))
    assert "| week 4 (after kickoff) | Dalton Schultz under, Tyler Allgeier under | $5 | $15 | 1 / 2 | lost | -5.00 |" in md
    rows[1].update(won=True)
    J.write(2026, rows)
    assert "| 2 / 2 | won | +10.00 |" in "\n".join(J.summary_md(2026))
    assert all(r["stake"] == 1.0 for r in rows), "a leg is one unit in the record; the dollars are the entry's"
    rows[1].update(status="void", won=None)
    J.write(2026, rows)
    assert "| check: a leg was dropped" in "\n".join(J.summary_md(2026))
    rows[0].update(won=False)
    J.write(2026, rows)
    assert "| lost | -5.00 |" in "\n".join(J.summary_md(2026)), "a lost leg loses the entry, void or not"


def test_the_cli_logs_an_entry(root):
    rc = J.main(["entry", "--stake", "5", "--payout", "100", "--angle", "role", "--why", "Houston redistributes",
                 "--season", "2026", "--week", "4", "--leg", "Dalton Schultz|rec_yds|under|40.5|HOU|return",
                 "--leg", "CeeDee Lamb|td|yes||DAL", "--leg", "Drake London|td|yes|"])
    rows = J.read(2026)
    assert rc == 0 and len(rows) == 3 and rows[1]["line"] is None and rows[1]["market"] == "player_anytime_td"
    assert rows[2]["team"] is None, "the team is optional on a leg"
    assert J.main(["entry", "--stake", "5", "--payout", "100", "--angle", "role", "--why", "x", "--season", "2026",
                   "--week", "4", "--leg", "bad leg"]) == 2


def test_a_rebooted_leg_and_the_real_payout(root):
    legs = [("A", "catches", "over", 3.5, "KC"), ("B", "catches", "over", 2.5, "KC"), ("C", "catches", "over", 4.5, "LV")]
    rows = J.make_power_play(legs, stake=5, payout=47.5, angle="role", why="x", season=2026, week=4)
    J.write(2026, rows)
    assert J.main(["entry-void", rows[0]["entry_id"], "--player", "a", "--season", "2026"]) == 0   # 'Reboot'
    assert J.read(2026)[0]["status"] == "void" and "Reboot" in J.read(2026)[0]["result"]
    assert J.main(["entry-void", rows[0]["entry_id"], "--player", "Nobody", "--season", "2026"]) == 2
    md = "\n".join(J.summary_md(2026))
    assert "check: a leg was dropped" in md and "journal entry-paid" in md
    assert J.main(["entry-paid", rows[0]["entry_id"], "--paid", "15", "--season", "2026"]) == 0
    assert "| won (as paid) | +10.00 |" in "\n".join(J.summary_md(2026)), "settled at what Sleeper paid"
    assert J.main(["entry-paid", "nope", "--paid", "1", "--season", "2026"]) == 2


def test_entry_paid_labels_a_refund_honestly(root):
    rows = J.make_power_play([("A", "catches", "over", 3.5, "KC"), ("B", "catches", "over", 2.5, "KC")],
                             stake=5, payout=15, angle="role", why="x", season=2026, week=4)
    J.write(2026, rows)
    J.entry_paid(2026, rows[0]["entry_id"], 5)
    assert "| refunded (as paid) | +0.00 |" in "\n".join(J.summary_md(2026))
    J.entry_paid(2026, rows[0]["entry_id"], 0)
    assert "| lost (as paid) | -5.00 |" in "\n".join(J.summary_md(2026))
    with pytest.raises(ValueError, match="0 or more"):
        J.entry_paid(2026, rows[0]["entry_id"], -1)
