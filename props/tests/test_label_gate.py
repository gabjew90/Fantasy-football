"""The label gate (DECISIONS #144, #151): decided at the week 8/12/18 reviews
on the model's weight beside the book AND the top-tier calls' profit at
Sleeper's recorded prices; the report's first line quotes it."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROPS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROPS))
sys.path.insert(0, str(PROPS / "engine" / "scripts"))

import blend  # noqa: E402
import scorecard  # noqa: E402
import score_game as SG  # noqa: E402


def _calls(n, model_informative, seed=3, weeks=(2, 10)):
    rng = np.random.default_rng(seed)
    p_book = rng.uniform(0.4, 0.6, n)
    truth = np.clip(p_book + rng.normal(0, 0.12, n), 0.05, 0.95)
    won = (rng.uniform(size=n) < truth).astype(float)
    p_model = truth if model_informative else np.clip(p_book + rng.normal(0, 0.12, n), 0.05, 0.95)
    return pd.DataFrame({"market": "player_receptions", "book": "sleeper", "p_model": p_model, "p_novig": p_book,
                         "won": won, "week": rng.integers(*weeks, n), "event_id": rng.integers(0, 120, n).astype(str),
                         "tier": np.where(p_model - p_book > 0.05, "STRONG", "LEAN"),
                         "pnl_per_100": np.where(won == 1, 100 / 1.1, -100.0)})


def test_the_gate_is_not_estimated_below_the_minimum():
    g = blend.yardage_gate(_calls(blend.MIN_CALLS - 1, True))
    assert g["estimated"] is False and g["gate_open"] is False and g["n_calls"] == blend.MIN_CALLS - 1


def test_the_gate_opens_only_when_the_model_carries_information():
    shut = blend.yardage_gate(_calls(3000, False), reps=200)
    assert shut["estimated"] and not shut["gate_open"], "a model that is noise around the book earns no weight"
    open_ = blend.yardage_gate(_calls(3000, True), reps=200)
    assert open_["review_week"] == 8 and open_["next_review"] == 12
    ar = open_["at_review"]
    assert ar["weight_ok"] and ar["profit_ok"] and open_["gate_open"]
    assert ar["n_calls"] < open_["n_calls"], "the review reads the calls through week 8 only"


def test_no_review_reached_means_closed_however_strong_the_running_number():
    g = blend.yardage_gate(_calls(3000, True, weeks=(2, 8)), reps=200)    # weeks 2-7
    assert g["estimated"] and g["lo"] > 0, "the running weight clears zero"
    assert g["review_week"] is None and g["next_review"] == 8 and not g["gate_open"]


def test_weight_without_profit_keeps_the_gate_shut():
    d = _calls(3000, True)
    d["pnl_per_100"] = np.where(d.won == 1, 100 / 3, -100.0)     # the same calls at -300: the hold eats it
    g = blend.yardage_gate(d, reps=200)
    assert g["at_review"]["weight_ok"] and not g["at_review"]["profit_ok"] and not g["gate_open"]


def test_the_profit_condition_grades_sleeper_top_tier_calls_only():
    d = _calls(400, True)
    pr = blend.selection_profit(d)
    n_strong = int(((d.tier == "STRONG") & (d.book == "sleeper")).sum())
    assert pr["n_bets"] == n_strong
    d2 = d.assign(book="draftkings")
    assert blend.selection_profit(d2)["n_bets"] == 0
    assert blend.selection_profit(d.head(50))["estimated"] is False, "below MIN_BETS it is not judged"
    assert blend.selection_profit(d.drop(columns="tier"))["n_bets"] == 0


def test_the_scorecard_writes_the_gate_the_engine_reads(tmp_path, monkeypatch):
    import persist
    monkeypatch.setattr(persist, "RECORD_ROOT", tmp_path)
    df = _calls(400, False).assign(model_id="m1")
    gate = scorecard.write_label_gate(2026, df, [("m1", df)])
    on_disk = json.loads((tmp_path / scorecard.GATE_FILE).read_text(encoding="utf-8"))
    assert on_disk["pooled"]["n_calls"] == 400 and on_disk["engines"][0]["model_id"] == "m1"
    assert "| all models, pooled (context only) | 400 |" in "\n".join(scorecard.label_gate_md(gate))


def test_the_report_quotes_the_record_or_says_it_could_not_read_it():
    assert "could not be read" in SG.gate_sentence(None)
    pooled = {"n_calls": 1180, "weeks": [2, 3], "estimated": True, "gate_open": False,
              "w_model": 0.029, "lo": -0.452, "hi": 0.564}
    thin = {"pooled": pooled, "current": {"engine": "props-v1.29", "n_calls": 120, "weeks": [4],
                                          "estimated": False, "gate_open": False, "next_review": 8}}
    s = SG.gate_sentence(thin)
    assert "current pricing model (props-v1.29) has 120 graded calls" in s and "too few to estimate" in s
    assert "the next is after week 8" in s
    assert "Across every pricing model (weeks 2-3, 1180 calls) it is +0.03 (95% -0.45 to +0.56)" in s
    shut = {"pooled": pooled, "current": dict(pooled, engine="props-v1.25", n_calls=400, weeks=[3],
                                              next_review=8)}
    assert "no review has been reached" in SG.gate_sentence(shut) and "Labels return only" in SG.gate_sentence(shut)
    # a running weight above zero never opens the gate before a review
    assert "OPEN" not in SG.gate_sentence({"pooled": pooled, "current": dict(shut["current"], lo=0.1)})
    opened_pool = {"pooled": dict(pooled, gate_open=True, lo=0.1), "current": thin["current"]}
    assert "OPEN" not in SG.gate_sentence(opened_pool)
    w = {"estimated": True, "w_model": 0.4, "lo": 0.1, "hi": 0.7}
    pr = {"estimated": True, "net_per_100": 6.2, "lo": 0.8, "hi": 11.5, "n_bets": 240}
    review = dict(shut["current"], weeks=list(range(2, 10)), next_review=12,
                  at_review={"week": 8, "n_calls": 900, "weight": w, "profit": pr})
    s = SG.gate_sentence({"pooled": pooled, "current": dict(review, gate_open=True)})
    assert "At the week-8 review" in s and "+6.2 per $100" in s and "label gate is OPEN until the next review" in s
    lost = dict(review, at_review=dict(review["at_review"], profit=dict(pr, net_per_100=-3.0, lo=-9.0, hi=2.9)))
    s = SG.gate_sentence({"pooled": pooled, "current": lost})
    assert "OPEN" not in s and "-3.0 per $100" in s and "the next is after week 12" in s
    assert "No call has been graded yet" in SG.gate_sentence({"pooled": {"n_calls": 0}, "current": None})
    assert SG.research_statement(pd.DataFrame({"player": ["A"], "market": ["m"], "line": [1.5]}), shut) \
        .startswith("**1 lines priced.** A research sheet, not a bet list. Graded so far")


def test_the_current_model_is_the_latest_graded_one_and_empty_paths_refresh(tmp_path, monkeypatch):
    import persist
    monkeypatch.setattr(persist, "RECORD_ROOT", tmp_path)
    old = _calls(350, False).assign(week=3, model_id="old")
    new = _calls(320, False, seed=5).assign(week=4, model_id="new")
    assert "first after week 8" in "\n".join(scorecard.label_gate_md(scorecard.write_label_gate(
        2026, new, [("new", new)])))
    gate = scorecard.write_label_gate(2026, pd.concat([old, new]), [("old", old), ("new", new)])
    assert gate["current"]["model_id"] == "new"
    empty = scorecard.write_label_gate(2027, pd.DataFrame(), [])
    assert empty["current"] is None and empty["pooled"]["n_calls"] == 0


def test_the_scorecard_grades_the_calls_the_snap_rule_moved():
    df = pd.DataFrame({"market": ["player_receptions"] * 4 + ["player_rush_yds"],
                       "snap_react": [1.2, 1.1, 0.8, 1.0, 1.3], "won": [1, 0, 1, 1, 0],
                       "p_model": [0.6] * 5, "p_novig": [0.5] * 5, "miss": [-1.0, -0.5, 0.5, 0.0, 9.0]})
    md = "\n".join(scorecard.snap_rule_section(df))
    assert "| catches | raised | 2 | 50.0% | 60.0% | 50.0% | -0.75 |" in md
    assert "| catches | lowered | 1 |" in md and "| catches | not moved | 1 |" in md
    assert "rush" not in md, "rushing calls are not the rule's"
    assert scorecard.snap_rule_section(df.drop(columns="snap_react")) == [], "records before the field: no section"


def test_a_model_first_used_after_a_review_week_waits_for_the_next_one():
    late = _calls(3000, True, weeks=(10, 12))           # weeks 10-11 only
    g = blend.yardage_gate(late, reps=200)
    assert g["review_week"] is None and g["next_review"] == 12 and not g["gate_open"]
    g = blend.yardage_gate(_calls(3000, True, weeks=(10, 13)), reps=200)   # weeks 10-12
    assert g["review_week"] == 12


def test_the_scorecard_grades_each_mark_on_its_own_side():
    df = pd.DataFrame({"market": ["player_rush_yds"] * 3, "side": ["Over", "Under", "Under"],
                       "look": ["Under", "Under", None], "won": [1, 1, 0],
                       "price_over": [-130] * 3, "price_under": [-125] * 3})
    md = "\n".join(scorecard.look_section(df))
    # row 1: model side Over won, so the marked Under LOST; row 2: marked Under won at -125
    assert "| rush_yds | 2 | 1 | 50% | 56% | -10.0 |" in md
    assert scorecard.look_section(df.drop(columns="look")) == []


def test_each_review_uses_the_three_look_level_and_its_interval_is_wider():
    """DECISIONS #180: three reviews share one 5% -- each review's intervals are at
    1 - 0.05/3 = 98.3%, so they nest around the running 95% interval on the same calls."""
    assert abs(blend.GATE_LEVEL - (1 - 0.05 / 3)) < 1e-12 and len(blend.REVIEW_WEEKS) == 3
    d = _calls(3000, True, weeks=(2, 9))                 # every call is through the week 8 review
    g = blend.yardage_gate(d, reps=400)
    w = g["at_review"]["weight"]
    assert w["level"] == blend.GATE_LEVEL and g["level"] == 0.95
    assert w["lo"] <= g["lo"] and w["hi"] >= g["hi"], "same calls, same draws: the 98.3% interval holds the 95%"
    assert g["at_review"]["profit"]["level"] == blend.GATE_LEVEL
    lines = scorecard.label_gate_md({"engines": [], "pooled": g})
    assert "98.3%" in lines[2] and "share one 5%" in lines[2]
