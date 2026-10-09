"""publish.py / publish_render.py: the check that stands between a written read and any version of
it, and the guide's generated pieces (DECISIONS #217, #218). Known answers on a small hand-built
run, so each check is pinned by the case it exists for."""
from __future__ import annotations

import copy
import json
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "engine" / "scripts"))
import publish as P  # noqa: E402
import publish_render as PR  # noqa: E402

LAMB = {
    "name": "CeeDee Lamb", "team": "DAL", "slot": "WR1", "pos": "WR", "book": "sleeper", "quoted": "2026-10-08 20:37 UTC",
    "rows": [{"market": "player_receptions", "line": 6.5, "book": "sleeper", "price_over": -127, "price_under": -130,
              "p_over_book": 0.4974, "p_over_model": 0.627, "p_push": 0.0, "median": 8.0, "p10": 4.0, "p90": 13.0,
              "market_volume": 9.2014, "unit": "targets", "implied": 9.305, "flags": None, "market_edge": None},
             {"market": "player_reception_yds", "line": 85.5, "book": "sleeper", "price_over": -128, "price_under": -128,
              "p_over_book": 0.50, "p_over_model": 0.545, "p_push": 0.0, "median": 92.0, "p10": 34.0, "p90": 174.0,
              "market_volume": 10.0067, "unit": "targets", "market_catches": 7.4}],
    "volume": [{"market": "player_receptions", "line": 6.5, "volume_text": "10.7 targets",
                "cells": {"unit": "targets", "need_out": 7, "proj": 10.737,
                          "rows": {"season": {"label": "2026 so far", "rate": 0.787, "rate_txt": "79%", "vol": 9,
                                              "vol_txt": "9 targets", "pct": 0.6703},
                                   "engine": {"label": None, "rate": 0.742, "rate_txt": "74%", "vol": 10,
                                              "vol_txt": "10 targets", "pct": 0.57335}},
                          "market_row": None, "need_txt": "65%", "need_rate": 0.652, "beat": [3, 4], "note": ""}},
               {"market": "player_reception_yds", "line": 85.5, "volume_text": "10.7 targets -> 8.0 catches",
                "cells": {"unit": "catches", "need_out": 86, "proj": 7.95,
                          "rows": {"capped": {"label": "Last 10 games", "rate": 12.956, "rate_txt": "13.0", "vol": 7,
                                              "vol_txt": "7 catches", "pct": 0.627},
                                   "season": {"label": "2026", "rate": 13.459, "rate_txt": "13.5", "vol": 7,
                                              "vol_txt": "7 catches", "pct": 0.627},
                                   "engine": {"label": None, "rate": 12.544, "rate_txt": "12.5", "vol": 7,
                                              "vol_txt": "7 catches", "pct": 0.627}},
                          "market_row": None, "need_txt": "10.8 yards a catch", "need_rate": 10.8, "beat": None, "note": ""}}],
    "usage": {"week": 4, "n_base": 3, "snap": 0.86, "snap_base": 0.793, "ts": 0.488, "ts_base": 0.259,
              "tn": 21.0, "tn_base": 8.667, "cn": 1.0},
    "watch": [], "matchup": "TB allows 24.1 PPR points a game to wide receivers."}

RUN = {
    "export_version": 1, "slug": "2026_wk05_TB_DAL", "season": 2026, "week": 5, "away": "TB", "home": "DAL",
    "kickoff_utc": "2026-10-09T00:15:00+00:00", "hours_to_kickoff": 3.5, "data_cutoff": "- **Data cutoff:** x",
    "model_states": "Model states (none tested against posted lines): ...",
    "header": ["**TB at DAL**", "", "Thursday, Oct 8 · AT&T Stadium"],
    "weather_line": "dome conditions",
    "market_env": {"home_spread": -9.5, "total_line": 48.5, "book": "DK", "as_of": "2026-10-08T20:42:14Z",
                   "home_ml": "-500", "away_ml": "+380", "open_home_spread": -3.5, "open_total": 52.5,
                   "home_win_prob": 0.80, "home_win_prob_open": 0.645},
    "teams": {"TB": {"implied_points": 19.5, "targets": 31.9, "carries": 24.7, "pass_td": 1.2, "rush_td": 0.8,
                     "td_anchor": "market", "market_throws": 32.3, "market_runs": 23.9},
              "DAL": {"implied_points": 29.0, "targets": 35.4, "carries": 26.2, "pass_td": 1.9, "rush_td": 1.2,
                      "td_anchor": "market", "market_throws": 31.4, "market_runs": 27.5}},
    "team_volume": {"TB": {"our_att": 33.2, "our_runs": 24.7, "att_avg": 31.5, "runs_avg": 24.25, "target_rate": 0.96, "games": 4},
                    "DAL": {"our_att": 36.9, "our_runs": 26.2, "att_avg": 37.75, "runs_avg": 23.5, "target_rate": 0.96, "games": 4}},
    "units": {"DAL": {"off_pass": {"score": 59.9, "grade": "A-", "rank": 4, "of": 32}},
              "TB": {"def_run": {"score": 68.1, "grade": "A+", "rank": 3, "of": 32}}},
    "points_allowed": {"TB": {p: {"ppr": 18.0, "rank_most": 23, "catches": 6.25, "rec_yds": 40.25, "rush_yds": 62.5, "tds": 0.25}
                              for p in ("RB", "WR", "TE")},
                       "DAL": {p: {"ppr": 21.9, "rank_most": 13, "catches": 3.0, "rec_yds": 16.8, "rush_yds": 97.2, "tds": 1.2}
                               for p in ("RB", "WR", "TE")},
                       "_league": {"RB": 21.9, "WR": 32.4, "TE": 13.6}, "_n": 32, "_games": {"TB": 4, "DAL": 4}},
    "live_record": {"weeks": "2-4", "lines": 1536, "engine_log_loss": 0.717, "market_log_loss": 0.692, "coin_flip": 0.693,
                    "markets": {}},
    "qb_change": {"TB": "Jalon Daniels starts for Baker Mayfield"},
    "sources": [{"name": "Play-by-play 2026", "purpose": "usage", "status": "ok", "detail": "weeks 1-4"}],
    "who_plays": {"DAL": {"Receivers, tight ends and backs": "Jonathan Mingo (WR, Questionable)"}},
    "who_note": "Official report: week 5 game statuses published for DAL and TB.",
    "gaps": [["DAL expected lead (9.5 points)", "the carry forecast does not follow the score", "DAL higher runs"]],
    "injuries": [{"team": "DAL", "name": "Jonathan Mingo", "pos": "WR", "gsis_id": "w5", "status": "Questionable",
                  "source": None, "practice": "Did Not Participate In Practice"},
                 {"team": "TB", "name": "Anthony Nelson", "pos": "LB", "gsis_id": "l1", "status": None,
                  "source": None, "practice": "Limited Participation in Practice"},
                 {"team": "TB", "name": "Baker Mayfield", "pos": "QB", "gsis_id": "q1", "status": "Out",
                  "source": None, "practice": "Did Not Participate In Practice"}],
    "cards": [LAMB],
}

