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
    assert it({"favorite": None, "spread_text": None, "total": 44.0}, "A", "B") is None, "no spread is not even"
    assert it({"favorite": "KC", "points": 3, "total": 44.0}, "A", "B") is None, "a favorite that is neither team"
    assert it(None, "A", "B") is None and it({"favorite": "A", "points": 3}, "A", "B") is None


def test_part_one_prints_the_books_split_and_both_bars():
    pl, c, kw = _card()
    rows = dict(card.line_part(pl, c, "over"))
    # -125 -> 55.6%, -132 -> 56.9%; margin removed: 55.6 / (55.6 + 56.9) = 49.4%
    assert rows["The book's split at this line, margin removed"] == "Over 49% / Under 51% (the book's numbers)"
    # near-even prices: the book's 50/50 sits within a point of the posted line
    assert abs(c["line_50"] - 64.5) <= 1.0 and rows["Where the book's 50/50 sits (our math)"].endswith("rushing yards")
    assert rows["Line"] == "64.5 rushing yards, Over -125 / Under -132"
    assert rows["Workload the prices imply (our math)"] == f"~{card._round(card.value(c, 'book_expects'))} carries"
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


def test_a_seasons_only_game_is_read_against_last_season_for_leaving_early():
    """Marquise Brown, 2026: 22% of snaps in week 2, his only game, then Out with an ankle in week 3."""
    hist = pd.DataFrame({"season": [2025, 2025, 2025, 2026], "week": [16, 17, 18, 2],
                         "snap_pct": [0.53, 0.60, 0.81, 0.22]})
    mine = pd.DataFrame({"season": [2026], "week": [2], "team": ["DAL"], "gsis_id": ["p"], "snap_pct": [0.22],
                         "fewer_snaps": [False]})
    b = _bundle([(2026, 3, "p", "Out")], [])
    out = player.left_early(mine, b, hist, 0.5)
    assert out["left_early"].tolist() == [True] and out["hurt_next"].tolist() == ["Out"]
    assert not player.left_early(mine, b)["left_early"].any(), "without his history there is nothing to compare"
    steady = mine.assign(snap_pct=[0.40])                      # 0.40 is not under half of last season's 0.65
    assert not player.left_early(steady, b, hist.assign(snap_pct=[0.53, 0.60, 0.81, 0.40]), 0.5)["left_early"].any()


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
    reasons, lines_, _ = player.lineup_detail(b, last, "00-0000001", "LA", "WR", 2026, 5)
    assert reasons == [[], ["Puka Nacua out"], ["Puka Nacua out"], ["B.Backup started at QB"]]
    marks, lines2, _ = player.lineup_marks(b, last, "00-0000001", "LA", "WR", 2026, 5)
    assert marks == [False, True, True, True] and lines2 == lines_


def _grid(pl, c, **kw):
    args = dict(opp="TB", game_lines=GL, opp_row=OPP, grades={"off": "B", "def": "C"}, qb_today="",
                scoring=SCORING, fixed_spread=3.0)
    return {f: (d, ev) for f, d, ev in card.holds_up(pl, c, "over", **{**args, **kw})}


def test_part_four_is_a_grid_of_every_factor_with_its_direction():
    pl, c, _ = _card()
    g = _grid(pl, c)
    assert list(g) == card.FACTORS, "the same rows on every card"
    assert g["Games over the line"] == ("high", "1 of 4")
    assert g["Games like tonight"] == ("high", "0 of 2 without weeks 2 and 3")
    assert g["His average vs the line"] == ("high", "51.5 vs 64.5 without them")
    assert g["Opponent's rate vs his longer-run rate"] == ("low", "4.4 vs 4.2 yards a carry")
    assert g["Unit matchup"] == ("low", "run offense B vs defense C")
    assert g["Implied points vs his team's scoring"] == ("low", "29.5 vs 27.3 a game")
    assert g["Game script"] == ("low", "favored by 9.5: teams ahead tend to run more")
    assert card.grid_cell("low", "4.4 vs 4.2") == "▼ low · 4.4 vs 4.2" and card.grid_cell(None, "x") == "– x"
    # the facts are about the line, not a side
    assert card.holds_up(pl, c, "under", opp="TB", game_lines=GL, opp_row=OPP, grades={"off": "B", "def": "C"},
                         qb_today="", scoring=SCORING, fixed_spread=3.0) == \
        card.holds_up(pl, c, "over", opp="TB", game_lines=GL, opp_row=OPP, grades={"off": "B", "def": "C"},
                      qb_today="", scoring=SCORING, fixed_spread=3.0)


