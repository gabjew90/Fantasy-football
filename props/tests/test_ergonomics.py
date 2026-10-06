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


def test_the_research_statement_says_what_the_sheet_is():
    R = pd.DataFrame({"player": ["A", "A", "B"], "market": ["m", "m", "m"], "line": [1.5, 1.5, 2.5]})
    out = SG.research_statement(R)
    assert out.startswith("**2 lines priced.**") and "no line carries a bet label" in out
    assert "No yardage" in SG.research_statement(pd.DataFrame())


def test_research_cells_show_both_prices_and_the_implied_workload():
    x = pd.Series({"market": "player_receptions", "line": 4.5, "price_over": -116, "price_under": -141,
                   "median": 5.0, "p10": 2.0, "p90": 10.0, "p_over_model": 0.587, "p_over_book": 0.479,
                   "implied": 6.298, "projected": 7.07, "unit": "targets"})
    row = SG.research_cells(x, {"player_receptions": "catches"})
    assert row == "| catches | 4.5 | O -116 / U -141 | 5 (2 to 10) | 59% / 48% | 6.3 targets (we project 7.1) | — |",         "no break-even search yet: the cell says so"
    x2 = x.copy()
    x2["over_needs"], x2["under_needs"], x2["be_over"], x2["be_under"] = 6.512, None, 0.537, 0.585
    assert SG.research_cells(x2, {}).endswith("| Over above 6.5 targets; Under: beyond the search range |")
    x2["be_under"] = None                       # no Under posted: never "beyond the search range"
    assert SG.research_cells(x2, {}).endswith("| Over above 6.5 targets; Under: no price posted |")
    assert "-0" not in SG.research_cells(x.assign(p10=-0.3) if hasattr(x, "assign") else x, {})


def test_usage_line_compares_last_game_with_earlier_weeks():
    u = {"week": 3, "snap": 0.54, "snap_base": 0.67, "ts": 0.12, "ts_base": 0.25, "cs": 0.0, "cs_base": 0.0}
    assert SG.usage_line(u, short=True) == "wk3: snaps 54% (67%), targets 12% (25%)"
    assert SG.usage_line(None) is None


def test_the_markets_summary_lists_only_what_was_priced():
    R = pd.DataFrame({"player": ["A"], "team": ["X"], "market": ["player_anytime_td"], "side": ["Yes"],
                      "line": [np.nan], "book": ["sleeper"], "price": [150], "p_model": [0.3],
                      "p_novig": [0.33], "gap": [-0.03], "ER": [-0.1]})
    out = "\n".join(SG.short_summary(R, "A", "B", 2026, 3, "Sleeper Picks", 0.5, ["player_anytime_td"]))
    assert "No bet labels" in out and "Candidate closing snapshot" in out
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


def test_the_slate_board_orders_games_by_total_and_can_show_overs_only():
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "engine" / "scripts"))
    import score_week as W
    row = dict(player="A", team="CIN", market="player_receptions", line=4.5, book="sleeper", price_over=-118,
               price_under=-139, median=5.0, p10=2.0, p90=9.0, p_over_model=0.55, p_over_book=0.48, implied=8.0,
               projected=8.5, unit="targets", over_needs=8.5, under_needs=7.1, be_over=0.54, be_under=0.58,
               snap=0.93, snap_base=0.72, ts=0.19, ts_base=0.25, cs=0.0, cs_base=0.0, flags="role up")
    RS = pd.DataFrame([dict(row, game="GB@TB"), dict(row, game="JAX@CIN", player="B")])
    runs = [dict(game="GB@TB", total="38.5", kickoff_utc="Sun 17:00Z"),
            dict(game="JAX@CIN", total="51.5", kickoff_utc="Sun 17:00Z")]
    B = W.slate_board(RS, runs, sort="total")
    heads = [ln for ln in B if ln.startswith("## ")]
    assert heads[0].startswith("## JAX @ CIN — total 51.5") and heads[1].startswith("## GB @ TB — total 38.5")
    assert any("| Over above 8.5 targets; Under at 7.1 or fewer · we project 8.5: no-bet zone |" in ln for ln in B)
    assert [ln for ln in W.slate_board(RS, runs) if ln.startswith("## ")][0].startswith("## GB @ TB"), \
        "kickoff order keeps the run order"
    O = W.slate_board(RS, runs, sort="total", overs_only=True)
    r = next(ln for ln in O if ln.startswith("| B (CIN)"))
    assert "| -118 |" in r and "| 8.5 targets |" in r and "U -139" not in r
    assert "The Over pays if you expect more than" in "\n".join(O)


