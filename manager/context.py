"""One live-league fetch pass shared by every module in a run.

Wraps draftkit's build_context (Sleeper client + caching + tiers + weekly
projections with placeholder fallback) and adds manager-specific views:
my/opponent team sets, current-week matchup pairing, remaining FAAB.
"""

from __future__ import annotations

import logging
from pathlib import Path

from draftkit import seasondata
from draftkit.briefs import build_context
from draftkit.config import Config

log = logging.getLogger("manager")

# Set once from the CLI before any job runs. Module state rather than a
# parameter threaded through seven job signatures: every job already calls
# league_context() with no arguments, and a partial thread-through is how a
# job ends up silently reading a different league than its siblings.
_LEAGUE: str | None = None
_WEEK: int | None = None


def configure(league: str | None = None, week: int | None = None) -> None:
    global _LEAGUE, _WEEK
    _LEAGUE, _WEEK = league, week


def state_dir() -> Path:
    """Where this league's committed state lives.

    One directory served every league until 2026-09-16, which was fine while
    only Omnibeta ran. The store keys (`ran:plan:2026-W38`, `waivers:2`, the
    consensus cache), the week plan and the gate hours are all per league,
    so a second league would have consumed the first league's runs and
    overwritten its plan. The default league keeps `state/` unchanged (no
    migration, the Actions history stays readable); every other league gets
    `state/<league>/`. Same convention as Config.scoped for tiers.csv.
    """
    cfg = Config.load(league=_LEAGUE)
    default = cfg.get("default_league")
    name = cfg.league_name
    if not name or name == default:
        return Path("state")
    return Path("state") / str(name)


def league_context(write_state: bool = True) -> dict:
    cfg = Config.load(league=_LEAGUE)
    # The league-side reads come from whichever platform hosts the league
    # (draftkit.briefs.SleeperSource is the seam). Yahoo was refused here
    # until 2026-09-16, when its API access was provisioned; an unknown
    # platform is still a loud error rather than a Sleeper call with a
    # foreign league id.
    platform = str(cfg.get("platform") or "sleeper").lower()
    if platform == "sleeper":
        source = None
    elif platform == "yahoo":
        from .yahoo_context import YahooSource
        source = YahooSource(cfg)
    else:
        raise RuntimeError(
            f"the in-season manager cannot run league {cfg.league_name!r}: "
            f"platform is {platform!r}; sleeper and yahoo are supported.")
    ctx = build_context(cfg, week=_WEEK, source=source, write_state=write_state)
    ctx["my_rid"] = int(ctx["my_roster"]["roster_id"])

    users_by_rid = {}
    for r in ctx["rosters"]:
        users_by_rid[int(r["roster_id"])] = ctx["users"].get(str(r.get("owner_id")), "?")
    ctx["users_by_rid"] = users_by_rid

    # current-week opponent via matchup_id pairing
    pair = {}
    seen: dict = {}
    for m in ctx["matchups"]:
        mid = m.get("matchup_id")
        rid = int(m["roster_id"])
        if mid in seen:
            pair[seen[mid]], pair[rid] = rid, seen[mid]
        else:
            seen[mid] = rid
    ctx["opp_rid"] = pair.get(ctx["my_rid"])
    ctx["opp_name"] = users_by_rid.get(ctx["opp_rid"], "(no matchup)")

    def teams_of(rid) -> set[str]:
        if rid is None:
            return set()
        return {p["team"] for p in ctx["roster_players"].get(rid, []) if p.get("team")}

    ctx["my_teams"] = teams_of(ctx["my_rid"])
    ctx["opp_teams"] = teams_of(ctx["opp_rid"])
    # ages for the in-season ROS decay (display/trade only, post-v2 item 4)
    ctx["age_of"] = {
        str(pid): p.get("age") for pid, p in ctx["players"].items()
        if isinstance(p, dict) and p.get("age")
    }
    ctx["budgets"] = seasondata.rival_budgets(ctx["rosters"], ctx["budget"])
    ctx["my_budget"] = ctx["budgets"].get(ctx["my_rid"], ctx["budget"])
    ctx["current_starters"] = [str(s) for s in (ctx["my_roster"].get("starters") or [])]
    return ctx


def rostered_ids(ctx) -> set[str]:
    out = set()
    for r in ctx["rosters"]:
        out |= {str(p) for p in (r.get("players") or [])}
    return out
