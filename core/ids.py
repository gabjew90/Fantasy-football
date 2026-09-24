"""Player identity resolution -- the one crosswalk.

Primary path: the DynastyProcess cross-platform ID map (fantasypros_id /
gsis_id / pfr_id / sleeper_id / espn_id / yahoo_id), cached daily through
core.fetch. Fallback path: normalized-name matching against the Sleeper player
universe (handles Jr./II suffixes, punctuation, and D/ST naming).

`sleeper_gsis` joins Sleeper ids to nflverse gsis ids, filling the ID map's
gaps (rookies arrive late) from the gsis_id Sleeper itself carries. Every
consumer that needs usage or play-by-play for a fantasy player goes through
it: matching nflverse names to Sleeper names breaks silently on duplicates
and suffixes.

Moved from draftkit/ids.py on 2026-09-24; that module re-exports these names.
"""

from __future__ import annotations

import re
from pathlib import Path

import polars as pl
from rapidfuzz import fuzz, process

# github.com/<org>/<repo>/raw/... is blocked in some environments; the
# raw.githubusercontent.com mirror (core.fetch.PLAYERIDS_URL) serves it.
from .fetch import PLAYERIDS_URL, fetch  # noqa: F401 -- PLAYERIDS_URL re-exported

CACHE_TTL = 24 * 3600

_SUFFIXES = {"jr", "sr", "ii", "iii", "iv", "v", "jr.", "sr."}

# Sleeper D/ST player_id is the team abbreviation ("SF"), full name in
# first/last ("San Francisco" / "49ers"). Other sources say "49ers D/ST",
# "San Francisco 49ers", "Niners", etc.
_DST_WORDS = {"dst", "d/st", "def", "defense", "st"}


def normalize_name(name: str) -> str:
    """Lowercase, strip punctuation and generational suffixes."""
    s = name.lower().strip()
    s = re.sub(r"[.'’]", "", s)
    s = re.sub(r"[-/]", " ", s)
    s = re.sub(r"\s+", " ", s)
    parts = [p for p in s.split(" ") if p and p not in _SUFFIXES]
    return " ".join(parts)


class NameIndex:
    """Normalised name -> Sleeper ids, with the two joins every source needs.

    It replaced three near-identical inline indexes (manager.consensus._espn,
    manager.fantasypros._index_by_name, manager.yahoo_context._by_name), each
    of which matched on `position` and dropped any name held by more than one
    player. Both rules were wrong, and measured on 2026-09-17:

    * `position` is the DEPTH-CHART slot, `fantasy_positions` is what the
      player is eligible at. Travis Hunter is position DB / fantasy WR, and
      every fullback is position FB / fantasy RB, so a source calling Hunter
      a WR matched nothing -- he was the largest unmatched row in the ESPN
      feed, and seven fullbacks went with him.
    * Retired namesakes made live players ambiguous. Three Kyle Williamses
      carry the name, two of them inactive with no team, so the live New
      England WR was dropped as "ambiguous" rather than matched.

    So: eligibility first, then prefer the candidates who are actually
    playing. Genuine ambiguity between two live players is still dropped
    rather than guessed -- a wrong match does not surface as a missing
    player, it surfaces as a lineup change.
    """

    def __init__(self, players: dict | None):
        self.by_name: dict[str, list[str]] = {}
        self.by_team: dict[str, str] = {}
        self.rows: dict[str, dict] = {}
        for pid, d in (players or {}).items():
            if not isinstance(d, dict):
                continue
            pid = str(pid)
            pos = d.get("position") or ""
            fantasy = [p for p in (d.get("fantasy_positions") or []) if p]
            if pos == "DEF" or "DEF" in fantasy:
                tm = (d.get("team") or "").upper()
                if tm:
                    self.by_team[tm] = pid
                continue
            name = d.get("full_name") or d.get("last_name")
            if not name or not (pos or fantasy):
                continue
            self.rows[pid] = {"pos": pos, "fantasy": set(fantasy) or {pos},
                              "team": (d.get("team") or "").upper(),
                              "active": bool(d.get("active"))}
            self.by_name.setdefault(normalize_name(name), []).append(pid)

    def candidates(self, name: str, pos: str | None = None) -> list[str]:
        """Every id this name could mean at this position, before tie-breaking.

        A caller that counts "ambiguous" needs this rather than the raw name
        bucket: a name held by two receivers is NOT ambiguous for a tight end,
        it is unmatched, and counting it as ambiguous hid position misses in
        the one diagnostic that would reveal a join regression.
        """
        cands = list(self.by_name.get(normalize_name(name), []))
        if not pos:
            return cands
        return [p for p in cands
                if pos in self.rows[p]["fantasy"] or self.rows[p]["pos"] == pos]

    def resolve(self, name: str, pos: str | None = None, team: str = "") -> str | None:
        """One Sleeper id, or None when nothing matches or a live tie remains."""
        cands = self.candidates(name, pos)
        if len(cands) > 1 and team:
            narrowed = [p for p in cands if self.rows[p]["team"] == team.upper()]
            if narrowed:
                cands = narrowed
        if len(cands) > 1:
            # A namesake who is retired or unsigned cannot be the player a
            # live feed is reporting on.
            live = [p for p in cands if self.rows[p]["active"] and self.rows[p]["team"]]
            if live:
                cands = live
        return cands[0] if len(cands) == 1 else None

    def defense(self, team: str, alias: dict | None = None) -> str | None:
        tm = (team or "").upper()
        tm = (alias or {}).get(tm, tm)
        return self.by_team.get(tm)


