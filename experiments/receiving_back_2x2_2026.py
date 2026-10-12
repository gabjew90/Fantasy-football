# expires: 2026-11-11
"""Running backs as receivers, as a 2x2 (the user's request, 2026-10-12). A study, not a model: it changes
nothing in the calculator (frozen to 2026-11-02, DECISIONS #245). The rushing version is
run_game_2x2_2026.py; this is its receiving twin.

From the nflverse play-by-play and snap counts, regular season, 2025 and 2026:
- x, his receiving role: targets per 100 offensive snaps. The team decides it, and in PPR every catch
  is a point.
- y, what he does with the ball: yards after the catch over expected, per catch. nflverse prices each
  completion's expected yards after the catch (xyac_mean_yardage, from where the catch is made and the
  game situation; play-by-play, not player tracking, so rougher than NGS's rushing model), and a running
  back's catch is mostly yards after it.
Context columns: catch rate over expected (catches minus nflverse's catch probability, per target),
yards per target (incompletions count as zero) and yards per catch.

A target is what props.calc.data.targets counts: a pass attempt with a named receiver, not a sack, not a
two-point try. A back is a running back by his latest weekly roster listing of that season (an id with no
roster listing is left out and counted). Snaps map from PFR ids to gsis ids through the weekly rosters, as
props.calc.data.played does; a back whose snaps cannot be mapped is left out and named.
Views: each season alone (15+ targets) and 2025-26 pooled (25+ targets, team = his 2026 team, or his 2025
team if he has no 2026 targets). Quadrants split at the running backs' own rate (all shown backs' targets
over their snaps) and at zero over expected."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from core import fetch as F  # noqa: E402
from props.calc import data  # noqa: E402

SEASONS = (2025, 2026)
MIN_TARGETS = {"season": 15, "pooled": 25}
COLS = ["game_id", "season", "week", "season_type", "posteam", "pass_attempt", "sack", "two_point_attempt",
        "receiver_player_id", "complete_pass", "receiving_yards", "yards_after_catch", "xyac_mean_yardage", "cp"]
QUADRANTS = {(True, True): "Featured weapon", (False, True): "Underused weapon",
             (True, False): "Volume checkdown", (False, False): "Not a receiving back"}


def flag(s: pd.Series) -> pd.Series:
    return s.fillna(0).astype(float) > 0


def season_rows(season: int) -> tuple[pd.DataFrame, dict]:
    """One row per running back with a target this season: counts and sums (rates come later, so seasons pool)."""
    max_age = F.CURRENT_SEASON_MAX_AGE_S if season == max(SEASONS) else None
    kw = {"max_age_s": max_age} if max_age else {}
    p = pd.read_csv(F.nflverse("pbp", season, **kw), usecols=COLS, low_memory=False)
    p = p[p["season_type"] == "REG"]
    t = p[flag(p["pass_attempt"]) & ~flag(p["sack"]) & ~flag(p["two_point_attempt"])
          & p["receiver_player_id"].notna()].copy()
    t["caught"] = flag(t["complete_pass"])
    t["yards"] = t["receiving_yards"].where(t["caught"], 0.0).fillna(0.0)
    priced = t["caught"] & t["yards_after_catch"].notna() & t["xyac_mean_yardage"].notna()
    t["yac_oe"] = (t["yards_after_catch"] - t["xyac_mean_yardage"]).where(priced)
    t["cp_oe"] = (t["caught"].astype(float) - t["cp"]).where(t["cp"].notna())

    ros = data.rosters(season)
    latest = ros.dropna(subset=["gsis_id"]).sort_values("week").drop_duplicates("gsis_id", keep="last")
    pos = latest.set_index("gsis_id")["position"]
    t["position"] = t["receiver_player_id"].map(pos)
    no_listing = int(t["position"].isna().sum())
    rb = t[t["position"] == "RB"]

    g = rb.groupby("receiver_player_id")
    out = pd.DataFrame({"targets": g.size(), "receptions": g["caught"].sum(), "rec_yards": g["yards"].sum(),
                        "yac_oe_sum": g["yac_oe"].sum(), "priced_catches": g["yac_oe"].count(),
                        "cp_oe_sum": g["cp_oe"].sum(), "cp_targets": g["cp_oe"].count(),
                        "team": g["posteam"].agg(lambda s: s.iloc[-1])})   # plays are in game order: his latest team

    # snaps: PFR id -> gsis id through the rosters (props.calc.data.played's mapping), games with plays loaded
    snap = data.snaps(season)
    snap = snap[snap["game_id"].isin(set(p["game_id"])) & (snap["offense_snaps"].fillna(0) > 0)]
    ids = ros.dropna(subset=["pfr_id", "gsis_id"]).drop_duplicates("pfr_id")
    snap = snap.assign(gsis_id=snap["pfr_player_id"].map(dict(zip(ids["pfr_id"], ids["gsis_id"]))))
    out["snaps"] = snap.dropna(subset=["gsis_id"]).groupby("gsis_id")["offense_snaps"].sum().reindex(out.index)
    no_snaps = out[out["snaps"].isna()]
    names = latest.set_index("gsis_id")["full_name"]
    out["name"] = names.reindex(out.index)
    out["season"] = season
    notes = {"targets without a roster listing": no_listing,
             "backs with targets but no mapped snaps (left out)": sorted(names.reindex(no_snaps.index).fillna("?")),
             "completions without expected yards after the catch": int((t["caught"] & ~priced).sum())}
    return out.dropna(subset=["snaps"]), notes


def rates(r: pd.DataFrame, min_targets: int) -> tuple[pd.DataFrame, float]:
    r = r[r["targets"] >= min_targets].copy()
    r["tgt_per100"] = 100 * r["targets"] / r["snaps"]
    r["yac_oe_pc"] = r["yac_oe_sum"] / r["priced_catches"]
    r["cr_oe"] = 100 * r["cp_oe_sum"] / r["cp_targets"]                 # percentage points
    r["yds_per_tgt"] = r["rec_yards"] / r["targets"]
    r["yds_per_rec"] = r["rec_yards"] / r["receptions"]
    mid = 100 * r["targets"].sum() / r["snaps"].sum()
    r["quadrant"] = [QUADRANTS[(x >= mid, y >= 0)] for x, y in zip(r["tgt_per100"], r["yac_oe_pc"])]
    keep = ["name", "team", "snaps", "targets", "receptions", "rec_yards", "priced_catches", "tgt_per100",
            "yac_oe_pc", "cr_oe", "yds_per_tgt", "yds_per_rec", "quadrant"]
    return r[keep].sort_values("yac_oe_pc", ascending=False).reset_index(names="gsis_id"), mid


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=ROOT / "experiments" / "out" / "receiving_back_2x2_2026")
    a = ap.parse_args(argv)
    per, notes = {}, {}
    for s in SEASONS:
        per[s], notes[s] = season_rows(s)
    both = pd.concat(per.values())
    sums = both.groupby(level=0)[["targets", "receptions", "rec_yards", "yac_oe_sum", "priced_catches",
                                  "cp_oe_sum", "cp_targets", "snaps"]].sum()
    last = both.sort_values("season").groupby(level=0)[["team", "name"]].last()
    pooled = sums.join(last)
    views = {}
    for key, frame, m in ((str(SEASONS[1]), per[SEASONS[1]], MIN_TARGETS["season"]),
                          (str(SEASONS[0]), per[SEASONS[0]], MIN_TARGETS["season"]),
                          (f"{SEASONS[0]}-{str(SEASONS[1])[2:]}", pooled, MIN_TARGETS["pooled"])):
        r, mid = rates(frame, m)
        views[key] = {"min_targets": m, "mid": mid, "rows": r.round(3).to_dict("records")}
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.with_suffix(".json").write_text(json.dumps({"views": views, "notes": {str(k): v for k, v in notes.items()}},
                                                     indent=1), encoding="utf-8")
    L = ["# Receiving backs 2x2 (nflverse play-by-play and snap counts, regular season)", ""]
    for key, v in views.items():
        rows = v["rows"]
        L += [f"## {key}: {len(rows)} backs with {v['min_targets']}+ targets; running backs' rate "
              f"{v['mid']:.1f} targets per 100 snaps", ""]
        for q in QUADRANTS.values():
            names = [f"{r['name']} ({r['team']}, {r['targets']} tgt, {r['priced_catches']} priced catches)"
                     for r in rows if r["quadrant"] == q]
            L += [f"**{q}** ({len(names)}): " + ", ".join(names), ""]
    L += ["Yards after the catch over expected settles slowly: 20-30 catches is a small sample, so the target and "
          "priced-catch counts are shown with every back.", ""]
    for s, n in notes.items():
        L.append(f"- {s}: " + "; ".join(f"{k}: {v}" for k, v in n.items()))
    a.out.with_suffix(".md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
