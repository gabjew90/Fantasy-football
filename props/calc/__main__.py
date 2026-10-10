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
from core.manifest import Manifest

from . import capture, card, data, log, odds, player, settings
from .checks import DataError, number


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
        sp = sub.add_parser(name)
        sp.add_argument("--season", type=int, required=True)
        if name == "settle":
            sp.add_argument("--list-missing", action="store_true",
                            help="list every leg settled earlier that still has no line near kickoff")
    a = ap.parse_args(argv)

    try:
        return run(a)
    except (player.NotFound, DataError) as ex:
        print(f"Stopped: {ex}")
        return 2


def run(a) -> int:
    if a.cmd == "leg":
        print(leg(a))
        return 0
    if a.cmd == "capture":
        r = capture.run()
        print(f"Saved {r['rows']} lines captured at {r['captured_at_utc']} to {r['path']}.")
        if r["stale"]:
            print(f"Warning: built on older copies of {', '.join(r['stale'])}; player and game matches may be "
                  f"out of date.")
        if r["misses"]:
            print(f"{r['misses']} lines could not be matched to a player and game; see {capture.MISSES_PATH}.")
        if r["skipped"]:
            print(f"{r['skipped']} lines were skipped on Sleeper's side (one side missing, split lines or bad "
                  f"prices); also listed there.")
        return 0
    if a.cmd == "settle":
        man = Manifest("props.calc settle")
        roster = data.rosters(a.season, manifest=man)
        plays = data.pbp(a.season, manifest=man)
        pg = data.player_games(plays)
        played = data.played(data.snaps(a.season, manifest=man), roster)
        games = data.games_played(pg, played)
        sched = data.schedule(manifest=man)
        stale = [f"{e['name']} ({e['status']})" for e in man.stale()]
        if stale:                          # results are written for good: never from a stale copy
            raise DataError(f"inputs not refreshed: {', '.join(stale)}; nothing settled")
        kickoffs = dict(zip(sched["game_id"], sched["kickoff_utc"]))
        # a game is settled only when its play-by-play is complete: its last
        # running score equals the schedule's final score
        ready = data.complete_games(plays, sched)
        unmapped = played.attrs["unmapped"]
        r = log.settle(a.season, games, roster, ready=ready, kickoffs=kickoffs)
        print(f"Settled {r['settled']} legs.")
        if unmapped:
            print(f"Note: {len(unmapped)} players' snaps could not be tied to a gsis id (e.g. {unmapped[0][0]}, "
                  f"{unmapped[0][1]}); a leg on one of them settles as 'did not play' until the ids are fixed.")
        if r["unmatched"]:
            print(f"{len(r['unmatched'])} of them have no line near kickoff matched to the player, team and game "
                  f"(left empty):")
            for u in r["unmatched"]:
                print(f"  {u}")
        if r["filled"]:
            print(f"Filled the missing line near kickoff for {r['filled']} legs settled earlier.")
        if r["still_missing"]:
            print(f"{len(r['still_missing'])} legs settled earlier still have no line near kickoff"
                  + (":" if a.list_missing else " (--list-missing lists them)."))
            for u in (r["still_missing"] if a.list_missing else []):
                print(f"  {u}")
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
        raise player.NotFound(f"no {season} game for {team}" + (f" in week {week}" if week else " still to play"))
    return g.sort_values("kickoff_utc").iloc[0]


