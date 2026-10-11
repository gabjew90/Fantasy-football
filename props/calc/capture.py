"""Sleeper line capture, run by hand (`python -m props.calc capture`; no
workflow runs it). Saves the current two-sided lines for the four markets to
props/calc/lines/<season>/line_archive_<season>.jsonl with props/persist.py's
writer, in the engine's row format with snapshot_type "calc". Not into
props/record: only the props workflow commits there (scripts/
check_commit_hygiene.py refuses a PR that mixes it with code).

parse() works out, per player-market: the line, both payout multipliers, who
he is (Sleeper id -> gsis id by ID, a name+team fallback only when the ID join
fails, every miss logged) and which nflverse game it is for (his team's next
game on the schedule). archive_rows() turns each matched one into an Over row
and an Under row; unmatched ones are logged as misses and not saved."""

from __future__ import annotations

import datetime as dt
import json
import re
from pathlib import Path

import pandas as pd

from core import fetch as F
from core.manifest import Manifest

from . import checks, data, names, odds
from .shared import persist
from .markets import ARCHIVE_MARKET, SLEEPER_WAGER

CALC = Path(__file__).resolve().parent
SNAPSHOT = "calc"            # the engine's rows are "decision"; persist's key keeps the two apart
TO_ARCHIVE = {v: k for k, v in ARCHIVE_MARKET.items()}
MISSES_PATH = CALC / "log" / "name_misses.jsonl"


def _sleeper_number(x):
    """Sleeper sends some numbers as text (payout_multiplier "1.80"; checked
    on the live board 2026-10-10). Numeric text becomes a number here, where
    that format is known; anything else is left for checks to refuse."""
    if isinstance(x, str):
        try:
            return float(x)
        except ValueError:
            return x
    return x


def _miss(stamp: str, r: dict, reason: str) -> dict:
    return {"logged_at_utc": stamp, "source": "sleeper_capture", "sleeper_id": r["sleeper_id"],
            "name": r["name"], "team": r["team"], "market": r["market"], "reason": reason}


def _now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def _player_name(info: dict) -> str:
    return info.get("full_name") or f'{info.get("first_name", "")} {info.get("last_name", "")}'.strip()


def parse(raw: list, players: dict, sleeper_gsis: dict, candidates: list[dict],
          games: pd.DataFrame, captured_at: dt.datetime,
          aside: pd.DataFrame | None = None) -> tuple[list[dict], list[dict]]:
    """(rows, misses) from Sleeper's lines payload. Kept: NFL, normal lines,
    pre-game, both sides active, one of the four markets, not a QB's rushing.
    `games`: schedule rows (game_id, season, week, home_team, away_team,
    kickoff_utc) used to attach his team's next game.

    A row is matched only when the player resolves to a gsis id, that player's
    roster team (from `candidates`) is the team Sleeper names, and the team has
    a game still to play. Otherwise gsis_id is None and the miss is logged."""
    roster_team = {c["gsis_id"]: names.team_code(c["team"]) for c in candidates if isinstance(c.get("team"), str)}
    rows, misses = [], []
    stamp = captured_at.astimezone(dt.timezone.utc).isoformat(timespec="seconds")
    for m in raw or []:
        market = SLEEPER_WAGER.get(m.get("wager_type"))
        if m.get("sport") != "nfl" or market is None or m.get("line_type", "normal") != "normal":
            continue
        opts = m.get("options") or []
        if not opts or opts[0].get("game_status") != "pre_game":
            continue
        over = next((o for o in opts if o.get("outcome") == "over" and o.get("status") == "active"), None)
        under = next((o for o in opts if o.get("outcome") == "under" and o.get("status") == "active"), None)
        sid = str(m.get("subject_id") or "")
        info = players.get(sid) or {}
        if market == "rush_yds" and info.get("position") == "QB":
            continue                      # QB rushing is not a market here (design note)
        pos = info.get("position")
        name = _player_name(info)
        team = names.team_code(opts[0].get("subject_team") or info.get("team"))
        skip = None
        if over is None or under is None:
            skip = "skipped: one side not offered"
        else:
            try:                          # the same rules the read side applies (checks.py)
                lo = checks.line_value(_sleeper_number(over.get("outcome_value")), "the Over line")
                lu = checks.line_value(_sleeper_number(under.get("outcome_value")), "the Under line")
                mo = checks.multiplier(_sleeper_number(over.get("payout_multiplier")), "the Over multiplier")
                mu = checks.multiplier(_sleeper_number(under.get("payout_multiplier")), "the Under multiplier")
                if lo != lu:
                    skip = "skipped: the two sides are quoted at different lines"
            except checks.DataError as ex:
                skip = f"skipped: {ex}"
        if skip:                          # recorded, so an unmatched card can be traced to Sleeper's side
            misses.append(_miss(stamp, {"sleeper_id": sid, "name": name, "team": team, "market": market}, skip))
            continue
        gsis, how = sleeper_gsis.get(sid), "sleeper_id"
        if not gsis and str(info.get("gsis_id") or "").strip():
            gsis, how = str(info["gsis_id"]).strip(), "sleeper_table_gsis"
        if not gsis and aside is not None and data.set_aside_namesake(aside, name, teams=[team]):
            how = f"miss: {name} is listed on two teams in the same week; the roster cannot say which"
        elif not gsis:
            gsis, how = names.match(name, team, candidates)
        game = next_game(games, team, captured_at)
        if gsis and roster_team.get(gsis) != team:
            gsis, how = None, f"miss: Sleeper says {team}, the roster says {roster_team.get(gsis) or 'not rostered'}"
        if gsis and game is None:
            gsis, how = None, f"miss: no game still to play for {team}"
        if gsis and not sleeper_game_agrees(m.get("game_id"), game):
            gsis, how = None, f"miss: Sleeper game {m.get('game_id')} is not week {game['week']} of {game['season']}"
        if not gsis:
            misses.append(_miss(stamp, {"sleeper_id": sid, "name": name, "team": team, "market": market}, how))
        rows.append({
            "captured_at_utc": stamp, "sleeper_id": sid, "gsis_id": gsis, "matched_by": how if gsis else None,
            "name": name, "team": team, "position": pos, "market": market,
            "line": lo, "mult_over": mo, "mult_under": mu,
            "sleeper_game_id": m.get("game_id"), "updated_at_ms": int(m.get("updated_at") or 0),
            **(game or {"game_id": None, "season": None, "week": None, "kickoff_utc": None}),
        })
    # every row Sleeper puts in one game must land in one nflverse game: rows
    # that disagree with a strict majority are unmatched (all of them, if no
    # nflverse game holds a strict majority)
    best = game_majority(rows)        # decided once, before any row changes
    for r in rows:
        if r["gsis_id"] and r["game_id"] != best.get(r["sleeper_game_id"]):
            misses.append(_miss(stamp, r, f"miss: Sleeper game {r['sleeper_game_id']} spans several nflverse games"))
            r["gsis_id"], r["matched_by"] = None, None
    return rows, misses