def test_part_four_says_why_a_row_has_no_direction():
    pl, c, _ = _card()
    g = _grid(pl, c, game_lines={**GL, "points": 2.5}, qb_today="Dak Prescott ruled Out.", opp_row=None)
    assert g["Unit matchup"] == (None, "graded with Dak Prescott, who is Out")
    assert g["Game script"] == (None, "favored by 2.5: a close game")
    assert g["Opponent's rate vs his longer-run rate"] == (None, "not available")
    dog = _grid(pl, c, game_lines={**GL, "favorite": "TB"})
    assert dog["Game script"] == ("high", "9.5-point underdog: teams behind tend to run less")


def test_a_passing_card_reads_the_game_script_the_other_way():
    pl, c, _ = _card()
    c = {**c, "market": "rec_yds"}
    pl.perf = None
    assert _grid(pl, c, opp_row=None, grades=None)["Game script"] == \
        ("high", "favored by 9.5: teams ahead tend to throw less")
    assert _grid(pl, c, opp_row=None, grades=None, game_lines={**GL, "favorite": "TB"})["Game script"] == \
        ("low", "9.5-point underdog: teams behind tend to throw more")


def test_the_even_line_interpolates_between_half_points():
    # 15% of games at 0 catches, 43% at 1, 42% at 2: over 0.5 is 85%, over 1.5 is 42% -> 0.5 + 0.35/0.43
    outs = [0] * 15 + [1] * 43 + [2] * 42
    assert card.even_line(outs) == pytest.approx(0.5 + 0.35 / 0.43)
    assert card.even_line([1] * 49 + [2] * 51) == pytest.approx(1.5 + 0.01 / 0.51), "51% over 1.5"
    # most games at or below zero: the even point is read below 0.5, never clamped to it
    # 60% at -2, 40% at 3: over -2.5 is 100%, over -1.5 is 40% -> -2.5 + 0.5 / 0.6
    assert card.even_line([-2] * 60 + [3] * 40) == pytest.approx(-2.5 + 0.5 / 0.6)
    assert card.even_line([0] * 70 + [3] * 30) < 0.5, "under a half go over 0.5: the even point is below it"


def test_uneven_prices_move_the_books_50_50_off_the_line():
    """Over -172 / Under +104 (Pickens' catches tonight): the book makes the Over the likelier side, so the
    line it splits evenly is above the posted one; turned round, below it."""
    fixed = settings.load()["fixed"]
    season, window = _games()
    pl = _player(season, window)
    m = rush_model(ypc=4.2)
    hi = card.compute(pl, m, "rush_yds", 64.5, odds.multiplier_from_american(-172),
                      odds.multiplier_from_american(104), fixed)
    lo = card.compute(pl, m, "rush_yds", 64.5, odds.multiplier_from_american(104),
                      odds.multiplier_from_american(-172), fixed)
    assert lo["line_50"] < 64.5 < hi["line_50"]
    # the 50/50 line is the median game at the implied workload: half the games go over it
    out = m.outcome(m._counts_at(card.value(hi, "book_expects")))
    assert abs((out > hi["line_50"]).mean() - 0.5) < 0.02


def test_the_books_split_always_adds_to_100():
    pl, c, _ = _card()
    c = {**c, "no_vig_over": 0.495}            # 49.5 rounds up to 50; the Under is the rest, not 50.5 -> 51
    assert dict(card.line_part(pl, c, "over"))["The book's split at this line, margin removed"] == \
        "Over 50% / Under 50% (the book's numbers)"


