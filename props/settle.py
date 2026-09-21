"""Grade recorded prop calls against actual outcomes.

Joins `record/predictions/<season>/wk<NN>.jsonl` to nflverse weekly player
stats and writes one settled row per call to
`record/settled/<season>/settled_<season>.csv`.

Settlement rules, matching how books settle these markets:
  receptions        stat > line -> Over wins; stat < line -> Under wins
  reception_yds     same, on receiving_yards
  rush_yds          same, on rushing_yards
  anytime_td        rushing_tds + receiving_tds >= 1 -> Yes wins
A half-point line cannot push. A whole-number line that lands exactly on the
stat is recorded as `push` and excluded from hit-rate denominators.

A call is only settled when the player appears in that week's stat file. A
player who did not play settles as `dnp` rather than as a loss, because a
book would have voided the prop; folding a void into the record as a loss
would bias every hit rate downward.

Name joining: nflverse `player_id` is not present on Sleeper rows, so the join
is on a normalized name within (season, week, team), with a first-initial +
surname fallback. Unjoined rows are written with status `unjoined` and counted
in the run summary rather than dropped, since a silent drop is the failure mode
that would quietly shrink the record.

Usage:
    python props/settle.py --season 2026 [--week 2] [--through-week 5]
"""

from __future__ import annotations

import argparse
import csv
import os
import json
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import calls as calls_mod  # noqa: E402
import persist  # noqa: E402

try:
    import pandas as pd
except ImportError:  # pragma: no cover
    print("pandas is required: pip install -r props/requirements.txt", file=sys.stderr)
    raise

NFLVERSE = "https://github.com/nflverse/nflverse-data/releases/download"
STATS_URL = NFLVERSE + "/stats_player/stats_player_week_{season}.csv"

SUFFIX = re.compile(r"\s+(jr|sr|ii|iii|iv|v)\.?$", re.IGNORECASE)

MARKET_STAT = {
    "player_receptions": "receptions",
    "player_reception_yds": "receiving_yards",
    "player_rush_yds": "rushing_yards",
    "player_anytime_td": "_anytime_td",
    "receptions": "receptions",
    "reception_yds": "receiving_yards",
    "rush_yds": "rushing_yards",
    "anytime_td": "_anytime_td",
}

SETTLED_FIELDS = [
    "season", "week", "game", "event_id", "book", "market", "player", "team",
    "slot", "side", "line", "price", "p_model", "p_novig", "gap", "tier",
    "decision", "new_team", "questionable", "questionable_teammate", "model_state",
    # Which anytime-TD model priced the row: anytime_td_v1, or the labelled v0
    # fallback when v1 could not run. Same engine hash, different model -- so
    # it has to survive into the settled file or the two would be graded as one.
    "td_model",
    # The engine that made the call. These must be listed here or the
    # DictWriter's extrasaction="ignore" below drops them silently, and the
    # scorecard could not separate two versions.
    "engine_hash", "engine_tag", "engine_source",
    "snapshot_type", "is_call",
    "logged_at_utc", "commence_time", "minutes_to_kickoff",
    "actual", "result", "status", "won", "pnl_per_100",
    # WHY IT MISSED, not just whether it did. A losing call has two very
    # different causes and the record has to tell them apart: the player's
    # ROLE was smaller than the model assumed (targets, carries,
    # target_share, air_yards_share, wopr), or the role was right and the
    # GAME did not cooperate (opponent, the two scores). `miss` is the
    # signed distance from the projection the call was built on, so a
    # systematic bias reads as a column of same-signed numbers rather than
    # as a feeling. All of it comes from the weekly stats settle already
    # downloads plus the schedule the guard already caches.
    "miss", "targets", "carries", "target_share", "air_yards_share", "wopr",
    "opponent", "team_points", "opp_points", "game_total",
    "join_method",
]

# nflverse weekly columns worth keeping beside a graded call, and the name
# each takes in the record. A column the release drops is simply absent;
# settling never fails over a diagnostic.
DIAGNOSTIC_STATS = {
    "targets": "targets",
    "carries": "carries",
    "target_share": "target_share",
    "air_yards_share": "air_yards_share",
    "wopr": "wopr",
    "opponent_team": "opponent",
}

# A settled row's identity. The engine belongs in it for the same reason it
# belongs in persist.PREDICTION_KEY: two versions' grades must not collapse
# into one another.
SETTLED_KEY = ("season", "week", "event_id", "book", "market", "player",
               "side", "line", "engine_hash")


def settled_key(row: dict) -> tuple[str, ...]:
    """The key, with None and "" the same thing.

    THIS FIXES A LATENT DUPLICATION BUG. The key used to be built with
    `str(r.get("line"))`, which is "None" for a row written in this process
    and "" for the same row read back from the CSV -- so the eight
    anytime-TD rows (no line) keyed differently on write and on read, and
    the first re-settle of a week would have duplicated every one of them.
    Settle has never run, so it never bit.
    """
    return tuple("" if row.get(f) is None else str(row.get(f, ""))
                 for f in SETTLED_KEY)


