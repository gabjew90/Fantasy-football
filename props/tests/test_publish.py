"""publish.py: the check that stands between a written read and any version of it (DECISIONS #217).
Known answers on a small hand-built run, so each check is pinned by the case it exists for."""
from __future__ import annotations

import copy
import json
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "engine" / "scripts"))
import publish as P  # noqa: E402

RUN = {
    "export_version": 1, "slug": "2026_wk05_TB_DAL", "season": 2026, "week": 5, "away": "TB", "home": "DAL",
    "kickoff_utc": "2026-10-09T00:15:00+00:00", "hours_to_kickoff": 3.5, "data_cutoff": "- **Data cutoff:** x",
    "model_states": "Model states (none tested against posted lines): ...",
    "market_env": {"home_spread": -9.5, "total_line": 48.5, "book": "DK", "as_of": "2026-10-08T20:42:14Z"},
    "teams": {"TB": {"implied_points": 19.5, "targets": 31.9, "carries": 24.7, "pass_td": 1.2, "rush_td": 0.8,
                     "td_anchor": "market"},
              "DAL": {"implied_points": 29.0, "targets": 35.4, "carries": 26.2, "pass_td": 1.9, "rush_td": 1.2,
                      "td_anchor": "market"}},
    "sources": [{"name": "Play-by-play 2026", "purpose": "usage", "status": "ok", "detail": "weeks 1-4"}],
    "who_plays": {"DAL": {"Receivers, tight ends and backs": "Jonathan Mingo (WR, Questionable)"}},
    "who_note": "Official report: week 5 game statuses published for DAL and TB.",
    "gaps": [["DAL expected lead (9.5 points)", "the carry forecast does not follow the score", "DAL higher runs"]],
    "injuries": [{"team": "DAL", "name": "Jonathan Mingo", "pos": "WR", "gsis_id": "w5", "status": "Questionable",
                  "source": None, "practice": "Did Not Participate In Practice"},
                 {"team": "TB", "name": "Anthony Nelson", "pos": "LB", "gsis_id": "l1", "status": None,
                  "source": None, "practice": "Limited Participation in Practice"}],
    "cards": [{
        "name": "CeeDee Lamb", "team": "DAL", "slot": "WR1", "pos": "WR", "book": "sleeper", "quoted": "2026-10-08 20:37 UTC",
        "rows": [{"market": "player_receptions", "line": 6.5, "book": "sleeper", "price_over": -127, "price_under": -130,
                  "p_over_book": 0.4974, "p_over_model": 0.627, "p_push": 0.0, "median": 8.0, "p10": 4.0, "p90": 13.0,
                  "market_volume": 9.2014, "unit": "targets", "implied": 9.305, "flags": None, "market_edge": None}],
        "volume": [{"market": "player_receptions", "line": 6.5, "volume_text": "10.7 targets",
                    "cells": {"unit": "targets", "need_out": 7, "proj": 10.737,
                              "rows": {"season": {"label": "2026 so far", "rate": 0.787, "rate_txt": "79%", "vol": 9,
                                                  "vol_txt": "9 targets", "pct": 0.6703},
                                       "engine": {"label": None, "rate": 0.742, "rate_txt": "74%", "vol": 10,
                                                  "vol_txt": "10 targets", "pct": 0.57335}},
                              "market_row": None, "need_txt": "65%", "need_rate": 0.652, "beat": [3, 4], "note": ""}}],
        "usage": {"week": 4, "n_base": 3, "snap": 0.86, "snap_base": 0.793, "ts": 0.488, "ts_base": 0.259,
                  "tn": 21.0, "tn_base": 8.667},
        "watch": [], "matchup": "TB allows 24.1 PPR points a game to wide receivers."}],
}

GOOD = {
    "reads_version": 1, "game": "TB@DAL",
    "thesis": "Dallas is favoured by 9.5 with a total of 48.5, implied 29.0 points against 19.5.",
    "legs": [{
        "player": "CeeDee Lamb", "market": "receptions", "side": "over", "line": 6.5,
        "condition": "his target share stays near the 49% of last game.",
        "case": "At 79%, 9 targets give 7.1 catches, which reaches the 7 the Over needs. The market has the Over "
                "at 50% in weeks 2-4 terms. Jonathan Mingo is Questionable.",
        "fails": "His share falls back toward 26%, under the market-implied 9.2 targets.",
        "needs": [{"volume": 9, "rate": 0.787, "reaches": True}],
        "cite": [{"field": "card.usage.ts", "value": "49%"}, {"field": "card.usage.ts_base", "value": "26%"},
                 {"field": "row.season.rate", "value": "79%"}, {"field": "market_p", "value": "50%"},
                 {"field": "market_volume", "value": 9.2}],
        "injuries": [{"player": "Jonathan Mingo", "status": "Questionable"}]}],
}


