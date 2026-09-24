#!/usr/bin/env python3
"""One CLI for the two use cases (docs/plans/2026-09-24-consolidation-plan.md).

  python nfl.py status [--season S] [--week W] [--league L]
  python nfl.py props game AWAY@HOME [--markets td,...] [--week W]
  python nfl.py props slate [--week W] [--skip-started] [--markets ...]
  python nfl.py fantasy lineup --league L [--week W] [--record]
  python nfl.py fantasy scenario --league L --player NAME|ID --out NAME|ID [--week W]
  python nfl.py fantasy waiver --league L [--pos RB,WR,TE] [--horizon stream|season] [--week W]

Reports and decision records go to $NFL_OUT (default /mnt/user-data/outputs).
`--record` appends to the graded ledger. A chat session never passes it (chat
is read-only, as for the props record); the scheduled runs will, from step 6.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):  # pragma: no cover
        pass

SCRIPTS = ROOT / "props" / "engine" / "scripts"


def _season_week(season, week):
    import pandas as pd

    from core import fetch as F
    s = season or F.current_season()
    if week:
        return s, week
    g = pd.read_csv(F.schedule(), low_memory=False)
    g = g[(g.season == s) & (g.game_type == "REG")]
    unplayed = g[g.result.isna()]
    return s, int(unplayed.week.min()) if not unplayed.empty else int(g.week.max())


def cmd_status(a) -> int:
    from core import status as ST
    league = None
    if a.league:
        from draftkit.config import Config
        from fantasy.league import roster_freshness
        league = roster_freshness(Config.load(league=a.league))
    season, week = _season_week(a.season, a.week)
    print(ST.markdown(ST.week_status(season, week, league=league)))
    return 0


def cmd_props(a) -> int:
    if a.what == "game":
        if not a.game or "@" not in a.game:
            print("props game needs AWAY@HOME", file=sys.stderr)
            return 2
        away, home = a.game.split("@", 1)
        cmd = [sys.executable, str(SCRIPTS / "score_game.py"), "--away", away, "--home", home]
    else:
        cmd = [sys.executable, str(SCRIPTS / "score_week.py")]
        if a.skip_started:
            cmd.append("--skip-started")
    if a.season:
        cmd += ["--season", str(a.season)]
    if a.week:
        cmd += ["--week", str(a.week)]
    if a.markets:
        cmd += ["--markets", a.markets]
    return subprocess.run(cmd).returncode


def cmd_fantasy(a) -> int:
    if a.what == "lineup":
        from fantasy import lineup as LU
        r = LU.run(a.league, a.week, record=a.record)
    elif a.what == "waiver":
        from fantasy import waiver as WV
        pos = tuple(x.strip().upper() for x in (a.pos or "RB,WR,TE").split(",") if x.strip())
        r = WV.run(a.league, pos, a.horizon, a.week)
    else:
        if not (a.player and a.out):
            print("fantasy scenario needs --player and --out", file=sys.stderr)
            return 2
        from fantasy import scenario as SC
        try:
            r = SC.run(a.league, a.player, a.out, a.week)
        except SC.ScenarioError as ex:
            print(f"SCENARIO: {ex}", file=sys.stderr)
            return 2
    print(r.markdown)
    print(f"report: {r.report_path}\ndecision record: {r.record_path}")
    return 0


def main(argv=None) -> int:
    try:
        from dotenv import load_dotenv
        load_dotenv(ROOT / ".env")
    except ImportError:  # pragma: no cover -- the credentials simply stay absent
        pass
    ap = argparse.ArgumentParser(prog="nfl", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("status", help="what is posted for a week, and whether a run is early")
    s.add_argument("--season", type=int)
    s.add_argument("--week", type=int)
    s.add_argument("--league")
    s.set_defaults(fn=cmd_status)

    p = sub.add_parser("props", help="price a game or the slate (the props engine)")
    p.add_argument("what", choices=("game", "slate"))
    p.add_argument("game", nargs="?")
    p.add_argument("--season", type=int)
    p.add_argument("--week", type=int)
    p.add_argument("--markets", default="")
    p.add_argument("--skip-started", action="store_true")
    p.set_defaults(fn=cmd_props)

    f = sub.add_parser("fantasy", help="fantasy decisions")
    f.add_argument("what", choices=("lineup", "scenario", "waiver"))
    f.add_argument("--league", required=True)
    f.add_argument("--week", type=int)
    f.add_argument("--record", action="store_true", help="append to the graded ledger (scheduled runs only)")
    f.add_argument("--player")
    f.add_argument("--out")
    f.add_argument("--pos", help="waiver: positions, e.g. RB,WR (default RB,WR,TE)")
    f.add_argument("--horizon", choices=("stream", "season"), default="season",
                   help="waiver: stream (this week) or season (a league-winner candidate)")
    f.set_defaults(fn=cmd_fantasy)

    a = ap.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    raise SystemExit(main())
