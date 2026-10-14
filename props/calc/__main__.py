"""python -m props.calc <command>

  leg "Name" rush_yds over   one side's leg card (rush_yds, receptions, rec_yds or pass_yds)
      [--team DEN] [--season 2026 --week 6] [--line 64.5 --over -125 --under -132]
      [--target 58]
      Without --line, the latest saved Sleeper quote before kickoff is used, from
      the props record's line history (your captures and the engine's).
  game PHI@JAX             every posted line of one game in one run: a summary table (each side's
      [--player "Name" ...]  workload bar against his recent average), then the cards for the
      [--all] [--side over]  players named (or --all), both sides unless --side; the data loads once
  screen --window "Sun 1pm PT"   (or --game AWAY@HOME) every saved line in the window, both sides,
      [--week N] [--grade]   listed only where his recent workload meets the bar and ranked by how
                             little the leg asks (untested); then the top 3 cards a side. --grade marks a
                             past week's list with the journal's grader
  capture                 save the current Sleeper lines (four markets) into that history
  entry --stake 5 --payout 50 --angle role --why "..." --leg "Name|rush_yds|over|64.5[|TEAM]" ...
      log a Power Play in the props journal (props/journal.py). The line is the
      one you played; the card is built on the newest saved quote at that line
      before kickoff (none saved at it: not logged). The card numbers are filled in. The journal grades it
      (`python props/journal.py grade --season 2026`).
"""

from __future__ import annotations

import argparse
from pathlib import Path
import json
import sys

import datetime as dt

import pandas as pd

from core import fetch as F
from core.manifest import Manifest

from . import capture, card, data, game_lines, lines, matchup, names, odds, opponent, player, settings, summary
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
    lg.add_argument("--format", choices=["text", "md"], default="text",
                    help="text: the 40-column card; md: the chat card (markdown, the user's layout)")
    gm = sub.add_parser("game", help="every posted line of one game: a summary table, then the cards asked for")
    gm.add_argument("matchup", help="AWAY@HOME, e.g. PHI@JAX")
    gm.add_argument("--player", action="append", default=[], help="a player whose cards to print (repeatable)")
    gm.add_argument("--all", action="store_true", help="print every posted line's cards")
    gm.add_argument("--side", choices=["over", "under", "both"], default="both")
    gm.add_argument("--season", type=int)
    gm.add_argument("--week", type=int)
    gm.add_argument("--format", choices=["text", "md"], default="text", help="the cards as text or as chat cards")
    sc = sub.add_parser("screen", help="every saved line in a kickoff window or game, both sides, smallest ask first")
    sc.add_argument("--window", help="'<day> <time> PT', e.g. 'Sun 1pm PT' (that clock hour, Pacific)")
    sc.add_argument("--game", help="AWAY@HOME instead of a window")
    sc.add_argument("--season", type=int)
    sc.add_argument("--week", type=int, help="a past week (default: the soonest window still to kick off)")
    sc.add_argument("--format", choices=["text", "md"], default="text", help="the top cards as text or chat cards")
    sc.add_argument("--grade", action="store_true", help="grade the listed legs (a played week) with the journal's grader")
    sub.add_parser("capture")
    en = sub.add_parser("entry", help="log a Power Play in the props journal, legs filled in from their cards")
    en.add_argument("--stake", type=float, required=True, help="dollars staked on the entry")
    en.add_argument("--payout", type=float,
                    help="the total returned if every leg wins, your stake included: the number Sleeper shows "
                         "(e.g. $5 entry, Sleeper shows $97.50 -> --payout 97.5); must be above --stake. "
                         "Needed to log; a --dry-run without it works the payout out from the legs' prices "
                         "and says so")
    en.add_argument("--angle", required=True, choices=list(journal.ANGLES), help="the entry's story")
    en.add_argument("--why", required=True, help="the entry's reason in one line")
    en.add_argument("--leg", action="append", required=True,
                    help="'Name|market|over or under|line played[|TEAM]', repeatable")
    en.add_argument("--season", type=int)
    en.add_argument("--week", type=int)
    en.add_argument("--format", choices=["text", "md"], default="text",
                    help="md: the chat layout -- a comparison table, the chat cards, then the fit check")
    en.add_argument("--dry-run", action="store_true",
                    help="print exactly the journal lines it would add, and write nothing")
    a = ap.parse_args(argv)

    try:
        return run(a)
    except (player.NotFound, DataError) as ex:
        print(f"Stopped: {ex}")
        return 2
    except F.FetchError as ex:
        # one line, never a traceback (DECISIONS #235): core.fetch has already retried
        print(f"Download failed: {ex}. Nothing was priced; try again in a minute.")
        return 1


