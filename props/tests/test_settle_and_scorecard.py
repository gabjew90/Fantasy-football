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
        "receptions": 4, "receiving_yards": 30, "rushing_yards": 40,
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
