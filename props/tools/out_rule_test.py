"""Round 35 (reports/round35_out_rule.md): WHAT the Out rule hands on, and for how long.

For every absence game in the chosen seasons -- a 15%+ target (20%+ carry) player rostered
but not active while his team played -- each priced teammate's share in that game is
predicted the way the live scorer does it: his season-to-date share before the game, plus
the Out rule's handoff (score_game.OUT_RULE's x and y, apply_out_rule's arithmetic), and
scored against his actual share. Three versions of what is handed on:

  V0  the absent player's raw share LAST season (the live scorer; this-season share if none)
  V1  his share THIS season, in the games he played before this one (what OUT_RULE was tuned on)
  V2  V1 times the fraction of the teammate's season-to-date games the absent player played
      (only what is not already in the teammate's share)

Every absent key player's handoff in a game is summed for each teammate, as the live rule
applies every excluded player, and each teammate-game is scored once. Key players are chosen
on their share over the whole season, as absence_tune.py chose them (it uses games after
the absence too; the sample leans toward players whose role held or grew). "First game out"
means he played the team's previous game.

    python props/tools/out_rule_test.py --seasons 2022,2023,2024,2025 --select 2022,2023,2024 --confirm 2025
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "engine" / "scripts"))

KEY_THR = {"targets": 0.15, "carries": 0.20}
SHARE_COL = {"targets": "target_share", "carries": "rush_share"}
RULE_COL = {"targets": "ts", "carries": "rs"}
ELIG = 0.05
VARIANTS = ("V0", "V1", "V2")


def handoff(cur: np.ndarray, same: np.ndarray, f: float, x: float) -> np.ndarray:
    """apply_out_rule for one absent player: f = y x his share; x of it pro rata over every
    priced teammate, 1 - x pro rata over those at his position."""
    add = np.zeros_like(cur, dtype=float)
    base = np.clip(cur, 0, None)
    if f <= 0:
        return add
    if base.sum() > 0:
        add += x * f * base / base.sum()
    bs = np.where(same, base, 0.0)
    if bs.sum() > 0:
        add += (1 - x) * f * bs / bs.sum()
    return add


def game_rows(t: pd.DataFrame, ros: pd.DataFrame, prior_share: dict, kind: str) -> pd.DataFrame:
    """One row per (absence game, priced teammate). t: per (game, team, player) counts with
    team_n (absence_tune.season_frames); ros: the regular-season weekly roster;
    prior_share: {gsis_id: his raw share last season}."""
    pos = ros.drop_duplicates("gsis_id").set_index("gsis_id")["position"].replace({"FB": "RB"})
    st = ros[["week", "team", "gsis_id", "status"]]
    act = set(map(tuple, st.loc[st.status == "ACT", ["week", "team", "gsis_id"]].to_numpy()))
    rostered_out = set(map(tuple, st.loc[st.status != "ACT", ["week", "team", "gsis_id"]].to_numpy()))
    rows = []
    for team, tt in t.groupby("team"):
        games = tt[["game_id", "week", "team_n"]].drop_duplicates("game_id").sort_values("week")
        wk = dict(zip(games.game_id, games.week))
        tn = dict(zip(games.game_id, games.team_n))
        n = {(g, p): v for g, p, v in zip(tt.game_id, tt.player_id, tt.n)}
        players = set(tt.player_id)
        played = {p: [g for g in games.game_id if (g, p) in n] for p in players}
        key_share = {p: sum(n[(g, p)] for g in played[p]) / max(sum(tn[g] for g in played[p]), 1)
                     for p in players if played[p]}
        keys = [p for p, s in key_share.items() if s >= KEY_THR[kind] and pos.get(p) in ("RB", "WR", "TE")]
        for kid in keys:
            for g in games.game_id:
                w = wk[g]
                if (w, team, kid) not in rostered_out or (g, kid) in n:
                    continue
                before = [h for h in games.game_id if wk[h] < w]
                k_games = [h for h in before if (h, kid) in n]
                if not k_games:
                    continue                    # no this-season share yet: V1 / V2 undefined
                v1 = sum(n[(h, kid)] for h in k_games) / sum(tn[h] for h in k_games)
                v0 = prior_share.get(kid)
                v0 = v1 if v0 is None or not np.isfinite(v0) else float(v0)
                mates = []
                for j in players:                       # a teammate with no touch all season is never priced
                    if j == kid or (w, team, j) not in act:
                        continue
                    j_games = [h for h in before if (wk[h], team, j) in act]
                    den = sum(tn[h] for h in j_games)
                    if not j_games or den <= 0:
                        continue
                    cur = sum(n.get((h, j), 0) for h in j_games) / den
                    if cur < ELIG:
                        continue
                    with_k = sum(1 for h in j_games if (h, kid) in n) / len(j_games)
                    mates.append((j, cur, with_k, n.get((g, j), 0) / tn[g], pos.get(j) == pos.get(kid)))
                if not mates:
                    continue
                first = bool(before) and (before[-1], kid) in n     # he played the team's previous game
                for j, cur, with_k, actual, same in mates:
                    rows.append({"event": f"{team}_{kid}", "game_id": g, "week": w, "team": team, "absent": kid,
                                 "player_id": j, "cur": cur, "with_k": with_k, "same": same, "actual": actual,
                                 "v0": v0, "v1": v1, "first_out": first})
    return pd.DataFrame(rows)


def collapse(d: pd.DataFrame, variant: str, x: float, y: float) -> pd.DataFrame:
    """One row per (game, teammate): his season-to-date share, the SUM of every absent key
    player's handoff to him under the variant, the prediction and the actual share.
    Rows come out in a fixed order, so the variants line up row for row."""
    d = d if "season" in d else d.assign(season=0)
    add = np.zeros(len(d))
    for _, idx in d.groupby(["season", "game_id", "absent"]).indices.items():
        g = d.iloc[idx]
        k = g["v0"].iloc[0] if variant == "V0" else g["v1"].iloc[0]
        a_ = handoff(g["cur"].to_numpy(float), g["same"].to_numpy(bool), y * k, x)
        add[idx] = a_ * g["with_k"].to_numpy(float) if variant == "V2" else a_
    out = (d.assign(add=add)
             .groupby(["season", "team", "game_id", "player_id"], sort=True)
             .agg(week=("week", "first"), cur=("cur", "first"), actual=("actual", "first"),
                  add=("add", "sum"), first_out=("first_out", "all"), n_absent=("absent", "nunique"))
             .reset_index())
    out["pred"] = out["cur"] + out["add"]
    out["cluster"] = out["season"].astype(str) + "_" + out["team"].astype(str)
    return out


def predict(d: pd.DataFrame, variant: str, x: float, y: float) -> np.ndarray:
    """Each teammate-game's predicted share under a variant (collapse order)."""
    return collapse(d, variant, x, y)["pred"].to_numpy()


