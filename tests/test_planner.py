"""Two-pick joint planner (v2 item 1.2) — the Flowers-seam regression test."""

from draftkit.planner import consume, pair_rank


def _cands():
    # the round-3 seam, stylized: greedy urgency prefers the RB (his survival
    # is low), but WR-now + RB-next beats RB-now + WR-next
    return [
        (7.5, "rb why", {"pos": "RB", "vorp": 78.5, "sleeper_id": "javonte"}),
        (5.7, "wr why", {"pos": "WR", "vorp": 84.0, "sleeper_id": "flowers"}),
    ]


REPORT = {
    "RB": {"e_best_next": 71.0},   # RBs run thin but a good one survives
    "WR": {"e_best_next": 66.0},   # calibrated: the top WRs will NOT survive
}
NEEDS = {"RB": 1, "WR": 2, "FLEX": 2}
SECOND = {"RB": 74.0, "WR": 80.0}
ALL = lambda pos_taken: {"RB", "WR"}  # noqa: E731


def test_joint_pair_flips_the_flowers_seam():
    ranked = pair_rank(_cands(), REPORT, NEEDS, SECOND, ALL)
    assert ranked[0][2]["sleeper_id"] == "flowers"
    assert "two-pick plan" in ranked[0][1]


def test_same_position_partner_uses_second_best_now():
    cands = [(9.0, "why", {"pos": "RB", "vorp": 90.0, "sleeper_id": "a"}),
             (1.0, "why", {"pos": "WR", "vorp": 20.0, "sleeper_id": "w"})]
    report = {"RB": {"e_best_next": 88.0}, "WR": {"e_best_next": 10.0}}
    ranked = pair_rank(cands, report, {"RB": 2, "FLEX": 2}, {"RB": 60.0, "WR": 15.0},
                       ALL)
    # RB-RB pair may not claim 88 twice: partner capped at second-best 60
    assert ranked[0][2]["sleeper_id"] == "a"
    assert abs(ranked[0][0] - 150.0) < 0.01  # 90 + 60, not 90 + 88


def test_no_report_means_greedy_fallback():
    cands = _cands()
    assert pair_rank(cands, None, NEEDS, SECOND, ALL) == cands


def test_partner_eligibility_is_conditioned_on_the_candidate():
    # taking the QB consumes the only QB slot; a guardrail-aware eligible_after
    # excludes QB as the partner, so no QB-QB pair credit (review finding C6)
    cands = [(5.0, "w", {"pos": "WR", "vorp": 50.0, "sleeper_id": "x"}),
             (4.0, "q", {"pos": "QB", "vorp": 45.0, "sleeper_id": "q"})]
    report = {"WR": {"e_best_next": 40.0}, "QB": {"e_best_next": 44.0}}

    def eligible_after(pos_taken):
        return {"WR"} if pos_taken == "QB" else {"WR", "QB"}

    ranked = pair_rank(cands, report, {"WR": 1, "QB": 1, "FLEX": 1},
                       {"WR": 35.0, "QB": 40.0}, eligible_after)
    q = next(r for r in ranked if r[2]["sleeper_id"] == "q")
    assert "QB expected" not in q[1]          # QB never paired with QB partner
    assert "WR expected" in q[1]


def test_consume_prefers_dedicated_slot_then_flex():
    needs = {"RB": 1, "WR": 0, "FLEX": 1}
    after_rb = consume(needs, "RB")
    assert after_rb == {"RB": 0, "WR": 0, "FLEX": 1}
    after_wr = consume(needs, "WR")           # no WR slot -> eats FLEX
    assert after_wr == {"RB": 1, "WR": 0, "FLEX": 0}


