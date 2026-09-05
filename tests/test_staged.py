"""The staged starter ranking (user design, 2026-09-05): value on the deadline
horizon picks the position and the player, one-turn urgency then banded
scarcity then variance by round break ties, pair last; the pair leads at the
turn and on a flat board."""

from draftkit.staged import (BOTH_GONE, SURV_GAP, URGENCY_BAND, VALUE_BAND, VARIANCE_BAND,
                             staged_rank, staged_value)

NEEDS = {"QB": 1, "RB": 1, "WR": 1, "TE": 1, "FLEX": 1}
FALLBACK = {"QB": 260.0, "RB": 120.0, "WR": 130.0, "TE": 100.0}
REPL = {"QB": 250.0, "RB": 146.0, "WR": 136.0, "TE": 113.0, "FLEX": 136.0}


def _p(sid, pos, pts, lo=None, hi=None, band=None):
    return {"sleeper_id": sid, "player": sid, "pos": pos, "proj_pts": pts,
            "vorp": pts - REPL[pos], "vorp_flex": pts - REPL["FLEX"],
            "proj_lo": lo, "proj_hi": hi, "proj_band": band}


def _report(surv, e_next=None, best_now=None):
    out = {}
    for pos in ("QB", "RB", "WR", "TE", "FLEX"):
        out[pos] = {"best_now": (best_now or {}).get(pos, 50.0), "e_best_next": (e_next or {}).get(pos, 30.0),
                    "urgency": 0.0, "survival": surv.get(pos, {})}
    return out


def _rank(cands, urg, surv, rnd=3, partner_certain=False, e_next=None, best_now=None):
    market_of = {c[2]["sleeper_id"]: c[2]["pos"] for c in cands}
    return staged_rank(cands, _report(surv, e_next, best_now), NEEDS, rnd, urg, market_of,
                       {pos: 0.0 for pos in REPL}, lambda pos: {"QB", "RB", "WR", "TE"},
                       fallback=FALLBACK, repl=REPL, partner_certain=partner_certain)


def test_stage_1_value_picks_the_position_even_when_another_market_is_more_urgent():
    # room 10804278 pick 14: QB one-turn urgency 27.7 vs RB 17.3 took Allen while
    # value had Achane 29 ahead. Stage 1 now reads the deadline horizon.
    qb = _p("qb", "QB", 315.0)      # value 55
    rb = _p("rb", "RB", 204.0)      # value 84
    out = _rank([(27.7, "q", qb), (17.3, "r", rb)], {"QB": 27.7, "RB": 17.3}, {})
    assert out[0][2]["sleeper_id"] == "rb"
    assert "STAGED: value picked RB (84.0, next QB 55.0; one-turn urgency 17.3, top 27.7), one row live" in out[0][1]
    assert "not live, QB best value 55.0 vs 84.0 at the top (band 2); one-turn urgency 27.7" in out[1][1]
    assert out[1][2]["_staged"]["market_best"] == 55.0


def test_stage_1_a_market_is_live_on_its_best_row_and_stage_2_ranks_the_players():
    wr1 = _p("wr1", "WR", 190.0)    # value 60
    wr2 = _p("wr2", "WR", 185.0)    # value 55, same market
    rb = _p("rb", "RB", 179.0)      # value 59, market within VALUE_BAND of WR
    out = _rank([(30.0, "w", wr1), (30.0, "w", wr2), (20.0, "r", rb)], {"WR": 30.0, "RB": 30.0 - URGENCY_BAND}, {})
    assert [c[2]["sleeper_id"] for c in out][:1] == ["wr1"]
    assert "value picked RB/WR (60.0" in out[0][1]
    assert out[-1][2]["sleeper_id"] == "wr2"
    assert "staged: value 55.0, 5.0 under the best" in out[-1][1]


def test_stage_3_one_turn_urgency_breaks_a_value_tie_across_markets():
    wr = _p("wr", "WR", 190.0)      # value 60
    rb = _p("rb", "RB", 181.0)      # value 61, inside VALUE_BAND
    surv = {"WR": {"wr": 0.20}, "RB": {"rb": 0.20 + SURV_GAP}}   # scarcity would take the WR
    out = _rank([(30.0, "w", wr), (28.0, "r", rb)], {"WR": 30.0 - URGENCY_BAND, "RB": 30.0}, surv)
    assert out[0][2]["sleeper_id"] == "rb"
    assert "value within 2, RB more urgent (30.0 vs 28.5 for WR); one row left" in out[0][1]
    assert "less urgent market (WR 28.5 vs RB 30.0)" in out[1][1]


def test_stage_3_skips_when_the_urgency_gap_is_inside_the_band():
    wr = _p("wr", "WR", 190.0)
    rb = _p("rb", "RB", 181.0)
    surv = {"WR": {"wr": 0.20}, "RB": {"rb": 0.20 + SURV_GAP}}
    out = _rank([(30.0, "w", wr), (29.0, "r", rb)], {"WR": 29.0, "RB": 30.0}, surv)
    assert out[0][2]["sleeper_id"] == "wr"
    assert "scarcer first (20% vs 35% for rb" in out[0][1]


