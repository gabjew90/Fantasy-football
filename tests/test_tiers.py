from draftkit.tiers import assign_tiers


def test_flat_values_single_tier():
    tiers, cliffs = assign_tiers([10.0, 9.9, 9.8, 9.7])
    assert tiers == [1, 1, 1, 1]
    assert not any(cliffs)


def test_big_gap_starts_new_tier_and_flags_cliff():
    values = [100.0, 99.0, 98.0, 70.0, 69.0, 68.0]
    tiers, cliffs = assign_tiers(values, break_z=0.5, cliff_z=1.0)
    assert tiers[:3] == [1, 1, 1]
    assert tiers[3:] == [2, 2, 2]
    assert cliffs[2]  # last player before the drop carries the flag
    assert not cliffs[3]


def test_empty_and_single():
    assert assign_tiers([]) == ([], [])
    assert assign_tiers([5.0]) == ([1], [False])


def test_monotone_tier_numbers():
    values = [50, 45, 44, 30, 29, 10, 9]
    tiers, _ = assign_tiers([float(v) for v in values])
    assert all(tiers[i] <= tiers[i + 1] for i in range(len(tiers) - 1))
