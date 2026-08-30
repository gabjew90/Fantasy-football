"""Module 1 — Tuesday waiver intelligence brief.

Ranked adds with actual role-change numbers, a drop/IR pairing, and a FAAB
bid with its logic spelled out (my budget, rival budgets, scarcity from my
next-3-weeks byes). Ends with the hard deadline line.
"""

from __future__ import annotations

import logging
import time as _time

from draftkit import seasondata, waivers
from draftkit.sleeper import BASE, get_json

from . import faab as faab_mod
from . import usage as usage_mod
from .context import POS_SLOTS, rostered_ids

log = logging.getLogger("manager")

FLEX_POS = ("RB", "WR", "TE")
TREND_TTL = 3600
TOP_N = 5

# add-ranking weights (documented in DECISIONS.md)
W_CONTINGENCY = 40.0
W_TREND_MAX = 25.0
W_USAGE = 10.0
W_NEED = 15.0


def trending(store, kind: str = "add") -> dict[str, int]:
    """sleeper_id -> count over 24h; cached one hour."""
    key = f"trending:{kind}"
    cached = store.get(key)
    if cached and _time.time() - cached.get("ts", 0) < TREND_TTL:
        return {str(k): int(v) for k, v in cached["data"].items()}
    try:
        raw = get_json(f"{BASE}/players/nfl/trending/{kind}?lookback_hours=24&limit=25") or []
        data = {str(r["player_id"]): int(r.get("count") or 0) for r in raw}
        store.set(key, {"ts": _time.time(), "data": data})
        return data
    except Exception as e:  # noqa: BLE001
        log.warning("trending fetch failed: %s", e)
        return {str(k): int(v) for k, v in (cached or {}).get("data", {}).items()}


def my_bye_needs(ctx) -> dict[str, int]:
    """pos -> deficit count across my starting slots over the next 3 weeks."""
    needs: dict[str, int] = {}
    week = ctx["week"]
    for w in range(week, week + 3):
        wb = seasondata.byes(ctx["schedule"], w)
        avail: dict[str, int] = {}
        for p in ctx["roster_players"].get(ctx["my_rid"], []):
            if p.get("team") in wb or p.get("status") in ("Out", "IR", "PUP", "Suspended"):
                continue
            avail[p["pos"]] = avail.get(p["pos"], 0) + 1
        flex_pool = sum(max(0, avail.get(pos, 0) - POS_SLOTS.get(pos, 0)) for pos in FLEX_POS)
        for pos, req in POS_SLOTS.items():
            if avail.get(pos, 0) < req:
                needs[pos] = needs.get(pos, 0) + (req - avail.get(pos, 0))
        if flex_pool < 2:
            for pos in FLEX_POS:
                needs[pos] = needs.get(pos, 0)  # mark position as at least relevant
    return needs


def rival_needy_budgets(ctx, pos: str) -> list[int]:
    """Remaining budgets of rivals who cannot fill `pos` from healthy players."""
    out = []
    for rid, roster in ctx["roster_players"].items():
        if rid == ctx["my_rid"]:
            continue
        healthy = [p for p in roster
                   if p["pos"] == pos and p.get("status") not in ("Out", "IR", "PUP")]
        if len(healthy) <= POS_SLOTS.get(pos, 1):
            out.append(ctx["budgets"].get(rid, 0))
    return sorted(out, reverse=True)


def _fa_pool(ctx) -> list[dict]:
    """Full Sleeper dump, not just the draft board — deep contingency stashes
    (a PUP starter's backup) are exactly the players tiers.csv never ranked."""
    taken = rostered_ids(ctx)
    pool = []
    for pid, pl in ctx["players"].items():
        pid = str(pid)
        if pid in taken or not isinstance(pl, dict) or not pl.get("active"):
            continue
        row = ctx["player_row"](pid)
        if row and (row.get("weekly", 0) > 0 or (row.get("ros") or 0) > 60):
            # VORP (from the board when ranked, 0 otherwise) ranks adds — raw
            # season totals make every backup QB outrank a startable WR
            t = ctx["trow"].get(pid) or {}
            row["vorp"] = float(t.get("vorp") or 0.0)
            pool.append(row)
    pool.sort(key=lambda p: -(p.get("ros") or 0.0))
    return pool[:300]


