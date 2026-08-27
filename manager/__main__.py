"""`python -m manager` — entrypoints.

  python -m manager run                      # long-lived scheduler (the real thing)
  python -m manager --dry-run --module all   # full pipeline vs live data, stdout only
  python -m manager --module waivers         # one module, delivered
"""

from __future__ import annotations

import argparse
import sys

from dotenv import load_dotenv

MODULES = ("plan", "waivers", "injuries", "lineup", "scout", "trade", "health", "all")


def main() -> int:
    if sys.platform == "win32":  # emoji in briefs vs cp1252 consoles
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    load_dotenv()
    ap = argparse.ArgumentParser(prog="manager")
    ap.add_argument("command", nargs="?", default="module",
                    choices=("run", "module"), help="run = long-lived scheduler")
    ap.add_argument("--module", choices=MODULES, default=None)
    ap.add_argument("--dry-run", action="store_true",
                    help="full pipeline against live data; print instead of post")
    args = ap.parse_args()

    from draftkit.config import Config
    from .scheduler import run as run_scheduler, setup_logging

    cfg = Config.load()
    setup_logging(str(cfg.path("logs")))

    if args.command == "run":
        run_scheduler(dry_run=args.dry_run)
        return 0

    if not args.module:
        ap.error("--module is required unless command is 'run'")

    from . import jobs

    def do(name: str) -> None:
        if name == "plan":
            plan = jobs.plan_week(dry_run=args.dry_run)
            print(f"\n[plan] {len(plan['jobs'])} jobs computed for week {plan['week']}")
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
            jobs.healthcheck(None, dry_run=args.dry_run)

    if args.module == "all":
        # scout before lineup so ceiling/floor mode is fresh; plan first (spec order)
        for m in ("plan", "waivers", "injuries", "scout", "lineup"):
            do(m)
        print("\n[all] trade radar is appended inside the waiver brief; healthcheck "
              "runs daily under the scheduler")
    else:
        do(args.module)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
