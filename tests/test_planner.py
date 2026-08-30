"""Two-pick joint planner (v2 item 1.2) — the Flowers-seam regression test."""

from draftkit.planner import pair_rank


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


def test_joint_pair_flips_the_flowers_seam():
    ranked = pair_rank(_cands(), REPORT, NEEDS, SECOND, {"RB", "WR"})
    # WR pair: 84 + min? partner RB 71 -> 155;  RB pair: 78.5 + 66 = 144.5
    assert ranked[0][2]["sleeper_id"] == "flowers"
    assert "two-pick plan" in ranked[0][1]


def test_same_position_partner_uses_second_best_now():
    cands = [(9.0, "why", {"pos": "RB", "vorp": 90.0, "sleeper_id": "a"})]
    cands.append((1.0, "why", {"pos": "WR", "vorp": 20.0, "sleeper_id": "w"}))
    report = {"RB": {"e_best_next": 88.0}, "WR": {"e_best_next": 10.0}}
    ranked = pair_rank(cands, report, {"RB": 2, "FLEX": 2}, {"RB": 60.0, "WR": 15.0},
                       {"RB", "WR"})
    # RB-RB pair may not claim 88 twice: partner capped at second-best 60
    assert ranked[0][2]["sleeper_id"] == "a"
    assert abs(ranked[0][0] - 150.0) < 0.01  # 90 + 60, not 90 + 88


def test_no_report_means_greedy_fallback():
    cands = _cands()
    assert pair_rank(cands, None, NEEDS, SECOND, {"RB", "WR"}) == cands


def test_ineligible_next_positions_are_never_partners():
    cands = [(5.0, "w", {"pos": "WR", "vorp": 50.0, "sleeper_id": "x"}),
             (4.0, "q", {"pos": "QB", "vorp": 45.0, "sleeper_id": "q"})]
    report = {"WR": {"e_best_next": 40.0}, "QB": {"e_best_next": 44.0}}
    ranked = pair_rank(cands, report, {"WR": 1, "QB": 0, "FLEX": 1},
                       {"WR": 35.0, "QB": 40.0}, eligible_next={"WR"})
    # QB is guardrailed out of the next pick, so no candidate pairs with it
    assert all("QB expected" not in why for _s, why, _p in ranked)