LEG = {"market": "receptions", "side": "over", "line": 6.5,
       "if": "his target share stays near the 49% of last game",
       "fails": "his share falls back toward 26%, under the market-implied 9.2 targets",
       "else": "if his share falls back, skip it: 8 targets at 79% make 6.3 catches, short of 7",
       "needs": [{"volume": 9, "rate": 0.787, "reaches": True}, {"volume": 8, "rate": 0.787, "reaches": False}],
       "cite": [{"field": "row.season.rate", "value": "79%"}, {"field": "market_p", "value": "50%"},
                {"field": "market_volume", "value": 9.2}],
       "injuries": [{"player": "Jonathan Mingo", "status": "Questionable"}]}

GOOD_RAW = {
    "reads_version": 2, "game": "TB@DAL",
    "opening": "The market expects Dallas to control this game. Its passing offense ranks 4th. Tampa's run defense ranks 3rd.",
    "market_read": "Dallas is favored by 9.5 with a total of 48.5, implied 29.0 points against 19.5, and an 80% win chance, up from 64%.",
    "workload_read": "The engine keeps 36.9 Dallas attempts against the market fit's 32.7.",
    "unit_reads": {"DAL": "Its passing offense ranks 4th by score."},
    "personnel": [{"player": "Baker Mayfield", "status": "Out", "changes": "Jalon Daniels starts.", "affects": "Tampa's passing props."}],
    "personnel_read": "The Mayfield change moved the line.",
    "allowed_read": "Tampa has allowed 62.5 rushing yards a game to backs.",
    "assumptions": ["Dallas builds a lead.", "Daniels sustains drives."],
    "handoff": "The player sections ask whether the opportunities belong to these players.",
    "players": [{"player": "CeeDee Lamb",
                 "basis": "His 49% target share last game against 26% before it.",
                 "explanation": "At 79%, 9 targets give 7.1 catches, which reaches the 7 the Over needs; the market has the "
                                "Over at 50% in weeks 2-4 terms. Jonathan Mingo is Questionable.",
                 "role_evidence": "last game's 21 targets",
                 "matchup": "supports", "matchup_reason": "Tampa is without its starting safety",
                 "cite": [{"field": "card.usage.ts", "value": "49%"}, {"field": "card.usage.ts_base", "value": "26%"},
                          {"field": "card.usage.tn", "value": 21}],
                 "legs": [LEG]}],
    "parlay": {"opening": "One leg, no ticket proposed. The read stands alone.",
               "closing": "For this game read, keep the Lamb leg on its own."},
}


def good():
    return P.validate(GOOD_RAW)


def fails(reads, run=RUN):
    return [c for c in P.check(run, reads) if not c["ok"]]


def edit(fn, raw=GOOD_RAW):
    r = copy.deepcopy(raw)
    fn(r)
    return P.validate(r)


def leg0(r):
    return r["players"][0]["legs"][0]


def test_a_read_that_says_only_what_the_run_says_passes_every_check():
    checks = P.check(RUN, good())
    assert checks and not [c for c in checks if not c["ok"]], [c for c in checks if not c["ok"]]


# ---- the leg checks (v1's known answers, carried over) ----
def test_arithmetic_that_contradicts_the_read_fails():
    f = fails(edit(lambda r: leg0(r).update(needs=[{"volume": 9, "rate": 0.742, "reaches": True}])))
    assert any(c["check"] == "volume x efficiency" and "short of 7" in c["run"] for c in f)


def test_the_whole_number_is_the_bar_not_the_half_line():
    r = edit(lambda r: leg0(r).update(needs=[{"volume": 9, "rate": 0.73, "reaches": True, "hypothetical": True}]))
    assert any(c["check"] == "volume x efficiency" for c in fails(r))


def test_a_rate_not_on_the_card_fails_unless_labelled_hypothetical():
    assert any(c["check"] == "rate source" for c in
               fails(edit(lambda r: leg0(r).update(needs=[{"volume": 8, "rate": 0.9, "reaches": True}]))))
    assert not any(c["check"] == "rate source" for c in
                   fails(edit(lambda r: leg0(r).update(needs=[{"volume": 8, "rate": 0.9, "reaches": True, "hypothetical": True}]))))


