"""props-v1.29 research columns (scripts/research.py): what a line implies, last
game's usage against earlier weeks, and the receiving role-shift flag."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ENGINE = Path(__file__).resolve().parents[1] / "engine" / "scripts"
sys.path.insert(0, str(ENGINE))

import model as M  # noqa: E402
import research as RS  # noqa: E402


def _p_over(targets, line, stat="receptions", team=34.0, share=0.2, cr=0.7, ypt=8.0):
    s = targets / team
    out, _ = M.simulate_team_game(np.random.default_rng(RS.SEED), RS.N_SEARCH, team, 30.0, {"p": s}, {"p": cr},
                                  {"p": ypt}, 1.06, other_bucket=True)
    return float((out["p"][0 if stat == "receptions" else 1] > line).mean())


def test_the_implied_targets_make_the_line_a_coin_flip():
    imp, proj = RS.implied_targets(4.5, "receptions", 34.0, 30.0, 0.2, 0.7, 8.0, 1.06)
    assert abs(proj - 6.8) < 1e-9, "projected targets = team targets x share"
    assert imp is not None and 5.0 < imp < 9.5
    assert abs(_p_over(imp, 4.5) - 0.5) < 0.03, "at the implied workload the Over is ~50%"


def test_a_higher_line_implies_more_targets():
    lo, _ = RS.implied_targets(3.5, "receptions", 34.0, 30.0, 0.2, 0.7, 8.0, 1.06)
    hi, _ = RS.implied_targets(5.5, "receptions", 34.0, 30.0, 0.2, 0.7, 8.0, 1.06)
    yds, _ = RS.implied_targets(60.5, "rec_yards", 34.0, 30.0, 0.2, 0.7, 8.0, 1.06)
    assert lo < hi and yds is not None


def test_a_line_outside_the_search_says_so_instead_of_guessing():
    imp, proj = RS.implied_targets(40.5, "receptions", 34.0, 30.0, 0.2, 0.7, 8.0, 1.06)
    assert imp is None and proj > 0


def test_the_search_never_touches_the_global_random_state():
    np.random.seed(1)
    before = np.random.random()
    np.random.seed(1)
    RS.implied_targets(4.5, "receptions", 34.0, 30.0, 0.2, 0.7, 8.0, 1.06)
    assert np.random.random() == before


def test_usage_change_needs_three_weeks_and_compares_the_last_with_the_rest():
    assert RS.usage_change([(1, 0.6, 0.2, 0.0), (2, 0.6, 0.2, 0.0)]) is None
    u = RS.usage_change([(1, 0.60, 0.20, 0.0), (2, 0.70, 0.20, 0.0), (3, 0.85, 0.21, 0.0)])
    assert u["week"] == 3 and abs(u["snap_base"] - 0.65) < 1e-12 and abs(u["ts_base"] - 0.20) < 1e-12


def test_the_role_flag_is_the_pre_registered_rule():
    up = RS.usage_change([(1, 0.60, 0.20, 0.0), (2, 0.60, 0.20, 0.0), (3, 0.80, 0.21, 0.0)])
    assert RS.role_flag(up, 3)[0] == "role up", "snaps +20 pts, targets +1 pt"
    assert RS.role_flag(up, 4) is None, "last week must be the week before this one"
    caught_up = RS.usage_change([(1, 0.60, 0.20, 0.0), (2, 0.60, 0.20, 0.0), (3, 0.80, 0.26, 0.0)])
    assert RS.role_flag(caught_up, 3) is None, "targets already followed the snaps"
    down = RS.usage_change([(1, 0.80, 0.20, 0.0), (2, 0.80, 0.20, 0.0), (3, 0.60, 0.19, 0.0)])
    assert RS.role_flag(down, 3)[0] == "role down"
    assert RS.role_flag(None, 3) is None


def test_the_scorers_research_block_never_draws_from_the_pricing_stream():
    """score_game prices every line from ONE sequential generator (`rng`); a draw
    from it in the research block would shift every recorded p_model. The
    block must reach randomness only through research.py's own generators."""
    src = (ENGINE / "score_game.py").read_text(encoding="utf-8")
    block = src[src.index("# ---------- 8a. research columns"):src.index("# ---------- 8b/9. report")]
    assert "rng" not in block and "random" not in block
    assert "pd.DataFrame(rows)" in block, "research rows come from this run's lines, not the prior-log merge"
    assert "SCENARIO" in block, "no implied-workload search inside a scenario run ('if he's out' or yours)"


def test_backfield_jobs_compare_the_last_game_with_earlier_weeks():
    assert RS.backfield_jobs([(1, 0.6, 0.1, 0.5, 1, 2), (2, 0.6, 0.1, 0.5, 1, 2)]) is None
    b = RS.backfield_jobs([(1, 0.60, 0.30, 1.0, 2, 2), (2, 0.70, 0.10, float("nan"), 0, 0),
                           (3, 0.55, 0.00, 0.0, 0, 1)])
    assert b["week"] == 3 and abs(b["early_base"] - 0.65) < 1e-12 and abs(b["passdown_base"] - 0.20) < 1e-12
    assert b["i5_base"] == 1.0, "a week with no team inside-5 carry says nothing about his share"
    assert (b["i5_n"], b["i5_team"]) == (0, 1)


def test_the_role_flag_never_claims_an_adjustment_the_snap_rule_skips():
    u = RS.usage_change([(1, 0.03, 0.02, 0.0), (2, 0.03, 0.02, 0.0), (3, 0.30, 0.03, 0.0)])
    assert RS.role_flag(u, 3) is None, "earlier snaps under 5%: model.snap_react does not act, so no flag"
    assert M.snap_react(0.02, 0.30, 0.03, 0.5) == 0.02


def test_a_research_row_names_its_book_when_it_is_not_sleeper():
    import pandas as pd
    import score_game as SG
    x = pd.Series({"market": "player_receptions", "line": 4.5, "book": "draftkings", "price_over": -120,
                   "price_under": -105, "median": 5.0, "p10": 2.0, "p90": 9.0, "p_over_model": 0.55,
                   "p_over_book": 0.52, "implied": 6.0, "projected": 6.5, "unit": "targets"})
    assert SG.research_cells(x, {"player_receptions": "catches"}).startswith("| catches (DraftKings) | 4.5 |")
    assert SG.research_cells(x.copy().replace({"draftkings": "sleeper"}), {"player_receptions": "catches"})         .startswith("| catches | 4.5 |")


def test_compare_books_is_opt_in_guarded_and_never_fatal():
    src = (ENGINE / "score_game.py").read_text(encoding="utf-8")
    block = src[src.index("# ---------- 7a2. other books"):src.index("if SNAP is None and not a.no_odds and not a.lines_file and (a.source")]
    assert "a.compare_books" in block and "COMPARE_QUOTA_MIN" in block
    assert "except Exception" in block, "a failed comparison is a sources note, never a lost run"
    assert "--archive" not in block, "a comparison pull never writes the line archive"


def test_break_even_workload_at_the_posted_prices():
    assert RS.breakeven(-141) == pytest.approx(141 / 241) and RS.breakeven(110) == pytest.approx(100 / 210)
    assert RS.breakeven(None) is None and RS.breakeven(float("nan")) is None and RS.breakeven(1.9) is None
    imp, proj, o, u = RS.implied_targets(4.5, "receptions", 34.0, 30.0, 0.2, 0.7, 8.0, 1.06, prices=(-141, 110))
    assert (imp, proj) == RS.implied_targets(4.5, "receptions", 34.0, 30.0, 0.2, 0.7, 8.0, 1.06), \
        "asking for the break-even never moves the coin flip"
    # at -141 the Over needs 58.5% of non-pushes: more targets than the coin flip; at +110 the Under
    # needs 47.6%, so it pays a little past the coin flip
    assert o > imp and u > imp and o > u
    assert abs(_p_over(o, 4.5) - 141 / 241) < 0.03 and abs(_p_over(u, 4.5) - (1 - 100 / 210)) < 0.03
    # a side with no price gives no number, and the cell says why
    _i, _p, o2, u2 = RS.implied_targets(4.5, "receptions", 34.0, 30.0, 0.2, 0.7, 8.0, 1.06, prices=(-141, None))
    assert o2 == pytest.approx(o) and u2 is None
    cell = RS.break_even_cell({"unit": "targets", "over_needs": o2, "under_needs": u2,
                               "be_over": RS.breakeven(-141), "be_under": None})
    assert cell == f"Over above {o2:.1f} targets; Under: no price posted"


def test_a_whole_line_coin_flip_ignores_pushes_like_the_prices_do():
    imp, _p, o, u = RS.implied_targets(4.0, "receptions", 34.0, 30.0, 0.2, 0.7, 8.0, 1.06, prices=(-110, -110))
    assert u < imp < o, "the coin flip sits between the two break-evens on a whole line too"