def fails(reads, run=RUN):
    return [c for c in P.check(run, reads) if not c["ok"]]


def edit(fn):
    r = copy.deepcopy(GOOD)
    fn(r)
    return r


def test_a_read_that_says_only_what_the_run_says_passes_every_check():
    checks = P.check(RUN, GOOD)
    assert checks and not [c for c in checks if not c["ok"]], [c for c in checks if not c["ok"]]


def test_arithmetic_that_contradicts_the_read_fails():
    # 9 x 0.742 = 6.68 is short of 7, but the read says it reaches
    f = fails(edit(lambda r: r["legs"][0].update(needs=[{"volume": 9, "rate": 0.742, "reaches": True}])))
    assert any(c["check"] == "volume x efficiency" and "short of 7" in c["run"] for c in f)


def test_the_whole_number_is_the_bar_not_the_half_line():
    # 9 x 0.73 = 6.57 clears 6.5 but not the 7 the Over needs (the TNF read's old mistake, #215)
    r = edit(lambda r: r["legs"][0].update(needs=[{"volume": 9, "rate": 0.73, "reaches": True, "hypothetical": True}]))
    assert any(c["check"] == "volume x efficiency" for c in fails(r))


def test_a_rate_not_on_the_card_fails_unless_labelled_hypothetical():
    bad = edit(lambda r: r["legs"][0].update(needs=[{"volume": 8, "rate": 0.9, "reaches": True}]))
    assert any(c["check"] == "rate source" for c in fails(bad))
    ok = edit(lambda r: r["legs"][0].update(needs=[{"volume": 8, "rate": 0.9, "reaches": True, "hypothetical": True}]))
    assert not any(c["check"] == "rate source" for c in fails(ok))


@pytest.mark.parametrize("value, ok", [("50%", True), ("51%", False), ("49.7%", True), ("49.8%", False), (0.5, True)])
def test_a_cite_matches_at_the_precision_it_is_written(value, ok):
    r = edit(lambda r: r["legs"][0]["cite"].__setitem__(3, {"field": "market_p", "value": value}))
    bad = [c for c in fails(r) if c["check"] == "cite"]
    assert (not bad) is ok


@pytest.mark.parametrize("phrase", ["This is the best play.", "I lean Over.", "There is an edge here.",
                                    "Good value.", "A lock.", "+EV", "Quarter Kelly.", "The probability is 50%."])
def test_pick_language_and_the_probability_are_refused(phrase):
    r = edit(lambda r: r["legs"][0].update(case=r["legs"][0]["case"] + " " + phrase))
    assert any(c["check"] == "language" for c in fails(r))


def test_a_number_no_cite_accounts_for_fails_and_labels_do_not():
    r = edit(lambda r: r["legs"][0].update(fails="He saw 12 targets."))
    assert any(c["check"] == "number traced" and "12" in c["stated"] for c in fails(r))
    labels = edit(lambda r: r["legs"][0].update(fails="Since weeks 2-4 of 2026, the 4th WR1 game, inside the 80% range."))
    assert not any(c["check"] == "number traced" for c in fails(labels))


def test_injuries_must_match_section_4_and_a_named_injured_player_must_be_cited():
    wrong = edit(lambda r: r["legs"][0].update(injuries=[{"player": "Jonathan Mingo", "status": "Out"}]))
    assert any(c["check"] == "injury" for c in fails(wrong))
    uncited = edit(lambda r: r["legs"][0].update(injuries=[]))
    assert any(c["check"] == "injury named" for c in fails(uncited))
    # a practice-only player is "practice only", not a game status
    r = edit(lambda r: r["legs"][0]["injuries"].append({"player": "Anthony Nelson", "status": "practice only"}))
    assert not any(c["check"] == "injury" for c in fails(r))


def test_a_leg_not_on_the_board_fails_and_names_what_is():
    f = fails(edit(lambda r: r["legs"][0].update(line=7.5)))
    assert any(c["check"] == "on the board" and "receptions 6.5" in c["run"] for c in f)
    f = fails(edit(lambda r: r["legs"][0].update(player="Ceedee Lam")))
    assert any(c["check"] == "on the board" for c in f)