def test_stage_3_a_survival_gap_takes_the_scarcer_player():
    wr = _p("wr", "WR", 190.0)      # value 60
    rb = _p("rb", "RB", 181.0)      # value 61, inside VALUE_BAND
    surv = {"WR": {"wr": 0.20}, "RB": {"rb": 0.20 + SURV_GAP}}
    out = _rank([(30.0, "w", wr), (30.0, "r", rb)], {"WR": 30.0, "RB": 30.0}, surv)
    assert out[0][2]["sleeper_id"] == "wr"
    assert "scarcer first (20% vs 35% for rb" in out[0][1]


def test_stage_3_both_gone_regardless_goes_to_the_pair():
    wr = _p("wr", "WR", 190.0)
    rb = _p("rb", "RB", 181.0)
    surv = {"WR": {"wr": 0.05}, "RB": {"rb": BOTH_GONE - 0.01}}
    # the pair: taking the WR leaves a 40-pt RB next turn, taking the RB a 10-pt WR
    e_next = {"RB": 40.0 + REPL["RB"] - FALLBACK["RB"] - 0.0, "WR": 10.0}
    out = _rank([(30.0, "w", wr), (30.0, "r", rb)], {"WR": 30.0, "RB": 30.0}, surv, e_next=e_next)
    assert "pair decided (all gone regardless" in out[0][1]
    assert out[0][2]["_pair"]["pair"] >= out[1][2]["_pair"]["pair"]


def test_stage_4_floor_through_round_7_ceiling_after():
    # same value, same survival, ranges differ: a wide-range back and a tight receiver
    wr = _p("wr", "WR", 190.0, lo=180.0, hi=200.0)     # floor 50 over the WR fallback, ceiling 70
    rb = _p("rb", "RB", 181.0, lo=150.0, hi=230.0)     # floor 30 over the RB fallback, ceiling 110
    surv = {"WR": {"wr": 0.5}, "RB": {"rb": 0.5}}
    early = _rank([(30.0, "w", wr), (30.0, "r", rb)], {"WR": 30.0, "RB": 30.0}, surv, rnd=7)
    late = _rank([(30.0, "w", wr), (30.0, "r", rb)], {"WR": 30.0, "RB": 30.0}, surv, rnd=8)
    assert early[0][2]["sleeper_id"] == "wr" and "higher floor over replacement (50 vs 30" in early[0][1]
    assert late[0][2]["sleeper_id"] == "rb" and "higher ceiling over replacement (110 vs 70" in late[0][1]


def test_stage_4_needs_a_range_on_every_side_else_the_pair_decides():
    wr = _p("wr", "WR", 190.0, lo=180.0, hi=200.0)
    rb = _p("rb", "RB", 181.0)                          # no range published
    surv = {"WR": {"wr": 0.5}, "RB": {"rb": 0.5}}
    out = _rank([(30.0, "w", wr), (30.0, "r", rb)], {"WR": 30.0, "RB": 30.0}, surv, rnd=3)
    assert "pair decided (no published range to compare floors)" in out[0][1]


def test_stage_4_within_the_variance_band_goes_to_the_pair():
    wr = _p("wr", "WR", 190.0, lo=180.0, hi=200.0)                      # floor 50
    rb = _p("rb", "RB", 181.0, lo=170.0 + VARIANCE_BAND - 0.5, hi=230.0)  # floor 50.5
    surv = {"WR": {"wr": 0.5}, "RB": {"rb": 0.5}}
    out = _rank([(30.0, "w", wr), (30.0, "r", rb)], {"WR": 30.0, "RB": 30.0}, surv, rnd=3)
    assert "pair decided (floors within 1" in out[0][1]


def test_the_turn_exception_lets_the_pair_lead_then_the_stages_break_its_ties():
    wr = _p("wr", "WR", 190.0, lo=180.0, hi=200.0)
    rb = _p("rb", "RB", 181.0, lo=150.0, hi=230.0)
    surv = {"WR": {"wr": 0.5}, "RB": {"rb": 0.5}}
    # the same partner value either way (best_now set so best_now + repl -
    # fallback is 56 in both markets), so the pairs sit within VALUE_BAND and
    # the stages settle it: round 3, floor, the WR
    out = _rank([(0.0, "w", wr), (0.0, "r", rb)], {"WR": 0.0, "RB": 0.0}, surv, rnd=3, partner_certain=True,
                best_now={"RB": 30.0, "WR": 50.0})
    assert out[0][2]["sleeper_id"] == "wr"
    assert out[0][1].count("STAGED (turn): pair band of 2, then higher floor") == 1
    assert all(p["_staged"]["mode"] == "turn" for _s, _w, p in out)


def test_staged_value_measures_a_flex_entrant_against_the_best_flex_fallback():
    needs = {"QB": 1, "RB": 0, "WR": 0, "TE": 1, "FLEX": 1}
    rb = _p("rb", "RB", 181.0)
    assert staged_value(rb, needs, FALLBACK) == 181.0 - max(FALLBACK["RB"], FALLBACK["WR"], FALLBACK["TE"])
    assert staged_value(rb, NEEDS, FALLBACK) == 181.0 - FALLBACK["RB"]


def test_without_a_report_the_pair_planner_alone_ranks():
    wr = _p("wr", "WR", 190.0)
    rb = _p("rb", "RB", 200.0)
    cands = [(30.0, "w", wr), (20.0, "r", rb)]
    out = staged_rank(cands, None, NEEDS, 3, {}, {}, {}, lambda pos: set(), fallback=FALLBACK, repl=REPL)
    assert [c[2]["sleeper_id"] for c in out] == ["wr", "rb"]
    assert all("STAGED" not in c[1] for c in out)