def norm_name(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower().replace(".", "").replace("'", "").replace("-", " ")
    s = SUFFIX.sub("", s.strip())
    return re.sub(r"\s+", " ", s).strip()


def loose_key(s: str) -> str:
    """First initial + surname.

    nflverse `player_name` is abbreviated (`C.McCaffrey`) while the record
    stores the book's full name (`Christian McCaffrey`). Normalising the dot to
    a space first makes both collapse to `c mccaffrey`, which is what lets the
    two sides join at all. This is deliberately lossy: two players on one team
    sharing an initial and surname would collide, so it is only ever a fallback
    after the full-name match.
    """
    n = norm_name(str(s).replace(".", ". ")).strip()
    parts = n.split()
    return f"{parts[0][0]} {parts[-1]}" if len(parts) >= 2 else n


def american_pnl(price: float, won: bool) -> float:
    """Profit per $100 staked."""
    if won is None:
        return 0.0
    if not won:
        return -100.0
    return price if price > 0 else 10000.0 / abs(price)


def load_stats(season: int, cache: Path) -> pd.DataFrame:
    cache.parent.mkdir(parents=True, exist_ok=True)
    if not cache.exists():
        import urllib.request
        urllib.request.urlretrieve(STATS_URL.format(season=season), cache)
    df = pd.read_csv(cache, low_memory=False)
    df = df[df["season_type"] == "REG"].copy()
    for col in ("receptions", "receiving_yards", "rushing_yards",
                "receiving_tds", "rushing_tds"):
        if col not in df.columns:
            df[col] = 0
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    df["_anytime_td"] = (df["rushing_tds"] + df["receiving_tds"] >= 1).astype(int)
    # `player_display_name` carries the full name and is what the book's name
    # can match exactly; `player_name` is abbreviated and only ever usable
    # through the loose key.
    full = df["player_display_name"] if "player_display_name" in df.columns \
        else df["player_name"]
    df["_name"] = full.map(norm_name)
    df["_loose"] = df["player_name"].map(loose_key)
    return df


def game_context(season: int) -> dict[tuple[int, str], dict]:
    """(week, team) -> {team_points, opp_points, game_total} for played games.

    Read through the guard, so this shares the schedule cache the capture
    path already keeps rather than introducing a second copy. Without it a
    losing Under cannot be told apart from a shootout no model would have
    caught, which is the first thing worth knowing about a bad week.
    """
    try:
        import guard
        games = guard.load_games(season)
    except Exception as exc:  # noqa: BLE001 -- context is a bonus, not a gate
        print(f"game context unavailable ({exc.__class__.__name__}); settling "
              f"without it", file=sys.stderr)
        return {}
    out: dict[tuple[int, str], dict] = {}
    for g in games:
        try:
            week = int(g["week"])
            home, away = g["home_team"], g["away_team"]
            hs, as_ = g.get("home_score"), g.get("away_score")
            if hs in (None, "") or as_ in (None, ""):
                continue  # not played yet
            hs, as_ = float(hs), float(as_)
        except (KeyError, TypeError, ValueError):
            continue
        total = hs + as_
        out[(week, home)] = {"team_points": hs, "opp_points": as_,
                             "game_total": total}
        out[(week, away)] = {"team_points": as_, "opp_points": hs,
                             "game_total": total}
    return out


def settle_row(row: dict, actual: float) -> tuple[str, bool | None]:
    """Return (result, won) for a call given the actual stat."""
    market = MARKET_STAT.get(str(row.get("market", "")).strip())
    side = str(row.get("side", "")).strip().lower()
    if market == "_anytime_td":
        scored = actual >= 1
        won = scored if side in ("yes", "over") else not scored
        return ("yes" if scored else "no"), won
    line = row.get("line")
    if line is None:
        return "no_line", None
    if actual == line:
        return "push", None
    over = actual > line
    won = over if side == "over" else not over
    return ("over" if over else "under"), won


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--season", type=int, required=True)
    ap.add_argument("--week", type=int, help="settle only this week")
    ap.add_argument("--through-week", type=int,
                    help="settle every week up to and including this one")
    ap.add_argument("--snapshot-type", default="decision",
                    help="which snapshot to grade (default: decision)")
    args = ap.parse_args(argv)

    pred_dir = persist.RECORD_ROOT / "predictions" / str(args.season)
    if not pred_dir.is_dir():
        print(f"no predictions recorded for {args.season}", file=sys.stderr)
        return 2

    weeks = []
    for f in sorted(pred_dir.glob("wk*.jsonl")):
        w = int(f.stem[2:])
        if args.week and w != args.week:
            continue
        if args.through_week and w > args.through_week:
            continue
        weeks.append((w, f))
    if not weeks:
        print("no matching weeks", file=sys.stderr)
        return 2

    # The nflverse stats file is a cacheable INPUT, so it belongs in the
    # workdir the props cache keeps, not in a hard-coded /tmp -- which exists
    # on the Ubuntu runner but resolves to C:\tmp when settle is run by hand
    # on the machine that holds the credentials.
    stats = load_stats(args.season,
                       persist.RECORD_ROOT.parent / ".cache"
                       / f"stats_player_week_{args.season}.csv")

    context = game_context(args.season)

    out_rows, counts = [], {"settled": 0, "push": 0, "dnp": 0,
                            "unjoined": 0, "unplayed_week": 0,
                            "calls": 0, "superseded": 0, "ties": 0}

    for week, path in weeks:
        wk_stats = stats[stats["week"] == week]
        if wk_stats.empty:
            with path.open(encoding="utf-8") as fh:
                counts["unplayed_week"] += sum(1 for line in fh if line.strip())
            print(f"week {week}: no results published yet, skipped")
            continue
        exact = {(r["team"], r["_name"]): r for _, r in wk_stats.iterrows()}
        loose = {(r["team"], r["_loose"]): r for _, r in wk_stats.iterrows()}
        name_only = {r["_name"]: r for _, r in wk_stats.iterrows()}

        # EVERY ROW IS GRADED; ONE PER MARKET IS A CALL. The whole week has
        # to be in hand before `is_call` can be decided, because the call is
        # the LAST decision for a market and a later tick supersedes an
        # earlier one. History is still graded -- a superseded line beside the
        # one that replaced it is what makes the CSV self-explaining -- but
        # the scorecard counts only calls.
        with path.open(encoding="utf-8") as fh:
            week_rows = [json.loads(line) for line in fh if line.strip()]
        n_calls, n_ties = calls_mod.mark_calls(week_rows, args.snapshot_type)
        counts["calls"] += n_calls
        counts["ties"] += n_ties

        for row in week_rows:
            if row.get("snapshot_type") != args.snapshot_type:
                continue
            if not row.get("is_call"):
                counts["superseded"] += 1
            team = row.get("team")
            nm = norm_name(row.get("player", ""))
            stat_row, how = None, None
            for key, table, method in (((team, nm), exact, "team+name"),
                                       ((team, loose_key(row.get("player", ""))),
                                        loose, "team+initial"),
                                       (nm, name_only, "name-only")):
                if key in table:
                    stat_row, how = table[key], method
                    break

            out = {f: row.get(f) for f in SETTLED_FIELDS if f in row}
            out["season"], out["week"] = args.season, week
            out["join_method"] = how or ""
            out["is_call"] = int(bool(row.get("is_call")))

            if stat_row is None:
                out.update(actual="", result="", status="dnp", won="",
                           pnl_per_100="")
                # A player on the week's roster who recorded no stat line is
                # a DNP/void; one absent from the file entirely is an
                # unresolved join and is flagged separately.
                out["status"] = "dnp" if nm in name_only else "unjoined"
                counts[out["status"]] += 1
                out_rows.append(out)
                continue

            for src_col, dest in DIAGNOSTIC_STATS.items():
                if src_col in stat_row:
                    value = stat_row[src_col]
                    out[dest] = None if pd.isna(value) else value
            out.update(context.get((week, str(row.get("team") or "")), {}))

            stat_col = MARKET_STAT.get(str(row.get("market", "")).strip())
            if stat_col is None:
                out.update(actual="", result="unknown_market", status="skipped",
                           won="", pnl_per_100="")
                out_rows.append(out)
                continue

            actual = float(stat_row[stat_col])
            try:
                out["miss"] = round(actual - float(row["model_mean"]), 3)
            except (KeyError, TypeError, ValueError):
                out["miss"] = None
            result, won = settle_row(row, actual)
            out["actual"] = actual
            out["result"] = result
            if won is None:
                out.update(status="push", won="", pnl_per_100=0.0)
                counts["push"] += 1
            else:
                price = row.get("price")
                out.update(status="settled", won=int(won),
                           pnl_per_100=round(american_pnl(float(price), won), 2)
                           if price is not None else "")
                counts["settled"] += 1
            out_rows.append(out)

    if not out_rows:
        print("nothing to settle")
        return 0

    dest = persist.settled_path(args.season)
    dest.parent.mkdir(parents=True, exist_ok=True)
    existing = {}
    if dest.exists():
        with dest.open(encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                existing[settled_key(r)] = r
    for r in out_rows:
        existing[settled_key(r)] = r
    # Atomic for the same reason persist.append_jsonl is: this rewrites the
    # whole settled record, and a process killed mid-write would otherwise be
    # committed truncated.
    tmp = dest.with_name(dest.name + ".tmp")
    with tmp.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=SETTLED_FIELDS, extrasaction="ignore")
        w.writeheader()
        for r in existing.values():
            w.writerow(r)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, dest)

    print(f"[{persist.mode()}] {dest}: {len(existing)} settled rows")
    print("  " + ", ".join(f"{k}={v}" for k, v in counts.items() if v))
    if counts["unjoined"]:
        print("  unjoined rows are kept, not dropped; check the name join "
              "before trusting hit rates for that week.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
