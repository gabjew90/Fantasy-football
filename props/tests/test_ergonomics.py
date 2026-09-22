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