def test_an_out_teammate_is_named_only_when_he_had_a_real_role():
    import pandas as pd
    t = pd.DataFrame({"posteam": "CIN", "week": [2] * 36 + [3] * 38,
                      "pid": ["chase"] * 12 + ["young"] + ["x"] * 23 + ["chase"] * 12 + ["young"] + ["x"] * 25})
    c = pd.DataFrame({"posteam": "CIN", "week": [2] * 25, "pid": ["brown"] * 18 + ["x"] * 7})
    d = pd.DataFrame({"posteam": "CHI", "week": [1] * 30, "pid": ["caleb"] * 30})
    e = pd.DataFrame(columns=["posteam", "week", "pid"])
    assert not RS.out_matters("young", "CIN", t, c, e), "two targets in two games is not news"
    assert RS.out_matters("chase", "CIN", t, c, e), "a third of the targets is"
    assert RS.out_matters("brown", "CIN", t, c, e), "the lead back"
    assert RS.out_matters("caleb", "CHI", e, e, d), "the starting QB"
    assert not RS.out_matters("rookie", "CIN", t, c, e), "no play and no prior: unknown, not flagged"
    assert RS.out_matters("vet", "CIN", t, c, e, prior_ts=0.22), "out all season: last season's share decides"
    assert not RS.out_matters("vet", "CIN", t, c, e, prior_ts=float("nan"))


def test_games_without_a_target_still_count_toward_his_share():
    import pandas as pd
    t = pd.DataFrame({"posteam": "CIN", "week": [1] * 30 + [2] * 30 + [3] * 30,
                      "pid": ["g"] * 4 + ["x"] * 26 + ["x"] * 60})
    e = pd.DataFrame(columns=["posteam", "week", "pid"])
    assert RS.role_share(t, "g", "CIN") == pytest.approx(4 / 30), "only the week he was targeted"
    assert RS.role_share(t, "g", "CIN", weeks={1, 2, 3}) == pytest.approx(4 / 90), "every week he was active"
    assert not RS.out_matters("g", "CIN", t, e, e, weeks={1, 2, 3}), "a gadget week is not a role"


def test_a_search_that_runs_out_says_where_in_his_units():
    imp, proj, o, u = RS.implied_targets(40.5, "receptions", 34.0, 30.0, 0.2, 0.7, 8.0, 1.06, prices=(-130, -127))
    e = RS.edges_for()
    assert o is None and e["over_edge"] == "max" and e["over_limit"] > proj
    cell = RS.break_even_cell({"unit": "targets", "over_needs": o, "under_needs": u, "be_over": RS.breakeven(-130),
                               "be_under": RS.breakeven(-127), **e})
    assert cell.startswith(f"Over: needs more than {e['over_limit']:.1f} targets (about all the work")
    assert "beyond the search range" not in cell


def test_usage_carries_the_counts_when_given():
    u = RS.usage_change([(1, 0.70, 0.25, 0.0, 9, 0), (2, 0.74, 0.25, 0.0, 8, 0), (3, 0.93, 0.19, 0.0, 6, 0)])
    assert (u["tn"], u["tn_base"], u["cn"]) == (6.0, 8.5, 0.0)
    assert "tn" not in RS.usage_change([(1, 0.6, 0.2, 0.0), (2, 0.6, 0.2, 0.0), (3, 0.6, 0.2, 0.0)])


def test_worth_a_look_needs_a_story_and_last_games_workload_past_the_price():
    base = dict(player="Woody Marks", market="player_rush_yds", unit="carries", over_needs=11.4, under_needs=9.3,
                cn=6.0, tn=1.0, usage_week=3, flags="Nico Collins back (missed last week)")
    assert RS.worth_a_look(base, 3) == ("Under", "last game 6 carries; the Under pays at 9.3 or fewer")
    assert RS.worth_a_look(dict(base, preview="last week differs: Nico Collins back"), 3)[1].endswith(
        "; last week differs: Nico Collins back"), "the mark says whether last week transfers"
    assert RS.worth_a_look(dict(base, flags="Zay Flowers active (missed 1 of 3 weeks)"), 3) is None, \
        "an old miss is not a return"
    assert RS.worth_a_look(dict(base, flags=""), 3) is None, "no story, no mark"
    assert RS.worth_a_look(dict(base, cn=7.0), 3) is None, "7 carries is inside the 3-carry margin"
    assert RS.worth_a_look(dict(base, usage_week=2), 3) is None, "last game must be the one just played"
    assert RS.worth_a_look(dict(base, flags="role up"), 3) is None, "a role-up story never marks an Under"
    hig = dict(player="Tee Higgins", market="player_receptions", unit="targets", over_needs=8.5,
               under_needs=7.1, tn=6.0, cn=0.0, usage_week=3, flags="role up")
    assert RS.worth_a_look(hig, 3) is None, "role up, but last game's 6 targets do not clear the Over's 8.5"
    assert RS.worth_a_look(dict(hig, tn=10.0), 3) is None, "10 targets is inside the 2-target margin"
    assert RS.worth_a_look(dict(hig, tn=11.0), 3) == ("Over", "last game 11 targets; the Over pays above 8.5")
    assert RS.worth_a_look(dict(hig, flags="Marks out, also out last week", tn=11.0), 3)[0] == "Over", \
        "a teammate out points Over"
    assert RS.worth_a_look(dict(hig, flags="Tee Higgins out, played last week", tn=11.0), 3) is None, \
        "his own out is not a story"
    # a story sets the direction even for a player on a new team
    assert RS.worth_a_look(dict(hig, flags="role down; new team (from ATL)", tn=11.0), 3) is None
    assert RS.worth_a_look(dict(hig, flags="new team (from ATL)", tn=4.0), 3)[0] == "Under", "new team alone: either"
    assert RS.worth_a_look(dict(hig, flags="role up; Puka Nacua back (missed last week)", tn=13.0), 3) is None,         "more snaps but the star teammate back: the stories conflict, no mark"
    assert RS.worth_a_look(dict(hig, unit=None), 3) is None


def test_a_qb_out_is_a_story_for_the_backs_only():
    rec = dict(player="Luther Burden III", market="player_receptions", unit="targets", over_needs=7.3,
               under_needs=6.1, tn=11.0, cn=0.0, usage_week=3, flags="Caleb Williams (QB) out, also out last week")
    assert RS.worth_a_look(rec, 3) is None, "a backup QB is not an Over story for a receiver"
    rb = dict(player="D'Andre Swift", market="player_rush_yds", unit="carries", over_needs=16.5,
              under_needs=13.8, cn=20.0, tn=2.0, usage_week=3, flags="Caleb Williams (QB) out, also out last week")
    assert RS.worth_a_look(rb, 3)[0] == "Over", "the backs carry more"


def test_the_preview_note_and_qb_change():
    import pandas as pd
    assert RS.preview_note([]) == "last week was a preview: same QB, same key absences"
    assert RS.preview_note(["Breece Hall newly out"]) == "last week differs: Breece Hall newly out"
    lw = pd.DataFrame({"passer_player_id": ["k"] * 30 + ["w"] * 2,
                       "passer_player_name": ["C.Keenum"] * 30 + ["C.Williams"] * 2})
    assert RS.qb_change(lw, "k", "Case Keenum") is None, "same starter"
    assert RS.qb_change(lw, "t", "Kyle Trask") == "QB change (C.Keenum last week, Kyle Trask today)"
    assert RS.qb_change(lw, None, None) is None and RS.qb_change(lw.iloc[0:0], "k", "x") is None


def test_a_returning_back_counts_as_a_key_teammate():
    assert RS.is_key_teammate(prior_ts=0.20), "a target earner"
    assert RS.is_key_teammate(prior_ts=0.03, prior_rs=0.28), "a back with a real share of the carries (Jaylen Wright)"
    assert RS.is_key_teammate(season_rs=0.40), "this season's carries count too"
    assert not RS.is_key_teammate(prior_ts=0.05, prior_rs=0.04, season_ts=float("nan"))
    assert not RS.is_key_teammate()


def test_the_board_flag_uses_the_tested_carry_weeks():
    # weeks 1-2 on special teams with no carries do not count; weeks 3-5 do
    wks = [(1, 0.10, 0.0, 0.0, 0, 0), (2, 0.12, 0.0, 0.0, 0, 0), (3, 0.40, 0.05, 0.30, 1, 8),
           (4, 0.45, 0.05, 0.35, 1, 9), (5, 0.80, 0.06, 0.70, 2, 19)]
    c = RS.carry_change(wks)
    assert c["week"] == 5 and abs(c["cs_base"] - 0.325) < 1e-9 and RS.carry_flag(c, 5)[0] == "carries up"
    assert RS.carry_change(wks[:4]) is None, "two carry weeks are not enough"
    assert RS.carry_change([(1, 0.5, 0.1, 0.4)] * 4) is None, "no counts, no flag"