def test_near_tie_goes_to_the_scarcer_player():
    """User rule (2026-09-03): pairs within NEAR_TIE points are a coin flip,
    so the player LESS likely to survive to the next turn goes first; outside
    the window the pair order holds."""
    from draftkit.planner import NEAR_TIE, pair_rank
    needs = {"RB": 1, "WR": 1, "FLEX": 1}
    a = {"sleeper_id": "a", "pos": "WR", "proj_pts": 160.0, "vorp": 40.0, "vorp_flex": 40.0}
    b = {"sleeper_id": "b", "pos": "RB", "proj_pts": 160.0, "vorp": 39.5, "vorp_flex": 39.5}
    report = {"WR": {"e_best_next": 30.0, "survival": {"a": 0.85}},
              "RB": {"e_best_next": 30.0, "survival": {"b": 0.75}}}
    cands = [(40.0, "wr why", a), (39.5, "rb why", b)]
    ranked = pair_rank(cands, report, needs, {"WR": 30.0, "RB": 30.0}, lambda pos: {"RB", "WR"})
    assert [p["sleeper_id"] for _, _, p in ranked] == ["b", "a"], "scarcer RB first within the tie window"
    assert "near tie" in ranked[0][1] and b["_pair"]["pick_cost"] == 0.0
    # outside the window the higher pair keeps the top spot
    a2 = dict(a, vorp=40.0 + NEAR_TIE + 1.0, vorp_flex=40.0 + NEAR_TIE + 1.0)
    ranked2 = pair_rank([(42.0, "wr why", a2), (39.5, "rb why", dict(b))], report, needs,
                        {"WR": 30.0, "RB": 30.0}, lambda pos: {"RB", "WR"})
    assert ranked2[0][2]["sleeper_id"] == "a"


# ---------- the reason must be the reason (2026-09-04, room 10704422) --------
# pair_rank sorts on `pair`. The urgency sentence a `why` OPENS with -- "waiting
# likely costs ~N pts" -- is the greedy score, which only breaks ties. Printing
# one number as the reason while sorting on another made the trails
# unauditable: at pick 11 the report showed McBride's waiting cost as 31 and
# Chase Brown's as 13, took Chase Brown, and nothing anywhere said why. The
# deciding term was own-value, which appeared in no human-readable output.

def _printed_total(why: str) -> float:
    """The number the reason claims decided the pick."""
    return float(why.split("RANKED ON ")[1].split(" =")[0])


def test_the_printed_number_is_the_one_the_sort_returned():
    """The invariant. pair_rank returns (pair, why, player) and sorts on pair,
    so the number printed in the reason must BE that pair, for every row --
    near-tie swaps included, since a swap moves the row and its number
    together."""
    ranked = pair_rank(_cands(), REPORT, NEEDS, SECOND, ALL)
    assert ranked
    for pair, why, p in ranked:
        assert "RANKED ON" in why, why
        assert abs(_printed_total(why) - pair) < 0.51, (why, pair)
        assert abs(_printed_total(why) - p["_pair"]["pair"]) < 0.51


def test_the_printed_parts_add_up_to_the_printed_total():
    """A reason showing a sum nobody can check is no better than no reason."""
    for _pair, _why, p in pair_rank(_cands(), REPORT, NEEDS, SECOND, ALL):
        d = p["_pair"]
        assert abs(d["own"] + d["partner_pts"] - d["pair"]) < 0.11, d


def test_a_candidate_with_no_partner_says_so_rather_than_going_silent():
    cands = [(5.0, "qb why", {"pos": "QB", "vorp": 30.0, "sleeper_id": "q1"}),
             (4.0, "rb why", {"pos": "RB", "vorp": 20.0, "sleeper_id": "r1"})]
    report = {"QB": {"e_best_next": 10.0}, "RB": {"e_best_next": 8.0}}
    ranked = pair_rank(cands, report, {"QB": 1, "RB": 1}, {"QB": 5.0, "RB": 5.0},
                       lambda pos_taken: set())
    for _pair, why, _p in ranked:
        assert "RANKED ON" in why
        assert "no partner" in why


