"""The leg log: props/calc/log/legs.jsonl, append only.

A "leg" row is written when the user logs a leg from a card: the line, both
prices, "book expects", the workload needed, his usual workload and the gap.
A "settle" row is appended after the game with the workload he actually got,
the result, and the line near kickoff. Rows are never edited; reading merges
each leg with its latest settle row.
"""

from __future__ import annotations

import datetime as dt
import json
import uuid
from pathlib import Path

import pandas as pd

from . import names
from .capture import append_jsonl, read_captures
from .markets import ARCHIVE_MARKET, stat_col, workload_col

CALC = Path(__file__).resolve().parent
LOG_PATH = CALC / "log" / "legs.jsonl"
ARCHIVE_ROOT = CALC.parent / "record" / "lines"      # the engine workflow's saved lines; read only

LEG_FIELDS = ("season", "week", "game_id", "kickoff_utc", "player", "gsis_id", "team", "market", "side",
              "line", "mult_over", "mult_under", "target_rate", "book_expects", "needed", "usual", "gap")


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def log_leg(leg: dict, *, path: Path = LOG_PATH, now: str | None = None) -> dict:
    missing = [f for f in LEG_FIELDS if f not in leg]
    if missing:
        raise ValueError(f"a leg needs {missing}")
    if leg["side"] not in ("over", "under"):
        raise ValueError("side is over or under")
    row = {"kind": "leg", "id": uuid.uuid4().hex[:12], "logged_at_utc": now or _now(), **leg}
    append_jsonl(path, [row])
    return row


def read(path: Path = LOG_PATH) -> list[dict]:
    """Legs, each merged with its latest settle row (if any)."""
    if not path.exists():
        return []
    legs, settles = {}, {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        if r["kind"] == "leg":
            legs[r["id"]] = r
        elif r["kind"] == "settle":
            settles[r["id"]] = r
    return [{**leg, **{k: v for k, v in settles.get(i, {}).items() if k not in ("kind", "id")}}
            for i, leg in legs.items()]


def result(side: str, line: float, actual: float | None) -> str:
    if actual is None:
        return "no stats"
    if actual == line:
        return "push"
    return "won" if (actual > line) == (side == "over") else "lost"


def settle_row(leg: dict, games: pd.DataFrame, kickoff_line: dict | None, now: str | None = None) -> dict:
    """The settle row for one leg from that week's player-game table."""
    g = games[(games["season"] == leg["season"]) & (games["week"] == leg["week"])
              & (games["gsis_id"] == leg["gsis_id"])]
    actual_w = int(g[workload_col(leg["market"])].sum()) if len(g) else None
    actual = float(g[stat_col(leg["market"])].sum()) if len(g) else None
    return {"kind": "settle", "id": leg["id"], "settled_at_utc": now or _now(),
            "actual_workload": actual_w, "actual": actual,
            "result": result(leg["side"], float(leg["line"]), actual),
            "kickoff_line": kickoff_line}


def line_near_kickoff(leg: dict, *, lines_root: Path | None = None, archive_root: Path = ARCHIVE_ROOT) -> dict | None:
    """The last quote before kickoff: the user's own captures first (joined by
    gsis id), else the engine workflow's archive (joined by name AND the game's
    kickoff time, never by name alone)."""
    ko = leg.get("kickoff_utc")
    if not ko:
        return None
    ko_t = pd.Timestamp(ko)
    caps = read_captures(int(leg["season"]), **({"lines_root": lines_root} if lines_root else {}))
    mine = [c for c in caps if c.get("gsis_id") == leg["gsis_id"] and c.get("market") == leg["market"]
            and c.get("game_id") == leg["game_id"] and pd.Timestamp(c["captured_at_utc"]) < ko_t]
    if mine:
        c = max(mine, key=lambda c: c["captured_at_utc"])
        return {"source": "own capture", "at_utc": c["captured_at_utc"], "line": c["line"],
                "mult_over": c["mult_over"], "mult_under": c["mult_under"]}
    arch = archive_root / str(leg["season"]) / f"line_archive_{leg['season']}.jsonl"
    if not arch.exists():
        return None
    key = names.norm(leg["player"])
    best: dict[str, dict] = {}
    with open(arch, encoding="utf-8") as fh:
        for line in fh:
            r = json.loads(line)
            if (r.get("bookmaker") != "sleeper" or ARCHIVE_MARKET.get(r.get("market")) != leg["market"]
                    or names.norm(r.get("player", "")) != key):
                continue
            try:
                same_game = pd.Timestamp(r["commence_time"]) == ko_t
                early = pd.Timestamp(r["retrieved_at_utc"]) < ko_t
            except (KeyError, ValueError):
                continue
            if same_game and early:
                best.setdefault(r["retrieved_at_utc"], {})[r["outcome"]] = r
    for at in sorted(best, reverse=True):
        pair = best[at]
        if "Over" in pair and "Under" in pair and pair["Over"]["point"] == pair["Under"]["point"]:
            return {"source": "engine archive", "at_utc": at, "line": float(pair["Over"]["point"]),
                    "american_over": pair["Over"]["price_american"],
                    "american_under": pair["Under"]["price_american"]}
    return None


def settle(season: int, player_games: pd.DataFrame, *, path: Path = LOG_PATH, **kw) -> int:
    """Append a settle row for every unsettled leg of `season` whose week is in
    `player_games`. Returns how many were settled."""
    done_weeks = set(zip(player_games["season"], player_games["week"]))
    rows = []
    for leg in read(path):
        if leg.get("result") or leg["season"] != season or (leg["season"], leg["week"]) not in done_weeks:
            continue
        rows.append(settle_row(leg, player_games, line_near_kickoff(leg, **kw)))
    append_jsonl(path, rows)
    return len(rows)


def gap_group(gap: float, edges: list[float]) -> str:
    lo = None
    for e in edges:
        if gap <= e:
            return f"{e} or less" if lo is None else f"{lo} to {e}"
        lo = e
    return f"more than {edges[-1]}"


def summary(season: int, edges: list[float], *, path: Path = LOG_PATH) -> list[dict]:
    """Settled legs (won or lost) grouped by market and gap: how many, how many
    won, the average break-even of the side played, needed vs actual workload."""
    legs = [x for x in read(path) if x["season"] == season and x.get("result") in ("won", "lost")]
    groups: dict[tuple, list] = {}
    for x in legs:
        groups.setdefault((x["market"], gap_group(float(x["gap"]), edges)), []).append(x)
    out = []
    for (market, grp), xs in sorted(groups.items()):
        be = [1 / (x["mult_over"] if x["side"] == "over" else x["mult_under"]) for x in xs]
        out.append({"market": market, "gap": grp, "legs": len(xs),
                    "won": sum(x["result"] == "won" for x in xs),
                    "break_even": sum(be) / len(be),
                    "needed": sum(float(x["needed"]) for x in xs) / len(xs),
                    "actual": sum(float(x["actual_workload"]) for x in xs) / len(xs)})
    return out
