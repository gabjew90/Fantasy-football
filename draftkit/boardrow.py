"""One definition of the ENGINE-FACING numbers on a board row.

Three loaders built the same dict by hand: `scripts/engine_parity.load_board`
(offline replays and every gate), `scripts/yahoo_bridge.load_players` (the
live Yahoo rig), and `draftkit/projections.external_projection`'s own select
list. They drifted, twice, and both times silently:

  * external_projection kept a hardcoded copy of the dispersion columns and
    selected `pts17_band` away three functions after it was computed;
  * yahoo_bridge never carried `proj_band` at all, so the same board that
    showed the analyst spread in an offline replay dropped it in a live room.

A column missing here does not raise. It reads as "the board does not carry
this", which is indistinguishable from a real absence, so the failure surfaces
as an engine that quietly ignores a signal rather than as an error. Hence one
definition, imported by every reader.

This module owns only the numeric fields the ENGINE reasons about. Presentation
fields (upside_why, starter fragility labels) and identity fields (sleeper_id,
name, team, bye) stay with each caller, because they legitimately differ.
"""

from __future__ import annotations

# name -> (kind, default). "f" float-or-default, "fn" float-or-None,
# "i" int-or-default, "b" bool, "s" str.
ENGINE_FIELDS: dict[str, tuple[str, object]] = {
    "vorp": ("f", 0.0),
    "proj_pts": ("f", 0.0),
    "adp_delta": ("f", 0.0),
    "tier": ("i", 9),
    "pos_rank": ("i", 99),
    "value_rank": ("i", 999),
    "cliff_flag": ("b", False),
    "upside_flag": ("b", False),
    "proj_source": ("s", "blend"),
    "backs_up": ("s", ""),
    # adp is None when the market does not rank him: the survival sim reads
    # that as "always available", which a 0.0 would not mean
    "adp": ("fn", None),
    # market-implied projection: floors the planner fallback (DECISIONS #39)
    "proj_market_pts": ("fn", None),
    # dispersion. proj_sd/n_sources are disagreement BETWEEN feeds; proj_band
    # is the analyst panel's spread INSIDE one feed (draftkit/external.py)
    "proj_sd": ("fn", None),
    "proj_hi": ("fn", None),
    "proj_lo": ("fn", None),
    "proj_band": ("fn", None),
    "n_sources": ("i", 0),
    # DECISIONS #35: Yahoo default rank (o_rank), for the list-walking autopick
    "yahoo_rank": ("fn", None),
    # DECISIONS #53: projected touchdowns, the tie_break: touchdowns input
    "proj_td": ("fn", None),
}


def published_range(q: dict) -> tuple[float | None, float | None]:
    """(floor, ceiling) of one board row: the source's own published low and
    high lines when it published a range, else the point minus/plus half the
    band, else (None, None). A single source with no lines carries
    proj_lo == proj_hi == proj_pts (external._with_dispersion_single), which
    is NOT a range and must not be read as one (review 2026-09-05): the
    planner's floor rule and the bench ceiling tiebreak both call this."""
    pts = q.get("proj_pts")
    lo, hi = q.get("proj_lo"), q.get("proj_hi")
    ok = lambda v: v is not None and v == v   # noqa: E731 - NaN guard
    band = q.get("proj_band")
    half = float(band) / 2.0 if ok(band) and pts is not None and float(band) > 0 else None
    # both ends sitting on the point is "no range published", not a range
    if ok(lo) and ok(hi) and pts is not None and float(lo) == float(pts) == float(hi):
        lo = hi = None
    floor = float(lo) if ok(lo) else (float(pts) - half if half is not None else None)
    ceiling = float(hi) if ok(hi) else (float(pts) + half if half is not None else None)
    return floor, ceiling


def engine_fields(r: dict) -> dict:
    """The engine-facing numbers from one board row (a csv DictReader row or a
    polars row dict). `vorp_flex` falls back to `vorp` for older boards."""
    out: dict = {}
    for name, (kind, default) in ENGINE_FIELDS.items():
        raw = r.get(name)
        blank = raw is None or raw == ""
        if kind == "s":
            out[name] = (raw or default) if not blank else default
        elif kind == "b":
            out[name] = str(raw).strip().lower() == "true" if isinstance(raw, str) else bool(raw)
        elif kind == "fn":
            try:
                out[name] = None if blank else float(raw)
            except (TypeError, ValueError):
                out[name] = None
        elif kind == "i":
            try:
                out[name] = default if blank else int(float(raw))
            except (TypeError, ValueError):
                out[name] = default
        else:
            try:
                out[name] = default if blank else float(raw)
            except (TypeError, ValueError):
                out[name] = default
    vf = r.get("vorp_flex")
    try:
        out["vorp_flex"] = float(vf) if vf not in (None, "") else out["vorp"]
    except (TypeError, ValueError):
        out["vorp_flex"] = out["vorp"]
    return out