def test_the_urgency_sentence_is_not_mistaken_for_the_ranking():
    """The actual defect, reproduced in miniature: the row with the WORSE
    greedy score can win, and when it does the reason must still explain the
    win. Before this, such a row printed only its urgency number and the
    reader was left with a reason that argued for the other player."""
    ranked = pair_rank(_cands(), REPORT, NEEDS, SECOND, ALL)
    winner_why = ranked[0][1]
    # 'flowers' wins on the pair despite the RB carrying the higher greedy score
    assert ranked[0][2]["sleeper_id"] == "flowers"
    assert "RANKED ON" in winner_why
    assert _printed_total(winner_why) >= _printed_total(ranked[1][1]) - 2.0


def test_greedy_fallback_adds_no_ranked_on_clause():
    """With no report the order is greedy and `pair` never runs, so claiming a
    pair total would be a lie."""
    cands = _cands()
    out = pair_rank(cands, None, NEEDS, SECOND, ALL)
    assert all("RANKED ON" not in w for _s, w, _p in out)


# ---------- touchdown tiebreak (user decision 2026-09-05, DECISIONS #53) ------

def _td_case(td_a, td_b, pos_a="WR", pos_b="RB", gap=4.0):
    from draftkit.planner import pair_rank
    needs = {"RB": 1, "WR": 1, "QB": 1, "FLEX": 1}
    a = {"sleeper_id": "a", "pos": pos_a, "proj_pts": 170.0, "vorp": 40.0 + gap, "vorp_flex": 40.0 + gap, "proj_td": td_a}
    b = {"sleeper_id": "b", "pos": pos_b, "proj_pts": 176.0, "vorp": 40.0, "vorp_flex": 40.0, "proj_td": td_b}
    report = {pos_a: {"e_best_next": 30.0, "survival": {"a": 0.69}},
              pos_b: {"e_best_next": 30.0, "survival": {"b": 0.57}}}
    cands = [(40.0 + gap, "a why", a), (40.0, "b why", b)]
    return pair_rank(cands, report, needs, {pos_a: 30.0, pos_b: 30.0}, lambda pos: {"RB", "WR", "QB"},
                     tie_break="touchdowns", tie_window=5.0), a, b


def test_touchdown_tiebreak_takes_the_higher_td_skill_player_inside_the_window():
    """Rice (10.5 TD) vs Javonte (11.9 TD), 4.7 apart on the ranked number:
    with tie_break touchdowns and a 5-point window Javonte goes first, and
    the label names the counterparty and both counts."""
    ranked, a, b = _td_case(10.5, 11.9, gap=4.7)
    assert [p["sleeper_id"] for _, _, p in ranked] == ["b", "a"]
    assert "more projected touchdowns (11.9 vs 10.5)" in ranked[0][1]
    assert b["_pair"]["pick_cost"] == 0.0


def test_touchdown_tiebreak_holds_the_order_when_the_top_player_has_more():
    ranked, _a, _b = _td_case(11.9, 10.5, gap=4.7)
    assert ranked[0][2]["sleeper_id"] == "a" and "near tie" not in ranked[0][1]


def test_touchdown_tiebreak_respects_the_window():
    ranked, _a, _b = _td_case(10.5, 11.9, gap=5.5)
    assert ranked[0][2]["sleeper_id"] == "a"


def test_touchdown_tiebreak_never_compares_a_quarterback():
    """A QB has thirty scores; a QB-vs-skill near-tie keeps the scarcity rule
    (inside NEAR_TIE only), so a 4-point gap is not touched at all."""
    ranked, _a, _b = _td_case(10.5, 32.0, pos_a="WR", pos_b="QB", gap=4.0)
    assert ranked[0][2]["sleeper_id"] == "a" and "touchdowns" not in ranked[0][1]


