"""Waiver claims engine (season spec Task 5)."""

import pytest

from draftkit.waivers import (bid_band, classify_contingencies, ir_actions,
                              protected_drop_ids, render_waiver_brief)

FAAB = {"league_winner": [0.40, 0.65], "breakout": [0.15, 0.35],
        "speculative": [0.05, 0.12], "streamer": [0.01, 0.03],
        "max_week_commit": 0.80}


def test_contingency_detection():
    rosters = {
        5: [{"sleeper_id": "s1", "name": "Star RB", "pos": "RB", "team": "SFO"}],
    }
    injury = {"s1": "Out"}
    fas = [
        {"sleeper_id": "b1", "name": "Backup RB", "pos": "RB", "team": "SFO", "ros": 60.0},
        {"sleeper_id": "x1", "name": "Other WR", "pos": "WR", "team": "SFO", "ros": 40.0},
        {"sleeper_id": "x2", "name": "Other RB", "pos": "RB", "team": "MIA", "ros": 50.0},
    ]
    claims = classify_contingencies(fas, rosters, injury)
    assert len(claims) == 1
    assert claims[0]["sleeper_id"] == "b1"
    assert "Star RB" in claims[0]["evidence"] and "Out" in claims[0]["evidence"]


def test_bid_band_regular_and_regime():
    fair, agg = bid_band("breakout", remaining_budget=80, regime="COMFORTABLE", faab=FAAB)
    assert (fair, agg) == (12, 28)  # 0.15*80, 0.35*80
    fair_b, agg_b = bid_band("breakout", remaining_budget=80, regime="BUBBLE", faab=FAAB)
    assert agg_b == 35  # 28 * 1.25 win-now multiplier
    fair_s, agg_s = bid_band("streamer", remaining_budget=80, regime="SAFE", faab=FAAB)
    assert fair_s >= 1  # never below $1


def test_league_winner_sealed_bid():
    # desperate rivals' max budget + 5, capped by fair-band hi and my budget
    fair, agg = bid_band("league_winner", remaining_budget=100, regime="BUBBLE",
                         faab=FAAB, rival_max_budget=41, value_cap=90)
    assert agg == 46  # 41 + 5, and 46 < 0.65*100*1.25
    _, agg2 = bid_band("league_winner", remaining_budget=100, regime="COMFORTABLE",
                       faab=FAAB, rival_max_budget=90, value_cap=100)
    assert agg2 == 65  # capped at the band hi (0.65 * 100), not 95


def test_drop_protections():
    bench = [
        {"sleeper_id": "h1", "name": "Handcuff", "pos": "RB", "ros": 10.0, "backs_up": "My Star"},
        {"sleeper_id": "d1", "name": "Deadweight", "pos": "WR", "ros": 5.0, "backs_up": None},
        {"sleeper_id": "ir1", "name": "IR Guy", "pos": "RB", "ros": 20.0, "backs_up": None},
    ]
    my_starters = {"My Star"}
    prot = protected_drop_ids(bench, my_starters, ir_occupants={"ir1"})
    assert prot == {"h1", "ir1"}  # handcuff of MY starter + IR occupant; deadweight droppable


def test_ir_both_directions():
    # empty slot + an Out player rostered -> move him in
    acts = ir_actions(ir_occupants=[], roster=[{"sleeper_id": "a", "name": "Hurt Guy"}],
                      injury={"a": "Out"}, reserve_allow=("Out", "Doubtful"))
    assert any("Hurt Guy" in a and "IR" in a for a in acts)
    # occupant upgraded past Doubtful -> forced exit warning
    acts2 = ir_actions(ir_occupants=[{"sleeper_id": "b", "name": "Healed Guy"}],
                       roster=[], injury={"b": "Questionable"},
                       reserve_allow=("Out", "Doubtful"))
    assert any("Healed Guy" in a and "must" in a.lower() for a in acts2)


def test_brief_renders_regime_and_commit_cap():
    model = {
        "week": 3, "record": "2-0", "odds": 0.7, "regime": "COMFORTABLE",
        "remaining_budget": 80, "ir_actions": ["Move X to IR"],
        "claims": [{"name": "Guy A", "pos": "RB", "cls": "breakout",
                    "evidence": "route share 41% -> 78%", "fair": 12, "aggressive": 28,
                    "drop": "Deadweight", "rivals_note": "2 RB-needy rivals hold $63, $12"}],
        "stale": [], "scoreboard_md": "",
    }
    md = render_waiver_brief(model)
    assert "COMFORTABLE" in md and "Guy A" in md and "$12–$28" in md and "Move X to IR" in md
