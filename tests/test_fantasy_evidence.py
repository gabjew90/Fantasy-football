"""The usage evidence table and its noise bands."""

from __future__ import annotations

import math

import pandas as pd
import pytest

from fantasy import evidence as EV


def _play(week, team, kind, who, ay=0.0, yl=50, secs=900, **kw):
    base = {"season": 2026, "week": week, "season_type": "REG", "posteam": team, "pass_attempt": 0,
            "rush_attempt": 0, "receiver_player_id": None, "rusher_player_id": None, "air_yards": None,
            "yardline_100": yl, "half_seconds_remaining": secs, "qb_kneel": 0, "sack": 0, "two_point_attempt": 0}
    if kind == "tgt":
        base.update(pass_attempt=1, receiver_player_id=who, air_yards=ay)
    else:
        base.update(rush_attempt=1, rusher_player_id=who)
    base.update(kw)
    return base


def test_usage_counts_targets_carries_air_yards_and_inside_ten():
    pbp = pd.DataFrame([
        _play(1, "ATL", "tgt", "wr", ay=20), _play(1, "ATL", "tgt", "wr", ay=10, yl=8),
        _play(1, "ATL", "tgt", "rb", ay=-2), _play(1, "ATL", "tgt", "wr", ay=5, sack=1),   # a sack: not a target
        _play(1, "ATL", "car", "rb", yl=5), _play(1, "ATL", "car", "rb", secs=60),
        _play(1, "ATL", "car", "qb", qb_kneel=1),                                        # a kneel: not a carry
        _play(1, "ATL", "tgt", "wr", ay=30, two_point_attempt=1),                        # a 2-pt try: out
    ])
    u = EV.usage_from_pbp(pbp).set_index("gsis_id")
    assert u.loc["wr", "targets"] == 2 and u.loc["rb", "targets"] == 1
    assert u.loc["wr", "tgt_share"] == pytest.approx(2 / 3)
    # shares use air yards floored at zero (a screen-heavy week cannot push a share past 100%);
    # aDOT keeps the raw value
    assert u.loc["wr", "ay_share"] == pytest.approx(30 / 30) and u.loc["rb", "ay_share"] == 0.0
    assert u.loc["wr", "adot"] == pytest.approx(15.0) and u.loc["rb", "adot"] == pytest.approx(-2.0)
    assert u.loc["wr", "wopr"] == pytest.approx(1.5 * 2 / 3 + 0.7 * 1.0)
    assert u.loc["rb", "carries"] == 2 and u.loc["rb", "carry_share"] == 1.0 and "qb" not in u.index
    assert u.loc["wr", "i10_tgt"] == 1 and u.loc["rb", "i10_car"] == 1
    assert u.loc["rb", "two_min"] == 1


def test_snap_counts_join_by_pfr_id_and_keep_a_blocker_with_no_touch():
    u = EV.usage_from_pbp(pd.DataFrame([_play(1, "ATL", "tgt", "g1", ay=5)]))
    snaps = pd.DataFrame([
        {"season": 2026, "week": 1, "team": "ATL", "game_type": "REG", "pfr_player_id": "P1", "offense_snaps": 50,
         "offense_pct": 0.8},
        {"season": 2026, "week": 1, "team": "ATL", "game_type": "REG", "pfr_player_id": "P2", "offense_snaps": 30,
         "offense_pct": 0.5},                                                       # a blocking TE, no target
        {"season": 2026, "week": 1, "team": "ATL", "game_type": "REG", "pfr_player_id": "P3", "offense_snaps": 0,
         "offense_pct": 0.0}])
    out = EV.with_snaps(u, snaps, {"P1": "g1", "P2": "g2", "P3": "g3"}).set_index("gsis_id")
    assert out.loc["g1", "snap_pct"] == 0.8 and out.loc["g2", "snap_pct"] == 0.5
    assert out.loc["g2", "targets"] == 0 and "g3" not in out.index


def test_a_role_change_must_beat_the_noise():
    sd = 0.05
    steady = EV.role_change([0.20, 0.22, 0.19, 0.21, 0.20], sd)
    assert steady["changed"] is False
    jump = EV.role_change([0.10, 0.12, 0.11, 0.30, 0.32], sd)
    assert jump["changed"] is True and jump["diff"] == pytest.approx(0.31 - 0.11, abs=1e-3)
    assert jump["z"] == pytest.approx(0.2 / (sd * math.sqrt(1 / 2 + 1 / 3)), rel=1e-2)
    assert EV.role_change([0.1, 0.2, 0.3], sd) is None, "three weeks is an insufficient sample"
    assert EV.role_change([0.1, 0.2, 0.3, 0.4], None) is None, "no band, no verdict"


def test_bands_measure_spread_around_each_players_own_mean():
    rows = []
    for g, level in (("a", 0.2), ("b", 0.4)):
        for w in range(1, 11):
            rows.append({"gsis_id": g, "week": w, "tgt_share": level + (0.02 if w % 2 else -0.02),
                         "snap_pct": 0.8, "ay_share": 0.1, "wopr": 0.3, "carry_share": 0.0})
    rows.append({"gsis_id": "c", "week": 1, "tgt_share": 0.9, "snap_pct": 0.1, "ay_share": 0.1, "wopr": 0.1,
                 "carry_share": 0.0})                                           # too few weeks: out of the fit
    b = EV.fit_bands(pd.DataFrame(rows), {"a": "WR", "b": "WR", "c": "WR"})
    assert b["WR"]["tgt_share"]["players"] == 2
    # robust: 1.4826 x MAD of residuals +-0.02 (never below half the classical SD)
    assert b["WR"]["tgt_share"]["sd"] == pytest.approx(1.4826 * 0.02, abs=1e-4)


