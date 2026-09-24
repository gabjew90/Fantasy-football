"""One league read for a fantasy command, with where it came from recorded.

Reuses the in-season manager's league context (Sleeper or Yahoo, the same
seven reads the scheduled jobs make) and adds what a decision needs: my
roster, my opponent's, both sides' starters, the league's lineup slots, and
the league scoring twice -- as the league yaml states it and as the platform
reports it -- so the gate can compare them stat by stat.

Every league read is recorded in the run's Manifest:
  Sleeper            live reads, status `fresh`, stamped when they returned
  Yahoo, live API    the same (credentials present)
  Yahoo, synced copy status `cached`, stamped with the sync time -- so the gate
                     can say the roster was NOT read after the request started
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field

from core.manifest import Manifest
from core.scoring import league_scoring

from .contract import fantasy_position


@dataclass
class LeagueView:
    league: str
    platform: str
    season: int
    week: int
    my_rid: int
    opp_rid: int | None
    my_name: str
    opp_name: str
    my_players: list
    opp_players: list
    my_starters: list
    opp_starters: list
    slots: object
    flex_slots: object
    info: dict                          # sleeper_id -> {name, pos, team, status}
    scoring_yaml: dict
    scoring_platform: dict
    notes: list = field(default_factory=list)
    ctx: dict = field(default_factory=dict, repr=False)

    @property
    def scoring(self) -> dict:
        """What projections are scored in: the platform's settings (the
        authority, and the only place K and DEF weights live), over the yaml.
        The gate separately checks that every yaml key agrees with it."""
        return {**self.scoring_yaml, **self.scoring_platform}


def _record_league_read(ctx: dict, league: str, manifest: Manifest) -> None:
    now = dt.datetime.now(dt.timezone.utc)
    src = ctx.get("source")
    if getattr(src, "platform", "sleeper") == "yahoo":
        from manager.yahoo_api import has_credentials, read_cached
        if not has_credentials():
            _, fetched = read_cached(f"{src.key}/teams/roster")
            manifest.record("league roster", source=f"yahoo sync ({league})", status="cached",
                            fetched_at=dt.datetime.fromtimestamp(fetched, dt.timezone.utc) if fetched else None,
                            detail="synced copy; the live Yahoo API needs credentials on this host")
            return
        manifest.record("league roster", source=f"yahoo api ({league})", status="fresh", fetched_at=now)
        return
    manifest.record("league roster", source=f"sleeper api ({league})", status="fresh", fetched_at=now)


def roster_freshness(cfg, now: dt.datetime | None = None) -> dict:
    """Where a league's roster would come from right now, and how old it is --
    without loading the league (for `nfl status`). Sleeper is always live;
    Yahoo is live with credentials on this host, else the last local sync."""
    now = now or dt.datetime.now(dt.timezone.utc)
    platform = str(cfg.get("platform") or "sleeper").lower()
    out = {"name": cfg.league_name, "platform": platform, "roster_age_h": 0.0, "source": "live API"}
    if platform == "yahoo":
        from manager import context as mctx
        from manager.yahoo_api import has_credentials, read_cached
        mctx.configure(cfg.league_name, None)          # the Yahoo cache lives in the league's state dir
        if not has_credentials():
            _, fetched = read_cached(f"league/nfl.l.{cfg.league_id}/teams/roster")
            out.update(source="local sync copy (no Yahoo credentials on this host)",
                       roster_age_h=None if fetched is None else round((now.timestamp() - fetched) / 3600, 1))
    return out


def load_scoring(league: str, manifest: Manifest) -> tuple[dict, dict]:
    """(yaml scoring, platform scoring) without loading rosters, matchups or
    transactions -- for commands that need only the league's scoring (the
    teammate-out scenario). Yahoo's comes RAW from the API's stat modifiers,
    for the same reason as in load()."""
    from draftkit.config import Config
    cfg = Config.load(league=league)
    platform = str(cfg.get("platform") or "sleeper").lower()
    now = dt.datetime.now(dt.timezone.utc)
    if platform == "yahoo":
        from manager import context as mctx
        from manager.yahoo_context import YahooSource, scoring_from_modifiers
        mctx.configure(league, None)
        plat = scoring_from_modifiers(YahooSource(cfg)._settings_body()["settings"])
    else:
        from draftkit.sleeper import SleeperClient
        raw = SleeperClient(cfg.path("raw")).league(cfg.league_id).get("scoring_settings") or {}
        plat = {str(k): float(v) for k, v in raw.items() if isinstance(v, (int, float))}
    manifest.record("league scoring", source=f"{platform} ({league})", status="fresh", fetched_at=now)
    return league_scoring(cfg), plat


def load(league: str, week: int | None, manifest: Manifest) -> LeagueView:
    from manager import context as mctx
    mctx.configure(league, week)
    ctx = mctx.league_context(write_state=False)        # a decision command reads; it never writes state
    _record_league_read(ctx, league, manifest)

    by_rid = {int(r["roster_id"]): r for r in ctx["rosters"]}
    info = {}
    for rid in (ctx["my_rid"], ctx.get("opp_rid")):
        for p in ctx["roster_players"].get(rid, []) if rid is not None else []:
            pid = str(p["sleeper_id"])
            raw = (ctx.get("players") or {}).get(pid) or {}
            info[pid] = {"name": p.get("name"), "pos": fantasy_position(raw) or p.get("pos"),
                         "team": p.get("team"), "status": p.get("status") or ""}

    def starters(rid):
        r = by_rid.get(rid) or {}
        return [str(s) for s in (r.get("starters") or []) if str(s) not in ("0", "", "None")]

    def players(rid):
        return [str(p["sleeper_id"]) for p in ctx["roster_players"].get(rid, [])] if rid is not None else []

    cfg = ctx["cfg"]
    src = ctx.get("source")
    if getattr(src, "platform", "sleeper") == "yahoo":
        # RAW from the API. The Yahoo source's scoring_settings fill any key the
        # API lacks from the yaml (setdefault), so a gate comparing against them
        # would verify the yaml against itself.
        from manager.yahoo_context import scoring_from_modifiers
        platform_scoring = scoring_from_modifiers(src._settings_body()["settings"])
    else:
        platform_scoring = {str(k): float(v) for k, v in
                            ((ctx.get("league") or {}).get("scoring_settings") or {}).items()
                            if isinstance(v, (int, float))}
    return LeagueView(
        league=league, platform=str(getattr(ctx.get("source"), "platform", "sleeper") or "sleeper"),
        season=int(ctx["state"]["season"]), week=int(ctx["week"]),
        my_rid=ctx["my_rid"], opp_rid=ctx.get("opp_rid"),
        my_name=ctx["users_by_rid"].get(ctx["my_rid"], "me"), opp_name=ctx.get("opp_name") or "(no matchup)",
        my_players=players(ctx["my_rid"]), opp_players=players(ctx.get("opp_rid")),
        my_starters=starters(ctx["my_rid"]), opp_starters=starters(ctx.get("opp_rid")),
        slots=ctx["slots"], flex_slots=ctx["flex_slots"], info=info,
        scoring_yaml=league_scoring(cfg), scoring_platform=platform_scoring,
        notes=list(ctx.get("stale") or []) + list(ctx.get("data_warnings") or []),
        ctx=ctx)