def test_a_questionable_role_player_is_worth_watching_even_unpriced():
    assert RS.worth_watching(target_share=0.096), "Noah Fant: 12 of 125 targets, below the 10% pricing rule"
    assert RS.worth_watching(carry_share=0.12) and RS.worth_watching(snap_share=0.47)
    assert not RS.worth_watching(target_share=0.02, carry_share=0.0, snap_share=0.12), "a depth body is not news"
    assert not RS.worth_watching(float("nan"), None, None)


def test_a_questionable_flag_lands_where_his_work_goes():
    assert RS.watch_applies("TE", "player_receptions", "TE") and RS.watch_applies("TE", "player_reception_yds", "WR")
    assert not RS.watch_applies("TE", "player_rush_yds", "RB"), "a TE2's status is not a rushing story"
    assert RS.watch_applies("RB", "player_rush_yds", "RB") and RS.watch_applies("RB", "player_receptions", "RB")
    assert not RS.watch_applies("RB", "player_receptions", "WR")
    assert RS.watch_applies("QB", "player_rush_yds", "RB"), "a QB's status touches every row"


def test_the_pays_cell_says_which_zone_our_projection_is_in():
    base = {"unit": "targets", "over_needs": 7.1, "under_needs": 5.7, "be_over": 0.56, "be_under": 0.57}
    assert RS.break_even_cell({**base, "projected": 5.5}).endswith("· we project 5.5: Under zone")
    assert RS.break_even_cell({**base, "projected": 6.3}).endswith("· we project 6.3: no-bet zone")
    assert RS.break_even_cell({**base, "projected": 7.4}).endswith("· we project 7.4: Over zone")
    assert "we project" not in RS.break_even_cell({**base, "projected": 5.5, "be_under": None}), \
        "no zone when a side has no price"


def test_a_backfield_takeover_is_flagged_and_points_the_mark():
    hub = {"week": 3, "snap": 0.84, "snap_base": 0.68, "ts": 0.10, "ts_base": 0.08, "cs": 0.83, "cs_base": 0.51}
    assert RS.carry_flag(hub, 3)[0] == "carries up"
    assert RS.carry_flag(dict(hub, cs=0.07, cs_base=0.42), 3)[0] == "carries down", "Allgeier"
    assert RS.carry_flag(dict(hub, cs=0.60), 3) is None, "a 9-point move is not a takeover"
    assert RS.carry_flag(hub, 4) is None, "last week must be the game just played"
    assert RS.carry_flag(None, 3) is None
    row = dict(player="Chuba Hubbard", market="player_rush_yds", unit="carries", over_needs=18.7, under_needs=15.7,
               cn=22.0, tn=4.0, usage_week=3, flags="carries up")
    assert RS.worth_a_look(row, 3)[0] == "Over", "a takeover points the rushing mark Over"
    assert RS.worth_a_look(dict(row, cn=20.0), 3) is None, "20 carries is inside the 3-carry margin of 18.7"
    assert RS.worth_a_look(dict(row, market="player_receptions", unit="targets", tn=9.0, over_needs=4.0), 3) is None, \
        "the carries flag never points a receiving line"
    dem = dict(row, flags="carries down", cn=2.0, over_needs=7.9, under_needs=6.2)
    assert RS.worth_a_look(dem, 3)[0] == "Under"


def test_lines_are_read_at_the_whole_number_that_wins_them():
    assert RS.to_clear(3.5) == 4 and RS.to_clear(44.5) == 45
    assert RS.to_clear(4) == 5, "a whole-number line pushes at 4, so the Over needs 5"
    assert RS.to_clear(0.5) == 1


def test_catches_and_yards_lines_read_together():
    # Devaughn Vele, NO week 4: 3.5 catches, 44.5 yards -> 4 catches for 45 = 11.25 a catch
    d = RS.catch_yards_read(3.5, 44.5, season_rec=14, season_yds=190, model_ypc=12.0, longest_line=17.5)
    assert (d["c_min"], d["y_min"], d["long_min"]) == (4, 45, 18)
    assert d["need_ypc"] == pytest.approx(11.25)
    assert d["season_ypc"] == pytest.approx(190 / 14)
    assert d["mid_ypc"] == pytest.approx(44.5 / 3.5)
    assert d["read"] == "about even", "the lines ask 12.7 a catch; he gets 13.6, inside the 1-yard band"
    assert d["long_share"] == pytest.approx(18 / 45)
    assert d["rest_ypc"] == pytest.approx((45 - 18) / 3)
    s = RS.catch_yards_sentence(d)
    assert "ask 12.7 yards a catch (44.5 over 3.5)" in s and "4 catches for 45 yards -- need 11.2" in s
    assert "one catch of 18" in s and "other 3 catches need 9.0 each" in s


def test_the_lines_yards_a_catch_is_read_against_ours():
    d = RS.catch_yards_read(3.5, 44.5, season_rec=15, season_yds=172)     # Vele, no model figure: his season
    assert d["ref"] == "season" and d["read"] == "yards line rich"
    assert "his yards Over still needs an extra catch or a long play" in RS.catch_yards_sentence(d)
    # London: 18.3 a catch on 15 catches, mostly with the old QB; ours is 13.4 and the lines ask 14.6
    d = RS.catch_yards_read(5.5, 80.5, season_rec=15, season_yds=275, model_ypc=13.4)
    assert d["ref"] == "model" and d["read"] == "yards line rich", \
        "ours carries the verdict; a raw season figure on 15 catches is noise at this band"
    s = RS.catch_yards_sentence(d)
    assert "we expect 13.4 from him, he has 18.3 this season on 15 catches" in s
    d = RS.catch_yards_read(5.5, 60.5, model_ypc=13.4)
    assert d["read"] == "yards line lean" and "the yards line usually comes with it" in RS.catch_yards_sentence(d)
    assert RS.catch_yards_read(4.5, 49.5, model_ypc=11.5)["read"] == "about even"
    s = RS.catch_yards_sentence(RS.catch_yards_read(1.5, 19.5, longest_line=12.5))
    assert "his other catch needs 7.0" in s, "one remaining catch reads in the singular"


def test_a_longest_line_at_or_above_the_yards_line_reads_as_one_catch():
    d = RS.catch_yards_read(1.5, 12.5, longest_line=13.5)
    assert d["rest_ypc"] is None
    assert "one catch carrying all of his yards" in RS.catch_yards_sentence(d)
    assert "108%" not in RS.catch_yards_sentence(d)


def test_the_read_degrades_without_its_inputs():
    assert RS.catch_yards_read(3.5, None) is None
    d = RS.catch_yards_read(3.5, 44.5, season_rec=5, season_yds=90)
    assert d["season_ypc"] is None and d["read"] is None, "five catches is too few to call his yards a catch"
    d = RS.catch_yards_read(3.5, 44.5, season_rec=5, season_yds=90, model_ypc=12.0)
    assert d["read"] == "about even" and "That is about ours" in RS.catch_yards_sentence(d)
    d = RS.catch_yards_read(None, 44.5, longest_line=19.5)
    assert d["need_ypc"] is None and d["rest_ypc"] is None and d["long_min"] == 20
    assert RS.catch_yards_sentence(d).startswith("The longest-catch line (19.5)")
    assert RS.catch_yards_sentence(RS.catch_yards_read(None, 44.5)) is None


def test_extra_lines_come_from_sleeper_for_this_game_only():
    opt = lambda team, out, v, mult=None, status="active", game="pre_game": {
        "subject_team": team, "outcome": out, "outcome_value": v, "status": status, "game_status": game,
        **({"payout_multiplier": mult} if mult else {})}
    mk = [
        {"sport": "nfl", "wager_type": "longest_reception", "subject_id": "1",
         "options": [opt("NO", "over", 19.5), opt("NO", "under", 19.5)]},
        {"sport": "nfl", "wager_type": "rushing_attempts", "subject_id": "5",
         "options": [opt("ATL", "over", 19.5, "1.87"), opt("ATL", "under", 19.5, "1.70")]},
        {"sport": "nfl", "wager_type": "longest_reception", "subject_id": "2", "line_type": "goblin",
         "options": [opt("NO", "over", 9.5)]},                                  # not a normal line
        {"sport": "nfl", "wager_type": "longest_reception", "subject_id": "3",
         "options": [opt("DAL", "over", 22.5)]},                                # another game
        {"sport": "nfl", "wager_type": "receptions", "subject_id": "1",
         "options": [opt("NO", "over", 3.5)]},                                  # a priced market
        {"sport": "nfl", "wager_type": "longest_reception", "subject_id": "4",
         "options": [opt("ATL", "over", 26.5, game="in_progress")]},            # kicked off
    ]
    players = {"1": {"full_name": "Devaughn Vele"}, "2": {"full_name": "Bryce Lance"},
               "3": {"full_name": "CeeDee Lamb"}, "4": {"first_name": "Drake", "last_name": "London"},
               "5": {"full_name": "Bijan Robinson"}}
    got = RS.extra_lines(mk, players, {"NO", "ATL"})
    assert got == [
        {"name": "Devaughn Vele", "team": "NO", "kind": "longest_reception", "line": 19.5,
         "mult_over": None, "mult_under": None},
        {"name": "Bijan Robinson", "team": "ATL", "kind": "rushing_attempts", "line": 19.5,
         "mult_over": 1.87, "mult_under": 1.70}]
    assert RS.favoured(1.87, 1.70) == "Under" and RS.favoured(1.70, 1.87) == "Over"
    assert RS.favoured(1.78, 1.78) is None and RS.favoured(1.80, None) is None


