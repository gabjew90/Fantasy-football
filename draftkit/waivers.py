"""Waiver claims engine + Tuesday brief (season spec Task 5).

Claim classes, in priority order:
  contingency — a free agent whose team's ROSTERED starter at his position is
                Out/IR anywhere in the league (the league-winning class)
  spike       — usage-trend role change with named evidence
  streamer    — DEF/K by next week's matchup multiplier

FAAB bands are fractions of REMAINING budget scaled by regime; the
league-winner class is exempt from calibration and uses sealed-bid logic
(max budget of position-needy rivals + $5), capped by the band and by the
asset's value to MY roster. Recommend-only; the user taps in Sleeper.
"""

from __future__ import annotations

REGIME_MULT = {"BUBBLE": 1.25, "LONGSHOT": 1.25, "SAFE": 0.8, "COMFORTABLE": 1.0}


def classify_contingencies(fa_pool: list[dict], rosters: dict[int, list[dict]],
                           injury: dict[str, str]) -> list[dict]:
    """FAs who inherit a role because a rostered same-team same-pos player is Out/IR."""
    downed: dict[tuple[str, str], str] = {}
    for roster in rosters.values():
        for p in roster:
            status = injury.get(str(p.get("sleeper_id")), "")
            if status in ("Out", "IR", "PUP"):
                downed[(p.get("team"), p.get("pos"))] = f"{p.get('name')} ({status})"
    claims = []
    for fa in fa_pool:
        key = (fa.get("team"), fa.get("pos"))
        if key in downed:
            claims.append({**fa, "cls": "contingency",
                           "evidence": f"inherits role: {downed[key]} on {fa.get('team')}"})
    claims.sort(key=lambda c: -(c.get("ros") or 0.0))
    return claims


def bid_band(cls: str, remaining_budget: int, regime: str, faab: dict,
             rival_max_budget: int | None = None,
             value_cap: int | None = None) -> tuple[int, int]:
    """(fair, aggressive) dollar band for a claim class."""
    lo, hi = faab[cls]
    mult = REGIME_MULT.get(regime, 1.0)
    fair = max(1, round(lo * remaining_budget))
    aggressive = max(1, round(hi * remaining_budget * mult))
    if cls == "league_winner" and rival_max_budget is not None:
        # sealed-bid: beat the most desperate rival by $5 — but never pay more
        # than the band or more than the player is worth to MY roster
        sealed = rival_max_budget + 5
        aggressive = min(sealed, aggressive, value_cap or aggressive, remaining_budget)
        fair = min(fair, aggressive)
    cap = round(faab.get("max_week_commit", 1.0) * remaining_budget)
    return min(fair, cap), min(aggressive, cap)


def protected_drop_ids(bench: list[dict], my_starter_names: set[str],
                       ir_occupants: set[str]) -> set[str]:
    """Never suggest dropping: handcuffs of MY starters, IR occupants."""
    prot = set()
    for p in bench:
        pid = str(p.get("sleeper_id"))
        if pid in ir_occupants:
            prot.add(pid)
        elif p.get("backs_up") and p["backs_up"] in my_starter_names:
            prot.add(pid)
    return prot


def ir_actions(ir_occupants: list[dict], roster: list[dict],
               injury: dict[str, str], reserve_allow: tuple[str, ...]) -> list[str]:
    """Both IR directions (spec review finding #5)."""
    acts = []
    for p in ir_occupants:
        status = injury.get(str(p.get("sleeper_id")), "")
        if status not in reserve_allow:
            acts.append(
                f"🔴 {p.get('name')} is now '{status or 'healthy'}' — Sleeper will "
                f"invalidate your roster: you MUST move him off IR and cut someone "
                f"before lineups lock."
            )
    if not ir_occupants:
        for p in roster:
            status = injury.get(str(p.get("sleeper_id")), "")
            if status in reserve_allow:
                acts.append(
                    f"IR slot is EMPTY and {p.get('name')} is {status} — move him to "
                    f"IR for a free roster spot, then claim with the opening."
                )
                break
    return acts


def render_waiver_brief(model: dict) -> str:
    m = model
    lines = [
        f"# Waiver Brief — week {m['week']}",
        "",
        f"**Record {m['record']} · playoff odds {m['odds']:.0%} · regime "
        f"{m['regime']} · ${m['remaining_budget']} FAAB left**",
        "",
    ]
    if m.get("stale"):
        lines += [f"⚠ STALE DATA: {', '.join(m['stale'])} — recommendations use last-good values.", ""]
    if m.get("preseason_note"):
        lines += [f"⚠ {m['preseason_note']}", ""]
    for a in m.get("ir_actions", []):
        lines.append(f"**{a}**")
    if m.get("ir_actions"):
        lines.append("")
    lines.append("## Claims (in order)")
    if not m.get("claims"):
        lines.append("- no claims clear the bar this week")
    for i, c in enumerate(m.get("claims", []), 1):
        lines += [
            f"{i}. **{c['name']}** ({c['pos']}) — {c['cls']}",
            f"   - why: {c['evidence']}",
            f"   - bid: **${c['fair']}–${c['aggressive']}** · drop: {c.get('drop') or '(open spot)'}",
        ]
        if c.get("rivals_note"):
            lines.append(f"   - competition: {c['rivals_note']}")
        if c.get("keeper_appeal"):
            lines.append(f"   - keeper note: {c['keeper_appeal']}")
    if m.get("scoreboard_md"):
        lines += ["", m["scoreboard_md"]]
    return "\n".join(lines) + "\n"
