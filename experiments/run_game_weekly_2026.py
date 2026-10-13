# expires: 2026-11-11
"""The run game 2x2 over time: weeks 1-3 against the weeks after (the user's question, 2026-10-12: "were
bad backs catching up to good olines and improving?"). A study, not a model: it changes nothing in the
calculator (frozen to 2026-11-02, DECISIONS #245). The season view is run_game_2x2_2026.py.

Two sources, because neither alone is complete:
- Next Gen Stats weekly rows -- the 2x2 as defined (expected yards per tracked carry; yards over expected
  per tracked carry). NGS lists a back in a week only with 10+ carries that game, and lists few teams in
  weeks 1-2, so the weekly rows hold about 70% of the season's back carries; the coverage is printed.
  Early = weeks 1-3, late = weeks 4-5.
- Pro Football Reference weekly rushing -- every running-back carry, all 32 teams, weeks 1-4 posted in
  full: yards before contact per carry (mostly the line) and yards after contact per carry (mostly the
  back). Early = weeks 1-3, late = week 4. A cruder split (after contact undersells a back who makes his
  yards by avoiding contact), but complete.

For each source: a back's early point and late point, his early quadrant (split at that window's
carry-weighted league lines on both axes -- for NGS the listed backs' own average over expected, not 0, so
the listing's drift between windows is taken out), the games behind each window, and per early quadrant the
carry-weighted change in the back's axis. "Catching up" would show as the 'blocking beating the back'
group improving MORE than the other groups -- every group drifts toward average from one window to the
next (an extreme early number is part luck), so the groups are compared with each other, not with zero.
Small samples: a back needs 20+ carries early and 10+ late; the number of backs per group is printed."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from core import fetch as F  # noqa: E402
from experiments.run_game_2x2_2026 import ALIASES, tracked_carries  # noqa: E402
from props.calc import data  # noqa: E402

SEASON = 2026
EARLY = (1, 2, 3)
LATE = {"ngs": (4, 5), "pfr": (4,)}
MIN_EARLY, MIN_LATE = 20, 10
GROUPS = {(True, True): "Both good", (False, True): "Back beating his blocking",
          (True, False): "Blocking beating the back", (False, False): "Both struggling"}


def ngs_rows(season: int) -> tuple[pd.DataFrame, dict]:
    df = pd.read_csv(F.nflverse("ngs_rushing", max_age_s=F.CURRENT_SEASON_MAX_AGE_S))
    d = df[(df["season"] == season) & (df["season_type"] == "REG") & (df["player_position"] == "RB")].copy()
    total = d[d["week"] == 0]
    d = d[d["week"].isin(EARLY + LATE["ngs"])].copy()
    d["tracked"], fallbacks = tracked_carries(d)
    d["team"] = d["team_abbr"].replace(ALIASES)
    out = pd.DataFrame({"id": d["player_gsis_id"], "name": d["player_display_name"], "team": d["team"],
                        "week": d["week"], "carries": d["tracked"],
                        "x_sum": d["expected_rush_yards"], "y_sum": d["rush_yards_over_expected"]})
    cov = {"weekly rows' carries": int(d["rush_attempts"].sum()), "season carries (week 0)": int(total["rush_attempts"].sum()),
           "teams listed by week": d.groupby("week")["team"].nunique().to_dict(), "tracked-carry fallbacks": fallbacks}
    return out, cov


def pfr_rows(season: int) -> tuple[pd.DataFrame, dict]:
    a = pd.read_csv(F.nflverse("pfr_adv_rush", season, max_age_s=F.CURRENT_SEASON_MAX_AGE_S))
    a = a[a["week"].isin(EARLY + LATE["pfr"])]
    ros = data.rosters(season)
    latest = ros.dropna(subset=["pfr_id"]).sort_values("week").drop_duplicates("pfr_id", keep="last").set_index("pfr_id")
    a = a.assign(position=a["pfr_player_id"].map(latest["position"]))
    unmatched = int(a["position"].isna().sum())
    a = a[(a["position"] == "RB") & (a["carries"].fillna(0) > 0)]
    ybc = a["rushing_yards_before_contact"]
    yac = a["rushing_yards_after_contact"]
    missing = int((ybc.isna() | yac.isna()).sum())
    if missing:
        raise ValueError(f"{missing} PFR running-back rows with carries but no before/after-contact yards")
    out = pd.DataFrame({"id": a["pfr_player_id"], "name": a["pfr_player_name"], "team": a["team"], "week": a["week"],
                        "carries": a["carries"], "x_sum": ybc, "y_sum": yac})
    cov = {"teams by week": a.groupby("week")["team"].nunique().to_dict(), "rows with no roster position": unmatched}
    return out, cov


def window(r: pd.DataFrame, weeks) -> pd.DataFrame:
    w = r[r["week"].isin(weeks)].sort_values("week", kind="stable")
    g = w.groupby("id")
    return pd.DataFrame({"name": g["name"].last(), "team": g["team"].last(), "games": g["week"].nunique(),
                         "carries": g["carries"].sum(), "x": g["x_sum"].sum() / g["carries"].sum(),
                         "y": g["y_sum"].sum() / g["carries"].sum()})


def league_line(w: pd.DataFrame) -> dict:
    return {"x": float((w["x"] * w["carries"]).sum() / w["carries"].sum()),
            "y": float((w["y"] * w["carries"]).sum() / w["carries"].sum())}


def compare(r: pd.DataFrame, late_weeks) -> dict:
    e, l = window(r, EARLY), window(r, late_weeks)
    lines = {"early": league_line(e), "late": league_line(l)}
    both = e.join(l, lsuffix="_e", rsuffix="_l", how="inner")
    both = both[(both["carries_e"] >= MIN_EARLY) & (both["carries_l"] >= MIN_LATE)].copy()
    # each window measured against its own league line, so the drift of the whole league is taken out
    both["dy"] = (both["y_l"] - lines["late"]["y"]) - (both["y_e"] - lines["early"]["y"])
    both["dx"] = (both["x_l"] - lines["late"]["x"]) - (both["x_e"] - lines["early"]["x"])
    both["group"] = [GROUPS[(x >= lines["early"]["x"], y >= lines["early"]["y"])]
                     for x, y in zip(both["x_e"], both["y_e"])]
    summary = {}
    for grp in GROUPS.values():
        s = both[both["group"] == grp]
        wts = s["carries_l"]
        summary[grp] = {"backs": len(s),
                        "back axis change (late-weighted)": float((s["dy"] * wts).sum() / wts.sum()) if len(s) else None,
                        "blocking axis change": float((s["dx"] * wts).sum() / wts.sum()) if len(s) else None,
                        "now above the back line": int(((s["y_l"] - lines["late"]["y"]) >= 0).sum())}
    persist = {"back axis, early vs late (r)": float(both["y_e"].corr(both["y_l"])),
               "blocking axis, early vs late (r)": float(both["x_e"].corr(both["x_l"]))}
    rows = both.rename(columns={"name_e": "name", "team_e": "team"})[
        ["name", "team", "games_e", "carries_e", "x_e", "y_e", "games_l", "carries_l", "x_l", "y_l", "dx", "dy", "group"]]
    return {"lines": lines, "summary": summary, "persistence": persist, "n_backs": len(both),
            "rows": rows.sort_values("dy", ascending=False).round(3).to_dict("records")}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=ROOT / "experiments" / "out" / "run_game_weekly_2026")
    a = ap.parse_args(argv)
    ngs, cov_n = ngs_rows(SEASON)
    pfr, cov_p = pfr_rows(SEASON)
    res = {"ngs": {**compare(ngs, LATE["ngs"]), "coverage": cov_n},
           "pfr": {**compare(pfr, LATE["pfr"]), "coverage": cov_p}}
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.with_suffix(".json").write_text(json.dumps(res, indent=1, default=str), encoding="utf-8")
    L = [f"# Run game 2x2 over time, {SEASON}: weeks 1-3 vs later", ""]
    for key, label, late, unit in (("ngs", "Next Gen Stats (expected vs over expected)", "4-5", "over expected per carry"),
                                   ("pfr", "PFR (before contact vs after contact)", "4", "after contact per carry")):
        r = res[key]
        L += [f"## {label}: weeks 1-3 vs week(s) {late}", "",
              f"{r['n_backs']} backs with {MIN_EARLY}+ carries early and {MIN_LATE}+ late. Coverage: "
              + "; ".join(f"{k}: {v}" for k, v in r["coverage"].items()) + ".",
              "League lines (blocking axis / back axis): early "
              f"{r['lines']['early']['x']:.2f} / {r['lines']['early']['y']:+.2f}, late "
              f"{r['lines']['late']['x']:.2f} / {r['lines']['late']['y']:+.2f}.",
              "Same back, early vs late (correlation over these backs): back axis "
              f"r = {r['persistence']['back axis, early vs late (r)']:.2f}, blocking axis "
              f"r = {r['persistence']['blocking axis, early vs late (r)']:.2f}.", "",
              f"| Early group | Backs | Change in yards {unit}, vs league | Change in blocking axis, vs league | Now above the line |",
              "|---|---|---|---|---|"]
        for grp, s in r["summary"].items():
            f = (lambda v: "" if v is None else f"{v:+.2f}")
            L.append(f"| {grp} | {s['backs']} | {f(s['back axis change (late-weighted)'])} | "
                     f"{f(s['blocking axis change'])} | {s['now above the back line']} of {s['backs']} |")
        L += ["", "Groups of 2-10 backs: a group's change moves by tenths of a yard with one back, so read the "
              "direction across groups, not the decimals.",
              "", "| Back | Team | Group (weeks 1-3) | Games early / late | Carries early / late | Back axis early -> late | Blocking early -> late |",
              "|---|---|---|---|---|---|---|"]
        for x in r["rows"]:
            L.append(f"| {x['name']} | {x['team']} | {x['group']} | {int(x['games_e'])} / {int(x['games_l'])} | "
                     f"{int(x['carries_e'])} / {int(x['carries_l'])} | "
                     f"{x['y_e']:+.2f} -> {x['y_l']:+.2f} | {x['x_e']:.2f} -> {x['x_l']:.2f} |")
        L.append("")
    a.out.with_suffix(".md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
