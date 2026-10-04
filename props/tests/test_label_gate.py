"""The label gate (DECISIONS #144): the scorecard writes the model's weight
beside the book on settled yardage calls; the report's first line quotes it."""

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


def _calls(n, model_informative, seed=3):
    rng = np.random.default_rng(seed)
    p_book = rng.uniform(0.4, 0.6, n)
    truth = np.clip(p_book + rng.normal(0, 0.12, n), 0.05, 0.95)
    won = (rng.uniform(size=n) < truth).astype(float)
    p_model = truth if model_informative else np.clip(p_book + rng.normal(0, 0.12, n), 0.05, 0.95)
    return pd.DataFrame({"market": "player_receptions", "book": "sleeper", "p_model": p_model, "p_novig": p_book,
                         "won": won, "week": rng.integers(2, 6, n), "event_id": rng.integers(0, 60, n).astype(str)})


def test_the_gate_is_not_estimated_below_the_minimum():
    g = blend.yardage_gate(_calls(blend.MIN_CALLS - 1, True))
    assert g["estimated"] is False and g["gate_open"] is False and g["n_calls"] == blend.MIN_CALLS - 1


def test_the_gate_opens_only_when_the_model_carries_information():
    shut = blend.yardage_gate(_calls(2000, False), reps=200)
    assert shut["estimated"] and not shut["gate_open"], "a model that is noise around the book earns no weight"
    open_ = blend.yardage_gate(_calls(2000, True), reps=200)
    assert open_["estimated"] and open_["gate_open"] and open_["lo"] > 0


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
                                          "estimated": False, "gate_open": False}}
    s = SG.gate_sentence(thin)
    assert "current pricing model (props-v1.29) has 120 graded calls" in s and "too few to estimate" in s
    assert "Across every pricing model (weeks 2-3, 1180 calls) it is +0.03 (95% -0.45 to +0.56)" in s
    shut = {"pooled": pooled, "current": dict(pooled, engine="props-v1.25", n_calls=400, weeks=[3])}
    assert "Labels return only" in SG.gate_sentence(shut)
    # pooled clearing zero never opens the gate for a current model that has not
    opened_pool = {"pooled": dict(pooled, gate_open=True, lo=0.1), "current": thin["current"]}
    assert "OPEN" not in SG.gate_sentence(opened_pool)
    opened = {"pooled": pooled, "current": dict(shut["current"], gate_open=True, lo=0.1)}
    assert "label gate is OPEN" in SG.gate_sentence(opened)
    assert "No call has been graded yet" in SG.gate_sentence({"pooled": {"n_calls": 0}, "current": None})
    assert SG.research_statement(pd.DataFrame({"player": ["A"], "market": ["m"], "line": [1.5]}), shut) \
        .startswith("**1 lines priced.** A research sheet, not a bet list. Graded so far")


def test_the_current_model_is_the_latest_graded_one_and_empty_paths_refresh(tmp_path, monkeypatch):
    import persist
    monkeypatch.setattr(persist, "RECORD_ROOT", tmp_path)
    old = _calls(350, False).assign(week=3, model_id="old")
    new = _calls(320, False, seed=5).assign(week=4, model_id="new")
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