def game_teams(game_id: str) -> set:
    """nflverse game ids read <season>_<week>_<away>_<home>."""
    return set(str(game_id).split("_")[2:])


def game_majority(rows: list[dict]) -> dict:
    """Sleeper game id -> the nflverse game its matched rows belong to: the game
    covering the most of the distinct teams Sleeper put in it, then the most
    distinct players (never rows, so one player's several markets cannot
    outvote the others). Absent when two games tie on both."""
    teams: dict = {}
    players: dict = {}
    for r in rows:
        if r.get("gsis_id") and r.get("game_id"):
            teams.setdefault(r["sleeper_game_id"], set()).add(r["team"])
            players.setdefault((r["sleeper_game_id"], r["game_id"]), set()).add(r["gsis_id"])
    out = {}
    for sg in teams:
        gs = [g for (s, g) in players if s == sg]
        score = sorted(((len(teams[sg] & game_teams(g)), len(players[(sg, g)]), g) for g in gs), reverse=True)
        if len(score) == 1 or score[0][:2] > score[1][:2]:
            out[sg] = score[0][2]
    return out


SLEEPER_GAME_ID = re.compile(r"^(\d{4})1(\d{2})\d{2}$")     # season, 1 = regular season, week, game


def sleeper_game_agrees(sleeper_game_id, game: dict | None) -> bool:
    """Sleeper's regular-season game ids read <season>1<week><game> (checked on
    the 2026 week-5 board: 14 ids, each one nflverse game of that week). The
    row's game must have that season and week; an id in another form fails."""
    m = SLEEPER_GAME_ID.match(str(sleeper_game_id or ""))
    return bool(m and game and int(m.group(1)) == game["season"] and int(m.group(2)) == game["week"])


def next_game(games: pd.DataFrame, team: str, at: dt.datetime) -> dict | None:
    """His team's first scheduled game kicking off after `at`."""
    if not team or games is None or games.empty:
        return None
    g = games[((games["home_team"] == team) | (games["away_team"] == team)) & games["kickoff_utc"].notna()]
    g = g[pd.to_datetime(g["kickoff_utc"], utc=True) > pd.Timestamp(at)]
    if g.empty:
        return None
    r = g.sort_values("kickoff_utc").iloc[0]
    return {"game_id": r["game_id"], "season": int(r["season"]), "week": int(r["week"]),
            "kickoff_utc": r["kickoff_utc"]}