def test_kickoff_reads_the_way_people_say_it_and_missing_totals_sort_last():
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "engine" / "scripts"))
    import score_week as W
    for said, want in [("13:00", "13:00"), ("1:00", "13:00"), ("1pm", "13:00"), ("1:00 PM", "13:00"),
                       ("4:25", "16:25"), ("16:05", "16:05"), ("8:20pm", "20:20"), ("9:30", "09:30"),
                       ("9:30am", "09:30"), ("1 pm ET", "13:00")]:
        assert W.eastern_kickoff(said) == want, said
    with pytest.raises(SystemExit, match="write an Eastern time"):
        W.eastern_kickoff("noon-ish")
    row = dict(player="A", team="X", market="player_receptions", line=2.5, book="sleeper", price_over=-110,
               price_under=-110, median=3.0, p10=1.0, p90=6.0, p_over_model=0.5, p_over_book=0.5, implied=5.0,
               projected=5.0, unit="targets", over_needs=5.5, under_needs=4.5, be_over=0.52, be_under=0.52,
               snap=0.8, snap_base=0.7, ts=0.2, ts_base=0.18, cs=0.0, cs_base=0.0, usage_week=3, flags="")
    RS = pd.DataFrame([dict(row, game="A@B"), dict(row, game="C@D")])
    runs = [dict(game="A@B", total="", kickoff_utc="Sun"), dict(game="C@D", total="41.5", kickoff_utc="Sun")]
    B = W.slate_board(RS, runs, sort="total")
    heads = [ln for ln in B if ln.startswith("## ")]
    assert heads[0].startswith("## C @ D") and heads[1].startswith("## A @ B — total —")
    assert any("| wk3: snaps 80% (70%), targets 20% (18%) |" in ln for ln in B), "the report's wording"


def test_last_game_shows_the_count_beside_the_share():
    u = {"week": 3, "snap": 0.93, "snap_base": 0.72, "ts": 0.19, "ts_base": 0.25, "cs": 0.0, "cs_base": 0.0,
         "tn": 6.0, "tn_base": 8.25, "cn": 0.0, "cn_base": 0.0}
    assert SG.usage_line(u, short=True) == "wk3: snaps 93% (72%), targets 19% / 6 (25% / 8.2)"
    assert "targets 19% of the team's, 6 (earlier 25%, 8.2 a game)" in SG.usage_line(u)
    old = {k: v for k, v in u.items() if k not in ("tn", "tn_base", "cn", "cn_base")}
    assert SG.usage_line(old, short=True) == "wk3: snaps 93% (72%), targets 19% (25%)", "older files: shares only"


def test_each_game_on_the_board_opens_with_its_context_line():
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "engine" / "scripts"))
    import score_week as W
    pv = {"DAL": "last week was a preview: same QB, same key absences", "HOU": "last week differs: Nico Collins back"}
    assert W.game_context("DAL@HOU", "HOU -3", "48.5", pv) == (
        "*HOU by 3 · implied points HOU 25.8, DAL 22.8 · DAL: last week was a preview: same QB, same key absences"
        " · HOU: last week differs: Nico Collins back*")
    assert W.game_context("ARI@NYG", "NYG +2.5", "44.5", {}) == "*ARI by 2.5 · implied points ARI 23.5, NYG 21.0*"
    assert W.game_context("A@B", "", "", {}) == ""


def test_a_spread_written_with_an_alias_still_names_the_right_favourite():
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "engine" / "scripts"))
    import score_week as W
    assert W.game_context("TEN@JAX", "JAC -3", "44.0", {}) == "*JAX by 3 · implied points JAX 23.5, TEN 20.5*"
    assert W.game_context("TEN@JAX", "XXX -3", "44.0", {}) == "", "an unknown team code says nothing rather than guess"


