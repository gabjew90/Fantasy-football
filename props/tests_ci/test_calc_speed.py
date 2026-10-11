"""The calculator's speed-ups (DECISIONS #236): parsed files kept for the session, a game's posted
lines listed from the saved quotes, and the `game` command building every card from one load.
A chat game read on 2026-10-11 ran 56 separate processes, each re-reading three seasons of
play-by-play (about 27 s here); card text does not change."""
from __future__ import annotations

import json
import os
from argparse import Namespace
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

from props.calc import __main__ as CLI
from props.calc import capture, data, lines
from props.calc.checks import DataError

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_calc_basics import LEG, ROSTER, _calc_rows, _write_archive  # noqa: E402


# ---------------------------------------------------------------- the parsed-file cache

def test_a_parsed_file_is_kept_and_reused_until_its_source_changes(tmp_path, monkeypatch):
    src = tmp_path / "pbp.csv"
    src.write_text("season,week,keep,drop\n2026,1,a,x\n2026,2,b,y\n", encoding="utf-8")
    first = data.parsed_csv(src, ["season", "week", "keep"], "t")
    assert list(first.columns) == ["season", "week", "keep"] and len(first) == 2
    assert len(list(tmp_path.glob("pbp.csv.t.*.pkl"))) == 1
    real = pd.read_csv
    monkeypatch.setattr(pd, "read_csv", lambda *a, **k: pytest.fail("the cache should have answered"))
    pd.testing.assert_frame_equal(data.parsed_csv(src, ["season", "week", "keep"], "t"), first)
    monkeypatch.setattr(pd, "read_csv", real)
    # a refreshed source (new size and time) is read again, and the old copy goes
    src.write_text("season,week,keep,drop\n2026,1,a,x\n2026,2,b,y\n2026,3,c,z\n", encoding="utf-8")
    os.utime(src, ns=(src.stat().st_atime_ns, src.stat().st_mtime_ns + 10_000_000))
    again = data.parsed_csv(src, ["season", "week", "keep"], "t")
    assert len(again) == 3 and len(list(tmp_path.glob("pbp.csv.t.*.pkl"))) == 1
    # other columns are another cache, not a wrong answer
    assert list(data.parsed_csv(src, ["season", "drop"], "t").columns) == ["season", "drop"]


def test_a_broken_cache_is_read_from_the_source_again(tmp_path):
    src = tmp_path / "r.csv"
    src.write_text("a,b\n1,2\n", encoding="utf-8")
    data.parsed_csv(src, ["a"], "t")
    (cache,) = tmp_path.glob("r.csv.t.*.pkl")
    cache.write_bytes(b"not a pickle")
    assert data.parsed_csv(src, ["a"], "t")["a"].tolist() == [1]


# ---------------------------------------------------------------- a game's posted lines

GAME = {"season": 2026, "week": 6, "kickoff_utc": LEG["kickoff_utc"], "game_id": "2026_06_LA_SF",
        "home_team": "SF", "away_team": "LA"}


