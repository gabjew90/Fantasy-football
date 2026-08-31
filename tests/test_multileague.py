"""Multi-league config (v2 amendment A): merge semantics + derived baselines."""

import pytest

from draftkit.config import Config
from draftkit.onboard import derive_baselines, derive_pool_sizes, slot_counts


def test_league_file_merges_over_globals():
    cfg = Config.load()  # default_league: omnibeta
    assert cfg.league_name == "omnibeta"
    assert cfg.league_id == "1395566811415588864"       # from league yaml
    assert cfg["season"] == 2026                        # league yaml scalar
    assert cfg["projections"]["model_alpha"] == 0.55    # global survives merge
    assert cfg.baselines["RB"] == 40                    # league-specific
    assert cfg["tilts"]["enabled"] is False             # omnibeta: draft done


def test_missing_league_fails_loudly(monkeypatch):
    monkeypatch.setenv("DRAFTKIT_LEAGUE", "nonexistent")
    with pytest.raises(FileNotFoundError, match="onboard"):
        Config.load()


def test_derived_baselines_standard_12_team():
    positions = ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "FLEX",
                 "K", "DEF", "BN", "BN", "BN", "BN", "BN"]
    b = derive_baselines(12, positions)
    # 2 RB + 2*0.45 flex = 2.9 -> 35; 2 WR + 0.9 = 34.8 -> 35; TE 1.2 -> 14
    assert b["RB"] == 35 and b["WR"] == 35 and b["TE"] == 14
    assert b["QB"] == 12 and b["K"] == 12 and b["DEF"] == 12
    pools = derive_pool_sizes(b)
    assert pools["RB"] == 60 and pools["QB"] == 28


def test_superflex_raises_qb_baseline():
    positions = ["QB", "SUPER_FLEX", "RB", "RB", "WR", "WR", "TE", "FLEX", "BN"]
    b = derive_baselines(10, positions)
    assert b["QB"] == 18  # 10 * (1 + 0.8)
    demand, bench = slot_counts(positions)
    assert bench == 1


def test_scoped_artifacts_isolate_leagues(monkeypatch):
    from pathlib import Path
    cfg_default = Config.load()
    assert cfg_default.scoped(Path("tiers.csv")).name == "tiers.csv"
    monkeypatch.setenv("DRAFTKIT_LEAGUE", "keefamania")
    cfg_k = Config.load()
    assert cfg_k.scoped(Path("tiers.csv")).name == "tiers.keefamania.csv"
    assert cfg_k.scoped(Path("data/processed/usage.parquet")).name == "usage.keefamania.parquet"


def test_scoring_from_league_yaml(monkeypatch):
    from draftkit.dataset import scoring_from_cfg
    cfg = Config.load()                       # omnibeta: no scoring block
    assert scoring_from_cfg(cfg)["receptions"] == 1.0
    monkeypatch.setenv("DRAFTKIT_LEAGUE", "keefamania")
    k = scoring_from_cfg(Config.load())
    assert k["receptions"] == 0.5             # half PPR
    assert k["rushing_fumbles_lost"] == -2.0  # fum_lost fans out
    assert k["passing_tds"] == 4.0
