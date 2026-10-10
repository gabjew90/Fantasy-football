"""python -m props.calc <command>

  leg "Name" rush_yds over   one side's leg card (rush_yds, receptions, rec_yds or pass_yds)
      [--team DEN] [--season 2026 --week 6] [--line 64.5 --over -125 --under -132]
      [--target 58]
      Without --line, the latest saved Sleeper quote before kickoff is used, from
      the props record's line history (your captures and the engine's).
  capture                 save the current Sleeper lines (four markets) into that history
  entry --stake 5 --payout 50 --angle role --why "..." --leg "Name|rush_yds|over|64.5[|TEAM]" ...
      log a Power Play in the props journal (props/journal.py). The line is the
      one you played; the card is built on the newest saved quote at that line
      before kickoff (none saved at it: not logged). The card numbers are filled in. The journal grades it
      (`python props/journal.py grade --season 2026`).
"""

from __future__ import annotations

import argparse
import json
import sys

import datetime as dt

import pandas as pd

from core import fetch as F
from core.manifest import Manifest

from . import capture, card, data, game_lines, lines, matchup, names, odds, opponent, player, settings
from .checks import DataError, number
from .markets import workload_col
from .shared import journal


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
    lg.add_argument("market", choices=["rush_yds", "receptions", "rec_yds", "pass_yds"])
    lg.add_argument("side", choices=["over", "under"])
    lg.add_argument("--team")
    lg.add_argument("--season", type=int)
    lg.add_argument("--week", type=int)
    lg.add_argument("--line", type=float)
    lg.add_argument("--over", type=float, help="American odds for the Over")
    lg.add_argument("--under", type=float, help="American odds for the Under")
    lg.add_argument("--target", type=float, help="your target win rate in percent (default: break-even)")
    sub.add_parser("capture")
    en = sub.add_parser("entry", help="log a Power Play in the props journal, legs filled in from their cards")
    en.add_argument("--stake", type=float, required=True, help="dollars staked on the entry")
    en.add_argument("--payout", type=float, required=True,
                    help="the total returned if every leg wins, your stake included: the number Sleeper shows "
                         "(e.g. $5 entry, Sleeper shows $97.50 -> --payout 97.5); must be above --stake")
    en.add_argument("--angle", required=True, choices=list(journal.ANGLES), help="the entry's story")
    en.add_argument("--why", required=True, help="the entry's reason in one line")
    en.add_argument("--leg", action="append", required=True,
                    help="'Name|market|over or under|line played[|TEAM]', repeatable")
    en.add_argument("--season", type=int)
    en.add_argument("--week", type=int)
    en.add_argument("--dry-run", action="store_true",
                    help="print exactly the journal lines it would add, and write nothing")
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
        print(f"Saved {r['lines']} lines ({r['added']} new, {r['replaced']} updated) captured at "
              f"{r['captured_at_utc']} to {', '.join(r['paths']) or 'nowhere (none matched)'}.")
        if r["stale"]:
            print(f"Warning: built on older copies of {', '.join(r['stale'])}; player and game matches may be "
                  f"out of date.")
        if r["misses"]:
            print(f"{r['misses']} lines could not be matched to a player and game and were not saved; see "
                  f"{capture.MISSES_PATH}.")
        if r["skipped"]:
            print(f"{r['skipped']} lines were skipped on Sleeper's side (one side missing, split lines or bad "
                  f"prices); also listed there.")
        return 0
    if a.cmd == "entry":
        print(entry(a))
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


def _check_inputs(a) -> dict:
    """Typed numbers validated once; returns the typed multipliers by side."""
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
    return typed


def _bundle(season: int, fixed: dict) -> tuple:
    man = Manifest("props.calc")
    b = player.Bundle(range(season - int(fixed["pool_seasons"]), season + 1), fixed, manifest=man)
    stale = [f"{e['name']} ({e['status']})" for e in man.stale()]
    warn = (f"WARNING: built on older copies of {', '.join(stale)} (a refresh failed); recent games may be "
            f"missing.\n" if stale else "")
    return b, warn


_SPREADS: dict = {}


NOT_CONFIRMED = {"Out", "Doubtful", "Questionable"}


