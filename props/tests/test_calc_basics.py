"""props/calc unit tests: settings cap and freeze, odds, names, play rules,
the leakage cut, the Sleeper capture and the leg log."""

from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from props.calc import capture, data, log, names, odds, settings  # noqa: E402

# ------------------------------------------------------------------ settings

# The fixed constants as approved on 2026-10-10. They may not change after any
# test result has been read; changing one here is a visible, reviewed act.
FIXED = {
    "season_type": "REG", "rate_window_games": 16, "pool_seasons": 2, "depth_short_below": 5,
    "depth_deep_from": 15, "sims": 20000, "seed": 20261010, "range_low_pct": 10, "range_high_pct": 90,
    "result_margin": 8, "usual_games": 4, "tested_min_prior_games": 3, "top_targets": 3,
    "garbage_wp_low": 0.10, "garbage_wp_high": 0.90, "thin_games": 4, "tier_size": 8,
    "league_wide_first_season": 2018, "gap_edges": [0, 2, 4], "conversion_line_scales": [0.8, 1.0, 1.2],
    "pass_band_points": 3, "pass_band_min_games": 200, "pass_range_low": 77, "pass_range_high": 83,
    "round_trip_points": 1, "game_story_points": 1.5,
}


def test_settings_load_and_the_fixed_block_is_pinned():
    s = settings.load()
    assert s["fixed"] == FIXED
    assert len(s["tuned"]) <= 8 and set(s["tuned"]) == set(settings.TUNED_NAMES)


def test_a_ninth_setting_or_a_missing_comment_is_refused():
    text = settings.SETTINGS_PATH.read_text(encoding="utf-8")
    ninth = text.replace("tuned:\n", "tuned:\n  extra: 1   # one too many\n", 1)
    assert any("cap is 8" in p for p in settings.problems(ninth))
    bare = "\n".join("  carry_r: 16" if l.strip().startswith("carry_r:") else l for l in text.splitlines())
    assert any("carry_r has no plain-English comment" in p for p in settings.problems(bare))


# ------------------------------------------------------------------ odds

def test_odds_conversions():
    assert odds.american_from_multiplier(1.80) == -125
    assert odds.american_from_multiplier(2.50) == 150
    assert odds.american_from_multiplier(1.78) == -128
    assert odds.multiplier_from_american(-125) == pytest.approx(1.80)
    assert odds.multiplier_from_american(150) == pytest.approx(2.50)
    assert odds.break_even(1.80) == pytest.approx(0.5556, abs=1e-4)
    m_o, m_u = odds.multiplier_from_american(-125), odds.multiplier_from_american(-132)
    assert odds.no_vig(m_o, m_u) == pytest.approx((1 / m_o) / (1 / m_o + 1 / m_u))
    assert odds.no_vig(1.9, 1.9) == pytest.approx(0.5)
    with pytest.raises(ValueError):
        odds.break_even(1.0)
    with pytest.raises(ValueError):
        odds.multiplier_from_american(-50)


def test_entry_cost():
    c = odds.entry_cost(20, 5)
    assert c["per_leg"] == pytest.approx(0.5493, abs=1e-4)
    assert c["coin_flip_loss"] == pytest.approx(1 - 20 / 32)
    assert odds.entry_cost(10, 4)["per_leg"] == pytest.approx(0.5623, abs=1e-4)


# ------------------------------------------------------------------ names

CANDS = [{"gsis_id": "00-1", "name": "Josh Palmer", "team": "BUF"},
         {"gsis_id": "00-2", "name": "Christian McCaffrey", "team": "SF"},
         {"gsis_id": "00-3", "name": "Ja'Marr Chase", "team": "CIN"},
         {"gsis_id": "00-4", "name": "Puka Nacua", "team": "LA"},
         {"gsis_id": "00-5", "name": "Chris Smith", "team": "DAL"},
         {"gsis_id": "00-6", "name": "Cody Smith", "team": "DAL"}]


