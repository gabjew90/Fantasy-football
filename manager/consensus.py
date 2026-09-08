"""Multi-source projections, and how much the sources disagree.

The manager has always shown one number. That number is an average of nothing
-- it is whichever shop the board happened to be built from. Meanwhile the
sources we already hold disagree by 20 to 65 points on exactly the players
decisions turn on: Travis Etienne is 188 on Sleeper, 209 on ESPN and 200 on
the FantasyPros sheet, while Drake London is 203/204/208. Same neighbourhood,
completely different confidence, and nothing downstream could tell them apart.

This module is an ANNOTATION LAYER. It does not change a single
recommendation. It says how firm the ground is under one. Whether the mean is
a better input than the current single source is an empirical question that
needs a season of actuals to answer, and until then substituting it would be
trading a known quantity for an untested one.

Scales differ between shops -- ESPN runs about 6% below Sleeper across the
board, not because it disagrees about players but because it models a
slightly different season. So each source is scored in the league's own
settings, then rescaled by the ratio of medians over the players all sources
carry, then averaged. `spread` is max minus min after rescaling.
"""

from __future__ import annotations

import csv
import logging
import statistics
import time as _time
from pathlib import Path

log = logging.getLogger("manager")

TTL = 12 * 3600
MIN_COMMON = 40          # below this the rescale is noise, so report unscaled
FLOOR = 40.0             # players too small to inform the median

# NOT EVERY SOURCE AGES THE SAME WAY.
#
# Sleeper and ESPN republish their season projections through the year, so
# they carry this week's information. The FantasyPros workbook is a PRESEASON
# DRAFT SHEET: nothing regenerates it once the season starts, and this module
# is its only consumer. Left at equal weight it would still be arguing for
# August by November, on a player whose role changed in September.
#
# So a static source decays: full weight in week 1, zero by DECAY_WEEKS. The
# preseason view is genuinely worth something early, when it encodes an
# offseason of work and there are no games to argue with it, and worth
# progressively less as real ones accumulate. Weights are printed, never
# implicit.
LIVE_SOURCES = ("sleeper", "espn")
DECAY_WEEKS = 8


def source_weight(label: str, week: int, decay_weeks: int = DECAY_WEEKS) -> float:
    if label in LIVE_SOURCES:
        return 1.0
    played = max(0, int(week or 1) - 1)
    return round(max(0.0, 1.0 - played / float(decay_weeks or 1)), 3)


def _scoring(cfg) -> dict:
    return dict(cfg.get("scoring") or (cfg.get("expected") or {}).get("scoring") or {})


def _score(line: dict, scoring: dict) -> float:
    return sum(scoring.get(k, 0.0) * v for k, v in (line or {}).items() if v is not None)


def _sleeper(scoring: dict, season) -> tuple[dict[str, float], str | None]:
    # NOT under /v1: the projections endpoint sits on the bare host, and
    # draftkit.sleeper.BASE carries the /v1 suffix every other call needs.
    from draftkit.sleeper import get_json
    try:
        raw = get_json(
            f"https://api.sleeper.app/projections/nfl/{season}"
            "?season_type=regular"
            "&position[]=QB&position[]=RB&position[]=WR&position[]=TE")
    except Exception as e:  # noqa: BLE001
        return {}, f"sleeper unavailable ({e.__class__.__name__})"
    out = {}
    for row in raw or []:
        pid = str(row.get("player_id") or "")
        if pid:
            out[pid] = _score(row.get("stats") or {}, scoring)
    return out, None


def _espn(scoring: dict, season, raw_dir, index) -> tuple[dict[str, float], str | None]:
    try:
        from draftkit import espn as espn_mod
        from draftkit.ids import normalize_name
        raw = espn_mod.fetch_projections(season, Path(raw_dir))
        rows = espn_mod.parse_players(raw, season)
    except Exception as e:  # noqa: BLE001
        return {}, f"espn unavailable ({e.__class__.__name__})"
    if not index:
        return {}, "espn unmatched (no player index)"
    by_norm: dict[str, list[str]] = {}
    for pid, d in (index or {}).items():
        nm = d.get("full_name") or d.get("last_name")
        if nm and d.get("position"):
            by_norm.setdefault(normalize_name(nm), []).append(pid)
    out = {}
    for r in rows:
        c = [x for x in by_norm.get(normalize_name(r["name"]), [])
             if (index[x].get("position") == r["pos"])]
        if len(c) == 1:                       # ambiguous names are dropped, not guessed
            out[c[0]] = _score(r["line"], scoring)
    return out, None


