"""Module 5 — trade radar (weeks 3–10, appended to the Tuesday brief).

Target identification, not fairness math: who to text and about what.
Values come from FantasyCalc (redraft, full PPR, 12 team, 1 QB); this module
never builds its own valuation. Repeats are suppressed via state unless the
opportunity's conditions changed.
"""

from __future__ import annotations

import logging
import time as _time

import requests

from draftkit.lineup import optimal_lineup


log = logging.getLogger("manager")

URL = ("https://api.fantasycalc.com/values/current"
       "?isDynasty=false&numQbs=1&numTeams=12&ppr=1")
TTL = 24 * 3600
MAX_OPPS = 3
VETO_RATIO = 0.7          # offer/ask value below this may draw veto votes
TRADE_WEEKS = (3, 10)     # active window; recommend initiating by week 10
DEADLINE_WEEK = 11


def values(store) -> tuple[dict[str, int], str | None]:
    """sleeper_id -> FantasyCalc redraft value. ({}, note) when unavailable."""
    cached = store.get("fantasycalc")
    if cached and _time.time() - cached.get("ts", 0) < TTL:
        return {str(k): int(v) for k, v in cached["data"].items()}, None
    try:
        resp = requests.get(URL, timeout=20)
        resp.raise_for_status()
        data = {}
        for row in resp.json():
            sid = (row.get("player") or {}).get("sleeperId")
            if sid:
                data[str(sid)] = int(row.get("value") or 0)
        store.set("fantasycalc", {"ts": _time.time(), "data": data})
        return data, None
    except Exception as e:  # noqa: BLE001
        if cached:
            return ({str(k): int(v) for k, v in cached["data"].items()},
                    "DATA MISSING: FantasyCalc refresh failed — using cached values")
        return {}, f"DATA MISSING: FantasyCalc values ({e.__class__.__name__})"


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


def build(ctx, store) -> str:
    week = ctx["week"]
    header = f"## Trade radar — week {week}"
    if week < TRADE_WEEKS[0]:
        return f"{header}\n\nscan ran; radar intentionally quiet before week {TRADE_WEEKS[0]}."
    if week > TRADE_WEEKS[1]:
        return (f"{header}\n\npast week {TRADE_WEEKS[1]} — deadline is week {DEADLINE_WEEK} "
                f"with a 2-day review window; new negotiations are unlikely to clear it.")

    vals, note = values(store)
    lines = [header, ""]
    if note:
        lines.append(f"⚠ {note}")
    if not vals:
        return "\n".join(lines + ["radar cannot rank without values this week."])

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
        starters = optimal_lineup(roster, ctx["slots"], ctx["flex_slots"])
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
