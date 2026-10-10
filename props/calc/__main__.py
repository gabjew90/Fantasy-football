"""python -m props.calc <command>

  leg "Name" rush_yds     the leg card (rush_yds or receptions for now)
      [--team DEN] [--season 2026 --week 6] [--line 64.5 --over -125 --under -132]
      [--target 58] [--log over|under]
      Without --line, the latest saved quote before kickoff is used: your own
      captures first, then the engine workflow's saved Sleeper lines.
  capture                 save the current Sleeper lines (four markets)
  settle --season 2026    add actual workloads and results to logged legs
  summary --season 2026   needed vs actual workload, legs won vs break-even, by gap
"""

from __future__ import annotations

import argparse
import sys

import datetime as dt

import pandas as pd

from core import fetch as F

from . import capture, card, data, log, odds, player, settings


def _utf8() -> None:
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass


def main(argv: list[str] | None = None) -> int:
    _utf8()
    ap = argparse.ArgumentParser(prog="python -m props.calc", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    lg = sub.add_parser("leg")
    lg.add_argument("name")
    lg.add_argument("market", choices=["rush_yds", "receptions"])
    lg.add_argument("--team")
    lg.add_argument("--season", type=int)
    lg.add_argument("--week", type=int)
    lg.add_argument("--line", type=float)
    lg.add_argument("--over", type=float, help="American odds for the Over")
    lg.add_argument("--under", type=float, help="American odds for the Under")
    lg.add_argument("--target", type=float, help="your target win rate in percent (default: break-even)")
    lg.add_argument("--log", choices=["over", "under"], help="log this leg, on this side")
    sub.add_parser("capture")
    for name in ("settle", "summary"):
        sub.add_parser(name).add_argument("--season", type=int, required=True)
    a = ap.parse_args(argv)

    if a.cmd == "leg":
        print(leg(a))
        return 0
    if a.cmd == "capture":
        r = capture.run()
        print(f"Saved {r['rows']} lines captured at {r['captured_at_utc']} to {r['path']}.")
        if r["misses"]:
            print(f"{r['misses']} players could not be matched; see {capture.MISSES_PATH}.")
        return 0
    if a.cmd == "settle":
        roster = data.rosters(a.season)
        games = data.games_played(data.player_games(data.pbp(a.season)),
                                  data.played(data.snaps(a.season), roster))
        n = log.settle(a.season, games)
        print(f"Settled {n} legs.")
        return 0
    if a.cmd == "summary":
        edges = settings.load()["fixed"]["gap_edges"]
        rows = log.summary(a.season, edges)
        if not rows:
            print("No settled legs yet.")
        for r in rows:
            need = "n/a" if r["needed"] is None else f"{r['needed']:.1f}"
            got = "n/a" if r["actual"] is None else f"{r['actual']:.1f}"
            print(f"{r['market']}, gap {r['gap']}: {r['won']} of {r['legs']} won "
                  f"(break-even {r['break_even']:.0%}); needed {need}, got {got} on average")
        return 0
    return 1


def _next_game(sched: pd.DataFrame, team: str, season: int, week: int | None) -> pd.Series:
    g = sched[(sched["season"] == season) & ((sched["home_team"] == team) | (sched["away_team"] == team))]
    if week is not None:
        g = g[g["week"] == week]
    else:
        g = g[pd.to_datetime(g["kickoff_utc"], utc=True) > pd.Timestamp(dt.datetime.now(dt.timezone.utc))]
    if g.empty:
        raise LookupError(f"no {season} game for {team}" + (f" in week {week}" if week else " still to play"))
    return g.sort_values("kickoff_utc").iloc[0]


def leg(a) -> str:
    s = settings.load()
    tuned, fixed = s["tuned"], s["fixed"]
    season = a.season or F.current_season()
    b = player.Bundle(range(season - int(fixed["pool_seasons"]), season + 1), fixed)
    gsis, name, team = player.find_player(b, a.name, season, a.team, a.week)
    game = _next_game(b.schedule, team, season, a.week)
    week = int(game["week"])
    stub = {"season": season, "week": week, "game_id": game["game_id"], "kickoff_utc": game["kickoff_utc"],
            "gsis_id": gsis, "player": name, "market": a.market}
    if a.line is not None:
        if a.over is None or a.under is None:
            raise SystemExit("--line needs both --over and --under (American odds)")
        line, mo, mu = a.line, odds.multiplier_from_american(a.over), odds.multiplier_from_american(a.under)
        source = "line typed in"
    else:
        q = log.line_near_kickoff(stub)
        if q is None:
            raise SystemExit(f"no saved quote for {name} {a.market} in week {week}; give --line --over --under")
        line = q["line"]
        mo = q.get("mult_over") or odds.multiplier_from_american(q["american_over"])
        mu = q.get("mult_under") or odds.multiplier_from_american(q["american_under"])
        source = f"Sleeper quote from {q['source']}, {q['at_utc'][:16].replace('T', ' ')} UTC"
    pl = player.build(b, gsis, name, team, season, week, tuned, fixed)
    model = player.model(pl, a.market, tuned, fixed)
    target = a.target / 100 if a.target is not None else None
    c = card.compute(pl, model, a.market, line, mo, mu, fixed, target)
    text = card.render(pl, c, source=source)
    if a.log:
        need = c["needed_over"] if a.log == "over" else c["needed_under"]
        row = log.log_leg({**stub, "team": team, "side": a.log, "line": line, "mult_over": mo, "mult_under": mu,
                           "target_rate": c["target_over"] if a.log == "over" else c["target_under"],
                           "book_expects": c["book_expects"], "needed": need, "usual": c["usual"],
                           "gap": c["gap_over"] if a.log == "over" else c["gap_under"], "settings": tuned})
        text += f"\nLogged as leg {row['id']} ({a.log})."
    return text


if __name__ == "__main__":
    raise SystemExit(main())