def test_the_reads_file_is_validated_before_any_check():
    for bad in ({"reads_version": 2, "legs": [{}]}, {"reads_version": 1, "legs": []},
                {"reads_version": 1, "legs": [{**GOOD["legs"][0], "market": "longest catch"}]},
                {"reads_version": 1, "legs": [{**GOOD["legs"][0], "side": "both"}]}):
        p = Path(__file__).with_name("_reads_tmp.json")
        try:
            p.write_text(json.dumps(bad), encoding="utf-8")
            with pytest.raises(P.ReadsError):
                P.load_reads(p)
        finally:
            p.unlink(missing_ok=True)


def test_qa_version_shows_the_read_its_numbers_and_every_check():
    checks = P.check(RUN, GOOD)
    qa = P.render_qa(RUN, GOOD, checks, {"tag": "nfl-v9.9", "hash": "ab" * 32, "source": "fetched"})
    assert "Checks: " in qa and f"{len(checks)} of {len(checks)} pass" in qa
    assert "**If** his target share" in qa and "Market's chance of the Over (the best available estimate) | **50%**" in qa
    assert "| volume x efficiency | 9 x 0.787 = 7.08: reaches 7 | reaches 7 | pass |" in qa
    assert "For the reviewer (not machine-checked)" in qa
    assert "nfl-v9.9" in qa


def test_agent_version_embeds_the_release_documents_and_says_data_missing_without_ci():
    checks = P.check(RUN, GOOD)
    ag = P.render_agent(RUN, GOOD, checks, {"tag": "nfl-v9.9", "hash": "cd" * 32, "source": "fetched"}, None)
    assert "https://github.com/gabjew90/Fantasy-football/tree/nfl-v9.9" in ag
    assert "## 1. The system" in ag and "Data Source Matrix" in ag and "How the props engine works" in ag
    assert "DATA MISSING" in ag and "The reads and their checks" in ag
    assert "{REF}" not in ag and "{REPO}" not in ag


def test_agent_version_carries_nothing_shaped_like_a_credential():
    ag = P.render_agent(RUN, GOOD, P.check(RUN, GOOD), {"tag": "t", "hash": "0" * 64, "source": "s"}, None)
    ag = ag.replace("0" * 64, "")
    # an Odds API key is 32 hex characters; a FantasyPros or GitHub token is a long opaque run
    assert not re.search(r"\b[0-9a-f]{32}\b", ag)
    assert not re.search(r"(api[_-]?key|apikey|token|secret)\s*[=:]\s*\S{12,}", ag, re.I)
    assert "credential.env" not in ag or "never" in ag


def test_ci_results_report_the_pull_requests_suites_and_the_tags_own_runs():
    calls = []

    def get(u):
        calls.append(u)
        if u.endswith("/commits/nfl-v9.9"):
            return {"sha": "m" * 40}
        if u.endswith("/pulls"):
            return [{"number": 143, "merged_at": "2026-10-08", "head": {"sha": "h" * 40}}]
        if "/commits/" + "h" * 40 in u:
            return {"check_runs": [{"name": "tests", "status": "completed", "conclusion": "success", "html_url": "u1"}]}
        return {"check_runs": [{"name": "tick", "status": "completed", "conclusion": "success", "html_url": "u2"}]}
    ci = P.ci_results(P.REPO_URL, "nfl-v9.9", get=get)
    assert ci["pr"] == 143 and [(c["name"], c["where"]) for c in ci["checks"]] == [
        ("tests", "pull request #143 head"), ("tick", "the tag's commit")]
    assert P.ci_results(P.REPO_URL, "x", get=lambda u: (_ for _ in ()).throw(OSError("offline"))) is None


def test_main_renders_nothing_when_a_check_fails(tmp_path):
    run_p, reads_p, out = tmp_path / "run.json", tmp_path / "reads.json", tmp_path / "out"
    run_p.write_text(json.dumps(RUN), encoding="utf-8")
    reads_p.write_text(json.dumps(edit(lambda r: r["legs"][0].update(fails="He saw 12 targets."))), encoding="utf-8")
    assert P.main(["--run", str(run_p), "--reads", str(reads_p), "--out", str(out), "--no-ci"]) == 3
    assert not out.exists() or not list(out.iterdir())
    reads_p.write_text(json.dumps(GOOD), encoding="utf-8")
    assert P.main(["--run", str(run_p), "--reads", str(reads_p), "--out", str(out), "--no-ci"]) == 0
    assert sorted(p.name for p in out.iterdir()) == ["2026_wk05_TB_DAL_agent.md", "2026_wk05_TB_DAL_qa.md"]