def test_carries_and_yards_lines_read_together():
    # Bijan Robinson, ATL week 4: 19.5 carries (Under favoured), 89.5 yards, longest run 17.5;
    # 349 yards on 66 carries this season, 55 of them on one run
    d = RS.carry_yards_read(19.5, 89.5, model_ypc=5.3, proj_carries=17.5, season_car=66, season_yds=349,
                            longest_line=17.5, carries_fav="Under")
    assert (d["c_min"], d["y_min"], d["long_min"]) == (20, 90, 18)
    assert d["mid_ypc"] == pytest.approx(89.5 / 19.5) and d["need_ypc"] == pytest.approx(4.5)
    assert d["read"] == "yards line lean", "4.6 asked against our 5.3 is past the half-yard band"
    assert d["rest_ypc"] == pytest.approx((90 - 18) / 19)
    s = RS.carry_yards_sentence(d)
    assert s.startswith("The book's carries line is 19.5, Under favoured; we project 17.5.")
    assert "5.3 this season on 66 carries (mostly noise this early" in s and "mostly a bet on the carries" in s
    assert "one run of 18, 20% of the 90 yards; with that one, his other 19 carries need 3.8 each" in s


def test_the_carries_read_degrades_without_its_inputs():
    assert RS.carry_yards_read(11.5, None) is None
    d = RS.carry_yards_read(11.5, 36.5, model_ypc=3.4, season_car=8, season_yds=30)
    assert d["season_ypc"] is None, "8 carries is too few to quote a season yards a carry"
    k = RS.carry_yards_read(11.5, 36.5, model_ypc=3.4, season_car=18, season_yds=51)
    assert "he has 2.8 this season on 18 carries (mostly noise" in RS.carry_yards_sentence(k), \
        "Kamara's own number shows, with its count, though it carries no verdict"
    assert d["read"] == "about even" and d["carries_fav"] is None
    assert "Under favoured" not in RS.carry_yards_sentence(d) and "we project" not in RS.carry_yards_sentence(d)
    d = RS.carry_yards_read(None, 29.5, longest_line=14.5)
    assert d["need_ypc"] is None and RS.carry_yards_sentence(d).startswith("The longest-run line (14.5)")
    assert RS.carry_yards_sentence(RS.carry_yards_read(None, 29.5)) is None
    assert RS.carry_yards_read(9.5, 29.5, model_ypc=2.5)["read"] == "yards line rich"



def test_extra_lines_are_indexed_by_our_team_code():
    rows = [{"name": "Puka Nacua", "team": "LAR", "kind": "longest_reception", "line": 24.5},
            {"name": "Bijan Robinson", "team": "ATL", "kind": "rushing_attempts", "line": 19.5}]
    ix = RS.extra_index(rows, {"LA": "LAR"})
    assert ix[("longest_reception", M.norm_name("Puka Nacua"), "LA")]["line"] == 24.5, "Sleeper's LAR is our LA"
    assert ix[("rushing_attempts", M.norm_name("Bijan Robinson"), "ATL")]["line"] == 19.5
    assert RS.extra_summary(rows) == "longest catch 1, carries 1"
    assert RS.extra_summary([]) == "none posted for this game"



def test_the_season_yards_a_catch_is_shown_capped():
    # London: 274 yards on 15 catches, 220 once each catch is capped (made-up capped total)
    lk = {"cap": 41.0, "own": True, "n": 52, "games": 10}
    d = RS.catch_yards_read(6.5, 81.5, season_rec=15, season_yds=274, model_ypc=13.4, luckfree_ypc=220 / 15, luck=lk)
    assert d["season_ypc_luckfree"] == pytest.approx(220 / 15)
    assert "he has 18.3 this season on 15 catches, 14.7 luck-free over his last 10 games" in RS.catch_yards_sentence(d)
    assert d["read"] == "about even", "context only: the verdict still compares the lines with ours"
    assert RS.catch_yards_read(6.5, 81.5, season_rec=5, season_yds=90, luckfree_ypc=16.0)["season_ypc_luckfree"] == 16.0, \
        "the 10-game window decides the luck-free rate, not this season's count"



def test_the_gauge_compares_the_volume_the_line_takes_with_ours():
    # Bijan: 349 yards on 66 carries, 323 once his 55-yarder counts as 29; 90 yards takes 18.4
    d = RS.carry_yards_read(19.5, 89.5, model_ypc=5.3, proj_carries=17.5, season_car=66, season_yds=349,
                            luckfree_ypc=323 / 66)
    assert d["gauge"]["need"] == pytest.approx(90 / (323 / 66))
    s = RS.carry_yards_sentence(d)
    assert "90 yards takes about 18.4 carries; we project 17.5 (our volume), about what it takes." in s
    assert "The book's own carries line is 19.5: the yards line takes less than the book's own volume." in s
    lk = {"cap": 31.0, "own": True, "n": 183, "games": 10}
    d = RS.carry_yards_read(None, 29.5, model_ypc=4.5, proj_carries=9.1, season_car=30, season_yds=132,
                            luckfree_ypc=132 / 30, luck=lk)
    assert ("At 4.4 yards a carry with the luck taken out (every run past 31 yards, his own 97.5th percentile "
            "over his last 10 games with a run (183 runs), counted as 31), 30 yards takes") in RS.carry_yards_sentence(d), \
        "with no carries line the gauge still names the cap it used"
    d = RS.carry_yards_read(None, 36.5, model_ypc=2.5, proj_carries=11.8)
    assert "fewer than it takes: the Over needs more carries or a long run." in RS.carry_yards_sentence(d)
    d = RS.carry_yards_read(None, 29.5, model_ypc=4.5, proj_carries=9.1)
    assert "comfortably more than it takes" in RS.carry_yards_sentence(d)
    assert "his usual game clears it" not in RS.carry_yards_sentence(d), "an average game is not a usual game"
    # a low-volume receiver gets the warning
    d = RS.catch_yards_read(1.5, 19.5, model_ypc=13.4, proj_catches=2.2)
    s = RS.catch_yards_sentence(d)
    assert "20 yards takes about 1.5 catches; we project 2.2" in s and "one catch either way decides it" in s
    assert RS.volume_gauge(45, 11.5, None, "catches", 3.0) is None



def test_the_luck_line_is_the_players_own_97_5th_percentile_play():
    plays = list(range(1, 101))                       # 100 plays of 1..100 yards
    lk = RS.player_luck_line(plays)
    assert lk["own"] and lk["n"] == 100 and lk["cap"] == pytest.approx(np.percentile(plays, 97.5))
    few = RS.player_luck_line([5, 8, 55])
    assert few == {"cap": None, "own": False, "n": 3}, "too few plays: no percentile"
    assert RS.luck_free_rate([5, 8, 55], few) == pytest.approx(6.5), "too few: his longest play left out"
    assert RS.luck_free_rate([5, 8, 120], lk) == pytest.approx((5 + 8 + np.percentile(plays, 97.5)) / 3)
    assert RS.luck_free_rate([9], few) is None and RS.luck_free_rate([], lk) is None
    assert RS.luck_words(dict(lk, games=10), "run") == \
        "every run past 98 yards, his own 97.5th percentile over his last 10 games with a run (100 runs), counted as 98"
    assert RS.luck_words(dict(few, games=2), "run") == \
        "his longest run left out -- only 3 runs in his last 2 games with a run, too few for a percentile"
    assert RS.player_luck_line(list(range(1, 21)))["own"], "20 plays of his own is enough"
    assert not RS.player_luck_line(list(range(1, 20)))["own"], "19 is too few"
    assert RS.luck_words(None, "run") == ""