def test_a_player_on_reserve_is_out_like_a_ruled_out_player():
    pop = pd.DataFrame({"team": ["NO"] * 4, "gsis_id": list("abcd"), "status": ["ACT", "RES", "INA", "ACT"],
                        "report_status": [None, None, None, "Out"]})
    p = SG.apply_designations(pop)
    assert p.excluded.tolist() == [False, True, True, True], "reserve/IR, inactive and Out are all excluded"
    assert SG.keep_in_pool("RES", True), "on reserve after playing this season: in, so his share is handed on"
    assert not SG.keep_in_pool("RES", False), "on reserve since before the season: already absent from the numbers"
    assert SG.keep_in_pool("ACT", False) and SG.keep_in_pool("INA", False)
    assert not SG.keep_in_pool("DEV", True) and not SG.keep_in_pool("CUT", True), "practice squad / cut: old handling"
    p2 = SG.apply_designations(pd.DataFrame({"team": ["NO"] * 2, "gsis_id": list("xy"), "status": ["DEV", "PUP"],
                                             "report_status": [None, None]}))
    assert p2.excluded.tolist() == [False, True], "only the not-playing statuses are excluded"


def test_last_weeks_game_day_inactive_does_not_rule_a_player_out_this_week():
    ros = pd.DataFrame({"season": [2026] * 4, "week": [4] * 4, "team": ["TB"] * 4, "gsis_id": list("abcd"),
                        "full_name": ["Baker Mayfield", "Jalon Daniels", "Mike Evans", "X"],
                        "position": ["QB", "QB", "WR", "WR"], "status": ["INA", "ACT", "RES", "DEV"]})
    rw, prov = SG.week_roster(ros, 2026, 5)
    assert prov == 4 and rw.status.tolist() == ["ACT", "ACT", "RES", "DEV"], "only INA is per-game"
    rw, prov = SG.week_roster(ros.assign(week=5), 2026, 5)
    assert prov is None and rw.status.tolist()[0] == "INA", "this week's own inactive list stands"


def test_the_line_flag_counts_the_five_regulars_and_why_each_is_out():
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "engine" / "scripts"))
    import research as RSCH
    rows = []
    for w in (1, 2, 3):
        for pid, nm, pos, sn in [("a", "LT A", "T", 60), ("b", "LG B", "G", 60), ("c", "C C", "C", 60),
                                 ("d", "RG D", "G", 60), ("e", "RT E", "T", 60 if w < 3 else 0),
                                 ("f", "Swing F", "OL", 5 if w < 3 else 60), ("g", "TE G", "TE", 70)]:
            rows.append({"team": "NO", "week": w, "pfr_player_id": pid, "player": nm, "position": pos,
                         "offense_snaps": sn})
    snaps = pd.DataFrame(rows)
    regs = RSCH.line_regulars(snaps, "NO", 4)
    assert [r["name"] for r in regs] == ["C C", "LG B", "LT A", "RG D", "RT E"], "top five by snaps, no TE"
    assert RSCH.line_regulars(snaps, "NO", 1) == [] and RSCH.line_regulars(snaps, "ATL", 4) == []
    pfr = {k: k.upper() for k in "abcdef"}
    roster = {"A": ("NO", "ACT"), "B": ("NO", "RES"), "C": ("NO", "ACT"), "D": ("NO", "ACT")}   # E traded
    report = {"A": "Out", "C": "Questionable"}
    st = RSCH.line_status(regs, "NO", pfr, roster, report, ("INA", "RES"))
    assert [(s["name"], s["state"], s["why"]) for s in st] == [
        ("C C", "questionable", "Questionable"), ("LG B", "out", "on reserve"), ("LT A", "out", "Out"),
        ("RG D", "playing", None), ("RT E", "out", "no longer on the roster")]
    txt = RSCH.line_sentence("NO", st)
    assert txt.startswith("NO: 3 of 5 regular linemen out -- ") and "questionable: C C (C, Questionable)" in txt
    assert RSCH.line_sentence("NO", st[:4]) is None
    ok = RSCH.line_status(regs, "NO", pfr, {k: ("NO", "ACT") for k in "ABCDE"}, {}, ("INA",))
    assert RSCH.line_sentence("NO", ok) == "NO: all five regular linemen available."

    # the roster file lacks many pfr ids: a same-team name match fills in; no match is never "out"
    by_name = {("NO", "lt a"): "A"}
    st2 = RSCH.line_status(regs, "NO", {}, {"A": ("NO", "ACT")}, {}, ("INA",), name_to_gsis=by_name)
    assert [s["state"] for s in st2] == ["unmatched", "unmatched", "playing", "unmatched", "unmatched"]
    assert RSCH.line_sentence("NO", st2).startswith("NO: no regular lineman reported out; not matched")
    assert RSCH.line_sentence("NO", ok, report_out=False) == (
        "NO: all five regular linemen available (no injury report yet this week: roster status only).")