def test_touchdown_tiebreak_is_off_by_default():
    from draftkit.planner import pair_rank
    needs = {"RB": 1, "WR": 1, "FLEX": 1}
    a = {"sleeper_id": "a", "pos": "WR", "proj_pts": 170.0, "vorp": 44.0, "vorp_flex": 44.0, "proj_td": 10.5}
    b = {"sleeper_id": "b", "pos": "RB", "proj_pts": 176.0, "vorp": 40.0, "vorp_flex": 40.0, "proj_td": 11.9}
    report = {"WR": {"e_best_next": 30.0, "survival": {"a": 0.69}}, "RB": {"e_best_next": 30.0, "survival": {"b": 0.57}}}
    ranked = pair_rank([(44.0, "a", a), (40.0, "b", b)], report, needs, {"WR": 30.0, "RB": 30.0}, lambda pos: {"RB", "WR"})
    assert ranked[0][2]["sleeper_id"] == "a"


def test_equal_touchdowns_fall_back_to_scarcity_inside_near_tie():
    from draftkit.planner import pair_rank
    needs = {"RB": 1, "WR": 1, "FLEX": 1}
    a = {"sleeper_id": "a", "pos": "WR", "proj_pts": 170.0, "vorp": 40.5, "vorp_flex": 40.5, "proj_td": 10.0}
    b = {"sleeper_id": "b", "pos": "RB", "proj_pts": 176.0, "vorp": 40.0, "vorp_flex": 40.0, "proj_td": 10.0}
    report = {"WR": {"e_best_next": 30.0, "survival": {"a": 0.85}}, "RB": {"e_best_next": 30.0, "survival": {"b": 0.75}}}
    ranked = pair_rank([(40.5, "a", a), (40.0, "b", b)], report, needs, {"WR": 30.0, "RB": 30.0}, lambda pos: {"RB", "WR"},
                       tie_break="touchdowns", tie_window=5.0)
    assert ranked[0][2]["sleeper_id"] == "b" and "scarcer player first" in ranked[0][1]


# ---------- floor rule (user, 2026-09-05, DECISIONS #55) -----------------------

def _floor_case(surv_a, surv_b, lo_a, lo_b, gap=0.5, band_a=None, band_b=None):
    from draftkit.planner import pair_rank
    needs = {"RB": 1, "WR": 1, "FLEX": 1}
    a = {"sleeper_id": "rice", "player": "Rashee Rice", "pos": "WR", "proj_pts": 170.0,
         "vorp": 40.0 + gap, "vorp_flex": 40.0 + gap, "proj_lo": lo_a, "proj_hi": 199.8, "proj_band": band_a}
    b = {"sleeper_id": "javonte", "player": "Javonte Williams", "pos": "RB", "proj_pts": 176.0,
         "vorp": 40.0, "vorp_flex": 40.0, "proj_lo": lo_b, "proj_hi": 188.6, "proj_band": band_b}
    report = {"WR": {"e_best_next": 30.0, "survival": {"rice": surv_a}},
              "RB": {"e_best_next": 30.0, "survival": {"javonte": surv_b}}}
    ranked = pair_rank([(40.0 + gap, "rice why", a), (40.0, "javonte why", b)], report, needs,
                       {"WR": 30.0, "RB": 30.0}, lambda pos: {"RB", "WR"})
    return [p["sleeper_id"] for _, _, p in ranked], ranked[0][1]


def test_javonte_beats_rice_on_the_floor_when_survival_cannot_separate_them():
    """Rice 0.5 ahead on the pair and 2 points scarcer (57% against 59%),
    so the survival rule keeps him first on noise. The survivals are within
    5 points, the floors from the sheet's low lines are 150 and 161: the
    higher floor goes first, and the reason names the man he went over."""
    order, why = _floor_case(surv_a=0.57, surv_b=0.59, lo_a=150.0, lo_b=161.1)
    assert order == ["javonte", "rice"]
    assert "near tie (0.5 pts) with Rashee Rice: higher floor (161 vs 150)" in why


