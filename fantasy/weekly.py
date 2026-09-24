"""weekly_blend_v0: one weekly projection per player, with its range.

The mean is Sleeper's weekly projection, blended with market_points where the
player has a FULL market board (a partial board is a zero in the total and
never enters the blend), at a weight that starts high in week 1 and decays to
zero (config.yaml fantasy.market_weight) -- the user's framework: prefer the
market while one or two games cannot establish a role. The range comes from
dispersion_v0. Every input is kept in `detail`, so a report shows the Sleeper
number, the market number and the weight side by side, and the ledger can
grade the blend against either component.

Game-day validity (framework question 5) is applied here, and only here:
  Out / IR / Suspended / PUP, or a team with no game   -> 0, no range
  Doubtful / Questionable                              -> projected, flagged
"""

from __future__ import annotations

import json

from core import fetch as F
from core.manifest import Manifest
from core.scoring import score

from . import dispersion as D
from . import environment as E
from .contract import QUANTILES, WEEK, Projection, validate
from .sources import market_points as MP
from .sources import sleeper_weekly as SW

NAME = "weekly_blend_v0"
OUT_STATUSES = {"out", "ir", "suspended", "pup", "sus", "na", "nfi"}
FLAG_STATUSES = {"doubtful", "questionable"}


def market_weight(week: int, cfg_block: dict | None) -> float:
    c = cfg_block or {}
    w1, zero_by = float(c.get("week1", 0.0)), int(c.get("zero_by_week", 1))
    if zero_by <= 1:
        return 0.0
    return max(0.0, w1 * (zero_by - week) / (zero_by - 1))


def _zero(pid: str, detail: dict, why: str) -> Projection:
    return validate(Projection(pid, NAME, WEEK, 0.0, quantiles={}, detail=dict(detail, zero_reason=why)))


def blend(pid: str, info: dict, s: Projection | None, m: Projection | None, env_row: dict | None,
          w_market: float, table: dict | None) -> Projection:
    status = (info.get("status") or "").strip()
    src = s or m
    detail = {"pos": info.get("pos") or (src.detail.get("pos") if src else None),
              "team": info.get("team"), "status": status, "name": info.get("name"),
              "sleeper": None if s is None else s.mean,
              "market": None if m is None else m.mean,
              "market_partial": None if m is None else m.detail.get("partial"),
              "market_missing": None if m is None else m.detail.get("missing_markets"),
              "market_weight": 0.0, "env": env_row}
    if status.lower() in OUT_STATUSES:
        return _zero(pid, detail, f"status {status}")
    if env_row is None:
        return _zero(pid, detail, "no game this week (bye, or no scheduled game)")
    if s is None and m is None:
        return _zero(pid, detail, "no projection from any source")
    if s is not None and m is not None and not m.detail.get("partial"):
        w = w_market
        mean = w * m.mean + (1 - w) * s.mean
    elif s is not None:
        w, mean = 0.0, s.mean
    else:
        # market only: a partial board understates the total, so say so rather than hide it
        w, mean = 1.0, m.mean
        detail["only_source"] = "market_points" + (" (partial board)" if m.detail.get("partial") else "")
    detail["market_weight"] = round(w, 3)
    if status.lower() in FLAG_STATUSES:
        detail["flag"] = status
    p = validate(Projection(pid, NAME, WEEK, round(mean, 2), detail=detail))
    return D.apply(p, table) if table else p


def project_players(pids, info: dict, season: int, week: int, scoring: dict, league: str,
                    manifest: Manifest, cfg_block: dict | None = None, *, cache_dir=None):
    """(projections by sleeper id, environment by team, notes)."""
    notes = []
    sw = SW.project(season, week, scoring, cache_dir=cache_dir, manifest=manifest)
    if not sw.available:
        notes += sw.notes
    try:
        mp = MP.project(scoring, cache_dir=cache_dir, manifest=manifest)
    except Exception as ex:  # noqa: BLE001 -- the market is context; its absence degrades, never blocks
        mp = None
        notes.append(f"market_points unavailable ({type(ex).__name__})")
    env = E.week_environment(season, week, cache_dir=cache_dir, manifest=manifest)
    table = D.load_table(league)
    if table is None:
        notes.append(f"no dispersion_v0 table for {league}: projections carry no range")
    w = market_weight(week, cfg_block)
    out = {}
    for pid in pids:
        pid = str(pid)
        i = info.get(pid, {})
        out[pid] = blend(pid, i, sw.projections.get(pid), (mp.projections.get(pid) if mp else None),
                         env.get(i.get("team")), w, table)
    # A FINISHED GAME IS ITS SCORE, not a projection: after Thursday night the
    # week's P(win) must count what those players actually scored.
    final = {t for t, e in env.items() if e.get("status") == "STATUS_FINAL"}
    if any((info.get(str(p)) or {}).get("team") in final for p in pids):
        stats = json.loads(F.sleeper_stats(season, week, cache_dir=cache_dir, manifest=manifest, max_age_s=600)
                           .read_text(encoding="utf-8"))
        for pid in pids:
            pid = str(pid)
            if (info.get(pid) or {}).get("team") in final:
                out[pid] = final_score(out[pid], stats.get(pid), scoring)
    return out, env, notes


def final_score(p: Projection, stat_line: dict | None, scoring: dict) -> Projection:
    """The projection replaced by the player's actual points (0 if he has no
    stat line: he did not play)."""
    pts = round(score(SW._stat_line(stat_line or {}), scoring), 2)
    return validate(Projection(p.player_id, NAME, WEEK, pts, quantiles={q: pts for q in QUANTILES},
                               range_from="final score", detail=dict(p.detail, final=True, projected=p.mean)))