def losses(d: pd.DataFrame, x: float, y: float) -> tuple[pd.DataFrame, dict]:
    """(the teammate-game frame, {variant: squared errors in that frame's order})."""
    frames = {v: collapse(d, v, x, y) for v in VARIANTS}
    base = frames["V0"]
    return base, {v: (f["pred"] - f["actual"]).to_numpy() ** 2 for v, f in frames.items()}


def diff_ci(f: pd.DataFrame, a: np.ndarray, b: np.ndarray, reps=2000, seed=35) -> tuple[float, float, float]:
    """Mean of b - a (positive = a better) with a 95% interval resampling whole
    team-seasons (absences on one team share teammates and games)."""
    g = pd.DataFrame({"e": f["cluster"].to_numpy(), "x": b - a}).groupby("e")["x"]
    sm, c = g.sum().to_numpy(), g.size().to_numpy()
    idx = np.random.default_rng(seed).integers(0, len(sm), size=(reps, len(sm)))
    boot = sm[idx].sum(1) / c[idx].sum(1)
    return float((b - a).mean()), *(float(v) for v in np.percentile(boot, [2.5, 97.5]))


def pick_variant(mean_loss: dict, tie=0.005) -> str:
    """The lowest loss; V0 (shipped) kept within tie x its own loss."""
    best = min(mean_loss, key=mean_loss.get)
    return "V0" if mean_loss["V0"] - mean_loss[best] <= tie * mean_loss["V0"] else best


