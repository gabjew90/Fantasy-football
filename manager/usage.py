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
