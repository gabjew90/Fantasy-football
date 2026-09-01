"""Season-level replay (scripts/season_replay.py) — the grader for bench value.

These cover the pure pieces: absence schedules, the wire pool, and one week's
lineup arithmetic. The independence property -- the grader draws from
empirical distributions and never from the constants in draftkit/bench.py --
is asserted directly, because the harness has been the broken thing twice.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import season_replay as SR  # noqa: E402

from draftkit import bench as B  # noqa: E402

SLOTS = {"QB": 1, "RB": 2, "WR": 2, "TE": 1, "FLEX": 1, "K": 1, "DEF": 1}
RATES = {"absent_weeks": {"QB": [0, 0, 1, 2], "RB": [0, 1, 2, 3, 6],
                          "WR": [0, 0, 1], "TE": [0, 1]},
         "handcuff_share": [0.5, 1.0, 1.5]}


def P(pid, pos, proj, adp=None, bye=None, backs_up="", team="XX"):
    return {"sleeper_id": pid, "name": pid, "pos": pos, "proj_pts": float(proj),
            "adp": adp, "bye": bye, "backs_up": backs_up, "team": team}


# ---------- absence schedules ----------

def test_bye_week_is_always_an_absence():
    p = P("a", "QB", 340.0, bye=7)
    for sim in range(5):
        assert 7 in SR.absence_schedule(p, sim, "t", RATES, {})


def test_bye_falls_back_to_the_team_schedule():
    p = P("a", "QB", 340.0, bye=None, team="KC")
    assert 9 in SR.absence_schedule(p, 0, "t", RATES, {"KC": 9})


def test_absences_are_drawn_from_the_position_distribution_not_the_player():
    """Two different players at the same position, same sim: different draws
    (keyed by player id) but both from the same positional distribution."""
    a = P("a", "RB", 200.0, bye=5)
    b = P("b", "RB", 200.0, bye=5)
    counts = set()
    for sim in range(40):
        sa = SR.absence_schedule(a, sim, "t", RATES, {})
        sb = SR.absence_schedule(b, sim, "t", RATES, {})
        counts.add(len(sa) - 1)
        counts.add(len(sb) - 1)
    assert counts <= set(RATES["absent_weeks"]["RB"])
    assert len(counts) > 1


def test_same_player_same_sim_is_identical_across_arms():
    """Common random numbers: the arm comparison must differ only in roster."""
    p = P("a", "RB", 200.0, bye=5)
    assert SR.absence_schedule(p, 3, "k", RATES, {}) == \
        SR.absence_schedule(p, 3, "k", RATES, {})


def test_positions_without_a_distribution_only_miss_their_bye():
    k = P("k", "K", 140.0, bye=4)
    assert SR.absence_schedule(k, 0, "t", RATES, {}) == {4}


# ---------- the wire ----------

def test_wire_pool_is_the_undrafted_top_2k():
    board = [P(f"q{i}", "QB", 300 - i * 10, adp=float(10 * i + 1)) for i in range(10)]
    board += [P("free", "QB", 200.0, adp=None)]
    pool = SR.wire_pool(board, last_pick=45, k=2)["QB"]
    names = [p["sleeper_id"] for p in pool]
    assert len(names) == 4
    assert all(p.get("adp") is None or p["adp"] > 45 for p in pool)
    assert names[0] == "q5"           # best projected of the undrafted


# ---------- one week ----------

def _roster():
    return [P("qb", "QB", 340.0), P("rb1", "RB", 255.0), P("rb2", "RB", 204.0),
            P("wr1", "WR", 238.0), P("wr2", "WR", 187.0), P("te", "TE", 170.0),
            P("flex", "WR", 153.0), P("k", "K", 136.0), P("def", "DEF", 119.0),
            P("cuff", "RB", 85.0, backs_up="rb1")]


def _no_absence(roster):
    return {p["sleeper_id"]: set() for p in roster}


def test_full_healthy_lineup_scores_every_starter_once():
    roster = _roster()
    wire = {pos: [] for pos in SR.STARTER_ORDER}
    total, from_wire = SR.week_points(roster, 1, _no_absence(roster), SLOTS, wire,
                                      {p["sleeper_id"] for p in roster}, 0, "t", RATES)
    expected = sum(p["proj_pts"] for p in roster if p["sleeper_id"] != "cuff") / 17
    assert abs(total - expected) < 1e-6
    assert from_wire == 0.0


def test_absent_starter_is_replaced_by_the_best_bench_option():
    roster = _roster()
    absent = _no_absence(roster)
    absent["rb2"] = {1}
    wire = {pos: [] for pos in SR.STARTER_ORDER}
    total, _ = SR.week_points(roster, 1, absent, SLOTS, wire,
                              {p["sleeper_id"] for p in roster}, 0, "t", RATES)
    # rb2 out -> cuff starts at RB (85/17) in place of 204/17
    healthy = sum(p["proj_pts"] for p in roster if p["sleeper_id"] != "cuff") / 17
    assert abs(total - (healthy - 204.0 / 17 + 85.0 / 17)) < 1e-6


def test_handcuff_inherits_the_starters_role_only_when_that_starter_is_out():
    roster = _roster()
    absent = _no_absence(roster)
    absent["rb1"] = {1}
    wire = {pos: [] for pos in SR.STARTER_ORDER}
    total, _ = SR.week_points(roster, 1, absent, SLOTS, wire,
                              {p["sleeper_id"] for p in roster}, 0, "t", RATES)
    healthy = sum(p["proj_pts"] for p in roster if p["sleeper_id"] != "cuff") / 17
    inherited = total - (healthy - 255.0 / 17)
    # a share drawn from {0.5, 1.0, 1.5} of rb1's 255/17
    assert any(abs(inherited - s * 255.0 / 17) < 1e-6 for s in RATES["handcuff_share"])


def test_empty_slot_goes_to_the_wire_and_is_counted_separately():
    roster = [p for p in _roster() if p["sleeper_id"] != "qb"]
    wire = {pos: [] for pos in SR.STARTER_ORDER}
    wire["QB"] = [P("stream", "QB", 221.0, adp=None)]
    total, from_wire = SR.week_points(roster, 1, _no_absence(roster), SLOTS, wire,
                                      {p["sleeper_id"] for p in roster}, 0, "t", RATES)
    assert abs(from_wire - 221.0 / 17) < 1e-6
    assert total > from_wire


# ---------- independence from the formula ----------

def test_grader_shares_no_constant_with_the_formula():
    """The formula uses means and a median; the grader must use only the
    exported distributions. If someone wires ABSENT_WEEKS or HANDCUFF_UPLIFT
    into season_replay, this is the test that should go red."""
    src = Path(SR.__file__).read_text(encoding="utf-8")
    assert "ABSENT_WEEKS" not in src
    assert "HANDCUFF_UPLIFT" not in src
    assert "insurance_value" not in src
    assert "from draftkit.bench import" not in src and "import draftkit.bench" not in src
    assert B.ABSENT_WEEKS  # the formula still has its own constants
