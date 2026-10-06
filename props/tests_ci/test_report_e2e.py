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
    assert "**Backfield jobs.** Week 3: early-down carries" in report
    assert "Snap-change rule (round 23)" in report


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
    for w in FORBIDDEN:
        assert w not in sec
    # the board itself is the plain run's, line for line
    plain = pd.read_csv(PLAIN_OUT["dir"] / "shadow_log_2026_wk04_DAL_HOU.csv")
    mine = pd.read_csv(run_assume / "shadow_log_2026_wk04_DAL_HOU.csv")
    cols = [c for c in plain.columns if c in mine.columns and not c.endswith("_utc")]
    assert plain[cols].equals(mine[cols])
    assert (run_assume / "scenarios" / "scenario_2026_wk04_DAL_HOU.json").exists()
