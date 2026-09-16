"""Yahoo leagues through the same trade framework: the API first, a snapshot file second.

Yahoo's Fantasy API was approval-gated from 2026-07-22; Keefamania's access
was provisioned 2026-09-16 (manager/yahoo_api.py holds the OAuth side). Until
then rosters came from a browser scrape saved as `POS|Player Name|Owner` in
data/raw/yahoo/<league>.txt, and that file is still the fallback: every
successful API read rewrites it, so an API outage degrades to a roster that
is at most as old as the last good read rather than to nothing.

Either way the rows are resolved to sleeper_ids so marginal.price, slot_moves
and explain work on them UNCHANGED. The API adds three things the scrape
could not carry:
  * Yahoo's player id, joined exactly through the DynastyProcess id map
    (`id_map`), with the name match kept as the fallback;
  * each player's lineup slot (`slot`: QB, BN, IR, ...);
  * Yahoo's own injury designation (`yahoo_status`: IR, IR-R, PUP-R, O, Q,
    ...), which is what decides IR-slot eligibility in this league.
    `injury_overlay()` maps it onto the Sleeper vocabulary the trade path reads.

manager.context still refuses the platform for the scheduled jobs; this
adapter serves scripts/keefamania_trades.py.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path

log = logging.getLogger("manager")

ROSTER_DIR = Path("data/raw/yahoo")
SKILL = ("QB", "RB", "WR", "TE")
STALE_DAYS = 2.0

# Yahoo status code -> the Sleeper injury_status vocabulary manager.marginal
# reads (INJURED, DEFAULT_WEEKS_OUT). Codes measured on the live league
# 2026-09-16: IR, IR-R, PUP-R, CEL, Q; the rest are Yahoo's documented set.
YAHOO_STATUS = {
    "IR": "IR", "IR-R": "IR", "IR-NFI": "NFI",
    "PUP-R": "PUP", "PUP-P": "PUP", "NFI-R": "NFI", "NFI-A": "NFI",
    "O": "Out", "D": "Doubtful", "Q": "Questionable", "DTD": "Questionable",
    "SUSP": "Sus", "CEL": "NA", "NA": "NA", "COVID-19": "COV",
}


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


# ------------------------------------------------------------------- sources

def _flat(parts) -> dict:
    """Yahoo returns an object as a list of one-key dicts (and empty lists)."""
    out: dict = {}
    for x in parts or []:
        if isinstance(x, dict):
            out.update(x)
    return out


def api_entries(league_id, get=None) -> list[dict]:
    """Every rostered player in the league, one dict per player:
    {pos, name, owner, yahoo_id, slot, yahoo_status, injury_note}.

    `owner` is the Yahoo team name. `pos` is the first listed position of
    `display_position` ("WR,TE" -> "WR"); the rest land in `positions`.
    Raises on any API failure -- the caller decides whether to fall back.
    """
    if get is None:
        from .yahoo_api import get
    body = get(f"league/nfl.l.{league_id}/teams/roster")
    teams = body["fantasy_content"]["league"][1]["teams"]
    out: list[dict] = []
    for tk, t in teams.items():
        if tk == "count" or not isinstance(t, dict):
            continue
        owner = _flat(t["team"][0]).get("name") or f"team {tk}"
        roster = (t["team"][1].get("roster") or {}).get("0") or {}
        players = roster.get("players") or {}
        if not isinstance(players, dict) or not players:
            # An empty roster is []. The team still exists and must still be
            # listed: a rival with no players is a fact, not a missing row.
            out.append({"pos": "", "positions": [], "name": "", "owner": owner})
            continue
        for pk, pv in players.items():
            if pk == "count" or not isinstance(pv, dict):
                continue
            parts = pv.get("player") or []
            f = _flat(parts[0] if parts else [])
            sel = _flat(parts[1].get("selected_position")) if len(parts) > 1 and isinstance(parts[1], dict) else {}
            positions = [p.strip() for p in str(f.get("display_position") or "").split(",") if p.strip()]
            out.append({
                "pos": positions[0] if positions else "", "positions": positions,
                "name": (f.get("name") or {}).get("full") or "",
                "owner": owner, "yahoo_id": str(f.get("player_id") or ""),
                "slot": sel.get("position"), "yahoo_status": f.get("status"),
                "injury_note": f.get("injury_note"),
            })
    return out


def _scrape_entries(path: Path) -> list[dict]:
    out = []
    for line in path.read_text(encoding="utf-8").strip().splitlines():
        parts = line.split("|")
        if len(parts) != 3:
            continue
        pos, name, owner = (p.strip() for p in parts)
        out.append({"pos": pos, "positions": [pos], "name": name, "owner": owner})
    return out


def _write_snapshot(path: Path, entries: list[dict]) -> None:
    """Keep the fallback file as fresh as the last good API read."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"{e['pos']}|{e['name']}|{e['owner']}" for e in entries if e.get("pos") and e.get("name")]
    tmp = path.with_suffix(".tmp")
    tmp.write_text("\n".join(lines) + "\n", encoding="utf-8")
    tmp.replace(path)


# ---------------------------------------------------------------------- load

