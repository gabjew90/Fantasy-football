"""Weekend usage from nflverse (nfl_data_py): snap %, target share, targets,
carries, receiving yards — week-over-week deltas as role-change evidence.

Inside-10 carries and route/YPRR data are not in the free weekly dataset;
the brief says so explicitly rather than fabricating (spec rule).
"""

from __future__ import annotations

import logging

log = logging.getLogger("manager")

MISSING_NOTE = ("DATA MISSING: inside-10 carries and route participation/YPRR "
                "(not in free nflverse weekly data)")


def load_usage(season: int) -> tuple[dict | None, str | None]:
    """name(lower) -> {week -> row}. None + note when the season isn't published."""
    try:
        import nfl_data_py as nfl
        df = nfl.import_weekly_data([season])
    except Exception as e:  # noqa: BLE001 — any failure degrades the section
        return None, f"DATA MISSING: nflverse weekly usage ({e.__class__.__name__})"
    if df is None or len(df) == 0:
        return None, f"DATA MISSING: nflverse weekly usage ({season} not yet published)"
    out: dict[str, dict[int, dict]] = {}
    cols = df.columns
    for _, r in df.iterrows():
        name = str(r.get("player_display_name") or "").lower()
        if not name:
            continue
        out.setdefault(name, {})[int(r["week"])] = {
            "targets": float(r.get("targets") or 0),
            "target_share": float(r.get("target_share") or 0) if "target_share" in cols else None,
            "carries": float(r.get("carries") or 0),
            "rec_yards": float(r.get("receiving_yards") or 0),
        }
    return out, None


def load_snaps(season: int) -> dict | None:
    """name(lower) -> {week -> offense snap pct}."""
    try:
        import nfl_data_py as nfl
        df = nfl.import_snap_counts([season])
    except Exception:  # noqa: BLE001
        return None
    if df is None or len(df) == 0:
        return None
    out: dict[str, dict[int, float]] = {}
    for _, r in df.iterrows():
        name = str(r.get("player") or "").lower()
        if name:
            out.setdefault(name, {})[int(r["week"])] = float(r.get("offense_pct") or 0)
    return out


def evidence(name: str, usage: dict | None, snaps: dict | None,
             last_week: int) -> str | None:
    """Week-over-week numbers for one player, or None if we have nothing."""
    if last_week < 1:
        return None
    key = name.lower()
    rows = (usage or {}).get(key, {})
    cur, prev = rows.get(last_week), rows.get(last_week - 1)
    parts = []
    if cur:
        def delta(field, label, pct=False):
            c = cur.get(field)
            if c is None:
                return
            p = (prev or {}).get(field)
            if pct:
                c_s = f"{c:.0%}"
                parts.append(f"{label} {(f'{p:.0%} -> ' if p is not None else '')}{c_s}")
            else:
                parts.append(f"{label} {(f'{p:.0f} -> ' if p is not None else '')}{c:.0f}")
        delta("target_share", "target share", pct=True)
        delta("targets", "targets")
        delta("carries", "carries")
        delta("rec_yards", "rec yds")
    srows = (snaps or {}).get(key, {})
    if last_week in srows:
        sp, sc = srows.get(last_week - 1), srows[last_week]
        parts.append(f"snaps {(f'{sp:.0%} -> ' if sp is not None else '')}{sc:.0%}")
    return "; ".join(parts) if parts else None


SPIKE_RATIO = 1.5      # production up 50%+ week-over-week...
FLAT_SHARE_PP = 0.03   # ...while target share moved under 3 points
FLAT_SNAP_PP = 0.05    # ...and snaps under 5 points


def overreaction(name: str, usage: dict | None, snaps: dict | None,
                 last_week: int) -> str | None:
    """One spike week with flat underlying usage -> the damper clause,
    else None. Needs both the spike week and the prior week to judge."""
    if last_week < 2:
        return None
    rows = (usage or {}).get(name.lower(), {})
    cur, prev = rows.get(last_week), rows.get(last_week - 1)
    if not cur or not prev:
        return None
    spiked = (prev.get("rec_yards", 0) > 0 and
              cur.get("rec_yards", 0) >= SPIKE_RATIO * prev["rec_yards"]) or              (prev.get("targets", 0) > 0 and
              cur.get("targets", 0) >= SPIKE_RATIO * prev["targets"])
    if not spiked:
        return None
    ts_c, ts_p = cur.get("target_share"), prev.get("target_share")
    share_flat = (ts_c is not None and ts_p is not None
                  and abs(ts_c - ts_p) < FLAT_SHARE_PP)
    srows = (snaps or {}).get(name.lower(), {})
    sn_c, sn_p = srows.get(last_week), srows.get(last_week - 1)
    snaps_flat = (sn_c is not None and sn_p is not None
                  and abs(sn_c - sn_p) < FLAT_SNAP_PP)
    if share_flat and (snaps_flat or sn_c is None):
        return (f"bid damped: one-week spike with flat usage (target share "
                f"{ts_p:.0%}->{ts_c:.0%}"
                + (f", snaps {sn_p:.0%}->{sn_c:.0%}" if snaps_flat else "")
                + ") — chasing points, not a role change")
    return None