def qb_today(b, team: str, season: int, week: int) -> str:
    """The MATCHUP quarterback line (the user, 2026-10-10): "Starting QB not
    confirmed." when this game's starter is not settled, else no line. Never
    a guessed name: no dependable source names a replacement before kickoff
    (ESPN's depth chart lagged a week in 2026; Sleeper's is live-only and
    hand-kept). Not settled when any of:
    - the week's official injury report (nflverse injuries) has no rows for
      his team yet (the report is not out);
    - the opening-day starter is listed Out, Doubtful or Questionable, or did
      not practise with no game status yet;
    - his team's most recent game was started by someone else (an injury,
      including IR, which the weekly report leaves out, or a benching).
    Display only."""
    sch = b.schedule[(b.schedule["season"] == season)
                     & ((b.schedule["home_team"] == team) | (b.schedule["away_team"] == team))].sort_values("week")
    played = sch[sch["week"] < week]
    if played.empty:
        return ""                              # his team's opener is this game or later: no opening-day starter yet
    opener = player._starter(played.iloc[0], team)
    if opener is None:
        return ""
    latest = player._starter(played.iloc[-1], team)
    if latest is not None and latest != opener:
        return "Starting QB not confirmed."
    if b.__dict__.get("_injuries_season") != season:
        b._injuries = data.injuries(season, manifest=b.manifest)
        b._injuries_season = season
    inj = b._injuries
    rows = inj[(inj["week"] == week) & (inj["team"] == team)]
    if rows.empty:
        return "Starting QB not confirmed."   # the report for this week is not out yet
    me = rows[rows["gsis_id"] == opener]
    if len(me):
        status = me["report_status"].iloc[-1]
        practice = str(me.get("practice_status", pd.Series([""])).iloc[-1])
        if str(status) in NOT_CONFIRMED or (pd.isna(status) and practice.startswith("Did Not Participate")):
            return "Starting QB not confirmed."
    return ""


def _display_text(fn) -> str:
    """A display-only line: an error is shown on the card, never stops it."""
    try:
        return fn()
    except Exception as ex:  # noqa: BLE001 -- shown on the card
        return f"Starting QB: not checked ({type(ex).__name__}: {str(ex)[:50]})."


def _display(fn) -> dict:
    """A display-only block: an error is shown on the card, never stops it."""
    try:
        return fn()
    except Exception as ex:  # noqa: BLE001 -- shown on the card as "not available (...)"
        msg = f"{type(ex).__name__}: {str(ex)[:60]}"
        return {"error": msg, "note": f"not available ({msg})."}


def line_footer(at_utc: str | None) -> str:
    """One line: when the quote was saved, in Pacific time ("Line as of Oct 8,
    4:59 PM PT."); a typed line says so."""
    if at_utc is None:
        return "Line typed in."
    try:
        from zoneinfo import ZoneInfo
        pacific = ZoneInfo("America/Los_Angeles")
    except Exception as ex:  # noqa: BLE001 -- ZoneInfoNotFoundError on Windows without tzdata
        raise DataError(f"no time-zone database for America/Los_Angeles ({ex}); install tzdata "
                        f"(pip install -r requirements.txt)") from ex
    t = pd.Timestamp(at_utc).tz_convert(pacific)
    month = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()[t.month - 1]     # not locale-dependent
    return f"Line as of {month} {t.day}, {t.hour % 12 or 12}:{t.minute:02d} {'AM' if t.hour < 12 else 'PM'} PT."


def _week_lines(season: int, week: int) -> tuple:
    """(ESPN's week, or None, and why not), fetched once per run. Display
    only: a failed fetch is said on the card, never raised."""
    if (season, week) not in _SPREADS:
        try:
            _SPREADS[(season, week)] = (game_lines.week_lines(season, week), "")
        except Exception as ex:  # noqa: BLE001 -- shown on the card's MATCHUP block
            _SPREADS[(season, week)] = (None, f"ESPN not read: {type(ex).__name__}: {str(ex)[:80]}")
    return _SPREADS[(season, week)]


