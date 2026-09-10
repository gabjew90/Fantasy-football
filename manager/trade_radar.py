"""Module 5 — trade radar (weeks 3–10, appended to the Tuesday brief).

Target identification, not fairness math: who to text and about what.
Values come from FantasyCalc, queried in THIS league's own format (see
league_format); this module never builds its own valuation. Repeats are
suppressed via state unless the opportunity's conditions changed.
"""

from __future__ import annotations

import logging

from draftkit.lineup import optimal_lineup


log = logging.getLogger("manager")

# The FantasyCalc client lives in manager.market now, so the trade pricing in
# manager.marginal can use the same values on the same league format instead
# of this module owning them behind a weeks 3-10 gate. Re-exported because
# manager.trade_watch imports `values` from here.
from .market import fetch as market, league_format, values   # noqa: E402,F401

MAX_OPPS = 3
VETO_RATIO = 0.7          # offer/ask value below this may draw veto votes
TRADE_WEEKS = (3, 10)     # active window; recommend initiating by week 10
DEADLINE_WEEK = 11


def _flex_split(ctx) -> dict[str, float]:
    """The league's own flex split (scripts/derive_flex_split.py writes it into
    the league yaml; onboard.resolve_flex_split falls back to the format's)."""
    from draftkit.onboard import resolve_flex_split
    cfg = ctx["cfg"]
    return resolve_flex_split(cfg.get("scoring") or (cfg.get("expected") or {}).get("scoring"),
                              cfg.get("flex_split"))


def surplus_deficit(roster: list[dict], slots: dict[str, int], flex: int,
                    split: dict[str, float]) -> dict[str, int]:
    """pos -> healthy startable count minus starting requirement (flex spread
    across RB/WR/TE by the league's own derived split)."""
    healthy: dict[str, int] = {}
    for p in roster:
        if (p.get("status") or "") in ("Out", "IR", "PUP", "Suspended"):
            continue
        healthy[p["pos"]] = healthy.get(p["pos"], 0) + 1
    out = {}
    for pos, req in slots.items():
        # the league's own derived flex split, not a hardcoded "one RB one WR"
        need = req + round(flex * float(split.get(pos, 0.0)))
        out[pos] = healthy.get(pos, 0) - need
    return out


def playoff_schedule(ctx, team: str, pos: str) -> str:
    """Weeks 15-17 strength as a NUMBER plus the opponent names (post-v2
    item 2 — replaces the qualitative name-the-opponents placeholder).
    Degrades to names-only when the defense metric is not yet meaningful."""
    from draftkit import defense as defense_mod
    pa = ctx.get("_pa_cache", "unset")
    if pa == "unset":
        try:
            pa = defense_mod.points_allowed(
                int(ctx["state"]["season"]), ctx["league"]["scoring_settings"],
                through_week=max(0, int(ctx["week"]) - 1))
        except Exception:  # noqa: BLE001
            pa = None
        ctx["_pa_cache"] = pa
    shrink_k = float((ctx.get("scfg") or {}).get("matchup_shrink_weeks", 5))
    val, label = defense_mod.schedule_strength(
        pa, ctx["schedule"], team, pos, (15, 16, 17), shrink_k)
    if val is None:
        return f"{label} (DATA MISSING: defense quality not yet meaningful)" if label else ""
    verdict = "soft" if val >= 1.05 else ("tough" if val <= 0.95 else "neutral")
    return f"{val:.2f}x league avg ({verdict}) — {label}"


def _waiver_pool(ctx, con=None) -> list[dict]:
    """The wire, for spots a package opens. Cached on ctx: the radar prices
    every opportunity and rebuilding a 300-row pool each time is waste."""
    pool = ctx.get("_wv_pool")
    if pool is None:
        try:
            from .waiver_brief import free_agent_pool
            pool = free_agent_pool(ctx, con)
        except Exception as e:  # noqa: BLE001
            log.warning("trade radar: no waiver pool (%s)", e.__class__.__name__)
            pool = []
        ctx["_wv_pool"] = pool
    return pool


