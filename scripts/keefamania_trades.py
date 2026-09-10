"""The slot-based trade engine on a Yahoo league, from the roster scrape.

Same code as the Omnibeta radar -- manager.marginal.price / accepts /
verdict, the rank panel, FantasyCalc in the league's own format, the
injury discount -- on rosters read from data/raw/yahoo/<league>.txt by
manager.yahoo. Nothing here is scheduled: a brief on a stale scrape is
worse than none, and the reader says how old the file is.

    venv/Scripts/python.exe scripts/keefamania_trades.py --from "Big PP" WHISTLE --want WR

Options: --league (default keefamania), --from OWNER... (substring, all
rivals when omitted), --want POS (a piece I receive must be this
position), --give NAME... (restrict what I send), --keep NAME... (never
send), --max-give/--max-get (default 2), --top N.
"""
from __future__ import annotations

import argparse
import sys
import time
from itertools import combinations
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.stdout.reconfigure(encoding="utf-8")

from dotenv import load_dotenv  # noqa: E402

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from draftkit import seasondata, weekly  # noqa: E402
from draftkit.briefs import INSEASON_PLAYERS_MAX_AGE  # noqa: E402
from draftkit.config import Config  # noqa: E402
from draftkit.sleeper import SleeperClient  # noqa: E402
from manager import consensus, marginal, market, trade_radar, yahoo  # noqa: E402

SK = ("QB", "RB", "WR", "TE")
SEASON_WEEKS = 17
WIRE_PER_POS = 40