@pytest.mark.parametrize("value, ok", [("50%", True), ("51%", False), ("49.7%", True), ("49.8%", False), (0.5, False),
                                       ("0.497", True)])
def test_a_cite_matches_at_the_precision_it_is_written(value, ok):
    r = edit(lambda r: leg0(r)["cite"].__setitem__(1, {"field": "market_p", "value": value}))
    assert (not [c for c in fails(r) if c["check"] == "cite"]) is ok


@pytest.mark.parametrize("phrase", ["This is the best play.", "I lean Over.", "There is an edge here.", "Good value.",
                                    "A lock.", "+EV", "Quarter Kelly.", "The probability is 50%.", "Take the Over.",
                                    "I like the Under.", "We'd love it."])
def test_pick_language_and_the_probability_are_refused(phrase):
    r = edit(lambda r: r["players"][0].update(explanation=r["players"][0]["explanation"] + " " + phrase))
    assert any(c["check"] == "language" for c in fails(r))


def test_pick_language_is_refused_in_the_team_brief_too():
    for k in ("opening", "market_read", "handoff"):
        r = edit(lambda r: r.update({k: "Take the Over. A lock. Fine."}))
        assert any(c["check"] == "language" and c["leg"] == 0 for c in fails(r)), k


def test_a_number_no_cite_accounts_for_fails_and_labels_do_not():
    assert any(c["check"] == "number traced" and "12" in c["stated"] for c in
               fails(edit(lambda r: leg0(r).update(fails="He saw 12 targets"))))
    labels = edit(lambda r: leg0(r).update(fails="since weeks 2-4 of 2026, the 4th WR1 game, inside the 80% range"))
    assert not any(c["check"] == "number traced" for c in fails(labels))


def test_prose_is_traced_to_the_runs_number_not_the_stated_cite():
    run = copy.deepcopy(RUN)
    run["cards"][0]["rows"][0]["p_over_book"] = 0.451
    r = edit(lambda r: leg0(r)["cite"].__setitem__(1, {"field": "market_p", "value": "45%"}))
    assert any(c["check"] == "number traced" and "50%" in c["stated"] for c in fails(r, run))


def test_a_rounded_rate_cannot_flip_the_verdict():
    run = copy.deepcopy(RUN)
    run["cards"][0]["volume"][0]["cells"]["rows"]["season"]["rate"] = 0.778      # 9 x 0.778 = 7.002, reaches 7
    r = edit(lambda r: leg0(r).update(needs=[{"volume": 9, "rate": 0.775, "reaches": False}]))
    assert any(c["check"] == "rate rounding" for c in fails(r, run))


def test_number_tracing_keeps_units_apart():
    # 9 is a need volume: "9%" must not trace to it; 0.787 is a catch rate: a plain "79" must not trace to it
    r = edit(lambda r: leg0(r).update(fails="9%, and 79 more"))
    bad = {c["stated"] for c in fails(r) if c["check"] == "number traced"}
    assert "fails: 9%" in bad and "fails: 79" in bad


def test_injuries_must_match_section_4_and_a_named_injured_player_must_be_cited():
    assert any(c["check"] == "injury" for c in
               fails(edit(lambda r: leg0(r).update(injuries=[{"player": "Jonathan Mingo", "status": "Out"}]))))
    assert any(c["check"] == "injury named" for c in fails(edit(lambda r: leg0(r).update(injuries=[]))))
    # by last name, and a practice-only player counts
    r = edit(lambda r: r["players"][0].update(role_evidence="Nelson is limited"))
    assert any(c["check"] == "injury named" and "Nelson" in c["stated"] for c in fails(r))
    # a player in the personnel table is checked there, so the prose may name him
    assert not any(c["check"] == "injury named" and "Mayfield" in c["stated"] for c in
                   fails(edit(lambda r: r["players"][0].update(role_evidence="with Mayfield out"))))


def test_a_leg_not_on_the_board_fails_and_names_what_is():
    f = fails(edit(lambda r: leg0(r).update(line=7.5)))
    assert any(c["check"] == "on the board" and "receptions 6.5" in c["run"] for c in f)
    assert any(c["check"] == "on the board" for c in fails(edit(lambda r: r["players"][0].update(player="Ceedee Lam"))))


def test_an_under_leg_cites_its_own_sides_chance():
    r = edit(lambda r: (r["players"][0].update(explanation="The market has the Under at 50%."), leg0(r).update(side="under", cite=[{"field": "market_p_under", "value": "50%"}], needs=[],
                                      fails="he gets 7 catches", **{"if": "his share falls", "else": "skip it"}, injuries=[])))
    assert not [c for c in fails(r) if c["check"] in ("cite", "number traced")]
    assert P.resolve("engine_p_under", RUN, LAMB, LAMB["rows"][0], None) == pytest.approx(0.373)


# ---- the team brief and the guide's rules ----
def test_the_opening_read_is_three_sentences():
    assert any(c["check"] == "opening read" for c in fails(edit(lambda r: r.update(opening="One. Two."))))


def test_personnel_statuses_match_section_4_and_the_qb_change():
    assert any(c["check"] == "personnel" for c in fails(edit(lambda r: r["personnel"][0].update(status="Questionable"))))
    r = edit(lambda r: r["personnel"].append({"player": "Anthony Nelson", "status": "practice only", "changes": "x.",
                                             "affects": "y."}))
    assert not any(c["check"] == "personnel" for c in fails(r))