def _rank_panel(ctx):
    """The rank panel accepts() reads, cached on ctx like the waiver pool.

    None when unavailable -- never {}. price() leaves acceptance None on
    None, and verdict(mode="slots") then says "not computed" instead of
    judging every package on a board that ranks nobody. Tests inject
    ctx["_rank_panel"] the way they inject ctx["_wv_pool"].
    """
    if "_rank_panel" not in ctx:
        try:
            from . import ecr
            panel, notes = ecr.rank_panel(ctx)
            for n in notes or ():
                if n.startswith("⚠") or n.startswith("DATA MISSING"):
                    log.warning("trade radar: %s", n)
            ctx["_rank_panel"] = panel or None
        except Exception as e:  # noqa: BLE001
            log.warning("trade radar: no rank panel (%s)", e.__class__.__name__)
            ctx["_rank_panel"] = None
    return ctx["_rank_panel"]


def _range_ppg(mine, theirs, give, get, shape, wv, wl):
    """(lo, hi) of my delta per week: the package priced on each source alone.

    The blend is the best estimate; this is how far the shops disagree about
    it, and the user decides on it -- it is reported, never gated. Rows carry
    `consensus.per_source` after consensus.apply(); a roster with none (a
    test fixture, a league on one source) gives None and the brief says so.
    The wire is priced on the blend: the backfill body's own spread is
    second-order next to the package's.
    """
    from . import marginal
    srcs: set[str] = set()
    for p in list(mine) + list(theirs):
        srcs |= set(((p.get("consensus") or {}).get("per_source") or {}).keys())
    if not srcs:
        return None

    def on(rows, src):
        out = []
        for p in rows:
            v = ((p.get("consensus") or {}).get("per_source") or {}).get(src)
            out.append(dict(p, ros=float(v if v is not None else (p.get("ros") or 0.0))))
        return out

    ids_g = {str(p["sleeper_id"]) for p in give}
    ids_t = {str(p["sleeper_id"]) for p in get}
    deltas = []
    for src in sorted(srcs):
        m, t = on(mine, src), on(theirs, src)
        g = [p for p in m if str(p["sleeper_id"]) in ids_g]
        h = [p for p in t if str(p["sleeper_id"]) in ids_t]
        deltas.append(marginal.price(m, t, g, h, shape, key="ros", waivers=wv).my_delta / wl)
    return (min(deltas), max(deltas))


def _biggest_row(give, get) -> dict | None:
    """The consensus row for the largest piece in the package.

    verdict() cannot tell a 16-point edge between players every source agrees
    about from the same edge on one they argue about by twenty-two -- unless
    it is handed the row to test against. It always could; nothing passed it,
    so `confident` came back None on every package the radar has ever priced.
    The biggest piece is the right one because the package's disagreement is
    dominated by its largest projection, and consensus.confident halves the
    spread before comparing, which already builds in slack for the rest.
    """
    rows = [p for p in list(give) + list(get) if isinstance(p, dict)]
    if not rows:
        return None
    return max(rows, key=lambda p: p.get("ros") or 0.0).get("consensus")


