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


def test_receiver_card_order_and_tables():
    d = {"name": "A Receiver", "team": "TB", "slot": "WR1", "pos": "WR", "book": "sleeper",
         "quoted": "2026-10-07 01:48 UTC",
         "rows": [_row("player_reception_yds", 49.5), _row("player_receptions", 4.5)],
         "usage": USAGE, "qbs": (["B.Mayfield"], "J.Daniels"),
         "prior": {"ts": 0.23, "games": 17, "team": "TB", "new_team": False},
         "season": {"games": 4, "targets": 24, "catches": 15},
         "matchup": "DAL allows a lot.", "watch": ["Baker Mayfield (QB) out"]}
    L = RS.player_card(d)
    text = "\n".join(L)
    assert L[0] == "#### A Receiver (WR1) · Receptions and Receiving yards"
    # the fixed market order: receptions before receiving yards whatever order the rows came in
    assert text.index("| Receptions | 4.5") < text.index("| Receiving yards | 49.5")
    assert "| Role evidence | Earlier games (3) | Last game (week 4) |" in text
    assert "| Targets and share of team targets | 6.3 a game; 20% | 8; 25% |" in text
    assert "| Quarterback who threw most | B.Mayfield | J.Daniels |" in text
    assert "Historical baseline: last season 23% of his team's targets over 17 games with TB." in text
    assert "This season: 24 targets, 15 catches in 4 games." in text
    assert "| At the quoted price | Over above 6.2; Under at or below 5.1 targets |" in text
    assert "carries" not in text.split("| Workload check")[1]           # receivers: no carries table
    assert text.rstrip().endswith("**Watch:** Baker Mayfield (QB) out.")


def test_back_card_combined_column_is_never_a_threshold():
    rr = {"proj_carries": 14.8, "proj_catches": 3.1, "book_catches": None, "air_share": 0.31}
    d = {"name": "A Back", "team": "TB", "slot": "RB1", "pos": "RB",
         "rows": [_row("player_rush_yds", 52.5, projected=14.8, implied=13.9, over_needs=15.0, under_needs=12.7),
                  _row("player_rush_reception_yds", 68.5, projected=None, implied=None, over_needs=None,
                       under_needs=None)],
         "usage": {**USAGE, "cs": 0.52, "cs_base": 0.61, "cn": 16.0, "cn_base": 13.3},
         "backfield": {"early": 0.62, "early_base": 0.69, "passdown": 0.0, "passdown_base": 0.14, "i5": 0.0,
                       "i5_base": float("nan"), "i5_n": 0, "i5_team": 1},
         "carries_book": {"line": 13.5, "fav": "Under", "fair": 13.4}, "reads": {"rr": rr},
         "shadow": [{"line": 52.5, "p_board": 0.55, "p_mkt": 0.53, "car_from": 14.8, "car_to": 14.3}]}
    text = "\n".join(RS.player_card(d))
    assert "| Workload check | Rushing yards | Combined yards |" in text
    assert ("| At the quoted price | Over above 15.0; Under at or below 12.7 carries, conditional on the model | "
            "compare the scenario's chance with the required win rate |") in text
    assert "| Workload making the line roughly 50/50 | 13.9 carries a game | use the separate carry-and-catch scenario |" in text
    assert "| Market's own volume lines | 13.5 carries, Under favoured; a coin flip near 13.4 | " \
           "13.5 carries, Under favoured and no receptions line |" in text
    assert "| Share of projected combined yards from catches | - | 31% |" in text
    assert "(0 of 1)" in text and "| Carries and share of team carries | 13.3 a game; 61% | 16; 52% |" in text
    assert "Over 55% on the board (his carries half from the market's script), 53% from history alone" in text


def test_qb_card_states_the_measured_bias_and_no_threshold():
    q = {"team_passes": 33.0, "games": [(3, 3, 0), (4, 27, 19)], "proj_cmp": 21.6, "cmp_line": 17.5,
         "att_line": 28.5, "att_fav": "Over", "gauge": {"need": 17.3}, "gauge_rate": 10.4, "luck_games": 1}
    d = {"name": "A Passer", "team": "TB", "slot": "QB1", "pos": "QB",
         "rows": [_row("player_pass_yds", 179.5)], "qb": q}
    text = "\n".join(RS.player_card(d))
    assert "| His recent workload | week 3: 3 attempts, 0 completions; week 4: 27 attempts, 19 completions |" in text
    assert "completions 17.5; attempts 28.5, Over favoured" in text
    assert "over his last 1 game (arithmetic, not a price-based break-even)" in text
    assert "Backtest calibration" not in text, "no implied total: no backtest row"
    assert "Live record at Sleeper's lines" in text
    d2 = {**d, "implied": 28.0}
    t2 = "\n".join(RS.player_card(d2))
    assert "| Passing yards | 57.0% | 41.7% | 50.1% | 86 |" in t2, "the live record at real lines comes first"
    assert "**Backtest calibration** (TB, implied 28.0):" in t2
    assert "| Passing yards, teams implied 27+ | 65.5% | 56.8% | 174 |" in t2
    assert "Role evidence" not in text
    three = RS.qb_table({**q, "games": [(1, 30, 20), (2, 34, 22), (3, 27, 19)]})
    assert "earlier games (2): 32.0 attempts, 21.0 completions a game; last game (week 3): 27 attempts, 19" in three[3]


