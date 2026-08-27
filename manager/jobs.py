"""Job bodies: everything the scheduler (or --module) actually runs.

Each job builds a fresh league context, does its work, and delivers. A job
never raises out — failures log, post an error line, and leave state intact
for the next run.
"""

from __future__ import annotations

import logging
import traceback
from datetime import datetime, time, timedelta
from pathlib import Path

from draftkit.config import Config

from . import games as games_mod
from . import injuries, lineup_opt, scout, trade_radar, triggers, waiver_brief
from .clock import PT, fmt, now_pt
from .context import league_context
from .deliver import deliver
from .store import Store

log = logging.getLogger("manager")

REPORT_DIR = Path("reports/manager")


def get_store() -> Store:
    cfg = Config.load()
    return Store(Path(cfg.path("processed")).parent / "manager" / "state.db")


def _write_report(name: str, body: str) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    (REPORT_DIR / f"{name}.md").write_text(body, encoding="utf-8")


def _safe(fn, *args, **kw):
    try:
        return fn(*args, **kw)
    except Exception:  # noqa: BLE001
        log.error("job failed:\n%s", traceback.format_exc())
        try:
            deliver(get_store(), f"error:{fn.__name__}", "⚠ manager job failed",
                    f"`{fn.__name__}` raised:\n```\n{traceback.format_exc()[-800:]}\n```")
        except Exception:  # noqa: BLE001
            pass
        return None


def plan_week(dry_run: bool = False) -> dict:
    """Module 0: compute the week's triggers, store txn history, post the plan."""
    ctx = league_context()
    store = get_store()
    week = ctx["week"]
    schedule = games_mod.load(ctx["cfg"], int(ctx["state"]["season"]))
    wk_games = games_mod.week_games(schedule, week)
    today = now_pt()
    monday = datetime.combine(today.date() - timedelta(days=today.weekday()),
                              time(6, 0), tzinfo=PT)
    jobs = triggers.compute_week_plan(week, monday, wk_games,
                                      ctx["my_teams"], ctx["opp_teams"])
    # accrue transaction history for FAAB accounting
    hist = store.get("txn_history", [])
    from draftkit.briefs import get_transactions
    try:
        wk_txns = get_transactions(ctx["client"], ctx["cfg"].league_id, week)
        if len(hist) < week:
            hist += [[] for _ in range(week - len(hist))]
        hist[week - 1] = wk_txns
        store.set("txn_history", hist)
    except Exception:  # noqa: BLE001
        log.warning("transaction history fetch failed")

    body = triggers.render_week_plan(week, jobs)
    deliver(store, f"plan:{week}", f"Week {week} plan", body, dry_run=dry_run)
    _write_report("week_plan", body)
    return {"week": week, "jobs": jobs}


def run_job(job: dict, dry_run: bool = False) -> None:
    kind = job["kind"]
    log.info("firing %s (%s)", job["id"], job.get("info", ""))
    if kind == "waiver_brief":
        _safe(waiver_job, dry_run)
    elif kind == "scout":
        _safe(scout_job, dry_run)
    elif kind == "injury_sweep":
        _safe(sweep_job, dry_run)
    elif kind == "lineup_plan":
        _safe(lineup_job, dry_run)
    elif kind == "slate_check":
        _safe(slate_job, job.get("teams", []), job.get("kickoff"), dry_run)


def waiver_job(dry_run: bool = False) -> None:
    ctx = league_context()
    store = get_store()
    body = waiver_brief.build(ctx, store)
    body += "\n\n" + trade_radar.build(ctx, store)
    deliver(store, f"waivers:{ctx['week']}", f"Waivers — week {ctx['week']}",
            body, dry_run=dry_run)
    _write_report("waivers", body)


def scout_job(dry_run: bool = False) -> None:
    ctx = league_context()
    store = get_store()
    body = scout.build(ctx, store)
    deliver(store, f"scout:{ctx['week']}", f"Scout — week {ctx['week']}",
            body, dry_run=dry_run)
    _write_report("scout", body)


def lineup_job(dry_run: bool = False) -> None:
    ctx = league_context()
    store = get_store()
    body = lineup_opt.build(ctx, store)
    deliver(store, f"lineup:{ctx['week']}", f"Lineup — week {ctx['week']}",
            body, dry_run=dry_run)
    _write_report("lineup", body)


def sweep_job(dry_run: bool = False) -> None:
    ctx = league_context()
    store = get_store()
    alerts = injuries.sweep(ctx, store)
    if alerts:
        key = f"sweep:{ctx['week']}:{now_pt().strftime('%m%d%H')}"
        deliver(store, key, "Injury changes", "\n".join(alerts), dry_run=dry_run)
    elif dry_run:
        print("[sweep] no designation changes since last sweep")


def slate_job(teams: list[str], kickoff_iso: str | None, dry_run: bool = False) -> None:
    ctx = league_context()
    store = get_store()
    kickoff = (datetime.fromisoformat(kickoff_iso) if kickoff_iso else now_pt())
    alerts = injuries.slate_check(ctx, store, teams, kickoff)
    if alerts:
        key = f"slate:{ctx['week']}:{kickoff.strftime('%m%d%H%M')}"
        deliver(store, key, f"⚠ INACTIVES — lock {fmt(kickoff)}",
                "\n".join(alerts), dry_run=dry_run)
    elif dry_run:
        print(f"[slate {teams}] all starters active")


def healthcheck(sched=None, dry_run: bool = False) -> None:
    n = len(sched.get_jobs()) if sched is not None else 0
    store = get_store()
    key = f"health:{now_pt().strftime('%Y%m%d')}"
    deliver(store, key, "alive",
            f"manager alive — {n} jobs scheduled — {fmt(now_pt())}", dry_run=dry_run)
