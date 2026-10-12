# expires: 2026-11-11
"""Offensive line tiers, 2026 (the user's request, 2026-10-12). A study, not a model: it changes
nothing in the calculator (frozen to 2026-11-02, DECISIONS #245).

- Run blocking: yards before contact per running-back carry (Pro Football Reference, through nflverse),
  the cleanest public split of the line's work from the back's.
- Pass protection: pressures allowed per dropback (the passers' pressures, PFR; dropbacks from the
  play-by-play). It carries the quarterback too: one who holds the ball is pressured more behind the
  same line.
- Each is adjusted once for the defenses faced: a game's rate minus how far that opponent's defense
  sits from the league in its OTHER games (so a team is not credited for its own games twice).
- Both go on one score (50 = league average, 10 = one standard deviation; higher = better line) and are
  cut into the repo's S-F tiers (props.calc.matchup.tiers / tier_grade, the unit grades' own method).
- Overall = the average of the two scores, an equal weight, stated as a choice.
Games: those in both the play-by-play and PFR's files (a game the play-by-play does not have yet is left
out, and the report says how many games each team has)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from core import fetch as F  # noqa: E402
from props.calc import data, matchup  # noqa: E402

SEASON = 2026


def load(season: int):
    rush = pd.read_csv(F.nflverse("pfr_adv_rush", season))
    pas = pd.read_csv(F.nflverse("pfr_adv_pass", season))
    pbp = data.pbp(season)                    # regular season, through core.fetch
    ros = data.rosters(season)
    return rush, pas, pbp, ros


def team_games(rush, pas, pbp, ros) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """(run rows, pass rows, notes): one row per team-game with its numerator and denominator."""
    games = set(pbp["game_id"].unique()) & set(rush["game_id"].unique()) & set(pas["game_id"].unique())
    rush = rush[rush["game_id"].isin(games) & (rush["game_type"] == "REG")]
    pas = pas[pas["game_id"].isin(games) & (pas["game_type"] == "REG")]
    pbp = pbp[pbp["game_id"].isin(games)]
    # running backs: PFR id -> position from the weekly rosters (his latest listing this season)
    pos = (ros.dropna(subset=["pfr_id"]).sort_values("week").drop_duplicates("pfr_id", keep="last")
           .set_index("pfr_id")["position"])
    rush = rush.assign(position=rush["pfr_player_id"].map(pos))
    unmatched = int(rush["position"].isna().sum())
    rb = rush[rush["position"] == "RB"]
    run = (rb.groupby(["game_id", "team", "opponent"], as_index=False)
             .agg(num=("rushing_yards_before_contact", "sum"), den=("carries", "sum")))
    press = pas.groupby(["game_id", "team", "opponent"], as_index=False).agg(num=("times_pressured", "sum"))
    drop = (pbp[pbp["qb_dropback"] == 1].groupby(["game_id", "posteam"]).size()
            .rename("den").reset_index().rename(columns={"posteam": "team"}))
    sacks = (pbp[pbp["sack"] == 1].groupby(["game_id", "posteam"]).size()
             .rename("sacks").reset_index().rename(columns={"posteam": "team"}))
    pas_rows = press.merge(drop, on=["game_id", "team"], how="inner").merge(sacks, on=["game_id", "team"], how="left")
    pas_rows["sacks"] = pas_rows["sacks"].fillna(0)
    notes = {"games": len(games), "rush rows without a roster position": unmatched,
             "weeks": sorted(pbp.loc[pbp["game_id"].isin(games), "week"].unique().tolist())}
    return run[run["den"] > 0], pas_rows[pas_rows["den"] > 0], notes


def adjusted(rows: pd.DataFrame) -> pd.DataFrame:
    """Per team: raw rate, and the rate adjusted once for the defenses faced (each game's rate minus that
    opponent defense's distance from the league in its other games), both weighted by plays."""
    league = rows["num"].sum() / rows["den"].sum()
    d_num = rows.groupby("opponent")["num"].sum()
    d_den = rows.groupby("opponent")["den"].sum()
    rest_num = rows["opponent"].map(d_num) - rows["num"]
    rest_den = rows["opponent"].map(d_den) - rows["den"]
    opp_effect = (rest_num / rest_den - league).where(rest_den > 0, 0.0)
    rows = rows.assign(adj_w=(rows["num"] / rows["den"] - opp_effect) * rows["den"])
    g = rows.groupby("team")
    return pd.DataFrame({"raw": g["num"].sum() / g["den"].sum(), "adj": g["adj_w"].sum() / g["den"].sum(),
                         "plays": g["den"].sum(), "games": g["game_id"].nunique()})


def score(s: pd.Series, higher_is_better: bool) -> pd.Series:
    z = (s - s.mean()) / s.std(ddof=0)
    return 50 + 10 * (z if higher_is_better else -z)


def build(season: int) -> tuple[pd.DataFrame, dict]:
    run_rows, pass_rows, notes = team_games(*load(season))
    run = adjusted(run_rows)
    pas = adjusted(pass_rows)
    pas["sacks"] = pass_rows.groupby("team")["sacks"].sum()
    t = pd.DataFrame({"run_score": score(run["adj"], True), "pass_score": score(pas["adj"], False)})
    t["overall"] = (t["run_score"] + t["pass_score"]) / 2
    for col in ("run_score", "pass_score", "overall"):
        tr = matchup.tiers(t[col].round(1).to_dict(), True)
        t[col.replace("score", "tier") if col != "overall" else "overall_tier"] = [matchup.tier_grade(tr, x) for x in t.index]
    t = t.join(run.add_prefix("run_")).join(pas.add_prefix("pass_"))
    return t.sort_values("overall", ascending=False), notes


def report(t: pd.DataFrame, notes: dict, season: int) -> str:
    L = [f"# Offensive line tiers, {season} (weeks {', '.join(map(str, notes['weeks']))})", "",
         "Run blocking: yards before contact per running-back carry. Pass protection: pressures allowed per "
         "dropback (it includes the quarterback's time to throw). Each adjusted once for the defenses faced; "
         "scores: 50 = league average, 10 = one standard deviation, higher = better line; overall = the two "
         "averaged. Tiers S (best) to F, the unit grades' own method. Five weeks of games: read these as tiers, "
         "not an exact order.", "",
         "| # | Team | Overall | Run block | YBC per RB carry (adjusted) | Pass pro | Pressure rate (adjusted) | Sacks | Games |",
         "|---|---|---|---|---|---|---|---|---|"]
    for i, (team, r) in enumerate(t.iterrows(), 1):
        L.append(f"| {i} | {team} | **{r['overall_tier']}** ({r['overall']:.0f}) | {r['run_tier']} ({r['run_score']:.0f}) | "
                 f"{r['run_raw']:.2f} ({r['run_adj']:.2f}) | {r['pass_tier']} ({r['pass_score']:.0f}) | "
                 f"{r['pass_raw'] * 100:.1f}% ({r['pass_adj'] * 100:.1f}%) | {int(r['pass_sacks'])} | {int(r['pass_games'])} |")
    L += ["", f"Games used: {notes['games']}. PFR rushing rows with no roster position (left out of the running-back "
          f"carries): {notes['rush rows without a roster position']}."]
    return "\n".join(L) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--season", type=int, default=SEASON)
    ap.add_argument("--out", type=Path, default=ROOT / "experiments" / "out" / "oline_tiers_2026.md")
    a = ap.parse_args(argv)
    t, notes = build(a.season)
    text = report(t, notes, a.season)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(text, encoding="utf-8")
    t.to_csv(a.out.with_suffix(".csv"))
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
