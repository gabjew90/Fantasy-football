"""End to end: render one real report offline and check what the user reads.

The engine runs on a trimmed copy of one game's inputs (DAL at HOU, 2026 week
4: Dallas/Houston rows of play-by-play, rosters, snaps, injuries, depth charts,
plus the saved odds snapshot), with fetching disabled by an infinite cache
age. It lives in props/tests_ci, which props-ci runs on pull requests and
props.yml never runs before a capture: a rendering check must not be able to
cost a slate (props/README.md, "the capture path must stay unskippable").
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "props" / "engine" / "scripts"
FIXTURE = ROOT / "props" / "tests" / "fixtures" / "report_dal_hou"

# words that would mean bet labels came back (DECISIONS #142)
FORBIDDEN = ["STRONG", "MODERATE", "Kelly", "EV/$100", "EV per $100", "eligible to bet", "Take UNDER",
             "Take OVER", "Bottom line", "Size them as one bet", "must-win", "Bet card", "bettable"]


PLAIN_OUT = {}      # the plain run's output folder, for the scenario comparison


@pytest.fixture(scope="module")
def run(tmp_path_factory):
    wd = tmp_path_factory.mktemp("wd")
    out = tmp_path_factory.mktemp("out")
    for f in FIXTURE.iterdir():
        shutil.copy(f, wd / f.name)
    env = dict(os.environ, NFL_FETCH_MAX_AGE_S="1000000000", NFL_OUT=str(out))
    r = subprocess.run([sys.executable, str(SCRIPTS / "score_game.py"), "--away", "DAL", "--home", "HOU",
                        "--season", "2026", "--week", "4", "--workdir", str(wd),
                        "--odds-snapshot", str(wd / "odds_snapshot_2026_wk04_DAL_HOU.json"), "--no-scenarios"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=600)
    assert r.returncode == 0, r.stderr[-2000:]
    report = (out / "report_2026_wk04_DAL_HOU.md").read_text(encoding="utf-8")
    research = pd.read_csv(out / "research_2026_wk04_DAL_HOU.csv")
    PLAIN_OUT["dir"] = out
    return report, research, r.stderr


def test_the_report_opens_as_a_research_sheet(run):
    report, _r, _e = run
    first = next(ln for ln in report.splitlines() if ln.startswith("**"))
    assert "A research sheet, not a bet list." in first


def test_cards_are_one_table_with_the_volume_chance_for_every_market_kind(run):
    # the user's framework and layout (2026-10-07): one table per player, a column per prop; the engine's
    # volume against the efficiency each line needs
    report, _r, _e = run
    for head in ("| | Receptions ", " Receiving yards ", " Rushing yards ", "| | Passing yards "):
        assert head in report, head
    assert "| **Market's chance of the Over** |" in report and "| At his luck-capped rate |" in report
    assert "| Market-implied volume (at the engine's efficiency) |" in report
    assert " completions at " in report and " catches at " in report and " carries at " in report
    assert " targets at " in report
    assert "luck-capped rate = last 10 games, long catches capped (" in report and "so far, uncapped (" in report
    assert "| His games this season that beat that |" in report
    for gone in ("| Workload check |", "**Capped-play check:**", "**How his lines fit together:**", "**Volume chance"):
        assert gone not in report, gone
    # the price-based margin flags belong to the research table, never to a card's Watch line
    watch = [ln for ln in report.splitlines() if ln.startswith("**Watch:**")]
    assert watch and not any("thin" in ln.lower() for ln in watch)


def test_no_bet_language_anywhere_the_user_reads(run):
    report, _r, log = run
    for w in FORBIDDEN:
        assert w not in report, f"'{w}' is back in the report"
    assert "Confidence tiers" not in log and "BET CARD" not in log


def test_the_research_table_has_its_columns_on_every_row(run):
    report, research, _e = run
    lines = report.splitlines()
    i = lines.index("## Research table")
    header = next(ln for ln in lines[i:] if ln.startswith("| Player |"))
    assert header == ("| Player | Prop | Line | Price | Our projection | Over: model / book | Line implies | "
                      "Pays at this price if you expect | Last game | Flags |")
    j = lines.index(header)
    rows = [ln for ln in lines[j + 2:] if ln.startswith("|")]
    rows = rows[:next((k for k, ln in enumerate(rows) if not ln.startswith("| ") or "(DAL)" not in ln
                       and "(HOU)" not in ln), len(rows))]
    assert len(rows) == research.drop_duplicates(["player", "market", "line", "book"]).shape[0] > 10
    for ln in rows:
        assert ln.count("|") == 11, ln
        assert re.search(r"O [+-]\d+ / U [+-]\d+", ln), "both prices on every row"


def test_line_implies_and_flags_are_filled(run):
    _rep, research, _e = run
    rec = research[research.market == "player_receptions"]
    assert rec.implied.notna().mean() > 0.8, "the implied workload resolves for most catches lines"
    assert research["flags"].fillna("").str.contains("Nico Collins back \\(missed last week\\)").any(), \
        "the teammate-back flag: he missed week 3 and plays week 4"
    assert research["preview"].dropna().str.contains("Nico Collins back").any(), "Houston's week 3 is not a preview"


def test_the_break_even_workload_straddles_the_coin_flip(run):
    _rep, research, _e = run
    d = research[research.market.isin(["player_receptions", "player_reception_yds", "player_rush_yds"])]
    both = d.dropna(subset=["over_needs", "under_needs", "implied"])
    assert len(both) >= 0.7 * len(d), "the break-even search resolves for most lines"
    half = both[((both.line % 1) == 0.5) & (both.be_over > 0.5) & (both.be_under > 0.5)]
    assert len(half) > 10
    # both sides at minus money: the Over needs more than a coin flip and the Under less. A
    # plus-money side (Boutte's Under at +122 needs 45%) can pay past the coin flip.
    assert (half.over_needs >= half.implied - 0.05).all() and (half.under_needs <= half.implied + 0.05).all()
    assert (both.over_needs > both.under_needs).all(), "the gap between them is the cut"
    assert both.be_over.between(0.3, 0.8).all() and both.be_under.between(0.3, 0.8).all()


def test_a_backs_three_jobs_and_the_snap_rule_are_shown(run):
    report, _r, _e = run
    # the player cards (user's draft, 2026-10-06): a back's three jobs are a role-evidence row
    assert "| Backfield jobs: early-down carries / passing-down targets / inside-5 carries |" in report
    assert "Snap-change rule (round 23)" in report


def test_the_team_matchup_section_and_the_cards_follow_the_users_guides(run):
    report, _r, _e = run
    for h in ("## Team matchup", "### 1. The market's view of the game",
              "### 2. Expected volume and how the teams have been playing",
              "### 3. Unit performance and matchup: scores and tiers", "### 4. Who plays: injuries and replacements",
              "### 7. Where the baseline could miss this game"):
        assert h in report, h
    # the fixture holds two teams' plays only: no league to score units against, said in words
    assert ("50 = league average; higher is better for both offense and defense." in report
            or "Unit scores: not included in this run" in report), "the user's caption, or the gap stated"
    assert "| Tier | Passing offence |" not in report, "no tier ladder"
    assert "| **Market's chance of the Over** |" in report
    assert report.count("**Live record at Sleeper's lines**") == 1, "the real-line record, once for the report"


@pytest.fixture(scope="module")
def run_assume(tmp_path_factory):
    wd = tmp_path_factory.mktemp("wd_assume")
    out = tmp_path_factory.mktemp("out_assume")
    for f in FIXTURE.iterdir():
        shutil.copy(f, wd / f.name)
    env = dict(os.environ, NFL_FETCH_MAX_AGE_S="1000000000", NFL_OUT=str(out))
    r = subprocess.run([sys.executable, str(SCRIPTS / "score_game.py"), "--away", "DAL", "--home", "HOU",
                        "--season", "2026", "--week", "4", "--workdir", str(wd),
                        "--odds-snapshot", str(wd / "odds_snapshot_2026_wk04_DAL_HOU.json"), "--no-scenarios",
                        "--assume", "Woody Marks: carries=14", "--assume", "Nico Collins: targets=10"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=900)
    assert r.returncode == 0, r.stderr[-2000:]
    return out


def test_your_scenario_prices_the_lines_again_and_leaves_the_board_alone(run, run_assume):
    report = (run_assume / "report_2026_wk04_DAL_HOU.md").read_text(encoding="utf-8")
    sec = report[report.index("## Your scenario (experimental)"):]
    assert "**Your assumptions:** Woody Marks: carries=14; Nico Collins: targets=10." in sec
    assert "not confidence intervals" in sec
    rows = [ln for ln in sec.splitlines() if ln.startswith("| ") and ("(HOU)" in ln or "(DAL)" in ln)]
    assert rows[0].startswith("| Woody Marks (HOU) | rushing yards"), "the named players lead"
    assert all(ln.count("|") == 9 for ln in rows)
    # one random stream per team (fourth expert review): what-ifs on Houston players leave every
    # Dallas draw identical, so no Dallas line may be listed as moved
    assert not any("(DAL)" in ln for ln in rows), [ln for ln in rows if "(DAL)" in ln]
    for w in FORBIDDEN:
        assert w not in sec
    # the board itself is the plain run's, line for line
    plain = pd.read_csv(PLAIN_OUT["dir"] / "shadow_log_2026_wk04_DAL_HOU.csv")
    mine = pd.read_csv(run_assume / "shadow_log_2026_wk04_DAL_HOU.csv")
    cols = [c for c in plain.columns if c in mine.columns and not c.endswith("_utc")]
    assert plain[cols].equals(mine[cols])
    assert (run_assume / "scenarios" / "scenario_2026_wk04_DAL_HOU.json").exists()


def test_an_away_team_what_if_leaves_every_home_line_alone(tmp_path):
    """Fourth expert review, reproduced: with one shared stream, a Dallas (away) what-if listed six
    Houston lines as moved although nothing about Houston changed. One stream per team: none."""
    wd, out = tmp_path / "wd", tmp_path / "out"
    wd.mkdir(); out.mkdir()
    for f in FIXTURE.iterdir():
        shutil.copy(f, wd / f.name)
    env = dict(os.environ, NFL_FETCH_MAX_AGE_S="1000000000", NFL_OUT=str(out))
    r = subprocess.run([sys.executable, str(SCRIPTS / "score_game.py"), "--away", "DAL", "--home", "HOU",
                        "--season", "2026", "--week", "4", "--workdir", str(wd),
                        "--odds-snapshot", str(wd / "odds_snapshot_2026_wk04_DAL_HOU.json"), "--no-scenarios",
                        "--assume", "CeeDee Lamb: targets=11"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=900)
    assert r.returncode == 0, r.stderr[-2000:]
    report = (out / "report_2026_wk04_DAL_HOU.md").read_text(encoding="utf-8")
    sec = report[report.index("## Your scenario (experimental)"):]
    rows = [ln for ln in sec.splitlines() if ln.startswith("| ") and "(HOU)" in ln]
    assert rows == [], rows
    assert any(ln.startswith("| CeeDee Lamb (DAL)") for ln in sec.splitlines()), "the named player is priced"


def test_a_practice_only_injury_report_is_said_and_shown(tmp_path):
    # expert review 2026-10-08 (DECISIONS #215): before game statuses post, the report must say the
    # report is practice-only and still list the defenders who missed practice -- not "no designations"
    wd, out = tmp_path / "wd", tmp_path / "out"
    wd.mkdir()
    out.mkdir()
    for f in FIXTURE.iterdir():
        shutil.copy(f, wd / f.name)
    inj = pd.read_csv(wd / "inj_2026.csv", low_memory=False)
    inj.loc[inj.week == 4, "report_status"] = None
    inj.to_csv(wd / "inj_2026.csv", index=False)
    env = dict(os.environ, NFL_FETCH_MAX_AGE_S="1000000000", NFL_OUT=str(out))
    r = subprocess.run([sys.executable, str(SCRIPTS / "score_game.py"), "--away", "DAL", "--home", "HOU",
                        "--season", "2026", "--week", "4", "--workdir", str(wd),
                        "--odds-snapshot", str(wd / "odds_snapshot_2026_wk04_DAL_HOU.json"), "--no-scenarios"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=600)
    assert r.returncode == 0, r.stderr[-2000:]
    report = (out / "report_2026_wk04_DAL_HOU.md").read_text(encoding="utf-8")
    sec = report[report.index("### 4. Who plays"):report.index("### 5.")]
    assert "PRACTICE STATUSES ONLY" in sec and "game statuses published" not in sec
    row = next(ln for ln in sec.splitlines() if ln.startswith("| Pass rush and coverage"))
    assert "did not participate" in row and "no designations |" not in row.split("|")[3]
    assert "practice statuses only" in report.split("## Team matchup")[1].split("### 1.")[0]


def test_the_run_export_matches_the_report_and_a_read_built_from_it_publishes(run, tmp_path):
    # run_<slug>.json is the report's cards as data (DECISIONS #217): one card per report card,
    # and a read that states only the run's numbers passes publish's checks and renders
    import json
    out = PLAIN_OUT["dir"]
    report, _r, _e = run
    data = json.loads((out / "run_2026_wk04_DAL_HOU.json").read_text(encoding="utf-8"))
    assert data["export_version"] == 1 and data["away"] == "DAL" and data["home"] == "HOU"
    assert len(data["cards"]) == len(re.findall(r"(?m)^#### ", report))
    assert data["sources"] and data["gaps"] and data["who_plays"]
    # the report guide's data (DECISIONS #218): the brief's tables travel as data too
    # (no unit scores: the fixture holds two teams' plays, no league to rank against)
    for k in ("header", "weather_line", "team_volume", "points_allowed", "live_record"):
        assert data.get(k), k
    assert data["live_record"]["lines"] == 1536
    card = next(c for c in data["cards"] for v in c["volume"]
                if v.get("cells") and "season" in v["cells"]["rows"] and v["market"] == "player_receptions")
    v = next(v for v in card["volume"] if v["market"] == "player_receptions")
    row = next(r for r in card["rows"] if r["market"] == "player_receptions" and r["line"] == v["line"])
    rate, need = v["cells"]["rows"]["season"]["rate"], v["cells"]["need_out"]
    vol = v["cells"]["rows"]["season"]["vol"]
    pct = f"{100 * row['p_over_book']:.0f}%"
    reads = {"reads_version": 2, "game": "DAL@HOU",
             "opening": "A read built from the run. It states only the run's numbers. It is a test.",
             "assumptions": ["The share holds.", "The volume holds."], "handoff": "The player sections follow.",
             "players": [{"player": card["name"], "basis": "His share.", "explanation": f"The market has the Over at {pct}.",
                          "role_evidence": "his share", "matchup": "supports", "matchup_reason": "the test says so",
                          "legs": [{"market": "receptions", "side": "over", "line": v["line"],
                                    "if": "his share holds", "fails": "his share falls", "else": "skip it",
                                    "needs": [{"volume": vol, "rate": rate, "reaches": vol * rate >= need - 1e-9}],
                                    "cite": [{"field": "market_p", "value": pct}]}]}]}
    rp = tmp_path / "reads.json"
    rp.write_text(json.dumps(reads), encoding="utf-8")
    r = subprocess.run([sys.executable, str(SCRIPTS / "publish.py"), "--run", str(out / "run_2026_wk04_DAL_HOU.json"),
                        "--reads", str(rp), "--out", str(tmp_path / "pub"), "--no-ci"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    assert r.returncode == 0, r.stdout + r.stderr
    assert (tmp_path / "pub" / "2026_wk04_DAL_HOU_qa.md").exists()
    assert (tmp_path / "pub" / "2026_wk04_DAL_HOU_agent.md").exists()