def test_game_narration_may_quote_the_brief_tables_and_nothing_else():
    assert not [c for c in fails(good()) if c["leg"] == 0]
    assert any(c["check"] == "number traced" and c["leg"] == 0 for c in
               fails(edit(lambda r: r.update(workload_read="The engine keeps 41.3 Dallas attempts."))))


@pytest.mark.parametrize("raw_edit, msg", [
    (lambda r: r.update(assumptions=["one"]), "two or three assumptions"),
    (lambda r: r.update(reads_version=1), "reads_version"),
    (lambda r: r["players"][0].update(matchup="neutral"), "matchup"),
    (lambda r: leg0(r).pop("else"), "missing else"),
    (lambda r: leg0(r)["cite"].append({"field": "market_p", "value": "about 50%"}), "not a number"),
    (lambda r: leg0(r)["needs"].append({"volume": 9, "rate": 0.787}), "reaches"),
    (lambda r: r["personnel"].append({"player": "X"}), "personnel row")])
def test_the_reads_are_validated_before_any_check(raw_edit, msg):
    r = copy.deepcopy(GOOD_RAW)
    raw_edit(r)
    with pytest.raises(P.ReadsError, match=msg):
        P.validate(r)


# ---- the verdict words, by definition ----
def test_verdict_words_follow_their_definitions():
    assert P.verdict(LAMB, "player_receptions")["word"] == "attainable"                 # 9 <= 10.7 and <= 21
    card = copy.deepcopy(LAMB)
    card["usage"]["tn"] = 8.0
    assert P.verdict(card, "player_receptions")["word"] == "requires a rebound"           # 9 > last game's 8
    card["volume"][0]["cells"]["proj"] = 9.5                                               # season 9 <= 9.5 -> by last game
    card["volume"][0]["cells"]["rows"]["season"]["vol"] = 11                               # 11 > 9.5, engine 10 > 9.5
    assert P.verdict(card, "player_receptions")["word"] == "requires more work than the engine expects"
    card["volume"][0]["cells"]["rows"]["engine"]["vol"] = 9                                # only the engine's rate clears
    assert P.verdict(card, "player_receptions")["word"] == "requires better gains"


def test_a_verdict_word_the_card_does_not_compute_is_refused():
    r = edit(lambda r: r["players"][0].update(explanation="This requires better gains."))
    assert any(c["check"] == "verdict word" for c in fails(r))
    assert not any(c["check"] == "verdict word" for c in
                   fails(edit(lambda r: r["players"][0].update(explanation="The workload is attainable."))))


# ---- the renders ----
def test_qa_version_follows_the_guide_and_shows_every_check():
    reads = good()
    checks = P.check(RUN, reads)
    qa = PR.render_qa(RUN, reads, checks, {"tag": "nfl-v9.9", "hash": "ab" * 32, "source": "fetched"})
    for h in ("## 1. What game does the market expect?", "## 2. How much passing and rushing", "## 3. What is each team",
              "## 4. Which personnel changes", "## 5. Where have opposing positions produced?", "## Receiving",
              "## A note on reliability", "## QA appendix"):
        assert h in qa, h
    assert qa.count("TB at DAL") == 0 and "TB AT DAL" in qa                 # the header's bold title is not repeated
    assert "| Win probability* | 80% | 20% |" in qa and "spread -3.5 to -9.5" in qa
    assert "not estimated" in qa and "log loss 0.717 against 0.692" in qa
    assert "| Verdict | attainable | attainable |" in qa
    assert "Engine chance he makes the required catches | 63% | 63%‡" in qa
    assert "**The market sets the line at 6.5, priced near even** (50% for the Over); the engine's middle is 8.0 (+1.5)." in qa
    assert "- **If you expect 9 targets at 79%, then receptions over 6.5 fits**, because 9 x 0.787 = 7.1" in qa
    assert "- **If his share falls back, skip it" in qa
    assert f"{len(checks)} of {len(checks)} pass" in qa


def test_production_paths_split_carries_and_catches():
    card = {"volume": [{"market": "player_rush_reception_yds", "cells": {"unit": "carries + catches", "proj": 19.4,
            "rows": {"season": {"vol_txt": "19 carries + 4 catches", "rate": [3.726, 5.133], "vol": 23, "pct": 0.29,
                                "rate_txt": "x"}}}}]}
    t = "\n".join(PR.production_paths(card))
    assert "| 19 carries at 3.7 + 4 catches at 5.1 (this season's gains) | 70.8 | 20.5 | 91.3 |" in t


def test_agent_version_embeds_the_release_documents_and_says_data_missing_without_ci():
    reads = good()
    ag = PR.render_agent(RUN, reads, P.check(RUN, reads), {"tag": "nfl-v9.9", "hash": "cd" * 32, "source": "fetched"}, None)
    assert "https://github.com/gabjew90/Fantasy-football/tree/nfl-v9.9" in ag
    assert "## 1. The system" in ag and "Data Source Matrix" in ag and "How the props engine works" in ag
    assert "DATA MISSING" in ag and "The reads and their checks" in ag and "margin_buckets_v0" in ag
    assert "{REF}" not in ag and "{REPO}" not in ag


def test_ci_results_report_the_pull_requests_suites_and_the_tags_own_runs():
    def get(u):
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


