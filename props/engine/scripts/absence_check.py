#!/usr/bin/env python3
"""Where does an absent TE1's target share actually go? A spot check of the
receiving model's Out path, which hands an excluded player's share to the
remaining eligible players IN PROPORTION to their own shares.

  python absence_check.py [--seasons 2022,2023,2024,2025] [--out DIR]

For each team-season, the TE1 is the tight end with the most targets who
averaged at least a 15% target share in the games he played. Games where he
was NOT on the game-day active list are the absence games. For every other
player on the team (including fill-ins seen only in absence games), compare his target share in absence games with
his share in the TE1's games, against the proportional rule's prediction
share_in / (1 - TE1 share). Pooled by position, target-weighted.

The question: does the proportional rule overstate the boost to backs and
receivers (the Kittle example moved McCaffrey's Over 4.5 catches 65% -> 82%)
because in reality a TE2 absorbs most of a TE1's work?
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import td_model as T  # noqa: E402
from td_backtest import NV, fetch  # noqa: E402

COLS = ["game_id", "season", "week", "season_type", "posteam", "play_type", "receiver_player_id",
        "two_point_attempt"]


def season_frames(s: int):
    pbp = pd.read_csv(fetch(f"{NV}/pbp/play_by_play_{s}.csv.gz", f"pbp_{s}.csv.gz"),
                      usecols=COLS, low_memory=False)
    p = pbp[(pbp["season_type"] == "REG") & (pbp["play_type"] == "pass")
            & pbp["receiver_player_id"].notna() & (pbp["two_point_attempt"].fillna(0) != 1)]
    t = (p.assign(team=T._norm_team(p["posteam"]))
         .groupby(["season", "week", "game_id", "team", "receiver_player_id"]).size()
         .rename("tgt").reset_index().rename(columns={"receiver_player_id": "player_id"}))
    t["team_tgt"] = t.groupby(["game_id", "team"])["tgt"].transform("sum")
    t["share"] = t["tgt"] / t["team_tgt"]
    ros = pd.read_csv(fetch(f"{NV}/weekly_rosters/roster_weekly_{s}.csv", f"roster_weekly_{s}.csv"),
                      low_memory=False)
    ros = ros[(ros["game_type"] == "REG") & ros["gsis_id"].notna()]
    ros = ros.assign(team=T._norm_team(ros["team"]))
    return t, ros


def check(seasons) -> pd.DataFrame:
    out = []
    for s in seasons:
        t, ros = season_frames(s)
        pos = ros.drop_duplicates("gsis_id").set_index("gsis_id")["position"]
        t["pos"] = t["player_id"].map(pos)
        games = t[["game_id", "week", "team", "team_tgt"]].drop_duplicates(["game_id", "team"])
        act = set(zip(ros.loc[ros["status"] == "ACT", "week"], ros.loc[ros["status"] == "ACT", "team"],
                      ros.loc[ros["status"] == "ACT", "gsis_id"]))
        for team, tt in t.groupby("team"):
            te = tt[tt["pos"] == "TE"].groupby("player_id").agg(tgt=("tgt", "sum"), share=("share", "mean"))
            te = te[te["share"] >= 0.15]
            if te.empty:
                continue
            te1 = te["tgt"].idxmax()
            gt = games[games["team"] == team]
            played = set(tt.loc[tt["player_id"] == te1, "game_id"])
            absent = [g for g, w in zip(gt["game_id"], gt["week"]) if (w, team, te1) not in act and g not in played]
            if not absent or not played:
                continue
            s_te1 = float(tt.loc[tt["player_id"] == te1, "share"].mean())
            others = tt[tt["player_id"] != te1]
            inn = others[others["game_id"].isin(played)]
            out_ = others[others["game_id"].isin(absent)]
            n_in, n_out = len(played), len(absent)
            tin = gt[gt["game_id"].isin(played)]["team_tgt"].sum()
            tout = gt[gt["game_id"].isin(absent)]["team_tgt"].sum()
            a = inn.groupby("player_id").agg(tgt_in=("tgt", "sum"), pos=("pos", "first"))
            b = out_.groupby("player_id")["tgt"].sum().rename("tgt_out")
            # OUTER: a fill-in seen only while the TE1 is out (share 0 with him) is
            # exactly where much of the share goes, so he must stay in
            j = a.join(b, how="outer")
            j["tgt_in"] = j["tgt_in"].fillna(0)
            j["tgt_out"] = j["tgt_out"].fillna(0)
            j["pos"] = j["pos"].fillna(j.index.to_series().map(pos))
            j["share_in"] = j["tgt_in"] / tin
            j["share_out"] = j["tgt_out"] / tout
            j["pred_out"] = j["share_in"] / (1 - s_te1)
            # the scorer's rule: the excluded share goes only to the ELIGIBLE set, in
            # proportion. Eligibility approximated by a 5%+ share with the TE1.
            elig = j["share_in"] >= 0.05
            e_tot = j.loc[elig, "share_in"].sum()
            j["pred_elig"] = np.where(elig, j["share_in"] * (e_tot + s_te1) / e_tot, j["share_in"])
            j = j.assign(season=s, team=team, te1=te1, te1_share=s_te1, games_in=n_in, games_out=n_out)
            out.append(j.reset_index())
    return pd.concat(out, ignore_index=True) if out else pd.DataFrame()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seasons", default="2022,2023,2024,2025")
    ap.add_argument("--out", default=str(Path(__file__).resolve().parent / "backtest_out"))
    a = ap.parse_args(argv)
    seasons = [int(x) for x in a.seasons.split(",")]
    d = check(seasons)
    cases = d.drop_duplicates(["season", "team"])
    d["grp"] = np.where(d["pos"] == "TE", "other TEs", np.where(d["pos"] == "RB", "RBs",
                                                                np.where(d["pos"] == "WR", "WRs", "other")))
    L = ["# Where an absent TE1's targets go", "",
         f"Seasons {seasons}. {len(cases)} team-seasons with a TE1 (>= 15% target share) who missed games; "
         f"{int(cases['games_out'].sum())} absence games. Players seen in the TE1s games or the absence "
         "games, plus fill-ins seen only in absence games. Shares pooled over games, weighted by team targets.", "",
         "The scorer's Out path hands the absent share to the remaining eligible players in proportion.", "",
         "Two references: proportional over ALL remaining targets, and the scorer's actual rule -- "
         "proportional over the ELIGIBLE set only (approximated as players with a 5%+ share with the TE1), "
         "which gives a larger boost.", "",
         "| group | players | share with TE1 | predicted, all | predicted, eligible (scorer) | actual without | "
         "actual gain / scorer's gain |",
         "|---|---|---|---|---|---|---|"]
    for grp, g in d.groupby("grp"):
        w = g["games_out"]
        si, po, pe, so = (np.average(g[c], weights=w) for c in ("share_in", "pred_out", "pred_elig", "share_out"))
        ratio = (so - si) / (pe - si) if pe > si else float("nan")
        L.append(f"| {grp} | {len(g)} | {si:.3f} | {po:.3f} | {pe:.3f} | {so:.3f} | {ratio:.2f} |")
    top = d[d["pos"] == "RB"].sort_values("share_in", ascending=False).groupby(["season", "team"]).head(1)
    w = top["games_out"]
    si, pe, so = (np.average(top[c], weights=w) for c in ("share_in", "pred_elig", "share_out"))
    L += ["", f"Lead back only (the McCaffrey case): share {si:.3f} with the TE1, scorer's rule {pe:.3f}, "
              f"actual {so:.3f} -- actual gain / scorer's gain {(so - si) / (pe - si):.2f}.", "",
          "A ratio near 1 means the proportional rule is right for that group; well below 1 means it "
          "overstates the boost; above 1 means it understates it.", ""]
    path = Path(a.out) / "absence_te1.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"wrote {path}", file=sys.stderr)
    print("\n".join(L))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
