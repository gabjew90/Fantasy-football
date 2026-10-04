"""Sleeper against the sharper books: one DraftKings/FanDuel snapshot per game.

The props engine prices from Sleeper Picks, which posts fixed prices on lines
that can lag the bigger books. Whether that lag is an edge does not depend on
the model at all: when Sleeper's line sits off the DraftKings/FanDuel consensus,
does the side the consensus favours, bet at Sleeper's price, beat break-even?
(DECISIONS #147; the reading rule is in reports/sleeper_vs_books.md.)

This file captures the evidence. Run after each props capture (props.yml):

    python props/compare.py --season 2026 --week 4 --engine-dir "$ENGINE_DIR"

For every game kicking off within the capture window that has no comparison
yet, it pulls DraftKings and FanDuel player lines once through the engine's own
odds client (the free events call, then ~4 credits a game) and appends them to
props/record/compare/<season>/wk<NN>.jsonl. It stops at COMPARE_QUOTA_MIN
remaining credits, needs ODDS_API_KEY (or the engine's key file), and any
failure is a printed reason and exit 0: a comparison must never cost a capture.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import persist  # noqa: E402

COMPARE_QUOTA_MIN = 100
WINDOW_H = 6.0                      # the capture window: games kicking off within this many hours
BOOKS = "draftkings,fanduel"
MARKETS = "player_receptions,player_reception_yds,player_rush_yds,player_pass_yds"
COMPARE_KEY = ("season", "week", "event_id", "book", "market", "player", "side", "line")


def compare_path(season: int, week: int) -> Path:
    return persist.RECORD_ROOT / "compare" / str(season) / f"wk{week:02d}.jsonl"


def compared_events(season: int, week: int) -> set[str]:
    p = compare_path(season, week)
    if not p.exists():
        return set()
    with p.open(encoding="utf-8") as fh:
        return {json.loads(ln)["event_id"] for ln in fh if ln.strip()}


def odds(engine_dir: Path, stage: str, *args: str) -> dict:
    """The engine's odds client, run from its scripts directory (its cache is
    relative). Raises with the client's own reason; it never prints the key."""
    scripts = engine_dir / "scripts"
    r = subprocess.run([sys.executable, str(scripts / "odds_client.py"), stage, *args],
                       capture_output=True, text=True, cwd=str(scripts), timeout=120)
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        raise RuntimeError((r.stdout.strip() or r.stderr.strip())[-300:] or f"exit {r.returncode}")


def rows_from(data: dict, season: int, week: int, retrieved: str) -> list[dict]:
    """One row per book / market / player / side from an Odds API event payload."""
    out = []
    for b in data.get("bookmakers", []):
        for m in b.get("markets", []):
            for o in m.get("outcomes", []):
                if o.get("name") not in ("Over", "Under") or o.get("point") is None:
                    continue
                out.append({"season": season, "week": week, "event_id": data["id"],
                            "commence_time": data.get("commence_time"), "home_team": data.get("home_team"),
                            "away_team": data.get("away_team"), "book": b["key"], "market": m["key"],
                            "player": o.get("description"), "side": o["name"], "line": float(o["point"]),
                            "price": int(o["price"]), "last_update": m.get("last_update"),
                            "retrieved_at_utc": retrieved})
    return out


def capture(season: int, week: int, engine_dir: Path, now: dt.datetime | None = None,
            odds_fn=odds) -> dict:
    now = now or dt.datetime.now(dt.timezone.utc)
    counts = {"events_in_window": 0, "compared": 0, "skipped_done": 0, "rows": 0, "stopped": ""}
    key_file = engine_dir / "resources" / "credential.env"
    kf = ["--key-file", str(key_file)] if key_file.exists() else []
    ev = odds_fn(engine_dir, "events", *kf)
    if ev.get("class") != "OK":
        counts["stopped"] = f"events call {ev.get('class')}"
        return counts
    done = compared_events(season, week)
    quota = (ev.get("quota") or {}).get("x-requests-remaining")
    for e in ev.get("events", []):
        ko = dt.datetime.fromisoformat(e["commence_time"].replace("Z", "+00:00"))
        hrs = (ko - now).total_seconds() / 3600
        if not 0 < hrs <= WINDOW_H:
            continue
        counts["events_in_window"] += 1
        if e["id"] in done:
            counts["skipped_done"] += 1
            continue
        if quota is not None and int(float(quota)) < COMPARE_QUOTA_MIN:
            counts["stopped"] = f"{quota} credits left (needs {COMPARE_QUOTA_MIN}+)"
            break
        od = odds_fn(engine_dir, "odds", e["id"], *kf, "--markets", MARKETS, "--books", BOOKS)
        quota = (od.get("quota") or {}).get("x-requests-remaining", quota)
        if od.get("class") != "OK":
            counts["stopped"] = f"odds call {od.get('class')} for {e['away_team']} at {e['home_team']}"
            continue
        cache = engine_dir / "scripts" / "cache"
        files = sorted(cache.glob(f"odds_{e['id']}_*.json"), key=lambda f: f.stat().st_mtime)
        if not files:
            continue
        data = json.loads(files[-1].read_text(encoding="utf-8"))["data"]
        rows = rows_from(data, season, week, od.get("retrieved_at_utc") or now.strftime("%Y-%m-%dT%H:%M:%SZ"))
        if rows:
            persist.append_jsonl(compare_path(season, week), rows, COMPARE_KEY)
            counts["compared"] += 1
            counts["rows"] += len(rows)
    counts["credits_left"] = quota
    return counts


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--season", type=int, required=True)
    ap.add_argument("--week", type=int, required=True)
    ap.add_argument("--engine-dir", default=str(HERE / "engine"))
    args = ap.parse_args(argv)
    try:
        c = capture(args.season, args.week, Path(args.engine_dir))
    except Exception as ex:  # noqa: BLE001 -- never cost a capture
        print(f"compare: skipped ({type(ex).__name__}: {str(ex)[:200]})")
        return 0
    print("compare: " + ", ".join(f"{k} {v}" for k, v in c.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
