# expires: 2026-11-11
"""Running backs on role vs creation, with the blocking as colour (the user's framework, 2026-10-12). A study,
not a model: it changes nothing in the calculator (frozen to 2026-11-02, DECISIONS #245). Its quadrant
actions (hold / candidate sell / candidate buy / drop) are labels to be TESTED, not findings: whether
creation predicts a later change of role is a separate backtest, not run here.

- x, role: one score from three of the back's shares of his team's work, in the games he played:
  carries 50%, carries inside the opponent's 10 25%, targets 25% (a stated choice; targets stand in for
  route participation, which no public feed carries). Inside-10 work is lumpy -- a few plays flip it -- so
  it is blended, never used alone.
- y, creation: missed tackles forced (PFR's broken tackles, on carries and catches) per touch (carries plus
  catches). Yards after contact per carry is shown beside it as the secondary check.
- colour, the blocking: the team's Next Gen Stats expected yards per carry (run_game_2x2_2026.py, weeks 1-5,
  frozen at the handoff, so the back's own vision is not in it), against the league.
Weeks: only those PFR has posted for every game in the play-by-play (PFR runs behind it), for both axes, so
role and creation cover the same games. A back is a running back by his latest weekly roster listing, with
fullbacks (depth chart FB) left out; PFR and snap ids map to gsis ids through the rosters. A back needs 30+
touches. Quadrants split at the median role score of the backs shown (a stated choice: half the listed
backs are 'high role') and at the league's missed tackles per touch over every running back's touches."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from core import fetch as F  # noqa: E402
from experiments import run_game_2x2_2026 as rg  # noqa: E402
from props.calc import data  # noqa: E402

SEASON = 2026
WEIGHTS = {"carry_share": 0.50, "i10_share": 0.25, "target_share": 0.25}
MIN_TOUCHES = 30
COLS = ["game_id", "season", "week", "season_type", "posteam", "yardline_100", "rush_attempt", "pass_attempt", "sack",
        "two_point_attempt", "qb_kneel", "rusher_player_id", "receiver_player_id", "complete_pass"]
ACTIONS = {(True, True): "Hold: lead role, creates", (True, False): "Candidate sell: role carrying him",
           (False, True): "Candidate buy: creates, small role", (False, False): "Drop: small role, little created"}


def flag(s: pd.Series) -> pd.Series:
    return s.fillna(0).astype(float) > 0


def full_pfr_weeks(p: pd.DataFrame, pfr: pd.DataFrame) -> list[int]:
    """Weeks in which PFR lists every team the play-by-play has."""
    have = pfr.groupby("week")["team"].apply(set)
    need = p.groupby("week")["posteam"].apply(lambda s: set(s.dropna()))
    return sorted(w for w in need.index if w in have.index and need[w] <= have[w])


def build(season: int) -> tuple[pd.DataFrame, dict]:
    age = {"max_age_s": F.CURRENT_SEASON_MAX_AGE_S}
    p = pd.read_csv(F.nflverse("pbp", season, **age), usecols=COLS, low_memory=False)
    p = p[p["season_type"] == "REG"]
    rush = pd.read_csv(F.nflverse("pfr_adv_rush", season, **age))
    rec = pd.read_csv(F.nflverse("pfr_adv_rec", season, **age))
    weeks = full_pfr_weeks(p, rush)
    p, rush, rec = (x[x["week"].isin(weeks)] for x in (p, rush, rec))

    ros = data.rosters(season)
    latest = ros.dropna(subset=["gsis_id"]).sort_values("week").drop_duplicates("gsis_id", keep="last")
    depth = pd.read_csv(F.nflverse("rosters_weekly", season, **age), usecols=["gsis_id", "week", "depth_chart_position"])
    depth = depth.dropna(subset=["gsis_id"]).sort_values("week").drop_duplicates("gsis_id", keep="last")
    fb = set(depth.loc[depth["depth_chart_position"] == "FB", "gsis_id"])
    rbs = set(latest.loc[latest["position"] == "RB", "gsis_id"]) - fb
    pfr_gsis = dict(zip(*ros.dropna(subset=["pfr_id", "gsis_id"]).drop_duplicates("pfr_id")[["pfr_id", "gsis_id"]].T.values))

    # plays: carries and targets as props.calc.data counts them, plus inside the 10
    car = p[flag(p["rush_attempt"]) & ~flag(p["two_point_attempt"]) & ~flag(p["qb_kneel"]) & p["rusher_player_id"].notna()]
    car = car.assign(i10=car["yardline_100"] <= 10)
    tgt = p[flag(p["pass_attempt"]) & ~flag(p["sack"]) & ~flag(p["two_point_attempt"]) & p["receiver_player_id"].notna()]
    team_g = pd.DataFrame({"t_car": car.groupby(["game_id", "posteam"]).size(),
                           "t_i10": car.groupby(["game_id", "posteam"])["i10"].sum(),
                           "t_tgt": tgt.groupby(["game_id", "posteam"]).size()}).fillna(0)
    pl = pd.DataFrame({"car": car.groupby(["game_id", "posteam", "rusher_player_id"]).size(),
                       "i10": car.groupby(["game_id", "posteam", "rusher_player_id"])["i10"].sum()})
    pl.index.names = ["game_id", "posteam", "gsis_id"]
    tg = tgt.groupby(["game_id", "posteam", "receiver_player_id"]).agg(tgt=("complete_pass", "size"),
                                                                       rec=("complete_pass", lambda s: int(flag(s).sum())))
    tg.index.names = ["game_id", "posteam", "gsis_id"]
    # games he played: offensive snaps (props.calc.data.played), so a game with no touch still counts
    played = data.played(data.snaps(season), ros)
    played = played[played["game_id"].isin(set(p["game_id"])) & played["gsis_id"].isin(rbs)]
    g = played.rename(columns={"team": "posteam"}).set_index(["game_id", "posteam", "gsis_id"])[[]]
    g = g.join(pl, how="outer").join(tg, how="outer").fillna(0).reset_index()
    g = g[g["gsis_id"].isin(rbs)]
    g = g.join(team_g, on=["game_id", "posteam"])

    per = g.groupby("gsis_id")
    b = pd.DataFrame({"games": per["game_id"].nunique(), "team": g.sort_values("game_id").groupby("gsis_id")["posteam"].last(),
                      "carries": per["car"].sum(), "i10": per["i10"].sum(), "targets": per["tgt"].sum(),
                      "receptions": per["rec"].sum(), "t_car": per["t_car"].sum(), "t_i10": per["t_i10"].sum(),
                      "t_tgt": per["t_tgt"].sum()})
    b["name"] = latest.set_index("gsis_id")["full_name"].reindex(b.index)

    # PFR creation: broken tackles on carries (rush file) and on catches (receiving file), yards after contact
    rush = rush.assign(gsis_id=rush["pfr_player_id"].map(pfr_gsis))
    rec = rec.assign(gsis_id=rec["pfr_player_id"].map(pfr_gsis))
    unmapped = sorted(set(rush.loc[rush["gsis_id"].isna(), "pfr_player_name"]) | set(rec.loc[rec["gsis_id"].isna(), "pfr_player_name"]))
    b["bt_rush"] = rush.groupby("gsis_id")["rushing_broken_tackles"].sum().reindex(b.index).fillna(0)
    b["bt_rec"] = rec.groupby("gsis_id")["receiving_broken_tackles"].sum().reindex(b.index).fillna(0)
    b["yac_sum"] = rush.groupby("gsis_id")["rushing_yards_after_contact"].sum().reindex(b.index)
    b["pfr_carries"] = rush.groupby("gsis_id")["carries"].sum().reindex(b.index).fillna(0)
    b["touches"] = b["carries"] + b["receptions"]
    notes = {"weeks": weeks, "PFR rows with no gsis id": unmapped,
             "backs whose PFR carries differ from the play-by-play by more than 2":
                 sorted(b.loc[(b["pfr_carries"] - b["carries"]).abs() > 2, "name"].fillna("?"))}
    return b, notes


def rates(b: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    league_bt = (b["bt_rush"] + b["bt_rec"]).sum() / b["touches"].sum()      # every running back's touches
    league_yac = b["yac_sum"].sum() / b.loc[b["yac_sum"].notna(), "pfr_carries"].sum()
    r = b[b["touches"] >= MIN_TOUCHES].copy()
    r["carry_share"] = r["carries"] / r["t_car"]
    r["i10_share"] = (r["i10"] / r["t_i10"]).where(r["t_i10"] > 0, 0.0)
    r["target_share"] = r["targets"] / r["t_tgt"]
    r["role"] = 100 * sum(w * r[k] for k, w in WEIGHTS.items())
    r["mtf_per_touch"] = (r["bt_rush"] + r["bt_rec"]) / r["touches"]
    r["yac_per_carry"] = r["yac_sum"] / r["pfr_carries"]
    r["touches_pg"] = r["touches"] / r["games"]
    role_mid = float(r["role"].median())
    r["action"] = [ACTIONS[(x >= role_mid, y >= league_bt)] for x, y in zip(r["role"], r["mtf_per_touch"])]

    # colour: the team's NGS expected yards per carry against the league (weeks 1-5)
    tb, mid, _ = rg.backs(rg.load(SEASON))
    tt = rg.teams(tb, mid)
    r["team_exp_ypc"] = r["team"].map(tt["exp_ypc"])
    r["block_vs_league"] = r["team_exp_ypc"] - mid
    lines = {"role_median": role_mid, "league_mtf_per_touch": float(league_bt), "league_yac_per_carry": float(league_yac),
             "league_exp_ypc": float(mid)}
    keep = ["name", "team", "games", "carries", "i10", "targets", "receptions", "touches", "touches_pg", "carry_share",
            "i10_share", "target_share", "role", "bt_rush", "bt_rec", "mtf_per_touch", "yac_per_carry", "team_exp_ypc",
            "block_vs_league", "action"]
    return r[keep].sort_values("role", ascending=False).reset_index(names="gsis_id"), lines


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=ROOT / "experiments" / "out" / "role_creation_2x2_2026")
    a = ap.parse_args(argv)
    b, notes = build(SEASON)
    r, lines = rates(b)
    if r["team_exp_ypc"].isna().any():
        raise ValueError(f"teams with no NGS expected yards: {sorted(r.loc[r['team_exp_ypc'].isna(), 'team'])}")
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.with_suffix(".json").write_text(json.dumps({"lines": lines, "weights": WEIGHTS, "notes": notes,
                                                      "rows": r.round(4).to_dict("records")}, indent=1, default=str),
                                          encoding="utf-8")
    L = [f"# Role vs creation, {SEASON} (weeks {notes['weeks'][0]}-{notes['weeks'][-1]}: the weeks PFR has in full)", "",
         f"{len(r)} running backs with {MIN_TOUCHES}+ touches. Role = carries {WEIGHTS['carry_share']:.0%}, inside-10 carries "
         f"{WEIGHTS['i10_share']:.0%}, targets {WEIGHTS['target_share']:.0%} of the team's, in his games; split at the median "
         f"{lines['role_median']:.1f}. Creation = missed tackles forced per touch; league {lines['league_mtf_per_touch']:.3f} "
         f"(yards after contact {lines['league_yac_per_carry']:.2f} a carry). Colour = team NGS expected yards per carry vs "
         f"{lines['league_exp_ypc']:.2f}. The actions are candidates until a backtest tests them.", ""]
    for act in ACTIONS.values():
        names = [f"{x['name']} ({x['team']}, role {x['role']:.0f}, {x['mtf_per_touch']:.3f} MTF/touch, {int(x['touches'])} touches)"
                 for x in r.to_dict("records") if x["action"] == act]
        L += [f"**{act}** ({len(names)}): " + ", ".join(names), ""]
    L += [f"Notes: " + "; ".join(f"{k}: {v}" for k, v in notes.items())]
    a.out.with_suffix(".md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
