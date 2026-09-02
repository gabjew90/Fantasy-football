"""The gate's arithmetic (DECISIONS #23) must be right before its verdict is
trusted: pooled accuracy, ADP-order rivals, actual-points grading, and the
pre-registered decision rule at its boundaries."""

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
                                (pl.col("actual") * 1.5).alias("lines"))           # external 50% MAE... ratio inf
    a = sg.pooled_accuracy(rows)
    assert a["pass"] is False
    # reversed ranks fail on Spearman even with tolerable MAE
    rows2 = _rows().with_columns((pl.col("actual") + 20).alias("blend"),
                                 (400 - pl.col("actual") + 20).alias("lines"))
    assert sg.pooled_accuracy(rows2)["pass"] is False


def test_lineup_actual_fills_slots_then_flex_and_ignores_kdef():
    slots = {"QB": 1, "RB": 1, "WR": 1, "FLEX": 1}
    chosen = [{"name": n, "pos": p} for n, p in
              [("q1", "QB"), ("q2", "QB"), ("r1", "RB"), ("r2", "RB"), ("w1", "WR"), ("t1", "TE"), ("k", "K")]]
    actual = {"q1": 300, "q2": 350, "r1": 100, "r2": 180, "w1": 90, "t1": 120, "k": 500}
    # QB 350, RB 180, WR 90, FLEX = best of r1 100 / t1 120 -> 120; K ignored
    assert sg.lineup_actual(chosen, actual, slots) == 350 + 180 + 90 + 120


class _StubTracker:
    """Recommends the highest-VORP available player; records nothing else."""

    def __init__(self, board, picks):
        taken = {str(p["player_id"]) for p in picks}
        self.avail = [p for p in board if p["sleeper_id"] not in taken]

    def recommendations(self, top_n=1):
        best = max(self.avail, key=lambda p: p["vorp"])
        return [(best["vorp"], "stub", best)]


def test_adp_replay_rivals_take_adp_order_and_we_take_the_engine_pick(monkeypatch):
    board = [{"sleeper_id": str(i), "name": f"p{i}", "pos": "RB", "adp": float(i), "vorp": 100.0 - i}
             for i in range(1, 9)]
    board[5]["vorp"] = 500.0          # p6: ADP 6 but the engine's favourite
    monkeypatch.setattr(sg.EP, "make_tracker", lambda board, picks, my_slot, **kw: _StubTracker(board, picks))
    chosen, errors = sg.adp_replay(board, my_slot=2, teams=3, rounds=2, slots={"RB": 2})
    # pick order (3 teams, snake): 1:s1 2:s2 3:s3 4:s3 5:s2 6:s1
    # s1 takes p1; we take p6; s3 takes p2 then p3; we take p4 (best vorp left); s1 takes p5
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