def run(a) -> int:
    if a.cmd == "leg":
        print(leg(a))
        return 0
    if a.cmd == "game":
        print(game(a))
        return 0
    if a.cmd == "screen":
        print(screen(a))
        return 0
    if a.cmd == "capture":
        r = capture.run()
        print(capture.summary_line(r))
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


NOT_CONFIRMED = {"Doubtful", "Questionable"}


def qb_today(b, team: str, season: int, week: int) -> str:
    """The MATCHUP quarterback line (the user, 2026-10-11, DECISIONS #241; was the opening-day starter,
    2026-10-10). The current starter is whoever started his team's most recent game. Never a guessed
    name: only the official report (nflverse injuries) and played games are read.
    - "<Name> ruled Out." when the official report lists the current starter Out (a fact, not a
      guess at who replaces him);
    - "Starting QB not confirmed." when it lists him Doubtful or Questionable, or he did not practise
      with no game status yet; or when a quarterback who started for the team earlier this season
      is on this week's report and not ruled Out (he may take the job back);
    - otherwise no line -- including before the week's report is out: he started the last game.
    Display only."""
    played = player.played_before(b.schedule, team, season, week)
    if played.empty:
        return ""                              # his team has not played yet: no starter yet
    started = played[[player._starter(g, team) is not None for _, g in played.iterrows()]]
    if started.empty:
        return ""                              # no played game with its plays posted yet
    last = started.iloc[-1]                    # a final score posted before its plays has no starter yet
    now = player._starter(last, team)
    if b.__dict__.get("_injuries_season") != season:
        b._injuries = data.injuries(season, manifest=b.manifest)
        b._injuries_season = season
    inj = b._injuries
    rows = inj[(inj["week"] == week) & (inj["team"] == team)]
    me = rows[rows["gsis_id"] == now]
    if len(me):
        status = me["report_status"].iloc[-1]
        practice = str(me.get("practice_status", pd.Series([""])).iloc[-1])
        if str(status) == "Out":
            name = str(me["full_name"].iloc[-1]) if "full_name" in me and pd.notna(me["full_name"].iloc[-1]) \
                and str(me["full_name"].iloc[-1]).strip() else player._starter(last, team, "name")
            return f"{name or 'His starting QB'} ruled Out."
        if str(status) in NOT_CONFIRMED or (pd.isna(status) and practice.startswith("Did Not Participate")):
            return "Starting QB not confirmed."
    earlier = {player._starter(g, team) for _, g in played.iterrows()} - {now, None}
    back = rows[rows["gsis_id"].isin(earlier)]
    if len(back) and (back["report_status"].astype(str) != "Out").any():
        return "Starting QB not confirmed."   # an earlier starter is on the report, not ruled Out
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


