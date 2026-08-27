"""Gate semantics: execute checks from the committed state/week_plan.json.

GitHub cron is UTC and best-effort (3-15 min late, occasionally skipped), so
nothing relies on a single tick: every check's due time is target minus 10
minutes and it stays eligible for ~45 minutes. The 15-minute gate workflow
gives at-least-once execution; the done flag plus content-hash idempotent
delivery gives at-most-once effect.

Statuses: pending (not yet due) | due (inside the window) | expired |
done (already executed).
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .clock import PT

log = logging.getLogger("manager")

EARLY_MIN = 10       # due = target - 10 min (late-cron buffer)
WINDOW_MIN = 45      # eligible for this long after due


def plan_path(root: str | Path = ".") -> Path:
    return Path(root) / "state" / "week_plan.json"


def to_plan_check(job: dict) -> dict:
    """Module 0 job -> serializable plan entry with gate fields."""
    target = job["when"]
    due = target - timedelta(minutes=EARLY_MIN)
    entry = {
        "id": job["id"], "kind": job["kind"], "info": job.get("info", ""),
        "target_pt": target.astimezone(PT).isoformat(),
        "due_utc": due.astimezone(timezone.utc).isoformat(),
        "due_pt": due.astimezone(PT).isoformat(),
        "window_min": WINDOW_MIN, "done": False,
    }
    for k in ("teams", "kickoff"):
        if k in job:
            entry[k] = job[k]
    return entry


def check_status(check: dict, now_utc: datetime) -> str:
    if check.get("done"):
        return "done"
    due = datetime.fromisoformat(check["due_utc"])
    if now_utc < due:
        return "pending"
    if now_utc <= due + timedelta(minutes=check.get("window_min", WINDOW_MIN)):
        return "due"
    return "expired"


def write_plan(week: int, jobs: list[dict], root: str | Path = ".") -> Path:
    path = plan_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = {}
    if path.exists():
        try:
            old = json.loads(path.read_text(encoding="utf-8"))
            if old.get("week") == week:  # re-plan same week keeps done flags
                existing = {c["id"]: c.get("done", False) for c in old.get("checks", [])}
        except ValueError:
            pass
    checks = [to_plan_check(j) for j in jobs]
    for c in checks:
        c["done"] = existing.get(c["id"], False)
    path.write_text(json.dumps({
        "week": week,
        "generated_pt": datetime.now(tz=PT).isoformat(),
        "checks": checks,
    }, indent=1), encoding="utf-8")
    return path


def gate_hours_utc(checks: list[dict]) -> list[list[int]]:
    """(iso_weekday, hour) UTC pairs the gate must tick in — the planner
    commits these so no-op ticks outside windows exit in seconds."""
    hours = set()
    for c in checks:
        due = datetime.fromisoformat(c["due_utc"])
        end = due + timedelta(minutes=c.get("window_min", WINDOW_MIN) + 15)
        t = due.replace(minute=0)
        while t <= end:
            hours.add((t.isoweekday(), t.hour))
            t += timedelta(hours=1)
    return sorted([d, h] for d, h in hours)


def run_gate(dry_run: bool = False, root: str | Path = ".") -> dict:
    """One tick: execute every due-and-not-done check; mark done; save."""
    from . import jobs as jobs_mod  # late import: gate math stays test-light

    path = plan_path(root)
    if not path.exists():
        log.warning("gate: no week plan committed yet")
        return {"ran": 0, "note": "no plan"}
    plan = json.loads(path.read_text(encoding="utf-8"))
    now = datetime.now(tz=timezone.utc)
    ran, statuses = 0, {}
    for check in plan.get("checks", []):
        status = check_status(check, now)
        statuses[check["id"]] = status
        if status != "due":
            continue
        job = dict(check)
        job["when"] = datetime.fromisoformat(check["target_pt"])
        log.info("gate: executing %s (%s)", check["id"], check["kind"])
        jobs_mod.run_job(job, dry_run=dry_run)
        check["done"] = True   # even a failed run counts — _safe() emailed the
        ran += 1               # error; retrying a crashing check every 15 min spams
    if ran:
        path.write_text(json.dumps(plan, indent=1), encoding="utf-8")
    pending = sum(1 for s in statuses.values() if s == "pending")
    log.info("gate: ran %d, %d pending", ran, pending)
    return {"ran": ran, "pending": pending, "statuses": statuses}
