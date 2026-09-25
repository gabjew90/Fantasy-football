"""Grading the record, and refusing to pool two engines.

settle grades every priced line (a superseded line beside the one that
replaced it is what makes the settled CSV self-explaining) and flags which
row is the call. scorecard counts only calls, and when the record holds more
than one engine version it prints each separately and no grand total unless
asked, because pooling two models' calls produces one number that describes
neither.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import pytest

PROPS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROPS))

import persist  # noqa: E402
import scorecard  # noqa: E402
import settle  # noqa: E402

pd = pytest.importorskip("pandas")


def _pred(**kw) -> dict:
    base = {"season": 2026, "week": 2, "game": "MIA@SF", "event_id": "ev1",
            "book": "sleeper", "market": "player_rush_yds",
            "player": "Christian McCaffrey", "team": "SF", "slot": "RB1",
            "side": "Under", "line": 58.5, "price": -123.0, "p_model": 0.556,
            "p_novig": 0.492, "gap": 0.063, "tier": "STRONG",
            "decision": "PASS", "model_state": "rush_yds_v0",
            "snapshot_type": "decision", "engine_hash": "aaa",
            "engine_tag": "props-v1.0",
            "logged_at_utc": "2026-09-18T05:07:37Z"}
    base.update(kw)
    return base


def _stat(display: str, abbrev: str) -> dict:
    """40 rushing yards, so an Under at 58.5 and at 59.5 both win."""
    return {
        "season": 2026, "week": 2, "team": "SF",
        "player_name": abbrev, "player_display_name": display,
        "receptions": 4, "receiving_yards": 30, "rushing_yards": 40, "passing_yards": 250,
        "receiving_tds": 0, "rushing_tds": 0, "_anytime_td": 0,
        "_name": settle.norm_name(display),
        "_loose": settle.loose_key(abbrev),
    }


def _stats_frame() -> "pd.DataFrame":
    return pd.DataFrame([_stat("Christian McCaffrey", "C.McCaffrey"),
                         _stat("Other Player", "O.Player")])


@pytest.fixture
def record(tmp_path, monkeypatch):
    """A record root with one week of predictions, and no network."""
    root = tmp_path / "record"
    (root / "predictions" / "2026").mkdir(parents=True)
    monkeypatch.setattr(persist, "RECORD_ROOT", root)
    monkeypatch.setattr(settle.persist, "RECORD_ROOT", root)
    monkeypatch.setattr(scorecard.persist, "RECORD_ROOT", root)
    monkeypatch.setattr(settle, "load_stats", lambda season, cache: _stats_frame())
    # The schedule is a network read behind a day-old cache. Tests that are
    # not about game context get a fixed one rather than a machine-dependent
    # one; the two tests below drive the real reader with a stub schedule.
    monkeypatch.setattr(settle, "game_context", lambda season: {
        (2, "SF"): {"team_points": 24.0, "opp_points": 17.0,
                    "game_total": 41.0}})
    return root


def _write(root: Path, rows: list[dict]) -> None:
    with (root / "predictions" / "2026" / "wk02.jsonl").open(
            "w", encoding="utf-8", newline="\n") as fh:
        for row in rows:
            fh.write(json.dumps(row, sort_keys=True) + "\n")


def _settled(root: Path) -> list[dict]:
    path = persist.settled_path(2026)
    with path.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


# ------------------------------------------------------------------- settle

def test_settle_grades_history_and_flags_the_call(record):
    """Both McCaffrey rows are graded; only the later one is the call."""
    _write(record, [_pred(),
                    _pred(line=59.5, price=-132.0,
                          logged_at_utc="2026-09-18T05:20:46Z")])
    assert settle.main(["--season", "2026"]) == 0

    rows = _settled(record)
    assert len(rows) == 2, "history is graded, not dropped"
    by_line = {r["line"]: r for r in rows}
    assert by_line["58.5"]["is_call"] == "0"
    assert by_line["59.5"]["is_call"] == "1"
    # csv writes the truth value as 1/0 or True/False depending on the dtype
    # the comparison produced; either way both Unders won on 40 rushing yards.
    assert all(str(r["won"]) in ("1", "True") for r in rows)
    assert all(r["engine_tag"] == "props-v1.0" for r in rows)


def test_passing_yards_settle_on_the_qbs_own_passing_yards(record):
    _write(record, [_pred(market="player_pass_yds", side="Over", line=240.5, model_state="pass_yds_v0")])
    assert settle.main(["--season", "2026"]) == 0
    (row,) = _settled(record)
    assert str(row["won"]) in ("1", "True"), "250 passing yards beats an Over at 240.5"


def test_a_second_settle_does_not_duplicate_rows_without_a_line(record):
    """The latent bug this pins: the settled key stringified line as "None"
    on write and "" on read, so anytime-TD rows (no line) keyed differently
    each way and the first re-settle duplicated every one of them."""
    _write(record, [_pred(market="player_anytime_td", side="Yes", line=None)])
    assert settle.main(["--season", "2026"]) == 0
    assert len(_settled(record)) == 1
    assert settle.main(["--season", "2026"]) == 0
    assert len(_settled(record)) == 1, "the no-line row duplicated on re-settle"


def test_two_engines_grade_into_separate_rows(record):
    _write(record, [_pred(engine_hash="aaa", engine_tag="props-v1.0"),
                    _pred(engine_hash="bbb", engine_tag="props-v1.1")])
    assert settle.main(["--season", "2026"]) == 0
    rows = _settled(record)
    assert len(rows) == 2
    assert {r["engine_hash"] for r in rows} == {"aaa", "bbb"}
    assert {r["is_call"] for r in rows} == {"1"}, "one call per engine"


# ---------------------------------------------------------------- scorecard

def test_the_scorecard_counts_calls_not_graded_rows(record, capsys):
    _write(record, [_pred(),
                    _pred(line=59.5, logged_at_utc="2026-09-18T05:20:46Z")])
    settle.main(["--season", "2026"])
    assert scorecard.main(["--season", "2026"]) == 0
    text = (record / "scorecard.md").read_text(encoding="utf-8")
    assert "1 calls (2 priced lines graded, so 1 superseded by a later line)" in text
    assert "## Engine props-v1.0" in text


def test_the_scorecard_refuses_to_pool_two_engines(record):
    _write(record, [_pred(engine_hash="aaa", engine_tag="props-v1.0"),
                    _pred(engine_hash="bbb", engine_tag="props-v1.1",
                          player="Other Player")])
    settle.main(["--season", "2026"])
    assert scorecard.main(["--season", "2026"]) == 0
    text = (record / "scorecard.md").read_text(encoding="utf-8")
    assert "2 engine versions in the record" in text
    assert "they are not pooled" in text
    assert "## Engine props-v1.0" in text and "## Engine props-v1.1" in text
    assert "pooled by request" not in text, "no grand total without --pool"


def test_pool_is_the_explicit_override(record):
    _write(record, [_pred(engine_hash="aaa", engine_tag="props-v1.0"),
                    _pred(engine_hash="bbb", engine_tag="props-v1.1",
                          player="Other Player")])
    settle.main(["--season", "2026"])
    assert scorecard.main(["--season", "2026", "--pool"]) == 0
    text = (record / "scorecard.md").read_text(encoding="utf-8")
    assert "## All engines (pooled by request)" in text
    assert "describe no single one of them" in text


def test_one_engine_needs_no_refusal_and_no_pool_section(record):
    _write(record, [_pred()])
    settle.main(["--season", "2026"])
    scorecard.main(["--season", "2026"])
    text = (record / "scorecard.md").read_text(encoding="utf-8")
    assert "not pooled" not in text
    assert "pooled by request" not in text


def test_a_settled_file_without_is_call_is_read_not_crashed(record, capsys):
    """Tuesday's job must not die on a CSV written before is_call existed."""
    _write(record, [_pred()])
    settle.main(["--season", "2026"])
    path = persist.settled_path(2026)
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    fields = [f for f in rows[0] if f != "is_call"]
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    assert scorecard.main(["--season", "2026"]) == 0
    assert "predates is_call" in capsys.readouterr().err