def append_jsonl(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, sort_keys=True) + "\n")


def archive_rows(rows: list[dict]) -> list[dict]:
    """parse()'s matched rows in the line history's format: one row per side,
    with the engine's fields (persist.LINE_KEY plus commence_time, the full team
    names and retrieved_at_utc, which journal.late_line reads) and calc's own
    (gsis_id, the nflverse game_id, team, the exact multiplier)."""
    out = []
    for r in rows:
        if not r["gsis_id"]:
            continue                       # unmatched: a logged miss, never a saved line
        teams = str(r["game_id"]).split("_")[2:]
        checks.require(len(teams) == 2, f"game id {r['game_id']!r} does not name two teams")
        away, home = (names.TEAM_NAMES.get(t) for t in teams)
        checks.require(away and home, f"game id {r['game_id']!r} names a team with no full name")
        at = checks.utc(r["captured_at_utc"], "the capture time")
        ko = checks.utc(r["kickoff_utc"], "the kickoff time")
        base = {"season": r["season"], "week": r["week"], "event_id": f"sleeper_{r['sleeper_game_id']}",
                "bookmaker": "sleeper", "market": TO_ARCHIVE[r["market"]], "player": r["name"],
                "point": r["line"], "snapshot_type": SNAPSHOT, "source": "props.calc capture",
                "commence_time": ko.isoformat(), "home_team": home, "away_team": away,
                "retrieved_at_utc": at.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "gsis_id": r["gsis_id"], "sleeper_id": r["sleeper_id"], "matched_by": r["matched_by"],
                "team": r["team"], "position": r["position"], "game_id": r["game_id"],
                "updated_at_ms": r["updated_at_ms"]}
        for side, mult in (("Over", r["mult_over"]), ("Under", r["mult_under"])):
            out.append({**base, "outcome": side, "multiplier": mult,
                        "price_american": odds.american_from_multiplier(mult)})
    return out


def run(*, misses_path: Path | None = None) -> dict:
    """Fetch, parse and save. Refuses to write when Sleeper could not be
    refreshed: an old copy must never be saved as a new capture."""
    man = Manifest("props.calc capture")
    path = F.sleeper_lines(manifest=man, max_age_s=60)
    entry = man.get("sleeper lines")
    if entry["status"] not in ("fresh", "cached"):
        raise checks.DataError(f"Sleeper lines not refreshed ({entry['status']}: {entry['detail']}); nothing captured")
    captured_at = dt.datetime.fromisoformat(entry["fetched_at_utc"])
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    players = json.loads(F.sleeper_players(manifest=man).read_text(encoding="utf-8"))
    season = F.current_season()
    roster = data.rosters(season, manifest=man)
    games = data.schedule(manifest=man)
    listed, aside = data.roster_split(roster, season, skill_only=True)
    rows, misses = parse(raw, players, data.sleeper_to_gsis(roster), data.candidates(listed),
                         games, captured_at, aside=aside)
    saved = archive_rows(rows)
    by_season: dict = {}
    for r in saved:
        by_season.setdefault(r["season"], []).append(r)
    from .lines import calc_path         # here, not at the top: lines imports this module
    written = {s: persist.append_jsonl(calc_path(s), rs, persist.LINE_KEY) for s, rs in by_season.items()}
    append_jsonl(misses_path or MISSES_PATH, misses)
    skipped = sum(m["reason"].startswith("skipped") for m in misses)
    stale = [f"{e['name']} ({e['status']})" for e in man.stale() if e["name"] != "sleeper lines"]
    return {"paths": [str(calc_path(s)) for s in written], "rows": len(saved), "sides": len(saved),
            "lines": len(saved) // 2, "added": sum(w["added"] for w in written.values()),
            "replaced": sum(w["replaced"] for w in written.values()), "misses": len(misses) - skipped,
            "skipped": skipped, "captured_at_utc": entry["fetched_at_utc"], "stale": stale}


def summary_line(r: dict) -> str:
    """The capture's one-line report. A line is saved as two sides (Over and Under), and the
    archive counts each side as new or updated, so the counts are given in sides: they add up
    (DECISIONS #235; the chat test printed "Saved 368 lines (736 new, 0 updated)")."""
    return (f"Saved {r['lines']} lines ({r['sides']} sides: {r['added']} new, {r['replaced']} updated) captured at "
            f"{r['captured_at_utc']} to {', '.join(r['paths']) or 'nowhere (none matched)'}.")
