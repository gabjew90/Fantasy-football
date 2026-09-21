#!/usr/bin/env python3
"""Tune where an absent player's target and carry share goes, for the
scorer's Out path (score_game.py, section A2).

  python absence_tune.py [--tune 2022,2023] [--test 2024,2025] [--out DIR]

THE RULE. A fraction y of the absent player's share goes to the eligible
(priced) teammates at all; the rest goes to players outside that set -- the
call-up or promoted backup who had almost no share while he played. Of the
part that stays, a fraction x goes to every eligible teammate in proportion to
his own share and 1 - x to eligible teammates at the absent player's POSITION
(to nobody priced when none is eligible). The scorer shipped with y = 1,
x = 1. (x, y) are tuned separately for targets and carries on the TUNE
seasons' absence games and scored as-is on TEST.

EVENTS. For each team-season, every player who averaged a 15%+ target share
(targets) or 20%+ carry share (carries) in the games he played, and missed
games -- not on the game-day active list and no opportunity. His share and
his teammates' shares are pooled over the games he played; the teammates'
actual shares over the games he missed. ELIGIBLE approximates the scorer's
priced set: a 5%+ share in the games he played.

LOSS. Squared error of each eligible teammate's predicted share without him
against his actual share, weighted by the number of absence games; a
bootstrap over events gives the interval for the test difference.
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
        "rusher_player_id", "two_point_attempt", "qb_kneel"]
KINDS = {"targets": ("receiver_player_id", "pass", 0.15), "carries": ("rusher_player_id", "run", 0.20)}
XS = [round(x, 2) for x in np.linspace(0, 1, 11)]
YS = [0.0, 0.25, 0.5, 0.75, 1.0]
SHIPPED = (1.0, 1.0)
ELIG = 0.05


def season_frames(s: int):
    pbp = pd.read_csv(fetch(f"{NV}/pbp/play_by_play_{s}.csv.gz", f"pbp_{s}.csv.gz"),
                      usecols=COLS, low_memory=False)
    pbp = pbp[(pbp["season_type"] == "REG") & (pbp["two_point_attempt"].fillna(0) != 1)
              & (pbp["qb_kneel"].fillna(0) != 1)]
    ros = pd.read_csv(fetch(f"{NV}/weekly_rosters/roster_weekly_{s}.csv", f"roster_weekly_{s}.csv"),
                      low_memory=False)
    ros = ros[(ros["game_type"] == "REG") & ros["gsis_id"].notna()].assign(team=lambda r: T._norm_team(r["team"]))
    out = {}
    for kind, (col, pt, _) in KINDS.items():
        p = pbp[(pbp["play_type"] == pt) & pbp[col].notna()]
        t = (p.assign(team=T._norm_team(p["posteam"]))
             .groupby(["season", "week", "game_id", "team", col]).size()
             .rename("n").reset_index().rename(columns={col: "player_id"}))
        t["team_n"] = t.groupby(["game_id", "team"])["n"].transform("sum")
        t["share"] = t["n"] / t["team_n"]
        out[kind] = t
    return out, ros


def events(seasons, kind: str) -> pd.DataFrame:
    """One row per (event, eligible teammate): share_in, share_out, pos, and
    the absent player's share and position."""
    thr = KINDS[kind][2]
    rows = []
    for s in seasons:
        frames, ros = season_frames(s)
        t = frames[kind]
        pos = ros.drop_duplicates("gsis_id").set_index("gsis_id")["position"].replace({"FB": "RB"})
        t = t.assign(pos=t["player_id"].map(pos))
        act = set(zip(ros.loc[ros["status"] == "ACT", "week"], ros.loc[ros["status"] == "ACT", "team"],
                      ros.loc[ros["status"] == "ACT", "gsis_id"]))
        games = t[["game_id", "week", "team", "team_n"]].drop_duplicates(["game_id", "team"])
        for team, tt in t.groupby("team"):
            gt = games[games["team"] == team]
            key = tt.groupby("player_id").agg(n=("n", "sum"), share=("share", "mean"), pos=("pos", "first"))
            for kid, kr in key[(key["share"] >= thr) & key["pos"].isin(["RB", "WR", "TE"])].iterrows():
                played = set(tt.loc[tt["player_id"] == kid, "game_id"])
                absent = [g for g, w in zip(gt["game_id"], gt["week"]) if (w, team, kid) not in act and g not in played]
                if not absent:
                    continue
                tin = gt[gt["game_id"].isin(played)]["team_n"].sum()
                tout = gt[gt["game_id"].isin(absent)]["team_n"].sum()
                others = tt[tt["player_id"] != kid]
                a = others[others["game_id"].isin(played)].groupby("player_id")["n"].sum() / tin
                b = others[others["game_id"].isin(absent)].groupby("player_id")["n"].sum() / tout
                j = pd.DataFrame({"share_in": a, "share_out": b}).fillna(0.0)
                j["pos"] = j.index.map(pos)
                # what the players OUTSIDE the eligible set took, with him and without
                small_in = float(j.loc[j["share_in"] < ELIG, "share_in"].sum())
                small_out = float(j.loc[j["share_in"] < ELIG, "share_out"].sum())
                j = j[j["share_in"] >= ELIG]
                if j.empty:
                    continue
                k_share = float(tt.loc[tt["player_id"] == kid, "n"].sum() / tin)
                rows.append(j.reset_index().assign(event=f"{s}_{team}_{kid}", season=s, team=team,
                                                   k_share=k_share, k_pos=kr["pos"], games_out=len(absent),
                                                   small_in=small_in, small_out=small_out))
    return pd.concat(rows, ignore_index=True)