def _game_line(game, season: int, wk: int, kicked_off: bool) -> tuple:
    """(the game's spread and total, why there is none): ESPN's, else the nflverse schedule's line."""
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
    return gl, why


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
           "not_enough": market in pl.not_enough, "opp": opp,
           "reason": "; ".join(pl.not_enough.get(market, [])) or (source if line is None else "")}
    # the chat card names where the quote came from (the user's layout: "quote source and capture time")
    md_footer = footer.replace("Line as of", "Sleeper line as of", 1) if at_utc is not None else footer
    md_warn = warn.strip() + "\n\n" if warn else ""
    if market in pl.not_enough:                 # the data gap is the first thing to say, line or not
        nmd = md_warn + card.render_not_enough_md(pl, market, side, line, mo, mu, footer=md_footer)
        return {**out, "text": warn + card.render_not_enough(pl, market, side, line, mo, mu, footer=footer),
                "md": nmd, "md_game": nmd}
    if line is None:
        return {**out, "text": warn + source, "md": md_warn + source, "md_game": md_warn + source}
    model = player.model(pl, market, tuned, fixed)
    c = card.compute(pl, model, market, line, mo, mu, fixed, target)
    gl, why = _game_line(game, season, wk, kicked_off)
    shown = dict(opp=opp, game_lines=gl, why_no_lines=why, line_note=line_note,
                 opp_row=_display(lambda: _opp_allows(b, market, opp, pl.position, season, wk, fixed)),
                 grades=_display(lambda: matchup.grade_pair(b, team, opp, "run" if market == "rush_yds"
                                                             else "pass", season, wk, fixed)),
                 qb_today=_display_text(lambda: qb_today(b, team, season, wk)))
    text = card.render(pl, c, side, footer=footer, **shown)
    md = card.render_md(pl, c, side, footer=md_footer, **shown)
    md_game = card.render_md(pl, c, side, footer=md_footer, matchup=False, **shown)
    return {**out, "c": c, "ready": True, "settings": tuned, "text": warn + text, "md": md_warn + md,
            "md_game": md_warn + md_game,          # a screen or game read: the matchup is in the game header
            "pl": pl, "shown": shown,                # the screen reads both sides from these (DECISIONS #240)
            # depths whose yards came from every position's catches (the "Calculation" follow-up; journal row)
            "pooled_depths": list(pl.receiving.get("pooled_all_positions", []))}


def _md_lead(warn: str) -> str:
    """A warning above chat output: its own paragraph, so markdown does not run it into the title."""
    return warn.strip() + "\n\n" if warn else ""


def leg(a) -> str:
    typed = _check_inputs(a)
    fixed = settings.load()["fixed"]
    season = a.season or F.current_season()
    b, warn = _bundle(season, fixed)
    got = build_card(b, a.name, a.market, a.side, team=a.team, season=season, week=a.week, line=a.line, typed=typed,
                     target=a.target / 100 if a.target is not None else None)
    if got["line"] is None and not got["not_enough"]:
        raise SystemExit(got["text"])          # no quote found and none typed: say why, no card
    if getattr(a, "format", "text") == "md":
        return _md_lead(warn) + got["md"]
    return warn + got["text"]


MARKET_ORDER = ("pass_yds", "rush_yds", "receptions", "rec_yds")


def _game_between(sched: pd.DataFrame, away: str, home: str, season: int, week: int | None) -> pd.Series:
    g = sched[(sched["season"] == season) & (sched["away_team"] == away) & (sched["home_team"] == home)]
    if week is not None:
        g = g[g["week"] == week]
    else:
        g = g[pd.to_datetime(g["kickoff_utc"], utc=True) > pd.Timestamp(dt.datetime.now(dt.timezone.utc))]
    if g.empty:
        raise player.NotFound(f"no {season} {away}@{home} game" + (f" in week {week}" if week else " still to play"))
    return g.sort_values("kickoff_utc").iloc[0]


def _bar_cell(c: dict, key: str, side: str, market: str) -> str:
    """One side's workload bar as the card prints it."""
    s = c["solutions"][key]
    many = card.SHOW[market][1][1]
    if s.status == "ok":
        return f"{card._work(s.value)} {many}" + (" or fewer" if side == "under" else "")
    return f"any workload clears it" if s.status == "always" else "no workload clears it"


def _cell(x) -> str:
    """Text safe inside one markdown table cell."""
    return " ".join(str(x).replace("|", "/").split())


def _named(typed: str, name: str) -> bool:
    """A typed name points at this player: the same name, or Sleeper's short form ("C. McCaffrey")."""
    return names.norm(typed) == names.norm(name) or (
        names.abbreviated(typed) and names.initial_key(typed) == names.initial_key(name))


