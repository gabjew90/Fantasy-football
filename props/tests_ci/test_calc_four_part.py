"""The four-part leg read (DECISIONS #249): the line and the book's 50/50, this season with the special
games named and left out of a second average, every unit pairing with implied points, and the facts
sorted by whether they point to the line being set high or low. Known answers, synthetic data."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from props.calc import card, odds, player, settings  # noqa: E402
from test_calc_model import _games, _player, rush_model  # noqa: E402

GL = {"favorite": "DAL", "points": 9.5, "spread_text": "DAL -9.5", "spread_unread": False, "total": 49.5}
OPP = {"value": 4.43, "games": 4, "who": " to RBs"}
GA = [("DAL", "TB", "run", {"off": "B", "def": "C"}), ("DAL", "TB", "pass", {"off": "A-", "def": "B"}),
      ("TB", "DAL", "run", {"off": "D", "def": "B+"}), ("TB", "DAL", "pass", {"note": "Only 3 games. No grades yet."})]
SCORING = {"DAL": (27.25, 18.0, 4), "TB": (20.0, 24.5, 4)}


def _card(perf_scope="recent", qb_today=""):
    fixed = settings.load()["fixed"]
    season, window = _games()
    pl = _player(season, window)
    perf = window.tail(4).assign(opp=["NYG", "PHI", "WAS", "PHI"], snap_pct=[0.6, 0.12, 0.7, 0.65],
                                 fewer_snaps=[False, True, False, False], left_early=[False, True, False, False],
                                 hurt_next=[None, "Out", None, None])
    perf["reasons"] = [[], [], ["Lead Back out"], []]
    pl.perf, pl.perf_scope = perf, perf_scope
    c = card.compute(pl, rush_model(ypc=4.2), "rush_yds", 64.5, odds.multiplier_from_american(-125),
                     odds.multiplier_from_american(-132), fixed)
    kw = dict(opp="TB", game_lines=GL, opp_row=OPP, grades={"off": "B", "def": "C"}, grades_all=GA,
              scoring=SCORING, qb_today=qb_today)
    return pl, c, kw


def test_implied_points_from_the_total_and_the_spread():
    it = card.implied_totals
    assert it({"favorite": "MIN", "points": 6.5, "total": 41.5}, "MIN", "IND") == {"MIN": 24.0, "IND": 17.5}
    assert it({"favorite": "HOU", "points": 10.5, "total": 42.5}, "NYG", "HOU") == {"HOU": 26.5, "NYG": 16.0}
    assert it({"favorite": None, "spread_text": "EVEN", "total": 44.0}, "A", "B") == {"A": 22.0, "B": 22.0}
    assert it({"spread_unread": True, "total": 44.0}, "A", "B") is None
    assert it({"favorite": "KC", "points": 3, "total": 44.0}, "A", "B") is None, "a favorite that is neither team"
    assert it(None, "A", "B") is None and it({"favorite": "A", "points": 3}, "A", "B") is None


def test_part_one_prints_the_books_split_and_both_bars():
    pl, c, kw = _card()
    rows = dict(card.line_part(pl, c, "over"))
    # -125 -> 55.6%, -132 -> 56.9%; margin removed: 55.6 / (55.6 + 56.9) = 49.4%
    assert rows["The book's 50/50, margin removed"] == "Over 49% / Under 51% (the book's numbers)"
    assert rows["Line"] == "64.5 rushing yards: Over -125 / Under -132"
    assert rows["Workload at the book's split (our math)"] == f"~{card._round(card.value(c, 'book_expects'))} carries"
    assert rows["His carries in his last 4 games"] == "15.5 a game; 15.5 without weeks 2 and 3"
    assert rows["Over 64.5"] == "1 of his last 4 games; 0 of 2 without weeks 2 and 3"
    assert rows["Under needs at its price (-132)"].endswith("carries or fewer")
    under = dict(card.line_part(pl, c, "under"))
    assert under["Under 64.5"] == "3 of his last 4 games; 2 of 2 without weeks 2 and 3"
    assert "Over needs at its price (-125)" in under


def test_the_season_read_names_the_special_games_and_averages_without_them():
    pl, c, _ = _card()
    S = card.season_read(pl, c)
    assert [r["special"] for r in S["rows"]] == [False, True, True, False]
    assert S["rows"][1]["notes"] == ["left early (Out next game)"] and S["rows"][2]["notes"] == ["Lead Back out"]
    assert S["all"]["stat"] == pytest.approx((41 + 30 + 98 + 62) / 4)
    assert S["clean"]["stat"] == pytest.approx(51.5) and S["clean"]["rate"] == pytest.approx(103 / 31)
    assert (S["over"], S["under"], S["over_clean"], S["under_clean"]) == (1, 3, 0, 2)
    head, body = card.season_table(pl, c, S)
    assert head == ["Week", "Opp", "Carries", "Rush yds", "Yds/carry", "Snaps", "Note"]
    assert body[1] == ["2", "PHI", "12", "30", "2.5", "12%", "SPECIAL: left early (Out next game)"]
    lines_ = card.season_lines(c, S)
    assert lines_[1] == ("Average without weeks 2 and 3 (the special games): 15.5 carries, 51.5 rushing yards, "
                         "3.3 yards a carry (2 games).")
    assert lines_[-1] == "Only 4 games this season, so this is his last 4."


def test_a_low_snap_game_with_no_injury_listing_stays_in():
    pl, c, _ = _card()
    pl.perf = pl.perf.assign(left_early=[False] * 4, hurt_next=[None] * 4)
    S = card.season_read(pl, c)
    assert not S["rows"][1]["special"] and S["rows"][1]["notes"] == ["far fewer snaps, no injury listing"]


def test_a_quarterbacks_relief_games_are_special():
    pl, c, _ = _card()
    pl.position, pl.gsis_id = "QB", "q9"
    pl.perf = pl.perf.assign(qb_id=["q9", "q9", "q1", "q9"], left_early=[False] * 4, reasons=[[], [], [], []])
    S = card.season_read(pl, c)
    assert [r["special"] for r in S["rows"]] == [False, False, True, False]
    assert S["rows"][2]["notes"] == ["did not start"]


def _sched():
    return pd.DataFrame([dict(game_id=f"2026_0{w}", season=2026, week=w, home_team="DAL", away_team="X",
                              home_qb_id="q", away_qb_id="x", home_score=20.0) for w in (1, 2, 3, 4, 6)])


def _bundle(report_rows, roster_rows):
    rep = pd.DataFrame(report_rows, columns=["season", "week", "gsis_id", "report_status"])
    ros = pd.DataFrame(roster_rows, columns=["season", "week", "gsis_id", "status"])
    return type("B", (), {"schedule": _sched(), "rosters": ros, "injury_report": lambda self, s: rep})()


def test_left_early_needs_fewer_snaps_and_a_listing_for_the_next_game():
    mine = pd.DataFrame({"season": [2026] * 4, "week": [1, 2, 3, 4], "team": ["DAL"] * 4, "gsis_id": ["p"] * 4,
                         "fewer_snaps": [True, True, False, True]})
    b = _bundle([(2026, 2, "p", "Questionable"), (2026, 4, "p", "Out"), (2026, 6, "p", "Doubtful")],
                [(2026, 3, "p", "ACT")])
    out = player.left_early(mine, b)
    # week 1: Questionable for week 2; week 2: nothing for week 3 (a role change); week 3: full snaps (the
    # week-4 Out does not reach back); week 4: the next game is week 6 (a bye in 5), Doubtful
    assert out["left_early"].tolist() == [True, False, False, True]
    assert out["hurt_next"].tolist() == ["Questionable", None, None, "Doubtful"]
    ir = _bundle([], [(2026, 3, "p", "RES")])
    assert player.left_early(mine, ir)["hurt_next"].tolist() == [None, "on IR", None, None]
    none_yet = _bundle([], [])
    assert not player.left_early(mine, none_yet)["left_early"].any(), "no report and no roster listing: not marked"


def test_a_quarterbacks_own_starts_are_never_backup_games():
    sched = pd.DataFrame([dict(game_id=f"2026_0{w}_TB_X", season=2026, week=w, home_team="X", away_team="TB",
                               home_qb_id="x", away_qb_id=q) for w, q in ((1, "baker"), (2, "baker"), (3, "teddy"))])
    mine = pd.DataFrame([dict(game_id=g, team="TB", season=2026) for g in sched["game_id"]])
    # priced week 4: teddy started week 3, so he is the current starter; baker's card is baker's own games
    assert player.backup_qb(mine, sched, "TB", 2026, 4)["backup_qb"].tolist() == [True, True, False]
    assert player.backup_qb(mine, sched, "TB", 2026, 4, "baker")["backup_qb"].tolist() == [False, False, False]
    assert player.backup_qb(mine, sched, "TB", 2026, 4, "mike")["backup_qb"].tolist() == [True, True, False]


def test_a_backs_receiving_markets_count_the_receivers_as_main_teammates():
    targets = pd.DataFrame({"season": [2026] * 9, "posteam": ["SF"] * 9,
                            "gsis_id": ["wr1"] * 4 + ["wr2"] * 3 + ["te1"] * 1 + ["rb1"] * 1})
    carries = pd.DataFrame({"season": [2026] * 5, "posteam": ["SF"] * 5, "gsis_id": ["rb2"] * 3 + ["rb1"] * 2})
    pos = {"wr1": "WR", "wr2": "WR", "te1": "TE", "rb1": "RB", "rb2": "RB"}
    b = type("B", (), {"targets": targets, "carries": carries, "cut": lambda self, df, s, w, n: df,
                       "position_at": lambda self, g, s, w: pos[g]})()
    assert player.main_teammates(b, "rb1", "SF", "RB", 2026, 5) == ["rb2"]
    assert player.main_teammates(b, "rb1", "SF", "RB", 2026, 5, "rush_yds") == ["rb2"]
    assert player.main_teammates(b, "rb1", "SF", "RB", 2026, 5, "receptions") == ["rb2", "wr1", "wr2", "te1"]
    assert player.main_teammates(b, "wr1", "SF", "WR", 2026, 5, "rec_yds") == ["wr2", "te1"], "a WR's list is unchanged"


def test_lineup_detail_gives_each_game_its_reason_and_lineup_marks_keeps_its_shape(monkeypatch):
    ros = pd.DataFrame([{"season": 2026, "week": w, "team": "LA", "gsis_id": "00-0000002", "full_name": "Puka Nacua",
                         "status": "ACT"} for w in (1, 2, 3, 4, 5)])
    share = pd.DataFrame({"game_id": ["g1", "g4"], "gsis_id": ["00-0000002"] * 2, "offense_pct": [0.9, 0.9]})
    rep = pd.DataFrame([{"season": 2026, "week": 5, "team": "LA", "gsis_id": "filler", "report_status": None}])
    b = type("B", (), {"rosters": ros, "snap_share": share, "schedule": None, "injury_report": lambda self, s: rep})()
    last = pd.DataFrame({"season": [2026] * 4, "week": [1, 2, 3, 4], "game_id": ["g1", "g2", "g3", "g4"],
                         "backup_qb": [False, False, False, True], "qb_started": [None, None, None, "B.Backup"]})
    monkeypatch.setattr(player, "main_teammates", lambda *a: ["00-0000002"])
    monkeypatch.setattr(player, "current_starter", lambda *a: "00-0000009")
    reasons, lines_, _ = player.lineup_detail(b, last, "00-0000001", "LA", "WR", 2026, 5, "rec_yds")
    assert reasons == [[], ["Puka Nacua out"], ["Puka Nacua out"], ["B.Backup started at QB"]]
    marks, lines2, _ = player.lineup_marks(b, last, "00-0000001", "LA", "WR", 2026, 5)
    assert marks == [False, True, True, True] and lines2 == lines_


def test_part_four_sorts_the_facts_by_direction():
    pl, c, kw = _card()
    high, low = card.holds_up(pl, c, "over", opp="TB", game_lines=GL, opp_row=OPP, grades=kw["grades"],
                              qb_today="", scoring=SCORING, fixed_spread=3.0)
    assert high[0] == "He went over 64.5 in 1 of his last 4 games."
    assert "He averaged 51.5 rushing yards in his last 4 games without weeks 2 and 3, against a 64.5 line." in high
    assert low == ["Tampa Bay has allowed 4.4 yards a carry to RBs; his longer-run rate is 4.2.",
                   "DAL run offense B vs TB run defense C.", "DAL is implied 29.5 points; it has scored 27.3 a game.",
                   "DAL is favored by 9.5: teams ahead tend to run more."]
    # the same side either way: the facts are about the line, not a side
    assert card.holds_up(pl, c, "under", opp="TB", game_lines=GL, opp_row=OPP, grades=kw["grades"], qb_today="",
                         scoring=SCORING, fixed_spread=3.0) == (high, low)
    # a grade earned with a quarterback who is out is not a fact; a spread under the threshold is not script
    _, low2 = card.holds_up(pl, c, "over", opp="TB", game_lines={**GL, "points": 2.5}, opp_row=OPP,
                            grades=kw["grades"], qb_today="Dak Prescott ruled Out.", scoring=SCORING, fixed_spread=3.0)
    assert not any("offense B" in x or "favored" in x for x in low2)


def test_a_passing_card_reads_the_underdog_as_throwing_more():
    pl, c, kw = _card()
    c = {**c, "market": "rec_yds"}
    pl.perf = None
    high, low = card.holds_up(pl, c, "over", opp="TB", game_lines={**GL, "favorite": "TB"}, opp_row=None,
                              grades=None, qb_today="", scoring=None, fixed_spread=3.0)
    assert low == ["DAL is a 9.5-point underdog: teams behind tend to throw more."] and high == []


def test_both_cards_print_the_four_parts_and_the_same_numbers():
    pl, c, kw = _card(perf_scope="season")
    md = card.render_md(pl, c, "over", **kw)
    text = card.render(pl, c, "over", **kw)
    L = md.splitlines()
    for h in ("**1 · The line**", "**2 · This season**", "**3 · Matchup**", "**4 · Does it hold up**"):
        assert h in L, h
    assert "| DAL pass offense vs TB pass defense | A- vs B |" in L and "| Implied points | DAL 29.5, TB 20.0 |" in L
    assert "| TB this season | 20.0 scored, 24.5 allowed a game (4 games) |" in L
    assert "| 3 | WAS | 19 | 98 | 5.2 | 70% | SPECIAL: Lead Back out |" in L
    assert card.HOLDS_NOTE in md and "1 THE LINE" in text and "4 DOES IT HOLD UP" in text
    import re
    nums = lambda t: set(re.findall(r"-?\d+(?:\.\d+)?", t))     # noqa: E731
    assert not (nums(md.split("What needs to be true:")[0]) - nums(text) - {"4"})
    for banned in ("bet", "lean", "pick", "recommend", "likely", "lock"):
        assert not re.search(rf"\b{banned}\b", md.lower()), banned
