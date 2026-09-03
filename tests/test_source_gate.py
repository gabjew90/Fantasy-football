"""The gate's arithmetic (DECISIONS #23) must be right before its verdict is
trusted: pooled accuracy, one shared rival list for both arms, actual-points
grading, and the pre-registered decision rule at its boundaries."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("sg", ROOT / "scripts" / "source_gate.py")
sg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sg)


def _rows():
    # two cells (one pair, two positions); the 'lines' arm is exactly right at
    # RB and off by a constant 10 at WR; blend is off by 20 everywhere.
    rb = [("a", "RB", 100.0), ("b", "RB", 200.0), ("c", "RB", 300.0)]
    wr = [("d", "WR", 50.0), ("e", "WR", 150.0), ("f", "WR", 250.0)]
    recs = []
    for name, pos, act in rb + wr:
        recs.append({"pair": "2024->2025", "sleeper_id": name, "name": name, "pos": pos, "adp": 1.0,
                     "usage": act, "curve": act, "blend": act + 20,
                     "lines": act if pos == "RB" else act + 10, "actual": act})
    # a row one arm did not project is excluded from the common set
    recs.append({"pair": "2024->2025", "sleeper_id": "z", "name": "z", "pos": "RB", "adp": 1.0,
                 "usage": None, "curve": 1.0, "blend": 1.0, "lines": 1.0, "actual": 999.0})
    return pl.DataFrame(recs)


def test_pooled_accuracy_pools_mae_and_weights_spearman_by_n():
    a = sg.pooled_accuracy(_rows())
    assert a["n"] == 6
    assert abs(a["blend_mae"] - 20.0) < 1e-9
    assert abs(a["lines_mae"] - 5.0) < 1e-9          # (0*3 + 10*3) / 6
    assert abs(a["blend_rho"] - 1.0) < 1e-9 and abs(a["lines_rho"] - 1.0) < 1e-9
    assert a["pass"] is True and abs(a["mae_ratio"] - 0.25) < 1e-9


def test_pooled_accuracy_fails_on_either_threshold():
    rows = _rows().with_columns(pl.col("actual").alias("blend"),                 # model exactly right
                                (pl.col("actual") * 1.5).alias("lines"))
    assert sg.pooled_accuracy(rows)["pass"] is False
    # reversed ranks fail on Spearman even with tolerable MAE
    rows2 = _rows().with_columns((pl.col("actual") + 20).alias("blend"),
                                 (400 - pl.col("actual") + 20).alias("lines"))
    assert sg.pooled_accuracy(rows2)["pass"] is False


def test_grade_actual_fills_slots_then_flex_on_actual_points_and_ignores_kdef():
    slots = {"QB": 1, "RB": 1, "WR": 1, "FLEX": 1}
    chosen = [{"name": n, "pos": p} for n, p in
              [("q1", "QB"), ("q2", "QB"), ("r1", "RB"), ("r2", "RB"), ("w1", "WR"), ("t1", "TE"), ("k", "K")]]
    actual = {"q1": 300, "q2": 350, "r1": 100, "r2": 180, "w1": 90, "t1": 120, "k": 500}
    # QB 350, RB 180, WR 90, FLEX = best of r1 100 / t1 120 -> 120; K ignored
    assert sg.grade_actual(chosen, actual, slots) == 350 + 180 + 90 + 120


def test_rival_order_is_the_whole_pool_by_adp_regardless_of_arm_coverage():
    rows = pl.DataFrame({"name": ["b", "a", "c", "d"], "adp": [2.0, 1.0, None, 3.0],
                         "blend": [1.0, 1.0, 1.0, 1.0], "lines": [1.0, None, 1.0, 1.0]})
    assert sg.rival_order(rows) == ["a", "b", "d"]     # 'a' is unlined but still a rival pick


class _StubTracker:
    """Recommends the highest-VORP available player; records nothing else."""

    def __init__(self, board, picks):
        taken = {str(p["player_id"]) for p in picks}
        self.avail = [p for p in board if p["sleeper_id"] not in taken]

    def recommendations(self, top_n=1):
        best = max(self.avail, key=lambda p: p["vorp"])
        return [(best["vorp"], "stub", best)]


def test_adp_replay_rivals_follow_the_shared_list_even_off_our_board(monkeypatch):
    """Review 2026-09-02: rivals used to draft from each arm's own board, so
    an arm that never projected McCaffrey faced rivals who never took him."""
    board = [{"sleeper_id": str(i), "name": f"p{i}", "pos": "RB", "adp": float(i), "vorp": 100.0 - i}
             for i in range(2, 9)]                   # p1 is NOT on our board
    board[4]["vorp"] = 500.0                        # p6: ADP 6 but the engine's favourite
    rivals = [f"p{i}" for i in range(1, 9)]         # the shared pool includes p1
    monkeypatch.setattr(sg.EP, "make_tracker", lambda board, picks, my_slot, **kw: _StubTracker(board, picks))
    chosen, errors = sg.adp_replay(board, rivals, my_slot=2, teams=3, rounds=2, slots={"RB": 2})
    # 3 teams, snake: 1:s1 2:s2 3:s3 4:s3 5:s2 6:s1
    # s1 takes p1 (off our board, still gone); we take p6; s3 takes p2, p3; we take p4; s1 takes p5
    assert [p["name"] for p in chosen] == ["p6", "p4"] and errors == 0


def test_verdict_rule_at_the_boundaries():
    acc_ok = {"k": {"pass": True}, "o": {"pass": True}}
    acc_bad = {"k": {"pass": True}, "o": {"pass": False}}
    assert sg.verdict(acc_ok, {"pass": True})["decision"] == "flip"
    assert sg.verdict(acc_bad, {"pass": False})["decision"] == "stay"
    assert sg.verdict(acc_ok, {"pass": False})["decision"] == "split"
    assert sg.verdict(acc_bad, {"pass": True})["decision"] == "split"


def test_outcome_summary_threshold_is_one_percent_of_the_model_mean():
    def pairs(ext):
        return [{"league": "k", "pair": "x", "slots": [{"blend": 1000.0, "lines": ext}]}]
    assert sg.summarize_outcome(pairs(990.0))["pass"] is True
    assert sg.summarize_outcome(pairs(989.0))["pass"] is False


def test_dedupe_names_suffixes_only_true_collisions():
    rows = pl.DataFrame({"pair": ["a", "a", "b"], "sleeper_id": ["1", "2", "3"],
                         "name": ["Mike Williams", "Mike Williams", "Mike Williams"]})
    out = sg.dedupe_names(rows).sort("sleeper_id")["name"].to_list()
    assert out == ["Mike Williams (1)", "Mike Williams (2)", "Mike Williams"]


def test_skill_shape_reads_the_league_yaml_and_drops_kdef():
    from draftkit.config import Config
    teams, rounds, slots = sg.skill_shape(Config.load(league="omnibeta"))
    assert (teams, rounds) == (12, 13)
    assert slots == {"QB": 1, "RB": 2, "WR": 2, "TE": 1, "FLEX": 2}
    teams, rounds, slots = sg.skill_shape(Config.load(league="keefamania"))
    assert (teams, rounds, slots["FLEX"]) == (10, 13, 1)


def test_gate_generalises_to_a_candidate_against_several_rivals():
    """Plan A1: pass only when the candidate is not worse than EVERY rival;
    the #23 defaults (lines vs blend) read exactly as before."""
    rows = _rows().with_columns(pl.col("actual").alias("curve"))          # a perfect third arm
    a = sg.pooled_accuracy(rows, candidate="lines", rivals=("blend", "curve"))
    assert a["vs"]["blend"]["pass"] is True and a["vs"]["curve"]["pass"] is False and a["pass"] is False
    assert a["mae_ratio"] == a["vs"]["blend"]["mae_ratio"]                # first rival keeps the #23 keys
    d = sg.pooled_accuracy(_rows())
    assert d["candidate"] == "lines" and d["rivals"] == ["blend"] and d["pass"] is True
    pairs = [{"league": "k", "pair": "x", "slots": [{"blend": 1000.0, "lines": 995.0, "curve": 1010.0,
                                                      "usage": 900.0}]}]
    s = sg.summarize_outcome(pairs, candidate="lines", rivals=("blend", "curve"))
    assert s["vs"]["blend"]["pass"] is True and s["vs"]["curve"]["pass"] is False and s["pass"] is False
    s2 = sg.summarize_outcome(pairs, candidate="lines", rivals=("blend", "usage"))
    assert s2["pass"] is True and s2["model_mean"] == 1000.0


def test_an_arm_named_like_a_legacy_key_keeps_its_own_value():
    """Regression (2026-09-02): the games-table gate judged `lines_gt` against
    `lines`. The old #23 alias keys (blend / lines) overwrote the rival's own
    grade with the candidate's, so the outcome summary compared the candidate
    with itself and reported 44 ties. Every value is keyed by arm name only."""
    rows = _rows().with_columns((pl.col("lines") * 1.10).alias("lines_gt"))
    a = sg.pooled_accuracy(rows, candidate="lines_gt", rivals=("lines",))
    assert a["lines_mae"] != a["lines_gt_mae"]
    assert a["mae_ratio"] == a["lines_gt_mae"] / a["lines_mae"]
    pairs = [{"league": "k", "pair": "x", "slots": [{"lines": 1000.0, "lines_gt": 900.0, "blend": 1200.0}]}]
    s = sg.summarize_outcome(pairs, candidate="lines_gt", rivals=("lines",))
    assert (s["model_mean"], s["ext_mean"], s["worse"], s["tied"]) == (1000.0, 900.0, 1, 0)
    assert s["pass"] is False
