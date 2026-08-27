"""Module 0 — schedule-driven trigger planner.

Fixed cron times are the failure mode: player locks follow kickoffs, and 2026
has a Wednesday opener, 6:30 AM PT international kickoffs, and December
Saturday slates. Every week's jobs are computed HERE from the real schedule,
as pure functions over (week, games, my teams, opponent teams) so the lock
math is unit-testable without a network.

All datetimes are aware, Pacific.
"""

from __future__ import annotations

from datetime import datetime, time, timedelta

from .clock import PT, fmt, inactives_time

# Fixed-by-league-facts anchors (Pacific). Waivers process ~9:00 PM PT Tuesday
# (daily_waivers_hour 0 ET Wednesday); brief lands 5:00 PM, bids due 7:00 PM.
WAIVER_BRIEF = time(17, 0)
WAIVER_DEADLINE = time(19, 0)
SCOUT = time(12, 0)          # Friday
SWEEP_HOURS = (8, 16)        # Wed..Sat twice-daily injury sweeps
PLAN_DEFAULT = time(7, 30)   # Sunday plan pass (normal weeks land exactly here)
PLAN_FLOOR = time(4, 0)
SLATE_CHECK_AFTER_INACTIVES_MIN = 10
PLAN_BEFORE_INACTIVES_MIN = 60


def relevant_slates(games: list[dict], my_teams: set[str],
                    opp_teams: set[str]) -> list[dict]:
    """Distinct kickoff datetimes among games involving my or my opponent's
    players. Slate = everything locking at the same moment."""
    interest = my_teams | opp_teams
    slates: dict[datetime, dict] = {}
    for g in games:
        mine = g["teams"] & interest
        if not mine:
            continue
        s = slates.setdefault(g["kickoff"], {"kickoff": g["kickoff"], "teams": set()})
        s["teams"] |= mine
    return sorted(slates.values(), key=lambda s: s["kickoff"])


def _at(day: datetime, t: time) -> datetime:
    return datetime.combine(day.date(), t, tzinfo=PT)


def compute_week_plan(week: int, monday: datetime, games: list[dict],
                      my_teams: set[str], opp_teams: set[str]) -> list[dict]:
    """The week's jobs: [{id, kind, when(aware PT), info}]. Deterministic ids so
    re-registration replaces rather than duplicates."""
    jobs: list[dict] = []
    slates = relevant_slates(games, my_teams, opp_teams)

    def add(kind: str, when: datetime, info: str, **payload):
        jobs.append({"id": f"wk{week}:{kind}:{when.strftime('%m%dT%H%M')}",
                     "kind": kind, "when": when, "info": info, **payload})

    tue = monday + timedelta(days=1)
    add("waiver_brief", _at(tue, WAIVER_BRIEF), "waiver brief (bids due 7:00 PM PT)")
    add("scout", _at(monday + timedelta(days=4), SCOUT), "opponent scout")

    for d in range(2, 6):  # Wed..Sat
        day = monday + timedelta(days=d)
        for h in SWEEP_HOURS:
            add("injury_sweep", _at(day, time(h, 0)), "injury designation sweep")

    # one lineup plan pass per day that has a relevant slate, before that day's
    # earliest inactives — this is what makes international/Wednesday weeks work
    by_day: dict = {}
    for s in slates:
        by_day.setdefault(s["kickoff"].date(), []).append(s)
    for day, day_slates in sorted(by_day.items()):
        earliest = min(s["kickoff"] for s in day_slates)
        plan_at = inactives_time(earliest) - timedelta(minutes=PLAN_BEFORE_INACTIVES_MIN)
        floor = datetime.combine(day, PLAN_FLOOR, tzinfo=PT)
        plan_at = max(plan_at, floor)
        if day.weekday() == 6:  # Sunday: never later than the default morning pass
            plan_at = min(plan_at, datetime.combine(day, PLAN_DEFAULT, tzinfo=PT))
        add("lineup_plan", plan_at, f"lineup plan pass ({day.strftime('%A')})")

    for s in slates:
        check = inactives_time(s["kickoff"]) + timedelta(minutes=SLATE_CHECK_AFTER_INACTIVES_MIN)
        add("slate_check", check,
            f"inactives check — {', '.join(sorted(s['teams']))} lock {fmt(s['kickoff'])}",
            teams=sorted(s["teams"]), kickoff=s["kickoff"].isoformat())

    jobs.sort(key=lambda j: j["when"])
    return jobs


def render_week_plan(week: int, jobs: list[dict]) -> str:
    """The Monday 'week plan' message — a silent scheduler failure is visible
    by this message's absence."""
    lines = [f"**Week {week} plan** — {len(jobs)} checks scheduled:"]
    lines += [f"- {fmt(j['when'])} — {j['info']}" for j in jobs]
    lines.append("(waiver bids due **7:00 PM PT Tuesday**; healthcheck daily 8:00 AM PT)")
    return "\n".join(lines)
