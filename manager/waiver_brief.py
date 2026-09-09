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

from . import consensus, ecr as ecr_mod, provenance
from . import faab as faab_mod
from . import usage as usage_mod
from .context import rostered_ids

log = logging.getLogger("manager")

FLEX_POS = ("RB", "WR", "TE")
TREND_TTL = 3600
TOP_N = 5

# Add-ranking weights, PER WEEK REMAINING (documented in DECISIONS.md).
#
# These are added to fa_value, which is a rest-of-season number. Once `ros`
# started shrinking with the calendar, a fixed +40 for a contingency stopped
# being a thumb on the scale and became the whole scale: in week 16, with two
# weeks left, every real add is worth single digits and the bonuses decide the
# ranking outright. So the bonuses shrink with it. The season-scale values
# below are the historical ones divided by a 17-week season, and are
# multiplied by weeks remaining at the call site -- which reproduces the old
# numbers exactly in week 1 and nowhere else, by design.
SEASON_WEEKS = 17.0
W_CONTINGENCY = 40.0 / SEASON_WEEKS
W_TREND_MAX = 25.0 / SEASON_WEEKS
W_USAGE = 10.0 / SEASON_WEEKS
W_NEED = 15.0 / SEASON_WEEKS


def _regime(ctx) -> tuple[str, str | None]:
    """This roster's FAAB regime from its live playoff odds.

    Degrades to COMFORTABLE with a visible note rather than crashing the
    brief: the simulation needs a season's matchups and cannot run in week 1
    of a fresh league, and a missing regime must never cost you the brief.
    """
    try:
        from draftkit.briefs import playoff_odds
        odds, reg = playoff_odds(ctx)
        ctx["_playoff_odds"] = odds
        return reg, None
    except Exception as e:  # noqa: BLE001
        return "COMFORTABLE", (f"DATA MISSING: playoff odds ({e.__class__.__name__}) "
                               f"— bids priced at COMFORTABLE")


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
    slots, flex = ctx["slots"], ctx["flex"]
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
        flex_pool = sum(max(0, avail.get(pos, 0) - slots.get(pos, 0)) for pos in FLEX_POS)
        for pos, req in slots.items():
            if avail.get(pos, 0) < req:
                needs[pos] = needs.get(pos, 0) + (req - avail.get(pos, 0))
        if flex_pool < flex:
            for pos in FLEX_POS:
                needs[pos] = needs.get(pos, 0)  # mark position as at least relevant
    return needs


def rival_needy_budgets(ctx, pos: str) -> list[int]:
    slots = ctx["slots"]
    """Remaining budgets of rivals who cannot fill `pos` from healthy players."""
    out = []
    for rid, roster in ctx["roster_players"].items():
        if rid == ctx["my_rid"]:
            continue
        healthy = [p for p in roster
                   if p["pos"] == pos and p.get("status") not in ("Out", "IR", "PUP")]
        if len(healthy) <= slots.get(pos, 1):
            out.append(ctx["budgets"].get(rid, 0))
    return sorted(out, reverse=True)


# A player on season-ending IR still carries his PRESEASON number on the board,
# because the board was built in August and nothing rebuilds it. Ricky Pearsall
# (PCL surgery, out for 2026) sat at 148.7 and ranked as the best free agent
# receiver in Omnibeta on 2026-09-08. Every LIVE source had already caught it --
# Sleeper projected him 0.0, ESPN and the sheet dropped him entirely -- but the
# consensus could not correct a player it has no row for, so the stale number
# sailed through. A shelved player at his August price is the most dangerous
# kind of wrong: it looks like the best add on the board.
RESERVE_STATUS = ("IR", "IR-R", "PUP", "PUP-R", "NFI", "NFI-R", "DNR", "Sus", "Inactive")


def _stale_reserve(pl: dict, con: dict, pid: str) -> bool:
    """On a reserve list AND no live source still carries him.

    Only meaningful for positions the sources are asked about. Kickers and
    defenses are absent from the consensus unconditionally -- the Sleeper
    projections request names QB/RB/WR/TE and nothing else -- so reading
    their n=0 as staleness deleted every reserve-status K and DEF from the
    pool on evidence that was never collected.
    """
    if (pl.get("injury_status") or "") not in RESERVE_STATUS:
        return False
    if (pl.get("position") or "") not in consensus.COVERED_POS:
        return False
    return (con.get(pid) or {}).get("n", 0) < 1


