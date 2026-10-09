"""Round 43 (reports/round43_own_rates.md): catch rate, yards per target and yards per carry from
the player's own last 10 games (long plays capped at his 90th percentile) against the shipped
league-anchored blend. Each single-rate arm is judged on its own market's conversion log loss;
the `all` arm is reported.

    python props/tools/round43_select.py <runs dir> [--out f.json]

<runs dir> holds backtest.py --conditional --save-results pickles named
r43_<arm>_s<seed>_<sel|con>.pkl: arm off / catch_rate / ypt / ypc / all, seed 0-3
(--audit-seed-offset), sel = 2022-24 weeks 2-18, con = 2026 weeks 2-4.

The four-seed rule (#202): each arm's Over chances are averaged over the four seeds per
player-game before scoring; per-seed gains are reported, and a gain under 0.3% of the shipped
log loss must be positive on every seed.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import grid_select as GS  # noqa: E402
import scoreboard as SB  # noqa: E402

SINGLE = {"catch_rate": "receptions", "ypt": "receiving yards", "ypc": "rushing yards"}
ARMS = ("off", "catch_rate", "ypt", "ypc", "all")
SEEDS = (0, 1, 2, 3)
SELECT, CONFIRM = [2022, 2023, 2024], [2026]
# the minimum Over move (#202: twice the seed noise, 3.6 points for ONE seed). On four-seed averages
# the noise halves (1/sqrt(4)): 1.8 for the yards markets; receptions are scored exactly (no seed
# noise), so the scoreboard's original 1.0-point "big enough to matter" applies (amended before any read)
MIN_MOVE = {"receptions": 1.0, "receiving yards": 1.8, "rushing yards": 1.8}
SMALL = 0.003            # a gain under 0.3% of the shipped log loss must hold on every seed
# family "efficiency source": 4 candidates read once on 2026 weeks 2-4; the ypc arm is also in the
# running-game family, already read four times there (reports/comparisons_ledger_2026.md)
CONFIRM_LEVEL = {"catch_rate": 1 - 0.05 / 4, "ypt": 1 - 0.05 / 4, "ypc": 1 - 0.05 / 6, "all": 1 - 0.05 / 4}
IRVING = "00-0039361"


def load(runs: Path, arm: str, seed: int) -> pd.DataFrame:
    parts = []
    for part in ("sel", "con"):
        f = runs / f"r43_{arm}_s{seed}_{part}.pkl"
        if not f.exists():
            raise FileNotFoundError(f"missing {f.name}: every arm needs seeds 0-3 on sel and con")
        d = pd.read_pickle(f)
        if not (isinstance(d, dict) and d.get("kind") == "harness"):
            raise ValueError(f"{f.name} is not a harness --save-results pickle")
        parts.append(d["results"])
    R = pd.concat(parts, ignore_index=True)
    got = set(R["own_rates"].unique()) if "own_rates" in R else {"(no stamp)"}
    if got != {arm}:
        raise ValueError(f"r43_{arm}_s{seed}: the rows say own_rates={sorted(got)}, not {arm}")
    if R.duplicated(SB.KEYS).any():
        raise ValueError(f"r43_{arm}_s{seed}: duplicate player-games (a season in both sel and con?)")
    return R


def seed_average(frames: list[pd.DataFrame]) -> pd.DataFrame:
    """One frame whose pc_* / pu_* chances are the mean over the seeds, per player-game. The seeds
    must agree on everything a seed cannot move: the rows, the lines, the outcomes."""
    base = frames[0].sort_values(SB.KEYS).reset_index(drop=True)
    pcols = [c for c in base.columns if c.startswith(("pc_", "pu_")) and c != "pc_rec_exact"]
    fixed = [c for c in base.columns if c.startswith("L_")] + [m[3] for m in SB.MARKETS.values() if m[3] in base]
    acc = base[pcols].to_numpy(float).copy()
    for F in frames[1:]:
        F = F.sort_values(SB.KEYS).reset_index(drop=True)
        if not F[SB.KEYS].equals(base[SB.KEYS]):
            raise ValueError("the seeds hold different player-games")
        for c in fixed:
            a, b = base[c].to_numpy(float), F[c].to_numpy(float)
            if not np.array_equal(a, b, equal_nan=True):
                raise ValueError(f"the seeds disagree on {c}: a seed moved a line or an outcome")
        acc += F[pcols].to_numpy(float)
    out = base.copy()
    out[pcols] = acc / len(frames)
    return out


def per_seed(raw: dict, arm: str, market: str, seasons) -> list[dict]:
    """raw: {(arm, seed): frame}, loaded once in main."""
    rows = []
    for s in SEEDS:
        a, r = raw[(arm, s)], raw[("off", s)]
        c = SB.compare(a[a.season.isin(seasons)], r[r.season.isin(seasons)], "game", reps=2000)[market]
        rows.append({"seed": s, "gain": c["logloss_c"]["gain"], "relative": c["logloss_c"]["relative"]})
    return rows


def role_of(F: pd.DataFrame) -> pd.Series:
    return F.slot.astype(str).str.replace(r"\d", "", regex=True)


def by_role(cand: pd.DataFrame, ref: pd.DataFrame, market: str, seasons) -> dict:
    out = {}
    c_, r_ = cand[cand.season.isin(seasons)], ref[ref.season.isin(seasons)]
    for role in ("RB", "WR", "TE"):
        a, b = c_[role_of(c_) == role], r_[role_of(r_) == role]
        if not len(SB.market_frame(b, market)):
            continue
        m = SB.compare(a, b, "game", reps=2000)[market]
        out[role] = {"n": m["n"], "gain": m["logloss_c"]["gain"], "ci": m["logloss_c"]["ci"],
                     "relative": m["logloss_c"]["relative"], "move_points": m["move_points_c"]}
    return out


def fallback_share(F: pd.DataFrame, market: str, seasons) -> dict:
    """How many scored player-games kept the blend (a thin window)."""
    d = SB.market_frame(F[F.season.isin(seasons)], market)
    col, need = ("own_n_ca", 40) if market == "rushing yards" else ("own_n_tg", 20)
    if col not in d:
        return {}
    return {"n": int(len(d)), "kept_blend": int((d[col].fillna(0) < need).sum())}


def irving(F_off: pd.DataFrame, F_arm: pd.DataFrame) -> list[dict]:
    """His 2026 rows: the arm's rates beside the shipped ones (the arm run carries both), the
    stand-in line, and the Over chance under each (the shipped arm's from the off run)."""
    cols = ["season", "week", "cr", "ypt", "cr_ship", "ypt_ship", "own_n_tg", "L_yds", "pc_yds", "act_rec_yards"]
    a = F_off[(F_off.gsis_id == IRVING) & (F_off.season == 2026)]
    b = F_arm[(F_arm.gsis_id == IRVING) & (F_arm.season == 2026)]
    m = b[[c for c in cols if c in b]].merge(a[["season", "week", "pc_yds"]], on=["season", "week"],
                                               suffixes=("", "_shipped"))
    return m.to_dict("records")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("runs")
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    runs = Path(a.runs)
    raw = {(arm, s): load(runs, arm, s) for arm in ARMS for s in SEEDS}
    avg = {arm: seed_average([raw[(arm, s)] for s in SEEDS]) for arm in ARMS}
    out = {"rule": "reports/round43_own_rates.md", "arms": {}}
    for arm, market in SINGLE.items():
        res = GS.run([{"own": "off"}, {"own": arm}], [avg["off"], avg[arm]], 0, market, "c", SELECT, CONFIRM,
                     ("own",), min_move=MIN_MOVE[market], reps=10_000)
        seeds = per_seed(raw, arm, market, SELECT)
        rel = (res.get("select_gain") or {}).get("relative")
        every_seed = (rel is None or abs(rel) >= SMALL or all(s["gain"] > 0 for s in seeds))
        con = SB.compare(avg[arm][avg[arm].season.isin(CONFIRM)], avg["off"][avg["off"].season.isin(CONFIRM)],
                         "game", level=CONFIRM_LEVEL[arm], reps=10_000)[market]
        out["arms"][arm] = {
            "market": market, "selection": res, "per_seed_select": seeds, "every_seed_ok": bool(every_seed),
            "confirm_family_interval": {"level": CONFIRM_LEVEL[arm], "logloss_c": con["logloss_c"]},
            "by_role_select": by_role(avg[arm], avg["off"], market, SELECT),
            "kept_blend_select": fallback_share(avg[arm], market, SELECT),
            "ship": bool(res.get("ship")) and bool(every_seed)}
    # the all arm: every bet market, both scores, reported (it ships only if all three single arms do)
    sel_c = SB.compare(avg["all"][avg["all"].season.isin(SELECT)], avg["off"][avg["off"].season.isin(SELECT)],
                       "game", reps=10_000)
    con_c = SB.compare(avg["all"][avg["all"].season.isin(CONFIRM)], avg["off"][avg["off"].season.isin(CONFIRM)],
                       "game", level=CONFIRM_LEVEL["all"], reps=10_000)
    pick = lambda c: {mk: {k: c[mk][k] for k in ("n", "logloss_c", "logloss_u", "move_points_c", "zone_c")
                           if k in c[mk]} for mk in c}
    out["arms"]["all"] = {"select": pick(sel_c), "confirm": pick(con_c),
                          "guards_select": {s: SB.guard_verdict(sel_c, None, s) for s in ("logloss_c", "logloss_u")}}
    shipped = [arm for arm in SINGLE if out["arms"][arm]["ship"]]
    out["final"] = shipped
    if len(shipped) == 3:
        out["final_guards"] = out["arms"]["all"]["guards_select"]
    elif len(shipped) == 2:
        out["final_note"] = (f"two rates ship ({', '.join(shipped)}): a four-seed run of exactly that set is "
                             "checked against the guards on 2022-24 before it ships (the rule)")
    out["irving_2026"] = {arm: irving(avg["off"], avg[arm]) for arm in ("ypt", "all")}
    txt = json.dumps(out, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o))
    print(txt)
    if a.out:
        Path(a.out).write_text(txt + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