def build_ctx(league: str) -> dict:
    cfg = Config.load(league=league)
    client = SleeperClient(cfg.path("raw"))
    state = seasondata.nfl_state()
    week = int(state["week"]) if state.get("season_type") == "regular" else 1
    # Championship week. The Sleeper path derives it from playoff settings;
    # the yaml records "playoffs: 6 teams, weeks 15-17" for Keefamania.
    last_week = int(cfg.get("last_week") or SEASON_WEEKS)
    weeks_left = weekly.weeks_remaining(week, last_week)
    players = client.players(max_age=INSEASON_PLAYERS_MAX_AGE)
    injury = seasondata.injury_map(players)
    ctx = {"cfg": cfg, "state": {"season": state["season"], "week": week}, "week": week,
           "weeks_left": weeks_left, "players": players, "injury": injury,
           # the radar's ir_weeks lookup reads Sleeper-shaped scoring; the
           # league yaml carries the same keys
           "league": {"scoring_settings": dict(cfg.get("scoring") or
                                               (cfg.get("expected") or {}).get("scoring") or {})}}
    con, notes = consensus.build(ctx)
    for n in notes:
        print(f"  consensus: {n}")
    rosters, shape, ynotes = yahoo.load(cfg, players, con)
    for n in ynotes:
        print(f"  yahoo: {n}")
    if not rosters:
        sys.exit("no rosters")

    def row(r, pid):
        c = con.get(pid) or {}
        mean = float(c.get("mean") or 0.0)
        return dict(r, ros=round(mean * weeks_left / SEASON_WEEKS, 2), ros_season=round(mean, 2),
                    consensus=c, team=(players.get(pid) or {}).get("team"))

    owners = sorted(rosters)
    ctx["users_by_rid"] = {i + 1: o for i, o in enumerate(owners)}
    ctx["roster_players"] = {i + 1: [row(r, r["sleeper_id"]) for r in rosters[o]]
                             for i, o in enumerate(owners)}
    me_name = str((cfg.get("me") or {}).get("username") or "")
    my = [rid for rid, o in ctx["users_by_rid"].items() if o == me_name]
    if len(my) != 1:
        sys.exit(f"me.username {me_name!r} is not exactly one owner in the scrape: {owners}")
    ctx["my_rid"] = my[0]
    ctx["rosters"] = [{"roster_id": rid} for rid in ctx["users_by_rid"]]
    ctx["slots"], ctx["flex"], ctx["flex_slots"] = shape["slots"], shape["flex"], None

    # The wire: everyone in the NFL universe with a projection who is not on
    # a scraped roster. Yahoo's own FA pool is a subset (waiver claims in
    # flight), so a backfill body here is slightly optimistic.
    rostered = {r["sleeper_id"] for rows in ctx["roster_players"].values() for r in rows}
    wire = []
    for pid, c in con.items():
        d = players.get(pid) or {}
        if pid in rostered or d.get("position") not in SK or not d.get("team"):
            continue
        if float(c.get("mean") or 0) <= 0:
            continue
        wire.append(row({"sleeper_id": pid, "pos": d["position"],
                         "name": d.get("full_name") or pid, "weekly": float(c["mean"])}, pid))
    by_pos: dict[str, list] = {}
    for p in sorted(wire, key=lambda p: -p["ros"]):
        by_pos.setdefault(p["pos"], []).append(p)
    ctx["_wv_pool"] = [p for rows in by_pos.values() for p in rows[:WIRE_PER_POS]]
    ctx["age_of"] = {}
    return ctx


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--league", default="keefamania")
    ap.add_argument("--from", dest="owners", nargs="*", default=[])
    ap.add_argument("--want", default=None)
    ap.add_argument("--give", nargs="*", default=[])
    ap.add_argument("--keep", nargs="*", default=[])
    ap.add_argument("--max-give", type=int, default=2)
    ap.add_argument("--max-get", type=int, default=2)
    ap.add_argument("--top", type=int, default=12)
    ap.add_argument("--out", nargs="*", default=[], metavar="NAME=WEEKS",
                    help="my read of an injury, e.g. \"A.J. Brown=6\"; marks him Out for that many weeks")
    a = ap.parse_args()

    ctx = build_ctx(a.league)
    ctx["weeks_out"] = {}
    for spec in a.out:
        name, _, weeks = spec.rpartition("=")
        hits = [p for rows in ctx["roster_players"].values() for p in rows
                if name.lower() in p["name"].lower()]
        if len(hits) != 1:
            sys.exit(f"--out {spec!r}: {len(hits)} roster names match")
        pid = str(hits[0]["sleeper_id"])
        ctx["injury"][pid] = ctx["injury"].get(pid) or "Out"
        ctx["weeks_out"][pid] = int(weeks)
    vals, note = market.values(None, ctx)
    print(f"  market: {note or f'{len(vals)} rows'}")
    ranks = trade_radar._rank_panel(ctx)
    print(f"  rank panel: {len(ranks or {})} rows")
    adj, wv = trade_radar._injury_adjusted(ctx)
    shape = {"slots": ctx["slots"], "flex": ctx["flex"], "flex_slots": None}
    wl = ctx["weeks_left"]
    me = ctx["my_rid"]
    mine = adj[me]

    def ov(p):
        return ((ranks or {}).get(str(p["sleeper_id"])) or {}).get("overall")

    def fmt(p):
        r = ov(p)
        inj = p.get("_injury")
        return (f"{p['name']} ({p['pos']} {p['ros']:.0f}{' ov %d' % r if r else ''} ${vals.get(str(p['sleeper_id']), 0)}"
                + (f" ⚠{inj['status']}" if inj else "") + ")")

    starters = {p["sleeper_id"] for p in marginal.slot_moves(mine, shape, key="ros")["before"]}
    print(f"\nMY ROSTER ({ctx['users_by_rid'][me]}; week {ctx['week']}, {wl} weeks left; starters *):")
    for p in sorted(mine, key=lambda p: (SK.index(p["pos"]), -p["ros"])):
        print(f"  {'*' if p['sleeper_id'] in starters else ' '} {fmt(p)}")

    rivals = {rid: rows for rid, rows in adj.items() if rid != me}
    if a.owners:
        rivals = {rid: rows for rid, rows in rivals.items()
                  if any(o.lower() in ctx["users_by_rid"][rid].lower() for o in a.owners)}
        if not rivals:
            sys.exit(f"no owner matches {a.owners}: {list(ctx['users_by_rid'].values())}")
    for rid, rows in rivals.items():
        st = {p["sleeper_id"] for p in marginal.slot_moves(rows, shape, key="ros")["before"]}
        print(f"\n{ctx['users_by_rid'][rid]} (starters *):")
        for p in sorted(rows, key=lambda p: (SK.index(p["pos"]), -p["ros"])):
            print(f"  {'*' if p['sleeper_id'] in st else ' '} {fmt(p)}")

    gives = [p for p in mine if p["pos"] in SK and p["name"] not in a.keep
             and (not a.give or any(g.lower() in p["name"].lower() for g in a.give))]
    give_sets = [list(c) for k in range(1, a.max_give + 1) for c in combinations(gives, k)]
    rows_out = []
    t0 = time.time()
    n = 0
    for rid, theirs in rivals.items():
        sk = [p for p in theirs if p["pos"] in SK]
        get_sets = [list(c) for k in range(1, a.max_get + 1) for c in combinations(sk, k)
                    if not a.want or any(x["pos"] == a.want.upper() for x in c)]
        for give in give_sets:
            for get in get_sets:
                n += 1
                try:
                    d = marginal.price(mine, theirs, give, get, shape, key="ros",
                                       market_values=vals, waivers=wv, ranks=ranks)
                except Exception:
                    continue
                acc = d.acceptance
                if d.my_delta <= 0 or not (acc and acc["accept"]):
                    continue
                if any(acc["tags"][str(p["sleeper_id"])] == marginal.SITS for p in give):
                    continue
                rows_out.append((d.my_delta / wl, d, give, get, rid))
    print(f"\n{n} packages priced in {time.time() - t0:.0f}s; {len(rows_out)} pass "
          f"(he accepts on rank + market, my lineup gains, no throw-ins)")

    rows_out.sort(key=lambda r: -r[0])
    print(f"\n{'me/wk':>6} {'range':>15} {'hismkt':>6} {'flag':>5} {'depth':>6}  package")
    for ppg, d, give, get, rid in rows_out[:a.top]:
        acc = d.acceptance
        theirs = adj[rid]
        rng = trade_radar._range_ppg(mine, theirs, give, get, shape, wv, wl)
        thin = marginal.newly_thin(mine, shape, arriving=get, departing=give, waivers=wv, key="ros")
        tags = ", ".join(f"{p['name'].split()[-1][:7]} {acc['tags'][str(p['sleeper_id'])][0]}" for p in give)
        r = f"{rng[0]:+.2f}..{rng[1]:+.2f}" if rng else "n/a"
        print(f"{ppg:>+6.2f} {r:>15} {acc['starters_market_after'] - acc['starters_market_before']:>+6d} "
              f"{acc['net_rank']:>+5.0f} {','.join(thin) or '-':>6}  "
              f"{' + '.join(p['name'] for p in give)} -> {' + '.join(fmt(p) for p in get)}  "
              f"[{ctx['users_by_rid'][rid]}]  ({tags})")

    print("\nRADAR LINES, best per rival:")
    seen = set()
    for ppg, d, give, get, rid in rows_out:
        if rid in seen:
            continue
        seen.add(rid)
        print(f"\n### {' + '.join(p['name'] for p in give)} -> {' + '.join(p['name'] for p in get)}  [{ctx['users_by_rid'][rid]}]")
        for line in trade_radar._priced(ctx, {"mgr": ctx["users_by_rid"][rid], "rid": rid,
                                              "give_p": give, "get_p": get}, vals):
            print(line)


if __name__ == "__main__":
    main()
