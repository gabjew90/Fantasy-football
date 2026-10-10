"""props/calc/matchup.py copies the props engine's unit grades (research.py:
unit_efficiency, tiers, tier_letter, tier_grade, _band_mod, unit_tiers). This test sits outside
props/calc, which may not import the engine (DECISIONS #231), and asserts both
versions give identical scores, bands and letters on the same play-by-play.
A change to either side fails it until the copy is brought back in line."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "props" / "engine" / "scripts"


@pytest.fixture(scope="module")
def both():
    sys.path.insert(0, str(ENGINE))
    try:
        import research
    finally:
        sys.path.remove(str(ENGINE))
    sys.path.insert(0, str(ROOT))
    from props.calc import matchup
    return research, matchup


def _plays(seed: int, n_teams: int = 32, n: int = 12000) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    teams = [f"T{i:02d}" for i in range(n_teams)]
    pos = rng.integers(0, n_teams, n)
    dfn = (pos + rng.integers(1, n_teams, n)) % n_teams
    is_pass = rng.random(n) < 0.58
    strength = rng.normal(0, 0.08, (n_teams, 2))           # each team's offense and defense, so the bands spread
    epa = rng.normal(0, 1.2, n) + strength[pos, 0] - strength[dfn, 1] + np.where(is_pass, 0.05, -0.03)
    return pd.DataFrame({
        "game_id": [f"g{(i // 150):04d}" for i in range(n)], "play_id": np.arange(n),
        "posteam": [teams[i] for i in pos], "defteam": [teams[i] for i in dfn],
        "pass": is_pass.astype(float), "rush": (~is_pass).astype(float),
        "play_type": np.where(is_pass, "pass", "run"), "epa": epa,
        "success": (epa > 0).astype(float), "wp": rng.random(n),
        "qb_kneel": (rng.random(n) < 0.01).astype(float), "qb_spike": (rng.random(n) < 0.005).astype(float),
    })


@pytest.mark.parametrize("seed", [1, 2, 3, 4])
def test_the_copied_grades_match_the_engine(both, seed):
    research, matchup = both
    p = _plays(seed)
    a, b = research.unit_efficiency(p, 0.10, 0.90), matchup.unit_efficiency(p, 0.10, 0.90)
    assert a["score"] == b["score"]
    ta, tb = research.unit_tiers(a), matchup.unit_tiers(b)
    assert ta.keys() == tb.keys()
    for key in ta:
        assert ta[key]["tier"] == tb[key]["tier"] and ta[key]["bands"] == tb[key]["bands"], key
        letters_a = {t: research.tier_letter(k) for t, k in ta[key]["tier"].items()}
        letters_b = {t: matchup.tier_letter(k) for t, k in tb[key]["tier"].items()}
        assert letters_a == letters_b and set(letters_a.values()) <= set("SABCDF")
        grades_a = {t: research.tier_grade(ta[key], t) for t in ta[key]["tier"]}
        grades_b = {t: matchup.tier_grade(tb[key], t) for t in tb[key]["tier"]}
        assert grades_a == grades_b and {g[1:] for g in grades_a.values()} <= {"", "+", "-"}


def test_the_copied_constants_match_the_engine(both):
    research, matchup = both
    for name in ("SCORE_EPA_WEIGHT", "TIER_STEPS", "MAX_TIERS", "TIER_LETTERS", "INT_STEPS"):
        assert getattr(research, name) == getattr(matchup, name), name


def test_the_copied_functions_are_the_engines_source_text(both):
    import inspect
    research, matchup = both
    for name in ("unit_efficiency", "tiers", "tier_letter", "tier_grade", "_band_mod", "unit_tiers"):
        assert inspect.getsource(getattr(research, name)) == inspect.getsource(getattr(matchup, name)), name


def test_band_mod_on_fractional_scores_matches(both):
    research, matchup = both
    vals = {f"T{i}": 50 + i * 0.37 for i in range(30)}             # not whole: the fractional branch
    ta, tb = research.tiers(vals), matchup.tiers(vals)
    assert {t: research.tier_grade(ta, t) for t in vals} == {t: matchup.tier_grade(tb, t) for t in vals}