# ---- the command line ----
def _files(tmp_path, run=RUN, reads=GOOD_RAW):
    run_p, reads_p = tmp_path / "run_2026_wk05_TB_DAL.json", tmp_path / "reads.json"
    run_p.write_text(json.dumps(run), encoding="utf-8")
    reads_p.write_text(json.dumps(reads), encoding="utf-8")
    return run_p, reads_p


def test_main_renders_nothing_when_a_check_fails(tmp_path):
    bad = copy.deepcopy(GOOD_RAW)
    leg0(bad)["fails"] = "he saw 12 targets"
    run_p, reads_p = _files(tmp_path, reads=bad)
    out = tmp_path / "out"
    assert P.main(["--run", str(run_p), "--reads", str(reads_p), "--out", str(out), "--no-ci", "--which", "qa,agent"]) == 3
    assert not out.exists() or not list(out.iterdir())
    run_p, reads_p = _files(tmp_path)
    assert P.main(["--run", str(run_p), "--reads", str(reads_p), "--out", str(out), "--no-ci", "--which", "qa,agent"]) == 0
    assert sorted(p.name for p in out.iterdir()) == ["2026_wk05_TB_DAL_agent.md", "2026_wk05_TB_DAL_qa.md"]


def test_a_malformed_reads_file_is_a_message_not_a_traceback(tmp_path):
    bad = copy.deepcopy(GOOD_RAW)
    leg0(bad)["cite"].append({"field": "market_p", "value": "about 50%"})
    run_p, reads_p = _files(tmp_path, reads=bad)
    assert P.main(["--run", str(run_p), "--reads", str(reads_p), "--out", str(tmp_path / "o"), "--no-ci"]) == 2


def test_key_shaped_strings_are_scrubbed_from_what_is_written(tmp_path):
    run = copy.deepcopy(RUN)
    run["sources"].append({"name": "Sportsbook prices (The Odds API)", "purpose": "fallback", "status": "unavailable",
                           "detail": "URLError: /v4/sports?apiKey=0123456789abcdef0123456789abcdef&regions=us"})
    run_p, reads_p = _files(tmp_path, run=run)
    out = tmp_path / "o"
    assert P.main(["--run", str(run_p), "--reads", str(reads_p), "--out", str(out), "--no-ci", "--which", "qa,agent",
                   "--release-hash", "ab" * 32]) == 0
    for f in out.iterdir():
        txt = f.read_text(encoding="utf-8")
        assert "0123456789abcdef0123456789abcdef" not in txt and "apiKey=<redacted>" in txt
        assert not re.search(r"(?<![0-9a-fA-F])[0-9a-f]{32}(?![0-9a-fA-F])", txt)
    assert "ab" * 32 in (out / "2026_wk05_TB_DAL_agent.md").read_text(encoding="utf-8")


def test_a_run_file_that_is_not_the_reports_run_is_refused(tmp_path):
    run_p, reads_p = _files(tmp_path, run={**RUN, "data_cutoff": "- **Data cutoff:** an older run"})
    (tmp_path / "report_2026_wk05_TB_DAL.md").write_text("- **Data cutoff:** the newer run\n", encoding="utf-8")
    assert P.main(["--run", str(run_p), "--reads", str(reads_p), "--out", str(tmp_path / "o"), "--no-ci"]) == 2


# ---- the second code review (2026-10-08) ----
def test_player_prose_cannot_quote_a_brief_table_number_without_citing_it():
    # 29.0 is Dallas's implied points: fine in the market narration, not in a player's prose uncited
    r = edit(lambda r: r["players"][0].update(basis="He has 29 catches."))
    assert any(c["check"] == "number traced" and "29" in c["stated"] for c in fails(r))
    cited = edit(lambda r: (r["players"][0].update(basis="Dallas is implied for 29.0 points."),
                            r["players"][0]["cite"].append({"field": "game.teams.DAL.implied_points", "value": 29.0})))
    assert not any(c["check"] == "number traced" and "29" in c["stated"] for c in fails(cited))


def test_a_legs_prose_traces_to_its_own_leg_not_a_sibling_legs():
    raw = copy.deepcopy(GOOD_RAW)
    yds = {"market": "rec yds", "side": "over", "line": 85.5, "if": "he catches 7 at 13.0", "fails": "he catches fewer",
           "else": "skip it", "needs": [{"volume": 7, "rate": 12.956, "reaches": True}]}
    raw["players"][0]["legs"].append(yds)
    leg0(raw)["fails"] = "he catches fewer than 86 yards' worth"         # 86 belongs to the yards leg
    assert any(c["check"] == "number traced" and "86" in c["stated"] for c in fails(P.validate(raw)))


def test_the_opening_counts_sentences_past_abbreviations():
    assert P.count_sentences("Antoine Winfield Jr. is out. Dallas vs. Tampa is lopsided. That is the game.") == 3


def test_an_alternate_line_leg_does_not_borrow_the_main_lines_requirement():
    card = copy.deepcopy(LAMB)
    card["rows"].append({**card["rows"][0], "line": 5.5, "book": "sleeper"})
    lg = {**LEG, "line": 5.5, "player": "CeeDee Lamb"}
    p = GOOD_RAW["players"][0]
    txt = PR.closing_paragraph(card, p, lg)
    assert "needs 9 targets" not in txt and "built at the 6.5 line" in txt


def test_an_under_legs_closing_says_the_requirement_is_the_overs():
    lg = {**LEG, "side": "under", "player": "CeeDee Lamb"}
    txt = PR.closing_paragraph(LAMB, GOOD_RAW["players"][0], lg)
    assert "the Over at receptions 6.5 needs" in txt and "(for the Over; this leg is the Under)" in txt
    assert "supports the Over's requirement" in txt and "receptions under 6.5 fits" in txt