def _sheet(cfg) -> tuple[dict[str, float], str | None]:
    name = getattr(cfg, "league_name", None)
    if not name:
        return {}, None
    p = Path("data/processed") / f"tiers.external.{name}.csv"
    if not p.exists():
        return {}, f"sheet absent ({p.name})"
    out = {}
    try:
        with p.open(encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                sid = (row.get("sleeper_id") or "").strip()
                try:
                    v = float(row.get("proj_pts") or 0.0)
                except ValueError:
                    continue
                if sid and v:
                    out[sid] = v
    except OSError as e:
        return {}, f"sheet unreadable ({e.__class__.__name__})"
    return out, f"sheet {_time.strftime('%Y-%m-%d', _time.localtime(p.stat().st_mtime))}"


def build(ctx, store=None) -> tuple[dict[str, dict], list[str]]:
    """sleeper_id -> {mean, n, spread, per_source}. Plus source notes.

    Cached in the store for TTL: three fetches per brief is wasteful and the
    numbers move on a daily cadence at best.
    """
    cfg = ctx["cfg"]
    season = (ctx.get("state") or {}).get("season") or ctx.get("season")
    ckey = f"consensus:{getattr(cfg, 'league_name', '?')}:{season}"
    if store is not None:
        cached = store.get(ckey)
        if cached and _time.time() - cached.get("ts", 0) < TTL:
            return cached["data"], list(cached.get("notes") or [])

    scoring = _scoring(cfg)
    notes: list[str] = []
    src: dict[str, dict[str, float]] = {}
    for label, (vals, note) in (
        ("sleeper", _sleeper(scoring, season)),
        ("espn", _espn(scoring, season,
                       cfg.path("raw") if hasattr(cfg, "path") else "data/raw",
                       ctx.get("players"))),
        ("sheet", _sheet(cfg)),
    ):
        if note:
            notes.append(f"{label}: {note}")
        if vals:
            src[label] = vals

    if not src:
        return {}, notes + ["DATA MISSING: no projection source reachable"]

    common = set.intersection(*({p for p, v in s.items() if v > FLOOR} for s in src.values())) \
        if len(src) > 1 else set()
    scale = {k: 1.0 for k in src}
    if len(common) >= MIN_COMMON:
        base = statistics.median(src["sleeper"][p] for p in common) if "sleeper" in src \
            else statistics.median(next(iter(src.values()))[p] for p in common)
        for k, s in src.items():
            med = statistics.median(s[p] for p in common)
            scale[k] = (base / med) if med else 1.0
    elif len(src) > 1:
        notes.append(f"sources not rescaled: only {len(common)} players in common")

    decay_weeks = int((ctx.get("scfg") or {}).get("consensus_decay_weeks", DECAY_WEEKS))
    week = int(ctx.get("week") or 1)
    weight = {k: source_weight(k, week, decay_weeks) for k in src}
    live = {k: w for k, w in weight.items() if w > 0}
    if not live:
        return {}, notes + ["DATA MISSING: every projection source has aged out"]

    out: dict[str, dict] = {}
    for pid in set().union(*(s.keys() for s in src.values())):
        per = {k: round(s[pid] * scale[k], 1) for k, s in src.items()
               if pid in s and s[pid] > 0 and weight[k] > 0}
        if not per:
            continue
        wsum = sum(weight[k] for k in per)
        mean = sum(v * weight[k] for k, v in per.items()) / wsum
        vals = list(per.values())
        out[pid] = {"mean": round(mean, 1), "n": len(vals),
                    "spread": round(max(vals) - min(vals), 1), "per_source": per,
                    "weights": {k: weight[k] for k in per}}

    wtxt = ", ".join(f"{k} x{weight[k]:g}" for k in sorted(src))
    notes.append(f"consensus over {len(live)} live sources ({wtxt}), "
                 f"{len(out)} players, rescaled on {len(common)} in common")
    aged = [k for k, w in weight.items() if 0 < w < 1.0]
    if aged:
        notes.append(f"⚠ preseason source(s) {', '.join(aged)} down-weighted to "
                     f"{', '.join(f'{weight[k]:g}' for k in aged)} — static file, "
                     f"reaches zero at week {decay_weeks + 1}")
    dead = [k for k, w in weight.items() if w == 0]
    if dead:
        notes.append(f"⚠ {', '.join(dead)} aged out of the consensus (preseason "
                     f"file, week {week})")
    if store is not None:
        store.set(ckey, {"ts": _time.time(), "data": out, "notes": notes})
    return out, notes


DEFAULT_CLAMP = (0.60, 1.60)


def apply(ctx, con: dict, *, min_sources: int = 2, clamp=DEFAULT_CLAMP
          ) -> tuple[int, list[str]]:
    """Re-base every projection on the consensus. Returns (n_changed, notes).

    RATIO, NOT REPLACEMENT. The sources give SEASON totals; the manager also
    needs a weekly number, and only Sleeper publishes one per week. That
    weekly figure carries the opponent, the bye and the matchup multiplier,
    which a season total cannot reconstruct. So the consensus sets the LEVEL
    and the existing weekly keeps the SHAPE: every projection key is scaled by
    consensus_mean / board_season.

    Guards, because a bad name match must not silently move a lineup:
      * a single source is not a consensus, so `min_sources` rows are skipped
      * a zero or missing board number has no ratio and is skipped
      * the ratio is clamped, and anything clamped is counted and reported

    Applied to the rosters AND wrapped around ctx["player_row"], so the free
    agent pool the waiver brief builds later is re-based on the same basis.
    Comparing a consensus roster against a single-source wire would be worse
    than using neither.
    """
    lo, hi = clamp
    changed = clamped = 0

    def _rescale(row: dict) -> dict:
        nonlocal changed, clamped
        if not isinstance(row, dict):
            return row
        r = con.get(str(row.get("sleeper_id") or ""))
        base = row.get("ros_season") or 0.0
        if not r or r.get("n", 0) < min_sources or not base:
            return row
        ratio = float(r["mean"]) / float(base)
        if not lo <= ratio <= hi:
            clamped += 1
            ratio = min(hi, max(lo, ratio))
        if abs(ratio - 1.0) < 1e-9:
            return row
        for k in ("weekly", "ros", "ros_season"):
            if row.get(k):
                row[k] = round(float(row[k]) * ratio, 2)
        row["consensus"] = r
        changed += 1
        return row

    for roster in (ctx.get("roster_players") or {}).values():
        for row in roster:
            _rescale(row)

    original = ctx.get("player_row")
    if callable(original) and not getattr(original, "_consensus_wrapped", False):
        def wrapped(pid, _orig=original):
            return _rescale(_orig(pid))
        wrapped._consensus_wrapped = True          # idempotent across modules
        ctx["player_row"] = wrapped

    notes = [f"projections re-based on the consensus: {changed} players adjusted"]
    if clamped:
        notes.append(f"⚠ {clamped} consensus ratios clamped to "
                     f"[{lo:.2f}, {hi:.2f}] — check for a bad name match")
    return changed, notes


def annotate(row: dict | None) -> str:
    """The inline suffix a brief shows next to a number.

    Silent when a single source carries the player -- claiming agreement you
    do not have is worse than saying nothing.
    """
    if not row or row.get("n", 0) < 2:
        return ""
    per = " / ".join(f"{v:.0f}" for _, v in sorted(row["per_source"].items()))
    return f" · {row['n']} sources {per}, spread {row['spread']:.0f}"


def confident(row: dict | None, edge: float, floor: float = 1.5) -> bool:
    """Is `edge` bigger than the sources' own disagreement?

    A 3-point edge between two players the shops argue about by 30 is not an
    edge, it is noise wearing a decimal point.
    """
    if not row or row.get("n", 0) < 2:
        return edge >= floor
    return edge >= max(floor, 0.5 * float(row.get("spread") or 0.0))