def test_name_matching():
    assert names.norm("Joshua Palmer Jr.") == "josh palmer"
    assert names.match("Joshua Palmer", "BUF", CANDS) == ("00-1", "name")
    assert names.match("C.McCaffrey", "SF", CANDS) == ("00-2", "initial")
    assert names.match("JaMarr Chase", "CIN", CANDS) == ("00-3", "name")
    assert names.match("Puka Nacua", "LAR", CANDS) == ("00-4", "name")       # Sleeper's LAR = nflverse LA


def test_name_misses_are_reported_not_guessed():
    gid, how = names.match("Christian McCaffrey", "KC", CANDS)               # wrong team
    assert gid is None and how.startswith("miss")
    gid, how = names.match("C.Smith", "DAL", CANDS)                          # two C. Smiths
    assert gid is None and "2 players" in how
    assert names.match("Nobody Here", "SF", CANDS)[0] is None
    assert names.match("Christian McCaffrey", None, CANDS)[0] is None


# ------------------------------------------------------------------ plays

def _plays():
    base = dict(game_id="g", season=2025, week=3, season_type="REG", posteam="SF", defteam="LA",
                home_team="SF", away_team="LA", rush_attempt=0, pass_attempt=0, complete_pass=0, sack=0,
                two_point_attempt=0, qb_kneel=0, rusher_player_id=None, receiver_player_id=None,
                passer_player_id=None, rushing_yards=np.nan, receiving_yards=np.nan, passing_yards=np.nan,
                air_yards=np.nan, wp=0.5, epa=0.0, success=0, play_type="run", qb_dropback=0, qb_scramble=0,
                lateral_receiver_player_id=None, lateral_receiving_yards=np.nan,
                lateral_rusher_player_id=None, lateral_rushing_yards=np.nan)
    rows = [
        dict(rush_attempt=1, rusher_player_id="rb", rushing_yards=5),
        dict(rush_attempt=1, rusher_player_id="rb", rushing_yards=-2),
        dict(rush_attempt=1, rusher_player_id="rb", rushing_yards=2, two_point_attempt=1),     # not a carry
        dict(rush_attempt=1, rusher_player_id="qb", rushing_yards=-1, qb_kneel=1),             # not a carry
        dict(pass_attempt=1, complete_pass=1, passer_player_id="qb", receiver_player_id="wr",
             receiving_yards=12, passing_yards=12, air_yards=8),
        dict(pass_attempt=1, passer_player_id="qb", receiver_player_id="wr", air_yards=20),    # NaN yards
        dict(pass_attempt=1, sack=1, passer_player_id="qb"),                                   # a sack
        dict(pass_attempt=1, complete_pass=1, passer_player_id="qb", receiver_player_id="te",
             receiving_yards=8, passing_yards=19, air_yards=3, lateral_receiver_player_id="rb",
             lateral_receiving_yards=11),                                                      # a lateral
    ]
    return pd.DataFrame([{**base, **r} for r in rows])


def test_play_rules_the_known_traps():
    p = _plays()
    c = data.carries(p)
    assert list(c["yards"]) == [5, -2]
    t = data.targets(p)
    assert len(t) == 3 and list(t["yards"]) == [12.0, 0.0, 8.0] and t["caught"].sum() == 2
    q = data.completions(p)
    assert list(q["yards"]) == [12, 19]
    g = data.player_games(p).set_index("gsis_id")
    assert g.loc["rb", "carries"] == 2 and g.loc["rb", "rush_yds"] == 3
    assert g.loc["wr", "targets"] == 2 and g.loc["wr", "receptions"] == 1 and g.loc["wr", "rec_yds"] == 12
    assert g.loc["qb", "completions"] == 2 and g.loc["qb", "pass_yds"] == 31 and g.loc["qb", "carries"] == 0
    # the lateral's 11 yards are the back's receiving yards, but not a target or a catch
    assert g.loc["rb", "rec_yds"] == 11 and g.loc["rb", "targets"] == 0 and g.loc["te", "rec_yds"] == 8