def predict(d: pd.DataFrame, xy) -> np.ndarray:
    """Predicted share without the absent player under (x, y)."""
    x, y = xy
    E = d.groupby("event")["share_in"].transform("sum")
    same = d["pos"] == d["k_pos"]
    Ep = d["share_in"].where(same, 0.0).groupby(d["event"]).transform("sum")
    freed = y * d["k_share"]
    cross = x * freed * d["share_in"] / E
    own = np.where(same & (Ep > 0), (1 - x) * freed * d["share_in"] / Ep.where(Ep > 0, 1.0), 0.0)
    return (d["share_in"] + cross + own).to_numpy()


def loss(d: pd.DataFrame, xy) -> float:
    e = (predict(d, xy) - d["share_out"].to_numpy()) ** 2
    return float(np.average(e, weights=d["games_out"]))


def boot_diff(d: pd.DataFrame, xa, xb, reps=2000, seed=11):
    w = d["games_out"].to_numpy()
    ea = (predict(d, xa) - d["share_out"].to_numpy()) ** 2 * w
    eb = (predict(d, xb) - d["share_out"].to_numpy()) ** 2 * w
    g = pd.DataFrame({"e": d["event"], "a": ea, "b": eb, "w": w}).groupby("e").sum()
    a, b, ww = g["a"].to_numpy(), g["b"].to_numpy(), g["w"].to_numpy()
    idx = np.random.default_rng(seed).integers(0, len(a), size=(reps, len(a)))
    bs = (a[idx].sum(1) - b[idx].sum(1)) / ww[idx].sum(1)
    return (a.sum() - b.sum()) / ww.sum(), *np.percentile(bs, [2.5, 97.5])