def _priced(ctx, opp, vals) -> list[str]:
    """What the package does to both starting lineups, seats named, and
    whether it clears the gates.

    Degrades to nothing rather than breaking the brief: a desperation row has
    no concrete ask, and an opportunity whose roster went missing is not
    worth a traceback in an email.
    """
    from . import marginal
    give, get = opp.get("give_p") or [], opp.get("get_p") or []
    theirs = (ctx.get("roster_players") or {}).get(opp.get("rid")) or []
    if not theirs or not (give or get):
        return []
    shape = {"slots": ctx["slots"], "flex": ctx.get("flex", 0),
             "flex_slots": ctx.get("flex_slots")}
    mine = ctx["roster_players"][ctx["my_rid"]]
    wv = _waiver_pool(ctx)
    ranks = _rank_panel(ctx)
    wl = ctx.get("weeks_left") or 1
    try:
        d = marginal.price(mine, theirs, give, get, shape, key="ros",
                           market_values=vals, waivers=wv, ranks=ranks)
        thin = marginal.newly_thin(mine, shape, arriving=get, departing=give,
                                   waivers=wv, key="ros")
        v = marginal.verdict(d, wl, thin=thin, con=_biggest_row(give, get))
        rng = _range_ppg(mine, theirs, give, get, shape, wv, wl)
    except Exception as e:  # noqa: BLE001
        log.warning("trade radar: could not price %s (%s)", opp.get("mgr"), e)
        return []
    # OFFER, not SEND. His side is a prediction that a position-by-position
    # manager plausibly says yes; my side is a mean with a range the user
    # decides on. Neither is a command.
    verdict_word = "OFFER" if v["send"] else "hold"
    rng_txt = (f"range {rng[0]:+.2f} to {rng[1]:+.2f}/wk across sources" if rng
               else "range n/a — one source")
    out = [f"- **{verdict_word}** — lineup effect (rest-of-season POINTS, not the "
           f"market values quoted above): **me {d.my_delta:+.1f}** "
           f"({rng_txt}; mean {v['my_ppg']:+.2f}/wk), them {d.their_delta:+.1f} "
           f"(my model of his lineup — shown, not gated)"]
    acc = d.acceptance
    if acc is None:
        out.append("  - his side: not judged — no rank panel this run")
    else:
        names = {str(p["sleeper_id"]): p.get("name", str(p["sleeper_id"])) for p in give}
        tags = ", ".join(f"{names.get(pid, pid)} {t}" for pid, t in acc["tags"].items())
        mb, ma = acc["starters_market_before"], acc["starters_market_after"]
        out.append(f"  - his side: {'accepts' if acc['accept'] else 'refuses'} — {tags}; "
                   f"his starters' market {mb} -> {ma} ({ma - mb:+d})"
                   + (f"; panel {acc['panel']}" if acc.get("panel") else ""))
        if acc["net_rank"] < 0:
            out.append(f"  - ⚑ a rankings-reader sees his lineup worse by "
                       f"{-acc['net_rank']:.0f} rank-points")
    for r in v["why"]:
        out.append(f"  - ⚠ {r}")
    for r in v["warnings"]:
        out.append(f"  - {r}")
    for label, mv in (("me", d.my_moves), ("them", d.their_moves)):
        for tag, rows in (("loses the spot", mv["benched"]),
                          ("comes off the bench", mv["promoted"]),
                          ("fills the opened spot off waivers",
                           mv.get("backfilled") or [])):
            for p in rows:
                out.append(f"  - {label}: {p['name']} ({p['pos']}) {tag}")
    if d.market:
        from . import market as market_mod
        out.append(f"  - {market_mod.annotate(d.market)}")
        if d.disputed:
            out.append("  - ⚠ lineup points and the market disagree on this one")
    return out


def _chips_lines(ctx) -> list[str]:
    """Step 1 of the slot-based plan, at the top of the radar: what I can sell
    without my lineup noticing, and who would START him as an upgrade -- a
    buyer found in the buyer's currency, overall rank, not in my points."""
    from . import marginal
    ranks = _rank_panel(ctx)
    if not ranks:
        return ["- chips: not ranked — no rank panel this run"]
    mine = ctx["roster_players"][ctx["my_rid"]]
    others = {ctx["users_by_rid"].get(rid, f"roster {rid}"): r
              for rid, r in ctx["roster_players"].items()
              if rid != ctx["my_rid"] and r}
    shape = {"slots": ctx["slots"], "flex": ctx.get("flex", 0),
             "flex_slots": ctx.get("flex_slots")}
    try:
        rows = marginal.tradeable(mine, others, shape, key="ros",
                                  waivers=_waiver_pool(ctx), ranks=ranks)
    except Exception as e:  # noqa: BLE001
        log.warning("trade radar: chips failed (%s)", e)
        return []
    out = ["- chips (cheap for me to sell, and someone would start him as an upgrade):"]
    shown = 0
    for r in rows:
        if not r["rank_buyers"]:
            break
        pl = r["player"]
        out.append(f"  - {pl['name']} ({pl['pos']}) costs my lineup {r['true_cost']:.1f} "
                   f"— buyers: {', '.join(r['rank_buyers'][:4])}")
        shown += 1
        if shown >= 3:
            break
    if shown == 0:
        out.append("  - none: nothing I hold is both cheap for me and an upgrade for anyone")
    return out


