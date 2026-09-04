"""Job bodies: everything the workflows (or --module) actually run.

Each job builds a fresh league context, does its work, and emails the result
with a decision-sufficient subject. A job never raises out — failures log,
email an error line, and leave state intact for the next tick.
"""

from __future__ import annotations

import json
import logging
import re
import traceback
from datetime import datetime, time, timedelta, timezone
from pathlib import Path

from . import games as games_mod
from . import gate as gate_mod
from . import (injuries, lineup_opt, scout, trade_radar, trade_watch,
               triggers, waiver_brief)
from .clock import PT, fmt, minutes_until, now_pt
from .context import league_context
from .deliver import deliver
from .store import Store

log = logging.getLogger("manager")

REPORT_DIR = Path("reports/manager")


# Set once from the CLI, same rationale as context._LEAGUE: get_store() is
# called from nine places including _safe()'s error path, and a partial
# thread-through is how one of them ends up writing state during a rehearsal.
_DRY_RUN = False


def configure(dry_run: bool = False) -> None:
    global _DRY_RUN
    _DRY_RUN = bool(dry_run)


def get_store() -> Store:
    return Store(Path("state"), read_only=_DRY_RUN)


def _write_report(name: str, body: str) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    (REPORT_DIR / f"{name}.md").write_text(body, encoding="utf-8")


def _safe(fn, *args, **kw):
    try:
        return fn(*args, **kw)
    except Exception:  # noqa: BLE001
        log.error("job failed:\n%s", traceback.format_exc())
        try:
            deliver(get_store(), f"error:{fn.__name__}", f"manager job failed: {fn.__name__}",
                    f"`{fn.__name__}` raised:\n```\n{traceback.format_exc()[-800:]}\n```",
                    act_now=True)
        except Exception:  # noqa: BLE001
            pass
        return None


def plan_week(dry_run: bool = False) -> dict:
    """Module 0: compute the week's checks, commit state/week_plan.json (+ gate
    hours), email the plan — a dead planner is visible by the email's absence."""
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
    plan = gate_mod.build_plan(week, jobs)
    hours = gate_mod.gate_hours_utc(plan["checks"])
    if dry_run:
        # state/ is committed and read by the live gate. A rehearsal that
        # writes the week plan hands the real run a schedule it never made.
        log.info("dry run: not writing state/week_plan.json or state/gate_hours.json")
    else:
        gate_mod.write_plan(week, jobs)
        (Path("state") / "gate_hours.json").write_text(json.dumps(hours), encoding="utf-8")

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
    deliver(store, f"plan:{week}", f"Week {week} plan — {len(jobs)} checks scheduled",
            body, dry_run=dry_run)
    _write_report("week_plan", body)
    return {"week": week, "jobs": jobs}


def run_job(job: dict, dry_run: bool = False) -> None:
    kind = job["kind"]
    log.info("firing %s (%s)", job.get("id", kind), job.get("info", ""))
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


def _identity_line(ctx) -> str:
    """Who this brief is about. Carries the ROSTER ID, not just the display
    name: a name collision is exactly the failure identity resolution exists to
    catch, so a body that only named the name could still look right while
    being about the wrong team."""
    i = ctx.get("identity") or {}
    week = ctx.get("week")
    lg = getattr(ctx.get("cfg"), "league_name", "?")
    return (f"_managing {i.get('display', '?')} · roster {i.get('roster_id', '?')} · "
            f"league {lg} · week {week} · identity via {i.get('source', '?')}_\n\n")


def waiver_job(dry_run: bool = False) -> None:
    ctx = league_context()
    store = get_store()
    body = _identity_line(ctx) + waiver_brief.build(ctx, store)
    body += "\n\n" + trade_radar.build(ctx, store)
    top = re.search(r"\*\*(.+?)\*\*", body.split("## Top adds", 1)[-1])
    subject = (f"Waivers wk {ctx['week']} — top add: {top.group(1)}" if top
               else f"Waivers wk {ctx['week']}") + " — bids by 7:00 PM PT"
    deliver(store, f"waivers:{ctx['week']}", subject, body, dry_run=dry_run)
    _write_report("waivers", body)


def scout_job(dry_run: bool = False) -> None:
    ctx = league_context()
    store = get_store()
    body = _identity_line(ctx) + scout.build(ctx, store)
    s = store.get(f"scout:{ctx['week']}", {})
    subject = (f"Scout wk {ctx['week']}: {ctx['opp_name']} — margin "
               f"{s.get('margin', 0):+.0f}, win {s.get('win_prob', 0.5):.0%}")
    deliver(store, f"scout:{ctx['week']}", subject, body, dry_run=dry_run)
    _write_report("scout", body)