def test_the_leakage_cut():
    df = pd.DataFrame({"season": [2024, 2025, 2025, 2025, 2026], "week": [18, 2, 3, 4, 1]})
    kept = data.before(df, 2025, 3)
    assert list(zip(kept.season, kept.week)) == [(2024, 18), (2025, 2)]


def test_kickoffs_convert_eastern_to_utc():
    assert data.kickoff_utc("2026-09-13", "13:00") == "2026-09-13T17:00:00+00:00"     # EDT
    assert data.kickoff_utc("2026-11-08", "13:00") == "2026-11-08T18:00:00+00:00"     # EST from Nov 1
    assert data.kickoff_utc("2026-10-25", "20:20") == "2026-10-26T00:20:00+00:00"
    assert data.kickoff_utc("nan", "13:00") is None


# ------------------------------------------------------------------ capture

def _market(pid, wager, line, over, under, team="SF", status="pre_game"):
    return {"sport": "nfl", "wager_type": wager, "subject_id": pid, "game_id": "s1", "updated_at": 7,
            "line_type": "normal",
            "options": [{"outcome": "over", "status": "active", "payout_multiplier": over,
                         "outcome_value": line, "game_status": status, "subject_team": team},
                        {"outcome": "under", "status": "active", "payout_multiplier": under,
                         "outcome_value": line, "game_status": status, "subject_team": team}]}


GAMES = pd.DataFrame([
    {"game_id": "2026_06_LA_SF", "season": 2026, "week": 6, "home_team": "SF", "away_team": "LA",
     "kickoff_utc": "2026-10-12T00:20:00+00:00"},
    {"game_id": "2026_05_SF_X", "season": 2026, "week": 5, "home_team": "X", "away_team": "SF",
     "kickoff_utc": "2026-10-05T17:00:00+00:00"},
])


def test_capture_parse_keeps_what_it_should_and_logs_misses():
    raw = [_market("1", "rushing_yards", 64.5, 1.80, 1.76),
           _market("2", "receptions", 6.5, 1.78, 1.78),
           _market("3", "rushing_yards", 20.5, 1.8, 1.8),                       # a QB's rushing: skipped
           _market("4", "receiving_yards", 40.5, 1.8, 1.8),                     # unmatched: kept, logged
           _market("1", "anytime_touchdowns", 0.5, 2.5, 1.4),                    # not our market
           _market("2", "receiving_yards", 50.5, 1.8, 1.8, status="in_progress"),
           dict(_market("1", "receptions", 2.5, 1.8, 1.8), line_type="discount"),
           {**_market("2", "rushing_yards", 5.5, 1.8, 1.8), "sport": "nba"}]
    split = _market("2", "receiving_yards", 60.5, 1.8, 1.8)
    split["options"][1]["outcome_value"] = 61.5                              # sides at different lines
    raw.append(split)
    players = {"1": {"full_name": "Christian McCaffrey", "position": "RB", "team": "SF"},
               "2": {"full_name": "Puka Nacua", "position": "WR", "team": "LAR", "gsis_id": "00-4"},
               "3": {"full_name": "Brock Purdy", "position": "QB", "team": "SF"},
               "4": {"full_name": "Nobody Here", "position": "WR", "team": "SF"}}
    raw[1]["options"][0]["subject_team"] = raw[1]["options"][1]["subject_team"] = "LAR"
    at = dt.datetime(2026, 10, 9, 12, tzinfo=dt.timezone.utc)
    rows, misses = capture.parse(raw, players, {"1": "00-2"}, CANDS, GAMES, at)
    by = {(r["sleeper_id"], r["market"]): r for r in rows}
    assert set(by) == {("1", "rush_yds"), ("2", "receptions"), ("4", "rec_yds")}
    r = by[("1", "rush_yds")]
    assert r["gsis_id"] == "00-2" and r["matched_by"] == "sleeper_id" and r["line"] == 64.5
    assert r["mult_over"] == 1.80 and r["mult_under"] == 1.76
    assert r["game_id"] == "2026_06_LA_SF" and r["week"] == 6          # the next game, not last week's
    assert by[("2", "receptions")]["team"] == "LA" and by[("2", "receptions")]["matched_by"] == "sleeper_table_gsis"
    assert by[("4", "rec_yds")]["gsis_id"] is None
    assert len(misses) == 1 and misses[0]["sleeper_id"] == "4"


