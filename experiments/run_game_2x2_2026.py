# expires: 2026-11-11
"""Running back and offensive line together, as a 2x2 (the user's request, 2026-10-12). A study, not a
model: it changes nothing in the calculator (frozen to 2026-11-02, DECISIONS #245).

From Next Gen Stats (player tracking, through nflverse), season to date, every back NGS lists (25+ carries):
- x, what the blocking and the situation gave him: expected rush yards per carry. NGS's model sets each
  carry's expectation from where every blocker and defender is at the handoff -- so it is the line and
  the scheme (and the box), before the back does anything.
- y, what the back added: rush yards over expected per carry (actual minus expected).
Quadrants split at the league's expected yards per carry (weighted by tracked carries over the backs shown) and at
zero over expected. A team view sums each team's listed backs the same way. Context columns, from the
same file: share of carries against 8+ defenders in the box, and time to the line of scrimmage.

NGS prices only the carries it tracked (a few per back go untracked), so every per-carry expectation and
over-expected figure divides by tracked carries: rush_yards_over_expected / its own per-carry field, which
is a whole number for every back. A back whose ratio is not a whole number between 85% and 100% of his carries
falls back to all carries, and the output counts how many did. Carries shown and actual yards a carry use all
carries; the team 8+ box share is weighted by tracked carries, the carries NGS saw the box on."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from core import fetch as F  # noqa: E402

SEASON = 2026
ALIASES = {"LAR": "LA", "JAC": "JAX", "WSH": "WAS"}          # NGS codes -> the play-by-play's
QUADRANTS = {(True, True): "Both good", (False, True): "Back adding more than the blocking gave",
             (True, False): "Blocking giving more than the back adds", (False, False): "Both struggling"}


def load(season: int) -> pd.DataFrame:
    df = pd.read_csv(F.nflverse("ngs_rushing", max_age_s=F.CURRENT_SEASON_MAX_AGE_S))
    d = df[(df["season"] == season) & (df["season_type"] == "REG") & (df["week"] == 0)
           & (df["player_position"] == "RB")].copy()            # week 0 = season to date
    d["team"] = d["team_abbr"].replace(ALIASES)
    return d


TRACKED_MIN_SHARE = 0.85      # a ratio below this share of carries is noise from a near-zero per-carry figure


def tracked_carries(d: pd.DataFrame) -> tuple[pd.Series, int]:
    """Carries NGS priced: its over-expected total over its own per-carry figure. Kept only when that is a
    whole number between TRACKED_MIN_SHARE and 100% of carries; otherwise all carries. Returns the count
    and how many backs fell back."""
    att = d["rush_attempts"]
    per = d["rush_yards_over_expected_per_att"]
    raw = d["rush_yards_over_expected"] / per.where(per != 0)
    ok = ((raw - raw.round()).abs() < 0.05) & (raw.round() <= att) & (raw.round() >= TRACKED_MIN_SHARE * att)
    return raw.round().where(ok, att).astype(int), int((~ok).sum())


def backs(d: pd.DataFrame) -> tuple[pd.DataFrame, float, int]:
    tracked, fallbacks = tracked_carries(d)
    b = pd.DataFrame({"name": d["player_display_name"], "team": d["team"], "carries": d["rush_attempts"],
                      "tracked": tracked, "exp_ypc": d["expected_rush_yards"] / tracked,
                      "ryoe_pc": d["rush_yards_over_expected_per_att"],
                      "ypc": d["rush_yards"] / d["rush_attempts"],
                      "box8_pct": d["percent_attempts_gte_eight_defenders"],
                      "time_to_los": d["avg_time_to_los"], "expected_yards": d["expected_rush_yards"],
                      "ryoe": d["rush_yards_over_expected"]})
    mid = b["expected_yards"].sum() / b["tracked"].sum()
    # a fallback back's NGS per-carry figure is on tracked carries; recompute his on the same base as his x
    b["ryoe_pc"] = b["ryoe"] / b["tracked"]
    b["quadrant"] = [QUADRANTS[(x >= mid, y >= 0)] for x, y in zip(b["exp_ypc"], b["ryoe_pc"])]
    return b.sort_values("ryoe_pc", ascending=False).reset_index(drop=True), mid, fallbacks


def teams(b: pd.DataFrame, mid: float) -> pd.DataFrame:
    g = b.groupby("team")
    t = pd.DataFrame({"carries": g["carries"].sum(), "backs": g["name"].apply(lambda s: ", ".join(s)),
                      "exp_ypc": g["expected_yards"].sum() / g["tracked"].sum(),
                      "ryoe_pc": g["ryoe"].sum() / g["tracked"].sum(),
                      "box8_pct": (b["box8_pct"] * b["tracked"]).groupby(b["team"]).sum() / g["tracked"].sum()})
    t["quadrant"] = [QUADRANTS[(x >= mid, y >= 0)] for x, y in zip(t["exp_ypc"], t["ryoe_pc"])]
    return t.sort_values("ryoe_pc", ascending=False)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--season", type=int, default=SEASON)
    ap.add_argument("--out", type=Path, default=ROOT / "experiments" / "out" / "run_game_2x2_2026")
    a = ap.parse_args(argv)
    d = load(a.season)
    b, mid, fallbacks = backs(d)
    t = teams(b, mid)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    payload = {"season": a.season, "league_exp_ypc": mid, "n_backs": len(b), "carries": int(b["carries"].sum()),
               "tracked": int(b["tracked"].sum()), "tracked_fallbacks": fallbacks,
               "backs": b.drop(columns=["expected_yards", "ryoe"]).round(3).to_dict("records"),
               "teams": t.reset_index().round(3).to_dict("records")}
    a.out.with_suffix(".json").write_text(json.dumps(payload, indent=1), encoding="utf-8")
    L = [f"# Run game 2x2, {a.season} (Next Gen Stats, season to date)", "",
         f"{len(b)} backs with 25+ carries, {int(b['carries'].sum())} carries ({int(b['tracked'].sum())} tracked by NGS); "
         f"league expected {mid:.2f} yards a tracked carry."
         + (f" {fallbacks} back(s) fell back to all carries (NGS's tracked count unreadable)." if fallbacks else ""),
         "", "Each team's point sums only its backs NGS lists (25+ carries); a back under 25 carries is not in it. "
         "Yards over expected settles slowly: a back on 25-50 carries can move a full yard a carry on one long run, "
         "so the carry count is shown with every back.", ""]
    for q in QUADRANTS.values():
        names = [f"{r.name} ({r.team}, {int(r.carries)})" for r in b.itertuples() if r.quadrant == q]
        L += [f"**{q}** ({len(names)}): " + ", ".join(names), ""]
    L += ["| Team | Backs | Carries | Expected YPC | Over expected per carry | 8+ box % | Quadrant |", "|---|---|---|---|---|---|---|"]
    for team, r in t.iterrows():
        L.append(f"| {team} | {r['backs']} | {int(r['carries'])} | {r['exp_ypc']:.2f} | {r['ryoe_pc']:+.2f} | "
                 f"{r['box8_pct']:.0f}% | {r['quadrant']} |")
    a.out.with_suffix(".md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