def test_every_game_special_is_said_in_part_four():
    pl, c, _ = _card()
    pl.perf["reasons"] = [["X out"]] * 4
    g = _grid(pl, c, game_lines=None, opp_row=None, grades=None, scoring=None)
    assert g["Games like tonight"] == (None, "every game was special")
    assert g["His average vs the line"] == ("high", "57.8 vs 64.5, all special")


def test_a_grade_earned_with_an_out_quarterback_says_so_in_the_matchup_table():
    rows = dict(card.matchup_extra("DAL", "TB", GL, GA, SCORING, "Dak Prescott ruled Out."))
    assert rows["DAL pass offense vs TB pass defense"] == "A- vs B (graded with Dak Prescott, who is Out)"
    assert rows["TB run offense vs DAL run defense"] == "D vs B+", "only his own team's offense"


def test_game_conditions_mark_a_game_only_for_what_was_different_in_it(monkeypatch):
    """The user, 2026-10-26: special "if somebody was out", not because somebody is out today."""
    from props.calc import player
    ros = pd.DataFrame([{"season": 2026, "week": w, "team": "PHI", "gsis_id": g, "full_name": n, "status": "ACT"}
                        for w in (1, 2, 3, 4) for g, n in (("wr1", "DeVonta Smith"), ("qb1", "Jalen Hurts"))])
    share = pd.DataFrame({"game_id": ["g1", "g2", "g4", "g1", "g2", "g3"],
                          "gsis_id": ["wr1", "wr1", "wr1", "qb1", "qb1", "qb1"]})
    rep = pd.DataFrame([{"season": 2026, "week": 5, "team": "PHI", "gsis_id": "wr1", "report_status": "Out"},
                        {"season": 2026, "week": 5, "team": "PHI", "gsis_id": "qb1", "report_status": "Out"}])
    b = type("B", (), {"rosters": ros, "snap_share": share, "schedule": None, "injury_report": lambda self, s: rep})()
    rows = pd.DataFrame({"season": [2026] * 4, "week": [1, 2, 3, 4], "game_id": ["g1", "g2", "g3", "g4"],
                         "team": ["PHI"] * 4, "qb_id": ["qb1", "qb1", "qb1", "qb2"],
                         "qb_name": ["J.Hurts", "J.Hurts", "J.Hurts", "T.McKee"]})
    monkeypatch.setattr(player, "main_teammates", lambda *a: ["wr1"])
    monkeypatch.setattr(player, "regular_qb", lambda *a: "qb1")
    reasons, today, like = player.game_conditions(b, rows, "rb1", "PHI", "RB", 2026, 5, "receptions")
    # Smith played weeks 1, 2, 4 and is Out today: only week 3 (he did not play) is special for him; Hurts
    # started weeks 1-3 and is Out today: only week 4 (McKee started) is special for the quarterback
    assert reasons == [[], [], ["DeVonta Smith out"], ["T.McKee started at QB"]]
    assert today == ["DeVonta Smith is Out; he missed 1 of these 4 games (week 3).",
                     "Jalen Hurts (QB) is Out; another quarterback started 1 of these 4 games (week 4)."]
    # each absence in weeks 3 and 4 is one of tonight's: those two are the games like tonight
    assert like == [False, False, True, True]
    # Marquise Brown's card: three games for KC last season, one for PHI -- the KC games say so, and today's
    # lines count his PHI game only
    kc = rows.assign(team=["KC", "KC", "KC", "PHI"], qb_id=["m", "m", "m", "qb1"], season=[2025, 2025, 2025, 2026])
    reasons, today, like = player.game_conditions(b, kc, "rb1", "PHI", "WR", 2026, 5)
    assert reasons[:3] == [["played for KC"]] * 3
    assert today[-1] == "Jalen Hurts (QB) is Out; he started it (his 1 game for PHI)."