# ---------------------------------------------------------------------- CLV

def test_clv_pairs_one_call_with_one_close(record):
    """The fan-out this prevents: the old join was on seven fields excluding
    `line`, so two decision rows each paired with every close row."""
    _write(record, [
        _pred(),
        _pred(line=59.5, logged_at_utc="2026-09-18T05:20:46Z"),
        _pred(snapshot_type="close", line=56.5,
              logged_at_utc="2026-09-20T19:40:00Z"),
        _pred(snapshot_type="close", line=55.5,
              logged_at_utc="2026-09-20T19:55:00Z"),
    ])
    clv = scorecard.clv_table(2026)
    assert len(clv) == 1, "one call, one closing line"
    row = clv.iloc[0]
    assert row["line_dec"] == 59.5, "the call, not the superseded line"
    assert row["line_close"] == 55.5, "the last close, not the first"
    assert row["line_move"] == pytest.approx(-4.0)
    assert bool(row["moved_our_way"]) is True, "an Under wants the number down"


# ------------------------------------------- why the call missed, not just that

def _rich_stats_frame() -> "pd.DataFrame":
    """The same week, with the usage columns nflverse actually publishes."""
    df = _stats_frame()
    df["targets"] = [7, 2]
    df["carries"] = [14, 0]
    df["target_share"] = [0.212, 0.061]
    df["air_yards_share"] = [0.184, 0.044]
    df["wopr"] = [0.511, 0.131]
    df["opponent_team"] = ["MIA", "MIA"]
    return df