def test_the_luck_free_check_reads_his_last_10_games():
    # last season's final 9 games (3 runs each), then this season's 3 games
    prior = {("00-001", "run"): [[float(g), 2.0, 3.0] for g in range(1, 10)]}
    cur = {"00-001": [[4.0, 6.0], [60.0, 1.0], [5.0]]}
    luck, rate = RS.luck_for(prior, cur, "00-001", "run")
    # the window is the last 10 games: prior games 3..9 (7 games) + this season's 3
    plays = [y for g in prior[("00-001", "run")][-7:] for y in g] + [4.0, 6.0, 60.0, 1.0, 5.0]
    assert luck["games"] == 10 and luck["n"] == len(plays) == 26 and luck["own"]
    assert luck["cap"] == pytest.approx(np.percentile(plays, 97.5))
    assert rate == pytest.approx(sum(min(y, luck["cap"]) for y in plays) / len(plays)), "rate: the same 10 games"
    # too few plays in the window: his longest left out; under 10 carries: no rate
    luck, rate = RS.luck_for({}, {"00-002": [[3.0, 4.0, 30.0], [2.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0]]},
                             "00-002", "run")
    assert not luck["own"] and luck["games"] == 2
    assert rate == pytest.approx((3 + 4 + 30 + 2 + 5 + 6 + 7 + 8 + 9 + 10 + 11 - 30) / 10)
    assert RS.luck_for({}, {"00-003": [[3.0, 9.0]]}, "00-003", "catch")[1] is None, "2 catches: too few for a rate"
    assert RS.luck_for({}, {}, "00-999", "run") == ({"cap": None, "own": False, "n": 0, "games": 0}, None)


def test_last_seasons_games_round_trip_through_the_resource():
    import pandas as pd
    import build_play_yards as BPY
    pbp = pd.DataFrame({"season_type": "REG", "week": [1, 1, 2, 3], "play_type": "run", "qb_kneel": 0,
                        "complete_pass": None, "receiver_player_id": None, "rusher_player_id": "00-001",
                        "receiving_yards": None, "rushing_yards": [3.0, 12.0, 5.0, -2.0]})
    out = BPY.play_yards(pbp, last_games=2)
    row = out[out.kind == "run"].iloc[0]
    assert row.games == "2:5;3:-2" and row.n == 2, "the last 2 games, oldest first"
    assert BPY.parse_games(row.games) == [[5.0], [-2.0]]



def test_the_gauge_says_whose_volume_each_number_is():
    d = RS.carry_yards_read(19.5, 89.5, model_ypc=4.4, proj_carries=17.5, carries_fav="Under")
    s = RS.carry_yards_sentence(d)
    assert "we project 17.5 (our volume)" in s
    assert "The book's own carries line is 19.5, Under favoured: fewer than the yards line takes" in s
    d = RS.carry_yards_read(None, 29.5, model_ypc=4.3, proj_carries=9.1)
    assert "The book posts no carries line for him, so this is against our volume only." in RS.carry_yards_sentence(d)
    d = RS.catch_yards_read(6.5, 81.5, model_ypc=16.4, proj_catches=5.8)
    assert "The book's own catches line is 6.5: the yards line takes less than the book's own volume." \
        in RS.catch_yards_sentence(d)



def test_fantasy_points_allowed_by_position():
    import pandas as pd
    pbp = pd.DataFrame([
        # ATL defence, game 1: a WR catch for 20 and a TD (1 + 2 + 6), an RB run for 30 (3)
        dict(game_id="g1", defteam="ATL", play_type="pass", complete_pass=1, receiver_player_id="wr1",
             rusher_player_id=None, receiving_yards=20, rushing_yards=None, pass_touchdown=1, rush_touchdown=0, qb_kneel=0),
        dict(game_id="g1", defteam="ATL", play_type="run", complete_pass=None, receiver_player_id=None,
             rusher_player_id="rb1", receiving_yards=None, rushing_yards=30, pass_touchdown=0, rush_touchdown=0, qb_kneel=0),
        # a QB kneel and a QB run: not counted
        dict(game_id="g1", defteam="ATL", play_type="run", complete_pass=None, receiver_player_id=None,
             rusher_player_id="qb1", receiving_yards=None, rushing_yards=-1, pass_touchdown=0, rush_touchdown=0, qb_kneel=1),
        # ATL game 2: an incomplete pass to the TE (0) and a FB catch for 5 (1.5, counts as RB)
        dict(game_id="g2", defteam="ATL", play_type="pass", complete_pass=0, receiver_player_id="te1",
             rusher_player_id=None, receiving_yards=0, rushing_yards=None, pass_touchdown=0, rush_touchdown=0, qb_kneel=0),
        dict(game_id="g2", defteam="ATL", play_type="pass", complete_pass=1, receiver_player_id="fb1",
             rusher_player_id=None, receiving_yards=5, rushing_yards=None, pass_touchdown=0, rush_touchdown=0, qb_kneel=0),
        # NO defence, one game: a TE catch for 10 (2)
        dict(game_id="g3", defteam="NO", play_type="pass", complete_pass=1, receiver_player_id="te1",
             rusher_player_id=None, receiving_yards=10, rushing_yards=None, pass_touchdown=0, rush_touchdown=0, qb_kneel=0),
    ])
    pos = {"wr1": "WR", "rb1": "RB", "qb1": "QB", "te1": "TE", "fb1": "FB"}
    pa = RS.points_allowed(pbp, pos)
    assert pa["_games"] == {"ATL": 2, "NO": 1}
    assert pa["ATL"]["WR"][0] == pytest.approx(9.0 / 2) and pa["ATL"]["RB"][0] == pytest.approx((3 + 1.5) / 2)
    assert pa["ATL"]["TE"][0] == 0.0 and pa["NO"]["TE"] == (pytest.approx(2.0), 1)
    assert pa["ATL"]["RB"][1] == 1 and pa["NO"]["RB"][1] == 2, "rank 1 = most allowed"
    line = RS.points_allowed_line(pa, ("ATL", "NO"))
    assert line.startswith("ATL's defence allows RB 2.2 (1st most of 2") and "League average: RB 1.1" in line
    assert RS.matchup_sentence(pa, "NO", "TE").startswith("NO allows 2.0 PPR points a game to tight ends, the 1st most of 2")
    assert "the 1st fewest of 2" in RS.matchup_sentence(pa, "NO", "RB"), "the bottom half counts from the bottom"
    assert RS.matchup_sentence(pa, "ATL", "FB").startswith("ATL allows 2.2 PPR points a game to running backs")
    assert RS.matchup_sentence(pa, "ATL", "QB") is None and RS.matchup_sentence(pa, "DAL", "WR") is None
    assert "context, not an adjustment" in line
    assert RS.points_allowed_line(pa, ("ATL", "DAL")) is None and RS.points_allowed(None, pos) == {}



def test_this_seasons_games_come_oldest_week_first():
    import pandas as pd
    df = pd.DataFrame({"week": [3, 1, 3, 2, 1], "pid": ["a", "a", "a", None, "b"], "y": [10.0, 4.0, None, 7.0, 2.0]})
    assert RS.games_by_player(df, "pid", "y") == {"a": [[4.0], [10.0]], "b": [[2.0]]}


def test_points_allowed_notes_players_without_a_position():
    import pandas as pd
    row = lambda pid, yds: dict(game_id="g1", defteam="ATL", play_type="pass", complete_pass=1, receiver_player_id=pid,
                                rusher_player_id=None, receiving_yards=yds, rushing_yards=None, pass_touchdown=0,
                                rush_touchdown=0, qb_kneel=0)
    pa = RS.points_allowed(pd.DataFrame([row("wr1", 50), row("ghost", 50)]), {"wr1": "WR"})
    assert pa["_unmapped_share"] == pytest.approx(0.5)
    pa["NO"], pa["_games"]["NO"] = pa["ATL"], 1
    assert "belong to players the roster file gives no position" in RS.points_allowed_line(pa, ("ATL", "NO"))


def test_the_quarterback_read_uses_completions():
    lk = {"cap": 41.0, "own": True, "n": 210, "games": 10}
    d = RS.qb_yards_read(completions_line=22.5, yards_line=259.5, proj_completions=20.1, model_ypc=11.9,
                         luck=lk, luckfree_ypc=10.8, longest_line=34.5, completions_fav="Under", attempts_line=35.5)
    assert d["gauge"]["need"] == pytest.approx(260 / 10.8)
    s = RS.qb_yards_sentence(d)
    assert s.startswith("The book's completions line is 22.5, Under favoured (attempts 35.5); we project 20.1.")
    assert "The lines ask 11.5 yards a completion (259.5 over 22.5); we expect 11.9, 10.8 luck-free over his last 10 games." in s
    assert ("every completion past 41 yards, his own 97.5th percentile over his last 10 games with a completion "
            "(210 completions), counted as 41") in s
    assert "260 yards takes about 24.1 completions; we project 20.1 (our volume), fewer than it takes" in s
    assert "The book's own completions line is 22.5, Under favoured: fewer than the yards line takes" in s
    assert "The longest-completion line (34.5) means one completion of 35, 13% of the 260 yards." in s
    assert RS.qb_yards_read(22.5, None) is None
    bare = RS.qb_yards_read(yards_line=225.5, proj_completions=19.0, model_ypc=11.0)
    assert "(our figure for him)" in RS.qb_yards_sentence(bare)