def test_if_out_tables_render_the_moves_or_say_why_not():
    run = {**RUN, "if_out": [{"player": "Jonathan Mingo", "team": "DAL", "pos": "WR", "ran": True,
                              "moves": [{"player": "CeeDee Lamb", "team": "DAL", "market": "player_receptions", "side": "Over",
                                         "line": 6.5, "p_plays": 0.62, "p_out": 0.66, "move": 0.04}]},
                             {"player": "X", "team": "TB", "pos": "WR", "ran": False, "moves": []}]}
    t = "\n".join(PR.if_out_tables(run))
    assert "| CeeDee Lamb (DAL) | Over 6.5 receptions | 62% | 66% | +4 |" in t and "re-pricing failed" in t
    assert PR.if_out_tables(RUN) == []


def test_the_unit_footnote_states_the_runs_own_filter():
    t = "\n".join(PR.unit_table({**RUN, "unit_filter": "win probability 5-95%"}))
    assert "win probability 5-95%" in t
    assert "not recorded" in "\n".join(PR.unit_table(RUN))


def test_the_external_version_carries_no_internals():
    reads = good()
    ext = PR.render_external(RUN, reads)
    for w in ("DECISIONS", "PROTOTYPE", "MODEL_", "Checks", "Backend", "QA appendix", "release", "slug", "gsis"):
        assert w not in ext, w
    assert "## Receiving" in ext and "## Parlay Fit" in ext and "## Notes" in ext and "Data as of:" in ext


# ---- the full report (the user, 2026-10-08): market scenarios, the line vs the middle, combined, coverage ----
ALT = [{"key": "draftkings", "markets": [
    {"key": "spreads", "last_update": "t1", "outcomes": [{"name": "Dallas Cowboys", "point": -8.5, "price": -120},
                                                         {"name": "Tampa Bay Buccaneers", "point": 8.5, "price": 100}]},
    {"key": "alternate_spreads", "last_update": "t2", "outcomes": [
        {"name": "Tampa Bay Buccaneers", "point": -8.5, "price": 970}, {"name": "Dallas Cowboys", "point": 8.5, "price": -4200},
        {"name": "Dallas Cowboys", "point": -9.5, "price": -110}]}]}]

def test_alt_spread_scenarios_read_the_main_line_and_the_alternates_together():
    import research as RS
    sm = RS.alt_spread_scenarios(ALT, "Dallas Cowboys", "Tampa Bay Buccaneers", -8.5, 9)
    assert sm["status"] == "ok" and sm["favourite"] == "Dallas Cowboys"
    assert sm["favourite_by_cut"] == pytest.approx(0.5217, abs=1e-3)
    assert sm["underdog_by_cut"] == pytest.approx(0.0873, abs=1e-3)
    assert sm["within_one_score"] == pytest.approx(1 - 0.5217 - 0.0873, abs=1e-3)
    # without the main line (the alternates alone omit it) the pair is missing, and it says so
    alts_only = [{"key": "draftkings", "markets": [ALT[0]["markets"][1]]}]
    assert "no two-sided 8.5-point" in RS.alt_spread_scenarios(alts_only, "Dallas Cowboys", "Tampa Bay Buccaneers", -8.5)["status"]
    assert "no alternate spreads" in RS.alt_spread_scenarios([], "Dallas Cowboys", "Tampa Bay Buccaneers", -8.5)["status"]


def test_the_scenario_table_shows_the_markets_likelihoods_or_why_not():
    import research as RS
    run = {**RUN, "scenarios_market": {**RS.alt_spread_scenarios(ALT, "Dallas Cowboys", "Tampa Bay Buccaneers", -8.5, 9),
                                       "as_of": "2026-10-08T22:52:27Z", "credits_left": "437"}}
    t = "\n".join(PR.scenario_table(run, detail=True))
    assert "| DAL (favorite) wins by 9+ points | 52% |" in t and "| TB (underdog) wins by 9+ points | 9% |" in t
    assert "| Final margin stays within one score | 39% |" in t and "not a model" in t and "credits left" in t
    short = "\n".join(PR.scenario_table(run))
    assert "the market's own estimate" in short and "credits" not in short and "-4200" not in short
    missing = "\n".join(PR.scenario_table({**RUN, "scenarios_market": {"status": "skipped: 40 credits left; needs 100+"}}))
    assert "not estimated" in missing and "skipped: 40 credits left" in missing
    # the narration may quote the market's scenario numbers
    r = edit(lambda r: r.update(market_read=r["market_read"] + " The market gives Dallas a 52% chance of winning by 9+."))
    assert not [c for c in fails(r, run) if c["leg"] == 0]


def test_table_a_shows_the_line_against_the_engines_middle():
    t = "\n".join(PR.table_a(LAMB))
    assert "| Receptions | 6.5 · -127 / -130 | 8.0 (+1.5) | 50% | 63% |" in t and "moves the line instead" in t


def test_rushing_vs_combined_reads_the_lines_against_their_parts():
    card = {"name": "Javonte Williams", "usage": {"tn": 5.0, "tn_base": 4.0}, "book": "sleeper", "rows": [
        {"market": "player_rush_yds", "line": 65.5, "book": "sleeper", "median": 59.3, "p_over_model": 0.43, "p_over_book": 0.50},
        {"market": "player_reception_yds", "line": 14.5, "book": "sleeper", "median": 13.5, "p_over_model": 0.47, "p_over_book": 0.50},
        {"market": "player_rush_reception_yds", "line": 86.5, "book": "sleeper", "median": 76.7, "p_over_model": 0.40,
         "p_over_book": 0.51}], "volume": []}
    t = "\n".join(PR.rushing_vs_combined(card))
    assert "| Combined line minus rushing + receiving lines (65.5 + 14.5) | | +6.5 |" in t
    assert "| +3.9 |" in t and "set 2.6 yards above what its parts justify" in t
    assert "5 targets last game against 4.0 a game before" in t and "independently" in t
    assert PR.rushing_vs_combined(LAMB) == []


