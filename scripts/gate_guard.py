"""The gate workflow's cheap window guard. stdlib only: it runs before pip.

Prints `run=true` when this tick should install Python and run the gate:
  * the tick was dispatched by hand; or
  * the current UTC (iso_weekday, hour) is in state/gate_hours.json, the
    hours the planner committed for this week's checks; or
  * the committed week plan is missing or older than PLAN_MAX_AGE_DAYS --
    the planner did not run, so the gate must tick to heal it (gate.run_gate
    replans when the plan's week is not the live week).

The third rule is what was missing when the planner silently stopped on
2026-08-31: gate_hours.json kept week-1 hours and the guard faithfully
skipped everything else for two weeks.
"""
from __future__ import annotations

import datetime as dt
import json
import pathlib
import sys

PLAN_MAX_AGE_DAYS = 6


def decide(now_utc: dt.datetime, hours_text: str | None, plan_text: str | None,
           forced: bool = False) -> tuple[bool, str]:
    if forced:
        return True, "dispatched"
    try:
        hours = json.loads(hours_text) if hours_text else []
    except ValueError:
        hours = []
    if [now_utc.isoweekday(), now_utc.hour] in hours:
        return True, "gate hour"
    if not plan_text:
        return True, "no week plan"
    try:
        plan = json.loads(plan_text)
        generated = dt.datetime.fromisoformat(plan["generated_pt"])
    except (ValueError, KeyError, TypeError):
        return True, "unreadable week plan"
    age = now_utc - generated.astimezone(dt.timezone.utc)
    if age > dt.timedelta(days=PLAN_MAX_AGE_DAYS):
        return True, f"week plan is {age.days} days old"
    return False, "outside gate hours"


def main(argv: list[str]) -> int:
    forced = "--forced" in argv
    root = pathlib.Path(".")
    hours = root / "state" / "gate_hours.json"
    plan = root / "state" / "week_plan.json"
    run, why = decide(dt.datetime.now(dt.timezone.utc),
                      hours.read_text(encoding="utf-8") if hours.exists() else None,
                      plan.read_text(encoding="utf-8") if plan.exists() else None,
                      forced)
    print(f"run={'true' if run else 'false'}")
    print(f"guard: {why}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
