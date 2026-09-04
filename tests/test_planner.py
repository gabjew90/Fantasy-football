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