def load(cfg, players: dict, con: dict | None = None,
         key: str = "mean", crosswalk: dict | None = None, *,
         source: str = "scrape", id_map: dict | None = None, get=None
         ) -> tuple[dict[str, list[dict]], dict, list[str]]:
    """(owner -> rows, shape, notes).

    Rows are the shape manager.marginal expects: sleeper_id, pos, name, and
    `weekly` carrying the consensus value so the optimiser sorts on it. An
    API row also carries yahoo_id, slot and yahoo_status. Unmatched names are
    REPORTED, never dropped silently -- a roster missing two players prices
    every trade for that team wrong, and the caller has to be able to see it.

    `source`: "scrape" reads the snapshot file only (the default, and what the
    offline tests use); "api" reads the API only; "auto" reads the API and
    falls back to the snapshot, saying so in the notes.

    `id_map` is {yahoo_id: sleeper_id} (the DynastyProcess id map). It is the
    exact join and is tried first; a mapped id whose Sleeper position does not
    fit the Yahoo position is ignored rather than trusted.

    `crosswalk` is manager.fantasypros.crosswalk(), optional: a SECOND
    SPELLING for the name fallback, not a second identity.
    """
    from draftkit.ids import normalize_name

    league = getattr(cfg, "league_name", None) or "unknown"
    path = roster_path(league)
    shape = _shape_from_cfg(cfg)
    notes: list[str] = []
    entries: list[dict] | None = None

    if source not in ("scrape", "api", "auto"):
        raise ValueError(f"yahoo.load source {source!r} is not scrape, api or auto")
    if source in ("api", "auto"):
        league_id = getattr(cfg, "league_id", None) or (cfg.get("league_id") if hasattr(cfg, "get") else None)
        try:
            entries = api_entries(league_id, get=get)
            notes.append(f"yahoo rosters from the API {time.strftime('%Y-%m-%d %H:%M')}")
            try:
                _write_snapshot(path, entries)
            except OSError as e:
                log.warning("yahoo: could not refresh the roster snapshot (%s)", e.__class__.__name__)
        except Exception as e:  # noqa: BLE001
            reason = f"{e.__class__.__name__}: {str(e)[:120]}"
            if source == "api":
                return {}, shape, [f"DATA MISSING: Yahoo API rosters ({reason})"]
            notes.append(f"⚠ Yahoo API unavailable ({reason}) — using the roster snapshot")
            entries = None

    if entries is None:
        if not path.exists():
            return {}, shape, notes + [
                f"DATA MISSING: no Yahoo roster snapshot at {path} — scrape it first"]
        age = (time.time() - path.stat().st_mtime) / 86400.0
        stamp = time.strftime("%Y-%m-%d %H:%M", time.localtime(path.stat().st_mtime))
        if age > STALE_DAYS:
            notes.append(f"⚠ Yahoo roster snapshot is {age:.1f} days old ({stamp}) — "
                         f"re-scrape before acting on a trade")
        else:
            notes.append(f"yahoo rosters scraped {stamp}")
        entries = _scrape_entries(path)

    by_norm: dict[str, list[str]] = {}
    for pid, d in (players or {}).items():
        if not isinstance(d, dict):
            continue
        nm = d.get("full_name") or d.get("last_name")
        if nm and d.get("position"):
            by_norm.setdefault(normalize_name(nm), []).append(str(pid))

    def fits(pid: str, pos: str) -> bool:
        d = (players or {}).get(pid) or {}
        return d.get("position") == pos or pos in (d.get("fantasy_positions") or [])

    con = con or {}
    cw_name = ((crosswalk or {}).get("by_name")) or {}
    out: dict[str, list[dict]] = {}
    unmatched: list[str] = []
    ambiguous: list[str] = []
    by_id = 0
    for e in entries:
        pos, name, owner = e["pos"], e["name"], e["owner"]
        skill = [p for p in (e.get("positions") or [pos]) if p in SKILL]
        if not skill:
            out.setdefault(owner, [])            # keep the team, skip K/DEF
            continue
        pos = skill[0]
        cand: list[str] = []
        mapped = (id_map or {}).get(str(e.get("yahoo_id") or ""))
        if mapped and fits(str(mapped), pos):
            cand = [str(mapped)]
            by_id += 1
        if not cand:
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
        row = {"sleeper_id": pid, "pos": pos, "name": name,
               "weekly": float((con.get(pid) or {}).get(key) or 0.0)}
        for k in ("yahoo_id", "slot", "yahoo_status", "injury_note"):
            if e.get(k):
                row[k] = e[k]
        out.setdefault(owner, []).append(row)

    if unmatched:
        notes.append(f"⚠ {len(unmatched)} roster names did not resolve to a player id, "
                     f"so their teams are priced short: {', '.join(unmatched[:6])}")
    if ambiguous:
        notes.append(f"⚠ {len(ambiguous)} roster names match more than one player and "
                     f"were NOT guessed, so their teams are priced short: "
                     f"{', '.join(ambiguous[:6])}")
    skill_n = sum(len(v) for v in out.values())
    notes.append(f"{len(out)} teams, {skill_n} skill players"
                 + (f" ({by_id} joined on Yahoo id)" if id_map else ""))
    return out, shape, notes


def injury_overlay(rosters: dict[str, list[dict]]) -> dict[str, str]:
    """sleeper_id -> Sleeper-vocabulary status, from Yahoo's designation on
    each rostered row. Only rows Yahoo flags are returned: a healthy row says
    nothing, so the caller's Sleeper feed still speaks for it."""
    out: dict[str, str] = {}
    for rows in rosters.values():
        for r in rows:
            mapped = YAHOO_STATUS.get(str(r.get("yahoo_status") or ""))
            if mapped:
                out[str(r["sleeper_id"])] = mapped
    return out
