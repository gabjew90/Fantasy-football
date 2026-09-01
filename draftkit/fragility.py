"""Standing contingency map + starter fragility (post-v2 item 3).

INFORMATIONAL ONLY. Nothing in this module may reach projections, VORP,
tiers, or any recommendation ranking — it produces displayed columns and
brief annotations. Module 1's contingency class already fires once a starter
is actually injured; this is the standing version that says who WOULD
inherit a role, and how fragile the incumbent is.

Fragility uses only signals research.md supports:
  - position (RB carries the highest structural risk)
  - workload (touches per game in the CURRENT season)
  - injury type when a designation exists (structural > soft-tissue)
It deliberately does NOT use games-missed history (research Q6: near-zero
year-over-year predictive value — the durability haircut built on it was
removed on 2026-08-30). Do not reintroduce it here.
"""

from __future__ import annotations

import polars as pl

# position base rates: RB highest, QB lowest (research Q6 — what little
# signal exists lives in position and workload, not personal history)
POS_BASE = {"RB": 0.55, "TE": 0.35, "WR": 0.30, "QB": 0.25}
# Saturation point for the workload term. hv_touches counts HIGH-VALUE
# touches (goal-line carries + targets) for a SEASON, not total touches:
# the RB p99 is 42 and the max 50, so an 18-per-game threshold made the term
# contribute ~nothing (caught in verification, 2026-08-31).
HIGH_WORKLOAD = 40.0   # season high-value touches at which the term saturates
WORKLOAD_WEIGHT = {"RB": 0.30, "WR": 0.10, "TE": 0.10, "QB": 0.10}

# body parts with structural (season-threatening) vs soft-tissue (recurring)
# risk. Anything unrecognised contributes nothing rather than a guess.
# Injury TYPES, never body parts. "knee" and "foot" were in this list
# until 2026-09-01, which scored a knee bruise or a foot sprain exactly
# like a torn ACL. An unrecognised description still contributes zero,
# so being narrow here is the safe direction.
STRUCTURAL = ("acl", "mcl", "pcl", "meniscus", "achilles", "lisfranc",
              "patell", "fracture")
SOFT_TISSUE = ("hamstring", "groin", "calf", "quad", "oblique")


def fragility(pos: str, workload: float | None,
              injury_part: str | None = None) -> float | None:
    """0..1 fragility of an incumbent starter (workload = SEASON high-value
    touches). None when the position is unknown."""
    base = POS_BASE.get(pos)
    if base is None:
        return None
    score = base
    if workload is not None:
        load = min(float(workload), HIGH_WORKLOAD) / HIGH_WORKLOAD
        score += WORKLOAD_WEIGHT.get(pos, 0.10) * load
    if injury_part:
        p = str(injury_part).lower()
        if any(k in p for k in STRUCTURAL):
            score += 0.15
        elif any(k in p for k in SOFT_TISSUE):
            score += 0.08
    return round(min(score, 1.0), 2)


def label(score: float | None) -> str:
    if score is None:
        return ""
    if score >= 0.75:
        return "high"
    if score >= 0.55:
        return "moderate"
    return "low"


def add_contingency_map(df: pl.DataFrame, injury: dict[str, str] | None = None,
                        injury_part: dict[str, str] | None = None) -> pl.DataFrame:
    """Add backs_up_pos / starter_fragility / starter_fragility_label.

    Depth order is inferred from the board's own within-team, within-position
    value ranking (no depth-chart feed exists in free data). A player with no
    identifiable incumbent gets empty fields rather than a guess.
    """
    name_col = "player" if "player" in df.columns else "name"
    if "team" not in df.columns:
        return df
    injury = injury or {}
    injury_part = injury_part or {}

    skill = df.filter(pl.col("pos").is_in(list(POS_BASE)) & pl.col("team").is_not_null())
    if skill.height == 0:
        return df

    # incumbent = highest-value healthy player at (team, pos)
    healthy = skill
    if "avail_status" in skill.columns:
        h = skill.filter(pl.col("avail_status").fill_null("") != "out")
        healthy = h if h.height else skill
    incumbent = (
        healthy.sort("vorp", descending=True)
        .group_by(["team", "pos"], maintain_order=True)
        .first()
        .select("team", "pos",
                pl.col(name_col).alias("_inc_name"),
                pl.col("sleeper_id").cast(pl.Utf8).alias("_inc_id"),
                pl.col("hv_touches").fill_null(0).alias("_inc_tpg"))
    )
    out = df.join(incumbent, on=["team", "pos"], how="left")

    frag, lab, backs = [], [], []
    for r in out.iter_rows(named=True):
        inc_id, inc_name = r.get("_inc_id"), r.get("_inc_name")
        me = str(r.get("sleeper_id"))
        if not inc_name or inc_id == me:
            frag.append(None); lab.append(""); backs.append(None)
            continue
        part = injury_part.get(str(inc_id)) or ""
        f = fragility(r["pos"], r.get("_inc_tpg"), part)
        frag.append(f)
        lab.append(label(f))
        backs.append(inc_name)
    return out.with_columns(
        pl.Series("backs_up_pos", backs, dtype=pl.Utf8),
        pl.Series("starter_fragility", frag, dtype=pl.Float64),
        pl.Series("starter_fragility_label", lab, dtype=pl.Utf8),
    ).drop(["_inc_name", "_inc_id", "_inc_tpg"], strict=False)
