"""What actually gets delivered: short, plain, action-first.

The user's rule (2026-09-16 review of the first production samples): if the
league app already shows it, do not send it. Send what needs a decision --
start/sit changes, claims and the drop that makes room, injury changes with
the replacement, deadlines -- as soon as it is known, in plain words.

So the analysis modules keep computing everything and writing their long
form to reports/manager/*.md for debugging, and THIS module renders the
delivered body from the structured summary each builder stashes on
ctx["_summary"]. Rules of the house style:
  * the subject line is the action; the body is a numbered list of actions
  * one reason per action, a dozen words at most
  * numbers only where they decide something (a projected edge, a bid)
  * no provenance, no source warnings, no dashes-as-punctuation, no dots
  * nothing to do means nothing sent
"""

from __future__ import annotations

import re
from datetime import datetime

from .clock import PT, fmt

WAIVER_DEADLINE_TEXT = {"faab": "Bids lock 7:00 PM PT tonight.",
                        "rolling": "Claims process overnight tonight. Put them in before you sleep."}


def plain_why(why: str, pos: str | None = None) -> str:
    """One reason in words a person would say. The analysis keeps its
    shorthand ("target share 14% -> 21%; carries 0; snaps 82%") for the
    report; the phone gets the two numbers that matter, zeros dropped."""
    why = (why or "").strip()
    if not why:
        return ""
    m = re.match(r"inherits role: (.+?) \((\w+)\) on (\w+)", why)
    if m:
        status = {"IR": "on IR", "PUP": "on PUP"}.get(m.group(2), m.group(2))
        return f"{m.group(1)} is {status}, he inherits the role"
    m = re.match(r"([\d,]+) Sleeper adds/24h", why)
    if m:
        return f"{m.group(1)} managers added him in the last day"
    if "snaps" in why or "target share" in why or "carries" in why:
        vals = {}
        for part in why.split(";"):
            mm = re.match(r"\s*(target share|targets|carries|rec yds|snaps)\s+(?:([\d.]+%?) -> )?([\d.]+%?)", part)
            if mm:
                vals[mm.group(1)] = (mm.group(2), mm.group(3))

        def say(key, label):
            if key not in vals:
                return None
            prev, cur = vals[key]
            if cur.rstrip("%") in ("0", "0.0"):
                return None
            up = ""
            if prev is not None and prev != cur:
                up = f", {'up' if float(cur.rstrip('%')) > float(prev.rstrip('%')) else 'down'} from {prev}"
            return label.format(cur) + up

        order = ([("carries", "{} carries"), ("target share", "{} of targets"), ("snaps", "{} of snaps")]
                 if pos == "RB" else
                 [("target share", "{} of targets"), ("snaps", "{} of snaps"), ("carries", "{} carries")])
        said = [x for x in (say(k, lab) for k, lab in order) if x][:2]
        if said:
            return "Last week: " + " and ".join(said)
    return why.replace(" — ", ". ").replace("—", ",").replace("–", ",")


def _plain_move(move: str) -> str:
    move = move.rstrip(".")
    if move.lower().startswith("no clean drop"):
        return "No obvious drop, only claim him if he beats your worst bench player"
    return re.sub(r"\s*\(.*\)$", "", move).replace(" — ", ", ").replace("—", ",")


def warnings_block(ctx) -> list[str]:
    """Anything that can make the advice below wrong, in plain words.

    Only ctx["data_warnings"] -- the report's `stale` banner is a list of
    provenance notes and does not belong on a phone.
    """
    return [str(w) for w in (ctx.get("data_warnings") or [])]


def _last(name: str) -> str:
    """Surname for a second mention. Suffixes stay with the surname."""
    parts = (name or "").split()
    if len(parts) >= 2 and parts[-1].rstrip(".") in ("Jr", "Sr", "II", "III", "IV"):
        return " ".join(parts[-2:])
    return parts[-1] if parts else name


def _num(x: float) -> str:
    return f"{x:.1f}".rstrip("0").rstrip(".")


CLASS_WORDS = {"league_winner": "he could start for you every week",
               "breakout": "starter upside",
               "speculative": "a stash, not a starter yet",
               "streamer": "a one week play"}