def leg(a) -> str:
    if a.target is not None and not 1 <= a.target <= 99:
        raise SystemExit(f"--target is a percent between 1 and 99 (e.g. 58); got {a.target}")
    if a.line is not None and (a.over is None or a.under is None):
        raise SystemExit("--line needs both --over and --under (American odds)")
    for name_, v in (("--line", a.line), ("--over", a.over), ("--under", a.under), ("--target", a.target)):
        if v is not None:
            try:
                number(v, name_)
            except DataError as ex:
                raise SystemExit(str(ex)) from None
    if a.line is not None and a.line <= 0:
        raise SystemExit(f"--line must be above 0; got {a.line}")
    typed = {}
    for side, v in (("over", a.over), ("under", a.under)):
        if v is not None:
            try:
                typed[side] = odds.multiplier_from_american(v)
            except ValueError:
                raise SystemExit(f"--over/--under are American odds like -125 or +110, not Sleeper's "
                                 f"multiplier (1.80x is -125); got {v}") from None
    if a.line is None and (a.over is not None or a.under is not None):
        raise SystemExit("--over and --under need --line (otherwise the saved quote's prices are used)")
    s = settings.load()
    tuned, fixed = s["tuned"], s["fixed"]
    season = a.season or F.current_season()
    man = Manifest("props.calc leg")
    b = player.Bundle(range(season - int(fixed["pool_seasons"]), season + 1), fixed, manifest=man)
    stale = [f"{e['name']} ({e['status']})" for e in man.stale()]
    warn = (f"WARNING: built on older copies of {', '.join(stale)} (a refresh failed); recent games may be "
            f"missing.\n" if stale else "")
    by_initial = [False]
    gsis, name, team = player.find_player(b, a.name, season, a.team, a.week, by_initial)
    if by_initial[0]:
        warn += (f"NOTE: {a.name!r} was matched to {name} by first initial and surname; check this is the "
                 f"player you meant.\n")
    game = _next_game(b.schedule, team, season, a.week)
    week = int(game["week"])
    stub = {"season": season, "week": week, "game_id": game["game_id"], "kickoff_utc": game["kickoff_utc"],
            "gsis_id": gsis, "player": name, "team": team, "market": a.market}
    if a.market == "rush_yds" and b.position_at(gsis, season, week) == "QB":
        raise SystemExit("QB rushing is not a market in this tool (design note)")
    pl = player.build(b, gsis, name, team, season, week, tuned, fixed, a.market)
    line = mo = mu = None
    if a.line is not None:
        line, mo, mu = a.line, typed["over"], typed["under"]
        source = "line typed in"
    else:
        try:
            q = log.line_near_kickoff(stub, b.rosters)
            if q:                                    # validated by the lookup: multipliers above 1
                source = f"Sleeper quote from {q['source']}, {q['at_utc'][:16].replace('T', ' ')} UTC"
                if q.get("note"):
                    source += f"; {q['note']}"
                line, mo, mu = q["line"], q["mult_over"], q["mult_under"]
            else:
                source = (f"Unmatched: no saved Sleeper quote belongs to {name} ({team}) in {game['game_id']} "
                          f"for {a.market}; give --line --over --under")
        except DataError as ex:                      # a bad saved row is reported; code errors are not caught
            source = f"Unmatched: {ex}; give --line --over --under"
    if a.market in pl.not_enough:               # the data gap is the first thing to say, line or not
        text = warn + card.render_not_enough(pl, a.market, line, mo, mu, source=source)
        return text + ("\nNot logged: not enough data for this leg." if a.log else "")
    if line is None:
        raise SystemExit(source)
    model = player.model(pl, a.market, tuned, fixed)
    target = a.target / 100 if a.target is not None else None
    c = card.compute(pl, model, a.market, line, mo, mu, fixed, target)
    text = warn + card.render(pl, c, source=source)
    if a.log and by_initial[0]:
        return text + "\nNot logged: the name was matched by initial; run again with the name as shown."
    if a.log and pd.Timestamp(game["kickoff_utc"]) <= pd.Timestamp(dt.datetime.now(dt.timezone.utc)):
        return text + "\nNot logged: this game has already kicked off (a leg is logged before its game only)."
    if a.log:
        row = log.log_leg({**stub, "side": a.log, "line": line, "mult_over": mo, "mult_under": mu,
                           "target_rate": c["target_over"] if a.log == "over" else c["target_under"],
                           "book_expects": card.value(c, "book_expects"),
                           "needed": card.value(c, f"needed_{a.log}"), "usual": c["usual"],
                           "gap": c["gap_over"] if a.log == "over" else c["gap_under"],
                           "needed_status": c["solutions"][f"needed_{a.log}"].status, "settings": tuned})
        text += f"\nLogged as leg {row['id']} ({a.log})."
    return text


if __name__ == "__main__":
    raise SystemExit(main())
