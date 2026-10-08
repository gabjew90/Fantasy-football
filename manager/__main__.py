"""`python -m manager` -- the local Yahoo sync, the one entrypoint left.

  python -m manager --league keefamania yahoo-sync   # pull Yahoo into state/<league>/yahoo/

The in-season cron stack this module used to drive (gate, cron, the --module
runs, vegas-refresh) was retired on 2026-10-08 (DECISIONS #212); the fantasy
commands (`nfl fantasy ...`) answer lineups, waivers and trades. yahoo-sync
stays because the fantasy commands read the synced copy on a host without
Yahoo credentials (manager.yahoo_api.read_cached).
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

PT = ZoneInfo("America/Los_Angeles")


def _setup_logging() -> None:
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    fmt.converter = lambda ts: datetime.fromtimestamp(ts, tz=PT).timetuple()
    h = logging.StreamHandler()
    h.setFormatter(fmt)
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(h)


def main() -> int:
    if sys.platform == "win32":  # non-ASCII names vs cp1252 consoles
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    load_dotenv()
    _setup_logging()
    ap = argparse.ArgumentParser(prog="manager")
    ap.add_argument("command", choices=("yahoo-sync",))
    ap.add_argument("--league", default=None,
                    help="league name; overrides DRAFTKIT_LEAGUE / default_league")
    ap.add_argument("--week", type=int, default=None,
                    help="sync this NFL week instead of the live one")
    args = ap.parse_args()

    from .context import configure
    configure(league=args.league, week=args.week)

    # The Yahoo credentials are LOCAL: this pulls every resource the fantasy
    # commands read into state/<league>/yahoo/ and the .bat commits it, so a
    # host without the credentials reads the synced copy.
    from draftkit.config import Config
    from draftkit.seasondata import nfl_state
    from . import yahoo_sync
    cfg = Config.load(league=args.league)
    if str(cfg.get("platform") or "sleeper").lower() != "yahoo":
        print(f"[yahoo-sync] {cfg.league_name} is not a Yahoo league")
        return 1
    st = nfl_state()
    week = args.week or (int(st["week"]) if st.get("season_type") == "regular" else 1)
    result = yahoo_sync.sync(cfg, week)
    for path, status in result.items():
        print(f"[yahoo-sync] {status:<8} {path}")
    return 0 if all(v == "ok" for v in result.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