def test_the_regular_qb_is_the_one_with_the_most_starts():
    from props.calc import player
    sch = pd.DataFrame([dict(game_id=f"g{w}", season=2026, week=w, home_team="PHI", away_team="X", home_score=20.0,
                             home_qb_id=q, away_qb_id="x") for w, q in ((1, "hurts"), (2, "hurts"), (3, "mckee"))])
    assert player.regular_qb(sch, "PHI", 2026, 4) == "hurts"
    assert player.regular_qb(sch, "PHI", 2026, 1) is None
    tie = sch.assign(home_qb_id=["hurts", "mckee", "x2"])
    assert player.regular_qb(tie, "PHI", 2026, 3) == "mckee", "a tie goes to the most recent starter"


def test_one_season_game_is_singular():
    pl, c, _ = _card()
    S = {**card.season_read(pl, c), "n_season": 1}
    assert card.season_lines(c, S)[-1] == "Only 1 game this season, so this is his last 4."


def test_the_card_says_when_the_player_himself_is_on_the_report():
    from props.calc import __main__ as CLI
    rep = pd.DataFrame([{"season": 2026, "week": 7, "gsis_id": "p1", "report_status": "Out"},
                        {"season": 2026, "week": 7, "gsis_id": "p2", "report_status": "Questionable"},
                        {"season": 2026, "week": 6, "gsis_id": "p3", "report_status": "Out"}])
    b = type("B", (), {"injury_report": lambda self, s: rep})()
    assert CLI.own_status(b, "p1", 2026, 7) == \
        "is ruled Out on this week's official injury report (Sleeper voids an Out player's leg)"
    assert CLI.own_status(b, "p2", 2026, 7) == "is listed Questionable on this week's official injury report"
    assert CLI.own_status(b, "p3", 2026, 7) == "", "last week's listing is not this week's"
    assert CLI.own_status(type("B", (), {"injury_report": lambda self, s: None})(), "p1", 2026, 7) == ""
    assert CLI.report_status(rep, "p1", 7) == "Out" and CLI.report_status(rep, "p1", 6) is None


def test_team_points_are_scored_and_allowed_a_game_from_either_side():
    from props.calc import __main__ as CLI
    sch = pd.DataFrame([dict(season=2026, week=1, home_team="DAL", away_team="NYG", home_score=27.0, away_score=20.0),
                        dict(season=2026, week=2, home_team="PHI", away_team="DAL", home_score=24.0, away_score=17.0),
                        dict(season=2026, week=3, home_team="DAL", away_team="WAS", home_score=None, away_score=None),
                        dict(season=2025, week=4, home_team="DAL", away_team="X", home_score=50.0, away_score=0.0)])
    assert CLI.team_points(sch, "DAL", 2026, 4) == (22.0, 22.0, 2), "(27+17)/2 scored, (20+24)/2 allowed; week 3 unplayed"
    assert CLI.team_points(sch, "PHI", 2026, 4) == (24.0, 17.0, 1)
    assert CLI.team_points(sch, "DAL", 2026, 1) == (0.0, 0.0, 0)


def test_both_cards_print_the_four_parts_and_the_same_numbers():
    pl, c, kw = _card(perf_scope="season")
    md = card.render_md(pl, c, "over", **kw)
    text = card.render(pl, c, "over", **kw)
    L = md.splitlines()
    for h in ("**1 · The line**", "**2 · This season**", "**3 · Matchup**", "**4 · Does it hold up**"):
        assert h in L, h
    assert "| DAL pass offense vs TB pass defense | A- vs B |" in L and "| Implied points | DAL 29.5, TB 20.0 |" in L
    assert "| TB this season | 20.0 scored, 24.5 allowed a game (4 games) |" in L
    assert "| 3 * | WAS | 19 | 98 | 5.2 | 70% |" in L and "- Week 3 *: Lead Back out" in L, "notes under the table"
    assert card.HOLDS_NOTE in md and "1 THE LINE" in text and "4 DOES IT HOLD UP" in text
    import re
    nums = lambda t: set(re.findall(r"-?\d+(?:\.\d+)?", t))     # noqa: E731
    assert not (nums(md.split("What needs to be true:")[0]) - nums(text) - {"4"})
    for banned in ("bet", "lean", "pick", "recommend", "likely", "lock"):
        assert not re.search(rf"\b{banned}\b", md.lower()), banned


