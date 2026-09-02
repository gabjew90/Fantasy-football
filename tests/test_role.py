"""Role gating (projection overhaul, usage-side fix 1).

Jameis Winston, QB2 in 2026, projected ~230 from two 2025 starts. The gate
scales the MODEL term by the share of weeks a backup can expect to start,
and only when the depth chart AND the market both call him a backup.
"""

from __future__ import annotations

import polars as pl

from draftkit import role
from draftkit.bench import ABSENT_WEEKS


def test_role_share_is_one_for_starters_and_the_absence_math_for_backups():
    assert role.role_share("QB", 1) == 1.0
    assert role.role_share("RB", 2) == 1.0
    assert role.role_share("WR", 3) == 1.0
    assert role.role_share("QB", None) == 1.0, "unknown depth: no gate"
    assert role.role_share("K", 2) == 1.0, "no base rate: no gate"
    q = ABSENT_WEEKS["QB"] / 17
    assert abs(role.role_share("QB", 2) - q) < 1e-9
    assert role.role_share("QB", 3) == 0.0, "two QBs must be out: beyond the model"
    qr = ABSENT_WEEKS["RB"] / 17
    assert abs(role.role_share("RB", 3) - (1 - (1 - qr) ** 2)) < 1e-9   # one of two starters out
    assert abs(role.role_share("RB", 4) - qr ** 2) < 1e-9                # both out
    # WR is not gated: Sleeper's receiver chart is per slot (LWR/RWR/SWR),
    # so its order is not an overall depth (Davante Adams reads RWR 2)
    assert role.role_share("WR", 4) == 1.0 and role.role_share("WR", 9) == 1.0
    assert 0.15 < role.role_share("TE", 2) < 0.2


def test_gate_needs_both_the_depth_chart_and_the_market_to_say_backup():
    teams = 10
    df = pl.DataFrame({
        "sleeper_id": ["starter", "backup", "glitch", "unknown", "rookie", "nomarket"],
        "pos": ["QB"] * 6,
        # market ranks within QB by ecr; with 10 teams x 1 starter, ranks > 10
        # are "market backup" -- give the backup and glitch big ecr. nomarket
        # has neither ECR nor ADP (reached the board via the no-market floor).
        "ecr": [3.0, 40.0, 5.0, 45.0, None, None],
        "adp": [None, None, None, None, 200.0, None],
        "proj_model_pts": [300.0, 220.0, 280.0, 200.0, None, 210.0],
    })
    # pad with fillers so market position ranks exceed 10 for the backups
    filler = pl.DataFrame({"sleeper_id": [f"f{i}" for i in range(12)], "pos": ["QB"] * 12,
                           "ecr": [10.0 + i for i in range(12)], "adp": [None] * 12,
                           "proj_model_pts": [250.0] * 12})
    # a tight end filed under the RB chart (H-back), no market rank at all:
    # only the chart-position rule stands between him and a 0.03 share
    hback = pl.DataFrame({"sleeper_id": ["hback"], "pos": ["TE"], "ecr": [None], "adp": [None],
                          "proj_model_pts": [90.0]}, schema_overrides={"ecr": pl.Float64, "adp": pl.Float64})
    df = pl.concat([df, filler, hback], how="diagonal_relaxed")
    depth = pl.DataFrame({"sleeper_id": ["starter", "backup", "glitch", "rookie", "nomarket", "hback"],
                          "depth_order": [1, 2, 2, 2, 2, 6],
                          "depth_pos": ["QB", "QB", "QB", "QB", "QB", "RB"]})
    out = role.apply_role_gate(df, depth, teams)
    got = {r["sleeper_id"]: r for r in out.iter_rows(named=True)}
    assert got["hback"]["proj_model_pts"] == 90.0 and got["hback"]["role_share"] == 1.0
    assert "depth_pos" not in out.columns
    q = ABSENT_WEEKS["QB"] / 17
    assert got["starter"]["proj_model_pts"] == 300.0 and got["starter"]["role_share"] == 1.0
    assert abs(got["backup"]["proj_model_pts"] - 220.0 * q) < 1e-6, "depth 2 + market backup -> gated"
    assert abs(got["nomarket"]["proj_model_pts"] - 210.0 * q) < 1e-6, \
        "no ECR and no ADP is the market's strongest 'backup', not an unknown"
    assert got["glitch"]["proj_model_pts"] == 280.0 and got["glitch"]["role_share"] == 1.0, \
        "depth chart says backup but the market has him QB3: never cut on one source"
    assert got["unknown"]["proj_model_pts"] == 200.0, "no depth order -> no gate"
    assert got["rookie"]["proj_model_pts"] is None and got["rookie"]["role_share"] < 1.0, \
        "no model term to gate; share still reported"
    assert "_mkt_pos_rank" not in out.columns and "depth_order" not in out.columns


def test_depth_orders_reads_the_players_cache(tmp_path):
    assert role.depth_orders(tmp_path) is None
    (tmp_path / "players_nfl.json").write_text(
        '{"1": {"depth_chart_order": 2, "depth_chart_position": "QB"}, "2": {"depth_chart_order": null}}',
        encoding="utf-8")
    d = role.depth_orders(tmp_path)
    assert d.filter(pl.col("sleeper_id") == "1")["depth_order"][0] == 2
    assert d.filter(pl.col("sleeper_id") == "2")["depth_order"][0] is None