def _opp_allows(b, market: str, opp: str, position, season: int, week: int, fixed: dict) -> dict:
    """opponent.allows, once per (market, opponent, position, week) in a run: a screen asks it for every
    player on a team and the answer depends on none of them."""
    cache = b.__dict__.setdefault("_opp_allows", {})
    key = (market, opp, position, season, week)
    if key not in cache:
        cache[key] = opponent.allows(b, market, opp, position, season, week, fixed)
    return cache[key]


def _matchup(text: str) -> tuple[str, str]:
    away, sep, home = str(text).upper().partition("@")
    if not sep or not away or not home:
        raise SystemExit(f"write the game as AWAY@HOME, e.g. PHI@JAX; got {text!r}")
    return names.team_code(away), names.team_code(home)


def _injuries(b, season: int) -> pd.DataFrame:
    if b.__dict__.get("_injuries_season") != season:
        b._injuries = data.injuries(season, manifest=b.manifest)
        b._injuries_season = season
    return b._injuries


def _release() -> str:
    """The release that is running: in chat the bootstrap's stamp beside the release (a release does
    not carry nfl.lock.json), in a checkout nfl.lock.json -- as nfl.py's _release reads it."""
    root = Path(__file__).resolve().parents[2]
    for path, keys in ((root.with_name(root.name + ".stamp.json"), ("release_tag", "lock_tag")),
                       (root / "nfl.lock.json", ("tag",))):
        try:
            d = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        for k in keys:
            if d.get(k):
                return d[k]
    return "unknown"


