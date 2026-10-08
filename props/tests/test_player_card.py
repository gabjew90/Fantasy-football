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
    assert "carries + catches at 4.0 a carry, 8.0 a catch -> **50%**" in text
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
