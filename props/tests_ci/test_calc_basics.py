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
    "min_pool_rb_carries": 5000, "min_pool_position_carries": 500, "min_pool_targets_per_bucket": 100, "min_own_carries": 30,
    "min_own_targets": 20, "league_ypc_range": [4.0, 5.0], "league_catch_rate_range": [0.60, 0.72],
    "league_yards_per_target_range": [6.5, 8.5],
    "max_count": {"carries": 80, "targets": 40, "completions": 60},
    "search_max": {"carries": 45, "targets": 25, "completions": 45},
    "rate_range": {"rush_yds": [0.0, 25.0], "receptions": [0.0, 1.0]}, "bisect_steps": 40,
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

def _market(pid, wager, line, over, under, team="SF", status="pre_game", game="202610601"):
    return {"sport": "nfl", "wager_type": wager, "subject_id": pid, "game_id": game, "updated_at": 7,
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
    reasons = {m["sleeper_id"]: m["reason"] for m in misses}
    assert set(reasons) == {"4", "2"} and reasons["2"].startswith("skipped: the two sides")   # traced, not dropped


def test_capture_refuses_a_player_on_the_wrong_team_or_without_a_game():
    at = dt.datetime(2026, 10, 9, 12, tzinfo=dt.timezone.utc)
    players = {"1": {"full_name": "Christian McCaffrey", "position": "RB", "team": "SF"}}
    # Sleeper says KC, the roster says SF: unmatched, logged
    rows, misses = capture.parse([_market("1", "rushing_yards", 64.5, 1.8, 1.8, team="KC")], players,
                                 {"1": "00-2"}, CANDS, GAMES, at)
    assert rows[0]["gsis_id"] is None and "roster says SF" in misses[0]["reason"]
    # right team, but no game left on the schedule: unmatched, logged
    late = dt.datetime(2027, 1, 1, tzinfo=dt.timezone.utc)
    rows, misses = capture.parse([_market("1", "rushing_yards", 64.5, 1.8, 1.8)], players,
                                 {"1": "00-2"}, CANDS, GAMES, late)
    assert rows[0]["gsis_id"] is None and "no game" in misses[0]["reason"]
    # Sleeper's game id says week 5, the schedule's next game is week 6: unmatched
    rows, misses = capture.parse([_market("1", "rushing_yards", 64.5, 1.8, 1.8, game="202610501")], players,
                                 {"1": "00-2"}, CANDS, GAMES, at)
    assert rows[0]["gsis_id"] is None and "not week 6" in misses[0]["reason"]
    assert capture.sleeper_game_agrees("202610501", {"season": 2026, "week": 5})
    assert not capture.sleeper_game_agrees("s1", {"season": 2026, "week": 5})


def test_name_clash_in_the_same_game():
    roster = pd.DataFrame([{"season": 2026, "week": 6, "team": t, "full_name": n, "gsis_id": g, "status": "ACT",
                            "position": "WR"}
                           for t, n, g in (("SF", "Mike Thomas", "a"), ("LA", "Michael Thomas", "b"),
                                           ("KC", "Christian McCaffrey", "c"))])
    assert log.name_clash({**LEG, "player": "Mike Thomas"}, roster)
    assert not log.name_clash(LEG, roster)
    assert not log.name_clash(LEG, ROSTER)                      # week 6 missing: week 5 is used
    with pytest.raises(Exception, match="no 2026 roster on file"):
        log.name_clash({**LEG, "game_id": "2026_06_NYJ_NE"}, ROSTER)
    with pytest.raises(Exception, match=r"\['KC'\]"):        # one team on file is not enough
        log.name_clash({**LEG, "game_id": "2026_06_KC_SF"}, ROSTER)


def test_rosters_as_of_a_week_keep_teams_on_bye():
    roster = pd.DataFrame([{"season": 2026, "week": w, "team": t, "full_name": n, "gsis_id": g, "status": "ACT"}
                           for w, t, n, g in ((4, "KC", "A", "a"), (5, "SF", "B", "b"), (6, "LA", "B", "b"))])
    assert {c["team"] for c in _cands(roster, 2026, 5)} == {"KC", "SF"}   # KC on bye in week 5
    assert {c["team"] for c in _cands(roster, 2026)} == {"KC", "LA"}       # b traded later


def test_capture_unmatches_a_sleeper_game_that_spans_two_nflverse_games():
    at = dt.datetime(2026, 10, 9, 12, tzinfo=dt.timezone.utc)
    games = pd.concat([GAMES, pd.DataFrame([{"game_id": "2026_06_KC_DAL", "season": 2026, "week": 6,
                                             "home_team": "DAL", "away_team": "KC",
                                             "kickoff_utc": "2026-10-11T17:00:00+00:00"}])], ignore_index=True)
    cands = CANDS + [{"gsis_id": "00-9", "name": "Dak Prescott", "team": "DAL"}]
    players = {"1": {"full_name": "Christian McCaffrey", "position": "RB", "team": "SF"},
               "9": {"full_name": "Dak Prescott", "position": "QB", "team": "DAL"}}
    raw = [_market("1", "rushing_yards", 64.5, 1.8, 1.8), _market("9", "passing_yards", 250.5, 1.8, 1.8, team="DAL")]
    rows, misses = capture.parse(raw, players, {"1": "00-2", "9": "00-9"}, cands, games, at)
    assert all(r["gsis_id"] is None for r in rows) and all("spans several" in m["reason"] for m in misses)


def test_a_saved_capture_is_rechecked_when_read(tmp_path):
    caps = tmp_path / "lines"
    capture.append_jsonl(caps / "2026" / "lines_2026.jsonl", [dict(
        captured_at_utc="2026-10-11T20:00:00+00:00", gsis_id="00-2", team="SF", market="rush_yds",
        game_id="2026_06_LA_SF", sleeper_game_id="202610501", line=64.5, mult_over=1.8, mult_under=1.8)])
    # saved by an older parser with a week-5 Sleeper game id for a week-6 leg: refused, and said so
    with pytest.raises(Exception, match="refused 1 own captures"):
        log.line_near_kickoff(LEG, ROSTER, lines_root=caps, archive_root=tmp_path / "none")


# ------------------------------------------------------------------ log

def _cands(roster, season, week=None):
    """The production path: roster_split, then candidates."""
    return data.candidates(data.roster_split(roster, season, week)[0])


# weekly rosters as of week 5 (week 6 not yet published): name_clash falls back to them
ROSTER = pd.DataFrame([{"season": 2026, "week": 5, "team": t, "full_name": n, "gsis_id": g, "status": "ACT",
                        "position": "RB"}
                       for t, n, g in (("SF", "Christian McCaffrey", "00-2"), ("LA", "Puka Nacua", "00-4"))])

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
    r = log.settle(2026, pg, ROSTER, ready=set(pg["game_id"]), path=path, lines_root=tmp_path / "none", archive_root=tmp_path / "none")
    assert r["settled"] == 2 and len(r["unmatched"]) == 2          # no saved lines: reported, not hidden
    assert log.settle(2026, pg, ROSTER, ready=set(pg["game_id"]), path=path, lines_root=tmp_path / "none",
                      archive_root=tmp_path / "none")["settled"] == 0
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
    rows = [dict(captured_at_utc=t, gsis_id="00-2", team="SF", market="rush_yds", game_id="2026_06_LA_SF",
                 sleeper_game_id="202610601",
                 line=l, mult_over=1.8, mult_under=1.8) for t, l in
            (("2026-10-11T20:00:00+00:00", 64.5), ("2026-10-11T23:50:00+00:00", 66.5),
             ("2026-10-12T01:00:00+00:00", 70.5))]                              # last one is after kickoff
    capture.append_jsonl(caps / "2026" / "lines_2026.jsonl", rows)
    got = log.line_near_kickoff(LEG, ROSTER, lines_root=caps, archive_root=tmp_path / "none")
    assert got["source"] == "own capture" and got["line"] == 66.5

    arch = tmp_path / "arch" / "2026" / "line_archive_2026.jsonl"
    arch.parent.mkdir(parents=True)
    base = dict(bookmaker="sleeper", market="player_rush_yds", player="Christian McCaffrey", week=6,
                commence_time="2026-10-12T00:20:00+00:00", home_team="San Francisco 49ers",
                away_team="Los Angeles Rams")
    lines = [dict(base, outcome=o, point=65.5, price_american=p, retrieved_at_utc="2026-10-11T22:00:00Z")
             for o, p in (("Over", -125), ("Under", -105))]
    lines += [dict(base, outcome="Over", point=66.5, price_american=-120, retrieved_at_utc="2026-10-11T23:00:00Z",
                   player="Someone Else")]
    arch.write_text("\n".join(json.dumps(x) for x in lines), encoding="utf-8")
    got = log.line_near_kickoff(LEG, ROSTER, lines_root=tmp_path / "empty", archive_root=tmp_path / "arch")
    assert got["source"] == "engine archive" and got["line"] == 65.5 and got["mult_over"] == pytest.approx(1.8)
    # same name and kickoff, but his team is not in that game: unmatched
    assert log.line_near_kickoff({**LEG, "team": "KC", "game_id": "2026_06_KC_SF"},
                                 pd.concat([ROSTER, pd.DataFrame([{"season": 2026, "week": 5, "team": "KC",
                                                                   "full_name": "X", "gsis_id": "x",
                                                                   "status": "ACT", "position": "RB"}])]),
                                 lines_root=tmp_path / "empty", archive_root=tmp_path / "arch") is None
    # a namesake in the same game: the archive cannot tell them apart, so unmatched
    clash = pd.concat([ROSTER, pd.DataFrame([{"season": 2026, "week": 5, "team": "LA", "status": "ACT",
                                              "position": "RB", "full_name": "Christian McCaffrey",
                                              "gsis_id": "00-99"}])])
    with pytest.raises(Exception, match="found but refused"):    # the reason is reported, not "no line"
        log.line_near_kickoff(LEG, clash, lines_root=tmp_path / "empty", archive_root=tmp_path / "arch")
    # an own capture with the right id but another team is not his line either
    assert log.line_near_kickoff({**LEG, "team": "KC"}, ROSTER, lines_root=caps, archive_root=tmp_path / "none") is None


def test_settle_waits_for_the_game_and_handles_no_work_and_no_play(tmp_path):
    path = tmp_path / "legs.jsonl"
    log.log_leg({**LEG, "market": "receptions", "side": "under", "line": 2.5}, path=path)
    log.log_leg({**LEG, "gsis_id": "00-9", "player": "Sat Out"}, path=path)
    none = dict(lines_root=tmp_path / "none", archive_root=tmp_path / "none")
    # Thursday's game is in, his Sunday game is not: nothing settles yet
    thu = pd.DataFrame([{"game_id": "2026_06_X_Y", "season": 2026, "week": 6, "team": "X", "gsis_id": "00-7",
                         "carries": 10, "rush_yds": 40.0, "targets": 0, "receptions": 0, "rec_yds": 0.0,
                         "completions": 0, "pass_yds": 0.0}])
    assert log.settle(2026, thu, ROSTER, ready=set(thu["game_id"]), path=path, **none)["settled"] == 0
    # his game is in: he played with no targets (a zero row from snaps); the other back did not play
    snaps = pd.DataFrame([{"game_id": "2026_06_LA_SF", "season": 2026, "week": 6, "team": "SF", "gsis_id": "00-2"}])
    sf = thu.assign(game_id="2026_06_LA_SF", gsis_id="00-8", team="LA")     # the game's plays are loaded
    games = pd.concat([thu, data.games_played(sf, snaps)], ignore_index=True)
    assert log.settle(2026, games, ROSTER, ready=set(games["game_id"]), path=path, **none)["settled"] == 2
    legs = {x["gsis_id"]: x for x in log.read(path)}
    assert legs["00-2"]["result"] == "won" and legs["00-2"]["actual_workload"] == 0
    assert legs["00-9"]["result"] == "did not play"


def test_summary_survives_an_out_of_reach_leg(tmp_path):
    path = tmp_path / "legs.jsonl"
    log.log_leg({**LEG, "needed": None, "gap": None}, path=path)
    pg = pd.DataFrame([{"game_id": "2026_06_LA_SF", "season": 2026, "week": 6, "team": "SF", "gsis_id": "00-2",
                        "carries": 30, "rush_yds": 150.0, "targets": 0, "receptions": 0, "rec_yds": 0.0,
                        "completions": 0, "pass_yds": 0.0}])
    log.settle(2026, pg, ROSTER, ready=set(pg["game_id"]), path=path, lines_root=tmp_path / "n", archive_root=tmp_path / "n")
    rows = log.summary(2026, [0, 2, 4], path=path)
    assert rows[0]["gap"] == "no gap (logged without a status)" and rows[0]["needed"] is None and rows[0]["actual"] == 30
    log.log_leg({**LEG, "side": "under", "needed": None, "gap": None, "needed_status": "high"}, path=path)
    log.log_leg({**LEG, "needed": None, "gap": None, "needed_status": "high"}, path=path)
    log.settle(2026, pg, ROSTER, ready=set(pg["game_id"]), path=path, lines_root=tmp_path / "n", archive_root=tmp_path / "n")
    groups = {r["gap"] for r in log.summary(2026, [0, 2, 4], path=path)}
    assert {"Under wins at any workload", "out of reach"} <= groups


def test_played_maps_snaps_to_gsis_and_skips_zero_snaps():
    snap = pd.DataFrame([{"game_id": "g1", "season": 2026, "week": 1, "team": "SF", "pfr_player_id": "p1",
                          "offense_snaps": 30},
                         {"game_id": "g1", "season": 2026, "week": 1, "team": "SF", "pfr_player_id": "p2",
                          "offense_snaps": 0}])
    roster = pd.DataFrame([{"pfr_id": "p1", "gsis_id": "00-1"}, {"pfr_id": "p2", "gsis_id": "00-2"}])
    out = data.played(snap, roster)
    assert list(out["gsis_id"]) == ["00-1"]


def test_namesakes_are_skill_players_still_on_the_team():
    roster = pd.DataFrame([
        {"season": 2026, "week": 5, "team": "SF", "full_name": "Christian McCaffrey", "gsis_id": "00-2",
         "position": "RB", "status": "ACT"},
        {"season": 2026, "week": 5, "team": "LA", "full_name": "Christian McCaffrey", "gsis_id": "db",
         "position": "DB", "status": "DEV"},                                  # a practice-squad DB: no namesake
        {"season": 2026, "week": 1, "team": "LA", "full_name": "Christian McCaffrey", "gsis_id": "cut",
         "position": "RB", "status": "CUT"}])                                 # cut in week 1: not on the team
    assert not log.name_clash(LEG, roster)
    assert {c["gsis_id"] for c in _cands(roster, 2026, 5)} == {"00-2", "db"}


def test_a_player_off_his_teams_latest_roster_is_not_on_it():
    roster = pd.DataFrame([{"season": 2026, "week": w, "team": t, "full_name": n, "gsis_id": g, "status": "ACT"}
                           for w, t, n, g in ((3, "NYG", "Gone Guy", "g"), (4, "NYG", "Stays", "s"),
                                              (4, "KC", "Bye Team", "k"), (5, "NYG", "Stays", "s"))])
    got = {c["gsis_id"]: c["team"] for c in _cands(roster, 2026, 5)}
    assert got == {"s": "NYG", "k": "KC"}          # g left NYG's roster without a CUT row; KC kept through its bye


def test_settle_reports_a_leg_it_cannot_check_and_settles_the_rest(tmp_path):
    path = tmp_path / "legs.jsonl"
    log.log_leg(LEG, path=path)
    log.log_leg({**LEG, "game_id": "2026_06_NYJ_NE", "team": "NE", "gsis_id": "00-7", "player": "Other"}, path=path)
    arch = tmp_path / "arch" / "2026" / "line_archive_2026.jsonl"
    arch.parent.mkdir(parents=True)
    arch.write_text("\n".join(json.dumps({"bookmaker": "sleeper", "market": "player_rush_yds", "player": "Other",
                                           "week": 6, "commence_time": "2026-10-12T00:20:00+00:00", "outcome": o,
                                           "point": 50.5, "price_american": -120,
                                           "retrieved_at_utc": "2026-10-11T20:00:00Z",
                                           "home_team": "New England Patriots", "away_team": "New York Jets"})
                              for o in ("Over", "Under")), encoding="utf-8")
    pg = pd.DataFrame([dict(game_id=g, season=2026, week=6, team=t, gsis_id=i, carries=10, rush_yds=70.0,
                            targets=0, receptions=0, rec_yds=0.0, completions=0, pass_yds=0.0)
                       for g, t, i in (("2026_06_LA_SF", "SF", "00-2"), ("2026_06_NYJ_NE", "NE", "00-7"))])
    r = log.settle(2026, pg, ROSTER, ready=set(pg["game_id"]), path=path, lines_root=tmp_path / "none", archive_root=tmp_path / "arch")
    assert r["settled"] == 2                                   # NYJ/NE have no roster: reported, not fatal
    assert any("Other" in u and "no 2026 roster" in u for u in r["unmatched"])


def test_malformed_archive_rows_fail_loudly(tmp_path):
    arch = tmp_path / "arch" / "2026" / "line_archive_2026.jsonl"
    arch.parent.mkdir(parents=True)
    rows = [{"bookmaker": "sleeper", "market": "player_rush_yds", "player": "Christian McCaffrey", "week": w,
             "home_team": "San Francisco 49ers", "away_team": "Los Angeles Rams", "commence_time": "not a time", "retrieved_at_utc": "x"} for w in (6, 3)]
    arch.write_text(json.dumps(rows[0]), encoding="utf-8")
    with pytest.raises(Exception, match="not a readable time"):
        log.line_near_kickoff(LEG, ROSTER, lines_root=tmp_path / "none", archive_root=tmp_path / "arch")
    arch.write_text(json.dumps(rows[1]), encoding="utf-8")                   # another week's bad row
    assert log.line_near_kickoff(LEG, ROSTER, lines_root=tmp_path / "none", archive_root=tmp_path / "arch") is None
    arch.write_text(json.dumps({**rows[0], "commence_time": None, "retrieved_at_utc": None}), encoding="utf-8")
    with pytest.raises(Exception, match="not a readable time|is empty"):
        log.line_near_kickoff(LEG, ROSTER, lines_root=tmp_path / "none", archive_root=tmp_path / "arch")


def test_a_missing_line_near_kickoff_is_filled_in_on_a_later_settle(tmp_path):
    path = tmp_path / "legs.jsonl"
    log.log_leg(LEG, path=path)
    pg = pd.DataFrame([{"game_id": "2026_06_LA_SF", "season": 2026, "week": 6, "team": "SF", "gsis_id": "00-2",
                        "carries": 21, "rush_yds": 88.0, "targets": 0, "receptions": 0, "rec_yds": 0.0,
                        "completions": 0, "pass_yds": 0.0}])
    caps = tmp_path / "lines"
    r = log.settle(2026, pg, ROSTER, ready=set(pg["game_id"]), path=path, lines_root=caps, archive_root=tmp_path / "none")
    assert r["settled"] == 1 and log.read(path)[0]["kickoff_line"] is None
    r = log.settle(2026, pg, ROSTER, ready=set(pg["game_id"]), path=path, lines_root=caps, archive_root=tmp_path / "none")
    assert r["settled"] == 0 and r["unmatched"] == [] and len(r["still_missing"]) == 1   # not re-reported as new
    capture.append_jsonl(caps / "2026" / "lines_2026.jsonl", [dict(
        captured_at_utc="2026-10-11T20:00:00+00:00", gsis_id="00-2", team="SF", market="rush_yds",
        game_id="2026_06_LA_SF", sleeper_game_id="202610601", line=64.5, mult_over=1.8, mult_under=1.8)])
    r = log.settle(2026, pg, ROSTER, ready=set(pg["game_id"]), path=path, lines_root=caps, archive_root=tmp_path / "none")
    leg = log.read(path)[0]
    assert r["settled"] == 0 and r["filled"] == 1 and leg["kickoff_line"]["line"] == 64.5 and leg["result"] == "won"


def test_one_stale_row_does_not_unmatch_its_whole_game():
    at = dt.datetime(2026, 10, 9, 12, tzinfo=dt.timezone.utc)
    games = pd.concat([GAMES, pd.DataFrame([{"game_id": "2026_06_KC_DAL", "season": 2026, "week": 6,
                                             "home_team": "DAL", "away_team": "KC",
                                             "kickoff_utc": "2026-10-11T17:00:00+00:00"}])], ignore_index=True)
    cands = CANDS + [{"gsis_id": "00-9", "name": "Dak Prescott", "team": "DAL"}]
    players = {"1": {"full_name": "Christian McCaffrey", "position": "RB", "team": "SF"},
               "2": {"full_name": "Puka Nacua", "position": "WR", "team": "LA", "gsis_id": "00-4"},
               "9": {"full_name": "Dak Prescott", "position": "QB", "team": "DAL"}}
    raw = [_market("1", "rushing_yards", 64.5, 1.8, 1.8), _market("2", "receptions", 6.5, 1.8, 1.8, team="LA"),
           _market("9", "passing_yards", 250.5, 1.8, 1.8, team="DAL")]       # all in Sleeper game 202610601
    rows, misses = capture.parse(raw, players, {"1": "00-2", "9": "00-9"}, cands, games, at)
    by = {r["sleeper_id"]: r for r in rows}
    assert by["1"]["gsis_id"] == "00-2" and by["2"]["gsis_id"] == "00-4"     # the two SF/LA rows agree
    assert by["9"]["gsis_id"] is None and len(misses) == 1                   # only the odd one out
    # one player's several markets do not outvote the others: teams are counted, not rows
    raw = [_market("1", "rushing_yards", 64.5, 1.8, 1.8)] + [
        _market("9", w, 50.5, 1.8, 1.8, team="DAL") for w in ("passing_yards", "rushing_yards", "receptions")]
    players["9"]["position"] = "WR"
    rows, _ = capture.parse(raw, players, {"1": "00-2", "9": "00-9"}, cands, games, at)
    assert all(r["gsis_id"] is None for r in rows)                            # 1 team each: a tie, so none kept


def test_traded_players_and_unlisted_namesakes():
    roster = pd.DataFrame([
        {"season": 2026, "week": 5, "team": "SF", "full_name": "Christian McCaffrey", "gsis_id": "00-2",
         "position": "RB", "status": "ACT"},
        {"season": 2026, "week": 5, "team": "LA", "full_name": "Traded Guy", "gsis_id": "t",
         "position": "RB", "status": "TRD"},
        {"season": 2026, "week": 5, "team": "LA", "full_name": "Christian McCaffrey", "gsis_id": None,
         "position": "RB", "status": "DEV"}])
    assert "t" not in {c["gsis_id"] for c in _cands(roster, 2026, 5)}
    assert log.name_clash(LEG, roster)          # the same name with no gsis id is still someone else


def test_saved_rows_without_a_time_zone_or_not_objects_fail_loudly(tmp_path):
    arch = tmp_path / "arch" / "2026" / "line_archive_2026.jsonl"
    arch.parent.mkdir(parents=True)
    row = {"bookmaker": "sleeper", "market": "player_rush_yds", "player": "Christian McCaffrey", "week": 6,
           "home_team": "San Francisco 49ers", "away_team": "Los Angeles Rams", "commence_time": "2026-10-12T00:20:00+00:00", "retrieved_at_utc": "2026-10-11T22:00:00"}
    arch.write_text(json.dumps(row), encoding="utf-8")
    with pytest.raises(Exception, match="no time zone"):
        log.line_near_kickoff(LEG, ROSTER, lines_root=tmp_path / "none", archive_root=tmp_path / "arch")
    arch.write_text("[1, 2]\n", encoding="utf-8")
    with pytest.raises(Exception, match="not a JSON object"):
        log.line_near_kickoff(LEG, ROSTER, lines_root=tmp_path / "none", archive_root=tmp_path / "arch")


def test_a_redo_keeps_the_first_result(tmp_path):
    path = tmp_path / "legs.jsonl"
    log.log_leg(LEG, path=path)
    pg = pd.DataFrame([{"game_id": "2026_06_LA_SF", "season": 2026, "week": 6, "team": "SF", "gsis_id": "00-2",
                        "carries": 21, "rush_yds": 88.0, "targets": 0, "receptions": 0, "rec_yds": 0.0,
                        "completions": 0, "pass_yds": 0.0}])
    caps = tmp_path / "lines"
    log.settle(2026, pg, ROSTER, ready=set(pg["game_id"]), path=path, lines_root=caps, archive_root=tmp_path / "none")
    capture.append_jsonl(caps / "2026" / "lines_2026.jsonl", [dict(
        captured_at_utc="2026-10-11T20:00:00+00:00", gsis_id="00-2", team="SF", market="rush_yds",
        game_id="2026_06_LA_SF", sleeper_game_id="202610601", line=64.5, mult_over=1.8, mult_under=1.8)])
    corrected = pg.assign(rush_yds=40.0)                    # the stats changed after the first settle
    log.settle(2026, corrected, ROSTER, ready=set(corrected["game_id"]), path=path, lines_root=caps, archive_root=tmp_path / "none")
    leg = log.read(path)[0]
    assert leg["result"] == "won" and leg["actual"] == 88.0 and leg["kickoff_line"]["line"] == 64.5


def test_a_departed_listing_never_hides_an_active_one():  # noqa: D103
    rows = [{"season": 2026, "week": 5, "team": t, "full_name": "P", "gsis_id": "p", "status": st}
            for t, st in (("SF", "ACT"), ("LA", "TRD"))]
    filler = [{"season": 2026, "week": 5, "team": "KC", "full_name": f"x{i}", "gsis_id": f"x{i}", "status": "ACT"}
              for i in range(60)]
    for order in (rows + filler, list(reversed(rows + filler))):
        got = {c["gsis_id"]: c["team"] for c in _cands(pd.DataFrame(order), 2026, 5)}
        assert got["p"] == "SF"


def test_rosters_without_a_status_column_fail_loudly():
    with pytest.raises(Exception, match="no status column"):
        _cands(pd.DataFrame([{"season": 2026, "week": 5, "team": "SF", "full_name": "P",
                                              "gsis_id": "p"}]), 2026, 5)


def test_unreadable_own_captures_fall_back_to_the_archive_with_a_note(tmp_path):
    caps = tmp_path / "lines" / "2026" / "lines_2026.jsonl"
    caps.parent.mkdir(parents=True)
    caps.write_text('{"captured_at_utc": "2026-10-11T20:00:00+00:00", "gsis_id": "00-2"', encoding="utf-8")  # cut off
    arch = tmp_path / "arch" / "2026" / "line_archive_2026.jsonl"
    arch.parent.mkdir(parents=True)
    base = dict(bookmaker="sleeper", market="player_rush_yds", player="Christian McCaffrey", week=6, point=65.5,
                commence_time="2026-10-12T00:20:00+00:00", retrieved_at_utc="2026-10-11T22:00:00Z",
                home_team="San Francisco 49ers", away_team="Los Angeles Rams")
    arch.write_text("\n".join(json.dumps(dict(base, outcome=o, price_american=p))
                              for o, p in (("Over", -125), ("Under", -105))), encoding="utf-8")
    got = log.line_near_kickoff(LEG, ROSTER, lines_root=tmp_path / "lines", archive_root=tmp_path / "arch")
    assert got["source"] == "engine archive" and "own captures not used" in got["note"]


def test_bad_saved_prices_and_weeks_fail_as_data_errors(tmp_path):
    from props.calc.checks import DataError
    caps = tmp_path / "lines"
    capture.append_jsonl(caps / "2026" / "lines_2026.jsonl", [dict(
        captured_at_utc="2026-10-11T20:00:00+00:00", gsis_id="00-2", team="SF", market="rush_yds",
        game_id="2026_06_LA_SF", sleeper_game_id="202610601", line=64.5, mult_over=1.0, mult_under=1.8)])
    with pytest.raises(DataError, match="payout multiplier"):
        log.line_near_kickoff(LEG, ROSTER, lines_root=caps, archive_root=tmp_path / "none")
    arch = tmp_path / "arch" / "2026" / "line_archive_2026.jsonl"
    arch.parent.mkdir(parents=True)
    arch.write_text(json.dumps({"bookmaker": "sleeper", "market": "player_rush_yds", "player": "Christian McCaffrey",
                                "home_team": "San Francisco 49ers", "away_team": "Los Angeles Rams",
                                "week": "6"}), encoding="utf-8")
    with pytest.raises(DataError, match="no usable week"):
        log.line_near_kickoff(LEG, ROSTER, lines_root=tmp_path / "none", archive_root=tmp_path / "arch")
    arch.write_text(json.dumps({"bookmaker": "sleeper", "market": "player_rush_yds", "player": "Christian McCaffrey",
                                "week": 6}), encoding="utf-8")
    with pytest.raises(DataError, match="names no teams"):
        log.line_near_kickoff(LEG, ROSTER, lines_root=tmp_path / "none", archive_root=tmp_path / "arch")


def test_a_player_on_two_teams_in_the_same_week_is_set_aside_not_guessed():
    roster = pd.DataFrame([{"season": 2026, "week": 5, "team": t, "full_name": n, "gsis_id": g, "status": "ACT",
                            "position": "RB"}
                           for t, n, g in (("SF", "P", "p"), ("LA", "P", "p"), ("SF", "Christian McCaffrey", "00-2"),
                                           ("LA", "Q", "q"))])
    got = {c["gsis_id"] for c in _cands(roster, 2026, 5)}
    assert got == {"00-2", "q"}                                  # p is on neither team, and nothing stops
    assert list(data.roster_split(roster, 2026, 5)[1]["gsis_id"].unique()) == ["p"]
    # a namesake who is set aside still blocks a name-only archive line
    amb = pd.concat([roster, pd.DataFrame([{"season": 2026, "week": 5, "team": t, "full_name": "Christian McCaffrey",
                                            "gsis_id": "x", "status": "ACT", "position": "RB"} for t in ("LA", "KC")])])
    assert log.name_clash(LEG, amb)
    # ...but not one on two other teams, or one who is not a skill player
    far = pd.concat([roster, pd.DataFrame([{"season": 2026, "week": 5, "team": t, "full_name": "Christian McCaffrey",
                                            "gsis_id": "x", "status": "ACT", "position": "RB"} for t in ("NYJ", "KC")])])
    assert not log.name_clash(LEG, far)
    db = pd.concat([roster, pd.DataFrame([{"season": 2026, "week": 5, "team": t, "full_name": "Christian McCaffrey",
                                           "gsis_id": "x", "status": "ACT", "position": "DB"} for t in ("LA", "KC")])])
    assert not log.name_clash(LEG, db)


def test_a_game_id_without_two_teams_fails_loudly():
    with pytest.raises(Exception, match="does not name two teams"):
        log.name_clash({**LEG, "game_id": "LA-SF"}, ROSTER)


def test_one_bad_capture_row_does_not_hide_an_older_good_one(tmp_path):
    caps = tmp_path / "lines"
    good = dict(captured_at_utc="2026-10-11T20:00:00+00:00", gsis_id="00-2", team="SF", market="rush_yds",
                game_id="2026_06_LA_SF", sleeper_game_id="202610601", line=64.5, mult_over=1.8, mult_under=1.8)
    capture.append_jsonl(caps / "2026" / "lines_2026.jsonl",
                         [good, {**good, "captured_at_utc": "2026-10-11T23:00:00+00:00", "mult_over": 1.0}])
    got = log.line_near_kickoff(LEG, ROSTER, lines_root=caps, archive_root=tmp_path / "none")
    assert got["at_utc"].startswith("2026-10-11T20") and "skipped 1 unreadable" in got["note"]


def test_another_teams_namesake_with_a_bad_row_does_not_block_him(tmp_path):
    arch = tmp_path / "arch" / "2026" / "line_archive_2026.jsonl"
    arch.parent.mkdir(parents=True)
    base = dict(bookmaker="sleeper", market="player_rush_yds", player="Christian McCaffrey", week=6, point=65.5,
                commence_time="2026-10-12T00:20:00+00:00", retrieved_at_utc="2026-10-11T22:00:00Z",
                home_team="San Francisco 49ers", away_team="Los Angeles Rams")
    rows = [dict(base, outcome=o, price_american=p) for o, p in (("Over", -125), ("Under", -105))]
    rows.append(dict(base, home_team="New York Jets", away_team="New England Patriots", week="6", outcome="Over"))
    arch.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
    got = log.line_near_kickoff(LEG, ROSTER, lines_root=tmp_path / "none", archive_root=tmp_path / "arch")
    assert got["line"] == 65.5


def test_the_newest_archive_quote_is_chosen_by_time_not_text(tmp_path):
    arch = tmp_path / "arch" / "2026" / "line_archive_2026.jsonl"
    arch.parent.mkdir(parents=True)
    base = dict(bookmaker="sleeper", market="player_rush_yds", player="Christian McCaffrey", week=6,
                commence_time="2026-10-12T00:20:00+00:00", home_team="San Francisco 49ers",
                away_team="Los Angeles Rams")
    rows = []
    for at, pt in (("2026-10-11T23:00:00+00:00", 66.5), ("2026-10-11T22:30:00Z", 65.5)):  # "+00:00" sorts after "Z"? no
        rows += [dict(base, retrieved_at_utc=at, point=pt, outcome=o, price_american=-115) for o in ("Over", "Under")]
    arch.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
    got = log.line_near_kickoff(LEG, ROSTER, lines_root=tmp_path / "none", archive_root=tmp_path / "arch")
    assert got["line"] == 66.5                        # 23:00 is later than 22:30, whatever the suffix


def test_capture_drops_qb_rushing_before_logging_anything():
    at = dt.datetime(2026, 10, 9, 12, tzinfo=dt.timezone.utc)
    one_sided = _market("3", "rushing_yards", 20.5, 1.8, 1.8)
    one_sided["options"] = one_sided["options"][:1]
    players = {"3": {"full_name": "Brock Purdy", "position": "QB", "team": "SF"}}
    rows, misses = capture.parse([one_sided], players, {}, CANDS, GAMES, at)
    assert rows == [] and misses == []


def test_infinite_numbers_fail_loudly():
    from props.calc import checks
    with pytest.raises(checks.DataError):
        checks.number(float("inf"), "x")
    with pytest.raises(checks.DataError):
        checks.multiplier(float("inf"), "x")


def _arch_rows(**kw):
    base = dict(bookmaker="sleeper", market="player_rush_yds", player="Christian McCaffrey", week=6, point=65.5,
                commence_time="2026-10-12T00:20:00+00:00", retrieved_at_utc="2026-10-11T22:00:00Z",
                home_team="San Francisco 49ers", away_team="Los Angeles Rams")
    return [dict(base, outcome=o, price_american=p, **kw) for o, p in (("Over", -125), ("Under", -105))]


def test_archive_rows_with_an_id_join_by_it(tmp_path):
    arch = tmp_path / "arch" / "2026" / "line_archive_2026.jsonl"
    arch.parent.mkdir(parents=True)
    clash = pd.concat([ROSTER, pd.DataFrame([{"season": 2026, "week": 5, "team": "LA", "status": "ACT",
                                              "position": "RB", "full_name": "Christian McCaffrey",
                                              "gsis_id": "00-99"}])])
    # his id on the rows: used even with a namesake in the game
    arch.write_text("\n".join(json.dumps(r) for r in _arch_rows(gsis_id="00-2")), encoding="utf-8")
    got = log.line_near_kickoff(LEG, clash, lines_root=tmp_path / "none", archive_root=tmp_path / "arch")
    assert got["line"] == 65.5
    # the same name but another player's id: never his line
    arch.write_text("\n".join(json.dumps(r) for r in _arch_rows(gsis_id="00-99")), encoding="utf-8")
    assert log.line_near_kickoff(LEG, ROSTER, lines_root=tmp_path / "none", archive_root=tmp_path / "arch") is None


def test_a_refused_own_capture_is_noted_when_the_archive_is_used(tmp_path):
    caps = tmp_path / "lines"
    capture.append_jsonl(caps / "2026" / "lines_2026.jsonl", [dict(
        captured_at_utc="2026-10-11T23:00:00+00:00", gsis_id="00-2", team="SF", market="rush_yds",
        game_id="2026_06_LA_SF", sleeper_game_id="202610501", line=66.5, mult_over=1.8, mult_under=1.8)])
    arch = tmp_path / "arch" / "2026" / "line_archive_2026.jsonl"
    arch.parent.mkdir(parents=True)
    arch.write_text("\n".join(json.dumps(r) for r in _arch_rows()), encoding="utf-8")
    got = log.line_near_kickoff(LEG, ROSTER, lines_root=caps, archive_root=tmp_path / "arch")
    assert got["source"] == "engine archive" and "refused 1 own captures" in got["note"]


def test_another_weeks_or_teams_broken_row_does_not_block_him(tmp_path):
    arch = tmp_path / "arch" / "2026" / "line_archive_2026.jsonl"
    arch.parent.mkdir(parents=True)
    broken = [dict(_arch_rows()[0], week=3, home_team=None),                       # week 3, no teams
              dict(_arch_rows()[0], week=None, home_team="New York Jets", away_team="New England Patriots")]
    arch.write_text("\n".join(json.dumps(r) for r in _arch_rows() + broken), encoding="utf-8")
    got = log.line_near_kickoff(LEG, ROSTER, lines_root=tmp_path / "none", archive_root=tmp_path / "arch")
    assert got["line"] == 65.5


def test_a_newer_one_sided_snapshot_is_passed_over_and_noted(tmp_path):
    arch = tmp_path / "arch" / "2026" / "line_archive_2026.jsonl"
    arch.parent.mkdir(parents=True)
    rows = _arch_rows() + [dict(_arch_rows()[0], retrieved_at_utc="2026-10-11T23:30:00Z", point=67.5)]
    arch.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
    got = log.line_near_kickoff(LEG, ROSTER, lines_root=tmp_path / "none", archive_root=tmp_path / "arch")
    assert got["line"] == 65.5 and "passed over 1 newer" in got["note"]


def test_a_saved_line_of_zero_fails_as_data():
    from props.calc.checks import DataError
    with pytest.raises(DataError, match="not above 0"):
        log._line(0, "a captured line")


def test_an_empty_roster_slice_is_handled_not_a_crash():
    roster = pd.DataFrame([{"season": 2026, "week": 3, "team": "SF", "full_name": "P", "gsis_id": "p",
                            "status": "ACT", "position": "RB"}])
    assert _cands(roster, 2026, 2) == []            # before the first roster week
    assert _cands(roster, 2027) == []                # another season


def test_a_leg_with_no_kickoff_time_fails_loudly(tmp_path):
    with pytest.raises(Exception, match="kickoff time"):
        log.line_near_kickoff({**LEG, "kickoff_utc": None}, ROSTER, lines_root=tmp_path, archive_root=tmp_path)


def test_capture_skips_a_malformed_option_and_keeps_the_rest():
    at = dt.datetime(2026, 10, 9, 12, tzinfo=dt.timezone.utc)
    bad = _market("1", "rushing_yards", 64.5, None, 1.8)
    good = _market("2", "receptions", 6.5, 1.78, 1.78, team="LA")
    players = {"1": {"full_name": "Christian McCaffrey", "position": "RB", "team": "SF"},
               "2": {"full_name": "Puka Nacua", "position": "WR", "team": "LA", "gsis_id": "00-4"}}
    rows, misses = capture.parse([bad, good], players, {"1": "00-2"}, CANDS, GAMES, at)
    assert [r["sleeper_id"] for r in rows] == ["2"] and "not a number" in misses[0]["reason"]


def test_a_tie_on_teams_is_broken_by_players_not_rows():
    rows = [dict(gsis_id=g, game_id="2026_06_LA_SF", team="SF", sleeper_game_id="s") for g in ("a", "b", "c")]
    rows.append(dict(gsis_id="k", game_id="2026_06_KC_DAL", team="KC", sleeper_game_id="s"))
    assert capture.game_majority(rows) == {"s": "2026_06_LA_SF"}       # 1 team each; 3 players to 1
    rows = rows[:1] + rows[3:]
    assert capture.game_majority(rows) == {}                            # 1 team and 1 player each: refused


def test_a_bad_newest_archive_snapshot_does_not_hide_an_older_good_one(tmp_path):
    arch = tmp_path / "arch" / "2026" / "line_archive_2026.jsonl"
    arch.parent.mkdir(parents=True)
    newer = [dict(r, retrieved_at_utc="2026-10-11T23:00:00Z", price_american=None) for r in _arch_rows()]
    arch.write_text("\n".join(json.dumps(r) for r in _arch_rows() + newer), encoding="utf-8")
    got = log.line_near_kickoff(LEG, ROSTER, lines_root=tmp_path / "none", archive_root=tmp_path / "arch")
    assert got["line"] == 65.5 and "skipped 1 unreadable archive" in got["note"]


def test_only_one_sided_archive_quotes_are_reported_not_hidden(tmp_path):
    arch = tmp_path / "arch" / "2026" / "line_archive_2026.jsonl"
    arch.parent.mkdir(parents=True)
    arch.write_text(json.dumps(_arch_rows()[0]), encoding="utf-8")
    with pytest.raises(Exception, match="one-sided or split"):
        log.line_near_kickoff(LEG, ROSTER, lines_root=tmp_path / "none", archive_root=tmp_path / "arch")


def test_settle_uses_the_games_kickoff_now(tmp_path):
    path = tmp_path / "legs.jsonl"
    log.log_leg({**LEG, "kickoff_utc": "2026-10-11T17:00:00+00:00"}, path=path)     # logged before a flex
    arch = tmp_path / "arch" / "2026" / "line_archive_2026.jsonl"
    arch.parent.mkdir(parents=True)
    arch.write_text("\n".join(json.dumps(r) for r in _arch_rows()), encoding="utf-8")   # kickoff 00:20Z
    pg = pd.DataFrame([{"game_id": "2026_06_LA_SF", "season": 2026, "week": 6, "team": "SF", "gsis_id": "00-2",
                        "carries": 21, "rush_yds": 88.0, "targets": 0, "receptions": 0, "rec_yds": 0.0,
                        "completions": 0, "pass_yds": 0.0}])
    log.settle(2026, pg, ROSTER, ready=set(pg["game_id"]), path=path, lines_root=tmp_path / "none", archive_root=tmp_path / "arch",
               kickoffs={"2026_06_LA_SF": "2026-10-12T00:20:00+00:00"})
    assert log.read(path)[0]["kickoff_line"]["line"] == 65.5


def test_a_full_name_never_falls_back_to_a_teammates_initial():
    cands = [{"gsis_id": "chris", "name": "Chris Smith", "team": "SF"}]
    assert names.match("Carl Smith", "SF", cands)[0] is None                    # a full name: exact or nothing
    assert names.match("C. Smith", "SF", cands) == ("chris", "initial")          # abbreviated: the fallback
    assert names.abbreviated("C.McCaffrey") and not names.abbreviated("Christian McCaffrey")


def test_capture_misses_a_set_aside_player_instead_of_guessing():
    at = dt.datetime(2026, 10, 9, 12, tzinfo=dt.timezone.utc)
    players = {"7": {"full_name": "Carl Smith", "position": "WR", "team": "SF"}}
    rows, misses = capture.parse([_market("7", "receptions", 4.5, 1.8, 1.8)], players, {}, CANDS, GAMES, at,
                                 aside=pd.DataFrame([{"full_name": "Carl Smith", "team": "SF",
                                                     "gsis_id": "carl", "position": "WR"}]))
    assert rows[0]["gsis_id"] is None and "two teams" in misses[0]["reason"]


def test_settle_skips_the_lookup_for_void_legs_and_fills_merge(tmp_path):
    path = tmp_path / "legs.jsonl"
    log.log_leg({**LEG, "gsis_id": "00-9", "player": "Sat Out"}, path=path)          # did not play: void
    log.log_leg(LEG, path=path)
    pg = pd.DataFrame([{"game_id": "2026_06_LA_SF", "season": 2026, "week": 6, "team": "SF", "gsis_id": "00-2",
                        "carries": 21, "rush_yds": 88.0, "targets": 0, "receptions": 0, "rec_yds": 0.0,
                        "completions": 0, "pass_yds": 0.0}])
    caps = tmp_path / "lines"
    r = log.settle(2026, pg, ROSTER, ready=set(pg["game_id"]), path=path, lines_root=caps, archive_root=tmp_path / "none",
                   kickoffs={"2026_06_LA_SF": None})                 # a blank schedule kickoff is ignored
    assert r["settled"] == 2 and [u.split(" ")[1] for u in r["unmatched"]] == ["(Christian"]   # void leg not listed
    first = {x["gsis_id"]: x for x in log.read(path)}["00-2"]["settled_at_utc"]
    capture.append_jsonl(caps / "2026" / "lines_2026.jsonl", [dict(
        captured_at_utc="2026-10-11T20:00:00+00:00", gsis_id="00-2", team="SF", market="rush_yds",
        game_id="2026_06_LA_SF", sleeper_game_id="202610601", line=64.5, mult_over=1.8, mult_under=1.8)])
    log.settle(2026, pg, ROSTER, ready=set(pg["game_id"]), path=path, lines_root=caps, archive_root=tmp_path / "none")
    leg = {x["gsis_id"]: x for x in log.read(path)}["00-2"]
    assert leg["settled_at_utc"] == first and leg["kickoff_line"]["line"] == 64.5 and "filled_at_utc" in leg


def test_an_unreadable_file_is_read_once_per_run(tmp_path, monkeypatch):
    caps = tmp_path / "lines" / "2026" / "lines_2026.jsonl"
    caps.parent.mkdir(parents=True)
    caps.write_text("{not json", encoding="utf-8")
    calls = []
    real = log._rows
    monkeypatch.setattr(log, "_rows", lambda p: calls.append(p) or real(p))
    lookup = log.LineLookup(ROSTER, lines_root=tmp_path / "lines", archive_root=tmp_path / "none")
    for _ in range(3):
        with pytest.raises(Exception, match="not valid JSON"):
            lookup.find(LEG)
    assert calls.count(caps) == 1


def test_did_not_play_is_rechecked_when_his_snaps_arrive(tmp_path):
    path = tmp_path / "legs.jsonl"
    log.log_leg({**LEG, "market": "receptions", "side": "under", "line": 2.5}, path=path)
    thu = pd.DataFrame([{"game_id": "2026_06_LA_SF", "season": 2026, "week": 6, "team": "LA", "gsis_id": "00-4",
                         "carries": 0, "rush_yds": 0.0, "targets": 9, "receptions": 7, "rec_yds": 80.0,
                         "completions": 0, "pass_yds": 0.0}])
    none = dict(lines_root=tmp_path / "none", archive_root=tmp_path / "none")
    log.settle(2026, thu, ROSTER, ready=set(thu["game_id"]), path=path, **none)                       # his snaps not loaded yet
    assert log.read(path)[0]["result"] == "did not play"
    snaps = pd.DataFrame([{"game_id": "2026_06_LA_SF", "season": 2026, "week": 6, "team": "SF", "gsis_id": "00-2"}])
    later = data.games_played(thu, snaps)                                  # now: he played, no targets
    r = log.settle(2026, later, ROSTER, ready=set(later["game_id"]), path=path, **none)
    leg = log.read(path)[0]
    assert r["settled"] == 1 and leg["result"] == "won" and leg["actual_workload"] == 0


def test_capture_checks_an_abbreviated_name_against_set_aside_players():
    at = dt.datetime(2026, 10, 9, 12, tzinfo=dt.timezone.utc)
    players = {"7": {"full_name": "C. Smith", "position": "WR", "team": "DAL"}}
    rows, misses = capture.parse([_market("7", "receptions", 4.5, 1.8, 1.8, team="DAL")], players, {}, CANDS,
                                 pd.concat([GAMES, pd.DataFrame([{"game_id": "2026_06_KC_DAL", "season": 2026,
                                                                  "week": 6, "home_team": "DAL", "away_team": "KC",
                                                                  "kickoff_utc": "2026-10-11T17:00:00+00:00"}])]),
                                 at, aside=pd.DataFrame([{"full_name": "Chris Smith", "team": "DAL",
                                                         "gsis_id": "chris", "position": "WR"}]))
    assert rows[0]["gsis_id"] is None and "two teams" in misses[0]["reason"]


def test_an_unknown_team_name_in_the_archive_fails_loudly(tmp_path):
    arch = tmp_path / "arch" / "2026" / "line_archive_2026.jsonl"
    arch.parent.mkdir(parents=True)
    # his own team misspelled: it could be his game, so it fails loudly
    arch.write_text("\n".join(json.dumps(dict(r, home_team="SF 49ers")) for r in _arch_rows()), encoding="utf-8")
    with pytest.raises(Exception, match="does not know"):
        log.line_near_kickoff(LEG, ROSTER, lines_root=tmp_path / "none", archive_root=tmp_path / "arch")
    # his team spelled right and only the opponent odd: still his game
    arch.write_text("\n".join(json.dumps(dict(r, away_team="LA Rams")) for r in _arch_rows()), encoding="utf-8")
    got = log.line_near_kickoff(LEG, ROSTER, lines_root=tmp_path / "none", archive_root=tmp_path / "arch")
    assert got["line"] == 65.5


def test_settle_waits_for_the_plays_and_a_final_score(tmp_path):
    path = tmp_path / "legs.jsonl"
    log.log_leg(LEG, path=path)
    snaps_only = data.games_played(pd.DataFrame(columns=["game_id", "season", "week", "team", "gsis_id", "carries",
                                                         "rush_yds", "targets", "receptions", "rec_yds",
                                                         "completions", "pass_yds"]),
                                   pd.DataFrame([{"game_id": "2026_06_LA_SF", "season": 2026, "week": 6,
                                                  "team": "SF", "gsis_id": "00-2"}]))
    r = log.settle(2026, snaps_only, ROSTER, ready=set(), path=path, lines_root=tmp_path, archive_root=tmp_path)
    assert r["settled"] == 0 and "result" not in log.read(path)[0]          # no play-by-play yet: not settled


def test_numbers_in_saved_rows_must_be_numbers():
    from props.calc import checks
    for bad in (True, "65.5", None):
        with pytest.raises(checks.DataError):
            checks.number(bad, "x")
    assert checks.number(65.5, "x") == 65.5 and checks.number(3, "x") == 3.0


def test_an_empty_comment_is_not_a_comment():
    text = settings.SETTINGS_PATH.read_text(encoding="utf-8")
    bare = "\n".join("  bisect_steps: 40   #" if l.strip().startswith("bisect_steps:") else l
                      for l in text.splitlines())
    assert any("bisect_steps has no plain-English comment" in p for p in settings.problems(bare))


def test_no_zero_rows_for_a_game_whose_plays_are_not_loaded():
    pg = pd.DataFrame([{"game_id": "g1", "season": 2026, "week": 5, "team": "SF", "gsis_id": "a", "carries": 3,
                        "rush_yds": 9.0, "targets": 0, "receptions": 0, "rec_yds": 0.0, "completions": 0,
                        "pass_yds": 0.0}])
    snaps = pd.DataFrame([{"game_id": g, "season": 2026, "week": 5, "team": "SF", "gsis_id": "b"} for g in ("g1", "g2")])
    out = data.games_played(pg, snaps)
    assert set(zip(out["game_id"], out["gsis_id"])) == {("g1", "a"), ("g1", "b")}     # g2: no plays loaded, no row


def test_a_sleeper_id_given_to_two_players_is_not_used():
    roster = pd.DataFrame([{"sleeper_id": "9", "gsis_id": g} for g in ("x", "y")] + [{"sleeper_id": "1", "gsis_id": "z"}])
    assert data.sleeper_to_gsis(roster) == {"1": "z"}


def test_a_typed_name_with_its_team_may_use_the_initial():
    cands = [{"gsis_id": "s", "name": "Scott Miller", "team": "CHI"}]
    assert names.match("Scotty Miller", "CHI", cands)[0] is None                       # automatic: strict
    assert names.match("Scotty Miller", "CHI", cands, allow_initial=True)[0] == "s"     # typed with its team


def test_capture_parses_the_real_sleeper_payload_shape():
    """Sleeper sends multipliers as text ("1.77"); a slice of the live board
    (fixtures/sleeper_lines_sample.json) must parse into priced rows."""
    fx = json.loads((Path(__file__).parent / "fixtures" / "sleeper_lines_sample.json").read_text(encoding="utf-8"))
    assert all(isinstance(o["payout_multiplier"], str) for m in fx["lines"] for o in m["options"])
    games = pd.DataFrame([{"game_id": "2026_05_DET_ARI", "season": 2026, "week": 5, "home_team": "ARI",
                           "away_team": "DET", "kickoff_utc": "2026-10-11T20:05:00+00:00"}])
    cands = [{"gsis_id": "w", "name": "Michael Wilson", "team": "ARI"},
             {"gsis_id": "v", "name": "Sione Vaki", "team": "DET"}]
    rows, misses = capture.parse(fx["lines"], fx["players"], {"10232": "w", "11729": "v"}, cands, games,
                                 dt.datetime(2026, 10, 10, 12, tzinfo=dt.timezone.utc))
    assert len(rows) == 3 and misses == []
    assert all(isinstance(r["mult_over"], float) and r["mult_over"] > 1 and r["gsis_id"] for r in rows)


def test_dotted_first_names_match_their_plain_spelling():
    cands = [{"gsis_id": "aj", "name": "A.J. Brown", "team": "PHI"}, {"gsis_id": "cj", "name": "C.J. Stroud", "team": "HOU"}]
    assert names.norm("A.J. Brown") == names.norm("AJ Brown") == "aj brown"
    assert names.match("AJ Brown", "PHI", cands) == ("aj", "name")
    assert names.match("CJ Stroud", "HOU", cands) == ("cj", "name")
    assert not names.abbreviated("A.J. Brown") and names.abbreviated("C. McCaffrey")


def test_a_game_counts_as_complete_only_when_its_plays_reach_the_final_score():
    plays = pd.DataFrame([{"game_id": g, "total_home_score": h, "total_away_score": a}
                          for g, h, a in (("g1", 7, 3), ("g1", 24, 17), ("g2", 10, 0))])
    sched = pd.DataFrame([{"game_id": "g1", "home_score": 24, "away_score": 17},
                          {"game_id": "g2", "home_score": 31, "away_score": 20},     # plays stop at 10-0: partial
                          {"game_id": "g3", "home_score": None, "away_score": None}])
    assert data.complete_games(plays, sched) == {"g1"}


def test_unmapped_snap_rows_are_counted_not_dropped_silently():
    snap = pd.DataFrame([{"game_id": "g1", "season": 2026, "week": 4, "team": "LV", "player": n,
                          "pfr_player_id": i, "position": p, "offense_snaps": 52}
                         for n, i, p in (("Cody White", "WhitCo05", "WR"), ("Big Guard", "GuarBi00", "G"))])
    out = data.played(snap, pd.DataFrame(columns=["pfr_id", "gsis_id"]))
    assert out.empty and out.attrs["unmapped"] == [("Cody White", "LV")]
