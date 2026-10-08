"""In-season age decay (post-v2 item 4) — capped, gated, ROS-display only."""

from manager.age_decay import apply, decay_factor, note

CFG = {"enabled": True, "cap": 0.10, "per_year": 0.02}


def test_young_players_and_unknown_age_are_untouched():
    assert decay_factor("RB", 24, 10, CFG) == 1.0
    assert decay_factor("RB", None, 10, CFG) == 1.0
    assert decay_factor("WR", 29, 17, CFG) == 1.0        # below the WR threshold


def test_decay_grows_with_the_season_and_with_age():
    wk1 = decay_factor("RB", 32, 1, CFG)
    wk9 = decay_factor("RB", 32, 9, CFG)
    wk17 = decay_factor("RB", 32, 17, CFG)
    assert wk1 == 1.0                                    # nothing in week 1
    assert 1.0 > wk9 > wk17                              # grows across the year
    assert decay_factor("RB", 34, 17, CFG) < decay_factor("RB", 29, 17, CFG)


def test_cap_holds_for_an_extreme_case():
    assert decay_factor("RB", 45, 17, CFG) >= 1.0 - CFG["cap"] - 1e-9


def test_position_thresholds_rb_earliest():
    # a 31-year-old: past the RB and WR thresholds, not the QB one
    assert decay_factor("RB", 31, 17, CFG) < decay_factor("WR", 31, 17, CFG)
    assert decay_factor("QB", 31, 17, CFG) == 1.0


def test_off_switch():
    assert decay_factor("RB", 34, 17, {"enabled": False}) == 1.0


def test_apply_and_note():
    assert apply(None, "RB", 34, 17, CFG) is None
    v = apply(100.0, "RB", 34, 17, CFG)
    assert v is not None and v < 100.0
    assert "unvalidated" in note("RB", 34, 17, CFG)
    assert note("RB", 24, 17, CFG) == ""                 # silent when immaterial


def test_age_decay_is_opt_in():
    """Phase 1 item 3: an unvalidated adjustment that is on by default is on
    in leagues nobody chose it for."""
    assert decay_factor("RB", 31.0, 17, {}) == 1.0
    assert decay_factor("RB", 31.0, 17, None) == 1.0
    assert decay_factor("RB", 31.0, 17, {"enabled": True}) < 1.0
