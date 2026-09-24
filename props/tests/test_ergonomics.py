"""The scorer's conveniences: team aliases, market filter, scoring presets,
the positive-EV statement, the --markets summary and the fantasy export."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "engine" / "scripts"))
pd = pytest.importorskip("pandas")
import score_game as SG  # noqa: E402


def test_team_aliases_resolve_to_games_csv_codes():
    assert [SG.resolve_team(x) for x in ("lar", "WSH", "JAC", "LVR", "SF")] == ["LA", "WAS", "JAX", "LV", "SF"]


def test_market_filter_accepts_short_names_and_rejects_typos():
    assert SG.parse_markets("td, rec_yds") == {"player_anytime_td", "player_reception_yds"}
    assert SG.parse_markets("") == set()
    with pytest.raises(SystemExit):
        SG.parse_markets("tds")


def test_scoring_presets_json_and_inline(tmp_path):
    assert SG.parse_scoring("half")["rec"] == 0.5
    assert SG.parse_scoring("std")["rec"] == 0.0
    f = tmp_path / "s.json"
    f.write_text(json.dumps({"rec": 0.5, "rush_td": 4, "unknown": 9}), encoding="utf-8")
    sc = SG.parse_scoring(str(f))
    assert sc["rec"] == 0.5 and sc["rush_td"] == 4.0 and "unknown" not in sc
    assert SG.parse_scoring("rec=0.25")["rec"] == 0.25


def test_the_positive_ev_statement_is_plain():
    R = pd.DataFrame({"ER": [-0.1, -0.02]})
    assert SG.ev_statement(R) == "**No row has positive expected value at the posted prices.**"
    assert "1 of 2 priced rows" in SG.ev_statement(pd.DataFrame({"ER": [0.05, -0.02]}))
    assert "No lines" in SG.ev_statement(pd.DataFrame())


def test_the_markets_summary_lists_only_what_was_priced():
    R = pd.DataFrame({"player": ["A"], "team": ["X"], "market": ["player_anytime_td"], "side": ["Yes"],
                      "line": [np.nan], "book": ["sleeper"], "price": [150], "p_model": [0.3],
                      "p_novig": [0.33], "gap": [-0.03], "ER": [-0.1]})
    out = "\n".join(SG.short_summary(R, "A", "B", 2026, 3, "Sleeper Picks", 0.5, ["player_anytime_td"]))
    assert "No row has positive expected value" in out and "Candidate closing snapshot" in out
    assert "| A (X) | anytime_td | Yes | sleeper | +150 | 30% | 33% | -3% |" in out


def test_the_fantasy_export_scores_draws_with_the_league_settings():
    M = pd.DataFrame({"name": ["W", "R"], "team": ["T", "T"], "pos": ["WR", "RB"], "slot": ["WR1", "RB1"],
                      "gsis_id": ["w", "r"]})
    n = 4000
    sims = {"W": {"receptions": np.full(n, 5.0), "rec_yards": np.full(n, 60.0), "rush_yards": np.zeros(n)},
            "R": {"receptions": np.full(n, 2.0), "rec_yards": np.full(n, 10.0), "rush_yards": np.full(n, 70.0)}}
    V1TD = pd.DataFrame({"team": ["T", "T"], "mu": [2.5, 2.5], "q": [0.0, 0.0], "p": [0.0, 0.0]}, index=["w", "r"])
    FP = SG.fantasy_table(M, sims, V1TD, lambda m: 0.0, SG.parse_scoring("ppr"), np.random.default_rng(1), n)
    by = FP.set_index("player")
    assert by.loc["W", "median"] == pytest.approx(5 + 6.0)       # q = 0: no TDs, 5 rec + 60 yds
    assert by.loc["R", "median"] == pytest.approx(2 + 1.0 + 7.0)
    half = SG.fantasy_table(M, sims, V1TD, lambda m: 0.0, SG.parse_scoring("half"), np.random.default_rng(1), n)
    assert half.set_index("player").loc["W", "median"] == pytest.approx(2.5 + 6.0)
    # the fantasy scenario command joins on the id and reads the contract's percentiles
    assert by.loc["W", "gsis_id"] == "w"
    assert by.loc["W", "p10"] <= by.loc["W", "p25"] <= by.loc["W", "median"] <= by.loc["W", "p75"] <= by.loc["W", "p90"]


def test_last_quota_reads_the_newest_cache_file(tmp_path, monkeypatch):
    monkeypatch.setattr(SG, "HERE", tmp_path)
    assert SG.last_oddsapi_quota() is None
    (tmp_path / "cache").mkdir()
    (tmp_path / "cache" / "odds_x_1.json").write_text(json.dumps({"quota": {"x-requests-remaining": "412"}}),
                                                     encoding="utf-8")
    assert SG.last_oddsapi_quota() == 412


def test_today_is_the_eastern_date_not_the_utc_one(monkeypatch):
    """Monday 8:30 pm ET is Tuesday 00:30 UTC: --today must still say Monday."""
    import datetime as dt

    class Fake(dt.datetime):
        @classmethod
        def now(cls, tz=None):
            return dt.datetime(2026, 9, 22, 0, 30, tzinfo=dt.timezone.utc)
    monkeypatch.setattr(SG, "datetime", Fake)
    assert SG.et_today() == "2026-09-21"

    class Winter(dt.datetime):
        @classmethod
        def now(cls, tz=None):
            return dt.datetime(2026, 12, 8, 4, 30, tzinfo=dt.timezone.utc)   # Mon 11:30 pm EST
    monkeypatch.setattr(SG, "datetime", Winter)
    assert SG.et_today() == "2026-12-07"


def _pairs():
    return pd.DataFrame({"kind": ["opponents", "teammates"], "player_a": ["A", "C"], "team_a": ["X", "X"],
                         "player_b": ["B", "D"], "team_b": ["Y", "X"], "p_indep": [0.10, 0.10],
                         "p_joint_plain": [0.10, 0.09], "p_joint_shift": [0.10, 0.09],
                         "p_joint_shift_copula": [0.105, 0.09], "p_joint_copula": [0.105, 0.09]})


def _gate(open_classes):
    b = {c: {"ratio": 1.0, "ci": [0.95, 1.05], "games": 1000}
         for c in ("cross-team pair", "teammate pair", "mixed 3-leg", "three teammates")}
    return {"open_classes": open_classes, "b_prime": b,
            "picks": {"cross-team pair": "joint + mix shift + copula", "teammate pair": "joint"}}


def test_td_pairs_render_only_open_classes_from_the_committed_gate(tmp_path, monkeypatch):
    monkeypatch.setattr(SG, "RES", tmp_path)
    assert SG.td_pairs_section(_pairs()) == []                      # no gate file: nothing renders
    (tmp_path / "td_parlay_gate.json").write_text(json.dumps(_gate(["cross-team pair"])), encoding="utf-8")
    text = "\n".join(SG.td_pairs_section(_pairs()))
    assert "cross-team pair" in text and "A (X) + B (Y) | 10.5%" in text     # its pick's column
    assert "teammate pair (layer 3" not in text                               # not open: not shown
    (tmp_path / "td_parlay_gate.json").write_text(json.dumps(_gate([])), encoding="utf-8")
    assert SG.td_pairs_section(_pairs()) == []


def test_joint_shadow_uses_the_gated_specification(tmp_path, monkeypatch):
    """The rendered pairs must be the model the gate scored: its mix shift,
    copula r and Dirichlet c come from the gate JSON, not from constants or a
    table estimated on other seasons."""
    import td_joint as TDJ
    ch = TDJ.CH
    V1TD = pd.DataFrame({"team": ["A", "A", "B"], "mu": [2.5, 2.5, 2.0]}, index=["a1", "a2", "b1"])
    for c_ in ch:
        V1TD[f"s_{c_}"] = [0.3, 0.2, 0.3]
        V1TD[f"w_{c_}"] = 1.0 / len(ch)
    M = pd.DataFrame({"name": ["P1", "P2", "Q1"], "gsis_id": ["a1", "a2", "b1"]})
    R = pd.DataFrame({"market": "player_anytime_td", "td_model": SG.TDV1.LABEL, "player": ["P1", "P2", "Q1"],
                      "team": ["A", "A", "B"], "p_model": [0.4, 0.3, 0.35]})
    monkeypatch.setattr(SG, "RES", tmp_path)
    no_gate = SG.joint_shadow(R, M, V1TD, "A", "B", 2025)
    assert "spec bundled" in no_gate["joint_model"].iloc[0]
    spec = {"copula_r": 0.0, "dirichlet_c": None,
            "mix_shift": {"channels": list(ch), "rows": [[1.0] * len(ch)] * TDJ.OPP_BUCKETS}}
    (tmp_path / "td_parlay_gate.json").write_text(json.dumps(spec), encoding="utf-8")
    J = SG.joint_shadow(R, M, V1TD, "A", "B", 2025)
    assert "spec gate" in J["joint_model"].iloc[0]
    # r = 0 and no shift: every candidate collapses to plain joint, and cross-team equals the product
    cross = J[J["kind"] == "opponents"]
    assert np.allclose(cross["p_joint_copula"], cross["p_joint_plain"])
    assert np.allclose(cross["p_joint_shift_copula"], cross["p_joint_shift"])


def test_run_odds_empty_output_is_a_runtime_error(monkeypatch):
    # An odds_client that prints nothing (no key on the host) must raise the error the Odds API
    # fallback catches, not a JSONDecodeError that kills the game.
    import subprocess
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: subprocess.CompletedProcess(a, 0, stdout="", stderr="no key"))
    with pytest.raises(RuntimeError, match="no JSON"):
        SG.run_odds("events", [])


def test_espn_scoreboard_asks_for_the_game_week():
    # The bare scoreboard still shows last week on Tuesday; an early-week run then found no
    # spread/total for any game and priced every TD with the v0 fallback.
    u = SG.espn_scoreboard_url(2026, 3)
    assert "seasontype=2" in u and "week=3" in u and "dates=2026" in u


def test_slate_pick_prefers_backtested_market_over_higher_td_probability():
    import score_week as SW
    ok = pd.DataFrame([
        dict(player="TD back", market="player_anytime_td", rule="any market, book agrees (no-vig >= 50%)",
             p_model=0.76, new_team=False, questionable=False),
        dict(player="Catcher", market="player_receptions", rule="calibrated market, book agrees (no-vig >= 55%)",
             p_model=0.66, new_team=False, questionable=False),
        dict(player="Disagree", market="player_receptions", rule="calibrated market, BOOK DISAGREES (weakest class)",
             p_model=0.90, new_team=False, questionable=False),
    ])
    assert SW.slate_pick_order(ok).player.tolist() == ["Catcher", "TD back"]


def _age(path, seconds):
    import os
    import time
    t = time.time() - seconds
    os.utime(path, (t, t))


def test_fetch_refreshes_a_stale_copy_and_keeps_a_fresh_one(tmp_path, monkeypatch):
    # The props cache is restored every tick; a fetch that only checked existence
    # priced every capture on the first capture's play-by-play and injuries.
    import urllib.request
    calls = []

    def fake(url, dest):
        calls.append(url)
        Path(dest).write_text("new", encoding="utf-8")
    monkeypatch.setattr(urllib.request, "urlretrieve", fake)
    f = tmp_path / "pbp_2026.csv"
    f.write_text("old", encoding="utf-8")
    _age(f, 60)
    SG.fetch("u", f, max_age_s=3600)
    assert calls == [] and f.read_text(encoding="utf-8") == "old"
    _age(f, 7200)
    SG.fetch("u", f, max_age_s=3600)
    assert calls == ["u"] and f.read_text(encoding="utf-8") == "new"


def test_fetch_keeps_the_stale_copy_when_the_refresh_fails(tmp_path, monkeypatch):
    import urllib.request

    def boom(url, dest):
        Path(dest).write_text("partial", encoding="utf-8")
        raise OSError("network")
    monkeypatch.setattr(urllib.request, "urlretrieve", boom)
    f = tmp_path / "injuries_2026.csv"
    f.write_text("old", encoding="utf-8")
    _age(f, 99999)
    assert SG.fetch("u", f, max_age_s=3600) == f
    assert f.read_text(encoding="utf-8") == "old"
    assert not (tmp_path / "injuries_2026.csv.part").exists()
    g = tmp_path / "missing.csv"
    with pytest.raises(OSError):
        SG.fetch("u", g, max_age_s=3600)


def test_season_inputs_refresh_once_and_report_their_age(tmp_path, monkeypatch):
    # score_week refreshes these once per slate and pins the per-game runs to them.
    got = []
    monkeypatch.setattr(SG, "fetch", lambda url, dest, max_age_s=None: got.append(Path(dest).name)
                        or Path(dest).write_text("x", encoding="utf-8") or dest)
    ages = SG.refresh_season_inputs(2026, tmp_path)
    assert set(ages) == {"pbp", "rosters", "injuries", "depth_charts", "snaps", "games"}
    assert all(isinstance(v, float) and v < 0.1 for v in ages.values())
    assert sorted(got) == sorted(p.name for _, p in SG.season_inputs(2026, tmp_path).values())
