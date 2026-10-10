"""Standalone Sleeper line capture: saves the current two-sided lines for the
four markets to props/calc/lines/<season>/lines_<season>.jsonl. Run by hand
(`python -m props.calc capture`); no workflow runs it.

Each row is one player-market at one moment: the line, both payout
multipliers, who he is (Sleeper id -> gsis id by ID, a name+team fallback
only when the ID join fails, every miss logged) and which nflverse game it
is for (his team's next game on the schedule)."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import pandas as pd

from core import fetch as F
from core.manifest import Manifest

from . import data, names
from .markets import SLEEPER_WAGER

CALC = Path(__file__).resolve().parent
LINES_ROOT = CALC / "lines"
MISSES_PATH = CALC / "log" / "name_misses.jsonl"


def _now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def _player_name(info: dict) -> str:
    return info.get("full_name") or f'{info.get("first_name", "")} {info.get("last_name", "")}'.strip()


def parse(raw: list, players: dict, sleeper_gsis: dict, candidates: list[dict],
          games: pd.DataFrame, captured_at: dt.datetime) -> tuple[list[dict], list[dict]]:
    """(rows, misses) from Sleeper's lines payload. Kept: NFL, normal lines,
    pre-game, both sides active, one of the four markets, not a QB's rushing.
    `games`: schedule rows (game_id, season, week, home_team, away_team,
    kickoff_utc) used to attach his team's next game."""
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
        if over is None or under is None or float(over["outcome_value"]) != float(under["outcome_value"]):
            continue                      # one-sided, or the two sides quoted at different lines
        sid = str(m.get("subject_id") or "")
        info = players.get(sid) or {}
        pos = info.get("position")
        if market == "rush_yds" and pos == "QB":
            continue
        name = _player_name(info)
        team = names.team_code(opts[0].get("subject_team") or info.get("team"))
        gsis, how = sleeper_gsis.get(sid), "sleeper_id"
        if not gsis and str(info.get("gsis_id") or "").strip():
            gsis, how = str(info["gsis_id"]).strip(), "sleeper_table_gsis"
        if not gsis:
            gsis, how = names.match(name, team, candidates)
        if not gsis:
            misses.append({"logged_at_utc": stamp, "source": "sleeper_capture", "sleeper_id": sid,
                           "name": name, "team": team, "market": market, "reason": how})
        game = next_game(games, team, captured_at)
        rows.append({
            "captured_at_utc": stamp, "sleeper_id": sid, "gsis_id": gsis, "matched_by": how if gsis else None,
            "name": name, "team": team, "position": pos, "market": market,
            "line": float(over["outcome_value"]),
            "mult_over": float(over["payout_multiplier"]), "mult_under": float(under["payout_multiplier"]),
            "sleeper_game_id": m.get("game_id"), "updated_at_ms": int(m.get("updated_at") or 0),
            **(game or {"game_id": None, "season": None, "week": None, "kickoff_utc": None}),
        })
    return rows, misses


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


def run(*, lines_root: Path = LINES_ROOT, misses_path: Path = MISSES_PATH) -> dict:
    """Fetch, parse and append. Refuses to write when Sleeper could not be
    refreshed: an old copy must never be saved as a new capture."""
    man = Manifest("props.calc capture")
    path = F.sleeper_lines(manifest=man, max_age_s=60)
    entry = man.get("sleeper lines")
    if entry["status"] not in ("fresh", "cached"):
        raise RuntimeError(f"Sleeper lines not refreshed ({entry['status']}: {entry['detail']}); nothing captured")
    captured_at = dt.datetime.fromisoformat(entry["fetched_at_utc"])
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    players = json.loads(F.sleeper_players(manifest=man).read_text(encoding="utf-8"))
    season = F.current_season()
    roster = data.rosters(season, manifest=man)
    games = data.schedule(manifest=man)
    rows, misses = parse(raw, players, data.sleeper_to_gsis(roster), data.roster_candidates(roster, season),
                         games, captured_at)
    out = lines_root / str(season) / f"lines_{season}.jsonl"
    append_jsonl(out, rows)
    append_jsonl(misses_path, misses)
    return {"path": str(out), "rows": len(rows), "misses": len(misses), "captured_at_utc": entry["fetched_at_utc"]}


def read_captures(season: int, *, lines_root: Path = LINES_ROOT) -> list[dict]:
    p = lines_root / str(season) / f"lines_{season}.jsonl"
    if not p.exists():
        return []
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]