def test_too_few_games_and_missing_pieces_degrade_in_words():
    assert RS.role_table(None)[0].startswith("Role evidence: fewer than three games")
    assert RS.workload_table([], "rec") == [] and RS.capped_line(None, "catch") == ""
    assert RS.baseline_line(None, {"games": 0}) == ""
    assert RS.qb_table({"games": []})[3] == "| His recent workload | no starts this season |"


def test_qb_workload_counts_attempts_not_sacks():
    import pandas as pd
    pbp = pd.DataFrame({"week": [1, 1, 1, 2], "passer_player_id": ["Q", "Q", "Q", "Q"],
                        "play_type": ["pass"] * 4, "sack": [0, 1, 0, 0], "pass_attempt": [1, 1, 1, 1],
                        "complete_pass": [1, 0, 0, 1]})
    assert RS.qb_workload(pbp, "Q") == [(1, 2, 1), (2, 1, 1)]
    assert RS.qb_workload(pbp, None) == []


def test_two_books_are_named_and_line_fit_reads_print():
    L = RS.prop_rows_table([_row("player_receptions", 4.5, book="sleeper"), _row("player_receptions", 5.5, book="draftkings")])
    assert L[2].startswith("| Receptions (sleeper) | 4.5") and L[3].startswith("| Receptions (draftkings) | 5.5")
    assert RS.prop_rows_table([_row("player_receptions", 4.5, book="sleeper")])[2].startswith("| Receptions | 4.5")
    d = {"name": "X", "team": "TB", "slot": "WR2", "pos": "WR", "rows": [_row("player_receptions", 4.5)],
         "fit": ["The book's yards a catch is 11.0."]}
    assert "**How his lines fit together:** The book's yards a catch is 11.0." in "\n".join(RS.player_card(d))


def test_a_tight_end_card_shows_his_roles_measured_row():
    d = {"name": "T", "team": "DAL", "slot": "TE1", "pos": "TE", "implied": 28.0,
         "rows": [_row("player_receptions", 3.5), _row("player_reception_yds", 32.5)]}
    text = "\n".join(RS.player_card(d))
    assert "| Receptions, every tight end | 49.0% | 44.1% | 1480 |" in text
    assert "| Receiving yards, every tight end | 54.0% | 47.4% | 1480 |" in text
    assert "| Receiving yards, teams implied 27+ | 52.2% | 47.6% | 709 |" in text
    wr = RS.calibration_line({"player_receptions"}, None, None, "WR2")
    assert "| Receptions, every wide receiver | 45.1% | 44.3% | 4754 |" in wr
    assert "| Receptions | 48.4% | 45.2% | 49.6% | 506 |" in wr, "the live record at real lines"
    assert RS.calibration_line({"player_rush_reception_yds"}, None, None, "RB1") == [], "no live lines, no implied row"


def test_volume_chance_known_answers():
    # 68.5 needs 69 yards: at 13.1 a catch that is ceil(69/13.1) = 6 catches; at 9.4, 8 (7.3 rounds up)
    draws = list(range(1, 11))                       # 1..10 catches, one each: P(>= 6) = 5/10
    L = RS.volume_chance("player_reception_yds", 68.5, draws, [("Capped", 13.1), ("Season", 9.4), ("Bad", None)],
                         games=[(5, 80.0), (6, 40.0), (0, 0.0)], team="DAL")
    txt = "\n".join(L)
    assert "| Capped | 13.1 | 6 catches | 50% |" in txt
    assert "| Season | 9.4 | 8 catches | 30% |" in txt
    assert "Bad" not in txt                         # an assumption with no rate is left out
    # the engine's mean is 5.5 catches, so the line needs 69 / 5.5 = 12.5 a catch; 16.0 beat it, 6.7 did not,
    # and the zero-catch game is not a game he could beat it in
    assert ("At the engine's 5.5 catches, the line needs 12.5 yards a catch; he beat that in 1 of his 2 games "
            "for DAL this season.") in txt
    assert "catch counts are calibrated" in txt     # the backtest note for catches rides on the table