def _fa_pool(ctx, con: dict | None = None) -> list[dict]:
    """Full Sleeper dump, not just the draft board — deep contingency stashes
    (a PUP starter's backup) are exactly the players tiers.csv never ranked."""
    taken = rostered_ids(ctx)
    con = con or {}
    pool, dropped = [], []
    for pid, pl in ctx["players"].items():
        pid = str(pid)
        if pid in taken or not isinstance(pl, dict) or not pl.get("active"):
            continue
        if _stale_reserve(pl, con, pid):
            row = ctx["player_row"](pid)
            if row and (row.get("ros") or 0) > 60:
                dropped.append(f"{row['name']} ({pl.get('injury_status')})")
            continue
        row = ctx["player_row"](pid)
        if row and (row.get("weekly", 0) > 0 or (row.get("ros") or 0) > 60):
            # VORP (from the board when ranked, 0 otherwise) ranks adds — raw
            # season totals make every backup QB outrank a startable WR
            t = ctx["trow"].get(pid) or {}
            row["vorp"] = float(t.get("vorp") or 0.0)
            pool.append(row)
    if dropped:
        log.info("fa pool: excluded %d shelved players carrying stale board "
                 "values: %s", len(dropped), ", ".join(sorted(dropped)[:6]))
        ctx["_stale_reserve_dropped"] = sorted(dropped)
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
    opt_ids = {str(p["sleeper_id"]) for p in optimal_lineup(mine, ctx["slots"], flex_slots=ctx["flex_slots"])}
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


def fa_replacement_levels(pool: list[dict]) -> dict[str, tuple[float, float, str]]:
    """pos -> (best FA ros, second-best FA ros, id of the best). The live
    replacement level: what a claim is worth is measured against what stays
    freely available (v2 item 0.2) — self-calibrating RB scarcity, no
    hand-set baselines.

    The id is carried because the leader has to be identified BY IDENTITY.
    Comparing on value alone meant an exact tie at the top counted both
    players as the leader, and both then priced themselves against
    second-best -- two names in the adds list each claiming a marginal value
    that only exists once, when only one of them can be claimed into it.
    """
    tops: dict[str, list[tuple[float, str]]] = {}
    for p in pool:
        tops.setdefault(p["pos"], []).append(
            (p.get("ros") or 0.0, str(p.get("sleeper_id") or "")))
    out = {}
    for pos, vals in tops.items():
        vals.sort(key=lambda t: -t[0])
        out[pos] = (vals[0][0], vals[1][0] if len(vals) > 1 else 0.0, vals[0][1])
    return out


def value_over_fa(p: dict, levels: dict[str, tuple[float, float, str]]) -> float:
    """ROS value above the best OTHER free agent at the position."""
    best, second, best_pid = levels.get(p["pos"], (0.0, 0.0, ""))
    baseline = second if str(p.get("sleeper_id") or "") == best_pid else best
    return round((p.get("ros") or 0.0) - baseline, 1)


DOWNGRADE = {"league_winner": "breakout", "breakout": "speculative",
             "speculative": "streamer", "streamer": "streamer"}

STASH_WEEKLY_FLOOR = 2.0  # under this weekly projection = no current role


def bench_stash_count(ctx) -> int:
    """Zero-role stashes on the BENCH PROPER. IR occupants are exempt from
    the one-stash budget (v2 item 0.4): with 1 IR slot, one injury stash is
    free and does not spend bench room."""
    ir = {str(x) for x in (ctx["my_roster"].get("reserve") or [])}
    starters = set(ctx["current_starters"])
    n = 0
    for p in ctx["roster_players"][ctx["my_rid"]]:
        pid = str(p["sleeper_id"])
        if pid in ir or pid in starters or p["pos"] in ("K", "DEF"):
            continue
        if (p.get("weekly") or 0.0) < STASH_WEEKLY_FLOOR:
            n += 1
    return n


def stash_note(ctx, candidate: dict, contingent: bool) -> str | None:
    """Roster-budget guidance when the claim is itself a zero-role stash."""
    if (candidate.get("weekly") or 0.0) >= STASH_WEEKLY_FLOOR:
        return None
    held = bench_stash_count(ctx)
    ir_free = not (ctx["my_roster"].get("reserve") or [])
    ir_eligible = [p["name"] for p in ctx["roster_players"][ctx["my_rid"]]
                   if p.get("status") in ctx["reserve_allow"]]
    if held == 0:
        return None  # first stash is always within budget
    if ir_free and ir_eligible:
        return (f"stash budget: bench already holds {held} — OK only because "
                f"{ir_eligible[0]} can move to IR (IR stashes don't count)")
    return (f"stash budget: bench already holds {held} zero-role stash(es) "
            f"and the IR slot can't absorb one — this claim is over budget "
            f"unless you value it above what you'd cut")


