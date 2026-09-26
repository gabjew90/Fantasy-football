"""The league, loaded once per chat session, for the question tools (fantasy.ask).

The decision commands (lineup, waiver, trade, scenario) each read the league,
the projections and the scoreboard from scratch and write a whole report:
seven to ten seconds per question, and one answer shape. The tools answer a
conversation -- "is X better than Y", "what if I start A", "who has Z" -- so
they share one read: every roster in the league, every player on an NFL team,
this week's projection for each (weekly_blend_v0, the lineup command's own
numbers), the scoreboard, and the data gate as it stood when the read was
made.

The snapshot is a JSON file under the session cache (cache_dir) and is reused for TTL_MIN
minutes. Every tool answer states its age, and `--fresh` rebuilds it: an
injury designation can change inside that window, and the reader must be able
to see when the data was read. The gate is the one computed at the read --
"roster read after the request" means read by this snapshot, which the age
line qualifies.

Usage (a player's snaps and shares) is not in the snapshot: it is read per
question for the players asked about, which is cheap and keeps the file small.
"""

from __future__ import annotations

import dataclasses
import datetime as dt
import json
import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from core.manifest import Manifest

from . import gate as G
from . import league as LG
from . import weekly as W
from .contract import Projection, fantasy_position

TTL_MIN = 20
FANTASY_POS = ("QB", "RB", "WR", "TE", "K", "DEF")
# what the tools read from Sleeper's player table: identity for name
# resolution (core.ids.NameIndex), and the injury fields the watch reads
KEEP = ("full_name", "first_name", "last_name", "position", "fantasy_positions", "team", "status", "active",
        "injury_status", "injury_body_part", "practice_participation", "depth_chart_order", "search_rank",
        "news_updated", "years_exp")


def cache_dir() -> Path:
    """$NFL_CACHE, else the system temp dir -- never $NFL_OUT, which is the
    folder the user downloads from (props/ask.py uses the same root)."""
    return Path(os.environ.get("NFL_CACHE") or Path(tempfile.gettempdir()) / "nfl_cache")


@dataclass
class Snapshot:
    league: str
    platform: str
    season: int
    week: int
    built_at_utc: str
    my_rid: int
    opp_rid: int | None
    teams: dict                  # rid -> {"name", "players": [sid], "starters": [sid]}
    slots: dict
    flex_slots: tuple
    standing: dict
    scoring: dict
    players: dict                # sid -> Sleeper's row, KEEP fields only
    info: dict                   # sid -> {name, pos, team, status}, as the decision commands build it
    projections: dict            # sid -> Projection (rostered players, and everyone projected above zero)
    env: dict                    # team -> scoreboard row
    gate: dict
    manifest: dict
    notes: list = field(default_factory=list)

    # ------------------------------------------------------------ views
    @property
    def my_players(self) -> list:
        return self.teams[self.my_rid]["players"]

    @property
    def opp_players(self) -> list:
        return self.teams[self.opp_rid]["players"] if self.opp_rid is not None else []

    def owner_rid(self, sid: str) -> int | None:
        return next((rid for rid, t in self.teams.items() if sid in t["players"]), None)

    def age_min(self, now: dt.datetime | None = None) -> float:
        now = now or dt.datetime.now(dt.timezone.utc)
        return (now - dt.datetime.fromisoformat(self.built_at_utc)).total_seconds() / 60

    # ------------------------------------------------------------ JSON
    def to_json(self) -> dict:
        d = {f.name: getattr(self, f.name) for f in dataclasses.fields(self)}
        d["teams"] = {str(k): v for k, v in self.teams.items()}
        d["flex_slots"] = [sorted(s) for s in self.flex_slots]
        d["projections"] = {k: dataclasses.asdict(p) for k, p in self.projections.items()}
        for p in d["projections"].values():
            p["quantiles"] = {str(q): v for q, v in p["quantiles"].items()}
        return d

    @classmethod
    def from_json(cls, d: dict) -> "Snapshot":
        d = dict(d)
        d["teams"] = {int(k): v for k, v in d["teams"].items()}
        d["flex_slots"] = tuple(frozenset(s) for s in d["flex_slots"])
        d["projections"] = {k: Projection(**dict(p, quantiles={float(q): v for q, v in p["quantiles"].items()}))
                            for k, p in d["projections"].items()}
        return cls(**d)


