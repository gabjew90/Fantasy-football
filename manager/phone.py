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
    swaps = [x[:1].upper() + x[1:] for x in swaps]
    first = swaps[0].split(" (")[0]
    subject = first if len(swaps) == 1 else f"{first}, and {len(swaps) - 1} more"
    lines = ["Set your lineup:"]
    for i, s in enumerate(swaps, 1):
        lines.append(f"{i}. {s}")
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
            why = plain_why(a.get("why") or "", a.get("pos"))
            if why:
                lines.append(f"   {why}.")
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
    urgent = False
    for c in changes:
        status = c["new"] or "healthy"
        note = f" ({c['note']})" if c.get("note") else ""
        line = f"{c['name']} ({c['pos']}): {status}{note}"
        heads.append(line)
        if c["pid"] in starters and c["new"] in BAD:
            repl = contingency.get(c["name"])
            line += ". Start " + (repl.split(" (")[0] if repl else "your best bench option") + " instead."
            urgent = True
        elif c["pid"] in starters and c["new"] == "Questionable":
            repl = contingency.get(c["name"])
            if repl:
                line += f". If he sits, start {repl.split(' (')[0]}."
        lines.append(line)
    # The urgent one leads the subject when there are several.
    order = sorted(range(len(lines)), key=lambda i: 0 if lines[i].endswith("instead.") else 1)
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
