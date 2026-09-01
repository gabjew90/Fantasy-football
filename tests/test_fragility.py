"""Standing contingency map (post-v2 item 3) — informational only."""

import polars as pl

from draftkit.fragility import add_contingency_map, fragility, label


def test_position_ordering_matches_research():
    # RB highest structural risk, QB lowest, same workload
    assert fragility("RB", 10) > fragility("TE", 10) > fragility("WR", 10) is not None
    assert fragility("WR", 10) > fragility("QB", 10)
    assert fragility("PK", 10) is None          # unknown position -> no guess


def test_workload_raises_fragility_most_for_rbs():
    # workload is SEASON high-value touches (RB p99 ~= 42, max 50)
    rb_lo, rb_hi = fragility("RB", 5), fragility("RB", 40)
    wr_lo, wr_hi = fragility("WR", 5), fragility("WR", 40)
    assert rb_hi - rb_lo > wr_hi - wr_lo        # RB workload term is heavier
    assert rb_hi - rb_lo > 0.2                  # and it actually discriminates
    assert fragility("RB", 200) == fragility("RB", 40)   # saturates


def test_injury_type_structural_beats_soft_tissue_beats_unknown():
    base = fragility("RB", 10)
    assert fragility("RB", 10, "Knee - ACL") > fragility("RB", 10, "Hamstring") > base
    assert fragility("RB", 10, "Undisclosed") == base    # unrecognised adds nothing


def test_labels():
    assert label(0.80) == "high" and label(0.60) == "moderate" and label(0.40) == "low"
    assert label(None) == ""


def test_map_identifies_the_incumbent_and_leaves_starters_empty():
    df = pl.DataFrame({
        "player": ["Star RB", "Backup RB", "Lone WR"],
        "sleeper_id": ["1", "2", "3"],
        "pos": ["RB", "RB", "WR"],
        "team": ["ATL", "ATL", "ATL"],
        "vorp": [90.0, 10.0, 50.0],
        "hv_touches": [45.0, 6.0, 20.0],
    })
    out = add_contingency_map(df, injury_part={"1": "Knee - ACL"})
    by = {r["player"]: r for r in out.iter_rows(named=True)}
    assert by["Backup RB"]["backs_up_pos"] == "Star RB"
    assert by["Backup RB"]["starter_fragility"] is not None
    assert by["Star RB"]["backs_up_pos"] is None          # the incumbent backs up nobody
    assert by["Lone WR"]["backs_up_pos"] is None          # no one above him
    # the ACL designation pushed the incumbent's fragility into 'high'
    assert by["Backup RB"]["starter_fragility_label"] == "high"


def test_module_never_touches_valuation():
    """Guard the informational constraint: the map adds columns, nothing else."""
    df = pl.DataFrame({
        "player": ["A", "B"], "sleeper_id": ["1", "2"], "pos": ["RB", "RB"],
        "team": ["SF", "SF"], "vorp": [50.0, 5.0], "hv_touches": [100.0, 10.0],
        "proj_pts": [200.0, 80.0], "tier": [1, 6],
    })
    out = add_contingency_map(df)
    for col in ("vorp", "proj_pts", "tier"):
        assert out[col].to_list() == df[col].to_list(), f"{col} was modified"


# ---------- Phase 1 item 2: body parts are not injury types ----------

def test_a_knee_bruise_no_longer_scores_like_a_torn_acl():
    """"knee" and "foot" were in STRUCTURAL until 2026-09-01, so any knee or
    foot mention took the full structural penalty."""
    from draftkit.fragility import fragility
    acl = fragility("RB", 300.0, "torn ACL")
    bruise = fragility("RB", 300.0, "knee bruise")
    assert acl > bruise
    assert bruise == fragility("RB", 300.0, None)


def test_ligament_tears_are_structural():
    from draftkit.fragility import fragility
    base = fragility("RB", 300.0, None)
    for desc in ("MCL sprain grade 3", "PCL tear", "meniscus surgery"):
        assert fragility("RB", 300.0, desc) > base, desc


def test_unrecognised_descriptions_still_contribute_nothing():
    from draftkit.fragility import fragility
    assert fragility("RB", 300.0, "sore") == fragility("RB", 300.0, None)