def test_games_like_tonight_keep_only_the_games_whose_absences_are_all_tonights(monkeypatch):
    """The user, 2026-10-27, after Makai Lemon's 7 catches with DeVonta Smith out: when tonight's absence
    happened before, those games are the comparison. A game with a different absence too (Goedert out
    then, playing tonight) is not like tonight; nor is a game with nobody out."""
    from props.calc import player
    ros = pd.DataFrame([{"season": 2026, "week": w, "team": "PHI", "gsis_id": g, "full_name": n, "status": "ACT"}
                        for w in (1, 2, 3, 4) for g, n in (("wr1", "DeVonta Smith"), ("te1", "Dallas Goedert"))])
    # Smith: no snap weeks 2 and 3; Goedert: no snap week 3
    share = pd.DataFrame({"game_id": ["g1", "g4", "g1", "g2", "g4"], "gsis_id": ["wr1", "wr1", "te1", "te1", "te1"]})
    rep = pd.DataFrame([{"season": 2026, "week": 5, "team": "PHI", "gsis_id": "wr1", "report_status": "Out"}])
    b = type("B", (), {"rosters": ros, "snap_share": share, "schedule": None, "injury_report": lambda self, s: rep})()
    rows = pd.DataFrame({"season": [2026] * 4, "week": [1, 2, 3, 4], "game_id": ["g1", "g2", "g3", "g4"],
                         "team": ["PHI"] * 4})
    monkeypatch.setattr(player, "main_teammates", lambda *a: ["wr1", "te1"])
    monkeypatch.setattr(player, "regular_qb", lambda *a: None)
    reasons, _, like = player.game_conditions(b, rows, "wr9", "PHI", "WR", 2026, 5, "receptions")
    assert reasons == [[], ["DeVonta Smith out"], ["DeVonta Smith out", "Dallas Goedert out"], []]
    assert like == [False, True, False, False]
    # nobody out tonight: no game is like tonight by absence, and the read keeps the games without a star
    none_out = type("B", (), {"rosters": ros, "snap_share": share, "schedule": None,
                              "injury_report": lambda self, s: rep.iloc[0:0]})()
    assert player.game_conditions(b=none_out, rows=rows, gsis="wr9", team="PHI", pos="WR", season=2026, week=5,
                                  market="receptions")[2] is None


def test_the_season_read_and_part_four_compare_with_the_games_like_tonight():
    pl, c, _ = _card()
    # weeks 3 and 4 share tonight's absence; week 2 left early, so it is never a game like tonight
    pl.perf["reasons"] = [[], ["X out"], ["X out"], ["X out"]]
    pl.perf["like_tonight"] = [False, True, True, True]
    pl.tonight = True
    S = card.season_read(pl, c)
    assert [r["like"] for r in S["rows"]] == [False, False, True, True]
    assert S["like_weeks"] == ["week 3", "week 4"]
    # weeks 3 and 4: 98 and 62 yards on 19 carries each (the _games fixture)
    assert S["clean"]["stat"] == pytest.approx(80.0) and S["clean"]["work"] == pytest.approx(19.0)
    assert (S["over_clean"], S["under_clean"]) == (1, 1)
    rows = dict(card.line_part(pl, c, "over"))
    assert rows["His carries in his last 4 games"] == "15.5 a game; 19.0 in games like tonight (weeks 3 and 4)"
    assert rows["Over 64.5"] == "1 of his last 4 games; 1 of 2 in games like tonight (weeks 3 and 4)"
    g = _grid(pl, c)
    assert g["Games like tonight"] == (None, "1 of 2 (weeks 3 and 4)")
    assert g["His average vs the line"] == ("low", "80.0 vs 64.5 in games like tonight")
    assert card.season_lines(c, S)[1] == ("Average in games like tonight (weeks 3 and 4): 19.0 carries, "
                                          "80.0 rushing yards, 4.2 yards a carry (2 games).")
    assert card.notes_head(True).startswith("What was different (*; the second average is the games like tonight")
