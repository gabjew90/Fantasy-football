"""Long-lived APScheduler process (America/Los_Angeles).

Static jobs: Monday 6:00 AM planner, daily 8:00 AM healthcheck. Everything
else is registered dynamically by the planner from the real schedule
(Module 0) with deterministic ids, so restarts and re-runs converge instead
of duplicating. The planner posts the week plan; silence = broken.
"""

from __future__ import annotations

import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger

from . import jobs as jobs_mod
from .clock import PT, now_pt

log = logging.getLogger("manager")


def setup_logging(log_dir: str | Path) -> None:
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(Path(log_dir) / "manager.log",
                                  maxBytes=2_000_000, backupCount=3, encoding="utf-8")
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    fmt.converter = lambda ts: datetime.fromtimestamp(ts, tz=PT).timetuple()
    handler.setFormatter(fmt)
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(handler)
    root.addHandler(logging.StreamHandler())


def register_week(sched: BlockingScheduler, dry_run: bool = False) -> int:
    """(Re)compute this week's plan and register its jobs. Returns job count."""
    plan = jobs_mod.plan_week(dry_run=dry_run)
    prefix = f"wk{plan['week']}:"
    # drop every dynamic job that is not in the fresh plan (incl. stale weeks)
    keep = {j["id"] for j in plan["jobs"]}
    for job in sched.get_jobs():
        if ":" in job.id and job.id not in keep and not job.id.startswith("static:"):
            sched.remove_job(job.id)
    n = 0
    for j in plan["jobs"]:
        if j["when"] <= now_pt():
            continue  # in the past (mid-week start) — planner already ran catch-up logic
        sched.add_job(jobs_mod.run_job, DateTrigger(run_date=j["when"]),
                      id=j["id"], args=[j, dry_run], replace_existing=True,
                      misfire_grace_time=600)
        n += 1
    log.info("registered %d jobs for week %s (prefix %s)", n, plan["week"], prefix)
    return n


def run(dry_run: bool = False) -> None:
    sched = BlockingScheduler(timezone="America/Los_Angeles")
    sched.add_job(lambda: register_week(sched, dry_run),
                  CronTrigger(day_of_week="mon", hour=6, minute=0),
                  id="static:planner", replace_existing=True, misfire_grace_time=3600)
    sched.add_job(jobs_mod.healthcheck, CronTrigger(hour=8, minute=0),
                  id="static:health", args=[sched, dry_run],
                  replace_existing=True, misfire_grace_time=3600)
    register_week(sched, dry_run)  # immediate plan on process start
    log.info("scheduler starting (PT) — %d jobs", len(sched.get_jobs()))
    sched.start()