def _classify(c: dict, contingent: bool) -> str:
    # `ros` is REMAINING points, so these bars tighten as the season runs out.
    # That is the intent: a player worth 100 points from week 2 is a league
    # winner, and the same weekly rate from week 14 is a streamer.
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

    # CONSENSUS FIRST. It re-bases every projection AND tells _fa_pool which
    # shelved players are carrying a stale August number, so it has to run
    # before the pool is built rather than after it is ranked.
    con, con_notes = consensus.build(ctx, store)
    if con and (ctx.get("scfg") or {}).get("consensus_projections", True):
        _n, _notes = consensus.apply(ctx, con)
        con_notes += _notes
    # A warning filed into a collapsed footer is a warning that is gone.
    con_warnings = [n for n in con_notes if n.startswith("⚠")]

    panel, panel_note = ecr_mod.by_sleeper_id(ctx, store)
    fa = _fa_pool(ctx, con)
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
              {pos: round(best, 1) for pos, (best, _s, _pid) in levels.items()})

    scored = []
    for p in fa:
        pid = str(p["sleeper_id"])
        ev = usage_mod.evidence(p["name"], usage, snaps, week - 1)
        p["fa_value"] = value_over_fa(p, levels)
        score = p["fa_value"]
        # every bonus on the same horizon as the value it is added to
        wl = ctx.get("weeks_left") or 1
        score += W_CONTINGENCY * wl if pid in cont_ids else 0
        score += W_TREND_MAX * wl * (trend.get(pid, 0) / trend_max)
        score += W_USAGE * wl if ev else 0
        score += W_NEED * wl if needs.get(p["pos"], 0) > 0 else 0
        scored.append((score, p, ev, pid))
    scored.sort(key=lambda t: -t[0])

    faab_cfg = ctx["scfg"].get("faab", {})
    lines = [f"# Waiver brief — week {week}", ""]
    if ctx.get("fallback"):
        lines.append("⚠ projections not yet published — values are season-baseline fallbacks")
    for n in notes:
        lines.append(f"⚠ {n}")
    for n in con_warnings:
        lines.append(n)
    lines.append("")

    # IR flags FIRST — a free roster spot changes every drop decision below
    ir_lines = waivers.ir_actions(
        [p for p in ctx["roster_players"][ctx["my_rid"]]
         if str(p["sleeper_id"]) in set(str(x) for x in (ctx["my_roster"].get("reserve") or []))],
        ctx["roster_players"][ctx["my_rid"]], ctx["injury"], ctx["reserve_allow"])
    if ir_lines:
        lines += ["## IR moves"] + [f"- {a}" for a in ir_lines] + [""]

    # REGIME IS COMPUTED, NOT ASSUMED (fixed 2026-09-07). This was the literal
    # "COMFORTABLE" for every league in every week, so every per-dollar number
    # below was regime-blind: a LONGSHOT roster that should be bidding
    # aggressively and a SAFE one that should be hoarding got the same band.
    regime, reg_note = _regime(ctx)
    if reg_note:
        lines.append(f"⚠ {reg_note}")
    else:
        # SHOW THE REGIME. It sets every bid band below, so a brief that
        # prices bids without naming the regime cannot be audited.
        odds = ctx.get("_playoff_odds")
        lines.append(f"_bids priced at **{regime}**"
                     + (f" (playoff odds {odds:.0%})_" if odds is not None else "_"))
    lines.append("")

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
            cls, ctx["my_budget"], regime, faab_cfg,
            rival_max_budget=(needy[0] if cls == "league_winner" and needy else None),
            # ros_season BY NAME -- see draftkit/briefs.py:waiver_brief for
            # why the bid cap stays on the season scale while everything else
            # around it moved to remaining points.
            value_cap=int((p.get("ros_season") or 0) / 2) if cls == "league_winner" else None)
        why = []
        if contingent:
            why.append(cont_ids[pid])
        if ev:
            why.append(ev)
        if trend.get(pid):
            why.append(f"{trend[pid]:,} Sleeper adds/24h")
        if damp_note and not contingent:
            why.append(damp_note)
        s_note = stash_note(ctx, p, contingent)
        from . import age_decay
        _a = (ctx.get("scfg") or {}).get("age_decay") or {}
        _n = age_decay.note(p["pos"], (ctx.get("age_of") or {}).get(pid), week, _a)
        if _n:
            why.append(_n)
        trow = ctx["trow"].get(pid) or {}
        if trow.get("backs_up_pos") and trow.get("starter_fragility_label") in ("high", "moderate"):
            why.append(f"standing handcuff: backs up {trow['backs_up_pos']} "
                       f"({trow['starter_fragility_label']} fragility)")
        if not why:
            why.append("value over my current bench")
        need_note = f"; I am short at {p['pos']} in the next 3 weeks (byes)" if needs.get(p["pos"]) else ""
        rival_note = (f"rival budgets at need: {', '.join(f'${b}' for b in needy[:3])}"
                      if needy else "no rival is forced to bid here")
        lines += [
            f"**{p['name']}** ({p['pos']}, {p.get('team') or '?'}) — {cls}",
            f"- why: {'; '.join(why)}{need_note}",
            # value_over_fa is negative for anyone who is not the best free
            # agent at his position, so the sign comes from the number
            f"- worth over next-best FA {p['pos']}: {p.get('fa_value', 0):+.0f} ROS pts"
            + consensus.annotate(con.get(pid)),
            f"- move: {_drop_or_ir(ctx, p.get('ros') or 0, p['pos'])}",
            f"- bid **${fair}–${agg}** of my ${ctx['my_budget']} — {rival_note}",
        ]
        # CEILING, NOT JUST THE MEAN. A bench player only ever enters the
        # lineup when he breaks out, so his median barely matters and the
        # panel's most optimistic rank is the whole question.
        pan = ecr_mod.annotate(panel.get(pid))
        if pan:
            lines.append("- ceiling:" + pan[2:])
        if contingent:
            lines.append(f"- insurance behind a downed starter: bid the "
                         f"AGGRESSIVE end (${agg})")
        if s_note:
            lines.append(f"- {s_note}")

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
    # RANKS BEYOND THE CUT. These were computed and then silently dropped, so
    # the brief could not be second-guessed: you saw five names with no way to
    # know what came sixth, or by how much it missed.
    rest = scored[TOP_N:TOP_N + 5]
    if rest and len(scored) > TOP_N:
        lines += ["", "## Also ranked (not recommended)"]
        for score, p, _ev, pid in rest:
            gap = scored[TOP_N - 1][0] - score
            lines.append(
                f"- {p['name']} ({p['pos']}, {p.get('team') or '?'}) — "
                f"{p.get('fa_value', 0):+.0f} ROS pts over next-best FA, "
                f"{gap:.0f} behind the last recommendation"
                + consensus.annotate(con.get(pid))
                + ecr_mod.annotate(panel.get(pid)))
        lines.append("")

    # THE UPSIDE BOARD. Everything above ranks on rest-of-season mean, which
    # is right for a player who will start and wrong for one who will sit. A
    # bench player only enters the lineup when he breaks out, so his median
    # barely matters and the panel's most optimistic rank is the question.
    #
    # RANKS ONLY COMPARE WITHIN A POSITION. The first cut sorted every free
    # agent by raw best-rank and produced a board of five kickers, because K3
    # is a smaller number than WR46. Grouped by position, and each candidate
    # is measured against the weakest player I would actually drop at that
    # same position -- which is the comparison that decides a roster spot.
    STASH_POS = ("RB", "WR", "TE")
    bench_ids = {str(q["sleeper_id"]) for q in ctx["roster_players"][ctx["my_rid"]]}         - set(ctx["current_starters"])
    worst_at = {}
    for q in ctx["roster_players"][ctx["my_rid"]]:
        qid = str(q["sleeper_id"])
        rec = panel.get(qid)
        if qid not in bench_ids or q["pos"] not in STASH_POS or not rec:
            continue
        cur = worst_at.get(q["pos"])
        if cur is None or rec["best"] > cur[0]["best"]:      # ranks: higher = worse
            worst_at[q["pos"]] = (rec, q["name"])
    board = []
    for pos in STASH_POS:
        cands = [(panel[str(q["sleeper_id"])], q) for q in fa[:120]
                 if q["pos"] == pos and str(q["sleeper_id"]) in panel]
        if not cands:
            continue
        held = worst_at.get(pos)
        for rec, q in sorted(cands, key=lambda t: t[0]["best"])[:3]:
            board.append((pos, rec, q, held, ecr_mod.ceiling_beats(rec, held[0] if held else None)))
    if board:
        lines += ["", "## Upside board (ranked by ceiling, not by mean)"]
        for pos in STASH_POS:
            rows_p = [b for b in board if b[0] == pos]
            if not rows_p:
                continue
            held = rows_p[0][3]
            hdr = (f"weakest {pos} you would drop is {held[1]}, best case "
                   f"{pos}{held[0]['best']:.0f}") if held else                   f"no benched {pos} with a panel rank to compare against"
            lines.append(f"_{hdr}_")
            for _pos, rec, q, _h, beats in rows_p:
                mark = " ← **higher ceiling than what you hold**" if beats else ""
                lines.append(f"- {q['name']} ({pos}) best case {pos}{rec['best']:.0f}, "
                             f"median {pos}{rec['ecr']:.0f}{mark}")
        lines.append("")

    lines.append("**Bids in by 7:00 PM PT tonight.**")

    srcs = {}
    for n in con_notes:
        if n.startswith("consensus"):
            srcs["consensus"] = n.split("consensus ", 1)[-1]
        elif ":" in n:
            k, v = n.split(":", 1)
            v = v.strip()
            srcs[k.strip()] = v[len(k) + 1:].strip() if v.startswith(k.strip()) else v
    if panel_note:
        srcs["experts"] = panel_note
    lines += ["", provenance.render(provenance.stamp(ctx, srcs))]
    return "\n".join(lines)
