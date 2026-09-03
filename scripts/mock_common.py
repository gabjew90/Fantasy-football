"""Shared naming and time helpers for the mock reports (2026-09-02).

The user reads the reports in Pacific time; every log writes UTC. Report
file names carry the mock label, the Pacific start time, the room's name,
its id and our seat, so a folder of them reads as a list:

    mock25_2026-09-02_2237pt_pooch-kick_room10532940_seat3.md
"""

from __future__ import annotations

import datetime as dt
import re
from zoneinfo import ZoneInfo

PT = ZoneInfo("America/Los_Angeles")


def to_pt(iso: str | None, fmt: str = "%Y-%m-%d %H:%M:%S PT") -> str:
    """An ISO timestamp (UTC 'Z' or with an offset; a bare local ISO from the
    bridge is taken as Pacific) -> Pacific wall time. Unparseable -> ''."""
    if not iso:
        return ""
    s = str(iso).strip()
    try:
        if s.endswith("Z"):
            t = dt.datetime.fromisoformat(s[:-1]).replace(tzinfo=dt.timezone.utc)
        else:
            t = dt.datetime.fromisoformat(s)
            if t.tzinfo is None:
                t = t.replace(tzinfo=PT)
        return t.astimezone(PT).strftime(fmt)
    except ValueError:
        return ""


def pt_lines(lines: list[str]) -> list[str]:
    """Driver log lines start with a full UTC ISO stamp; show them in Pacific."""
    out = []
    for l in lines:
        m = re.match(r"^(\d{4}-\d{2}-\d{2}T[\d:.]+Z)\s?(.*)$", l)
        out.append((to_pt(m.group(1), "%H:%M:%S PT") + " " + m.group(2)) if m else l)
    return out


def key(name: str) -> str:
    """first initial + last token, lower, suffixes dropped -- the board key,
    for joining names across the trail, the snapshot and the board."""
    parts = re.sub(r"[^a-z0-9 ]", " ", (name or "").lower()).split()
    parts = [p for p in parts if p not in ("jr", "sr", "ii", "iii", "iv", "v")] or parts
    return (parts[0][0] + " " + parts[-1]) if parts else ""


def slug(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", (name or "").lower()).strip("-")
    return s[:32] or "room"


def room_display_name(trail: dict, override: str | None = None) -> str:
    """The room's nickname ('Pooch Kick'), from the override, the trail's
    room_name when it is not just the tab title, else the room id."""
    if override:
        return override
    rn = str(trail.get("room_name") or "")
    if rn and "Live NFL Draft" not in rn and "|" not in rn:
        return rn
    return f"room {trail.get('room')}"


def start_iso(trail: dict) -> str | None:
    """When the driver started in this room: the first log line's stamp,
    else the capture time."""
    for l in trail.get("log") or []:
        m = re.match(r"^(\d{4}-\d{2}-\d{2}T[\d:.]+Z)", str(l))
        if m:
            return m.group(1)
    return trail.get("captured_at")


def load_trail(root, room: str) -> dict:
    """The trail JSON for a room, with the records and log saved before an
    injected/real page reload (mock_<room>_prereload.json) merged in, so
    both renderers see the whole draft and agree on its start time."""
    import json
    from pathlib import Path
    root = Path(root)
    trail = json.loads((root / "data" / "logs" / "mocks" / f"mock_{room}.json").read_text(encoding="utf-8"))
    pre = root / "data" / "logs" / "mocks" / f"mock_{room}_prereload.json"
    if pre.exists():
        before = json.loads(pre.read_text(encoding="utf-8"))
        have = {r.get("pick_no") for r in trail.get("our_records") or []}
        trail["our_records"] = [r for r in (before.get("our_records") or []) if r.get("pick_no") not in have] + (trail.get("our_records") or [])
        trail["log"] = (before.get("log") or []) + (trail.get("log") or [])
        trail["reloaded"] = before.get("captured_at")
    return trail


def report_stem(trail: dict, label: str | None, name: str | None, seat: int | None) -> str:
    lab = re.sub(r"[^a-z0-9]+", "", (label or "mock").lower()) or "mock"
    when = to_pt(start_iso(trail), "%Y-%m-%d_%H%Mpt") or "undated"
    nm = slug(room_display_name(trail, name))
    return f"{lab}_{when}_{nm}_room{trail.get('room')}_seat{seat if seat is not None else '?'}"


def header_line(trail: dict, label: str | None, name: str | None, seat: int | None, teams: int) -> str:
    when = to_pt(start_iso(trail), "%A %Y-%m-%d %H:%M PT")
    return (f"{label or 'Mock'} -- {room_display_name(trail, name)} (room {trail.get('room')}) -- "
            f"{when} -- {teams} teams, our seat {seat if seat is not None else '?'}")


HOW_THE_ENGINE_THINKS = """## How the engine thinks, in plain English

1. **Projections first.** Every player has a season points projection for this league's
   scoring. On its own that number ranks quarterbacks at the top of every list, which is why it
   is never used on its own.
2. **Value over what is freely available.** The engine subtracts, per position, the points of the
   player you could get for nothing at that position (the replacement level, derived from how
   many starters this league's format demands). That difference is the value column, VORP. A
   player who can only start in the flex is valued against the flex replacement instead.
3. **Markets, not positions.** It only shops in slots you have not filled. Once your tight end
   slot is full there is no tight end market any more; remaining tight ends compete inside the
   flex against running backs and receivers.
4. **Survival: who will still be there at your next turn.** It simulates the picks between now
   and your next turn a thousand times. Each rival takes players near their average draft
   position, prefers positions they still need, and an autopick seat follows Yahoo's default
   list more tightly than a human would. The share of simulations in which a player is still
   on the board at your next pick is the survival percentage. It never ranks anyone by itself.
5. **Cost of waiting is what ranks.** For each market: the best value available now, minus the
   best value it expects to still be there at your next turn. That is the "waiting likely costs
   about N points" line. A big player with low survival makes waiting expensive; a deep position
   makes waiting nearly free. When every cost is near zero, the most valuable player who fills a
   slot wins the tie.
6. **Two picks at once.** It checks the pair: this pick plus the best partner it expects at the
   next turn, so it does not win this pick and lose the round.
7. **Hard rules override everything.** No second quarterback before round 10, no second tight
   end unless a top-6 one has fallen far past his ADP, kicker and defense only in the last two
   picks, and never leave a starting slot unfillable.
8. **Late rounds are insurance, not points.** Once the lineup is full, a bench player is priced
   by how many weeks you will need him (position injury rates plus the bye) times his weekly
   edge over the waiver wire; a handcuff to your own starter is worth more.
9. **The driver executes and verifies.** The page asks the engine at the turn, makes the pick
   through Yahoo's own action, and confirms it in Yahoo's data before recording it. If its
   readings disagree it does nothing and the queue it keeps catches the pick.
"""
