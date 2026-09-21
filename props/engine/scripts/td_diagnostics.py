#!/usr/bin/env python3
"""Two structural checks on anytime_td_v1, run before layer 3 is designed.

  python td_diagnostics.py [--seasons 2022,2023] [--confirm 2024,2025] [--out DIR]

1. SHARE BY TEAM TOUCHDOWN COUNT. P(score) = sum_k P(N = k) (1 - q)^k assumes
   a player's per-touchdown share q is the same on his team's fourth
   touchdown as on its first. If four-touchdown games are blowouts whose late
   scores go to backups, the top-share player's realised share falls with k
   and a backup's rises -- the pattern of the calibration misses (top bins
   high, lowest bin low). The answer decides whether the layer-3 sim draws
   shares once per game or conditions each touchdown on the count or script.

2. STARTING-QUARTERBACK LEVEL. v1.1 ranks starters better but predicts 0.123
   against 0.148. Whether the channel weight (the starter's QB-rush rate,
   shrunk to a league fraction pooled over past seasons) or his share within
   the channel is what runs low.

Diagnostic, not tuning: it reads the TUNE seasons for the finding and the
test seasons only as confirmation. Every number comes out of the harness
(td_alloc_backtest.run), which calls td_v1 -- the priced model.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import td_alloc_backtest as B  # noqa: E402
import td_model as T  # noqa: E402
import td_v1 as V  # noqa: E402

QK_SHIP = (B.SHIP[0], B.SHIP[2], B.SHIP[3])
QK_V10 = (B.V10[0], B.V10[2], B.V10[3])
K_BINS = [(1, 1, "1"), (2, 2, "2"), (3, 3, "3"), (4, 99, "4+")]
RANKS = [(1, 1, "1 (top q)"), (2, 2, "2"), (3, 3, "3"), (4, 6, "4-6"), (7, 99, "7+")]


def _bucket(x, bins):
    for lo, hi, lab in bins:
        if lo <= x <= hi:
            return lab
    return None


def prepare(d: pd.DataFrame, tg: pd.DataFrame) -> pd.DataFrame:
    q = f"q|{B.qid(QK_SHIP)}"
    d = d[d["n_off"] > 0].copy()
    d["q"] = d[q]
    d["rank"] = d.groupby(["game_id", "team"])["q"].rank(ascending=False, method="first").astype(int)
    d["rank_b"] = d["rank"].map(lambda r: _bucket(r, RANKS))
    d["k_b"] = d["n_off"].map(lambda k: _bucket(k, K_BINS))
    pts = tg.set_index(["game_id", "team"])["points"]
    opp = tg.merge(tg[["game_id", "team", "points"]], on="game_id", suffixes=("", "_opp"))
    opp = opp[opp["team"] != opp["team_opp"]].set_index(["game_id", "team"])["points_opp"]
    idx = pd.MultiIndex.from_arrays([d["game_id"], d["team"]])
    d["opp_pts"] = opp.reindex(idx).to_numpy()
    d["margin"] = pts.reindex(idx).to_numpy() - d["opp_pts"]
    # spread from the team's view: POSITIVE = favoured (team_games convention)
    d["spread"] = tg.set_index(["game_id", "team"])["spread"].reindex(idx).to_numpy()
    return d


def _boot_ratio(g: pd.DataFrame, reps=1000, seed=7):
    """Realised / expected touchdowns, game-clustered 95% interval."""
    x = g.groupby("game_id").agg(r=("tds", "sum"), e=("exp", "sum"))
    r, e = x["r"].to_numpy(), x["e"].to_numpy()
    idx = np.random.default_rng(seed).integers(0, len(r), size=(reps, len(r)))
    bs = r[idx].sum(1) / e[idx].sum(1)
    return r.sum() / e.sum(), *np.percentile(bs, [2.5, 97.5])


def share_tables(L: list, d: pd.DataFrame, label: str) -> None:
    d = d.assign(exp=d["q"] * d["n_off"])
    L += [f"### {label}: realised touchdowns / expected (k x q), by rank of q within the team-game", "",
          "1.00 means the player's share on a k-touchdown day is what the model assumes. A top-share "
          "ratio falling with k, and a backup ratio rising, is the blowout pattern.", "",
          "| rank | " + " | ".join(f"k = {lab}" for *_, lab in K_BINS) + " |",
          "|---" * (len(K_BINS) + 1) + "|"]
    for *_, rl in RANKS:
        cells = []
        for *_, kl in K_BINS:
            g = d[(d["rank_b"] == rl) & (d["k_b"] == kl)]
            if len(g) < 30:
                cells.append("-")
                continue
            m, lo, hi = _boot_ratio(g)
            cells.append(f"{m:.2f} ({lo:.2f}-{hi:.2f})")
        L.append(f"| {rl} | " + " | ".join(cells) + " |")
    L += ["", "Same cells as realised share of team touchdowns vs mean q (n team-games):", "",
          "| rank | " + " | ".join(f"k = {lab}" for *_, lab in K_BINS) + " |",
          "|---" * (len(K_BINS) + 1) + "|"]
    for *_, rl in RANKS:
        cells = []
        for *_, kl in K_BINS:
            g = d[(d["rank_b"] == rl) & (d["k_b"] == kl)]
            cells.append(f"{g['tds'].sum() / g['n_off'].sum():.3f} vs {g['q'].mean():.3f} "
                         f"(n {g['game_id'].nunique()})" if len(g) else "-")
        L.append(f"| {rl} | " + " | ".join(cells) + " |")
    # Mechanism: does the top player's share move with the game state? NOT split
    # by final margin -- his own touchdowns move it (a blanked star makes
    # 'trailing' likelier), which manufactures the effect. Split by what he
    # cannot move: the pre-game spread, and the OPPONENT's points.
    L += ["", "Mechanism check, top-q player, all k: realised / expected by pre-game spread and by the "
              "opponent's points (neither is moved by his own touchdowns).", "",
          "| state | ratio (95% CI) | team-games |", "|---|---|---|"]
    top = d[d["rank"] == 1]
    for lab, m in (("pre-game underdog by 3+", top["spread"] <= -3), ("pre-game within 3", top["spread"].abs() < 3),
                   ("pre-game favourite by 3+", top["spread"] >= 3),
                   ("opponent scored 27+", top["opp_pts"] >= 27), ("opponent scored 14-26", top["opp_pts"].between(14, 26)),
                   ("opponent scored 13 or fewer", top["opp_pts"] <= 13)):
        g = top[m]
        if len(g) >= 30:
            r, lo, hi = _boot_ratio(g)
            L.append(f"| {lab} | {r:.2f} ({lo:.2f}-{hi:.2f}) | {len(g)} |")
    L.append("")


def qb_tables(L: list, d: pd.DataFrame, mass: pd.DataFrame, label: str) -> None:
    mm = mass[mass["n_off"] > 0]
    real = mm["qb_rush_tds"].sum() / mm["n_off"].sum()
    st = d[d["starter"]]
    L += [f"### {label}: starting quarterbacks", "",
          "| | team mix (v1) | starter rate (v1.1) | realised |", "|---|---|---|---|",
          f"| qb_rush weight: mean, team-games with a TD | {mm['wqb|' + B.qid(QK_V10)].mean():.4f} | "
          f"{mm['wqb|' + B.qid(QK_SHIP)].mean():.4f} | {real:.4f} (QB-rush TDs / offensive TDs) |",
          f"| league fraction used as the shrinkage target | {mm['qb_league'].mean():.4f} | "
          f"{mm['qb_league'].mean():.4f} | |",
          f"| starter per-TD share q | {st['q|' + B.qid(QK_V10)].mean():.4f} | {st['q|' + B.qid(QK_SHIP)].mean():.4f} | "
          f"{st['tds'].sum() / st['n_off'].sum():.4f} (his TDs / team offensive TDs) |",
          f"| starter P(score) given the team's TD count | {st['n|' + B.cid(B.V10)].mean():.3f} | "
          f"{st['n|' + B.cid(B.SHIP)].mean():.3f} | {st['scored'].mean():.3f} |", ""]
    # within-channel share: starter's TDs over the team's QB-rush TDs, against q / weight
    stm = st.merge(mm[["game_id", "team", "qb_rush_tds", "wqb|" + B.qid(QK_SHIP)]], on=["game_id", "team"])
    implied_s = (stm["q|" + B.qid(QK_SHIP)] / stm["wqb|" + B.qid(QK_SHIP)]).clip(upper=1).mean()
    real_s = stm["tds"].sum() / max(stm["qb_rush_tds"].sum(), 1)
    L += [f"Within the channel: starter's implied share of QB-rush TDs (q / weight, capped at 1) "
          f"{implied_s:.3f}; realised starter TDs / team QB-rush TDs {real_s:.3f} "
          "(a starter's TDs are almost all QB rushes).", ""]


def starter_channel(L: list, mass: pd.DataFrame, cch: pd.DataFrame, label: str) -> None:
    """Predicted within-channel share of the starter vs his realised share of
    the team's QB carries in that game, by week and by whether he is new."""
    mm = mass.dropna(subset=["s_qb_pred"]).copy()
    c = cch[["game_id", "team", "player_id", "qb_rush"]]
    tot = c.groupby(["game_id", "team"])["qb_rush"].sum().rename("team_qbr")
    mine = c.rename(columns={"player_id": "starter_id", "qb_rush": "own_qbr"})
    mm = mm.merge(mine, on=["game_id", "team", "starter_id"], how="left").merge(tot, on=["game_id", "team"], how="left")
    mm["own_qbr"] = mm["own_qbr"].fillna(0)
    mm = mm[mm["team_qbr"] > 0]
    L += [f"### {label}: the starter's share WITHIN the QB-rush channel", "",
          "Predicted = his qb_rush share after blending and reallocation. Realised = his QB carries over "
          "the team's QB carries in that game.", "",
          "| population | team-games | predicted share | realised carry share |", "|---|---|---|---|"]
    for lab, g in (("all", mm), ("weeks 1-4", mm[mm["week"] <= 4]), ("weeks 5+", mm[mm["week"] > 4]),
                   ("new to his team as starter", mm[mm["new_starter"]]),
                   ("started for this team before", mm[~mm["new_starter"]])):
        if len(g):
            L.append(f"| {lab} | {len(g)} | {g['s_qb_pred'].mean():.3f} | "
                     f"{g['own_qbr'].sum() / g['team_qbr'].sum():.3f} |")
    L.append("")