def lineup_job(dry_run: bool = False) -> None:
    ctx = league_context()
    store = get_store()
    body = _identity_line(ctx) + lineup_opt.build(ctx, store)
    n = body.count("\n- **") if "## Changes" in body else 0
    subject = (f"Lineup wk {ctx['week']} — {n} change(s) needed" if n
               else f"Lineup wk {ctx['week']} — no changes needed")
    deliver(store, f"lineup:{ctx['week']}", subject, body,
            dry_run=dry_run, act_now=bool(n))
    _write_report("lineup", body)


def _trade_alerts(ctx, store, dry_run: bool) -> None:
    for subject, body, urgent in trade_watch.scan(ctx, store):
        key = f"trade:{_hashkey(subject)}"
        deliver(store, key, subject, body, dry_run=dry_run, act_now=urgent)


def _hashkey(text: str) -> str:
    import hashlib
    return hashlib.sha256(text.encode()).hexdigest()[:10]


def sweep_job(dry_run: bool = False) -> None:
    ctx = league_context()
    store = get_store()
    _trade_alerts(ctx, store, dry_run)
    alerts = injuries.sweep(ctx, store)
    if alerts:
        urgent = any(a.startswith("🔴") for a in alerts)
        first = re.sub(r"[*🔴🟡🟢 ]+", " ", alerts[0]).strip()
        key = f"sweep:{ctx['week']}:{now_pt().strftime('%m%d%H')}"
        deliver(store, key, f"Injury change: {first}", "\n".join(alerts),
                dry_run=dry_run, act_now=urgent)
    elif dry_run:
        print("[sweep] no designation changes since last sweep")


def slate_job(teams: list[str], kickoff_iso: str | None, dry_run: bool = False) -> None:
    ctx = league_context()
    store = get_store()
    kickoff = (datetime.fromisoformat(kickoff_iso) if kickoff_iso else now_pt())
    alerts = injuries.slate_check(ctx, store, teams, kickoff)
    if alerts:
        # subject must be decision-sufficient from the lock screen
        first = re.sub(r"\*\*|🔴", "", alerts[0])
        instr = first.split(".")[0] + f" — locks in {minutes_until(kickoff)} min"
        key = f"slate:{ctx['week']}:{kickoff.strftime('%m%d%H%M')}"
        deliver(store, key, instr, "\n".join(alerts), dry_run=dry_run, act_now=True)
    elif dry_run:
        print(f"[slate {teams}] all starters active")


def healthcheck(dry_run: bool = False) -> None:
    store = get_store()
    # daily trade sweep rides the healthcheck so Sun-Tue trades (outside the
    # Wed-Sat injury sweeps) are still caught inside the 48h veto window
    try:
        _trade_alerts(league_context(), store, dry_run)
    except Exception:  # noqa: BLE001
        log.warning("trade watch inside healthcheck failed")
    pending = 0
    path = gate_mod.plan_path()
    if path.exists():
        plan = json.loads(path.read_text(encoding="utf-8"))
        now = datetime.now(tz=timezone.utc)
        pending = sum(1 for c in plan.get("checks", [])
                      if gate_mod.check_status(c, now) == "pending")
    key = f"health:{now_pt().strftime('%Y%m%d')}"
    deliver(store, key, f"alive — {pending} checks pending this week",
            f"manager alive — {pending} checks pending — {fmt(now_pt())}",
            dry_run=dry_run)


# -- weekly.yml dispatcher ------------------------------------------------
# GitHub cron is UTC; PT-fixed events live at two possible UTC hours across
# DST. The workflow fires at both; this guard runs the job only inside its
# PT window, and delivery idempotency absorbs the double fire.
WINDOWS = {
    # kind: (iso_weekday or None=daily, start_pt, end_pt)
    "plan":   (1, time(5, 30), time(7, 30)),
    "health": (None, time(7, 30), time(9, 30)),
    "waivers": (2, time(15, 30), time(18, 30)),
    "scout":  (5, time(11, 30), time(14, 0)),
    "lineup": (7, time(6, 0), time(8, 30)),   # Sunday backstop; gate leads
}


def cron_tick(dry_run: bool = False, force: str | None = None) -> list[str]:
    now = now_pt()
    ran = []
    for kind, (dow, start, end) in WINDOWS.items():
        if force and kind != force:
            continue
        if not force:
            if dow is not None and now.isoweekday() != dow:
                continue
            if not (start <= now.time() <= end):
                continue
        ran.append(kind)
        if kind == "plan":
            _safe(plan_week, dry_run)
        elif kind == "health":
            _safe(healthcheck, dry_run)
        elif kind == "waivers":
            _safe(waiver_job, dry_run)
        elif kind == "scout":
            _safe(scout_job, dry_run)
        elif kind == "lineup":
            _safe(lineup_job, dry_run)
    log.info("cron tick ran: %s", ran or "nothing (outside all windows)")
    return ran