def build(league: str, week: int | None = None) -> Snapshot:
    m = Manifest(f"fantasy snapshot {league}")
    view = LG.load(league, week, m)
    ctx = view.ctx
    raw_players = ctx.get("players") or {}
    by_rid = {int(r["roster_id"]): r for r in ctx["rosters"]}

    teams, info = {}, {}
    for rid, r in by_rid.items():
        rows = ctx["roster_players"].get(rid, [])
        for p in rows:
            sid = str(p["sleeper_id"])
            raw = raw_players.get(sid) or {}
            info[sid] = {"name": p.get("name"), "pos": fantasy_position(raw) or p.get("pos"),
                         "team": p.get("team"), "status": p.get("status") or ""}
        teams[rid] = {"name": ctx["users_by_rid"].get(rid, f"team {rid}"),
                      "players": [str(p["sleeper_id"]) for p in rows],
                      "starters": [str(s) for s in (r.get("starters") or []) if str(s) not in ("0", "", "None")]}
    # every player on an NFL team at a fantasy position, rostered or not
    players = {}
    for sid, raw in raw_players.items():
        sid = str(sid)
        pos = fantasy_position(raw)
        if sid in info or (raw.get("team") and pos in FANTASY_POS):
            players[sid] = {k: raw.get(k) for k in KEEP if raw.get(k) is not None}
            info.setdefault(sid, {"name": raw.get("full_name") or f"{raw.get('first_name', '')} {raw.get('last_name', '')}".strip(),
                                  "pos": pos, "team": raw.get("team"), "status": raw.get("injury_status") or ""})

    cfg = ctx["cfg"]
    projs, env, notes = W.project_players(list(info), info, view.season, view.week, view.scoring, league, m,
                                          (cfg.get("fantasy") or {}).get("market_weight"))
    rostered = {s for t in teams.values() for s in t["players"]}
    projs = {s: p for s, p in projs.items() if s in rostered or p.mean > 0}
    gate = G.evaluate(m, view.scoring_yaml, view.scoring_platform, view.my_players, projs)
    return Snapshot(
        league=league, platform=view.platform, season=view.season, week=view.week,
        built_at_utc=dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        my_rid=view.my_rid, opp_rid=view.opp_rid, teams=teams, slots=dict(view.slots),
        flex_slots=tuple(frozenset(s) for s in (view.flex_slots or ())), standing=view.standing,
        scoring=view.scoring, players=players, info=info, projections=projs, env=env,
        gate=gate.to_dict(), manifest=m.to_dict(), notes=notes + view.notes)


def path_for(league: str, week: int | None) -> Path:
    return cache_dir() / f"fantasy_{league}_{'current' if week is None else f'wk{int(week):02d}'}.json"


def load(league: str, week: int | None = None, *, fresh: bool = False,
         now: dt.datetime | None = None) -> Snapshot:
    """The session's snapshot: the cached one while it is younger than
    TTL_MIN (and `fresh` is not asked), else a new read, saved for the next
    question. A cache file that cannot be read is rebuilt, never trusted."""
    p = path_for(league, week)
    if not fresh and p.exists():
        try:
            snap = Snapshot.from_json(json.loads(p.read_text(encoding="utf-8")))
            if snap.age_min(now) < TTL_MIN:
                return snap
        except (ValueError, KeyError, TypeError):
            pass
    snap = build(league, week)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(snap.to_json(), default=str), encoding="utf-8")
    tmp.replace(p)
    return snap