def _drop_or_ir(ctx, candidate_ros: float, pos: str | None = None) -> str:
    """Concrete roster move that makes space, respecting protections."""
    if pos in ("K", "DEF"):
        cur = [p for p in ctx["roster_players"][ctx["my_rid"]] if p["pos"] == pos]
        if cur:
            return f"swap for {cur[0]['name']} (streamers replace, never eat a bench spot)"
    ir_ready = [p for p in ctx["roster_players"].get(ctx["my_rid"], [])
                if p.get("status") in ctx["reserve_allow"]]
    if ir_ready and not (ctx["my_roster"].get("reserve") or []):
        return f"move {ir_ready[0]['name']} to IR (opens the slot free)"
    from draftkit.lineup import optimal_lineup
    mine = ctx["roster_players"][ctx["my_rid"]]
    opt_ids = {str(p["sleeper_id"]) for p in optimal_lineup(mine, POS_SLOTS, 2)}
    keep = opt_ids | set(ctx["current_starters"])
    starters = {p["name"] for p in mine if str(p["sleeper_id"]) in keep}
    bench = [p for p in mine if str(p["sleeper_id"]) not in keep]
    prot = waivers.protected_drop_ids(
        bench, starters, set(str(x) for x in (ctx["my_roster"].get("reserve") or [])))
    droppable = sorted((p for p in bench if str(p["sleeper_id"]) not in prot),
                       key=lambda p: p.get("ros") or 0)
    for d in droppable:
        if (d.get("ros") or 0) < candidate_ros:
            return f"drop {d['name']}"
    return "no clean drop — only claim if you value him over your worst bench spot"


def fa_replacement_levels(pool: list[dict]) -> dict[str, tuple[float, float]]:
    """pos -> (best FA ros, second-best FA ros). The live replacement level:
    what a claim is worth is measured against what stays freely available
    (v2 item 0.2) — self-calibrating RB scarcity, no hand-set baselines."""
    tops: dict[str, list[float]] = {}
    for p in pool:
        tops.setdefault(p["pos"], []).append(p.get("ros") or 0.0)
    return {pos: (vals[0], vals[1] if len(vals) > 1 else 0.0)
            for pos, vals in ((k, sorted(v, reverse=True)) for k, v in tops.items())}


def value_over_fa(p: dict, levels: dict[str, tuple[float, float]]) -> float:
    """ROS value above the best OTHER free agent at the position."""
    best, second = levels.get(p["pos"], (0.0, 0.0))
    baseline = second if (p.get("ros") or 0.0) >= best else best
    return round((p.get("ros") or 0.0) - baseline, 1)


DOWNGRADE = {"league_winner": "breakout", "breakout": "speculative",
             "speculative": "streamer", "streamer": "streamer"}


def _classify(c: dict, contingent: bool) -> str:
    if contingent and (c.get("ros") or 0) >= 100:
        return "league_winner"
    if contingent:
        return "speculative"
    if c["pos"] in ("K", "DEF"):
        return "streamer"
    return "breakout" if (c.get("ros") or 0) >= 100 else "speculative"