def load_id_map(cache_dir: Path, manifest=None) -> pl.DataFrame:
    cache = fetch(PLAYERIDS_URL, Path(cache_dir) / "db_playerids.csv", CACHE_TTL,
                  name="id map", manifest=manifest, timeout=60)
    df = pl.read_csv(cache, infer_schema_length=10000, null_values=["NA"])
    casts = [pl.col("sleeper_id").cast(pl.Utf8, strict=False),
             pl.col("fantasypros_id").cast(pl.Utf8, strict=False)]
    if "espn_id" in df.columns:          # plan A1: the ESPN feed joins on this, no name matching
        casts.append(pl.col("espn_id").cast(pl.Utf8, strict=False))
    return df.with_columns(casts)


class SleeperIndex:
    """Fuzzy-match index over the Sleeper player universe."""

    def __init__(self, players: dict[str, dict]):
        self.players = players
        # position -> {normalized name: sleeper_id}; keep only fantasy positions
        self.by_pos: dict[str, dict[str, str]] = {}
        self.dst_by_token: dict[str, str] = {}
        for pid, p in players.items():
            pos = p.get("position")
            if pos == "DEF":
                city = normalize_name(p.get("first_name") or "")
                nick = normalize_name(p.get("last_name") or "")
                for token in (f"{city} {nick}", nick, city, pid.lower()):
                    if token:
                        self.dst_by_token.setdefault(token, pid)
                continue
            # a two-way player carries his fantasy side in fantasy_positions
            # (Travis Hunter: position DB, fantasy_positions [DB, WR], 2026-09-04);
            # index him under every fantasy position so a WR source line lands
            fpos = [x for x in (p.get("fantasy_positions") or []) if x in ("QB", "RB", "WR", "TE", "K")]
            slots = [x for x in dict.fromkeys(([pos] if pos in ("QB", "RB", "WR", "TE", "K") else []) + fpos)]
            if not slots:
                continue
            name = p.get("full_name") or f"{p.get('first_name','')} {p.get('last_name','')}"
            key = normalize_name(name)
            for slot in slots:
                bucket = self.by_pos.setdefault(slot, {})
                # prefer active players on a name collision, and the primary
                # position's holder over a secondary-position claimant
                if key in bucket:
                    existing = self.players[bucket[key]]
                    primary_now, primary_before = pos == slot, existing.get("position") == slot
                    if primary_before and not primary_now:
                        continue                      # a secondary claimant never displaces the primary
                    if not (primary_now and not primary_before):
                        if existing.get("active") or not p.get("active"):
                            continue
                bucket[key] = pid

    def match_dst(self, name: str) -> str | None:
        n = normalize_name(name)
        n = " ".join(w for w in n.split() if w not in _DST_WORDS)
        if n in self.dst_by_token:
            return self.dst_by_token[n]
        hit = process.extractOne(n, list(self.dst_by_token.keys()), scorer=fuzz.token_set_ratio)
        if hit and hit[1] >= 85:
            return self.dst_by_token[hit[0]]
        return None

    def match(self, name: str, position: str, team: str | None = None, min_score: int = 87) -> str | None:
        """Return sleeper_id or None. Position is required to constrain the pool."""
        pos = {"DST": "DEF", "D/ST": "DEF", "PK": "K"}.get(position, position)
        if pos == "DEF":
            return self.match_dst(name)
        bucket = self.by_pos.get(pos, {})
        key = normalize_name(name)
        if key in bucket:
            return bucket[key]
        hit = process.extractOne(key, list(bucket.keys()), scorer=fuzz.token_sort_ratio)
        if hit and hit[1] >= min_score:
            pid = bucket[hit[0]]
            if team and self.players[pid].get("team") and self.players[pid]["team"] != team:
                # name match but team disagrees — accept only very high scores
                if hit[1] < 94:
                    return None
            return pid
        return None