def test_sleeper_fills_the_injury_report_only_where_it_is_silent():
    """DECISIONS #183: Baker Mayfield 'Out, thumb' on Sleeper four days before a Thursday
    game, no official report yet. The official report wins wherever it has an entry."""
    players = {"1": {"full_name": "Baker Mayfield", "team": "TB", "injury_status": "Out", "injury_body_part": "Thumb"},
               "2": {"full_name": "Mike Evans", "team": "TB", "injury_status": "Questionable", "injury_body_part": None},
               "3": {"full_name": "Puka Nacua", "team": "LAR", "injury_status": "IR", "injury_body_part": "Ankle"},
               "4": {"full_name": "Healthy Guy", "team": "TB", "injury_status": None}}
    m = SG.sleeper_injury_map(players, {"LA": "LAR"})
    assert m[("TB", "baker mayfield")] == ("Out", "Thumb") and ("LA", "puka nacua") in m
    assert ("TB", "healthy guy") not in m
    roster = pd.DataFrame({"team": ["TB", "TB", "LA", "TB"], "gsis_id": ["b", "e", "p", "h"],
                           "full_name": ["Baker Mayfield", "Mike Evans", "Puka Nacua", "Healthy Guy"]})
    st, src = SG.injuries_with_fallback({("TB", "e"): None, ("TB", "h"): "Questionable"}, roster, m)
    assert st[("TB", "b")] == "Out" and "thumb" in src[("TB", "b")]
    assert st[("LA", "p")] == "Out", "IR reads as Out"
    assert st[("TB", "e")] == "Questionable" and ("TB", "e") in src, "an empty official entry is no entry"
    assert st[("TB", "h")] == "Questionable" and ("TB", "h") not in src, "the official report wins"


def test_once_the_report_is_out_a_stale_sleeper_out_does_not_bench_a_healthy_player():
    """Code review 2026-10-06: a player off this week's report (or practising fully) is
    healthy even if Sleeper still shows last week's Out; one listed DNP/limited with no
    game status yet takes Sleeper's; a reserve list counts whatever the report says."""
    players = {"1": {"full_name": "Back Returning", "team": "NO", "injury_status": "Out", "gsis_id": "r"},
               "2": {"full_name": "Back Limited", "team": "NO", "injury_status": "Doubtful", "gsis_id": "l"},
               "3": {"full_name": "Back Full", "team": "NO", "injury_status": "Out", "gsis_id": "f"},
               "4": {"full_name": "Back Ir", "team": "NO", "injury_status": "IR", "gsis_id": "i"},
               "5": {"full_name": "Gabriel Davis", "team": "BUF", "injury_status": "Out", "gsis_id": "gd"}}
    m = SG.sleeper_injury_map(players)
    roster = pd.DataFrame({"team": ["NO"] * 4 + ["BUF"], "gsis_id": ["r", "l", "f", "i", "gd"],
                           "full_name": ["Back Returning", "Back Limited", "Back Full", "Back Ir", "Gabe Davis"]})
    practice = {("NO", "l"): "Limited Participation in Practice", ("NO", "f"): "Full Participation in Practice"}
    st, src = SG.injuries_with_fallback({("NO", "l"): None, ("NO", "f"): None}, roster, m,
                                        practice=practice, reported_teams={"NO"})
    assert ("NO", "r") not in st or not isinstance(st[("NO", "r")], str), "off the report: healthy"
    assert st[("NO", "f")] is None, "practising fully: healthy"
    assert st[("NO", "l")] == "Doubtful" and "practice" in src[("NO", "l")]
    assert st[("NO", "i")] == "Out", "a reserve list is never on the weekly report"
    assert st[("BUF", "gd")] == "Out", "joined by gsis id, not by name (Gabe / Gabriel)"


def test_the_next_quarterback_starts_when_qb1_is_out():
    roles = pd.DataFrame([{"team": "TB", "gsis_id": "baker", "slot": "QB1", "dc_dt": None},
                          {"team": "TB", "gsis_id": "evans", "slot": "WR1", "dc_dt": None}])
    out = {"baker"}
    r2, got = SG.promote_qb(roles, "TB", ["baker", "stick", "daniels"], lambda g: g in out,
                            lambda g: g != "stick")
    assert got == "daniels", "the next QB on the roster and not out"
    assert set(r2[r2.slot == "QB1"].gsis_id) == {"baker", "daniels"}, "the out QB stays listed (and excluded)"
    r3, got3 = SG.promote_qb(roles, "TB", ["baker", "daniels"], lambda g: False, lambda g: True)
    assert got3 is None and r3.equals(roles), "QB1 healthy: nothing moves"
    _r4, got4 = SG.promote_qb(roles, "TB", ["baker"], lambda g: g in out, lambda g: True)
    assert got4 is None, "no other QB: nobody is invented"


