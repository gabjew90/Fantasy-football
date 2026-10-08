"""Yahoo roster reads for manager.yahoo_context: the API's league roster in
plain dicts, the Yahoo-to-Sleeper id join, and the status vocabulary.

Yahoo's Fantasy API was approval-gated from 2026-07-22; Keefamania's access
was provisioned 2026-09-16 (manager/yahoo_api.py holds the OAuth side).
yahoo_context (through which the fantasy commands read a Yahoo league) uses
what is left here: api_entries, yahoo_id_map, _flat and YAHOO_STATUS. The
API rows carry three things a name list cannot:
  * Yahoo's player id, joined exactly through the DynastyProcess id map
    (`yahoo_id_map`), with the name match kept as the fallback;
  * each player's lineup slot (`slot`: QB, BN, IR, ...);
  * Yahoo's own injury designation (`yahoo_status`: IR, IR-R, PUP-R, O, Q,
    ...), which is what decides IR-slot eligibility in this league.

load() (rows priced by the trade framework, with the browser-scrape snapshot
at data/raw/yahoo/<league>.txt as its fallback) and injury_overlay() served
the trade radar and scripts/keefamania_trades.py; they were retired with the
radar on 2026-10-08 (DECISIONS #212).
"""

from __future__ import annotations

import logging

log = logging.getLogger("manager")

# Yahoo status code -> the Sleeper injury_status vocabulary (yahoo_context's
# injury overlay reads it). Codes measured on the live league 2026-09-16: IR,
# IR-R, PUP-R, CEL, Q; the rest are Yahoo's documented set.
YAHOO_STATUS = {
    "IR": "IR", "IR-R": "IR", "IR-NFI": "NFI",
    "PUP-R": "PUP", "PUP-P": "PUP", "NFI-R": "NFI", "NFI-A": "NFI",
    "O": "Out", "D": "Doubtful", "Q": "Questionable", "DTD": "Questionable",
    "SUSP": "Sus", "CEL": "NA", "NA": "NA", "COVID-19": "COV",
}


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
                "owner": owner, "owner_key": _flat(t["team"][0]).get("team_key"),
                "team_id": _flat(t["team"][0]).get("team_id"),
                "yahoo_id": str(f.get("player_id") or ""),
                "team": str(f.get("editorial_team_abbr") or "").upper(),
                "slot": sel.get("position"), "yahoo_status": f.get("status"),
                "injury_note": f.get("injury_note"),
            })
    return out


def yahoo_id_map(cfg) -> dict[str, str]:
    """{yahoo_id: sleeper_id} from the DynastyProcess id map; empty on any
    failure, and the callers then match on names as they always did."""
    try:
        import polars as pl
        from core.ids import load_id_map
        df = load_id_map(cfg.path("raw"))
        if "yahoo_id" not in df.columns:
            return {}
        df = df.select(pl.col("yahoo_id").cast(pl.Int64, strict=False).cast(pl.Utf8),
                       pl.col("sleeper_id")).drop_nulls()
        return dict(df.iter_rows())
    except Exception as e:  # noqa: BLE001
        log.warning("yahoo: no id map (%s) -- matching on names", e.__class__.__name__)
        return {}