def test_volume_chance_receptions_and_carries():
    # 4.5 catches needs 5: at a 65% catch rate ceil(5/0.65) = 8 targets
    L = RS.volume_chance("player_receptions", 4.5, [8] * 3 + [7] * 7, [("Season", 0.65)])
    assert "| Season | 65% | 8 targets | 30% |" in "\n".join(L)
    # a whole-number rate lands exactly: 60 yards at 4.0 a carry is 15 carries, not 16
    L = RS.volume_chance("player_rush_yds", 59.5, [15] * 4 + [14] * 6, [("Engine", 4.0)], market_volume=14.5)
    txt = "\n".join(L)
    assert "| Engine | 4.0 | 15 carries | 40% |" in txt
    assert "| The market's own carries line | - | more than 14.5 carries | 40% |" in txt
    assert "4-5 points low" in txt
    assert RS.volume_chance("player_rush_yds", None, [10], [("Engine", 4.0)]) == []
    assert RS.volume_chance("player_rush_yds", 59.5, [], [("Engine", 4.0)]) == []


def test_volume_chance_passing_counts_completions():
    # 265.5 needs 266: at 11.7 a completion ceil(266/11.7) = 23 completions
    L = RS.volume_chance("player_pass_yds", 265.5, [23] * 5 + [22] * 5, [("Capped", 11.7)], market_volume=22.5)
    txt = "\n".join(L)
    assert "| Capped | 11.7 | 23 completions | 50% |" in txt
    assert "| The market's own completions line | - | more than 22.5 completions | 50% |" in txt


def test_volume_chance_rushing_plus_receiving_uses_two_rates():
    # carries and catches drawn together: 10 carries + 2 catches, or 14 carries + 4 catches
    car, cat = [10] * 5 + [14] * 5, [2] * 5 + [4] * 5
    # at 4.0 a carry and 8.0 a catch: 56 or 88 yards; a 60.5 line needs 61 -> only the second half clears
    L = RS.volume_chance("player_rush_reception_yds", 60.5, (car, cat), [("Engine", (4.0, 8.0)), ("Half", (4.0, None))],
                         games=[(15, 70.0)])
    txt = "\n".join(L)
    # blended rate (12*4 + 3*8) / 15 = 4.8 a touch -> ceil(61/4.8) = 13 carries + catches
    assert "| Engine | 4.0 a carry, 8.0 a catch | 13 carries + catches | 50% |" in txt
    assert "Half" not in txt                        # a pair with a missing rate is left out
    assert "Engine's chance at that efficiency" in txt
    assert "the line needs 4.1 yards a carry or catch; he beat that in 1 of his 1 games" in txt
    assert RS.volume_chance("player_rush_reception_yds", 60.5, ([1, 2], [1]), [("E", (4.0, 8.0))]) == []


def test_volume_chance_receptions_past_his_targets():
    # 2.5 catches needs 3; the engine projects 2.0 targets -- no catch rate gets there
    L = RS.volume_chance("player_receptions", 2.5, [2.0] * 10, [("Season", 0.8)], games=[(3, 3.0)])
    txt = "\n".join(L)
    assert "the line needs 3 catches -- more than his targets." in txt and "%;" not in txt


def test_the_card_prints_a_volume_chance_block():
    vol = RS.volume_chance("player_reception_yds", 68.5, list(range(1, 11)), [("Season", 13.1)])
    d = {"name": "Test Player", "team": "DAL", "slot": "WR1", "pos": "WR",
         "rows": [_row("player_reception_yds", 68.5)], "book": "sleeper", "quoted": None, "fit": [],
         "volume": [{"market": "player_reception_yds", "line": 68.5, "lines": vol}]}
    txt = "\n".join(RS.player_card(d))
    assert "**Volume chance, receiving yards 68.5**" in txt and "| Season | 13.1 | 6 catches | 50% |" in txt


def test_the_capped_label_names_the_window_luck_for_used():
    # 4 games last season with a catch, 3 this season: the window holds all 7 (fewer than 10 -> says 7)
    prior = {("p1", "catch"): [[10.0, 12.0]] * 4}
    cur = {"p1": [[8.0], [9.0, 30.0], [5.0]]}
    luck, _rate = RS.luck_for(prior, cur, "p1", "catch")
    assert (luck["games"], luck["prior_games"], luck["cur_games"], luck["plays"]) == (7, 4, 3, 12)
    assert RS.capped_label(luck, "catches", "catches", 2025, 2026) ==         "Last 7 games, long catches capped (4 from 2025, 3 from 2026; 12 catches)"
    # 12 games last season: only the latest 7 of them fit beside this season's 3
    luck, _ = RS.luck_for({("p1", "catch"): [[10.0]] * 12}, cur, "p1", "catch")
    assert (luck["games"], luck["prior_games"], luck["cur_games"]) == (10, 7, 3)
    # a passer's cameo games (under 5 completions) are not in his window, last season or this
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
