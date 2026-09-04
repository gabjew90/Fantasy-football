"""`python -m manager` — entrypoints.

  python -m manager gate                      # one 15-min gate tick (Actions)
  python -m manager cron                      # weekly.yml dispatcher (PT-guarded)
  python -m manager cron --job waivers        # force one weekly job (dispatch)
  python -m manager --dry-run --module all    # full pipeline vs live data, stdout
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime

from dotenv import load_dotenv

MODULES = ("plan", "waivers", "injuries", "lineup", "scout", "trade", "health", "all")


def _setup_logging() -> None:
    from .clock import PT
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    fmt.converter = lambda ts: datetime.fromtimestamp(ts, tz=PT).timetuple()
    h = logging.StreamHandler()
    h.setFormatter(fmt)
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(h)


def main() -> int:
    if sys.platform == "win32":  # emoji in briefs vs cp1252 consoles
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    load_dotenv()
    _setup_logging()
    ap = argparse.ArgumentParser(prog="manager")
    ap.add_argument("command", nargs="?", default="module",
                    choices=("gate", "cron", "module"))
    ap.add_argument("--module", choices=MODULES, default=None)
    ap.add_argument("--job", choices=tuple(k for k in MODULES if k != "all"),
                    default=None, help="cron: force one job regardless of window")
    ap.add_argument("--dry-run", action="store_true",
                    help="full pipeline against live data; print instead of email")
    ap.add_argument("--league", default=None,
                    help="league name; overrides DRAFTKIT_LEAGUE / default_league")
    ap.add_argument("--week", type=int, default=None,
                    help="render as if it were this NFL week (module runs only)")
    args = ap.parse_args()

    if args.week is not None and args.command != "module":
        ap.error("--week is for 'module' runs only: pinning gate/cron to a stale "
                 "week would make the live manager act on the wrong week")

    from . import jobs
    from .context import configure
    configure(league=args.league, week=args.week)

    if args.command == "gate":
        from .gate import run_gate
        result = run_gate(dry_run=args.dry_run)
        print(f"[gate] ran {result.get('ran', 0)}, pending {result.get('pending', 0)}")
        return 0

    if args.command == "cron":
        force = {"plan": "plan", "waivers": "waivers", "scout": "scout",
                 "lineup": "lineup", "health": "health"}.get(args.job or "", None)
        ran = jobs.cron_tick(dry_run=args.dry_run, force=force)
        print(f"[cron] ran: {ran or 'nothing (outside all windows)'}")
        return 0

    if not args.module:
        ap.error("--module is required unless command is 'gate' or 'cron'")

    def do(name: str) -> None:
        if name == "plan":
            plan = jobs.plan_week(dry_run=args.dry_run)
            print(f"\n[plan] {len(plan['jobs'])} checks computed for week {plan['week']}")
        elif name == "waivers":
            jobs.waiver_job(dry_run=args.dry_run)
        elif name == "injuries":
            jobs.sweep_job(dry_run=args.dry_run)
        elif name == "lineup":
            jobs.lineup_job(dry_run=args.dry_run)
        elif name == "scout":
            jobs.scout_job(dry_run=args.dry_run)
        elif name == "trade":
            from .context import league_context
            from .trade_radar import build
            print(build(league_context(), jobs.get_store()))
        elif name == "health":
            jobs.healthcheck(dry_run=args.dry_run)

    if args.module == "all":
        # scout before lineup so ceiling/floor mode is fresh; plan first (spec order)
        for m in ("plan", "waivers", "injuries", "scout", "lineup"):
            do(m)
        print("\n[all] trade radar is appended inside the waiver brief; healthcheck "
              "runs daily via weekly.yml")
    else:
        do(args.module)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