def test_the_game_lists_each_market_and_player_once_from_quotes_before_kickoff(tmp_path):
    rows = capture.archive_rows(_calc_rows([(64.5, "2026-10-11T20:00:00+00:00"), (66.5, "2026-10-11T23:50:00+00:00")]))
    late = capture.archive_rows(_calc_rows([(70.5, "2026-10-12T01:00:00+00:00")], gsis="00-9"))   # after kickoff
    other = capture.archive_rows(_calc_rows([(50.5, "2026-10-11T20:00:00+00:00")], gsis="00-8",
                                            game="2026_06_DAL_NYG"))
    for r in other:
        r["home_team"], r["away_team"] = "New York Giants", "Dallas Cowboys"
    _write_archive(tmp_path / "mine", rows + late + other)
    # the engine's rows: names only; one is the same player and market (folded in), one is new
    eng = [dict(r, gsis_id=None, game_id=None, team=None, snapshot_type="decision", player="Christian McCaffrey")
           for r in rows[:2]]
    eng += [dict(rows[0], gsis_id=None, game_id=None, team=None, player="Puka Nacua", market="player_reception_yds",
                 snapshot_type="decision")]
    eng += [dict(rows[0], retrieved_at_utc="garbled", player="Someone Else", gsis_id=None, game_id=None, team=None)]
    _write_archive(tmp_path / "rec", eng)
    got, unread, bad = lines.LineLookup(ROSTER, archive_root=tmp_path / "rec", calc_root=tmp_path / "mine").posted(GAME)
    assert bad == []
    by = {(g["market"], g["player"]): g for g in got}
    # Sleeper's "C. McCaffrey" (id) and the engine's "Christian McCaffrey" (name) are one player: one entry,
    # under the roster's full name so the card finds him exactly
    assert set(by) == {("rush_yds", "Christian McCaffrey"), ("rec_yds", "Puka Nacua")}, by
    assert (by[("rush_yds", "Christian McCaffrey")]["gsis_id"], by[("rush_yds", "Christian McCaffrey")]["team"]) == ("00-2", "SF")
    assert (by[("rec_yds", "Puka Nacua")]["gsis_id"], by[("rec_yds", "Puka Nacua")]["team"]) == ("00-4", "LA"), \
        "a name-only row takes its id and team from the two teams' roster"
    assert unread == 1, "the garbled row is counted, not dropped silently"


def test_a_name_the_roster_cannot_settle_stays_a_name(tmp_path):
    rows = capture.archive_rows(_calc_rows([(64.5, "2026-10-11T20:00:00+00:00")]))
    eng = [dict(rows[0], gsis_id=None, game_id=None, team=None, player="Practice Squad Guy", snapshot_type="decision")]
    _write_archive(tmp_path / "rec", eng)
    got, _, _ = lines.LineLookup(ROSTER, archive_root=tmp_path / "rec", calc_root=tmp_path / "none").posted(GAME)
    assert got == [{"player": "Practice Squad Guy", "gsis_id": None, "team": None, "market": "rush_yds"}]


def test_a_blank_roster_team_and_an_unreadable_file_do_not_stop_the_game(tmp_path):
    blank = pd.concat([ROSTER, ROSTER.iloc[[0]].assign(gsis_id="00-99", full_name="No Team", team=None)])
    _write_archive(tmp_path / "mine", capture.archive_rows(_calc_rows([(64.5, "2026-10-11T20:00:00+00:00")])))
    (tmp_path / "rec" / "2026").mkdir(parents=True)
    lines.archive_path(2026, tmp_path / "rec").write_text("{not json\n", encoding="utf-8")
    got, _, bad = lines.LineLookup(blank, archive_root=tmp_path / "rec", calc_root=tmp_path / "mine").posted(GAME)
    assert [g["player"] for g in got] == ["Christian McCaffrey"], "calc's own captures still count"
    assert len(bad) == 1, "the unreadable file is named, not a crash"


# ---------------------------------------------------------------- the game command

def _fake_card(name, team, market, side, line=64.5, ready=True, not_enough=False):
    sol = lambda v: SimpleNamespace(status="ok", value=v)
    c = {"solutions": {"needed_over": sol(19.1), "needed_under": sol(15.6)}, "usual": 16.0}
    return {"stub": {"player": name, "team": team, "game_id": GAME["game_id"]}, "ready": ready, "c": c,
            "line": line, "not_enough": not_enough, "reason": "12 carries in his last 16 games (needs 30)",
            "text": f"CARD {name} {market} {side}"}