# ------------------------------------------------------------------ log

LEG = dict(season=2026, week=6, game_id="2026_06_LA_SF", kickoff_utc="2026-10-12T00:20:00+00:00",
           player="Christian McCaffrey", gsis_id="00-2", team="SF", market="rush_yds", side="over",
           line=64.5, mult_over=1.80, mult_under=1.76, target_rate=0.5556, book_expects=17.6,
           needed=19.1, usual=16.0, gap=3.1)


def test_log_settle_and_summary(tmp_path):
    path = tmp_path / "legs.jsonl"
    leg = log.log_leg(LEG, path=path, now="2026-10-10T12:00:00+00:00")
    log.log_leg({**LEG, "side": "under", "gap": -1.0}, path=path)
    with pytest.raises(ValueError):
        log.log_leg({k: v for k, v in LEG.items() if k != "needed"}, path=path)
    pg = pd.DataFrame([{"game_id": "2026_06_LA_SF", "season": 2026, "week": 6, "team": "SF", "gsis_id": "00-2",
                        "carries": 21, "rush_yds": 88.0, "targets": 3, "receptions": 2, "rec_yds": 10.0,
                        "completions": 0, "pass_yds": 0.0}])
    n = log.settle(2026, pg, path=path, lines_root=tmp_path / "none", archive_root=tmp_path / "none")
    assert n == 2
    assert log.settle(2026, pg, path=path, lines_root=tmp_path / "none", archive_root=tmp_path / "none") == 0
    legs = {x["side"]: x for x in log.read(path)}
    assert legs["over"]["id"] == leg["id"] and legs["over"]["result"] == "won"
    assert legs["over"]["actual_workload"] == 21 and legs["under"]["result"] == "lost"
    rows = log.summary(2026, [0, 2, 4], path=path)
    assert {(r["gap"], r["legs"], r["won"]) for r in rows} == {("2 to 4", 1, 1), ("0 or less", 1, 0)}
    assert len(path.read_text(encoding="utf-8").splitlines()) == 4          # append only


def test_result_rules():
    assert log.result("over", 64.5, 65) == "won" and log.result("under", 64.5, 65) == "lost"
    assert log.result("over", 5, 5) == "push" and log.result("over", 5.5, None) == "no stats"
    assert log.gap_group(0, [0, 2, 4]) == "0 or less" and log.gap_group(4.5, [0, 2, 4]) == "more than 4"


def test_line_near_kickoff_prefers_own_capture_then_archive(tmp_path):
    caps = tmp_path / "lines"
    rows = [dict(captured_at_utc=t, gsis_id="00-2", market="rush_yds", game_id="2026_06_LA_SF",
                 line=l, mult_over=1.8, mult_under=1.8) for t, l in
            (("2026-10-11T20:00:00+00:00", 64.5), ("2026-10-11T23:50:00+00:00", 66.5),
             ("2026-10-12T01:00:00+00:00", 70.5))]                              # last one is after kickoff
    capture.append_jsonl(caps / "2026" / "lines_2026.jsonl", rows)
    got = log.line_near_kickoff(LEG, lines_root=caps, archive_root=tmp_path / "none")
    assert got["source"] == "own capture" and got["line"] == 66.5

    arch = tmp_path / "arch" / "2026" / "line_archive_2026.jsonl"
    arch.parent.mkdir(parents=True)
    base = dict(bookmaker="sleeper", market="player_rush_yds", player="Christian McCaffrey",
                commence_time="2026-10-12T00:20:00+00:00")
    lines = [dict(base, outcome=o, point=65.5, price_american=p, retrieved_at_utc="2026-10-11T22:00:00Z")
             for o, p in (("Over", -125), ("Under", -105))]
    lines += [dict(base, outcome="Over", point=66.5, price_american=-120, retrieved_at_utc="2026-10-11T23:00:00Z",
                   player="Someone Else")]
    arch.write_text("\n".join(json.dumps(x) for x in lines), encoding="utf-8")
    got = log.line_near_kickoff(LEG, lines_root=tmp_path / "empty", archive_root=tmp_path / "arch")
    assert got["source"] == "engine archive" and got["line"] == 65.5 and got["american_over"] == -125


