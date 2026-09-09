"""Yahoo leagues through the same trade framework, from a scraped roster file.

Yahoo's Fantasy API has been approval-gated since 2026-07-22, so there is no
data path and manager.context refuses the platform outright. That refusal is
right for the scheduled jobs -- a brief built on a guess is worse than no
brief -- but it left Keefamania with no way to use manager.marginal at all,
and every trade priced for it this week was priced in a throwaway script.

This is the adapter. Rosters come from a periodic browser scrape (see
`docs` in memory: players?status=T on the Yahoo players page), land in
data/raw/yahoo/<league>.txt as `POS|Player Name|Owner`, and are resolved to
sleeper_ids so that marginal.price, slot_moves and explain work on them
UNCHANGED. Same code, same numbers, same seat-by-seat output as Omnibeta.

What the scrape cannot carry, and the caller must not assume:
  * injury designations -- there is no status field, so nothing here can
    tell you a player is Out. Check Yahoo before acting on a lineup.
  * the file is a SNAPSHOT. `as_of` is its mtime and `stale_days` is how old
    it is; anything past a couple of days should be re-scraped before a
    trade is sent, because a roster that moved makes every number wrong.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path

log = logging.getLogger("manager")

ROSTER_DIR = Path("data/raw/yahoo")
SKILL = ("QB", "RB", "WR", "TE")
STALE_DAYS = 2.0


def roster_path(league: str) -> Path:
    return ROSTER_DIR / f"{league}.txt"


def _shape_from_cfg(cfg) -> dict:
    """{slots, flex} for the skill positions, from the league's roster list.

    K and DEF are dropped: no projection source in this repo covers them --
    the Sleeper request names QB/RB/WR/TE only -- so including their slots
    would price a lineup against zeros.
    """
    exp = (cfg.get("expected") if hasattr(cfg, "get") else None) or {}
    roster = (cfg.get("roster") if hasattr(cfg, "get") else None) or exp.get("roster") or []
    slots: dict[str, int] = {}
    flex = 0
    for raw in roster:
        s = str(raw).upper().replace(" ", "")
        if s in SKILL:
            slots[s] = slots.get(s, 0) + 1
        elif s in ("W/R/T", "FLEX", "WRT", "R/W/T"):
            flex += 1
    return {"slots": slots, "flex": flex}


def load(cfg, players: dict, con: dict | None = None,
         key: str = "mean", crosswalk: dict | None = None
         ) -> tuple[dict[str, list[dict]], dict, list[str]]:
    """(owner -> rows, shape, notes).

    Rows are the shape manager.marginal expects: sleeper_id, pos, name, and
    `weekly` carrying the consensus value so the optimiser sorts on it.
    Unmatched names are REPORTED, never dropped silently -- a roster missing
    two players prices every trade for that team wrong, and the caller has
    to be able to see it.

    `crosswalk` is manager.fantasypros.crosswalk(), optional. Yahoo and
    FantasyPros are both fantasy-industry feeds and often agree on a
    rendering Sleeper writes differently, so a name the Sleeper index misses
    can still land. It is a SECOND SPELLING, not a second identity: the
    crosswalk resolves its own names through the same Sleeper index, so it
    widens coverage without making any single match more certain. The exact
    join needs the scrape to carry Yahoo's player id, which it does not yet.
    """
    from draftkit.ids import normalize_name

    league = getattr(cfg, "league_name", None) or "unknown"
    path = roster_path(league)
    notes: list[str] = []
    if not path.exists():
        return {}, _shape_from_cfg(cfg), [
            f"DATA MISSING: no Yahoo roster snapshot at {path} — scrape it first"]

    age = (time.time() - path.stat().st_mtime) / 86400.0
    stamp = time.strftime("%Y-%m-%d %H:%M", time.localtime(path.stat().st_mtime))
    if age > STALE_DAYS:
        notes.append(f"⚠ Yahoo roster snapshot is {age:.1f} days old ({stamp}) — "
                     f"re-scrape before acting on a trade")
    else:
        notes.append(f"yahoo rosters scraped {stamp}")

    by_norm: dict[str, list[str]] = {}
    for pid, d in (players or {}).items():
        if not isinstance(d, dict):
            continue
        nm = d.get("full_name") or d.get("last_name")
        if nm and d.get("position"):
            by_norm.setdefault(normalize_name(nm), []).append(str(pid))

    con = con or {}
    cw_name = ((crosswalk or {}).get("by_name")) or {}
    out: dict[str, list[dict]] = {}
    unmatched: list[str] = []
    ambiguous: list[str] = []
    for line in path.read_text(encoding="utf-8").strip().splitlines():
        parts = line.split("|")
        if len(parts) != 3:
            continue
        pos, name, owner = (p.strip() for p in parts)
        if pos not in SKILL:
            out.setdefault(owner, [])            # keep the team, skip K/DEF
            continue
        cand = [x for x in by_norm.get(normalize_name(name), [])
                if (players.get(x) or {}).get("position") == pos]
        if not cand and cw_name:
            # Second spelling. "Harold Fannin Jr." on the Yahoo page against
            # "Harold Fannin" in the Sleeper index is the common shape.
            cand = [pid for pid, cw_pos, _ in cw_name.get(normalize_name(name), [])
                    if cw_pos == pos]
        if not cand:
            unmatched.append(f"{name} ({pos})")
            continue
        if len(cand) > 1:
            # AMBIGUITY WAS A SILENT WRONG ANSWER. cand[0] picked whichever
            # Mike Williams the index happened to list first and priced that
            # team around him. A duplicate name is a roster the caller must
            # resolve by hand, so it is reported like any other miss --
            # short by one is visible, wrong by one is not.
            ambiguous.append(f"{name} ({pos}, {len(cand)} matches)")
            continue
        pid = cand[0]
        out.setdefault(owner, []).append({
            "sleeper_id": pid, "pos": pos, "name": name,
            "weekly": float((con.get(pid) or {}).get(key) or 0.0),
        })

    if unmatched:
        notes.append(f"⚠ {len(unmatched)} roster names did not resolve to a player id, "
                     f"so their teams are priced short: {', '.join(unmatched[:6])}")
    if ambiguous:
        notes.append(f"⚠ {len(ambiguous)} roster names match more than one player and "
                     f"were NOT guessed, so their teams are priced short: "
                     f"{', '.join(ambiguous[:6])}")
    notes.append(f"{len(out)} teams, {sum(len(v) for v in out.values())} skill players")
    return out, _shape_from_cfg(cfg), notes