def screen(a) -> str:
    """Every saved Sleeper line in a kickoff window (or one game), both sides, from one data load
    (DECISIONS #240): listed only where his recent workload already meets the bar, ranked by how
    little the leg asks (screen.py), then the top 3 cards a side. Untested; the header says so."""
    from . import screen as S
    fixed = settings.load()["fixed"]
    season = a.season or F.current_season()
    if bool(a.window) == bool(a.game):
        raise SystemExit("give --window '<day> <time> PT' (e.g. 'Sun 1pm PT') or --game AWAY@HOME")
    b, warn = _bundle(season, fixed)
    now = dt.datetime.now(dt.timezone.utc)
    if a.window:
        games = S.window_games(b.schedule, season, a.week, S.parse_window(a.window), now)
        label = a.window.strip()
    else:
        away, home = _matchup(a.game)
        games = _game_between(b.schedule, away, home, season, a.week).to_frame().T
        label = f"{away} at {home}"
    started = games[[pd.Timestamp(k) <= pd.Timestamp(now) for k in games["kickoff_utc"]]]
    replay = len(started) == len(games)
    if not replay:
        games = games.drop(started.index)
    lookup = lines.LineLookup(b.rosters)
    inj = _display(lambda: _injuries(b, season))
    inj_ok = not isinstance(inj, dict)
    rows, problems, ruled_out, n_posted, lineup_out = [], [], {}, 0, []
    lines_out, sides_out = {}, {}                  # whole lines never built; sides built but not listed
    skip = lambda why: lines_out.__setitem__(why, lines_out.get(why, 0) + 1)      # noqa: E731
    unlisted = lambda why: sides_out.__setitem__(why, sides_out.get(why, 0) + 1)  # noqa: E731
    for _, g in games.iterrows():
        wk = int(g["week"])
        posted, unread, bad = lookup.posted({"season": season, "week": wk, "kickoff_utc": g["kickoff_utc"],
                                             "game_id": g["game_id"], "home_team": g["home_team"],
                                             "away_team": g["away_team"]})
        problems += bad + ([f"{unread} saved rows for {g['away_team']} at {g['home_team']} could not be read"]
                           if unread else [])
        n_posted += len(posted)
        for p_ in posted:
            try:
                got = build_card(b, p_["player"], p_["market"], "over", team=p_["team"], season=season, week=wk,
                                 lookup=lookup)
            except (player.NotFound, DataError, SystemExit):
                skip("not built")
                continue
            if got["stub"]["game_id"] != g["game_id"]:
                skip("not built")
                continue
            if got["not_enough"]:
                skip("not enough data")
                continue
            if not got["ready"]:
                skip("no usable quote")
                continue
            c = got["c"]
            bars = {sd: card.value(c, f"needed_{sd}") for sd in ("over", "under")}
            status = None
            if inj_ok:
                me = inj[(inj["week"] == wk) & (inj["gsis_id"] == got["stub"]["gsis_id"])]
                st = str(me["report_status"].iloc[-1]) if len(me) else ""
                status = st if st in ("Questionable", "Doubtful", "Out") else None
            if status == "Out":             # Sleeper voids his leg: named below the tables, never ranked (DECISIONS #243)
                ruled_out.setdefault(got["stub"]["player"], []).append(card.SHOW[p_["market"]][0])
                continue
            for sd in ("over", "under"):
                r = S.side_row(got["pl"], c, sd, got["shown"], got["stub"], bars["under" if sd == "over" else "over"])
                if status:
                    r["flags"].insert(0, status)
                if r["lineup_out"]:                    # carried only by marked games (DECISIONS #247)
                    lineup_out.append(f"{got['stub']['player']} {card.SHOW[p_['market']][0]} {sd}: {r['lineup_out']}")
                elif r["bar"] is None:
                    unlisted("bar out of range")
                elif c["usual"] is None:
                    unlisted("no recent average")
                elif not r["passes"]:
                    unlisted("recent workload short of the bar")
                r["_lookup"] = (got["stub"]["player"], got["stub"]["team"], wk)
                rows.append(r)
    weeks = sorted({int(w) for w in games["week"]})
    if not n_posted and not problems:
        # nothing saved for the week: say so and fail, never a list that reads as "no leg at the bar" and a
        # grade that reads as "nothing to grade" (DECISIONS #246)
        raise SystemExit(f"No Sleeper lines are saved for {label}, week {', '.join(map(str, weeks))}: nothing to "
                         f"screen{' or grade' if a.grade else ''}. Lines are saved by `python nfl.py calc capture` "
                         f"before kickoff; calc's captures are read from {lines.CALC_LINES}.")
    L = [f"**Smallest ask at the price · {label} · week {', '.join(map(str, weeks))}**", "", S.HEADER, "", S.ORDER, ""]
    for _, g in games.iterrows():
        L += game_header(b, g, season, fixed, now) + [""]
    L += [f"Quotes: the newest saved Sleeper quote before each kickoff (each card shows its time). Release {_release()}."]
    if replay:
        L += ["", S.REPLAY]
    elif len(started):
        L += ["", "Already kicked off, left out: " + ", ".join(
            f"{g['away_team']} at {g['home_team']} ({S.clock(g['kickoff_utc'])})" for _, g in started.iterrows()) + "."]
    for x in problems:
        L += ["", f"Check first: {x}."]
    ranked = {sd: S.rank([r for r in rows if r["side"] == sd])[:S.TOP] for sd in ("over", "under")}
    for sd, title in (("over", "Overs"), ("under", "Unders")):
        L += [""] + S.table(ranked[sd], f"{title} (top {S.TOP})")
    if lines_out:
        L += ["", "Lines not ranked: " + ", ".join(f"{n} {why}" for why, n in sorted(lines_out.items())) + "."]
    if ruled_out:
        L += ["", "Not listed, ruled Out: " + "; ".join(f"{n} ({', '.join(m)})" for n, m in sorted(ruled_out.items()))
              + "."]
    if lineup_out:
        L += ["", "Not listed, lineup changed:"] + [f"- {x}" for x in lineup_out]
    if sides_out:
        L += ["", "Sides not listed (an Over and an Under count separately): "
              + ", ".join(f"{n} {why}" for why, n in sorted(sides_out.items())) + "."]
    if a.grade:
        L += [""] + _grade_screen(S, season, ranked, label)
    key = "md_game" if a.format == "md" else "text"
    gap = ["", "---", ""] if key == "md_game" else [""]
    for sd in ("over", "under"):
        for r in ranked[sd][:3]:
            name, team, wk = r["_lookup"]
            try:
                L += gap + [build_card(b, name, r["market"], sd, team=team, season=season, week=wk, lookup=lookup)[key]]
            except (player.NotFound, DataError, SystemExit) as ex:
                L += gap + [f"{name} {card.SHOW[r['market']][0]} {sd}: card not built: {ex}"]
            L += ["", S.checks(r, key == "md_game")]      # the row's ✓ and ✗ under its card
    return (_md_lead(warn) if key == "md_game" else warn) + "\n".join(L)