def test_a_graded_call_carries_the_usage_and_the_game_that_explain_it(
        record, monkeypatch):
    """Grading says the Under won. Review asks why the projection was 22
    yards high, and that question is only answerable if the row remembers how
    much of the offence the player actually got and what the game looked
    like."""
    monkeypatch.setattr(settle, "load_stats",
                        lambda season, cache: _rich_stats_frame())
    _write(record, [_pred(model_mean=62.4)])
    assert settle.main(["--season", "2026"]) == 0

    row = _settled(record)[0]
    assert float(row["actual"]) == 40.0
    # 40 rushing yards against a 62.4 projection: the model was 22.4 high.
    assert float(row["miss"]) == pytest.approx(-22.4)
    assert int(float(row["carries"])) == 14
    assert float(row["target_share"]) == pytest.approx(0.212)
    assert float(row["wopr"]) == pytest.approx(0.511)
    assert row["opponent"] == "MIA"
    # SF 24, MIA 17 -- not a blowout, so a starter's snaps are not the story.
    assert float(row["team_points"]) == 24.0
    assert float(row["opp_points"]) == 17.0
    assert float(row["game_total"]) == 41.0


def test_a_row_with_no_projection_grades_anyway_and_leaves_miss_empty(
        record, monkeypatch):
    """`model_mean` is not in the settled schema's required core. A row that
    predates it, or a market that does not produce one, still grades -- the
    diagnostic is a bonus and may never gate a settle."""
    monkeypatch.setattr(settle, "load_stats",
                        lambda season, cache: _rich_stats_frame())
    _write(record, [_pred()])
    assert settle.main(["--season", "2026"]) == 0
    row = _settled(record)[0]
    assert row["status"] == "settled" and row["miss"] == ""