def test_only_role_defining_metrics_are_flagged():
    usage = pd.DataFrame([{"gsis_id": "te", "week": w, "team": "DET", "snap_pct": 0.8, "tgt_share": 0.15,
                           "ay_share": 0.1, "wopr": 0.3, "carry_share": (0.0 if w < 4 else 0.3), "adot": 7.0,
                           "i10_tgt": 0, "i10_car": 0, "two_min": 0, "targets": 5, "carries": 0}
                          for w in range(1, 6)])
    bands = {"TE": {m: {"sd": 0.01} for m in EV.BAND_METRICS}}
    e = EV.evidence_for(["te"], usage, {"te": "TE"}, bands)["te"]
    assert "carry_share" not in e["role_change"], "carries do not define a tight end's role"
    assert e["trajectory"] == "STABLE"


def test_the_shipped_bands_passed_their_stability_check():
    import json
    d = json.loads((EV.RESOURCES / f"{EV.NAME}.json").read_text(encoding="utf-8"))
    assert d["validation"]["passed"] and d["fit_season"] < d["test_season"]
    for pos, ms in EV.ROLE_METRICS.items():
        for m in ms:
            assert abs(d["stability"][pos][m] - 1) <= 0.2, (pos, m)
            assert d["bands"][pos][m]["z"] > 0, (pos, m)
            assert d["false_alarm_rate"][pos][m] <= 0.10, (pos, m)


def test_the_band_follows_the_players_usage_level():
    band = {"sd": 0.10, "by_level": [{"lo": 0.0, "hi": 0.15, "sd": 0.03, "n": 200},
                                     {"lo": 0.15, "hi": 1.01, "sd": 0.12, "n": 200}]}
    assert EV.band_sd(band, 0.08) == 0.03 and EV.band_sd(band, 0.5) == 0.12
    assert EV.band_sd({"sd": 0.1}, 0.5) == 0.1 and EV.band_sd(0.07, None) == 0.07
    # the review's case: a backup going 10% -> 25% of carries is judged on the backup's noise
    rc = EV.role_change([0.10, 0.09, 0.11, 0.25, 0.26], dict(band, z=2.5))
    assert rc["changed"] and rc["sd"] == 0.03


def test_a_missing_recent_week_is_insufficient_not_shifted():
    assert EV.role_change([0.2, 0.2, 0.2, None, 0.5], 0.05) is None
    assert EV.role_change([0.2, None, 0.2, 0.2, 0.2], 0.05) is not None, "a gap in the EARLIER weeks is fine"


def test_thresholds_are_calibrated_to_the_target_false_alarm_rate():
    import numpy as np
    zs = {"WR": {"tgt_share": list(np.linspace(0, 5, 101))}}
    cal = EV.calibrate({"WR": {"tgt_share": {"sd": 0.05}}}, zs, target=0.05)
    assert cal["WR"]["tgt_share"]["z"] == pytest.approx(4.75, abs=0.01)
    far = EV.false_alarm_rate(zs, cal)
    assert far["WR"]["tgt_share"] == pytest.approx(0.05, abs=0.011)


def test_a_partial_game_is_marked_not_hidden():
    rows = [{"gsis_id": "wr", "week": w, "team": "DET", "snap_pct": sp, "tgt_share": ts, "ay_share": 0.2,
             "wopr": 0.4, "carry_share": 0.0, "adot": 9.0, "i10_tgt": 0, "i10_car": 0, "two_min": 0,
             "targets": 5, "carries": 0}
            for w, sp, ts in ((1, 0.9, 0.25), (2, 0.9, 0.25), (3, 0.9, 0.25), (4, 0.1, 0.02), (5, 0.9, 0.05))]
    bands = {"WR": {m: {"sd": 0.01, "z": 2.0} for m in EV.BAND_METRICS}}
    e = EV.evidence_for(["wr"], pd.DataFrame(rows), {"wr": "WR"}, bands)["wr"]
    assert e["partial_weeks"] == [4]
    assert e["trajectory"] == "CHANGED (includes a partial game)"


def test_a_two_game_injury_exit_is_marked_partial():
    """DJ Moore, 2026: 77% of snaps in week 1, 31% in week 2 (left in the
    second quarter). The partial game must not hide inside its own median."""
    rows = [{"gsis_id": "wr", "week": w, "team": "CHI", "snap_pct": sp, "tgt_share": 0.2, "ay_share": 0.2,
             "wopr": 0.4, "carry_share": 0.0, "adot": 9.0, "i10_tgt": 0, "i10_car": 0, "two_min": 0,
             "targets": 5, "carries": 0}
            for w, sp in ((1, 0.77), (2, 0.31))]
    e = EV.evidence_for(["wr"], pd.DataFrame(rows), {"wr": "WR"}, {})["wr"]
    assert e["partial_weeks"] == [2]


def test_a_backup_who_takes_over_has_no_partial_games():
    """25%, 30%, 85%, 90%: a role that GREW. Measuring each week against the
    other weeks would mark weeks 1-2 as exits and dismiss the change."""
    rows = [{"gsis_id": "rb", "week": w, "team": "NYJ", "snap_pct": sp, "tgt_share": 0.1, "ay_share": 0.0,
             "wopr": 0.2, "carry_share": 0.3, "adot": 2.0, "i10_tgt": 0, "i10_car": 0, "two_min": 0,
             "targets": 2, "carries": 8}
            for w, sp in ((1, 0.25), (2, 0.30), (3, 0.85), (4, 0.90))]
    e = EV.evidence_for(["rb"], pd.DataFrame(rows), {"rb": "RB"}, {})["rb"]
    assert e["partial_weeks"] == []