def game_header(b, g, season: int, fixed: dict, now) -> list[str]:
    """One game's matchup, printed once above its legs (the user, 2026-10-11, DECISIONS #243): the spread
    and total, all four unit pairings (both teams' run and pass offense against the other's defense,
    whatever legs are listed), each team's quarterback line, and the players ruled Out, Doubtful or
    Questionable. A grade earned with a quarterback who is out says so. Display only: every part that
    cannot be read says why, never stops the run."""
    from . import screen as S
    wk, away, home = int(g["week"]), g["away_team"], g["home_team"]
    try:
        gl, why = _game_line(g, season, wk, pd.Timestamp(g["kickoff_utc"]) <= pd.Timestamp(now))
    except Exception as ex:  # noqa: BLE001 -- display only
        gl, why = None, f"{type(ex).__name__}: {str(ex)[:60]}"
    L = [f"**{away} at {home}** · {S.clock(g['kickoff_utc'])} · {card.spread_sentence(gl, why)}", "",
         "| Unit matchup | Grades |", "|---|---|"]
    qb = {t: _display_text(lambda t=t: qb_today(b, t, season, wk)) for t in (away, home)}
    for off, dfn in ((away, home), (home, away)):
        out_qb = qb[off].removesuffix(" ruled Out.") if qb[off].endswith(" ruled Out.") else ""
        for kind in ("run", "pass"):
            gr = _display(lambda off=off, dfn=dfn, kind=kind: matchup.grade_pair(b, off, dfn, kind, season, wk, fixed))
            if gr.get("off") and gr.get("def"):
                cell = f"{gr['off']} vs {gr['def']}" + (f" (graded with {out_qb}, who is Out)" if out_qb else "")
            else:
                cell = gr.get("note") or "not available"
            L.append(f"| {off} {kind} offense vs {dfn} {kind} defense | {card._cell(cell)} |")
    L.append("")
    for t in (away, home):
        if qb[t]:
            L.append(f"{t} quarterback: {qb[t]}")
    inj = _display(lambda: _injuries(b, season))
    if isinstance(inj, dict):
        L.append(f"Injury report not read: {inj.get('note', 'not available')}")
        return L
    for t in (away, home):
        tr = inj[(inj["week"] == wk) & (inj["team"] == t)]
        if tr.empty:
            L.append(f"{t}: the week's injury report is not out yet.")
            continue
        out = sorted(tr[tr["report_status"] == "Out"]["full_name"].dropna().unique())
        q = tr[tr["report_status"].isin(["Doubtful", "Questionable"])].dropna(subset=["full_name"])
        qs = sorted(f"{n} ({s})" for n, s in zip(q["full_name"], q["report_status"]))
        L.append(f"{t} Out: {', '.join(out) or 'none'}. Doubtful or Questionable: {', '.join(qs) or 'none'}.")
    return L


def _grade_screen(S, season: int, ranked: dict, label: str) -> list[str]:
    """Grade the listed legs with the journal's own grader, in a throwaway journal (never the betting
    record): the same stats file, name join and push rule as every logged bet."""
    import tempfile
    rows = S.journal_rows(ranked["over"], label) + S.journal_rows(ranked["under"], label)
    if not rows:
        return ["**Results**", "", "No leg was listed, so nothing to grade."]
    keep = journal.JOURNAL_ROOT
    with tempfile.TemporaryDirectory() as tmp:
        try:
            journal.JOURNAL_ROOT = Path(tmp)
            journal.write(season, rows)
            journal.grade(season)
            graded = journal.read(season)
        finally:
            journal.JOURNAL_ROOT = keep
    return S.results(graded, ranked["over"] + ranked["under"])