def test_every_priced_player_gets_a_card_and_the_qa_counts_coverage():
    other = copy.deepcopy(LAMB)
    other["name"], other["slot"] = "George Pickens", "WR2"
    run = {**RUN, "cards": [LAMB, other]}
    reads = good()
    qa = PR.render_qa(run, reads, P.check(run, reads), {})
    ext = PR.render_external(run, reads)
    assert "### George Pickens · WR2, DAL" in qa and "### CeeDee Lamb · WR1, DAL" in qa
    assert "### George Pickens · DAL · WR" in ext and "### CeeDee Lamb · DAL · WR" in ext
    assert "No written read for this player" in qa and "No written read for this player" not in ext
    assert "**Coverage:** 1 of 2 priced players have a written read; data cards only: George Pickens." in qa


def test_style_checks_refuse_long_paragraphs_vague_matchups_and_heavy_bold():
    long = edit(lambda r: r["players"][0].update(explanation="One. Two. Three. Four. Five."))
    assert any(c["check"] == "style" and "5 sentences" in c["stated"] for c in fails(long))
    vague = edit(lambda r: r["players"][0].update(explanation="This is a favorable matchup for him."))
    assert any(c["check"] == "style" and "favorable matchup" in c["stated"] for c in fails(vague))
    bold = edit(lambda r: r["players"][0].update(explanation="**One** thing and **another**."))
    assert any(c["check"] == "style" and "bold" in c["stated"] for c in fails(bold))
    assert not [c for c in fails(good()) if c["check"] == "style"]


def test_the_customer_card_follows_the_guide_exactly():
    reads = good()
    ext = PR.render_external(RUN, reads)
    # the guide's tables, and only those
    assert "| Prop | Line · Over / Under prices | Market Over estimate | Engine Over estimate |" in ext
    assert "| Gain reference | Workload needed to clear | Engine chance of reaching that workload |" in ext
    assert "| This season | 9 targets at 79% | 67% |" in ext and "| Big gains trimmed | Unavailable | Unavailable |" in ext
    assert "Engine middle" not in ext and "| Verdict |" not in ext and "Chance of those catches" not in ext
    assert "*Chance of reaching the workload, not of clearing the line." in ext
    assert "Workload consistent with the market price, assuming the engine's gains: 9.2 targets." in ext
    # the closing read in the guide's order, then the two if-then bullets with the price
    order = ["The market prices receptions 6.5 near even (50% Over); the engine's middle forecast is 8.",
             "The engine expects 10.7 targets, based on last game's 21 targets.",
             "At this season's gain reference, the line requires **9 targets**, which the engine reaches 67% of the time: attainable.",
             "This matchup supports that requirement because Tampa is without its starting safety.",
             "Catches vs yards: receptions 6.5 needs 7 catches; receiving yards 85.5 needs 7 at 13.0 yards",
             "- **If you expect 9 targets at 79%, receptions over 6.5 (-127) fits**: about 7.1 catches, past the 7 the Over needs."]
    idx = [ext.index(x) for x in order]
    assert idx == sorted(idx)
    assert "It stops fitting if his share falls back toward 26%, under the market-implied 9.2 targets." in ext
    # horizontal rules, Parlay Fit, the shared notes at the end
    assert ext.count("\n---\n") >= 6 and "Parlay value not assessed" in ext and "**Missing inputs:**" in ext


def test_parlay_relationships_must_fit_the_legs():
    def with_pairs(pairs):
        return edit(lambda r: r["parlay"].update(pairs=pairs))
    a, b = "CeeDee Lamb|receptions|over|6.5", "CeeDee Lamb|receptions|under|6.5"
    ok = [c for c in P.check(RUN, with_pairs([{"a": a, "b": b, "relationship": "direct conflict", "reason": "x",
                                               "guidance": "Do not combine"}])) if c["check"] == "parlay pair"]
    assert ok and ok[0]["ok"]
    # over 6.5 and under 7.5 both win at 7: not a direct conflict
    bad = with_pairs([{"a": a, "b": "CeeDee Lamb|receptions|under|7.5", "relationship": "direct conflict",
                       "reason": "x", "guidance": "y"}])
    assert any(c["check"] == "parlay pair" and not c["ok"] for c in P.check(RUN, bad))
    # shared exposure is one player's role
    other = with_pairs([{"a": a, "b": "George Pickens|rec yds|over|65.5", "relationship": "shared exposure",
                         "reason": "x", "guidance": "y"}])
    assert any(c["check"] == "parlay pair" and not c["ok"] for c in P.check(RUN, other))
    assert P.both_can_win(P.parse_leg("X|receptions|over|6.5"), P.parse_leg("X|receptions|under|8.5"))
    assert not P.both_can_win(P.parse_leg("X|receptions|over|6.5"), P.parse_leg("X|receptions|under|7"))
    with pytest.raises(P.ReadsError):
        P.validate({**GOOD_RAW, "parlay": {"opening": "x"}})