def mix_by_margin(L: list, tg: pd.DataFrame, seasons) -> None:
    """Channel mix of offensive TDs by final margin -- and by the PRE-GAME
    spread, which is what a model can use."""
    t = tg[tg["season"].isin(seasons)].copy()
    opp = t[["game_id", "team", "points"]].rename(columns={"team": "opp", "points": "opp_pts"})
    t = t.merge(opp, on=["game_id", "opp"])
    t["margin"] = t["points"] - t["opp_pts"]
    ch = list(T.OFFENSIVE)
    L += [f"### {seasons}: where offensive TDs come from, by game state", "",
          "The 'final' rows are produced partly BY these touchdowns (goal-line rushing while leading "
          "widens the margin), so only the pre-game rows say what a model could know.", "",
          "| state | team-games | " + " | ".join(ch) + " |", "|---" * (len(ch) + 2) + "|"]
    rows = [("final: trailing or tied", t["margin"] <= 0), ("final: won by 1-16", t["margin"].between(1, 16)),
            ("final: won by 17+", t["margin"] >= 17)]
    if "spread" in t:
        # spread is from the team view in team_games: POSITIVE = favoured (sign check below)
        rows += [("pre-game: favourite by 3+", t["spread"] >= 3), ("pre-game: within 3", t["spread"].abs() < 3),
                 ("pre-game: underdog by 3+", t["spread"] <= -3)]
    for lab, m in rows:
        g = t[m]
        tot = g[ch].sum().sum()
        L.append(f"| {lab} | {len(g)} | " + " | ".join(f"{g[c].sum() / tot:.3f}" for c in ch) + " |")
    fav = t[t["spread"] >= 3]
    L += ["", f"Sign check on spread: favourites by 3+ average {fav['implied'].mean():.1f} implied points vs "
              f"{t.loc[t['spread'] <= -3, 'implied'].mean():.1f} for underdogs by 3+.", ""]