def test_the_floor_rule_stays_out_when_survival_settled_it():
    """Survivals 80% against 60%: the survival rule already decided (the
    scarcer man first) and a 20-point gap is not a tie the floor may reopen."""
    order, why = _floor_case(surv_a=0.60, surv_b=0.80, lo_a=150.0, lo_b=161.1)
    assert order == ["rice", "javonte"] and "higher floor" not in why


def test_the_floor_rule_needs_three_points_and_falls_back_to_the_band():
    # floors 158 and 160: too close to call, the survival order (Rice scarcer) holds
    order, _ = _floor_case(surv_a=0.57, surv_b=0.59, lo_a=158.0, lo_b=160.0)
    assert order == ["rice", "javonte"]
    # no low lines: projection minus half the band stands in (170-10 vs 176-5.6)
    order, why = _floor_case(surv_a=0.57, surv_b=0.59, lo_a=None, lo_b=None, band_a=20.1, band_b=11.2)
    assert order == ["javonte", "rice"] and "higher floor (170 vs 160)" in why
    # neither floor nor band on one side: left alone
    order, _ = _floor_case(surv_a=0.57, surv_b=0.59, lo_a=None, lo_b=161.1, band_a=None, band_b=None)
    assert order == ["rice", "javonte"]


def test_one_comparator_leaves_no_stale_label_on_the_demoted_row():
    """Review 2026-09-05: with the input order reversed (Javonte ahead, Rice
    2 points scarcer) the old survival pass promoted Rice and labelled him,
    then the floor pass demoted him again and left the label. One comparator:
    Javonte stays first, nobody carries a near-tie label."""
    from draftkit.planner import pair_rank
    needs = {"RB": 1, "WR": 1, "FLEX": 1}
    j = {"sleeper_id": "javonte", "player": "Javonte Williams", "pos": "RB", "proj_pts": 176.0,
         "vorp": 40.5, "vorp_flex": 40.5, "proj_lo": 161.1, "proj_hi": 188.6, "proj_band": 11.3}
    r = {"sleeper_id": "rice", "player": "Rashee Rice", "pos": "WR", "proj_pts": 170.0,
         "vorp": 40.0, "vorp_flex": 40.0, "proj_lo": 150.0, "proj_hi": 199.8, "proj_band": 20.1}
    report = {"WR": {"e_best_next": 30.0, "survival": {"rice": 0.57}},
              "RB": {"e_best_next": 30.0, "survival": {"javonte": 0.59}}}
    ranked = pair_rank([(40.5, "j", j), (40.0, "r", r)], report, needs, {"WR": 30.0, "RB": 30.0}, lambda pos: {"RB", "WR"})
    assert [p["sleeper_id"] for _, _, p in ranked] == ["javonte", "rice"]
    assert all("near tie" not in why for _, why, _ in ranked)


def test_a_lineless_single_source_has_no_floor_to_compare():
    """proj_lo == proj_hi == proj_pts is a point, not a range: the floor rule
    falls back to the band, and with no band it leaves the pair alone."""
    from draftkit.planner import pair_rank
    needs = {"RB": 1, "WR": 1, "FLEX": 1}
    a = {"sleeper_id": "a", "pos": "WR", "proj_pts": 170.0, "vorp": 40.5, "vorp_flex": 40.5,
         "proj_lo": 170.0, "proj_hi": 170.0, "proj_band": None}
    b = {"sleeper_id": "b", "pos": "RB", "proj_pts": 176.0, "vorp": 40.0, "vorp_flex": 40.0,
         "proj_lo": 176.0, "proj_hi": 176.0, "proj_band": None}
    report = {"WR": {"e_best_next": 30.0, "survival": {"a": 0.57}}, "RB": {"e_best_next": 30.0, "survival": {"b": 0.59}}}
    ranked = pair_rank([(40.5, "a", a), (40.0, "b", b)], report, needs, {"WR": 30.0, "RB": 30.0}, lambda pos: {"RB", "WR"})
    assert ranked[0][2]["sleeper_id"] == "a" and "higher floor" not in ranked[0][1]
