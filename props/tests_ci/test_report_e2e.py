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
                      "Last game | Flags |")
    j = lines.index(header)
    rows = [ln for ln in lines[j + 2:] if ln.startswith("|")]
    rows = rows[:next((k for k, ln in enumerate(rows) if not ln.startswith("| ") or "(DAL)" not in ln
                       and "(HOU)" not in ln), len(rows))]
    assert len(rows) == research.drop_duplicates(["player", "market", "line", "book"]).shape[0] > 10
    for ln in rows:
        assert ln.count("|") == 10, ln
        assert re.search(r"O [+-]\d+ / U [+-]\d+", ln), "both prices on every row"


def test_line_implies_and_flags_are_filled(run):
    _rep, research, _e = run
    rec = research[research.market == "player_receptions"]
    assert rec.implied.notna().mean() > 0.8, "the implied workload resolves for most catches lines"
    assert research["flags"].fillna("").str.contains("Nico Collins active").any(), "the teammate-back flag"


def test_a_backs_three_jobs_and_the_snap_rule_are_shown(run):
    report, _r, _e = run
    assert "**Backfield jobs.** Week 3: early-down carries" in report
    assert "Snap-change rule (round 23)" in report