def build(ctx, store) -> str:
    week = ctx["week"]
    header = f"## Trade radar — week {week}"
    if week < TRADE_WEEKS[0]:
        return f"{header}\n\nscan ran; radar intentionally quiet before week {TRADE_WEEKS[0]}."
    if week > TRADE_WEEKS[1]:
        return (f"{header}\n\npast week {TRADE_WEEKS[1]} — deadline is week {DEADLINE_WEEK} "
                f"with a 2-day review window; new negotiations are unlikely to clear it.")

    vals, note = values(store, ctx)
    lines = [header, ""]
    if note:
        lines.append(f"⚠ {note}")
    if not vals:
        return "\n".join(lines + ["radar cannot rank without values this week."])

    lines += _chips_lines(ctx)
    lines.append("")

    from . import age_decay
    acfg = (ctx.get("scfg") or {}).get("age_decay") or {}

    def val(p) -> int:
        """FantasyCalc value with the in-season age decay applied (display and
        trade logic only — never a draft-layer number)."""
        raw = vals.get(str(p["sleeper_id"]), 0)
        if not raw:
            return 0
        f = age_decay.decay_factor(p.get("pos"), (ctx.get("age_of") or {}).get(
            str(p["sleeper_id"])), int(ctx["week"]), acfg)
        return int(round(raw * f))

    mine = ctx["roster_players"][ctx["my_rid"]]
    shape_args = (ctx["slots"], ctx["flex"], _flex_split(ctx))
    my_sd = surplus_deficit(mine, *shape_args)
    records = {int(r["roster_id"]): (int((r.get("settings") or {}).get("wins", 0)),
                                     int((r.get("settings") or {}).get("losses", 0)))
               for r in ctx["rosters"]}
    wins_sorted = sorted((w for w, _ in records.values()), reverse=True)
    sixth_seed_wins = wins_sorted[5] if len(wins_sorted) >= 6 else 0

    opps = []
    for rid, roster in ctx["roster_players"].items():
        if rid == ctx["my_rid"] or not roster:
            continue
        mgr = ctx["users_by_rid"].get(rid, f"roster {rid}")
        their_sd = surplus_deficit(roster, *shape_args)
        w, l = records.get(rid, (0, 0))
        seller = week > 5 and w < l and (sixth_seed_wins - w) >= 2

        # desperation: their optimal starter freshly Out/IR where I hold the shape
        desperation = None
        starters = optimal_lineup(roster, ctx["slots"], flex_slots=ctx["flex_slots"])
        for s in starters:
            if (s.get("status") or "") in ("Out", "IR") and store.first_time(
                    f"desp:{rid}:{s['sleeper_id']}:{s.get('status')}"):
                shaped = [p for p in mine if p["pos"] == s["pos"]
                          and 0.6 * val(s) <= val(p) <= 1.4 * val(s)
                          and my_sd.get(p["pos"], 0) > 0]
                if shaped:
                    desperation = (s, shaped[0])
                    break

        # structural fit: they're deep where I'm thin, and vice versa
        fit = None
        for pos in ("RB", "WR", "TE", "QB"):
            if their_sd.get(pos, 0) >= 2 and my_sd.get(pos, 0) < 0:
                gives = [p for p in roster if p["pos"] == pos and val(p) > 0]
                for pos2 in ("RB", "WR", "TE"):
                    if my_sd.get(pos2, 0) >= 2 and their_sd.get(pos2, 0) < 0:
                        mine_give = [p for p in mine if p["pos"] == pos2 and val(p) > 0]
                        if gives and mine_give:
                            ask = max(gives, key=val)
                            offer = max(mine_give, key=lambda p: val(p) if val(p) <= val(ask) else -val(p))
                            fit = (ask, offer)
                if fit:
                    break

        if desperation:
            s, give = desperation
            opps.append({
                "score": 100 + val(s), "mgr": mgr,
                "ask": "whatever unlocks their week" if seller else f"a piece back for {give['name']}",
                "offer": give["name"],
                "why": f"their starter {s['name']} just went {s['status']} and {give['name']} "
                       f"is the replacement-shaped asset I can spare",
                "urgency": "48-HOUR WINDOW — text today",
                "playoff": playoff_schedule(ctx, give.get("team") or "", give.get("pos") or "RB"),
                "ratio": None,
                "rid": rid, "give_p": [give], "get_p": [],
            })
        elif fit:
            ask, offer = fit
            ratio = (val(offer) / val(ask)) if val(ask) else 1.0
            opps.append({
                "score": 50 + val(ask) + (25 if seller else 0), "mgr": mgr,
                "ask": f"{ask['name']} ({ask['pos']}, value {val(ask)})",
                "offer": f"{offer['name']} ({offer['pos']}, value {val(offer)})",
                "why": (f"they are +{their_sd.get(ask['pos'], 0)} deep at {ask['pos']} where I'm thin; "
                        f"I'm deep at {offer['pos']}"
                        + ("; they're falling out of the race (seller window)" if seller else "")),
                "urgency": "seller window — this discount grows weekly" if seller else "no rush",
                "playoff": playoff_schedule(ctx, ask.get("team") or "", ask.get("pos") or "RB"),
                "ratio": ratio,
                "rid": rid, "give_p": [offer], "get_p": [ask],
            })

    opps.sort(key=lambda o: -o["score"])
    shown = 0
    for o in opps:
        sig = f"radar:{o['mgr']}:{o['ask']}:{o['offer']}"
        if not store.first_time(sig):
            continue  # suppressed repeat, conditions unchanged
        shown += 1
        lines += [f"**{shown}. {o['mgr']}** — ask about {o['ask']}",
                  f"- offer: {o['offer']}",
                  f"- why: {o['why']}",
                  f"- urgency: {o['urgency']}"]
        if o["playoff"]:
            lines.append(f"- playoff schedule (buying for wks 15-17): {o['playoff']}")
        # PRICE IT, do not just name it. The radar has always said who to
        # text and about what; until now it never said what the package
        # actually does to either lineup, which is the only thing that
        # decides whether to send it. Both sides re-solve, bench promotions
        # included -- see manager.marginal.slot_moves.
        lines += _priced(ctx, o, vals)
        aged = [age_decay.note(p.get("pos"), (ctx.get("age_of") or {}).get(str(p.get("sleeper_id"))),
                               int(ctx["week"]), acfg) for p in (mine or [])]
        if o["ratio"] is not None and (o["ratio"] < VETO_RATIO or o["ratio"] > 1 / VETO_RATIO):
            lines.append("- ⚠ value gap large enough to draw veto votes (6 of 12 kill it; "
                         "2-day review) — pad the light side")
        if shown >= MAX_OPPS:
            break
    if shown == 0:
        lines.append("no new opportunities this week (repeats suppressed).")
    if week >= 9:
        lines.append(f"\n⏰ deadline week {DEADLINE_WEEK} + 2-day review: initiate by week 10.")
    return "\n".join(lines)