def build_card(b, name_in: str, market: str, side: str = "over", *, team=None, season: int, week=None, line=None,
               typed=None, target=None, lookup=None, at_line=None) -> dict:
    """One leg's card and the numbers behind it. Keys: text, ready (a full
    card with a line), by_initial, kicked_off, stub, line, mult_over,
    mult_under, source, not_enough, c (card.compute's dict, or None).
    at_line: use the newest saved quote at this line (the line a bet was made at)."""
    s = settings.load()
    tuned, fixed = s["tuned"], s["fixed"]
    warn = ""
    by_initial = [False]
    gsis, name, team = player.find_player(b, name_in, season, team, week, by_initial)
    if by_initial[0]:
        warn += (f"NOTE: {name_in!r} was matched to {name} by first initial and surname; check this is the "
                 f"player you meant.\n")
    game = _next_game(b.schedule, team, season, week)
    wk = int(game["week"])
    stub = {"season": season, "week": wk, "game_id": game["game_id"], "kickoff_utc": game["kickoff_utc"],
            "gsis_id": gsis, "player": name, "team": team, "market": market}
    if market == "rush_yds" and b.position_at(gsis, season, wk) == "QB":
        raise SystemExit("QB rushing is not a market in this tool (design note)")
    pl = player.build(b, gsis, name, team, season, wk, tuned, fixed, market)
    mo = mu = None
    at_utc = None                              # None: a line typed in
    line_note = ""
    if line is not None:
        mo, mu = typed["over"], typed["under"]
        source = "line typed in"
    else:
        try:
            q = (lookup or lines.LineLookup(b.rosters)).find(stub, line=at_line)
            if q:                                    # validated by the lookup: multipliers above 1
                source = f"Sleeper quote from {q['source']}, {q['at_utc'][:16].replace('T', ' ')} UTC"
                if q.get("note"):
                    source += f"; {q['note']}"
                    line_note = q["note"]
                line, mo, mu, at_utc = q["line"], q["mult_over"], q["mult_under"], q["at_utc"]
            else:
                at = "" if at_line is None else f" at {at_line:g}"
                source = (f"Unmatched: no saved Sleeper quote{at} belongs to {name} ({team}) in {game['game_id']} "
                          f"for {market}; give --line --over --under")
        except DataError as ex:                      # a bad saved row is reported; code errors are not caught
            source = f"Unmatched: {ex}; give --line --over --under"
    opp = game["away_team"] if game["home_team"] == team else game["home_team"]
    footer = line_footer(at_utc) if line is not None else source      # no line: why not
    kicked_off = pd.Timestamp(game["kickoff_utc"]) <= pd.Timestamp(dt.datetime.now(dt.timezone.utc))
    out = {"by_initial": by_initial[0], "kicked_off": kicked_off, "stub": stub, "line": line, "mult_over": mo,
           "mult_under": mu, "source": source, "c": None, "ready": False,
           "not_enough": market in pl.not_enough,
           "reason": "; ".join(pl.not_enough.get(market, [])) or (source if line is None else "")}
    if market in pl.not_enough:                 # the data gap is the first thing to say, line or not
        return {**out, "text": warn + card.render_not_enough(pl, market, side, line, mo, mu, footer=footer)}
    if line is None:
        return {**out, "text": warn + source}
    model = player.model(pl, market, tuned, fixed)
    c = card.compute(pl, model, market, line, mo, mu, fixed, target)
    week_lines, why = _week_lines(season, wk)
    gl = None
    if week_lines is not None:
        gl = week_lines.get((game["away_team"], game["home_team"]))
        why = "" if gl else f"ESPN lists no {game['away_team']} at {game['home_team']} game in week {wk}"
    if not game_lines.has_odds(gl):            # ESPN has none: the nflverse schedule's line
        sched = game_lines.closing(game)
        if sched is not None:
            # after kickoff it is the closing line; before, the schedule's current line (and ESPN's reason)
            sched["closing"] = True if kicked_off else ("schedule line; " + why if why else "schedule line")
            gl = sched
        why = why or "ESPN and the schedule show none"
    text = card.render(pl, c, side, opp=opp, game_lines=gl, why_no_lines=why, footer=footer,
                       opp_row=_display(lambda: opponent.allows(b, market, opp, pl.position, season, wk, fixed)),
                       grades=_display(lambda: matchup.grade_pair(b, team, opp, "run" if market == "rush_yds"
                                                                   else "pass", season, wk, fixed)),
                       line_note=line_note,
                       qb_today=_display_text(lambda: qb_today(b, team, season, wk)))
    return {**out, "c": c, "ready": True, "settings": tuned, "text": warn + text,
            # depths whose yards came from every position's catches (the "Calculation" follow-up; journal row)
            "pooled_depths": list(pl.receiving.get("pooled_all_positions", []))}


def leg(a) -> str:
    typed = _check_inputs(a)
    fixed = settings.load()["fixed"]
    season = a.season or F.current_season()
    b, warn = _bundle(season, fixed)
    got = build_card(b, a.name, a.market, a.side, team=a.team, season=season, week=a.week, line=a.line, typed=typed,
                     target=a.target / 100 if a.target is not None else None)
    if got["line"] is None and not got["not_enough"]:
        raise SystemExit(got["text"])          # no quote found and none typed: say why, no card
    return warn + got["text"]


def _parse_leg(spec: str) -> tuple:
    parts = [x.strip() for x in spec.split("|")]
    if len(parts) not in (4, 5) or not parts[0] or parts[2].lower() not in ("over", "under"):
        raise SystemExit(f"leg {spec!r}: write it as 'Name|market|over or under|line played[|TEAM]'")
    if parts[1] not in ("rush_yds", "receptions", "rec_yds", "pass_yds"):
        raise SystemExit(f"leg {spec!r}: market is rush_yds, receptions, rec_yds or pass_yds")
    try:
        line = number(float(parts[3]), "the leg's line")
    except (ValueError, DataError):
        raise SystemExit(f"leg {spec!r}: the line played is a number, e.g. 64.5") from None
    if line <= 0:
        raise SystemExit(f"leg {spec!r}: the line played must be above 0")
    return parts[0], parts[1], parts[2].lower(), line, (parts[4] if len(parts) == 5 and parts[4] else None)


