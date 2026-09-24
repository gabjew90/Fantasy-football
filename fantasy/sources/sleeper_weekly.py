"""Source: Sleeper's weekly projection, scored in the league's own scoring.

Sleeper serves Rotowire-sourced stat lines per player-week; they are scored
here through core.scoring, so a half-PPR league gets half-PPR points. It is a
mean-only source: the range comes from fantasy/dispersion.py, which was fitted
on exactly this source's historical errors.

Before a week's projections are published Sleeper serves ADP placeholders
only; that is reported as `available=False`, never as a board of zeroes.
"""

from __future__ import annotations

import json

from core import fetch as F
from core.scoring import score

from ..contract import WEEK, Projection, SourceResult, fantasy_position, validate

NAME = "sleeper_weekly"
_NOT_STATS = ("adp_", "pos_adp_", "pts_", "pos_rank_")


def _stat_line(stats: dict) -> dict:
    return {k: v for k, v in (stats or {}).items()
            if not k.startswith(_NOT_STATS) and k != "gp" and v is not None}


def from_rows(rows: list, scoring: dict) -> SourceResult:
    """Score Sleeper projection rows. Separated from the fetch for tests."""
    out = SourceResult(source=NAME, horizon=WEEK)
    for r in rows or []:
        pid = str(r.get("player_id") or "")
        line = _stat_line(r.get("stats"))
        if not pid or not line:
            continue
        p = r.get("player") or {}
        pos = fantasy_position(p)
        out.projections[pid] = validate(Projection(
            player_id=pid, source=NAME, horizon=WEEK, mean=round(score(line, scoring), 2),
            detail={"pos": pos, "team": r.get("team") or p.get("team"),
                    "opponent": r.get("opponent"), "updated_ms": r.get("last_modified")}))
    if not out.projections:
        out.available = False
        out.notes.append("Sleeper is serving placeholders only (no stat lines) for this week")
    return out


ALL_POSITIONS = ("QB", "RB", "WR", "TE", "K", "DEF")


def project(season: int, week: int, scoring: dict, *, positions=ALL_POSITIONS, cache_dir=None,
            manifest=None) -> SourceResult:
    path = F.sleeper_projections(season, week, positions=positions, cache_dir=cache_dir, manifest=manifest)
    return from_rows(json.loads(path.read_text(encoding="utf-8")), scoring)
