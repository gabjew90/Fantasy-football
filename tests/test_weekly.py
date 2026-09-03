"""Pure projection-composer math (season spec Task 3)."""

import pytest

from draftkit.weekly import compose, matchup_mult, shrunk_ratio


def test_shrinkage_early_season():
    # week 2 of data, shrink 5: a 1.6x defense reads as mild
    assert shrunk_ratio(1.6, weeks=2, shrink_weeks=5) == pytest.approx(1.171, abs=0.01)


def test_matchup_capped_both_ways():
    assert matchup_mult(2.5, weeks=10, cap=0.10, shrink_weeks=5) == pytest.approx(1.10)
    assert matchup_mult(0.2, weeks=10, cap=0.10, shrink_weeks=5) == pytest.approx(0.90)
    assert matchup_mult(None, weeks=10, cap=0.10, shrink_weeks=5) == 1.0


def test_availability_gate_is_absolute():
    assert compose(20.0, 1.10, 0.15, "Out") == 0.0
    assert compose(20.0, 1.10, 0.15, "IR") == 0.0
    assert compose(20.0, 1.0, 0.0, "Questionable") == 20.0  # Q plays normally


def test_compose_bounded_stack():
    # 10 pts * 1.10 matchup * 1.15 adj = 12.65 — worst-case combined swing
    assert compose(10.0, 1.10, 0.15, "") == pytest.approx(12.65)
