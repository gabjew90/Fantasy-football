"""Yahoo as a league source for build_context: seven reads, Sleeper's shapes.

draftkit.briefs.build_context asks its `source` for the league, the rosters,
the users, my identity, the platform's injury designations, the week's
matchups and the week's transactions. Everything else it does is NFL-wide.
This class answers those seven from the Yahoo Fantasy API (access
provisioned for Keefamania 2026-09-16) in the dict shapes Sleeper returns,
so waivers, lineup, injuries, scout and trade watch run for a Yahoo league
without a branch anywhere downstream.

The shapes, and where each field comes from:

  league   {"scoring_settings": the league yaml's Sleeper-keyed block,
            "settings": {waiver_budget, playoff_week_start, playoff_teams,
                         reserve_slots, max_weekly_adds, trade_deadline},
            "roster_positions": the Yahoo list expanded per count}
  rosters  [{"roster_id": team_id, "owner_id": team_key, "players": [sleeper ids],
             "starters": [...], "reserve": [...],
             "settings": {wins, losses, ties, fpts, waiver_position,
                          waiver_budget_used}}]
  users    {team_key: team name}
  matchups [{"matchup_id", "roster_id", "points"}]  (scoreboard;week=N)
  transactions  Sleeper-shaped: type free_agent|waiver|trade, status
            complete|pending, adds/drops {sleeper_id: roster_id}, roster_ids

Players are resolved to Sleeper ids the same way manager.yahoo does it --
the DynastyProcess id map first, the name within position second; a K by
either; a DEF by team code, which IS its Sleeper id. Unresolved players
are reported in `notes`, never dropped silently.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime

from draftkit.ids import normalize_name
from draftkit.sleeper import IdentityError, SleeperClient

from . import yahoo as yahoo_mod
from .yahoo_api import get as yahoo_api_get

log = logging.getLogger("manager")

SKILL = ("QB", "RB", "WR", "TE")
BENCH_SLOTS = ("BN", "IR", "IR+", "NA")
# Yahoo team codes that differ from Sleeper's DEF ids.
TEAM_TO_SLEEPER = {"JAC": "JAX", "WSH": "WAS", "LA": "LAR"}

# Yahoo stat_id -> Sleeper scoring key(s). Yahoo's ids are stable across
# leagues (4 is always passing yards); the league's stat_modifiers carry the
# weights. Sleeper's weekly projections and nflverse-scored actuals are keyed
# the Sleeper way, so this is what lets a Yahoo league's K and DEF project
# anything at all -- the yaml's offensive block alone scored them at zero
# (Keefamania dry run, 2026-09-16: Tyler Loop 0.0, Buccaneers 0.0).
YAHOO_STAT_TO_SLEEPER: dict[int, tuple[str, ...]] = {
    4: ("pass_yd",), 5: ("pass_td",), 6: ("pass_int",),
    9: ("rush_yd",), 10: ("rush_td",), 11: ("rec",), 12: ("rec_yd",), 13: ("rec_td",),
    15: ("st_td",), 16: ("pass_2pt", "rush_2pt", "rec_2pt"), 18: ("fum_lost",),
    19: ("fgm_0_19",), 20: ("fgm_20_29",), 21: ("fgm_30_39",), 22: ("fgm_40_49",),
    23: ("fgm_50_59", "fgm_60p"), 29: ("xpm",), 30: ("xpmiss",),
    32: ("sack",), 33: ("int",), 34: ("fum_rec",), 35: ("def_td",), 36: ("safe",),
    37: ("blk_kick",), 49: ("def_st_td",),
    50: ("pts_allow_0",), 51: ("pts_allow_1_6",), 52: ("pts_allow_7_13",),
    53: ("pts_allow_14_20",), 54: ("pts_allow_21_27",), 55: ("pts_allow_28_34",),
    56: ("pts_allow_35p",), 57: ("fum_rec_td",), 60: ("pass_td_40p",),
}
# What Yahoo lets a manager park in an IR slot, in Sleeper's status
# vocabulary. A plain Out needs the league's IR+ option, which this league
# does not carry, so Out is deliberately absent.
YAHOO_RESERVE_ALLOW = ("IR", "PUP", "NFI", "COV")


def scoring_from_modifiers(settings: dict) -> dict[str, float]:
    """The league's scoring as Sleeper keys, from Yahoo's stat_modifiers."""
    out: dict[str, float] = {}
    mods = ((settings.get("stat_modifiers") or {}).get("stats")) or []
    for m in mods:
        s = m.get("stat") or m
        try:
            sid, val = int(s.get("stat_id")), float(s.get("value"))
        except (TypeError, ValueError):
            continue
        for key in YAHOO_STAT_TO_SLEEPER.get(sid, ()):
            out[key] = val
    return out


def _flat(parts) -> dict:
    return yahoo_mod._flat(parts)


class YahooSource:
    platform = "yahoo"

    def __init__(self, cfg, get=None, players: dict | None = None,
                 id_map: dict | None = None):
        self.cfg = cfg
        self.league_id = str(getattr(cfg, "league_id", None) or cfg.get("league_id"))
        self.key = f"league/nfl.l.{self.league_id}"
        self._get = get or yahoo_api_get
        self.client = SleeperClient(cfg.path("raw"))
        self._players = players
        self._id_map = id_map
        self._settings: dict | None = None
        self._entries: list[dict] | None = None
        self._rosters: list[dict] | None = None
        self._standings: dict | None = None
        self.notes: list[str] = []

    # ------------------------------------------------------------ helpers
    @property
    def players(self) -> dict:
        if self._players is None:
            from draftkit.briefs import INSEASON_PLAYERS_MAX_AGE
            self._players = self.client.players(max_age=INSEASON_PLAYERS_MAX_AGE)
        return self._players

    @property
    def id_map(self) -> dict:
        if self._id_map is None:
            self._id_map = yahoo_mod.yahoo_id_map(self.cfg)
        return self._id_map

    def _by_name(self) -> dict[str, list[str]]:
        out: dict[str, list[str]] = {}
        for pid, d in self.players.items():
            if not isinstance(d, dict):
                continue
            nm = d.get("full_name") or d.get("last_name")
            if nm and d.get("position"):
                out.setdefault(normalize_name(nm), []).append(str(pid))
        return out

    def resolve(self, yahoo_id: str, name: str, pos: str, team: str = "") -> str | None:
        """Sleeper id for one Yahoo player, or None."""
        if pos in ("DEF", "DST", "D/ST"):
            code = TEAM_TO_SLEEPER.get(team.upper(), team.upper())
            return code if code in self.players else None
        mapped = self.id_map.get(str(yahoo_id))
        if mapped:
            d = self.players.get(str(mapped)) or {}
            if d.get("position") == pos or pos in (d.get("fantasy_positions") or []):
                return str(mapped)
        cands = [x for x in self._names.get(normalize_name(name), [])
                 if (self.players.get(x) or {}).get("position") == pos]
        return cands[0] if len(cands) == 1 else None

    # ------------------------------------------------------------- league
    def _freshness_note(self) -> None:
        """Say where the Yahoo data came from and how old it is. Live reads
        need no note; a synced copy names its age, and a stale one warns."""
        from .yahoo_api import has_credentials, read_cached
        if self._get is not yahoo_api_get:
            return
        if has_credentials():
            # Logged so an Actions run shows which path it took: with the
            # secrets present this is the live API, and no note is needed.
            log.info("yahoo: reading league %s live from the API", self.league_id)
            return
        _, fetched = read_cached(f"{self.key}/teams/roster")
        if fetched is None:
            return
        age_h = (time.time() - float(fetched)) / 3600.0
        mark = "⚠ " if age_h > 6 else ""
        self.notes.append(f"{mark}Yahoo data from the local sync, {age_h:.1f}h old"
                          + (" — is the sync job running?" if age_h > 6 else ""))

    def _settings_body(self) -> dict:
        if self._settings is None:
            self._freshness_note()
            body = self._get(f"{self.key}/settings")
            lg = body["fantasy_content"]["league"]
            meta = lg[0] if isinstance(lg[0], dict) else {}
            settings = _flat(lg[1].get("settings")) if len(lg) > 1 else {}
            self._settings = {"meta": meta, "settings": settings}
        return self._settings

    def league(self) -> dict:
        s = self._settings_body()
        meta, st = s["meta"], s["settings"]
        roster_positions: list[str] = []
        reserve_slots = 0
        for rp in st.get("roster_positions") or []:
            r = rp.get("roster_position") or rp
            pos, n = str(r.get("position")), int(r.get("count") or 0)
            roster_positions += [pos] * n
            if pos in ("IR", "IR+"):
                reserve_slots += n
        faab = str(st.get("uses_faab") or "0") in ("1", "true", "True")
        yaml_scoring = dict(self.cfg.get("scoring") or (self.cfg.get("expected") or {}).get("scoring") or {})
        scoring = scoring_from_modifiers(st)
        if scoring:
            # The yaml block is a hand transcription of the settings page; the
            # API is the settings page. Report any disagreement -- that is
            # what `verify` does for Sleeper -- and let the API win.
            diffs = [f"{k} yaml {v} vs api {scoring.get(k)}" for k, v in yaml_scoring.items()
                     if k in scoring and abs(float(v) - float(scoring[k])) > 1e-9]
            if diffs:
                self.notes.append("⚠ Yahoo scoring differs from the league yaml: " + "; ".join(diffs))
            for k, v in yaml_scoring.items():
                scoring.setdefault(k, float(v))
        else:
            scoring = yaml_scoring
            self.notes.append("⚠ Yahoo stat_modifiers unavailable — K/DEF score from the yaml block only")
        return {
            "name": meta.get("name"), "league_id": self.league_id, "season": meta.get("season"),
            "current_week": int(meta.get("current_week") or 0),
            "scoring_settings": scoring,
            "roster_positions": roster_positions,
            "settings": {
                "waiver_budget": 100 if faab else 0,
                "waiver_type": st.get("waiver_type"),
                "playoff_week_start": int(st.get("playoff_start_week") or 15),
                "playoff_teams": int(st.get("num_playoff_teams") or 6),
                "reserve_slots": reserve_slots,
                # Yahoo's IR slot takes its own IR/PUP/NFI designations; a
                # plain Out is not eligible unless the league enables IR+.
                "reserve_allow": list(YAHOO_RESERVE_ALLOW),
                "reserve_allow_out": 0, "reserve_allow_doubtful": 0,
                "max_weekly_adds": int(st.get("max_weekly_adds") or 0) or None,
                "trade_deadline": st.get("trade_end_date"),
                "num_teams": int(meta.get("num_teams") or 0),
            },
        }

    # ------------------------------------------------------------ rosters
    def _load_entries(self) -> list[dict]:
        if self._entries is None:
            self._names = self._by_name()
            self._entries = yahoo_mod.api_entries(self.league_id, get=self._get)
        return self._entries

    def _standings_by_team(self) -> dict[str, dict]:
        if self._standings is None:
            out: dict[str, dict] = {}
            try:
                body = self._get(f"{self.key}/standings")
                teams = body["fantasy_content"]["league"][1]["standings"][0]["teams"]
                for k, t in teams.items():
                    if k == "count" or not isinstance(t, dict):
                        continue
                    meta = _flat(t["team"][0])
                    extra = _flat(t["team"][1:])
                    tot = (extra.get("team_standings") or {}).get("outcome_totals") or {}
                    out[str(meta.get("team_id"))] = {
                        "wins": int(tot.get("wins") or 0), "losses": int(tot.get("losses") or 0),
                        "ties": int(tot.get("ties") or 0),
                        "fpts": float((extra.get("team_points") or {}).get("total") or 0.0),
                        "rank": int((extra.get("team_standings") or {}).get("rank") or 0),
                    }
            except Exception as e:  # noqa: BLE001
                log.warning("yahoo: standings unavailable (%s)", e.__class__.__name__)
                self.notes.append(f"DATA MISSING: Yahoo standings ({e.__class__.__name__})")
            self._standings = out
        return self._standings

    def rosters(self) -> list[dict]:
        if self._rosters is not None:
            return self._rosters
        entries = self._load_entries()
        order = self.league().get("roster_positions") or []
        slot_rank = {s: i for i, s in enumerate(dict.fromkeys(order))}
        standings = self._standings_by_team()
        teams: dict[str, dict] = {}
        unresolved: list[str] = []
        priority: dict[str, int] = {}
        # waiver priority sits on the team object; api_entries flattens only
        # players, so read it off the same roster payload
        for e in entries:
            tid = str(e.get("team_id") or "")
            if not tid:
                continue
            t = teams.setdefault(tid, {
                "roster_id": int(tid), "owner_id": e.get("owner_key"),
                "players": [], "starters": [], "reserve": [], "_slots": [],
                "settings": dict(standings.get(tid) or {"wins": 0, "losses": 0, "ties": 0, "fpts": 0.0},
                                 waiver_budget_used=0, waiver_position=priority.get(tid)),
            })
            if not e.get("name"):
                continue                      # the empty-roster placeholder row
            sid = self.resolve(e.get("yahoo_id", ""), e["name"], e["pos"], e.get("team", ""))
            if sid is None:
                unresolved.append(f"{e['name']} ({e['pos']}, {e['owner']})")
                continue
            t["players"].append(sid)
            slot = e.get("slot") or "BN"
            if slot in ("IR", "IR+"):
                t["reserve"].append(sid)
            elif slot not in BENCH_SLOTS:
                t["_slots"].append((slot_rank.get(slot, 99), sid))
        for t in teams.values():
            t["starters"] = [sid for _, sid in sorted(t.pop("_slots"))]
        self._fill_waiver_priority(teams)
        if unresolved:
            self.notes.append(f"⚠ {len(unresolved)} Yahoo roster players did not resolve to a "
                              f"Sleeper id: {', '.join(unresolved[:6])}")
        self._rosters = sorted(teams.values(), key=lambda r: r["roster_id"])
        return self._rosters

    def _fill_waiver_priority(self, teams: dict[str, dict]) -> None:
        try:
            body = self._get(f"{self.key}/teams")
            for k, t in body["fantasy_content"]["league"][1]["teams"].items():
                if k == "count" or not isinstance(t, dict):
                    continue
                meta = _flat(t["team"][0])
                tid = str(meta.get("team_id"))
                if tid in teams and meta.get("waiver_priority") is not None:
                    teams[tid]["settings"]["waiver_position"] = int(meta["waiver_priority"])
        except Exception as e:  # noqa: BLE001
            log.warning("yahoo: teams (waiver priority) unavailable (%s)", e.__class__.__name__)

    def users(self) -> dict[str, str]:
        return {str(e["owner_key"]): e["owner"] for e in self._load_entries() if e.get("owner_key")}

    def resolve_me(self, users: dict, rosters: list[dict]) -> tuple[dict, dict]:
        """me.username is the Yahoo TEAM NAME (there is no Sleeper identity);
        me.user_id, when set, is the team_key. Exactly one roster must match."""
        me = self.cfg.get("me") or {}
        want_name = str(me.get("username") or "").strip().lower()
        want_key = str(me.get("user_id") or "").strip() or None
        matches = []
        for r in rosters:
            key = str(r.get("owner_id"))
            if want_key and key == want_key:
                matches.append((r, "me.user_id (team_key)"))
            elif want_name and users.get(key, "").strip().lower() == want_name:
                matches.append((r, "yahoo team name"))
        if len(matches) != 1:
            raise IdentityError(
                f"me.username={me.get('username')!r} / me.user_id={want_key!r} matched "
                f"{len(matches)} of {len(rosters)} Yahoo teams: {sorted(users.values())}")
        roster, source = matches[0]
        return roster, {"source": source, "user_id": str(roster.get("owner_id")),
                        "display": users.get(str(roster.get("owner_id")), "?"),
                        "roster_id": roster.get("roster_id")}

    # ------------------------------------------------------------ injuries
    def injury_overlay(self) -> dict[str, str]:
        self.rosters()
        out: dict[str, str] = {}
        for e in self._load_entries():
            if not e.get("name"):
                continue
            mapped = yahoo_mod.YAHOO_STATUS.get(str(e.get("yahoo_status") or ""))
            if not mapped:
                continue
            sid = self.resolve(e.get("yahoo_id", ""), e["name"], e["pos"], e.get("team", ""))
            if sid:
                out[sid] = mapped
        return out

    # ------------------------------------------------------------ matchups
    def matchups(self, week: int) -> list[dict]:
        body = self._get(f"{self.key}/scoreboard;week={int(week)}")
        sb = body["fantasy_content"]["league"][1]["scoreboard"]["0"]["matchups"]
        out: list[dict] = []
        for k, m in sb.items():
            if k == "count" or not isinstance(m, dict):
                continue
            mid = int(k) + 1
            teams = (m["matchup"].get("0") or {}).get("teams") or {}
            for tk, t in teams.items():
                if tk == "count" or not isinstance(t, dict):
                    continue
                meta = _flat(t["team"][0])
                extra = _flat(t["team"][1:]) if len(t["team"]) > 1 else {}
                out.append({"matchup_id": mid, "roster_id": int(meta.get("team_id")),
                            "points": float((extra.get("team_points") or {}).get("total") or 0.0),
                            "projected": float((extra.get("team_projected_points") or {}).get("total") or 0.0)})
        return out

    # -------------------------------------------------------- transactions
    def transactions(self, week: int, count: int = 50) -> list[dict]:
        """Yahoo's recent transactions in Sleeper's shape. Yahoo has no
        per-week endpoint; the seen-gate downstream makes repeats harmless."""
        self.rosters()
        body = self._get(f"{self.key}/transactions;count={int(count)}")
        txs = body["fantasy_content"]["league"][1]["transactions"]
        out: list[dict] = []
        for k, t in txs.items():
            if k == "count" or not isinstance(t, dict):
                continue
            parts = t["transaction"]
            meta = _flat(parts[0])
            plist = (parts[1].get("players") if len(parts) > 1 and isinstance(parts[1], dict) else {}) or {}
            adds: dict[str, int] = {}
            drops: dict[str, int] = {}
            sources = set()
            for pk, pv in plist.items():
                if pk == "count" or not isinstance(pv, dict):
                    continue
                pf = _flat(pv["player"][0])
                td = _flat((pv["player"][1] or {}).get("transaction_data") if len(pv["player"]) > 1 else [])
                if isinstance((pv["player"][1] or {}).get("transaction_data"), dict):
                    td = (pv["player"][1] or {}).get("transaction_data")
                name = (pf.get("name") or {}).get("full") or ""
                pos = str(pf.get("display_position") or "").split(",")[0]
                sid = self.resolve(str(pf.get("player_id") or ""), name, pos,
                                   str(pf.get("editorial_team_abbr") or ""))
                if not sid:
                    continue
                sources.add(td.get("source_type"))
                kind = td.get("type")
                dest = str(td.get("destination_team_key") or "")
                src = str(td.get("source_team_key") or "")
                if kind in ("add", "trade") and dest.startswith("470.l.") or (kind == "add" and dest):
                    adds[sid] = int(dest.rsplit(".t.", 1)[-1]) if ".t." in dest else 0
                if kind == "drop" and src:
                    drops[sid] = int(src.rsplit(".t.", 1)[-1]) if ".t." in src else 0
                if kind == "trade" and src and ".t." in src:
                    drops[sid] = int(src.rsplit(".t.", 1)[-1])
            ytype = str(meta.get("type") or "")
            if ytype == "trade":
                stype = "trade"
            elif "waivers" in sources:
                stype = "waiver"
            else:
                stype = "free_agent"
            status = "complete" if str(meta.get("status")) == "successful" else "pending"
            rids = sorted({*adds.values(), *drops.values()} - {0})
            out.append({"transaction_id": str(meta.get("transaction_id")), "type": stype,
                        "status": status, "adds": adds or None, "drops": drops or None,
                        "roster_ids": rids, "draft_picks": [],
                        "created": int(meta.get("timestamp") or 0) * 1000,
                        "settings": {}, "metadata": {"yahoo_type": ytype}})
        return out


def describe(cfg) -> str:
    """One-line provenance for briefs: which Yahoo league and when."""
    return f"yahoo league {getattr(cfg, 'league_id', '?')} via API {datetime.now().strftime('%Y-%m-%d %H:%M')}"