def test_the_resource_holds_a_quarterbacks_completions():
    import pandas as pd
    import build_play_yards as BPY
    pbp = pd.DataFrame({"season_type": "REG", "week": [1, 1, 2], "play_type": "pass", "qb_kneel": 0,
                        "complete_pass": [1, 0, 1], "receiver_player_id": ["wr", "wr", "te"], "rusher_player_id": None,
                        "receiving_yards": [12.0, None, 30.0], "rushing_yards": None, "passer_player_id": "qb"})
    out = BPY.play_yards(pbp)
    assert out[(out.gsis_id == "qb") & (out.kind == "pass")].iloc[0].games == "1:12;2:30"



def test_projected_completions_match_the_simulated_mean():
    rng = np.random.default_rng(7)
    rec = [rng.poisson(5.0, 20000).astype(float), rng.poisson(3.0, 20000).astype(float)]
    other = rng.poisson(6.0, 20000)
    share = [0.85, 0.95, 1.0]
    sim = M.simulate_qb_completions(np.random.default_rng(8), 20000, rec, other, {"catch_rate": 0.6},
                                    starter_share=share)
    proj = RS.projected_completions([r.mean() for r in rec], other.mean(), 0.6, np.mean(share))
    assert proj == pytest.approx(float(np.mean(sim)), rel=0.02), "the mean of the draw the model makes"
    assert RS.projected_completions([5.0], None, None, 1.0) == 5.0


def test_a_quarterbacks_cameo_games_stay_out_of_his_window():
    prior = {("qb", "pass"): [[10.0] * 3, [8.0] * 20]}          # a 3-completion cameo, then a start
    luck, rate = RS.luck_for(prior, {"qb": [[12.0] * 22]}, "qb", "pass")
    assert luck["games"] == 2 and luck["n"] == 42, "the cameo is left out"


def test_the_quarterback_read_says_whether_the_yards_line_asks_more():
    d = RS.qb_yards_read(completions_line=23.5, yards_line=260.5, proj_completions=23.1, model_ypc=10.0)
    assert d["read"] == "yards line rich" and "needs extra completions or a long one" in RS.qb_yards_sentence(d)



def test_the_books_coin_flip_volume():
    # Bijan, week 4: 19.5 carries, Over 1.87x / Under 1.70x -> a fair 47.6% Over
    p = RS.fair_over(1.87, 1.70)
    assert p == pytest.approx((1 / 1.87) / (1 / 1.87 + 1 / 1.70))
    assert RS.fair_volume(19.5, p, 4.5) == pytest.approx(19.23, abs=0.02)
    assert RS.fair_volume(5.5, RS.fair_over(price_over=-182, price_under=107), 2.0) > 5.5, "a favoured Over sits above"
    assert RS.fair_volume(19.5, None, 4.5) is None and RS.fair_over(None, None) is None
    d = dict(RS.carry_yards_read(19.5, 89.5, model_ypc=4.9, proj_carries=17.5, carries_fav="Under"), book_fair=19.2)
    assert "The book's own carries line is 19.5, Under favoured (a coin flip at about 19.2)" in RS.carry_yards_sentence(d)


def test_team_volume_against_our_projection():
    import pandas as pd
    def play(week, pos, typ, **kw):
        base = dict(week=week, posteam=pos, home_team="DAL", away_team="NYG", home_score=20, away_score=28,
                    play_type=typ, sack=0, pass_attempt=0, qb_scramble=0, qb_kneel=0, receiver_player_id=None,
                    passer_player_name=None, score_differential=0)
        base.update(kw)
        return base
    rows = ([play(1, "DAL", "pass", pass_attempt=1, receiver_player_id="w", passer_player_name="D.Prescott")] * 30
            + [play(1, "DAL", "pass", pass_attempt=1, passer_player_name="D.Prescott")] * 2          # throwaways
            + [play(1, "DAL", "pass", pass_attempt=1, sack=1)] * 3                                  # sacks
            + [play(1, "DAL", "run")] * 20 + [play(1, "DAL", "run", qb_scramble=1)] * 2
            + [play(1, "DAL", "run", qb_kneel=1)] * 3 + [play(1, "NYG", "run")] * 25)
    tv = RS.team_volume(pd.DataFrame(rows), "DAL")
    keep = {k: v for k, v in tv[0].items() if k not in ("state", "lead_share", "trail_share")}
    assert keep == {"week": 1, "opp": "vs NYG", "score": "20-28", "margin": -8.0, "att": 32, "sacks": 3,
                    "carries": 20, "scrambles": 2, "targets": 30, "qb": "D.Prescott"}
    assert tv[0]["state"]["close"] == {"plays": 57, "att": 32, "runs": 22} and tv[0]["lead_share"] == 0.0
    chk = RS.team_volume_check(tv, our_targets=30.0, our_runs=22.0)
    assert chk["our_att"] == pytest.approx(32.0) and chk["att_inside"] and chk["runs_inside"]
    assert "Both sit inside the range of its games this season." in " ".join(RS.team_volume_lines("DAL", tv, chk))
    chk = RS.team_volume_check(tv, our_targets=40.0, our_runs=30.0)
    assert "sit outside every game this season" in " ".join(RS.team_volume_lines("DAL", tv, chk))
    assert RS.team_volume(None, "DAL") == [] and RS.team_volume_lines("DAL", [], None) == []



def test_the_script_vegas_expects_sets_the_pass_share():
    rows = [{"att": 30, "carries": 20, "scrambles": 2, "targets": 28, "score": "", "week": 1, "opp": "", "sacks": 0,
             "qb": "", "state": {"lead": {"plays": 40, "att": 14, "runs": 26}, "close": {"plays": 60, "att": 33, "runs": 27},
                                 "trail": {"plays": 20, "att": 14, "runs": 6}}}]
    sr = RS.script_rates(rows)
    assert sr["lead"][0] == pytest.approx(14 / 40) and sr["trail"][2] == 20
    assert RS.expected_state(-9.5) == "lead" and RS.expected_state(9.5) == "trail" and RS.expected_state(-1.5) == "close"
    league = {"lead": 0.45, "close": 0.56, "trail": 0.63}
    mix = {"big favourite": {"lead": 0.4, "close": 0.5, "trail": 0.1}}
    chk = RS.team_volume_check(rows, our_targets=28.0, our_runs=22.0, team_spread=-9.5, league=league, mix=mix)
    plays = 30.0 + 22.0
    sh = {"lead": (14 + 60 * 0.45) / (40 + 60), "close": (33 + 60 * 0.56) / (60 + 60), "trail": (14 + 60 * 0.63) / (20 + 60)}
    share = 0.4 * sh["lead"] + 0.5 * sh["close"] + 0.1 * sh["trail"]
    assert chk["state"] == "lead" and chk["script_att"] == pytest.approx(plays * share)
    text = " ".join(RS.team_volume_lines("DAL", rows, chk))
    assert "Teams playing as a favourite by 7+ spent their plays 40% ahead by 8+, 50% within one score" in text
    assert "ahead by 8+ 35% (40 plays)" in text
    far = RS.team_volume_check(rows, our_targets=28.0, our_runs=22.0, team_spread=-9.5,
                               league={"lead": 0.05, "close": 0.05, "trail": 0.05}, mix=mix)
    assert not far["script_inside"] and "read it as the direction the script pushes" in " ".join(
        RS.team_volume_lines("DAL", rows, far))
    assert RS.blended_share(14, 26, None) == pytest.approx(14 / 40)



def test_league_script_shares():
    import pandas as pd
    df = pd.DataFrame({"posteam": ["A", "A", "A", "B"], "play_type": ["pass", "run", "pass", "run"],
                       "pass_attempt": [1, 0, 1, 0], "sack": [0, 0, 1, 0], "qb_scramble": [0, 0, 0, 0],
                       "qb_kneel": [0, 0, 0, 0], "score_differential": [10, 10, 0, -9]})
    lg = RS.league_script_shares(df)
    assert lg == {"lead": 0.5, "trail": 0.0}, "the sack is not an attempt; no close plays but the sack"



def test_league_state_mix_by_pregame_line():
    import pandas as pd
    # home team H favoured by 7 (spread_line +7): H's plays 2 ahead, 1 close; road team R's 1 behind, 1 close
    df = pd.DataFrame({"posteam": ["H", "H", "H", "R", "R"], "home_team": "H", "play_type": "pass",
                       "qb_kneel": 0, "spread_line": 7.0, "score_differential": [10, 9, 0, -10, 3]})
    mix = RS.league_state_mix(df)
    assert mix["big favourite"] == {"lead": pytest.approx(2 / 3), "close": pytest.approx(1 / 3), "trail": 0.0}
    assert mix["big underdog"] == {"lead": 0.0, "close": 0.5, "trail": 0.5}
    assert RS.line_bucket(-9.5) == "big favourite" and RS.line_bucket(4) == "underdog" and RS.line_bucket(1.5) == "close"