def _check_entry(a, legs: list) -> None:
    """The checks that need no data, made before the bundle is loaded."""
    for name_, v in (("--stake", a.stake), ("--payout", a.payout)):
        try:
            number(v, name_)
        except DataError as ex:
            raise SystemExit(str(ex)) from None
    if len(legs) < 2:
        raise SystemExit("a Power Play has at least two legs")
    if not 0 < a.stake < a.payout:
        raise SystemExit(f"--payout is the total returned if every leg wins, stake included (the number Sleeper "
                         f"shows), so it is above --stake; got ${a.stake:g} staked, ${a.payout:g} payout")
    if not str(a.why or "").strip():
        raise SystemExit("--why is required: the entry's reason in one line")
    seen = [(names.norm(n), m) for n, m, *_ in legs]
    dup = sorted({x for x in seen if seen.count(x) > 1})
    if dup:
        raise SystemExit(f"the same player and market twice in one entry: {dup}")


def entry(a) -> str:
    """Logs a Power Play through journal.make_power_play. Every leg needs a full
    card from a saved quote at the line played, before its kickoff, and an
    exact name match; one leg that falls short and nothing is logged. Each journal row then carries the
    card's numbers (calc_*) and volume_unit, which journal.grade reads to save
    his actual workload."""
    legs = [_parse_leg(x) for x in a.leg]
    _check_entry(a, legs)
    fixed = settings.load()["fixed"]
    season = a.season or F.current_season()
    b, warn = _bundle(season, fixed)
    lookup = lines.LineLookup(b.rosters)
    cards, problems = [], []
    for name_in, market, side, played, team in legs:
        got = build_card(b, name_in, market, side, team=team, season=season, week=a.week, lookup=lookup, at_line=played)
        who = f"{name_in} ({market})"
        if got["by_initial"]:
            problems.append(f"{who}: matched by initial; use the name as the card shows it")
        elif not got["ready"]:
            problems.append(f"{who}: no full card ({got['reason']})")
        elif got["kicked_off"]:
            problems.append(f"{who}: the game has kicked off")
        elif got["line"] != played:            # the lookup was asked for this line: never expected
            raise DataError(f"{who}: the card was built at {got['line']:g}, not the line played {played:g}")
        cards.append((side, got))
    weeks = {g["stub"]["week"] for _, g in cards}
    if len(weeks) > 1:
        problems.append(f"the legs are in different weeks ({sorted(weeks)}); the journal logs one week per entry")
    if problems:
        return warn + "Not logged:\n" + "\n".join(f"  {p}" for p in problems)
    week = weeks.pop()
    jlegs = [(g["stub"]["player"], g["stub"]["market"], side, g["line"], g["stub"]["team"]) for side, g in cards]
    try:
        rows = journal.make_power_play(jlegs, stake=a.stake, payout=a.payout, angle=a.angle, why=a.why,
                                       season=season, week=week)
    except ValueError as ex:
        return warn + f"Not logged: {ex}"
    for r, (side, g) in zip(rows, cards):
        r.update(journal_fields(side, g))
    text = "\n\n".join(g["text"] for _, g in cards)
    if getattr(a, "dry_run", False):
        # the same serialisation journal.write uses, line for line
        added = "\n".join(json.dumps(r, sort_keys=True) for r in rows)
        return (warn + text + f"\n\nDRY RUN: nothing written. These {len(rows)} lines would be added to "
                f"{journal.journal_path(season)}:\n{added}")
    journal.write(season, journal.read(season) + rows)
    return (warn + text + f"\n\nLogged entry {rows[0]['entry_id']}: {len(rows)} legs, ${a.stake:g} to "
            f"${a.payout:g}, in {journal.journal_path(season)}.")


def journal_fields(side: str, g: dict) -> dict:
    """What a journal leg row carries from its card. volume_unit names the
    stats column journal.grade copies into actual_volume."""
    c, st = g["c"], g["stub"]
    return {"volume_unit": workload_col(st["market"]), "gsis_id": st["gsis_id"], "game_id": st["game_id"],
            "kickoff_utc": st["kickoff_utc"], "calc_line_source": g["source"],
            "calc_mult_over": g["mult_over"], "calc_mult_under": g["mult_under"],
            "calc_bar": card.value(c, f"needed_{side}"),
            "calc_bar_status": c["solutions"][f"needed_{side}"].status,
            "calc_target_rate": c[f"target_{side}"], "calc_line_implies": card.value(c, "book_expects"),
            "calc_usual": c["usual"], "calc_gap": c[f"gap_{side}"], "calc_settings": g["settings"],
            "calc_pooled_depths": g.get("pooled_depths", [])}


if __name__ == "__main__":
    raise SystemExit(main())