def swap_why(f: dict, mode: str = "neutral") -> str:
    """One sentence on why the swap: the two projections, then the single
    fact that separates them (a status, a game total, or how far the
    sources disagree)."""
    if not f:
        return ""
    a, b = _last(f["in"]), _last(f["out"]) if f.get("out") else None
    parts = []
    if b:
        parts.append(f"{a} projects {_num(f['in_pts'])}, {b} {_num(f['out_pts'] or 0)}")
    else:
        parts.append(f"{a} projects {_num(f['in_pts'])} and the slot was empty")
    if f.get("out_status"):
        parts.append(f"{b} is {f['out_status']}")
    elif f.get("in_status"):
        parts.append(f"{a} is {f['in_status']} but still the better play")
    # The Vegas note carries its own sign: "implied 28 (+5%)" is a high
    # total, "implied 16 (-5%)" a low one. One phrase at most.
    vin = re.search(r"implied (\d+) \(([+-])", f.get("in_vegas") or "")
    vout = re.search(r"implied (\d+) \(([+-])", f.get("out_vegas") or "")
    if vin and vin.group(2) == "+":
        parts.append(f"{a}'s team is in a high scoring game, {vin.group(1)} points implied")
    elif vin:
        parts.append(f"{a}'s game is a low scoring one, {vin.group(1)} points implied, and he still projects higher")
    elif vout and b and vout.group(2) == "+":
        parts.append(f"{b}'s team is in the higher scoring game, {vout.group(1)} points implied, but {a} still projects higher")
    elif vout and b:
        parts.append(f"{b}'s game is a low scoring one, {vout.group(1)} points implied")
    gap = abs(f["in_pts"] - (f["out_pts"] or 0))
    if b and f.get("spread", 0) > max(gap, 1.0) * 3:
        parts.append(f"the sources disagree by {f['spread']:.0f} on these two, so this is close to a coin flip"
                     + (" and the higher ceiling wins it" if mode == "ceiling" else
                        " and the safer floor wins it" if mode == "floor" else ""))
    return ". ".join(p[:1].upper() + p[1:] for p in parts)


def add_why(a: dict, faab: bool) -> list[str]:
    """Up to two lines under a claim: what he is and what he is worth,
    then the bid logic."""
    out = []
    parts = []
    w = plain_why(a.get("why") or "", a.get("pos"))
    if w:
        parts.append(w)
    ros, drop_ros = a.get("ros"), a.get("drop_ros")
    if ros and a.get("drop") and drop_ros is not None:
        parts.append(f"{_last(a['name'])} projects {ros:.0f} points the rest of the way, "
                     f"{_last(a['drop'])} {drop_ros:.0f}")
    elif ros:
        parts.append(f"projects {ros:.0f} points the rest of the way")
    e = a.get("ecr")
    if e and e.get("ecr") is not None:
        parts.append(f"experts have him {e['pos']}{e['ecr']:.0f}, best case {e['pos']}{e['best']:.0f}")
    cls = CLASS_WORDS.get(a.get("cls") or "")
    if cls:
        parts.append(cls)
    if parts:
        out.append("Why: " + ". ".join(p[:1].upper() + p[1:] for p in parts) + ".")
    if faab and a.get("fair") is not None:
        if a.get("contingent"):
            out.append("Bid: he backs up a downed starter, so pay the high end.")
        elif a.get("rivals"):
            budgets = " and ".join(f"${b}" for b in a["rivals"][:2])
            out.append(f"Bid: rivals with a need at {a['pos']} hold {budgets}, so lean to the high end.")
        else:
            out.append("Bid: no rival is forced to bid here, so the low end should land him.")
    elif not faab and a.get("contingent"):
        out.append("He backs up a downed starter, so he is worth more than his spot in this list suggests.")
    return out


def _name(p) -> str:
    return (p.get("name") or str(p.get("sleeper_id")))


def _when(dt: datetime) -> str:
    """'Thu 5:15 PM' style, Pacific."""
    d = dt.astimezone(PT)
    return d.strftime("%a %I:%M %p").replace(" 0", " ").lstrip("0")


# ------------------------------------------------------------------ lineup

COINFLIP = 1.5   # lineup_opt.COINFLIP: under this a swap is a nudge, not ACT NOW