def test_the_team_line_sign_and_the_mix_fallback():
    assert RS.team_line(-9.5, True) == -9.5 and RS.team_line(-9.5, False) == 9.5, "DAL -9.5 at home: TB is +9.5"
    assert RS.line_bucket(RS.team_line(-9.5, True)) == "big favourite"
    assert RS.line_bucket(RS.team_line(-9.5, False)) == "big underdog"
    assert RS.team_line(None, True) is None
    rows = [{"att": 30, "carries": 20, "scrambles": 2, "targets": 28, "score": "", "week": 1, "opp": "", "sacks": 0,
             "qb": "", "state": {"lead": {"plays": 40, "att": 14, "runs": 26}, "close": {"plays": 60, "att": 33, "runs": 27},
                                 "trail": {"plays": 20, "att": 14, "runs": 6}}}]
    league = {"lead": 0.45, "close": 0.56, "trail": 0.63}
    chk = RS.team_volume_check(rows, 28.0, 22.0, team_spread=-9.5, league=league,
                               mix={"_all": {"lead": 0.2, "close": 0.6, "trail": 0.2}})
    assert chk["line_bucket"] == "all lines" and chk["state_mix"] == {"lead": 0.2, "close": 0.6, "trail": 0.2}
    none = RS.team_volume_check(rows, 28.0, 22.0, team_spread=-9.5, league=league, mix={})
    assert none["script_att"] is None, "no mix at all: no script, never every snap in one state"


def test_spikes_are_not_pass_attempts():
    import pandas as pd
    base = dict(week=1, posteam="DAL", home_team="DAL", away_team="NYG", home_score=20, away_score=28, sack=0,
                qb_scramble=0, qb_kneel=0, receiver_player_id=None, passer_player_name="D.Prescott", score_differential=0)
    df = pd.DataFrame([dict(base, play_type="pass", pass_attempt=1, receiver_player_id="w"),
                       dict(base, play_type="qb_spike", pass_attempt=1)])
    assert RS.team_volume(df, "DAL")[0]["att"] == 1



def test_the_rushing_plus_receiving_read():
    d = RS.rush_rec_read(line=52.5, mult_over=1.70, mult_under=1.87, proj_carries=15.8, proj_catches=3.1,
                         run_rate=4.3, catch_rate=7.0, sd=24.0, book_carries=13.5, book_catches=2.5)
    assert d["fav"] == "Over" and d["coin"] > 52.5
    rate = (15.8 * 4.3 + 3.1 * 7.0) / 18.9
    assert d["touch_rate"] == pytest.approx(rate) and d["need"] == pytest.approx(53 / rate)
    assert d["air_share"] == pytest.approx(3.1 * 7.0 / (15.8 * 4.3 + 3.1 * 7.0))
    s = RS.rush_rec_sentence(d)
    assert s.startswith("The book's line is 52.5, Over favoured (a coin flip at about")
    assert "53 yards takes about" in s and "we project 18.9 (15.8 carries, 3.1 catches)" in s
    assert "The book's own carries and catches lines add to 16 touches." in s
    assert "if his team falls behind, that part holds up" in s
    assert "Our model gives the Over" not in s, "no model chance passed in: none claimed"
    priced = RS.rush_rec_sentence({**d, "p_model_over": 0.57})
    assert "Our model gives the Over 57%" in priced and "DECISIONS #187" in priced
    assert RS.rush_rec_read(None) is None
    bare = RS.rush_rec_read(line=40.5)
    assert RS.rush_rec_sentence(bare).startswith("The book's line is 40.5.")



def test_the_rushing_plus_receiving_read_names_whose_rate():
    d = RS.rush_rec_read(line=30.5, proj_carries=6.0, proj_catches=2.0, run_rate=3.9, catch_rate=6.5,
                         rates_luck_free=False)
    assert "At our yards a touch (too few of his own plays)" in RS.rush_rec_sentence(d)


def test_the_book_quarterback_flag_fires_only_when_the_book_skips_our_starter():
    """DECISIONS #181: the backtest graded the wrong QB in 27% of backup starts because a
    stale depth chart named an active primary; live, the book's own lines say who starts."""
    extra = [{"name": "Teddy Bridgewater", "team": "TB", "kind": "passing_attempts", "line": 30.5},
             {"name": "Teddy Bridgewater", "team": "TB", "kind": "pass_completions", "line": 19.5},
             {"name": "Dak Prescott", "team": "DAL", "kind": "passing_attempts", "line": 34.5},
             {"name": "Bucky Irving", "team": "TB", "kind": "rushing_attempts", "line": 14.5}]
    got = RS.book_qb_mismatch(extra, {"TB": "Baker Mayfield", "DAL": "Dak Prescott"})
    assert got == [{"team": "TB", "engine": "Baker Mayfield", "book": ["Teddy Bridgewater"]}]
    assert RS.book_qb_mismatch(extra, {"TB": "Teddy Bridgewater", "DAL": "Dak Prescott"}) == []
    assert RS.book_qb_mismatch([], {"TB": "Baker Mayfield"}) == [], "no QB lines posted: no claim"
    la = [{"name": "Matthew Stafford", "team": "LAR", "kind": "passing_attempts", "line": 33.5}]
    assert RS.book_qb_mismatch(la, {"LA": "Matthew Stafford"}, {"LA": "LAR"}) == [], "team codes mapped"
    py = [{"name": "Teddy Bridgewater", "team": "TB", "kind": "passing_yards"}]
    assert RS.book_qb_mismatch(py, {"TB": "Baker Mayfield"}) == [
        {"team": "TB", "engine": "Baker Mayfield", "book": ["Teddy Bridgewater"]}], "the passing-yards line counts"


def test_ordinals_read_like_english():
    assert [RS.ordinal(n) for n in (1, 2, 3, 4, 10, 11, 12, 13, 21, 22, 23, 32)] == [
        "1st", "2nd", "3rd", "4th", "10th", "11th", "12th", "13th", "21st", "22nd", "23rd", "32nd"]


def test_defence_epa_and_points_per_drive_allowed():
    """Known answers: ATL allows +0.5 and -0.1 EPA (kneel and spike out), one TD drive (7)
    and one empty drive -> 3.5 a drive; NO allows -0.2 EPA and a field goal (3)."""
    import pandas as pd
    def play(g, d, dr, typ, epa, s0, s1, kneel=0, spike=0, pos="X"):
        return dict(game_id=g, defteam=d, posteam=pos, fixed_drive=dr, play_type=typ, epa=epa,
                    posteam_score=s0, posteam_score_post=s1, qb_kneel=kneel, qb_spike=spike)
    pbp = pd.DataFrame([
        play("g1", "ATL", 1, "pass", 0.5, 0, 0), play("g1", "ATL", 1, "run", 0.3, 0, 7),
        play("g1", "ATL", 2, "run", -0.4, 7, 7), play("g1", "ATL", 2, "run", -5.0, 7, 7, kneel=1),
        play("g1", "ATL", 2, "pass", -3.0, 7, 7, spike=1),
        play("g2", "NO", 1, "pass", -0.2, 0, 3),
    ])
    dm = RS.defense_metrics(pbp)
    assert dm["ATL"]["epa_play"][0] == pytest.approx((0.5 + 0.3 - 0.4) / 3), "kneel-downs and spikes out"
    assert dm["ATL"]["epa_pass"][0] == pytest.approx(0.5) and dm["ATL"]["epa_rush"][0] == pytest.approx(-0.05)
    assert dm["ATL"]["pts_drive"] == (pytest.approx(3.5), 1) and dm["NO"]["pts_drive"] == (pytest.approx(3.0), 2)
    assert dm["ATL"]["epa_play"][1] == 1, "1st = most allowed"
    line = RS.defense_line(dm, ("ATL", "NO"))
    assert line.startswith("ATL allows +0.13 EPA a play (1st)") and "3.50 points a drive (1st)" in line
    assert "NO allows -0.20 EPA a play (2nd)" in line and "1st = most allowed" in line
    assert RS.defense_line(dm, ("ATL", "DAL")) is None
    assert RS.defense_metrics(pbp.drop(columns=["epa"])) == {}
    no_drives = RS.defense_metrics(pbp.drop(columns=["fixed_drive"]))
    assert "pts_drive" not in no_drives["ATL"] and "epa_play" in no_drives["ATL"], "EPA without drive columns"


