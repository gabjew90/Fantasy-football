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
    # London: 274 yards on 15 catches, 220 once each catch is capped at 30
    d = RS.catch_yards_read(6.5, 81.5, season_rec=15, season_yds=274, model_ypc=13.4, season_capped_yds=220)
    assert d["season_ypc_cap"] == pytest.approx(220 / 15)
    assert "he has 18.3 this season on 15 catches (14.7 with each catch capped at 30 yards)" in RS.catch_yards_sentence(d)
    assert d["read"] == "about even", "context only: the verdict still compares the lines with ours"
    assert RS.catch_yards_read(6.5, 81.5, season_rec=5, season_yds=90, season_capped_yds=80)["season_ypc_cap"] is None



def test_the_gauge_compares_the_volume_the_line_takes_with_ours():
    # Bijan: 349 yards on 66 carries, 323 once his 55-yarder counts as 29; 90 yards takes 18.4
    d = RS.carry_yards_read(19.5, 89.5, model_ypc=5.3, proj_carries=17.5, season_car=66, season_yds=349,
                            season_capped_yds=323)
    assert d["gauge"]["need"] == pytest.approx(90 / (323 / 66))
    s = RS.carry_yards_sentence(d)
    assert ("At his yards a carry with every run capped at 29 (4.9), 90 yards takes about 18.4 carries; "
            "we project 17.5, about what it takes.") in s
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