def _gain(swap: str) -> float:
    m = re.search(r"\(\+([\d.]+)", swap)
    return float(m.group(1)) if m else 0.0


def lineup(ctx, summary: dict) -> tuple[str | None, str, bool]:
    """(subject, body, act_now). subject None means: nothing to send."""
    swaps = list(summary.get("swaps") or [])
    table = dict(summary.get("contingency") or {})
    mode = summary.get("mode") or "neutral"
    lock = summary.get("first_lock")
    if not swaps:
        return None, "", False
    facts = summary.get("facts") or {}
    shown = [x[:1].upper() + x[1:] for x in swaps]
    first = shown[0].split(" (")[0]
    subject = first if len(shown) == 1 else f"{first}, and {len(shown) - 1} more"
    lines = []
    warn = warnings_block(ctx)
    if warn:
        lines += warn + [""]
    lines.append("Set your lineup:")
    for i, (raw, s) in enumerate(zip(swaps, shown), 1):
        lines.append(f"{i}. {s}")
        why = swap_why(facts.get(raw) or {}, mode)
        if why:
            lines.append(f"   Why: {why}.")
    swaps = shown
    if mode != "neutral":
        lines.append("")
        lines.append("You are the " + ("underdog this week: take the higher ceiling on coin flips."
                                       if mode == "ceiling" else
                                       "favorite this week: take the safer floor on coin flips."))
    if table:
        lines += ["", "If a starter is ruled out:"]
        for name, repl in table.items():
            lines.append(f"- {name} out: start {repl.split(' (')[0]}")
    if lock:
        lines += ["", f"First lock {lock}."]
    return subject, "\n".join(lines), any(_gain(x) >= COINFLIP for x in swaps)


# ----------------------------------------------------------------- waivers

def waivers(ctx, summary: dict) -> tuple[str | None, str, bool]:
    adds = list(summary.get("adds") or [])[:3]
    ir = list(summary.get("ir") or [])
    faab = bool(ctx.get("faab", True))
    if not adds and not ir:
        return None, "", False
    lines = []
    warn = warnings_block(ctx)
    if warn:
        lines += warn + [""]
    if ir:
        lines.append("Roster first:")
        lines += [f"- {x}" for x in ir]
        lines.append("")
    if adds:
        lines.append("Claims, in order:")
        used: dict[str, int] = {}
        for i, a in enumerate(adds, 1):
            move = _plain_move(a.get("move") or "")
            drop = a.get("drop")
            if drop and drop in used:
                # One player can only be dropped once: the later claim is the
                # fallback if the earlier one misses.
                move = f"Drop {drop} if claim {used[drop]} misses"
            elif drop:
                used[drop] = i
            price = f" Bid ${a['fair']} to ${a['agg']}." if faab and a.get("fair") is not None else ""
            lines.append(f"{i}. Claim {a['name']} ({a['pos']}, {a.get('team') or '?'}). {move}.{price}")
            lines += [f"   {w}" for w in add_why(a, faab)]
        lines.append("")
    lines.append(WAIVER_DEADLINE_TEXT["faab" if faab else "rolling"])
    if faab and summary.get("budget") is not None:
        lines.append(f"FAAB left: ${summary['budget']}.")
    if not faab and summary.get("priority"):
        lines.append(f"Your waiver priority: {summary['priority']} of {summary.get('teams', '?')}.")
    top = adds[0] if adds else None
    subject = (f"Claim {top['name']}" + (f", drop {top['drop']}" if top.get("drop") else "")
               if top else ir[0].split(":")[0])
    return subject, "\n".join(lines), False


# ------------------------------------------------------------------- plan

def trade_deadline_text(ctx) -> str | None:
    """Sleeper keeps the deadline as a week number in settings (99 = none);
    Yahoo as a date on the league. Either way, a phrase or None."""
    if ctx.get("trade_deadline_text"):
        return str(ctx["trade_deadline_text"])
    league = ctx.get("league") or {}
    for raw in (league.get("trade_deadline"), (league.get("settings") or {}).get("trade_deadline")):
        if raw in (None, "", 0):
            continue
        text = str(raw)
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}.*", text):
            d = datetime.fromisoformat(text[:10])
            return d.strftime("%a %b %d").replace(" 0", " ")
        if text.isdigit():
            return f"after week {int(text)} games" if int(text) < 90 else None
    return None