def test_only_a_chat_game_run_spends_credits_on_scenario_prices():
    root = Path(__file__).resolve().parents[2]
    sg = (root / "props/engine/scripts/score_game.py").read_text(encoding="utf-8")
    assert "if SNAP is None and not a.no_odds and a.scenario_prices:" in sg       # opt-in, never a what-if re-run
    for f in ("props/engine/scripts/score_week.py", ".github/workflows/props.yml"):
        assert "scenario-prices" not in (root / f).read_text(encoding="utf-8"), f
    assert "--scenario-prices" in (root / "nfl.py").read_text(encoding="utf-8")


def test_a_pickem_has_no_favorite_label():
    import research as RS
    alt = copy.deepcopy(ALT)
    sm = RS.alt_spread_scenarios(alt, "Dallas Cowboys", "Tampa Bay Buccaneers", 0.0, 9)
    t = "\n".join(PR.scenario_table({**RUN, "market_env": {**RUN["market_env"], "home_spread": 0.0},
                                     "scenarios_market": sm}))
    assert "favorite" not in t and "underdog" not in t and "| DAL wins by 9+ points |" in t


def test_a_near_miss_is_never_rounded_onto_the_need():
    lg = {"market": "pass yds", "side": "under", "line": 270.5, "if": "x", "fails": "y", "else": "z",
          "needs": [{"volume": 24, "rate": 11.27, "reaches": False}]}
    t = "\n".join(PR.branches(lg, {"volume": [{"market": "player_pass_yds", "cells": {"unit": "completions"}}]},
                              compact=True))
    assert "about 270.5 yards, short of the 271" in t


def test_the_needs_row_says_when_it_is_the_season_rate():
    card = {"name": "B", "usage": {}, "book": "sleeper", "rows": [
        {"market": "player_rush_yds", "line": 40.5, "book": "sleeper", "median": 40.0},
        {"market": "player_rush_reception_yds", "line": 50.5, "book": "sleeper", "median": 52.0}],
        "volume": [{"market": "player_rush_yds", "line": 40.5, "cells": {"unit": "carries", "proj": 10.0, "rows": {
            "season": {"vol": 11, "vol_txt": "11 carries", "rate": 3.8, "rate_txt": "3.8", "pct": 0.4}}}}]}
    t = "\n".join(PR.rushing_vs_combined(card, compact=True))
    assert "11 carries (this season's gains)" in t


# ---- the review of the guide-exact card (2026-10-08) ----
def test_an_alternate_line_leg_says_table_b_is_at_the_main_line():
    card = copy.deepcopy(LAMB)
    card["rows"].append({**card["rows"][0], "line": 5.5})
    leg = {**LEG, "line": 5.5, "player": "CeeDee Lamb"}
    lines = "\n".join(PR.card_customer(RUN, card, GOOD_RAW["players"][0], [leg]))
    assert "Table B is built at the 6.5 line; this leg's 5.5 has no workload table in the run." in lines
    assert "requires **9 targets**" not in lines
    assert "This line has no workload table in the run (Table B is at the 6.5 line)." in lines


def test_an_unavailable_gain_row_says_why():
    card = copy.deepcopy(LAMB)
    card["volume"][1]["cells"]["rows"].pop("capped")
    t = "\n".join(PR.table_b_guide(card, "player_reception_yds"))
    assert "| Big gains trimmed | Unavailable | Unavailable |" in t and "too few plays in his recent games" in t


def test_a_combined_only_player_keeps_his_workload_line():
    card = {"rows": [{"market": "player_rush_reception_yds", "line": 50.5, "book": "s"}], "book": "s",
            "volume": [{"market": "player_rush_reception_yds", "volume_text": "14.4 carries + 3.2 catches"}]}
    assert PR.workload_line(card) == "14.4 carries + 3.2 catches"
    both = {"rows": [{"market": "player_rush_yds", "line": 40.5, "book": "s"},
                     {"market": "player_rush_reception_yds", "line": 50.5, "book": "s"}], "book": "s",
            "volume": [{"market": "player_rush_yds", "volume_text": "14.4 carries"},
                       {"market": "player_rush_reception_yds", "volume_text": "14.4 carries + 3.2 catches"}]}
    assert PR.workload_line(both) == "14.4 carries"


def test_pair_rules_check_the_stat_for_tension_and_competition():
    run = copy.deepcopy(RUN)
    qb = {"name": "Dak Prescott", "team": "DAL", "pos": "QB", "slot": "QB1", "book": "s", "rows": [], "volume": []}
    back = {"name": "Javonte Williams", "team": "DAL", "pos": "RB", "slot": "RB1", "book": "s", "rows": [], "volume": []}
    run["cards"] = [LAMB, qb, back]
    bad = {"a": "Dak Prescott|pass yds|under|270.5", "b": "Javonte Williams|rush yds|over|65.5",
           "relationship": "production tension", "reason": "x", "guidance": "y"}
    assert P.check_pair(run, bad)
    good_ = {**bad, "b": "CeeDee Lamb|rec yds|over|85.5"}
    assert P.check_pair(run, good_) is None
    comp = {"a": "CeeDee Lamb|rec yds|over|85.5", "b": "Javonte Williams|rush yds|over|65.5",
            "relationship": "opportunity competition", "reason": "x", "guidance": "y"}
    assert "same pool" in P.check_pair(run, comp)


def test_the_parlay_closing_is_bolded_once():
    r = P.validate({**GOOD_RAW, "parlay": {"opening": "x.", "closing": "keep **Lamb** alone"}})
    sec = "\n".join(PR.parlay_section(r))
    assert "**keep Lamb alone**" in sec and "****" not in sec