def league_drift(L: list, tg: pd.DataFrame) -> None:
    by = tg.groupby("season")[["qb_rush", "off_tds"]].sum()
    L += ["### League QB-rush fraction of offensive touchdowns, by season", "",
          "| season | QB-rush TDs | offensive TDs | fraction |", "|---|---|---|---|"]
    for s, r in by.iterrows():
        L.append(f"| {s} | {int(r['qb_rush'])} | {int(r['off_tds'])} | {r['qb_rush'] / r['off_tds']:.4f} |")
    L.append("")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seasons", default="2022,2023")
    ap.add_argument("--confirm", default="2024,2025")
    ap.add_argument("--out", default=str(Path(__file__).resolve().parent / "backtest_out"))
    a = ap.parse_args(argv)
    main_s = [int(x) for x in a.seasons.split(",")]
    conf = [int(x) for x in a.confirm.split(",")] if a.confirm else []
    allsz = main_s + conf
    D = B.load(sorted({x for s in allsz for x in (s, s - 1)}))
    win = V.V1["qb_window"]
    D["starts"] = B.load_starts(sorted({x for s in allsz for x in range(s - win, s + 1)}), D["qb_ids"])
    cfgs = list(dict.fromkeys([B.V10, B.SHIP]))
    L = ["# anytime_td_v1: share by team touchdown count, and the starting-QB level", "",
         f"Model: {B.cid(B.SHIP)} (td_v1.V1 as shipped). Finding on {main_s}; confirmation on {conf}. "
         "Team-games where the team scored at least one offensive touchdown.", ""]
    parts = [("finding", main_s)] + ([("confirmation", conf)] if conf else [])
    for tag, seasons in parts:
        d, m = B.run(D, seasons, cfgs)
        dp = prepare(d, D["tg"])
        L += [f"## {tag.title()}: {seasons}", ""]
        share_tables(L, dp, str(seasons))
        qb_tables(L, d[d["n_off"] > 0], m, str(seasons))
        starter_channel(L, m, D["cch"], str(seasons))
        mix_by_margin(L, D["tg"], seasons)
    league_drift(L, D["tg"])
    out = Path(a.out) / "td_diagnostics.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"wrote {out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