def build(ctx, store) -> str:
    week = ctx["week"]
    notes: list[str] = list(ctx.get("stale") or [])
    fa = _fa_pool(ctx)
    trend = trending(store, "add")
    drops_trend = trending(store, "drop")

    cont = waivers.classify_contingencies(fa, ctx["roster_players"], ctx["injury"])
    cont_ids = {str(c["sleeper_id"]): c["evidence"] for c in cont}

    stats_season = int(ctx["state"]["season"]) if str(ctx["state"]["season"]).isdigit() else week
    usage, u_note = usage_mod.load_usage(stats_season)
    snaps = usage_mod.load_snaps(stats_season) if usage else None
    if u_note:
        notes.append(u_note)
    notes.append(usage_mod.MISSING_NOTE)

    needs = my_bye_needs(ctx)
    trend_max = max(trend.values(), default=1) or 1

    levels = fa_replacement_levels(fa)
    store.set(f"fa_replacement:{week}",
              {pos: round(best, 1) for pos, (best, _s) in levels.items()})

    scored = []
    for p in fa:
        pid = str(p["sleeper_id"])
        ev = usage_mod.evidence(p["name"], usage, snaps, week - 1)
        p["fa_value"] = value_over_fa(p, levels)
        score = p["fa_value"]
        score += W_CONTINGENCY if pid in cont_ids else 0
        score += W_TREND_MAX * (trend.get(pid, 0) / trend_max)
        score += W_USAGE if ev else 0
        score += W_NEED if needs.get(p["pos"], 0) > 0 else 0
        scored.append((score, p, ev, pid))
    scored.sort(key=lambda t: -t[0])

    faab_cfg = ctx["scfg"].get("faab", {})
    lines = [f"# Waiver brief — week {week}", ""]
    if ctx.get("fallback"):
        lines.append("⚠ projections not yet published — values are season-baseline fallbacks")
    for n in notes:
        lines.append(f"⚠ {n}")
    lines.append("")

    # IR flags FIRST — a free roster spot changes every drop decision below
    ir_lines = waivers.ir_actions(
        [p for p in ctx["roster_players"][ctx["my_rid"]]
         if str(p["sleeper_id"]) in set(str(x) for x in (ctx["my_roster"].get("reserve") or []))],
        ctx["roster_players"][ctx["my_rid"]], ctx["injury"], ctx["reserve_allow"])
    if ir_lines:
        lines += ["## IR moves"] + [f"- {a}" for a in ir_lines] + [""]

    lines.append("## Top adds")
    if not scored:
        lines.append("- free agent pool is empty of ranked players")
    for score, p, ev, pid in scored[:TOP_N]:
        contingent = pid in cont_ids
        cls = _classify(p, contingent)
        damp_note = usage_mod.overreaction(p["name"], usage, snaps, week - 1)
        if damp_note and not contingent:  # a real inherited role is not a mirage
            cls = DOWNGRADE[cls]
        needy = rival_needy_budgets(ctx, p["pos"])
        fair, agg = waivers.bid_band(
            cls, ctx["my_budget"], "COMFORTABLE", faab_cfg,
            rival_max_budget=(needy[0] if cls == "league_winner" and needy else None),
            value_cap=int((p.get("ros") or 0) / 2) if cls == "league_winner" else None)
        why = []
        if contingent:
            why.append(cont_ids[pid])
        if ev:
            why.append(ev)
        if trend.get(pid):
            why.append(f"{trend[pid]:,} Sleeper adds/24h")
        if damp_note and not contingent:
            why.append(damp_note)
        if not why:
            why.append("value over my current bench")
        need_note = f"; I am short at {p['pos']} in the next 3 weeks (byes)" if needs.get(p["pos"]) else ""
        rival_note = (f"rival budgets at need: {', '.join(f'${b}' for b in needy[:3])}"
                      if needy else "no rival is forced to bid here")
        lines += [
            f"**{p['name']}** ({p['pos']}, {p.get('team') or '?'}) — {cls}",
            f"- why: {'; '.join(why)}{need_note}",
            f"- worth over next-best FA {p['pos']}: +{p.get('fa_value', 0):.0f} ROS pts",
            f"- move: {_drop_or_ir(ctx, p.get('ros') or 0, p['pos'])}",
            f"- bid **${fair}–${agg}** of my ${ctx['my_budget']} — {rival_note}",
        ]

    spent = faab_mod.spent_from_transactions(store.get("txn_history", []))
    for n in faab_mod.crosscheck(spent, ctx["rosters"]):
        lines.append(f"- {n}")
    budgets = sorted(((ctx['users_by_rid'][rid], b) for rid, b in ctx["budgets"].items()),
                     key=lambda t: -t[1])
    lines += ["", "## League FAAB remaining",
              " · ".join(f"{n} ${b}" for n, b in budgets), ""]
    if drops_trend:
        hot_drops = [pid for pid in drops_trend if pid in {str(p['sleeper_id']) for p in ctx['roster_players'][ctx['my_rid']]}]
        if hot_drops:
            names = [ctx["player_row"](p)["name"] for p in hot_drops if ctx["player_row"](p)]
            lines.append(f"⚠ league-wide drop trend includes my players: {', '.join(names)} — check news before assuming they're fine.")
    lines.append("**Bids in by 7:00 PM PT tonight.**")
    return "\n".join(lines)
