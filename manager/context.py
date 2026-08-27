"""One live-league fetch pass shared by every module in a run.

Wraps draftkit's build_context (Sleeper client + caching + tiers + weekly
projections with placeholder fallback) and adds manager-specific views:
my/opponent team sets, current-week matchup pairing, remaining FAAB.
"""

from __future__ import annotations

import logging

from draftkit import seasondata
from draftkit.briefs import SLOTS, FLEX, build_context
from draftkit.config import Config

log = logging.getLogger("manager")

POS_SLOTS = SLOTS  # starting requirements: QB1 RB2 WR2 TE1 K1 DEF1 + 2 FLEX


def league_context() -> dict:
    cfg = Config.load()
    ctx = build_context(cfg)
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
    ctx["budgets"] = seasondata.rival_budgets(ctx["rosters"], ctx["budget"])
    ctx["my_budget"] = ctx["budgets"].get(ctx["my_rid"], ctx["budget"])
    ctx["current_starters"] = [str(s) for s in (ctx["my_roster"].get("starters") or [])]
    return ctx


def rostered_ids(ctx) -> set[str]:
    out = set()
    for r in ctx["rosters"]:
        out |= {str(p) for p in (r.get("players") or [])}
    return out
