"""The player card (user's "Player props section" draft, 2026-10-06): known-answer checks on
research.player_card and its tables."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "engine" / "scripts"))
import research as RS  # noqa: E402


def _row(market, line, **kw):
    r = {"market": market, "line": line, "price_over": -120, "price_under": 100, "median": 50.0, "p10": 20.0,
         "p90": 90.0, "p_over_model": 0.55, "p_over_book": 0.52, "p_push": None, "projected": 6.0,
         "implied": 5.5, "over_needs": 6.2, "under_needs": 5.1}
    r.update(kw)
    return r


USAGE = {"week": 4, "n_base": 3, "snap": 0.9, "snap_base": 0.8, "ts": 0.25, "ts_base": 0.2,
         "cs": 0.0, "cs_base": 0.0, "tn": 8.0, "tn_base": 6.3, "cn": 0.0, "cn_base": 0.0}


def test_prop_table_shows_the_push_on_a_whole_number_line_and_keeps_every_line():
    L = RS.prop_rows_table([_row("player_receptions", 5.0, p_push=0.18, p_over_model=0.41, median=5, p10=2, p90=8),
                            _row("player_receptions", 4.5)])
    assert L[2] == "| Receptions | 5 | -120 / +100 | 5; 2-8 catches | 41% (push 18%) / 52% |"
    assert "push" not in L[3] and len(L) == 4


def _vol(market, line, draws, rates, games=None, mvol=None, text=None):
    return {"market": market, "line": line, "volume_text": text,
            "cells": RS.volume_cells(market, line, draws, rates, games, mvol)}


def test_receiver_card_is_one_table_with_a_column_per_prop():
    d = {"name": "A Receiver", "team": "TB", "slot": "WR1", "pos": "WR", "book": "sleeper",
         "quoted": "2026-10-07 01:48 UTC",
         "rows": [_row("player_reception_yds", 68.5, p_over_book=0.50, p_over_model=0.48),
                  _row("player_receptions", 4.5, p_over_book=0.55, p_over_model=0.58)],
         "volume": [_vol("player_reception_yds", 68.5, list(range(1, 11)),
                         [("capped", "Last 10 games, long catches capped (7 from 2025, 3 from 2026; 51 catches)", 12.0),
                          ("season", "2026 so far, uncapped (3 games, longest catch 19)", 9.4),
                          ("engine", None, 13.8)], games=[(5, 80.0), (6, 40.0)], text="8.3 targets -> 5.5 catches"),
                    _vol("player_receptions", 4.5, [8] * 6 + [7] * 4, [("season", "2026 so far (3 games)", 0.64)],
                         text="8.3 targets")],
         "usage": USAGE, "qbs": (["B.Mayfield"], "J.Daniels"),
         "prior": {"ts": 0.23, "games": 17, "team": "TB", "new_team": False},
         "season": {"games": 4, "targets": 24, "catches": 15},
         "matchup": "DAL allows a lot.", "watch": ["Baker Mayfield (QB) out"]}
    L = RS.player_card(d)
    text = "\n".join(L)
    assert L[0] == "#### A Receiver · WR1, TB"
    # one column per prop, receptions before receiving yards whatever order the rows came in
    assert "| | Receptions 4.5 | Receiving yards 68.5 |" in text
    assert "| **Market's chance of the Over** | **55%** | **50%** |" in text
    assert "| Engine's chance | 58% | 48% |" in text
    assert "| The Over needs | 5 catches | 69 yards |" in text
    assert "| Engine's volume | 8.3 targets | 8.3 targets -> 5.5 catches |" in text
    # 69 yards at 12.0 a catch = 6 catches; P(>= 6) over 1..10 = 50%; receptions has no capped row
    assert "| At his luck-capped rate | - | 6 catches at 12.0 -> **50%** |" in text
    assert "| At his rate this season | 8 targets at 64% -> **60%** | 8 catches at 9.4 -> **30%** |" in text
    assert "| At the engine's rate | - | 5 catches at 13.8 -> **60%** |" in text
    assert "| His games this season that beat that | - | 1 of 2 |" in text
    # the windows are notes under the table, the calibration note with them
    assert ("*Receiving yards: luck-capped rate = last 10 games, long catches capped (7 from 2025, 3 from 2026; "
            "51 catches). rate this season = 2026 so far, uncapped (3 games, longest catch 19).") in text
    assert "catch counts are calibrated" in text
    assert "| Role evidence | Earlier games (3) | Last game (week 4) |" in text
    assert "| Quarterback who threw most | B.Mayfield | J.Daniels |" in text
    assert "Historical baseline: last season 23% of his team's targets over 17 games with TB." in text
    # gone from the card: the price workload, the capped-play line, the per-card calibration tables
    for gone in ("Workload check", "Capped-play check", "Live record at Sleeper", "Backtest calibration",
                 "How his lines fit together"):
        assert gone not in text, gone
    assert text.rstrip().endswith("**Watch:** Baker Mayfield (QB) out.")


def test_back_card_two_rate_column_and_the_markets_carries_line():
    d = {"name": "A Back", "team": "TB", "slot": "RB1", "pos": "RB",
         "rows": [_row("player_rush_yds", 52.5), _row("player_rush_reception_yds", 68.5)],
         "volume": [_vol("player_rush_yds", 52.5, [15] * 4 + [13] * 6, [("engine", None, 4.0)], mvol=13.5,
                         text="13.8 carries"),
                    _vol("player_rush_reception_yds", 68.5, ([14] * 5 + [12] * 5, [4] * 5 + [2] * 5),
                         [("engine", None, (4.0, 8.0))], text="13.0 carries + 3.0 catches")],
         "usage": {**USAGE, "cs": 0.52, "cs_base": 0.61, "cn": 16.0, "cn_base": 13.3},
         "shadow": [{"line": 52.5, "p_board": 0.55, "p_mkt": 0.53, "car_from": 14.8, "car_to": 14.3}]}
    text = "\n".join(RS.player_card(d))
    assert "| | Rushing yards 52.5 | Rushing + receiving yards 68.5 |" in text
    # 53 yards at 4.0 = 14 carries (13.25 up); P(>= 14) = 40%
    assert "14 carries at 4.0 -> **40%**" in text
    assert "| The market's own volume line | more than 13.5 carries -> 40% | - |" in text
    # 69 yards: 14*4 + 4*8 = 88 clears, 12*4 + 2*8 = 64 does not -> 50%
    # blended 4.75 a touch at the engine's 13 carries / 3 catches -> 15 touches, split 12 + 3
    assert "12 carries + 3 catches at 4.0 a carry, 8.0 a catch -> **50%**" in text
    assert "| Carries and share of team carries | 13.3 a game; 61% | 16; 52% |" in text
    assert "Over 55% on the board (his carries half from the market's script), 53% from history alone" in text


def test_qb_card_keeps_his_recent_workload_row():
    q = {"team_passes": 33.0, "games": [(3, 3, 0), (4, 27, 19)], "proj_cmp": 21.6, "cmp_line": 17.5,
         "att_line": 28.5, "att_fav": "Over", "gauge": {"need": 17.3}, "gauge_rate": 10.4, "luck_games": 1}
    d = {"name": "A Passer", "team": "TB", "slot": "QB1", "pos": "QB",
         "rows": [_row("player_pass_yds", 179.5)], "qb": q,
         "volume": [_vol("player_pass_yds", 179.5, [17] * 5 + [15] * 5, [("capped", "Last 10 games", 10.6)],
                         text="16.0 completions")]}
    text = "\n".join(RS.player_card(d))
    assert "| | Passing yards 179.5 |" in text and "17 completions at 10.6 -> **50%**" in text
    assert "| His recent workload | week 3: 3 attempts, 0 completions; week 4: 27 attempts, 19 completions |" in text
    assert "Role evidence" not in text
    three = RS.qb_table({**q, "games": [(1, 30, 20), (2, 34, 22), (3, 27, 19)]})
    assert "earlier games (2): 32.0 attempts, 21.0 completions a game; last game (week 3): 27 attempts, 19" in three[3]


def test_other_books_lines_get_their_own_small_table():
    d = {"name": "X", "team": "TB", "slot": "WR2", "pos": "WR",
         "rows": [_row("player_receptions", 4.5, book="sleeper"), _row("player_receptions", 5.5, book="draftkings")]}
    text = "\n".join(RS.player_card(d))
    assert "| | Receptions 4.5 |" in text and "Other lines for him:" in text
    assert "| Receptions | 5.5 |" in text


def test_the_calibration_block_prints_once_for_the_report():
    L = RS.calibration_block({"player_receptions", "player_reception_yds"}, {"DAL": 28.0, "HOU": 20.0},
                             ["TE1", "WR1", "WR2"])
    text = "\n".join(L)
    assert text.count("Live record at Sleeper's lines") == 1
    assert "| Receptions | 48.4% | 45.2% | 49.6% | 506 |" in text
    assert "| Receiving yards, DAL (implied 28.0: teams implied 27+) | 52.2% | 47.6% | 709 |" in text
    assert "| Receptions, every tight end | 49.0% | 44.1% | 1480 |" in text
    assert "| Receptions, every wide receiver | 45.1% | 44.3% | 4754 |" in text
    assert RS.calibration_block(set(), {}, []) == []


def test_too_few_games_and_missing_pieces_degrade_in_words():
    assert RS.role_table(None)[0].startswith("Role evidence: fewer than three games")
    assert RS.baseline_line(None, {"games": 0}) == ""
    assert RS.qb_table({"games": []})[3] == "| His recent workload | no starts this season |"
    assert RS.prop_table([], None) == ([], [])


def test_qb_workload_counts_attempts_not_sacks():
    import pandas as pd
    pbp = pd.DataFrame({"week": [1, 1, 1, 2], "passer_player_id": ["Q", "Q", "Q", "Q"],
                        "play_type": ["pass"] * 4, "sack": [0, 1, 0, 0], "pass_attempt": [1, 1, 1, 1],
                        "complete_pass": [1, 0, 0, 1]})
    assert RS.qb_workload(pbp, "Q") == [(1, 2, 1), (2, 1, 1)]
    assert RS.qb_workload(pbp, None) == []


def test_volume_cells_known_answers():
    # 68.5 needs 69 yards: at 13.1 a catch ceil(69/13.1) = 6 catches; at 9.4, 8 (7.3 rounds up)
    c = RS.volume_cells("player_reception_yds", 68.5, list(range(1, 11)),
                        [("capped", "L", 13.1), ("season", "S", 9.4), ("engine", None, None)],
                        games=[(5, 80.0), (6, 40.0), (0, 0.0)])
    assert c["rows"]["capped"]["vol"] == 6 and abs(c["rows"]["capped"]["pct"] - 0.5) < 1e-9
    assert c["rows"]["season"]["vol"] == 8 and abs(c["rows"]["season"]["pct"] - 0.3) < 1e-9
    assert "engine" not in c["rows"]                 # an assumption with no rate is left out
    # the engine's mean is 5.5 catches: the line needs 69/5.5 = 12.5 a catch; 16.0 beat it, 6.7 did not,
    # and the zero-catch game is not a game he could beat it in
    assert c["need_txt"] == "12.5 yards a catch" and c["beat"] == (1, 2)
    assert "catch counts are calibrated" in c["note"]
    # receptions: more catches than targets says so
    c = RS.volume_cells("player_receptions", 2.5, [2.0] * 10, [("season", None, 0.8)], games=[(3, 3.0)])
    assert c["need_txt"] == "3 catches: more than his targets" and c["beat"] is None
    # a whole-number rate lands exactly: 60 yards at 4.0 a carry is 15 carries, not 16
    c = RS.volume_cells("player_rush_yds", 59.5, [15] * 4 + [14] * 6, [("engine", None, 4.0)], market_volume=14.5)
    assert c["rows"]["engine"]["vol"] == 15 and c["market_row"] == (14.5, 0.4)
    assert "4-5 points" in c["note"]
    assert RS.volume_cells("player_rush_yds", None, [10], [("engine", None, 4.0)]) is None
    assert RS.volume_cells("player_rush_yds", 59.5, [], [("engine", None, 4.0)]) is None
    assert RS.volume_cells("player_rush_reception_yds", 60.5, ([1, 2], [1]), [("engine", None, (4.0, 8.0))]) is None


def test_the_capped_label_names_the_window_luck_for_used():
    # 4 games last season with a catch, 3 this season: the window holds all 7 (fewer than 10 -> says 7)
    prior = {("p1", "catch"): [[10.0, 12.0]] * 4}
    cur = {"p1": [[8.0], [9.0, 30.0], [5.0]]}
    luck, _rate = RS.luck_for(prior, cur, "p1", "catch")
    assert (luck["games"], luck["prior_games"], luck["cur_games"], luck["plays"]) == (7, 4, 3, 12)
    assert RS.capped_label(luck, "catches", "catches", 2025, 2026) == \
        "Last 7 games, long catches capped (4 from 2025, 3 from 2026; 12 catches)"
    luck, _ = RS.luck_for({("p1", "catch"): [[10.0]] * 12}, cur, "p1", "catch")
    assert (luck["games"], luck["prior_games"], luck["cur_games"]) == (10, 7, 3)
    luck, _ = RS.luck_for({("q", "pass"): [[9.0] * 2, [9.0] * 20]}, {"q": [[9.0] * 18, [9.0]]}, "q", "pass")
    assert (luck["prior_games"], luck["cur_games"]) == (1, 1)
    assert RS.capped_label(None, "runs", "carries", 2025, 2026) == "Recent games, long runs capped"


def test_keeping_target_draws_changes_no_simulated_number():
    # the volume chance reads the per-player targets the sampler already draws: asking for them must not
    # consume random numbers, or every price after it would move
    import numpy as np
    import model as MODEL
    args = (60_000, 34.0, 30.0, {"a": 0.25, "b": 0.2}, {"a": 0.65, "b": 0.7}, {"a": 8.0, "b": 7.0}, 1.4)
    out1, tt1 = MODEL.simulate_team_game(np.random.default_rng(11), *args, other_bucket=True, return_other=True)
    out2, tt2, tg = MODEL.simulate_team_game(np.random.default_rng(11), *args, other_bucket=True, return_other=True,
                                             return_targets=True)
    assert np.array_equal(tt1, tt2)
    for k in ("a", "b"):
        assert np.array_equal(out1[k][0], out2[k][0]) and np.array_equal(out1[k][1], out2[k][1])
    assert abs(tg["a"].mean() - 34.0 * 0.25) < 0.2


def test_the_books_other_lines_row_and_a_missing_price():
    d = {"name": "A Back", "team": "TB", "slot": "RB1", "pos": "RB",
         "rows": [_row("player_rush_yds", 52.5, p_over_book=None)],
         "volume": [{"market": "player_rush_yds", "line": 52.5, "volume_text": "13.8 carries",
                     "book_lines": "carries 13.5, Under favoured; longest run 19.5",
                     "cells": RS.volume_cells("player_rush_yds", 52.5, [15] * 4 + [13] * 6, [("engine", None, 4.0)])}]}
    text = "\n".join(RS.player_card(d))
    assert "| The book's other lines | carries 13.5, Under favoured; longest run 19.5 |" in text
    assert "| **Market's chance of the Over** | **-** |" in text, "no no-vig price: a dash, not a number"


def test_a_card_with_no_priced_line_keeps_its_combined_read():
    d = {"name": "A Back", "team": "TB", "slot": "RB2", "pos": "RB", "rows": [],
         "unpriced_read": "The book's combined line is 40.5."}
    text = "\n".join(RS.player_card(d))
    assert "**Rushing + receiving yards (read, not priced):** The book's combined line is 40.5." in text
    assert "| |" not in text


def test_the_qb_table_no_longer_repeats_the_capped_rate():
    q = {"team_passes": 33.0, "games": [(4, 27, 19)], "gauge": {"need": 17.3}, "gauge_rate": 10.4, "luck_games": 1}
    assert "long completions capped" not in "\n".join(RS.qb_table(q))
    assert "Prices are the books' quoted side prices." in RS.CARD_FOOTNOTE


def test_the_card_guide_explains_every_row_the_table_prints():
    guide = "\n".join(RS.card_guide())
    rows = ["**Market's chance of the Over**", "Engine's chance", "Price: Over / Under",
            "Engine's forecast: middle; 80% range", "The Over needs", "Engine's volume", *RS.ROW_WORDS.values(),
            "The market's own volume line", "The book's other lines", "At the engine's volume, the line needs",
            "His games this season that beat that"]
    for r in rows:
        assert f"| {r} |" in guide, r
    assert "| Row | How it is produced | How to read it |" in guide
    assert f"{RS.LUCK_PCT['catch']:g}th percentile" in guide


def test_the_market_implied_volume_is_the_search_aimed_at_the_markets_chance():
    # a share_over rising linearly in k: P = 0.5 at k = 1, +0.1 per 0.2 of k; work = 8 targets x k
    share_over = lambda k: 0.5 + 0.5 * (k - 1.0)
    work = lambda k: 8.0 * k
    RS._market_cache(share_over, 0.55, work)
    assert abs(RS.LAST_EDGES["market_volume"] - 8.8) < 0.05      # P = 0.55 at k = 1.1
    # the anchor: the main run says 0.52 where the search says 0.50 at k = 1, so a market 0.55
    # is 3 points above the engine and the volume follows that gap (k = 1.06), not the raw 0.55
    RS._market_cache(share_over, 0.55, work, engine_p=0.52)
    assert abs(RS.LAST_EDGES["market_volume"] - 8.48) < 0.05
    # outside the search range: an edge, not a number
    RS._market_cache(lambda k: 0.2, 0.9, work)
    assert RS.LAST_EDGES["market_volume"] is None and RS.LAST_EDGES["market_edge"] == "max"
    RS._market_cache(share_over, None, work)
    assert RS.LAST_EDGES["market_volume"] is None and RS.LAST_EDGES["market_edge"] is None


def test_the_card_shows_the_market_implied_volume():
    d = {"name": "X", "team": "TB", "slot": "WR1", "pos": "WR",
         "rows": [_row("player_receptions", 4.5, unit="targets", market_volume=8.1),
                  _row("player_reception_yds", 68.5, unit="targets", market_volume=8.6, market_catches=5.6),
                  _row("player_rush_yds", 52.5, unit="carries", market_volume=None, market_edge="max")]}
    text = "\n".join(RS.player_card(d))
    assert ("| Market-implied volume (at the engine's efficiency) | 8.1 targets | 8.6 targets -> 5.6 catches | "
            "more carries than the search covers |") in text
    assert "| Market-implied volume (at the engine's efficiency) |" in "\n".join(RS.card_guide())


def test_a_practice_only_report_is_not_a_published_game_report():
    import pandas as pd
    iw = pd.DataFrame({"team": ["TB", "TB", "DAL"], "gsis_id": ["s1", "q1", "c1"],
                       "full_name": ["A Safety", "A Passer", "A Corner"], "position": ["S", "QB", "CB"],
                       "report_status": [None, None, None],
                       "practice_status": ["Did Not Participate In Practice", "Did Not Participate In Practice",
                                           "Full Participation in Practice"]})
    assert RS.report_state(iw, "TB") == "practice" and RS.report_state(iw, "NYG") == "none"
    assert RS.report_state(iw.assign(report_status=["Out", None, None]), "TB") == "game"
    # the defender who missed practice is shown, with the status the prices use and its source
    cell = RS.injury_cell("TB", iw, {("TB", "s1"): "Out"}, {("TB", "s1"): "Sleeper injury feed, knee"})
    assert cell == "A Safety (S, Out; Sleeper injury feed, knee; practice: did not participate in practice)"
    assert RS.injury_cell("TB", iw) == "A Safety (S, no game status yet; practice: did not participate in practice)"
    assert RS.injury_cell("DAL", iw) == "no designations", "full practice is not a designation"
    # once game statuses post, a limited practice with no status reads as no designation, not "not yet"
    fin = iw.assign(report_status=["Out", None, None]).assign(practice_status=["Did Not Participate In Practice",
                                                                                  "Limited Participation in Practice",
                                                                                  "Full Participation in Practice"])
    fin = pd.concat([fin, pd.DataFrame({"team": ["TB"], "gsis_id": ["l1"], "full_name": ["A Backer"],
                                        "position": ["LB"], "report_status": [None],
                                        "practice_status": ["Limited Participation in Practice"]})])
    assert "A Backer (LB, no game designation; practice: limited participation in practice)" in RS.injury_cell("TB", fin)
    note = RS.injury_note({"TB": "practice", "DAL": "game"}, 5)
    assert "game statuses published for DAL" in note and "TB: PRACTICE STATUSES ONLY" in note
    assert "published" not in RS.injury_note({"TB": "practice"}, 5).split("PRACTICE")[0]


def test_out_defenders_and_the_rushing_width_reach_section_7():
    g = RS.known_gaps({"defense_out": {"TB": ["A Safety"]}, "has_rush_lines": True})
    rows = {r[0]: r for r in g}
    assert "TB defense: A Safety out" in rows
    assert "main line is unaffected" not in " ".join(" ".join(r) for r in g)
    assert "not measured" in rows["Rushing width"][1]


def test_the_small_sample_label_says_his_longest_play_was_left_out():
    luck, _ = RS.luck_for({}, {"p": [[3.0, 9.0, 40.0], [5.0, 6.0]]}, "p", "catch")
    assert not luck["own"]
    assert RS.capped_label(luck, "catches", "catches", 2025, 2026) == (
        "Last 2 games, his longest catch left out (2 from 2026; only 5 catches, too few for a percentile cap)")


def test_the_card_guide_says_what_its_numbers_are_not():
    g = "\n".join(RS.card_guide())
    assert "best available estimate" in g and "is the probability" not in g and "as the probability" not in g
    assert "AVERAGE-production threshold" in g and "is not the chance the prop wins" in g
    assert "One game in ten" not in g and "too narrow" in g and "too wide" in g
    assert "luckless" not in g and "sensitivity check" in g
    assert "model error" in g


def test_the_skill_cell_lists_every_listed_receiver_not_only_the_priced_ones():
    import pandas as pd
    iw = pd.DataFrame({"team": ["DAL", "DAL"], "gsis_id": ["w5", "s1"], "full_name": ["A Fifth Receiver", "A Safety"],
                       "position": ["WR", "S"], "report_status": ["Questionable", None],
                       "practice_status": ["Did Not Participate In Practice", "Full Participation in Practice"]})
    cell = RS.injury_cell("DAL", iw, positions=RS.SKILL_POS)
    assert cell == "A Fifth Receiver (WR, Questionable; practice: did not participate in practice)"


def test_a_status_the_prices_use_but_the_report_lacks_still_reaches_section_4():
    import pandas as pd
    iw = pd.DataFrame({"team": ["DAL"], "gsis_id": ["s1"], "full_name": ["A Safety"], "position": ["S"],
                       "report_status": [None], "practice_status": ["Full Participation in Practice"]})
    cell = RS.injury_cell("DAL", iw, {}, {("DAL", "w9"): "Sleeper injury feed; a reserve list"},
                          positions=RS.SKILL_POS, extra=[("A Receiver", "WR", "w9", "Out"),
                                                         ("A Back", "RB", "b1", "Out (scenario)")])
    assert cell == "A Receiver (WR, Out; Sleeper injury feed; a reserve list); A Back (RB, Out (scenario))"
    # no report rows at all: the extras still show
    assert RS.injury_cell("NYG", iw.iloc[0:0], positions=RS.SKILL_POS,
                          extra=[("A Back", "RB", "b1", "Out (scenario)")]) == "A Back (RB, Out (scenario))"


def test_def_starters_reads_the_depth_charts_side_specific_spots():
    # nflverse/ESPN depth charts name spots by side (RCB, LILB, LDE, NB...), not the report's CB / LB / DE;
    # week 5's TNF dropped Morrison (RCB 1) and Overshown (LILB 1) from section 7 (DECISIONS #216)
    import pandas as pd
    t0, t1 = pd.Timestamp("2026-10-01", tz="UTC"), pd.Timestamp("2026-10-08", tz="UTC")
    spots = ["LDE", "RDE", "LDT", "RDT", "NT", "LILB", "RILB", "MLB", "SLB", "WLB", "LCB", "RCB", "NB", "FS", "SS"]
    rows = [("TB", f"g_{s}", s, 1, t1) for s in spots] + [
        ("TB", "g_backup", "RCB", 2, t1),       # a backup is not a starter
        ("TB", "g_old", "LCB", 1, t0),          # an older snapshot does not count
        ("TB", "g_qb", "QB", 1, t1),            # offence and specialists are not defenders
        ("TB", "g_k", "PK", 1, t1)]
    dcf = pd.DataFrame(rows, columns=["team", "gsis_id", "pos_abb", "pos_rank", "dt"])
    assert RS.def_starters(dcf) == {("TB", f"g_{s}") for s in spots}     # no pos_grp: the spot list
    assert RS.def_starters(dcf.iloc[0:0]) == set()
    # with pos_grp (the real feed): a defender is any rank-1 row in a defensive group, so a spot
    # code the list does not know still counts, and offence / special teams never do
    grp = dcf.assign(pos_grp=["Base 3-4 D"] * len(spots) + ["Base 3-4 D", "Base 3-4 D", "3WR 1TE", "Special Teams"])
    grp = pd.concat([grp, pd.DataFrame([("TB", "g_edge", "EDGE", 1, t1, "Base 4-3 D")], columns=grp.columns)])
    assert RS.def_starters(grp) == {("TB", f"g_{s}") for s in spots} | {("TB", "g_edge")}
    # a snapshot after kickoff is not read: the pre-game chart decides
    assert RS.def_starters(grp, before=pd.Timestamp("2026-10-05", tz="UTC")) == {("TB", "g_old")}


def test_section_7_names_out_starters_by_id_not_by_report_position():
    import pandas as pd
    iw = pd.DataFrame({"team": ["TB", "TB", "TB", "DAL"], "gsis_id": ["s1", "s2", "b1", "s3"],
                       "full_name": ["A Corner", "An Edge", "A Backup", "A Backer"],
                       "position": ["CB", None, "LB", "LB"]})
    status = {("TB", "s1"): "Out", ("TB", "s2"): "Doubtful", ("TB", "b1"): "Out", ("DAL", "s3"): "Questionable"}
    starters = {("TB", "s1"), ("TB", "s2"), ("DAL", "s3")}
    # the backup is out but not a starter; the Questionable starter is not out; the starter with no
    # report position still counts
    assert RS.defense_out(iw, status, starters, ("TB", "DAL")) == {"TB": ["A Corner", "An Edge"], "DAL": []}
    gaps = RS.known_gaps({"defense_out": {"TB": ["A Corner"]}})
    assert any("TB defense: A Corner out" in str(g) for g in gaps)