def test_rushing_plus_receiving_is_priced_and_settled_end_to_end():
    """DECISIONS #187: the combined line is the sum of a player's two draws, settled on
    rushing + receiving yards, and labelled wherever markets are named."""
    import settle as ST
    import blend as BL
    assert SG.YARD_MARKETS["player_rush_reception_yds"] == "rush_rec_yards"
    assert ST.MARKET_STAT["player_rush_reception_yds"] == "_rush_rec_yards"
    assert "player_rush_reception_yds" in BL.YARDAGE_MARKETS
    assert SG.MARKET_WORDS["player_rush_reception_yds"] == "rushing + receiving yards"
    assert SG.parse_markets("rush_rec") == {"player_rush_reception_yds"}


def test_a_blank_roof_reads_the_stadiums_history_not_outdoors():
    """Outside review 2026-10-06: nflverse leaves roof blank until kickoff; AT&T Stadium read
    as outdoors and the wind screen could fire under a closed roof."""
    games = pd.DataFrame({"stadium_id": ["DAL00"] * 9 + ["GB00"], "gameday": [f"2025-10-{d:02d}" for d in range(1, 11)],
                          "roof": ["closed"] * 8 + [None, "outdoors"]})
    r, note = SG.resolve_roof(float("nan"), "DAL00", games)
    assert r == "closed" and "8 of this stadium's last 8" in note and "retractable" in note
    assert SG.resolve_roof("outdoors", "GB00", games) == ("outdoors", None), "a posted roof is used as is"
    assert SG.resolve_roof(None, "NEW00", games)[0] == "unknown"


def test_snap_rows_take_the_rosters_name_by_id():
    """Outside review 2026-10-06: 'Kenneth Gainwell' (snaps) vs 'Kenny Gainwell' (roster)."""
    import model as MODEL
    snp = pd.DataFrame({"player": ["Kenneth Gainwell", "Zonovan Knight", "No Id Guy"],
                        "pfr_player_id": ["GainKe00", "KnigZo00", None], "team": ["TB", "ARI", "NO"]})
    ros = pd.DataFrame({"full_name": ["Kenny Gainwell", "Bam Knight"], "pfr_id": ["GainKe00", "KnigZo00"],
                        "season": [2026, 2026], "week": [1, 1]})
    out = MODEL.snap_names_from_roster(snp, ros)
    assert out.player.tolist() == ["Kenny Gainwell", "Bam Knight", "No Id Guy"], "id first, name as fallback"
    assert out.player_snap_file.tolist()[0] == "Kenneth Gainwell"


def test_prior_shares_divide_by_every_active_week_with_one_team_per_week():
    """build_priors.active_week_denominators: a part-timer active 4 weeks with a touch in
    one counts all 4 weeks of team volume; a bye week adds nothing; in a trade week listed
    on both teams, the team he touched the ball for counts once."""
    import build_priors as BP
    tw = pd.DataFrame({"team": ["A"] * 4 + ["B"] * 4, "week": [1, 2, 3, 5, 3, 4, 5, 6],
                       "targets": [30, 30, 30, 30, 40, 40, 40, 40], "carries": [25] * 8,
                       "i10_targets": [2] * 8, "i10_carries": [3] * 8})          # A's bye is week 4
    ros = pd.DataFrame({"gsis_id": ["p"] * 4 + ["t"] * 6,
                        "team": ["A", "A", "A", "A", "A", "A", "A", "B", "B", "B"],
                        "week": [1, 2, 3, 4, 1, 2, 3, 3, 4, 5],
                        "status": ["ACT"] * 10})
    pw = pd.DataFrame({"gsis_id": ["p", "t", "t"], "team": ["A", "A", "B"], "week": [2, 1, 4]})
    den = BP.active_week_denominators(ros, pw, tw)
    assert den.loc["p", "targets"] == 90, "weeks 1-3 counted, the bye (4) has no team volume"
    # t: A weeks 1-2, week 3 listed on both (no touch) -> the later roster row (B), B weeks 4-5
    assert den.loc["t", "targets"] == 30 + 30 + 40 + 40 + 40, "one team per week in the trade week"