def test_settle_waits_for_the_game_and_handles_no_work_and_no_play(tmp_path):
    path = tmp_path / "legs.jsonl"
    log.log_leg({**LEG, "market": "receptions", "side": "under", "line": 2.5}, path=path)
    log.log_leg({**LEG, "gsis_id": "00-9", "player": "Sat Out"}, path=path)
    none = dict(lines_root=tmp_path / "none", archive_root=tmp_path / "none")
    # Thursday's game is in, his Sunday game is not: nothing settles yet
    thu = pd.DataFrame([{"game_id": "2026_06_X_Y", "season": 2026, "week": 6, "team": "X", "gsis_id": "00-7",
                         "carries": 10, "rush_yds": 40.0, "targets": 0, "receptions": 0, "rec_yds": 0.0,
                         "completions": 0, "pass_yds": 0.0}])
    assert log.settle(2026, thu, path=path, **none) == 0
    # his game is in: he played with no targets (a zero row from snaps); the other back did not play
    snaps = pd.DataFrame([{"game_id": "2026_06_LA_SF", "season": 2026, "week": 6, "team": "SF", "gsis_id": "00-2"}])
    games = data.games_played(thu.iloc[0:0], snaps)
    games = pd.concat([thu, games], ignore_index=True)
    assert log.settle(2026, games, path=path, **none) == 2
    legs = {x["gsis_id"]: x for x in log.read(path)}
    assert legs["00-2"]["result"] == "won" and legs["00-2"]["actual_workload"] == 0
    assert legs["00-9"]["result"] == "did not play"


def test_summary_survives_an_out_of_reach_leg(tmp_path):
    path = tmp_path / "legs.jsonl"
    log.log_leg({**LEG, "needed": None, "gap": None}, path=path)
    pg = pd.DataFrame([{"game_id": "2026_06_LA_SF", "season": 2026, "week": 6, "team": "SF", "gsis_id": "00-2",
                        "carries": 30, "rush_yds": 150.0, "targets": 0, "receptions": 0, "rec_yds": 0.0,
                        "completions": 0, "pass_yds": 0.0}])
    log.settle(2026, pg, path=path, lines_root=tmp_path / "n", archive_root=tmp_path / "n")
    rows = log.summary(2026, [0, 2, 4], path=path)
    assert rows[0]["gap"] == "out of reach" and rows[0]["needed"] is None and rows[0]["actual"] == 30


def test_played_maps_snaps_to_gsis_and_skips_zero_snaps():
    snap = pd.DataFrame([{"game_id": "g1", "season": 2026, "week": 1, "team": "SF", "pfr_player_id": "p1",
                          "offense_snaps": 30},
                         {"game_id": "g1", "season": 2026, "week": 1, "team": "SF", "pfr_player_id": "p2",
                          "offense_snaps": 0}])
    roster = pd.DataFrame([{"pfr_id": "p1", "gsis_id": "00-1"}, {"pfr_id": "p2", "gsis_id": "00-2"}])
    out = data.played(snap, roster)
    assert list(out["gsis_id"]) == ["00-1"]