def verdict(sel: pd.DataFrame, conf: pd.DataFrame, x: float, y: float) -> dict:
    """The registered rule (reports/round35_out_rule.md), computed: pick on the selection
    seasons, detectable against V0 there, no worse than 5% of V0's loss in either the
    first-game-out or continuing part there, and not worse on the confirmation season."""
    fs, Ls = losses(sel, x, y)
    ms = {v: float(Ls[v].mean()) for v in VARIANTS}
    pick = pick_variant(ms)
    out = {"loss_select": ms, "pick": pick}
    if pick == "V0":
        return {**out, "ship": False, "why": "the shipped version is within 0.5% of the best"}
    m, lo, hi = diff_ci(fs, Ls[pick], Ls["V0"])
    parts = {}
    for nm, msk in (("first game out", fs.first_out.to_numpy()), ("continuing", ~fs.first_out.to_numpy())):
        if msk.any():
            worse = float((Ls[pick][msk] - Ls["V0"][msk]).mean())
            parts[nm] = {"n": int(msk.sum()), "worse_by": worse, "v0_loss": float(Ls["V0"][msk].mean()),
                         "ok": worse <= 0.05 * float(Ls["V0"][msk].mean())}
    fc, Lc = losses(conf, x, y)
    mc, loc, hic = diff_ci(fc, Lc[pick], Lc["V0"])
    ship = lo > 0 and all(p_["ok"] for p_ in parts.values()) and mc >= 0
    return {**out, "gain_select": [m, lo, hi], "parts": parts, "gain_confirm": [mc, loc, hic], "ship": bool(ship)}


def build(seasons, kind: str) -> pd.DataFrame:
    import absence_tune as AT
    import backtest as BT
    out = []
    for s in seasons:
        frames, ros = AT.season_frames(s)
        pdir = BT.priors_cache_dir()                  # the harness's priors, built by the current builder
        BT.ensure_priors(s - 1, pdir, True)
        pri = pd.read_csv(pdir / f"priors_{s - 1}_players.csv")
        prior = dict(zip(pri.gsis_id, pri[SHARE_COL[kind]]))
        out.append(game_rows(frames[kind], ros, prior, kind).assign(season=s))
    return pd.concat(out, ignore_index=True)


def main(argv=None):
    import score_game as SG
    ap = argparse.ArgumentParser()
    ap.add_argument("--seasons", default="2022,2023,2024,2025")
    ap.add_argument("--select", default="2022,2023,2024")
    ap.add_argument("--confirm", default="2025")
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    seasons = [int(v) for v in a.seasons.split(",")]
    sel, conf = [int(v) for v in a.select.split(",")], [int(v) for v in a.confirm.split(",")]
    res = {}
    for kind in ("targets", "carries"):
        x, y = SG.OUT_RULE[RULE_COL[kind]]
        d = build(seasons, kind)
        f_all, _ = losses(d, x, y)
        print(f"\n== {kind} (OUT_RULE x {x}, y {y}): {d.event.nunique()} absence events, "
              f"{f_all.game_id.nunique()} games, {len(f_all)} teammate-games "
              f"({int((f_all.n_absent > 1).sum())} with two or more key players out)")
        for lab, part in (("select " + a.select, d[d.season.isin(sel)]), ("confirm " + a.confirm, d[d.season.isin(conf)])):
            fr, L = losses(part, x, y)
            print(f"  {lab}: loss x1e4 " + ", ".join(f"{v} {1e4 * L[v].mean():.3f}" for v in VARIANTS))
            for v in ("V1", "V2"):
                m, lo, hi = diff_ci(fr, L[v], L["V0"])
                print(f"    {v} vs V0: gain x1e4 {1e4 * m:+.3f} ({1e4 * lo:+.3f}, {1e4 * hi:+.3f})")
                for nm, msk in (("first game out", fr.first_out.to_numpy()), ("continuing", ~fr.first_out.to_numpy())):
                    if msk.any():
                        mm, l2, h2 = diff_ci(fr[msk], L[v][msk], L["V0"][msk])
                        print(f"      {nm:15s} n {int(msk.sum()):5d}: {1e4 * mm:+.3f} ({1e4 * l2:+.3f}, {1e4 * h2:+.3f})"
                              f"  [V0 loss {1e4 * L['V0'][msk].mean():.3f}]")
        v_ = verdict(d[d.season.isin(sel)], d[d.season.isin(conf)], x, y)
        print(f"  VERDICT: pick {v_['pick']}, {'SHIPS' if v_['ship'] else 'does not ship'}"
              + (f" ({v_['why']})" if "why" in v_ else ""))
        oof = []
        for s_ in seasons:
            _, Lt = losses(d[d.season != s_], x, y)
            pk = pick_variant({v: float(Lt[v].mean()) for v in VARIANTS})
            _, Le = losses(d[d.season == s_], x, y)
            oof.append({"held_out": s_, "pick": pk, "gain": float((Le["V0"] - Le[pk]).mean())})
        print("  leave-one-season-out: " + "; ".join(f"{o['held_out']} pick {o['pick']} gain x1e4 {1e4 * o['gain']:+.3f}"
                                                    for o in oof))
        res[kind] = {"x": x, "y": y, "verdict": v_, "loso": oof}
    if a.out:
        Path(a.out).write_text(json.dumps(res, indent=1, default=float) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