def _clean_gsis(v) -> str | None:
    """Sleeper stores a few gsis ids with stray whitespace (" 00-0035057",
    seen 2026-09-24); nflverse never does."""
    v = str(v or "").strip()
    return v if re.fullmatch(r"00-\d{7}", v) else None


def sleeper_gsis(id_map: pl.DataFrame | None, sleeper_players: dict | None) -> tuple[dict[str, str], dict]:
    """sleeper_id -> gsis_id, and a report of where each join came from.

    The DynastyProcess map wins; Sleeper's own `gsis_id` field fills players
    the map does not have yet. A disagreement is kept on the map's side and
    listed, not guessed. When a gsis id is claimed more than once, the map's
    single claimant keeps it and the Sleeper-only claimants (duplicate or
    stale Sleeper entries) are dropped; when the map itself claims it twice,
    or only Sleeper entries claim it, every claimant is dropped -- a wrong
    join surfaces as the wrong player's usage, which is worse than a missing
    one.
    """
    out: dict[str, str] = {}
    from_map: set[str] = set()
    report = {"from_map": 0, "from_sleeper": 0, "conflicts": [], "dropped_shared_gsis": []}
    if id_map is not None and len(id_map) and {"sleeper_id", "gsis_id"} <= set(id_map.columns):
        for sid, gid in id_map.select(["sleeper_id", "gsis_id"]).iter_rows():
            g = _clean_gsis(gid)
            if sid and g:
                out[str(sid)] = g
                from_map.add(str(sid))
        report["from_map"] = len(out)
    for sid, d in (sleeper_players or {}).items():
        if not isinstance(d, dict):
            continue
        g = _clean_gsis(d.get("gsis_id"))
        if not g:
            continue
        sid = str(sid)
        if sid in out:
            if out[sid] != g:
                report["conflicts"].append((sid, out[sid], g))
            continue
        out[sid] = g
        report["from_sleeper"] += 1
    owners: dict[str, list[str]] = {}
    for sid, g in out.items():
        owners.setdefault(g, []).append(sid)
    for g, sids in owners.items():
        if len(sids) < 2:
            continue
        mapped = [s for s in sids if s in from_map]
        keep = mapped[0] if len(mapped) == 1 else None
        dropped = sorted(s for s in sids if s != keep)
        report["dropped_shared_gsis"].append((g, dropped))
        for sid in dropped:
            out.pop(sid, None)
    return out, report


def invert(mapping: dict[str, str]) -> dict[str, str]:
    """gsis_id -> sleeper_id from a sleeper_gsis mapping (already one-to-one)."""
    return {g: s for s, g in mapping.items()}