def test_game_context_reads_the_schedule_and_ignores_unplayed_games(monkeypatch):
    """Both teams get a row, and a game with no score yet contributes none --
    otherwise week 3's fixtures would settle week 2's calls to 0-0."""
    import guard
    monkeypatch.setattr(guard, "load_games", lambda season: [
        {"week": "2", "home_team": "SF", "away_team": "MIA",
         "home_score": "24", "away_score": "17"},
        {"week": "3", "home_team": "SF", "away_team": "ARI",
         "home_score": "", "away_score": ""},
    ])
    ctx = settle.game_context(2026)
    assert ctx[(2, "SF")] == {"team_points": 24.0, "opp_points": 17.0,
                              "game_total": 41.0}
    assert ctx[(2, "MIA")] == {"team_points": 17.0, "opp_points": 24.0,
                               "game_total": 41.0}
    assert (3, "SF") not in ctx


def test_an_unreadable_schedule_costs_context_and_nothing_else(monkeypatch, capsys):
    """settle runs on Tuesday against a record that is already written. A
    schedule fetch that fails must not take the grades down with it."""
    import guard

    def boom(season):
        raise OSError("no network")

    monkeypatch.setattr(guard, "load_games", boom)
    assert settle.game_context(2026) == {}
    assert "game context unavailable" in capsys.readouterr().err


def test_anytime_td_rows_without_a_model_stamp_are_model_unknown_not_v1():
    """Rows captured before td_model reached the record carry no stamp. They
    must not be pooled with v1 rows (or with the v0 fallback)."""
    import pandas as pd
    df = pd.DataFrame({"market": ["player_anytime_td", "player_anytime_td", "player_anytime_td",
                                  "player_receptions"],
                       "td_model": [None, "anytime_td_v1", "anytime_td_v0", None]})
    keys = list(scorecard.market_key(df))
    assert keys == ["player_anytime_td [model unknown]", "player_anytime_td [anytime_td_v1]",
                    "player_anytime_td [anytime_td_v0]", "player_receptions"]
    assert list(scorecard.market_key(df.drop(columns="td_model")))[0] == "player_anytime_td [model unknown]"


def test_the_pooled_tables_hold_only_v1_anytime_rows():
    import pandas as pd
    df = pd.DataFrame({"market": ["player_anytime_td"] * 3 + ["player_receptions"],
                       "td_model": ["anytime_td_v1", "anytime_td_v0", None, None],
                       "won": [1, 0, 1, 0], "p_model": [0.3, 0.3, 0.3, 0.6], "p_novig": [0.3] * 4,
                       "pnl_per_100": [100, -100, 100, -100], "tier_base": ["UNTIERED"] * 4,
                       "week": [3] * 4, "engine_hash": ["h"] * 4, "questionable_teammate": [False] * 4})
    out, _ = scorecard.render_sections(df)
    text = "\n".join(out)
    assert text.startswith("2 settled calls")              # v1 TD + receptions
    assert "2 anytime-TD calls priced by the v0 fallback or by an unrecorded model" in text
    assert "player_anytime_td [anytime_td_v0]" in text and "player_anytime_td [model unknown]" in text
    only_other = df.iloc[1:3]
    scorecard.render_sections(only_other)                     # no division by zero


def test_load_stats_refreshes_a_file_older_than_its_max_age(tmp_path, monkeypatch):
    # A settle file cached before week N was played would grade week N as unplayed.
    import os
    import time
    import urllib.request
    import settle
    csv_ = "season_type,week,player_name,player_display_name\nREG,{w},A.Brown,A.J. Brown\n"

    def fake(url, dest):
        Path(dest).write_text(csv_.format(w=2), encoding="utf-8")
    monkeypatch.setattr(urllib.request, "urlretrieve", fake)
    f = tmp_path / "stats_player_week_2026.csv"
    f.write_text(csv_.format(w=1), encoding="utf-8")
    old = time.time() - 4 * 3600
    os.utime(f, (old, old))
    df = settle.load_stats(2026, f, max_age_s=3 * 3600)
    assert df["week"].tolist() == [2]