def game(a) -> str:
    """Every posted line of one game in one run (DECISIONS #236): the data loads once, then a
    summary row per line (each side's bar, as its card prints it, beside his last-4 average) and
    the full cards for the players asked for. A card is built exactly as `leg` builds it."""
    fixed = settings.load()["fixed"]
    season = a.season or F.current_season()
    away, home = _matchup(a.matchup)
    b, warn = _bundle(season, fixed)
    g = _game_between(b.schedule, away, home, season, a.week)
    wk = int(g["week"])
    lookup = lines.LineLookup(b.rosters)
    posted, unread, bad = lookup.posted({"season": season, "week": wk, "kickoff_utc": g["kickoff_utc"],
                                    "game_id": g["game_id"], "home_team": home, "away_team": away})
    head = f"{away} at {home}, week {wk}: "
    warn += "".join(f"A saved-quote file could not be read and was left out: {x}\n" for x in bad)
    if not posted:
        return warn + head + "no saved Sleeper line before kickoff. Run `capture` first."
    built, rows = [], []
    for p in posted:
        try:
            got = build_card(b, p["player"], p["market"], "over", team=p["team"], season=season, week=wk, lookup=lookup)
        except (player.NotFound, DataError, SystemExit) as ex:   # SystemExit: build_card's "not a market here"
            rows.append((p, None, f"not built: {ex}"))
            continue
        if got["stub"]["game_id"] != g["game_id"]:
            rows.append((p, None, f"not built: the name matched {got['stub']['player']} of {got['stub']['team']}"))
            continue
        built.append((p, got))
        rows.append((p, got, None))
    order = {away: 0, home: 1}
    rows.sort(key=lambda x: (order.get((x[1]["stub"]["team"] if x[1] else x[0]["team"]) or "", 2),
                             str(x[1]["stub"]["player"] if x[1] else x[0]["player"]), MARKET_ORDER.index(x[0]["market"])))
    L = [head + f"{len(rows)} posted lines (Sleeper quotes saved before kickoff)."
         + (f" {unread} saved rows could not be read and were left out." if unread else ""), ""]
    L += game_header(b, g, season, fixed, dt.datetime.now(dt.timezone.utc)) + [""]
    L += [f"| Player | Bet | Line | Over needs | Under needs | Last-{int(fixed['usual_games'])} average |",
         "|---|---|---|---|---|---|"]
    for p, got, why in rows:
        bet = card.SHOW[p["market"]][0]
        if got is None:
            L.append(f"| {_cell(p['player'])} | {bet} | -- | {_cell(why)} | | |")
            continue
        name_ = f"{got['stub']['player']} ({got['stub']['team']})"
        if got["not_enough"]:
            L.append(f"| {name_} | {bet} | {got['line'] if got['line'] is not None else '--'} | "
                     f"not enough data: {_cell(got['reason'])} | | |")
        elif not got["ready"]:
            L.append(f"| {name_} | {bet} | -- | {_cell(got['reason'] or 'no usable quote')} | | |")
        else:
            c = got["c"]
            avg = card.d1(c["usual"]) if c["usual"] is not None else "--"
            L.append(f"| {name_} | {bet} | {got['line']:g} | {_bar_cell(c, 'needed_over', 'over', p['market'])} | "
                     f"{_bar_cell(c, 'needed_under', 'under', p['market'])} | {avg} |")
    def asked(p, got):
        return any(_named(x, got["stub"]["player"]) or _named(x, p["player"]) for x in a.player)
    sides = ["over", "under"] if a.side == "both" else [a.side]
    pick = [(p, got) for p, got in built if a.all or asked(p, got)]
    pick.sort(key=lambda x: (order.get(x[1]["stub"]["team"], 2), x[1]["stub"]["player"],
                             MARKET_ORDER.index(x[0]["market"])))
    unbuilt = [p for p, got, _ in rows if got is None]
    for x in sorted(a.player):
        if any(_named(x, got["stub"]["player"]) or _named(x, p["player"]) for p, got in built):
            continue
        if any(_named(x, p["player"]) for p in unbuilt):
            L += ["", f"No card for {x}: the summary row says why."]
        else:
            L += ["", f"No posted line in this game for: {x}."]
    key = "md_game" if getattr(a, "format", "text") == "md" else "text"
    gap = ["", "---", ""] if key == "md_game" else [""]          # one divider between chat cards
    for p, got in pick:
        for side in sides:
            if side == "over":
                L += gap + [got[key]]
                continue
            try:
                L += gap + [build_card(b, got["stub"]["player"], p["market"], side, team=got["stub"]["team"],
                                       season=season, week=wk, lookup=lookup)[key]]
            except (player.NotFound, DataError, SystemExit) as ex:
                L += gap + [f"{got['stub']['player']} {card.SHOW[p['market']][0]} {side}: card not built: {ex}"]
    if not pick and not a.player:
        L += ["", "Cards: name players with --player, or print every line's cards with --all."]
    return (_md_lead(warn) if key == "md_game" else warn) + "\n".join(L)


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
    if a.payout is None and not getattr(a, "dry_run", False):
        raise SystemExit("--payout (the total Sleeper shows for your entry) is needed to log it; a --dry-run "
                         "can work it out from the legs' prices")
    for name_, v in (("--stake", a.stake), ("--payout", a.payout)):
        if v is None:
            continue
        try:
            number(v, name_)
        except DataError as ex:
            raise SystemExit(str(ex)) from None
    if len(legs) < 2:
        raise SystemExit("a Power Play has at least two legs")
    if not a.stake > 0:
        raise SystemExit(f"--stake must be above 0; got {a.stake}")
    if a.payout is not None and not a.stake < a.payout:
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
    md = getattr(a, "format", "text") == "md"
    if md:
        warn = _md_lead(warn)
    if problems:
        if md:                                  # a list, so markdown keeps one reason per line
            return warn + "Not logged:\n\n" + "\n".join(f"- {p}" for p in problems)
        return warn + "Not logged:\n" + "\n".join(f"  {p}" for p in problems)
    week = weeks.pop()
    views = [summary.leg_view(g["stub"]["player"], g["stub"]["market"], side, g["c"], g["stub"]["team"], g["opp"],
                              g["stub"]["game_id"]) for side, g in cards]
    payout = a.payout if a.payout is not None else summary.payout_from_legs(a.stake, views)
    entry_text = (summary.render_md(views, a.stake, payout, a.payout is None, [g["md"] for _, g in cards]) if md
                  else summary.render(views, a.stake, payout, payout_from_legs=a.payout is None))
    jlegs = [(g["stub"]["player"], g["stub"]["market"], side, g["line"], g["stub"]["team"]) for side, g in cards]
    try:
        rows = journal.make_power_play(jlegs, stake=a.stake, payout=payout, angle=a.angle, why=a.why,
                                       season=season, week=week)
    except ValueError as ex:
        return warn + f"Not logged: {ex}"
    for r, (side, g) in zip(rows, cards):
        r.update(journal_fields(side, g))
    # the text layout prints the cards, then the summary; the chat layout puts its table first (render_md)
    text = entry_text if md else "\n\n".join(g["text"] for _, g in cards) + "\n\n" + entry_text
    if getattr(a, "dry_run", False):
        # the same serialisation journal.write uses, line for line
        added = "\n".join(json.dumps(r, sort_keys=True) for r in rows)
        if a.payout is None:                   # the payout was worked out, not Sleeper's: no journal preview
            return (warn + text + "\n\nDRY RUN: nothing written. No journal preview: the payout above was worked "
                    "out from the legs' prices; logging needs --payout, the total Sleeper shows for your entry.")
        if md:                                 # machine lines: fenced, so markdown keeps one row per line
            added = f"```json\n{added}\n```"
        return (warn + text + f"\n\nDRY RUN: nothing written. These {len(rows)} lines would be added to "
                f"{journal.journal_path(season)}:\n{added}")
    journal.write(season, journal.read(season) + rows)
    return (warn + text + f"\n\nLogged entry {rows[0]['entry_id']}: {len(rows)} legs, {summary.money(a.stake)} to "
            f"{summary.money(payout)}, in {journal.journal_path(season)}.")


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