@pytest.fixture
def one_load(monkeypatch):
    sched = pd.DataFrame([{**GAME, "kickoff_utc": "2099-10-12T00:20:00+00:00"}])
    loads, built = [], []
    monkeypatch.setattr(CLI, "_bundle", lambda season, fixed: loads.append(season) or
                        (SimpleNamespace(schedule=sched, rosters=ROSTER), ""))
    monkeypatch.setattr(lines.LineLookup, "posted", lambda self, g: (
        [{"player": "Puka Nacua", "gsis_id": "00-4", "team": "LA", "market": "rec_yds"},
         {"player": "Christian McCaffrey", "gsis_id": "00-2", "team": "SF", "market": "rush_yds"},
         {"player": "Backup Back", "gsis_id": "00-7", "team": "SF", "market": "rush_yds"},
         {"player": "Broken Guy", "gsis_id": "00-6", "team": "SF", "market": "rec_yds"}], 0, []))

    def card(b, name, market, side, **kw):
        built.append((name, market, side))
        if name == "Broken Guy":
            raise DataError("two quotes | one line\nsecond line")
        if name == "Puka Nacua" and side == "under":
            raise DataError("no under quote")
        return _fake_card(name, kw["team"], market, side, not_enough=(name == "Backup Back"))
    monkeypatch.setattr(CLI, "build_card", card)
    return loads, built


def _args(**kw):
    return Namespace(matchup="LA@SF", player=[], all=False, side="both", season=2026, week=6, **kw)


def test_one_load_a_summary_row_per_line_and_no_cards_unless_asked(one_load):
    loads, built = one_load
    out = CLI.game(_args())
    assert loads == [2026], "the data loads once for the whole game"
    assert out.startswith("LA at SF, week 6: 4 posted lines")
    assert "| Broken Guy | receiving yards | -- | not built: two quotes / one line second line | | |" in out, \
        "an error's text cannot break the table"
    assert "| Puka Nacua (LA) | receiving yards | 64.5 | ~19 targets | ~16 targets or fewer | 16.0 |" in out
    assert "| Christian McCaffrey (SF) | rushing yards | 64.5 | ~19 carries | ~16 carries or fewer | 16.0 |" in out
    assert "| Backup Back (SF) | rushing yards | 64.5 | not enough data: 12 carries" in out
    assert out.index("Puka Nacua") < out.index("Christian McCaffrey"), "the away team first"
    assert "CARD" not in out and "name players with --player" in out
    assert all(side == "over" for *_, side in built), "the summary needs one build per line"


def test_cards_for_the_players_named_both_sides_and_a_missing_name_is_said(one_load):
    _loads, built = one_load
    out = CLI.game(Namespace(matchup="la@sf", player=["Christian McCaffrey", "Nobody"], all=False, side="both",
                             season=2026, week=6))
    assert "CARD Christian McCaffrey rush_yds over" in out and "CARD Christian McCaffrey rush_yds under" in out
    assert "CARD Puka Nacua" not in out
    assert "No posted line in this game for: Nobody." in out
    one = CLI.game(Namespace(matchup="LA@SF", player=[], all=True, side="under", season=2026, week=6))
    assert one.count("CARD") == 2 and "over" not in " ".join(x for x in one.splitlines() if x.startswith("CARD"))
    assert "Puka Nacua receiving yards under: card not built: no under quote" in one, \
        "one side failing keeps the rest of the output"


def test_a_short_name_finds_the_player_and_a_failed_card_is_not_called_missing(one_load):
    out = CLI.game(Namespace(matchup="LA@SF", player=["C. McCaffrey", "Broken Guy"], all=False, side="over",
                             season=2026, week=6))
    assert "CARD Christian McCaffrey rush_yds over" in out, "Sleeper's short form names him"
    assert "No card for Broken Guy: the summary row says why." in out
    assert "No posted line" not in out


def test_a_bad_matchup_or_a_missing_game_stops_plainly(one_load):
    with pytest.raises(SystemExit, match="AWAY@HOME"):
        CLI.game(Namespace(matchup="LASF", player=[], all=False, side="both", season=2026, week=6))
    from props.calc import player
    with pytest.raises(player.NotFound, match="no 2026 SF@LA game in week 6"):
        CLI.game(Namespace(matchup="SF@LA", player=[], all=False, side="both", season=2026, week=6))
