"""Module 0 acceptance gate: lock-time math for the 2026 schedule quirks."""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from manager.clock import PT, inactives_time, kickoff_pt
from manager.triggers import compute_week_plan, relevant_slates

MON_WK1 = datetime(2026, 9, 7, 6, 0, tzinfo=PT)   # Monday of week 1
MON_DEC = datetime(2026, 12, 14, 6, 0, tzinfo=PT)  # a December Monday


def _jobs_of(jobs, kind):
    return [j for j in jobs if j["kind"] == kind]


def test_wednesday_opener_lock_math():
    # NE@SEA, Sept 9, 5:20 PM PT (8:20 PM ET)
    ko = kickoff_pt("2026-09-09", "20:20")
    assert ko == datetime(2026, 9, 9, 17, 20, tzinfo=PT)
    games = [{"teams": frozenset({"NEP", "SEA"}), "kickoff": ko}]
    jobs = compute_week_plan(1, MON_WK1, games, my_teams={"SEA"}, opp_teams=set())
    checks = _jobs_of(jobs, "slate_check")
    assert len(checks) == 1
    # inactives 3:50 PM PT, check at +10 min = 4:00 PM PT — WEDNESDAY
    assert checks[0]["when"] == datetime(2026, 9, 9, 16, 0, tzinfo=PT)
    # and a Wednesday plan pass exists BEFORE inactives
    plans = _jobs_of(jobs, "lineup_plan")
    wed_plans = [p for p in plans if p["when"].date().isoweekday() == 3]
    assert wed_plans and wed_plans[0]["when"] < inactives_time(ko)


def test_international_630am_kickoff():
    # 9:30 AM ET international game = 6:30 AM PT Sunday
    ko = kickoff_pt("2026-09-20", "09:30")
    assert ko == datetime(2026, 9, 20, 6, 30, tzinfo=PT)
    games = [{"teams": frozenset({"JAC", "MIA"}), "kickoff": ko},
             {"teams": frozenset({"ATL", "DAL"}),
              "kickoff": kickoff_pt("2026-09-20", "13:00")}]
    jobs = compute_week_plan(2, MON_WK1 + timedelta(days=7), games,
                             my_teams={"MIA", "ATL"}, opp_teams=set())
    # inactives 5:00 AM PT, slate check 5:10 AM PT
    checks = _jobs_of(jobs, "slate_check")
    assert checks[0]["when"] == datetime(2026, 9, 20, 5, 10, tzinfo=PT)
    # plan pass pulled earlier than the default 7:30 — floored at 4:00 AM
    plans = _jobs_of(jobs, "lineup_plan")
    assert plans[0]["when"] == datetime(2026, 9, 20, 4, 0, tzinfo=PT)
    assert plans[0]["when"] < inactives_time(ko)


def test_normal_sunday_lands_on_default_plan_time():
    # 1:00 PM ET main slate = 10:00 AM PT; inactives 8:30, minus 60 = 7:30 exactly
    ko = kickoff_pt("2026-09-27", "13:00")
    games = [{"teams": frozenset({"ATL", "CAR"}), "kickoff": ko}]
    jobs = compute_week_plan(3, MON_WK1 + timedelta(days=14), games,
                             my_teams={"ATL"}, opp_teams=set())
    plans = _jobs_of(jobs, "lineup_plan")
    assert plans[0]["when"] == datetime(2026, 9, 27, 7, 30, tzinfo=PT)
    checks = _jobs_of(jobs, "slate_check")
    assert checks[0]["when"] == datetime(2026, 9, 27, 8, 40, tzinfo=PT)


def test_saturday_slate_gets_own_jobs():
    ko_sat = kickoff_pt("2026-12-19", "16:30")  # Saturday 1:30 PM PT
    ko_sun = kickoff_pt("2026-12-20", "13:00")
    games = [{"teams": frozenset({"BAL", "PIT"}), "kickoff": ko_sat},
             {"teams": frozenset({"ATL", "TBB"}), "kickoff": ko_sun}]
    jobs = compute_week_plan(15, MON_DEC, games,
                             my_teams={"BAL", "ATL"}, opp_teams=set())
    plans = _jobs_of(jobs, "lineup_plan")
    days = {p["when"].date().isoweekday() for p in plans}
    assert days == {6, 7}  # a Saturday pass AND a Sunday pass
    checks = _jobs_of(jobs, "slate_check")
    assert checks[0]["when"] == ko_sat - timedelta(minutes=80)


def test_opponent_teams_count_for_slates():
    ko = kickoff_pt("2026-09-27", "13:00")
    games = [{"teams": frozenset({"NYJ", "NYG"}), "kickoff": ko}]
    assert relevant_slates(games, set(), {"NYJ"})  # opp player -> still a slate
    assert not relevant_slates(games, {"ATL"}, {"DAL"})


def test_dst_fall_back_boundary_nov_1_2026():
    # Nov 1 2026: US falls back. ET stays exactly 3h ahead of PT through it.
    before = kickoff_pt("2026-10-31", "13:00")
    after = kickoff_pt("2026-11-01", "13:00")
    assert before.hour == 10 and after.hour == 10
    assert before.utcoffset() != after.utcoffset()  # offsets DID change
    # absolute elapsed time across fall-back is 25h. NOTE: same-zone aware
    # subtraction (after - before) is WALL-CLOCK (24h) — the pitfall
    # clock.minutes_until avoids by using timestamps.
    assert after.timestamp() - before.timestamp() == 25 * 3600
    assert (after - before) == timedelta(hours=24)


def test_waiver_brief_is_tuesday_5pm():
    jobs = compute_week_plan(3, MON_WK1 + timedelta(days=14), [], {"ATL"}, set())
    wb = _jobs_of(jobs, "waiver_brief")[0]
    assert wb["when"] == datetime(2026, 9, 22, 17, 0, tzinfo=PT)
    assert wb["when"].date().isoweekday() == 2