def plan(week: int, jobs: list[dict], ctx, faab: bool = True) -> tuple[str, str]:
    """Deadlines only: when bids lock, when your players lock, trade deadline."""
    locks = {}
    for j in jobs:
        if j.get("kind") == "slate_check" and j.get("kickoff"):
            k = datetime.fromisoformat(j["kickoff"])
            locks.setdefault(k, sorted(j.get("teams") or []))
    lines = [f"Week {week} deadlines:"]
    lines.append("- Waiver " + ("bids: Tuesday 7:00 PM PT." if faab else "claims: Tuesday night."))
    for k in sorted(locks):
        lines.append(f"- {_when(k)}: {', '.join(locks[k])} lock.")
    td = trade_deadline_text(ctx)
    if td:
        lines.append(f"- Trade deadline: {td}.")
    first = min(locks) if locks else None
    subject = (f"Week {week}: first lock {_when(first)} ({', '.join(locks[first])})"
               if first else f"Week {week} deadlines")
    return subject, "\n".join(lines)


# --------------------------------------------------------------- injuries

BAD = ("Out", "IR", "Doubtful", "Suspended", "Inactive", "PUP")


def injury_changes(changes: list[dict], contingency: dict, starters: set[str]) -> tuple[str | None, str, bool]:
    """changes: [{pid, name, pos, old, new, note}]. A starter going Out or
    Doubtful is an ACT NOW with his replacement; the rest is one line each."""
    if not changes:
        return None, "", False
    lines = []
    heads = []
    hot = []
    urgent = False
    for c in changes:
        status = c["new"] or "healthy"
        note = f" ({c['note']})" if c.get("note") else ""
        line = f"{c['name']} ({c['pos']}): {status}{note}"
        heads.append(line)
        hot.append(c["pid"] in starters and c["new"] in BAD)
        if c["pid"] in starters and c["new"] in BAD:
            repl = contingency.get(c["name"])
            if repl:
                m = re.match(r"(.+?) \((\w+), ([\d.]+) pts\)", repl)
                line += (f". Start {m.group(1)} instead, your best bench {m.group(2)} at {_num(float(m.group(3)))} projected."
                         if m else f". Start {repl.split(' (')[0]} instead.")
            else:
                line += ". Start your best bench option instead."
            urgent = True
        elif c["pid"] in starters and c["new"] == "Questionable":
            repl = contingency.get(c["name"])
            if repl:
                line += f". If he sits, start {repl.split(' (')[0]}."
        lines.append(line)
    # The urgent one leads the subject when there are several.
    order = sorted(range(len(lines)), key=lambda i: 0 if hot[i] else 1)
    head = heads[order[0]]
    subject = head if len(lines) == 1 else f"{head}, and {len(lines) - 1} more"
    return subject, "\n".join(lines), urgent


# ------------------------------------------------------------------ ledger

def ledger(week: int, grades: dict) -> tuple[str | None, str]:
    lu, sc = grades.get("lineup") or {}, grades.get("scout") or {}
    adds = [a for a in grades.get("waiver_add") or [] if a.get("delta") is not None]
    if not grades.get("graded"):
        return None, ""
    lines = [f"Week {week}, how the calls did:"]
    if lu.get("efficiency") is not None:
        lines.append(f"- Lineup: {lu['chosen_pts']:.1f} points, {lu['efficiency']:.0%} of the best you could have started "
                     f"({lu['left_on_bench']:.1f} left on the bench).")
    if sc.get("graded"):
        lines.append(f"- Result: {'won' if sc['won'] == 1 else 'lost' if sc['won'] == 0 else 'tied'} by "
                     f"{abs(sc['actual_margin']):.1f}; the model had you {'winning' if float(grades.get('win_prob', 0.5)) >= 0.5 else 'losing'}.")
    if adds:
        good = sum(1 for a in adds if a["delta"] > 0)
        lines.append(f"- Waiver calls: {good} of {len(adds)} recommended adds outscored the drop that week.")
    return f"Week {week} graded", "\n".join(lines)