def gains(d: pd.DataFrame, xy) -> dict:
    """Actual gain / predicted gain by teammate position group."""
    p = predict(d, xy)
    g = d.assign(pred=p, grp=np.where(d["pos"] == d["k_pos"], "same position", "other positions"))
    out = {}
    for grp, h in g.groupby("grp"):
        w = h["games_out"]
        si, pr, so = (np.average(h[c], weights=w) for c in ("share_in", "pred", "share_out"))
        out[grp] = (si, pr, so, (so - si) / (pr - si) if pr != si else float("nan"))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tune", default="2022,2023")
    ap.add_argument("--test", default="2024,2025")
    ap.add_argument("--out", default=str(Path(__file__).resolve().parent / "backtest_out"))
    a = ap.parse_args(argv)
    tune = [int(x) for x in a.tune.split(",")]
    test = [int(x) for x in a.test.split(",")]
    L = ["# Where an absent player's share goes: the Out path, tuned", "",
         f"Tune {tune}, test {test}. Rule: a fraction y of the absent player's share goes to eligible "
         "(priced) teammates at all, the rest to players outside that set; of the part that stays, x goes to "
         "every eligible teammate pro rata and 1 - x to eligible teammates at his position. The scorer shipped "
         "with x = 1, y = 1. Eligible = 5%+ share in the games he played.", ""]
    chosen = {}
    for kind in KINDS:
        dtu, dte = events(tune, kind), events(test, kind)
        tl = {(x, y): loss(dtu, (x, y)) for x in XS for y in YS}
        best = min(tl, key=tl.get)
        chosen[kind] = best
        ev = dte.drop_duplicates("event")
        w = ev["games_out"]
        L += [f"## {kind.title()}", "",
              f"Tune: {dtu['event'].nunique()} absence events, {int(dtu.drop_duplicates('event')['games_out'].sum())} "
              f"games. Test: {dte['event'].nunique()} events, {int(w.sum())} games.", "",
              f"Test: the absent player held {np.average(ev['k_share'], weights=w):.3f} of the team's {kind}. Players "
              f"OUTSIDE the eligible set went from {np.average(ev['small_in'], weights=w):.3f} with him to "
              f"{np.average(ev['small_out'], weights=w):.3f} without him.", "",
              "Tune loss (x 1e4), rows x, columns y:", "",
              "| x | " + " | ".join(f"y={y:g}" for y in YS) + " |", "|---" * (len(YS) + 1) + "|"]
        for x in XS:
            L.append(f"| {x:g} | " + " | ".join(
                (f"**{tl[(x, y)] * 1e4:.2f}**" if (x, y) == best else f"{tl[(x, y)] * 1e4:.2f}") for y in YS) + " |")
        m, lo, hi = boot_diff(dte, best, SHIPPED)
        L += ["", f"Test, chosen x = {best[0]:g}, y = {best[1]:g} vs shipped x = 1, y = 1: loss "
                  f"{loss(dte, best) * 1e4:.3f} vs {loss(dte, SHIPPED) * 1e4:.3f} (x 1e4); difference "
                  f"{m * 1e4:+.3f} ({lo * 1e4:+.3f}, {hi * 1e4:+.3f}), "
                  f"{'better' if hi < 0 else 'worse' if lo > 0 else 'not established'}.", "",
              "Test, actual gain / predicted gain by teammate group (1.00 = the rule is right):", "",
              "| group | share with him | predicted, shipped | predicted, chosen | actual | ratio shipped | ratio chosen |",
              "|---|---|---|---|---|---|---|"]
        g1, gb = gains(dte, SHIPPED), gains(dte, best)
        for grp in g1:
            si, p1, so, r1 = g1[grp]
            _, pb, _, rb = gb[grp]
            L.append(f"| {grp} | {si:.3f} | {p1:.3f} | {pb:.3f} | {so:.3f} | {r1:.2f} | {rb:.2f} |")
        L.append("")
    L += [f"Chosen: targets x = {chosen['targets'][0]:g}, y = {chosen['targets'][1]:g}; "
          f"carries x = {chosen['carries'][0]:g}, y = {chosen['carries'][1]:g}.", ""]
    path = Path(a.out) / "absence_tune.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"wrote {path}", file=sys.stderr)
    print("\n".join(L))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
