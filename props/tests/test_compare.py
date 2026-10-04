"""Sleeper against DraftKings/FanDuel (props/compare.py, DECISIONS #147):
one snapshot per game in the capture window, graded on the scorecard by the
pre-registered rule in reports/sleeper_vs_books.md."""

from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

import pandas as pd
import pytest

PROPS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROPS))

import compare as C  # noqa: E402
import persist  # noqa: E402
import scorecard  # noqa: E402

NOW = dt.datetime(2026, 10, 4, 15, 0, tzinfo=dt.timezone.utc)
EVENT = {"id": "ev1", "commence_time": "2026-10-04T17:00:00Z", "away_team": "Dallas Cowboys",
         "home_team": "Houston Texans"}
LATER = {"id": "ev2", "commence_time": "2026-10-05T00:20:00Z", "away_team": "A", "home_team": "B"}


def _payload():
    def out(desc, line, po, pu):
        return [{"name": "Over", "description": desc, "point": line, "price": po},
                {"name": "Under", "description": desc, "point": line, "price": pu}]
    return {"id": "ev1", "commence_time": EVENT["commence_time"], "home_team": EVENT["home_team"],
            "away_team": EVENT["away_team"], "bookmakers": [
                {"key": "draftkings", "markets": [{"key": "player_receptions", "last_update": "x",
                                                   "outcomes": out("Dalton Schultz", 3.5, -105, -125)}]},
                {"key": "fanduel", "markets": [{"key": "player_receptions", "last_update": "x",
                                                "outcomes": out("Dalton Schultz", 3.5, -110, -120)}]}]}


@pytest.fixture
def engine(tmp_path, monkeypatch):
    monkeypatch.setattr(persist, "RECORD_ROOT", tmp_path / "record")
    eng = tmp_path / "engine"
    (eng / "scripts" / "cache").mkdir(parents=True)
    calls = []

    def fake(engine_dir, stage, *args):
        calls.append(stage)
        if stage == "events":
            return {"class": "OK", "quota": {"x-requests-remaining": "450"}, "events": [EVENT, LATER]}
        (engine_dir / "scripts" / "cache" / f"odds_{args[0]}_1.json").write_text(
            json.dumps({"class": "OK", "data": _payload()}), encoding="utf-8")
        return {"class": "OK", "quota": {"x-requests-remaining": "446"}, "retrieved_at_utc": "2026-10-04T15:00:00Z"}
    return eng, fake, calls


def test_one_snapshot_per_game_in_the_window(engine):
    eng, fake, calls = engine
    c = C.capture(2026, 4, eng, now=NOW, odds_fn=fake)
    assert c["events_in_window"] == 1 and c["compared"] == 1 and c["rows"] == 4, "ev2 is outside the window"
    assert calls == ["events", "odds"]
    again = C.capture(2026, 4, eng, now=NOW, odds_fn=fake)
    assert again["compared"] == 0 and again["skipped_done"] == 1, "never twice for one game"
    rows = [json.loads(l) for l in C.compare_path(2026, 4).read_text(encoding="utf-8").splitlines()]
    assert {r["book"] for r in rows} == {"draftkings", "fanduel"} and rows[0]["line"] == 3.5


def test_the_last_credits_are_never_spent(engine):
    eng, fake, calls = engine
    def poor(engine_dir, stage, *args):
        if stage == "events":
            return {"class": "OK", "quota": {"x-requests-remaining": "60"}, "events": [EVENT]}
        raise AssertionError("no odds call below the floor")
    c = C.capture(2026, 4, eng, now=NOW, odds_fn=poor)
    assert c["compared"] == 0 and "60 credits left" in c["stopped"]


def test_no_key_is_a_reason_not_a_failure(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(C, "capture", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("no key")))
    assert C.main(["--season", "2026", "--week", "4"]) == 0
    assert "compare: skipped (RuntimeError: no key)" in capsys.readouterr().out


def test_the_scorecard_grades_the_consensus_side_at_sleepers_price(tmp_path, monkeypatch):
    monkeypatch.setattr(persist, "RECORD_ROOT", tmp_path / "record")
    rows = C.rows_from(_payload(), 2026, 4, "t")
    # Sleeper at 4.5 vs consensus 3.5 (line off by 1 catch): the Under is favoured
    settled = pd.DataFrame([
        {"week": 4, "player": "Dalton Schultz", "market": "player_receptions", "line": 4.5, "actual": 3,
         "price_over": -116, "price_under": -141, "event_id": "s1"},
        # same line, Sleeper's no-vig Over 53.2% vs the consensus 48.4%: price off, Under favoured
        {"week": 4, "player": "Dalton Schultz", "market": "player_receptions", "line": 3.5, "actual": 5,
         "price_over": -125, "price_under": 105, "event_id": "s2"}])
    b = scorecard.books_rows(settled, rows)
    assert list(b.kind) == ["line off", "price off"]
    assert bool(b.won.iloc[0]) is True and b.pnl.iloc[0] == pytest.approx(10000 / 141)
    assert bool(b.won.iloc[1]) is False and b.pnl.iloc[1] == -100.0
    C.compare_path(2026, 4).parent.mkdir(parents=True)
    C.compare_path(2026, 4).write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
    md = "\n".join(scorecard.books_section(settled, 2026))
    assert "| line off | 1 | 1 | 100.0% |" in md and "no verdict yet" in md
