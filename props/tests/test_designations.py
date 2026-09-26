"""The injury report's designations, and a scenario's assumed-out players.

The chat container runs pandas 3; this repo pins 1.5.3. A game where no
eligible player carries a designation gives an all-NaN status column, which
pandas types float64 -- and pandas 3 refuses the "Out (scenario)" string the
teammate-out scenario writes into it (found in the chat session logs,
2026-09-26). These tests pin the behaviour on either version.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "engine" / "scripts"))
pd = pytest.importorskip("pandas")
import score_game as SG  # noqa: E402


def _pop(statuses):
    return pd.DataFrame({"gsis_id": ["a", "b", "c"], "status": ["ACT", "ACT", "INA"],
                         "report_status": statuses})


def test_an_assumed_out_player_is_marked_even_when_nobody_carries_a_designation():
    pop = SG.apply_designations(_pop([np.nan, np.nan, np.nan]), {"a"})
    assert pop.loc[0, "report_status"] == "Out (scenario)"
    assert list(pop.excluded) == [True, False, True], "assumed out, active, inactive"
    assert not pop.questionable.any()


def test_the_report_decides_who_is_out_and_who_is_questionable():
    pop = SG.apply_designations(_pop(["Doubtful", "Questionable", None]))
    assert list(pop.excluded) == [True, False, True]
    assert list(pop.questionable) == [False, True, False]


def test_an_assumed_out_questionable_player_is_out_not_a_regime():
    pop = SG.apply_designations(_pop([np.nan, "Questionable", np.nan]), {"b"})
    assert pop.loc[1, "report_status"] == "Out (scenario)" and pop.loc[1, "excluded"]
    assert not pop.loc[1, "questionable"]