def test_offence_epa_and_points_per_drive_gained():
    """The same plays by the team with the ball: X gains every play above (two drives in
    g1 -> 3.5 a drive, the kneel and spike out), Y the field goal."""
    import pandas as pd
    rows = [("g1", "ATL", "X", 1, "pass", 0.5, 0, 0, 0, 0), ("g1", "ATL", "X", 1, "run", 0.3, 0, 7, 0, 0),
            ("g1", "ATL", "X", 2, "run", -0.4, 7, 7, 0, 0), ("g1", "ATL", "X", 2, "run", -5.0, 7, 7, 1, 0),
            ("g2", "NO", "Y", 1, "pass", -0.2, 0, 3, 0, 0)]
    pbp = pd.DataFrame(rows, columns=["game_id", "defteam", "posteam", "fixed_drive", "play_type", "epa",
                                      "posteam_score", "posteam_score_post", "qb_kneel", "qb_spike"])
    om = RS.offense_metrics(pbp)
    assert om["X"]["epa_play"] == (pytest.approx(0.4 / 3), 1) and om["X"]["pts_drive"][0] == pytest.approx(3.5)
    assert om["Y"]["pts_drive"] == (pytest.approx(3.0), 2)
    line = RS.defense_line(om, ("X", "Y"), verb="gains")
    assert line.startswith("X gains +0.13 EPA a play (1st)") and "1st = most gained" in line


def test_rank_words_count_from_the_nearer_end():
    assert [RS.rank_words(r, 32) for r in (1, 10, 16, 17, 31, 32)] == [
        "1st most", "10th most", "16th most", "16th fewest", "2nd fewest", "1st fewest"]


def test_epa_uses_the_pass_and_rush_flags_so_a_scramble_is_a_dropback():
    import pandas as pd
    pbp = pd.DataFrame({"game_id": "g", "defteam": "ATL", "posteam": "X", "epa": [0.6, -0.2, 1.0],
                        "play_type": ["pass", "run", "run"], "pass": [1, 0, 1], "rush": [0, 1, 0],
                        "qb_scramble": [0, 0, 1]})
    dm = RS.defense_metrics(pbp)
    assert dm["ATL"]["epa_pass"][0] == pytest.approx(0.8), "the scramble is a dropback"
    assert dm["ATL"]["epa_rush"][0] == pytest.approx(-0.2)


def test_unit_efficiency_splits_dropbacks_and_runs_removes_garbage_time_and_ranks_by_side():
    """Matchup brief (user, 2026-10-06): A's two dropbacks (+0.5, -0.1) and run (+0.2); a
    garbage-time play (wp 0.97) and a kneel are left out; B allows them; pace from snaps on
    one drive in a neutral first quarter."""
    import pandas as pd
    rows = [dict(game_id="g", play_id=i, posteam="A", defteam="B", epa=e, **{"pass": ps, "rush": rs},
                 success=float(e > 0), wp=wp, qb_kneel=k, qb_spike=0, game_seconds_remaining=3600 - 30 * i,
                 qtr=1, score_differential=0, fixed_drive=1)
            for i, (e, ps, rs, wp, k) in enumerate([(0.5, 1, 0, 0.5, 0), (-0.1, 1, 0, 0.5, 0), (0.2, 0, 1, 0.5, 0),
                                                    (3.0, 1, 0, 0.97, 0), (-1.0, 0, 1, 0.5, 1)])]
    rows.append(dict(game_id="g", play_id=9, posteam="B", defteam="A", epa=-0.3, **{"pass": 1, "rush": 0},
                     success=0.0, wp=0.5, qb_kneel=0, qb_spike=0, game_seconds_remaining=1000, qtr=2,
                     score_differential=0, fixed_drive=2))
    ue = RS.unit_efficiency(pd.DataFrame(rows))
    a = ue["off"]["A"]["pass"]
    assert a[0] == pytest.approx(0.2) and a[2] == pytest.approx(0.5) and a[4] == 2, "garbage time out"
    assert ue["off"]["A"]["run"][4] == 1, "the kneel-down is out"
    assert ue["def"]["B"]["pass"][0] == pytest.approx(0.2) and ue["off"]["A"]["pass"][1] == 1
    assert ue["pace"]["A"][0] == pytest.approx(30.0), "30 seconds between snaps on one drive"
    assert RS.unit_table(ue, "A", "B") == [], "two teams: no league to score against"
    assert RS.unit_efficiency(pd.DataFrame(rows).drop(columns=["epa"])) == {}


def test_brief_tables_and_known_gaps_read_the_game_not_a_template():
    assert RS.market_table("TB", "DAL", -9.5, 47.5)[2:4] == ["| Spread | +9.5 | -9.5 |",
                                                             "| Implied team points | 19.0 | 28.5 |"]
    chk = {"TB": {"our_att": 33.2, "our_runs": 26.0, "att_avg": 31.5, "runs_avg": 24.2,
                  "rates": {"close": (57, 43, 100)}, "league": {"close": 0.56}}}
    ot = RS.outlook_table(chk, "TB", "DAL")
    assert ot[2] == "| TB | 33 | 26 | 31.5 / 24.2 | 57% |" and "56%" in ot[-1]
    g = RS.known_gaps({"qb_change": {"TB": "Daniels starts for Mayfield"}, "fav": "DAL", "spread": 9.5,
                       "new_team": ["Kenny Gainwell"], "has_pass_lines": True, "oline_out": {"TB": 1, "DAL": 2},
                       "wind_mph": 20, "roof": "closed"})
    names = [x[0] for x in g]
    assert names[0].startswith("TB's quarterback") and any(n.startswith("DAL's expected lead (9.5") for n in names)
    assert any("DAL offensive line (2 of 5" in n for n in names) and not any("TB offensive line" in n for n in names)
    assert not any(n.startswith("Wind") for n in names), "a closed roof: no wind gap"
    assert RS.known_gaps({"fav": "DAL", "spread": 3}) == [], "a 3-point line is not an expected lead"
    assert RS.known_gaps_table([])[0].startswith("No known gap")


def test_margin_flags_mark_thin_sides_at_our_projection():
    assert RS.margin_flags(20.0, 18.5, 16.0, "carries") == ["thin: the Over needs 18.5 carries, we project 20.0"]
    assert RS.margin_flags(24.0, 18.5, 16.0, "carries") == [], "a wide margin is not flagged"
    assert RS.margin_flags(15.0, 18.5, 15.8, "carries")[0].startswith("thin: the Under needs 15.8")
    assert RS.margin_flags(17.0, 18.5, 16.0) == [], "inside the cut: the break-even cell says it already"
    assert RS.margin_flags(None, 18.5, 16.0) == []



def test_the_unit_score_blends_epa_and_success_and_tiers_from_the_best_team_down():
    """User, 2026-10-06: one score per unit (EPA per play and success rate standardised and
    averaged, 50 = league average, 10 = one standard deviation, higher better for offences
    and defences alike), tiered in equal bands counted from the best team."""
    import pandas as pd
    rows, i = [], 0
    for k, team in enumerate("ABCDEFGHIJ"):
        for j in range(20):                     # team k: EPA +0.05k-0.2, success rises with k
            e = 0.05 * k - 0.2 + (0.3 if j % 2 else -0.3)
            rows.append(dict(game_id=f"g{k}", play_id=i, posteam=team, defteam="ABCDEFGHIJ"[(k + 1) % 10],
                             epa=e, success=float(j < 5 + k), **{"pass": 1, "rush": 0}, wp=0.5,
                             qb_kneel=0, qb_spike=0))
            i += 1
    ue = RS.unit_efficiency(pd.DataFrame(rows))
    off = ue["score"]["off"]["pass"]
    assert off["J"] > off["A"] and abs(sum(off.values()) / len(off) - 50) < 1e-9, "50 is the league average"
    d = ue["score"]["def"]["pass"]
    assert d["B"] > d["A"], "B faces the worst offence (A): allowing less scores higher"
    t = RS.tiers(off)
    assert t["tier"]["J"] == 1 and max(t["tier"].values()) == t["n"] <= RS.MAX_TIERS
    assert t["bands"][0][2] == pytest.approx(max(off.values())), "bands count down from the best team"
    assert all(b[2] - b[1] == pytest.approx(t["step"]) for b in t["bands"]), "equal-width bands"
    tab = RS.unit_table(ue, "A", "B")
    assert tab[0] == "| Matchup | Offence score | Offence tier | Defence faced: score | Defence tier |"
    assert any(r.startswith("| A pass vs. B | ") for r in tab) and any(r.startswith("| 1 (best) |") for r in tab)
    assert "50 is the league average" in " ".join(tab)


def test_tiers_narrow_for_a_tight_league_and_widen_for_a_spread_one():
    tight = RS.tiers({str(i): 50 + i for i in range(10)})          # spread 9
    wide = RS.tiers({str(i): 30 + 5 * i for i in range(10)})       # spread 45
    assert tight["step"] < wide["step"] and tight["n"] <= RS.MAX_TIERS and wide["n"] <= RS.MAX_TIERS
    low = RS.tiers({"a": 10.0, "b": 2.0}, higher_is_better=False)
    assert low["tier"] == {"a": low["n"], "b": 1}, "lower is better: the smaller value is tier 1"
