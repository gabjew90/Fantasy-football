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


def test_scoring_without_league_block_fails_loudly():
    import pytest as _pytest
    from draftkit.dataset import scoring_from_cfg

    class FakeCfg(dict):
        pass

    with _pytest.raises(ValueError, match="no scoring"):
        scoring_from_cfg(FakeCfg({}))


def test_overrides_are_league_scoped(monkeypatch):
    """Override projections are absolute points in league scoring, so a
    full-PPR value must never leak onto a half-PPR board (review 8/31)."""
    from pathlib import Path
    cfg = Config.load()                       # omnibeta (default)
    assert cfg.scoped(Path("data/external/overrides.csv")).name == "overrides.csv"
    monkeypatch.setenv("DRAFTKIT_LEAGUE", "keefamania")
    k = Config.load()
    assert k.scoped(Path("data/external/overrides.csv")).name == "overrides.keefamania.csv"


def test_no_omnibeta_identity_in_shared_code():
    """League facts must not live in league-agnostic modules (item 1)."""
    import subprocess
    r = subprocess.run(
        ["git", "grep", "-n", "-E",
         "farmerjamal|omnibeta|1395566811415588864|1395566812157984768",
         "--", "draftkit/*.py", "manager/*.py"],
        capture_output=True, text=True)
    assert r.stdout.strip() == "", f"Omnibeta identity leaked:\n{r.stdout}"


def test_no_roster_shape_literals_in_shared_code():
    """A league's LINEUP SHAPE is a league fact too (plan B2).

    The name/id guard above passed for months while
    `SLOTS = {QB 1, RB 2, WR 2, TE 1, K 1, DEF 1}` and `FLEX = 2` sat in
    draftkit/briefs.py, so every non-Omnibeta league had a ten-starter lineup
    optimised for a nine-starter roster. draftkit/shape.py is the one place
    allowed to turn roster positions into slot counts.
    """
    import subprocess
    pat = (r"^(SLOTS|POS_SLOTS|FLEX|N_STARTERS|ROSTER_SLOTS)\s*=|"
           r"flex\s*(<|>|==|<=|>=)\s*[0-9]|"
           r"\bflex\s*=\s*[1-9]")
    r = subprocess.run(
        ["git", "grep", "-n", "-E", pat, "--",
         "draftkit/*.py", "manager/*.py", ":!draftkit/shape.py"],
        capture_output=True, text=True)
    assert r.stdout.strip() == "", (
        "roster shape hardcoded outside draftkit/shape.py -- resolve it with "
        f"shape_for(cfg, league) instead:\n{r.stdout}")



def test_no_roster_shape_literals_in_shared_code():
    """A league's LINEUP SHAPE is a league fact too (plan B2).

    The name/id guard above passed for months while
    `SLOTS = {QB 1, RB 2, WR 2, TE 1, K 1, DEF 1}` and `FLEX = 2` sat in
    draftkit/briefs.py, so every non-Omnibeta league had a ten-starter lineup
    optimised for a nine-starter roster. draftkit/shape.py is the one place
    allowed to turn roster positions into slot counts.
    """
    import subprocess
    pat = (r"^(SLOTS|POS_SLOTS|FLEX|N_STARTERS|ROSTER_SLOTS)\s*=|"
           r"flex\s*(<|>|==|<=|>=)\s*[0-9]|"
           r"\bflex\s*=\s*[1-9]")
    r = subprocess.run(
        ["git", "grep", "-n", "-E", pat, "--",
         "draftkit/*.py", "manager/*.py", ":!draftkit/shape.py"],
        capture_output=True, text=True)
    assert r.stdout.strip() == "", (
        "roster shape hardcoded outside draftkit/shape.py -- resolve it with "
        f"shape_for(cfg, league) instead:\n{r.stdout}")



def test_lenses_read_from_league_yaml_and_degrade_off(monkeypatch):
    from draftkit.lenses import load_lenses, scoreboard_md
    cfg = Config.load()                                  # omnibeta
    lenses = load_lenses(cfg)
    assert lenses.get("farmerjamal") == (1989, 1995, 10)
    monkeypatch.setenv("DRAFTKIT_LEAGUE", "keefamania")
    k = Config.load()
    assert load_lenses(k) == {}                          # no block -> empty
    md = scoreboard_md({"a": 1.0, "b": 2.0, "c": 3.0}, k)
    assert "off for this league" in md                   # degrades, never borrows
