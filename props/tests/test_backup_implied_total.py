"""Tier 3 backup-QB diagnostic (reports/backup_qb_implied_total.md): the definitions and
the verdict are checked on cases with a known answer before the real run."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import backup_implied_total as BI  # noqa: E402


def test_planned_start_is_the_first_dropback_and_primary_needs_two_starts():
    pbp = pd.DataFrame({
        "season": 2023, "season_type": "REG", "posteam": "TB", "play_type": "pass",
        "week": [1, 1, 2, 3, 3, 4],
        "play_id": [10, 5, 7, 3, 9, 4],
        "passer_player_id": ["B", "A", "A", "C", "A", "A"]})
    s = BI.planned_starts(pbp).sort_values("week")
    assert s.starter.tolist() == ["A", "A", "C", "A"], "week 3: C threw first, then A came in"
    f = BI.backup_flags(s)
    assert f.week.tolist() == [3, 4] and f.backup.tolist() == [True, False], "primary only after two starts"


def test_implied_total_sign():
    g = pd.DataFrame({"season": [2023], "game_type": ["REG"], "week": [1], "home_team": ["KC"],
                      "away_team": ["DEN"], "spread_line": [7.0], "total_line": [45.0]})
    imp = BI.implied_totals(g).set_index("team").implied
    assert imp["KC"] == 26.0 and imp["DEN"] == 19.0, "home favoured by 7: 26 to 19"


def _world(extra_backup_drop, n_teams=40, seed=0, b_true=1.0):
    """Team-games where yards follow the implied ratio with slope b_true, and backup
    starts lose `extra_backup_drop` on top of what their lower implied total says."""
    rng = np.random.default_rng(seed)
    rows = []
    for season in (2022, 2023, 2024, 2025):
        for t in range(n_teams):
            for w in range(1, 18):
                backup = w > 3 and rng.uniform() < 0.12
                ratio = np.exp(rng.normal(-0.08 if backup else 0.0, 0.08))
                mod = 180.0
                act = mod * ratio ** b_true * (1 - extra_backup_drop * backup) * np.exp(rng.normal(0, 0.1))
                rows.append({"season": season, "team": f"T{t}", "week": w, "backup": backup, "ratio": ratio,
                             "rec_act": act, "rec_mod": mod})
    return pd.DataFrame(rows)


def _verdict(d):
    rng = np.random.default_rng(1)
    a, b, _ = BI.fit_b(d[d.season.isin((2022, 2023))], "rec_act", "rec_mod")
    per = {p: BI.gap(d[d.season.isin(ss)], "rec_act", "rec_mod", a, b, 500, rng) for p, ss in BI.PERIODS.items()}
    return b, per, BI.verdict(per)


def test_when_the_market_carries_the_drop_the_verdict_says_so():
    b, per, v = _verdict(_world(0.0))
    assert abs(b - 1.0) < 0.15
    assert all(p["raw_gap"] < -0.04 for p in per.values()), "backups do score less"
    assert v == "the implied total carries it"


def test_when_backups_lose_more_than_the_market_says_the_verdict_catches_it():
    _b, per, v = _verdict(_world(0.10))
    assert all(p["remaining_gap"] < -0.06 for p in per.values())
    assert v == "it does not"


def test_the_level_is_on_the_gap_s_own_scale_with_realistic_noise():
    """Found on the first real run: with team-game noise near real size (sd 0.35 in logs),
    a mean of logs sits well under the sum-over-sum level the gap is measured on, so an
    intercept from the log fit made backups look BETTER than expected. When the market
    carries the drop exactly, the remaining gap must still be about zero."""
    rng = np.random.default_rng(7)
    rows = []
    for season in (2022, 2023, 2024, 2025):
        for t in range(40):
            for w in range(1, 18):
                backup = w > 3 and rng.uniform() < 0.12
                ratio = np.exp(rng.normal(-0.08 if backup else 0.0, 0.08))
                act = 180.0 * ratio * np.exp(rng.normal(-0.35 ** 2 / 2, 0.35))     # mean-one noise
                rows.append({"season": season, "team": f"T{t}", "week": w, "backup": backup, "ratio": ratio,
                             "rec_act": act, "rec_mod": 180.0})
    d = pd.DataFrame(rows)
    a, b, _ = BI.fit_b(d[d.season.isin((2022, 2023))], "rec_act", "rec_mod")
    for p, ss in BI.PERIODS.items():
        g = BI.gap(d[d.season.isin(ss)], "rec_act", "rec_mod", a, b, 300, rng)
        assert abs(g["remaining_gap"]) < 0.03, (p, g)
