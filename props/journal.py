"""The bet journal: bets the user actually makes from the research board, each
with the four checklist answers, graded by the Tuesday settle run.

The model's record (props/record) says whether the MODEL beats the book. This
says whether the USER's process does: a role or personnel story, checked
against what the line implies, placed at a price. It is kept apart from the
model's record on purpose -- a handicapped bet is not a model call, and
pooling them would describe neither (DECISIONS #142).

    python props/journal.py add "Dalton Schultz" catches under 4.5 -141 --team HOU \\
        --change "targets fell to 12% in the one game Collins played" \\
        --implies "4.5 needs ~6.3 targets; with Collins back he got ~4" \\
        --fails "Collins re-aggravates the injury, or HOU trails and throws 45 times"
    python props/journal.py list [--open]
    python props/journal.py grade --season 2026
    python props/journal.py summary --season 2026

All three checklist answers are required: a bet that cannot state its change,
its implied workload and its failure case is not logged. Stdlib + pandas.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

JOURNAL_ROOT: Path | None = None    # None: beside the record (persist.RECORD_ROOT.parent / "journal")

MARKETS = {
    "catches": "player_receptions", "receptions": "player_receptions", "rec": "player_receptions",
    "rec_yds": "player_reception_yds", "receiving_yards": "player_reception_yds", "rec yds": "player_reception_yds",
    "rush_yds": "player_rush_yds", "rushing_yards": "player_rush_yds", "rush yds": "player_rush_yds",
    "pass_yds": "player_pass_yds", "passing_yards": "player_pass_yds", "pass yds": "player_pass_yds",
    "td": "player_anytime_td", "anytime_td": "player_anytime_td", "anytime td": "player_anytime_td",
}
LABEL = {"player_receptions": "catches", "player_reception_yds": "rec yds", "player_rush_yds": "rush yds",
         "player_pass_yds": "pass yds", "player_anytime_td": "anytime TD"}


def journal_path(season: int) -> Path:
    if JOURNAL_ROOT is not None:
        base = JOURNAL_ROOT
    elif os.environ.get("PROPS_JOURNAL_ROOT"):
        base = Path(os.environ["PROPS_JOURNAL_ROOT"])
    else:
        import persist
        base = persist.RECORD_ROOT.parent / "journal"
    return base / f"{season}.jsonl"


def read(season: int) -> list[dict]:
    p = journal_path(season)
    if not p.exists():
        return []
    with p.open(encoding="utf-8") as fh:
        return [json.loads(ln) for ln in fh if ln.strip()]


def write(season: int, rows: list[dict]) -> None:
    """Atomic rewrite, LF line endings, one sorted-key JSON object per line."""
    p = journal_path(season)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8", newline="\n") as fh:
        for r in rows:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    os.replace(tmp, p)


def current_week(season: int, now: dt.datetime | None = None) -> int:
    """The week whose games are next on the schedule; the calendar when the
    schedule cannot be read."""
    now = now or dt.datetime.now(dt.timezone.utc)
    try:
        import guard
        wk = guard._soonest_week(guard.load_games(season), now)
        if wk:
            return int(wk)
    except Exception:  # noqa: BLE001 -- the calendar is the fallback
        pass
    import guard
    return guard.week_from_calendar(now, season)


def make_entry(player: str, market: str, side: str, line, price: int, *, change: str, implies: str,
               fails: str, team: str | None = None, book: str = "sleeper", stake: float = 1.0,
               season: int, week: int, now: dt.datetime | None = None) -> dict:
    """One journal row, validated. Raises ValueError with a plain reason."""
    mk = MARKETS.get(" ".join(str(market).lower().replace("-", " ").split()), MARKETS.get(str(market).lower()))
    if mk is None:
        raise ValueError(f"unknown market '{market}' (catches, rec_yds, rush_yds, pass_yds, td)")
    side_ = str(side).lower()
    if mk == "player_anytime_td":
        if side_ not in ("yes", "no"):
            raise ValueError("an anytime TD bet is 'yes' or 'no'")
        line = None
    else:
        if side_ not in ("over", "under"):
            raise ValueError("a yardage or catches bet is 'over' or 'under'")
        if line is None or str(line).strip() == "":
            raise ValueError("a yardage or catches bet needs its line, e.g. 4.5")
        line = float(line)
    price = int(price)
    if abs(price) < 100:
        raise ValueError(f"price {price} is not American odds (e.g. -125 or +110)")
    for name, val in (("change", change), ("implies", implies), ("fails", fails)):
        if not str(val or "").strip():
            raise ValueError(f"--{name} is required: a bet that cannot state it is not logged")
    if stake <= 0:
        raise ValueError("stake must be positive (units)")
    now = now or dt.datetime.now(dt.timezone.utc)
    return {"id": uuid.uuid4().hex[:10], "logged_at_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "season": int(season), "week": int(week), "player": player.strip(),
            "team": (team or "").upper() or None, "market": mk, "side": side_, "line": line, "price": price,
            "book": book, "stake": float(stake), "change": change.strip(), "implies": implies.strip(),
            "fails": fails.strip(), "status": "open"}


def grade(season: int, stats=None, now: dt.datetime | None = None) -> dict:
    """Grade every open bet whose week has published stats, with settle's own
    stat file, name join and win/push rules. Returns counts."""
    import settle
    rows = read(season)
    counts = {"graded": 0, "void": 0, "check": 0, "unjoined": 0, "unplayed": 0, "open_left": 0}
    if not any(r.get("status") == "open" for r in rows):
        return counts      # nothing to grade: no download, no file written
    if stats is None:
        stats = settle.load_stats(season, HERE / ".cache")
    now = now or dt.datetime.now(dt.timezone.utc)
    for r in rows:
        if r.get("status") != "open":
            continue
        wk = stats[stats["week"] == int(r["week"])]
        if wk.empty:
            counts["unplayed"] += 1
            continue
        nm = settle.norm_name(r["player"])
        team = r.get("team")
        hit = None
        if team:
            m = wk[(wk["team"] == team) & (wk["_name"] == nm)]
            if m.empty:
                m = wk[(wk["team"] == team) & (wk["_loose"] == settle.loose_key(r["player"]))]
            hit = m.iloc[0] if len(m) else None
        if hit is None:
            m = wk[wk["_name"] == nm]
            hit = m.iloc[0] if len(m) == 1 else None
        if hit is None:
            # Absent from the week's stats. nflverse's weekly file has no row for a
            # player who did not play AND none for one who played and recorded
            # nothing -- the book voids the first and pays the second at 0. Never
            # guess: a known name goes to 'check' for `journal resolve`; an
            # unknown one stays open.
            if (stats["_name"] == nm).any():
                r.update(status="check", result="not in the week's stats: did he play?")
                counts["check"] += 1
            else:
                counts["unjoined"] += 1
            continue
        actual = float(hit[settle.MARKET_STAT[r["market"]]])
        result, won = settle.settle_row({"market": r["market"], "side": r["side"], "line": r["line"]}, actual)
        pnl = settle.american_pnl(r["price"], won) * float(r.get("stake", 1.0))
        r.update(status="graded" if won is not None else "void", result=result, actual=actual, won=won,
                 pnl_per_100=round(pnl, 2), graded_at_utc=now.strftime("%Y-%m-%dT%H:%M:%SZ"))
        counts["graded" if won is not None else "void"] += 1
    counts["open_left"] = sum(1 for r in rows if r.get("status") == "open")
    write(season, rows)
    counts["late_lines"] = add_late_lines(season)
    return counts


def resolve(season: int, bet_id: str, *, actual: float | None = None, void: bool = False,
            now: dt.datetime | None = None) -> dict:
    """Settle one bet by hand: `actual` (he played; his real stat, 0 included)
    or `void` (he did not play). Returns the updated row."""
    import settle
    if (actual is None) == (not void):
        raise ValueError("give exactly one of --actual or --void")
    rows = read(season)
    hit = [r for r in rows if r["id"] == bet_id]
    if not hit:
        raise ValueError(f"no bet {bet_id} in the {season} journal")
    r = hit[0]
    now = now or dt.datetime.now(dt.timezone.utc)
    stamp = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    if void:
        r.update(status="void", result="dnp", actual=None, won=None, pnl_per_100=0.0, graded_at_utc=stamp)
    else:
        result, won = settle.settle_row({"market": r["market"], "side": r["side"], "line": r["line"]}, float(actual))
        pnl = settle.american_pnl(r["price"], won) * float(r.get("stake", 1.0))
        r.update(status="graded" if won is not None else "void", result=result, actual=float(actual), won=won,
                 pnl_per_100=round(pnl, 2), graded_at_utc=stamp)
    write(season, rows)
    return r


def implied(price: int) -> float:
    """The raw implied chance of an American price (vig included)."""
    return abs(price) / (abs(price) + 100) if price < 0 else 100 / (price + 100)


def late_line(bet: dict, archive: list[dict]) -> dict | None:
    """The last Sleeper quote the capture logged before kickoff for this bet's
    player, market and side (DECISIONS #148). Not the true close -- a capture
    inside the final hour needs speed, which is off -- but the latest line the
    record holds, usually a few hours out."""
    import settle
    nm = settle.norm_name(bet["player"])
    # the archive labels anytime-TD quotes Yes / No, yardage quotes Over / Under
    side = {"over": "Over", "under": "Under", "yes": "Yes", "no": "No"}[bet["side"]]
    best = None
    for q in archive:
        if (q.get("bookmaker") != "sleeper" or q.get("market") != bet["market"]
                or q.get("outcome") != side or settle.norm_name(str(q.get("player", ""))) != nm):
            continue
        if q.get("season") != bet["season"] or int(q.get("week") or -1) != int(bet["week"]):
            continue
        if q.get("commence_time") and q.get("retrieved_at_utc") and \
                q["retrieved_at_utc"] > q["commence_time"].replace("+00:00", "Z"):
            continue
        if best is None or q["retrieved_at_utc"] > best["retrieved_at_utc"]:
            best = q
    if best is None:
        return None
    out = {"late_line": best.get("point"), "late_price": best.get("price_american"),
           "late_at_utc": best.get("retrieved_at_utc")}
    if bet.get("line") is None and best.get("price_american") is not None:
        # anytime TD: no line, so the price is the whole value (late price costs more = value)
        out["clv_points"] = 0.0
        out["clv_price"] = round(implied(int(best["price_american"])) - implied(int(bet["price"])), 4)
    elif bet.get("line") is not None and best.get("point") is not None:
        # positive = the number moved your way: an Over bought below the late
        # line, an Under bought above it
        mv = float(best["point"]) - float(bet["line"])
        out["clv_points"] = round(mv if side == "Over" else -mv, 2)
        if mv == 0 and best.get("price_american") is not None:
            # same line: the late price for your side costs more = you got value
            out["clv_price"] = round(implied(int(best["price_american"])) - implied(int(bet["price"])), 4)
    return out


def read_archive(season: int) -> list[dict]:
    import persist
    p = persist.lines_path(season)
    if not p.exists():
        return []
    with p.open(encoding="utf-8") as fh:
        return [json.loads(ln) for ln in fh if ln.strip()]


def add_late_lines(season: int, archive: list[dict] | None = None) -> int:
    """Stamp the late line on every bet that has none yet; returns how many."""
    rows = read(season)
    archive = read_archive(season) if archive is None else archive
    n = 0
    for r in rows:
        if r.get("late_line") is not None:
            continue
        ll = late_line(r, archive)
        if ll:
            r.update(ll)
            n += 1
    if n:
        write(season, rows)
    return n


def breakeven(price: int) -> float:
    """The win rate a price needs to break even."""
    return abs(price) / (abs(price) + 100) if price < 0 else 100 / (price + 100)


def summary_md(season: int) -> list[str]:
    """The scorecard's journal section."""
    rows = read(season)
    out = ["## Bet journal", ""]
    if not rows:
        return out + ["No bets logged yet. Log one with `python props/journal.py add ...` (all four "
                      "checklist answers required); it is graded here every Tuesday.", ""]
    done = [r for r in rows if r.get("status") == "graded"]
    n_open = sum(1 for r in rows if r.get("status") == "open")
    n_void = sum(1 for r in rows if r.get("status") == "void")
    n_check = sum(1 for r in rows if r.get("status") == "check")
    out.append(f"{len(rows)} bets logged: {len(done)} graded, {n_void} void (push or did not play), "
               f"{n_open} open" + (f", {n_check} to check (`journal resolve`)" if n_check else "")
               + ". Kept apart from the model's record: these are the user's handicapped bets.")
    out.append("")
    lv = [r for r in rows if r.get("clv_points") is not None]
    if lv:
        beat = sum(1 for r in lv if r["clv_points"] > 0 or (r["clv_points"] == 0 and (r.get("clv_price") or 0) > 0))
        tied = sum(1 for r in lv if r["clv_points"] == 0 and not r.get("clv_price"))
        out += ["**Late-line value, the first number to watch:** "
                f"{beat} of {len(lv)} bets got a better number than the last line Sleeper showed before kickoff "
                f"({beat / len(lv):.0%}; {tied} tied); mean move your way {sum(r['clv_points'] for r in lv) / len(lv):+.2f} "
                "points. Beating the late line shows up in about 100-200 bets; the win rate needs far more. It is the "
                "last line the capture logged (usually a few hours out), not the true close.", ""]
    if done:
        wins = sum(1 for r in done if r.get("won"))
        stake = sum(float(r.get("stake", 1.0)) for r in done)
        net = sum(float(r.get("pnl_per_100", 0.0)) for r in rows if r.get("status") in ("graded", "void"))
        be = sum(breakeven(int(r["price"])) for r in done) / len(done)
        out += ["| Bets | Won | Win rate | Break-even at these prices | Net per $100 staked |", "|---|---|---|---|---|",
                f"| {len(done)} | {wins} | {wins / len(done):.0%} | {be:.0%} | {net / stake:+.1f} |", ""]
        out.append("A few dozen bets say little; about 100 is where the win rate starts to separate from luck.")
        out.append("")
    out += ["| Week | Player | Bet | Price | Late line | Result | Net | The change |",
            "|---|---|---|---|---|---|---|---|"]
    for r in sorted(rows, key=lambda r: (r["week"], r["logged_at_utc"])):
        bet = (f"{r['side']} {LABEL.get(r['market'], r['market'])}" if r.get("line") is None
               else f"{r['side']} {r['line']:g} {LABEL.get(r['market'], r['market'])}")
        res = r.get("status") if r.get("status") != "graded" else ("won" if r.get("won") else "lost")
        net = "" if r.get("pnl_per_100") is None else f"{float(r['pnl_per_100']):+.0f}"
        late = ("—" if r.get("late_line") is None else
                f"{r['late_line']:g} {int(r['late_price']):+d} ({r.get('clv_points', 0):+g})")
        out.append(f"| {r['week']} | {r['player']} | {bet} | {int(r['price']):+d} | {late} | {res} | {net} | "
                   f"{r['change']} |")
    return out + [""]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add", help="log a bet with its four checklist answers")
    a.add_argument("player"); a.add_argument("market"); a.add_argument("side")
    a.add_argument("line", nargs="?", default=None, help="omit for an anytime TD")
    a.add_argument("price", type=int)
    a.add_argument("--team"); a.add_argument("--book", default="sleeper")
    a.add_argument("--stake", type=float, default=1.0, help="units (default 1)")
    a.add_argument("--change", required=True, help="the verified change in his duties")
    a.add_argument("--implies", required=True, help="the workload the line implies vs what he gets")
    a.add_argument("--fails", required=True, help="how the bet fails")
    a.add_argument("--season", type=int, default=None); a.add_argument("--week", type=int, default=None)
    ls = sub.add_parser("list"); ls.add_argument("--season", type=int, default=None)
    ls.add_argument("--open", action="store_true")
    g = sub.add_parser("grade"); g.add_argument("--season", type=int, required=True)
    sm = sub.add_parser("summary"); sm.add_argument("--season", type=int, default=None)
    rv = sub.add_parser("resolve", help="settle a 'check' bet by hand from the box score")
    rv.add_argument("id"); rv.add_argument("--season", type=int, default=None)
    rv.add_argument("--actual", type=float, default=None, help="his real stat (0 if he played and got none)")
    rv.add_argument("--void", action="store_true", help="he did not play")
    args = ap.parse_args(argv)
    season = getattr(args, "season", None) or dt.datetime.now(dt.timezone.utc).year
    if args.cmd == "add":
        line = args.line
        if line is not None and MARKETS.get(args.market.lower()) == "player_anytime_td":
            raise SystemExit("an anytime TD bet has no line: journal add PLAYER td yes PRICE ...")
        try:
            e = make_entry(args.player, args.market, args.side, line, args.price, change=args.change,
                           implies=args.implies, fails=args.fails, team=args.team, book=args.book,
                           stake=args.stake, season=season,
                           week=args.week or current_week(season))
        except ValueError as exc:
            print(f"not logged: {exc}", file=sys.stderr)
            return 2
        rows = read(season) + [e]
        write(season, rows)
        ln = "" if e["line"] is None else f"{e['line']:g} "
        print(f"logged {e['id']}: week {e['week']} {e['player']} {e['side']} "
              f"{ln}{LABEL[e['market']]} {e['price']:+d} -> {journal_path(season)}")
        return 0
    if args.cmd == "list":
        for r in read(season):
            if args.open and r.get("status") != "open":
                continue
            print(json.dumps(r, sort_keys=True))
        return 0
    if args.cmd == "resolve":
        try:
            r = resolve(season, args.id, actual=args.actual, void=args.void)
        except ValueError as exc:
            print(f"not resolved: {exc}", file=sys.stderr)
            return 2
        print(f"{r['id']}: {r['status']} ({r.get('result')}), net {r.get('pnl_per_100')}")
        return 0
    if args.cmd == "grade":
        c = grade(season)
        print(f"journal {season}: " + ", ".join(f"{k} {v}" for k, v in c.items()))
        return 0
    print("\n".join(summary_md(season)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
