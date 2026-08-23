"""Pure projection-composer math (season spec Task 3)."""

import pytest

from draftkit.weekly import compose, matchup_mult, shrunk_ratio, trend_adj


def test_shrinkage_early_season():
    # week 2 of data, shrink 5: a 1.6x defense reads as mild
    assert shrunk_ratio(1.6, weeks=2, shrink_weeks=5) == pytest.approx(1.171, abs=0.01)


def test_matchup_capped_both_ways():
    assert matchup_mult(2.5, weeks=10, cap=0.10, shrink_weeks=5) == pytest.approx(1.10)
    assert matchup_mult(0.2, weeks=10, cap=0.10, shrink_weeks=5) == pytest.approx(0.90)
    assert matchup_mult(None, weeks=10, cap=0.10, shrink_weeks=5) == 1.0


def test_trend_threshold_and_cap():
    assert trend_adj(0.05, cap=0.15, threshold=0.07) == 0.0     # under threshold: no adj
    assert trend_adj(0.12, cap=0.15, threshold=0.07) == pytest.approx(0.15)  # 0.24 capped
    assert trend_adj(-0.10, cap=0.15, threshold=0.07) == pytest.approx(-0.15)
    assert trend_adj(None, cap=0.15, threshold=0.07) == 0.0


def test_availability_gate_is_absolute():
    assert compose(20.0, 1.10, 0.15, "Out") == 0.0
    assert compose(20.0, 1.10, 0.15, "IR") == 0.0
    assert compose(20.0, 1.0, 0.0, "Questionable") == 20.0  # Q plays normally


def test_compose_bounded_stack():
    # 10 pts * 1.10 matchup * 1.15 trend = 12.65 — worst-case combined swing
    assert compose(10.0, 1.10, 0.15, "") == pytest.approx(12.65)
