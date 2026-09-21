#!/usr/bin/env python3
"""Layer 2 backtest, and the end-to-end test against the engine's anytime model.

  python td_alloc_backtest.py [--tune 2022,2023] [--test 2024,2025] [--out DIR]
                               [--grid | --grid-v11] [--report NAME]

Population: every QB/RB/WR/TE on the GAME-DAY ACTIVE LIST (weekly-roster
status ACT, known before kickoff). Walk-forward throughout: a game is priced
from the prior season plus the current season's earlier weeks only, and
every setting is chosen on TUNE, frozen, then scored on TEST.

What is settled and carried in: five channels on raw opportunity counts
(expected-TD weighting was tested and dropped), reallocation of an absent
player's share across the active roster, and a slot prior for players with no
history -- which the engine has too, so both sides get it here.

What this run adds:

  - WHERE THE MASS GOES. The engine under-predicts the anytime scoring rate
    (0.135 vs 0.148). The direct diagnostic: the summed per-touchdown share
    of each team's actives under each model, against the fraction of the
    team's offensive touchdowns that actives actually scored.
  - A BETA-DISTRIBUTED SHARE. P(none) = (1 - s)^n on the mean share
    overstates P(score) for high-share players, because (1 - s)^n is convex
    and a player's share varies game to game. Concentration c tuned on TUNE.
  - A SCALED SLOT PRIOR. The full slot share runs 2.5x high on no-history
    players; the factor is tuned on TUNE.
  - The END-TO-END comparison against the anytime_td_v0 structure, with the
    cross terms that say which layer carries any difference.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import model as M  # noqa: E402
import td_alloc as A  # noqa: E402
import td_model as T  # noqa: E402
import td_v1 as V  # noqa: E402  -- the shipped model; this harness calls it, not a copy
from td_backtest import GAMES, NV, fetch  # noqa: E402

KAPPA = V.V1["kappa"]
MODE = V.V1["mode"]
MOVED = V.V1["moved"]
SKILL = V.SKILL
EPS = 1e-3
PASS_CH, RUSH_CH = ("pass_rz", "pass_far"), ("rush_in5", "rush_far", "qb_rush")
L1 = T.LAYER1                    # {"trials": 10, "gamma": 0.25, ...}

# A configuration is (alloc, c, cap, qb_beta); alloc = (prior, slot scale, moved weight).
BASE_ALLOC = ("none", 1.0, 0.5)                    # the spec before the slot prior
FULL_ALLOC = ("slot", 1.0, MOVED)
V1_ALLOC = ("slot", V.V1["slot_scale"], MOVED)
V10 = (V1_ALLOC, None, 0.99, None)                 # anytime_td_v1 as first shipped (props-v1.4)
SHIP = (V1_ALLOC, V.V1["c"], V.V1["cap"], V.V1["qb_beta"])   # what td_v1.V1 ships now
SCALES = [0.4, 0.6, 1.0]
C_GRID = [None, 80.0, 40.0, 20.0, 10.0, 5.0]
C_DIAG = [40.0, 20.0, 10.0]      # Beta concentrations shown beside the shipped share; never chosen by default
CAPS = [0.99, 0.993, 0.995, 0.997, 0.999]
QB_BETAS = [None, 10.0, 20.0, 40.0, 80.0]


def configs(mode: str) -> list:
    """ship: the shipped model and its references (td_v1.md). grid: slot scale
    x Beta c (td_layer2.md). grid-v11: share cap x the starter's QB-rush
    shrinkage (td_v1_1_tuning.md)."""
    if mode == "grid":
        return [(BASE_ALLOC, None, 0.99, None)] + [(("slot", sc, MOVED), c, 0.99, None)
                                                   for sc in SCALES for c in C_GRID]
    if mode == "grid-v11":
        return [(V1_ALLOC, None, cap, b) for cap in CAPS for b in QB_BETAS]
    out = [(BASE_ALLOC, None, 0.99, None), (FULL_ALLOC, None, 0.99, None), V10, SHIP]
    out += [(SHIP[0], c, SHIP[2], SHIP[3]) for c in C_DIAG]
    return list(dict.fromkeys(out))


def qid(qk) -> str:
    """Key of a per-touchdown share vector: (alloc, cap, qb_beta)."""
    (p, sc, m), cap, b = qk
    return f"{p}|x{sc:g}|m{m:g}|cap{cap:g}|qb{'team' if b is None else f'{b:g}'}"


def cid(cfg) -> str:
    al, c, cap, b = cfg
    return f"{qid((al, cap, b))}|c{'inf' if c is None else f'{c:g}'}"


def _kick_lookup(games: pd.DataFrame) -> dict:
    """(team, week) -> kickoff in UTC, for picking the pre-game depth chart."""
    out = {}
    for _, r in games.dropna(subset=["gametime"]).iterrows():
        naive = pd.Timestamp(f"{r['gameday']} {r['gametime']}")
        off = 4 if pd.Timestamp(f"{naive.year}-03-15") <= naive < pd.Timestamp(f"{naive.year}-11-01") else 5
        kt = (naive + pd.Timedelta(hours=off)).tz_localize("UTC")
        out[(r["home_team"], r["week"])] = kt
        out[(r["away_team"], r["week"])] = kt
    return out


def load(seasons: list[int]) -> dict:
    players = pd.read_csv(fetch(f"{NV}/players/players.csv", "players.csv"),
                          usecols=["gsis_id", "pfr_id", "position"], low_memory=False)
    qb_ids = set(players.loc[players["position"] == "QB", "gsis_id"].dropna())
    pfr = players.dropna(subset=["pfr_id", "gsis_id"]).drop_duplicates("pfr_id").set_index("pfr_id")["gsis_id"]
    sched = pd.read_csv(fetch(GAMES, "games.csv"), low_memory=False)

    opps, sc, tds, played, active, slots, fin = [], [], [], [], [], [], {}
    for s in seasons:
        pbp = pd.read_csv(fetch(f"{NV}/pbp/play_by_play_{s}.csv.gz", f"pbp_{s}.csv.gz"),
                          usecols=A.PBP_COLS_L2, low_memory=False)
        opps.append(A.opportunities(pbp, qb_ids))
        sc.append(A.scorers(pbp, qb_ids))
        tds.append(T.classify_tds(pbp, qb_ids))
        td = pbp[(pbp["season_type"] == "REG") & (pbp["touchdown"] == 1) & (pbp["td_team"] == pbp["posteam"])]
        fin[s] = {"pass": float((td.loc[td["pass_touchdown"] == 1, "yardline_100"] <= 10).mean()),
                  "rush": float((td.loc[td["rush_touchdown"] == 1, "yardline_100"] <= 10).mean())}
        snaps = pd.read_csv(fetch(f"{NV}/snap_counts/snap_counts_{s}.csv", f"snap_counts_{s}.csv"),
                            low_memory=False)
        snaps = snaps[(snaps["game_type"] == "REG") & (snaps["offense_snaps"] > 0)
                      & snaps["position"].isin(SKILL)]
        played.append(pd.DataFrame({
            "season": snaps["season"], "week": snaps["week"], "game_id": snaps["game_id"],
            "team": T._norm_team(snaps["team"]), "player_id": snaps["pfr_player_id"].map(pfr),
            "pos": snaps["position"].map(SKILL)}))
        # the game-day active list -- pre-game information, unlike snaps
        ros = pd.read_csv(fetch(f"{NV}/weekly_rosters/roster_weekly_{s}.csv",
                                f"roster_weekly_{s}.csv"), low_memory=False)
        ros = ros[(ros["game_type"] == "REG") & (ros["status"] == "ACT")
                  & ros["position"].isin(SKILL) & ros["gsis_id"].notna()]
        active.append(pd.DataFrame({"season": ros["season"], "week": ros["week"],
                                    "team": T._norm_team(ros["team"]),
                                    "player_id": ros["gsis_id"], "pos": ros["position"].map(SKILL)}))
        # the pre-game depth chart: the engine's slot, and its no-history prior
        dc = pd.read_csv(fetch(f"{NV}/depth_charts/depth_charts_{s}.csv", f"dc_{s}.csv"), low_memory=False)
        g = sched[(sched["season"] == s) & (sched["game_type"] == "REG")]
        roles = M.normalize_depth_charts(dc, _kick_lookup(g))
        slots.append(pd.DataFrame({"season": s, "week": roles["week"].astype(int),
                                   "team": T._norm_team(roles["team"]),
                                   "player_id": roles["gsis_id"], "slot": roles["slot"]}))

    opps = pd.concat(opps, ignore_index=True)
    played = pd.concat(played, ignore_index=True)
    unmapped = int(played["player_id"].isna().sum())
    played = played.dropna(subset=["player_id"]).drop_duplicates(["game_id", "player_id"])
    slots = pd.concat(slots, ignore_index=True).drop_duplicates(["season", "week", "team", "player_id"])
    tg = T.team_games(sched[sched["season"].isin(seasons)], pd.concat(tds, ignore_index=True))

    pbp_teams = set(opps["team"].unique())
    for name, frame in (("snap counts", played), ("depth charts", slots)):
        if set(frame["team"]) - pbp_teams:
            raise SystemExit(f"team codes in {name} not in play-by-play: {sorted(set(frame['team']) - pbp_teams)}")
    active = pd.concat(active, ignore_index=True).drop_duplicates(["season", "week", "player_id"])
    active = active.merge(tg[["season", "week", "team", "game_id"]], on=["season", "week", "team"], how="inner")
    active = active.merge(slots, on=["season", "week", "team", "player_id"], how="left")
    both = played.merge(active[["game_id", "player_id"]], on=["game_id", "player_id"], how="left", indicator=True)
    cover = float((both["_merge"] == "both").mean())
    if cover < 0.95:
        raise SystemExit(f"only {cover:.1%} of players with a snap are on the active list")
    sc = pd.concat(sc, ignore_index=True)
    return {"qb_ids": qb_ids, "cch": A.counts(opps, "channel"), "ceng": A.counts(opps, "engine"),
            "sc": sc, "scored_n": sc.groupby(["game_id", "player_id"])["tds"].sum().to_dict(),
            "played": played, "active": active, "slots": slots, "tg": tg, "fin": fin,
            "unmapped": unmapped, "cover": cover, "slot_cover": float(active["slot"].notna().mean())}


def load_starts(seasons, qb_ids: set[str]) -> pd.DataFrame:
    """Starting quarterbacks and their QB-rush touchdowns, for the starter's
    career rate (td_v1.qb_starts) -- over `qb_window` seasons before the
    earliest priced season as well, so week 1 has a history."""
    out = []
    for s in seasons:
        pbp = pd.read_csv(fetch(f"{NV}/pbp/play_by_play_{s}.csv.gz", f"pbp_{s}.csv.gz"),
                          usecols=A.PBP_COLS_L2, low_memory=False)
        out.append(V.qb_starts(pbp, qb_ids))
    return pd.concat(out, ignore_index=True)


def run(D: dict, seasons: list[int], cfgs: list) -> tuple[pd.DataFrame, pd.DataFrame]:
    """(player rows, team-game mass rows). Every rebuild number here comes out
    of td_v1 -- the module score_game.py calls -- so what is validated is
    what ships. Only the ENGINE reproduction has its own code, because it
    models the other system."""
    cch, ceng, played, active, slots, tg = D["cch"], D["ceng"], D["played"], D["active"], D["slots"], D["tg"]
    scored_n = D["scored_n"]
    allocs = list(dict.fromkeys(cfg[0] for cfg in cfgs))
    qkeys = list(dict.fromkeys((cfg[0], cfg[2], cfg[3]) for cfg in cfgs))
    rows, mass = [], []
    for s in seasons:
        pl_pri = played[played["season"] == s - 1]
        sl_pri = slots[slots["season"] == s - 1]
        f = D["fin"][s - 1]
        pri_c, pri_e = cch[cch["season"] == s - 1], ceng[ceng["season"] == s - 1]
        pg_e = V.per_game(pri_e, A.ENGINE_CHANNELS)
        sp_e = A.slot_prior(pri_e, pl_pri, sl_pri, A.ENGINE_CHANNELS)
        for w in sorted(tg.loc[tg["season"] == s, "week"].unique()):
            cur = lambda d: d[(d["season"] == s) & (d["week"] < w)]  # noqa: E731
            pl_cur = cur(played)
            now = active[(active["season"] == s) & (active["week"] == w)]
            both = pd.concat([pl_pri, pl_cur, now])
            pos = dict(zip(both["player_id"], both["pos"]))
            team_now = dict(zip(now["player_id"], now["team"]))
            hist = tg[(tg["season"] == s - 1) | ((tg["season"] == s) & (tg["week"] < w))]
            qh = V.qb_history(D["starts"], s, w)
            ctx = V.context(hist, qb_hist=qh)
            started_here = set(zip(qh["player_id"], qh["team"]))
            mix_team, mix_league, ratio_off = ctx["mix_team"], ctx["mix_league"], ctx["ratio_off"]

            # engine: counts, its own half-weight convention, the slot prior it has
            sh_e = A.fill_no_history(
                A.blended_shares(cur(ceng), pri_e, pl_cur, pl_pri, A.ENGINE_CHANNELS, KAPPA, pg_e,
                                 current_team=team_now, moved_weight=0.5),
                now, sp_e, A.ENGINE_CHANNELS)
            filled, raw = {}, {}
            for al in allocs:
                filled[al], raw[al[2]] = V.week_shares(cur(cch), pri_c, pl_cur, pl_pri, sl_pri, now,
                                                       moved=al[2], slot_scale=al[1],
                                                       prior=al[0] == "slot")

            for _, g in tg[(tg["season"] == s) & (tg["week"] == w)].iterrows():
                act = now[(now["game_id"] == g["game_id"]) & (now["team"] == g["team"])]
                if act.empty:
                    continue
                ids = list(act["player_id"])
                qb = V.starter(act)
                new_qb = qb is not None and (qb, g["team"]) not in started_here
                mix = mix_team.loc[g["team"]] if g["team"] in mix_team.index else mix_league
                n_off = int(g["off_tds"])
                mu_eng = g["implied"] * ratio_off
                pmf_new = V.team_pmf(g["implied"], ctx)
                pmf_eng = T.count_pmf([mu_eng])[0]

                e = A.reallocate(A.candidates(sh_e, g["team"], A.ENGINE_CHANNELS), set(ids), pos,
                                 A.ENGINE_CHANNELS, "none").reindex(ids).fillna(0)
                s_pass = f["pass"] * e["tgt_i10"] + (1 - f["pass"]) * e["tgt_all"]
                s_rush = f["rush"] * e["car_i10"] + (1 - f["rush"]) * e["car_all"]
                prm = pd.Series({"pass": mix[list(PASS_CH)].sum(), "rush": mix[list(RUSH_CH)].sum()})
                q_eng = ((prm["pass"] * s_pass + prm["rush"] * s_rush) / prm.sum()).clip(upper=0.999)
                eng_n = A.p_score_given(q_eng.to_numpy(), n_off)
                eng_e2e = 1 - np.exp(-mu_eng * q_eng.to_numpy())
                l1_engalloc = A.p_score_dist(q_eng.to_numpy(), pmf_new)

                # no history = active but absent from the history-based shares;
                # the same set for both models, which share the played history
                nohist_ids = [p for p in ids if p not in raw[MOVED].index]
                act_tds = sum(scored_n.get((g["game_id"], p), 0) for p in ids)
                mrow = {"season": s, "week": w, "game_id": g["game_id"], "team": g["team"],
                        "n_off": n_off, "actives_scored": act_tds, "sum_q_engine": float(q_eng.sum()),
                        "nohist_q_engine": float(q_eng[nohist_ids].sum()),
                        "qb_rush_tds": int(g["qb_rush"]), "qb_league": ctx["qb_league"],
                        "starter_id": qb, "new_starter": bool(new_qb)}
                # td_v1.game_q is per_td(game_shares, game_mix); split here only so the
                # reallocation is not repeated for every quarterback setting
                qs, by_cap = {}, {}
                for qk in qkeys:
                    al, cap, b = qk
                    if (al, cap) not in by_cap:
                        by_cap[(al, cap)] = V.game_shares(filled[al], g["team"], ids, pos, MODE, cap)
                    mix_k = V.game_mix(ctx, g["team"], qb, b)
                    qs[qk] = V.per_td(by_cap[(al, cap)], mix_k).clip(upper=0.999)
                    mrow[f"wqb|{qid(qk)}"] = float(mix_k["qb_rush"])
                    if qk == (SHIP[0], SHIP[2], SHIP[3]) and qb is not None:
                        mrow["s_qb_pred"] = float(by_cap[(al, cap)].loc[qb, "qb_rush"])
                    mrow[f"sum_q|{qid(qk)}"] = float(qs[qk].sum())
                    mrow[f"nohist_q|{qid(qk)}"] = float(qs[qk][nohist_ids].sum())
                mass.append(mrow)

                base = {"season": s, "week": w, "game_id": g["game_id"], "team": g["team"]}
                cols = {}
                for cfg in cfgs:
                    q = qs[(cfg[0], cfg[2], cfg[3])].to_numpy()
                    k, c = cid(cfg), cfg[1]
                    cols[f"q|{qid((cfg[0], cfg[2], cfg[3]))}"] = q
                    cols[f"n|{k}"] = A.p_score_given(q, n_off, c)
                    cols[f"e2e|{k}"] = A.p_score_dist(q, pmf_new, c)
                    cols[f"engl2|{k}"] = A.p_score_dist(q, pmf_eng, c)
                nh_set = set(nohist_ids)
                for i, pid in enumerate(ids):
                    r = {**base, "player_id": pid, "pos": pos.get(pid), "no_history": pid in nh_set,
                         "starter": pid == qb, "new_starter": pid == qb and new_qb,
                         "scored": int(scored_n.get((g["game_id"], pid), 0) > 0),
                         "tds": int(scored_n.get((g["game_id"], pid), 0)), "n_off": n_off,
                         "eng_n": float(eng_n[i]), "eng_e2e": float(eng_e2e[i]),
                         "l1_engalloc": float(l1_engalloc[i])}
                    for key, arr in cols.items():
                        r[key] = float(arr[i])
                    rows.append(r)
    return pd.DataFrame(rows), pd.DataFrame(mass)


def logloss(p, y):
    p = np.clip(np.asarray(p, float), EPS, 1 - EPS)
    y = np.asarray(y, float)
    return -(y * np.log(p) + (1 - y) * np.log(1 - p))


def ll(d, col):
    return float(logloss(d[col], d["scored"]).mean())


def boot(d: pd.DataFrame, a: str, b: str, reps=2000, seed=5):
    x = pd.DataFrame({"g": d["game_id"].to_numpy(),
                      "v": logloss(d[a], d["scored"]) - logloss(d[b], d["scored"])}).groupby("g")["v"]
    sums, cnt = x.sum().to_numpy(), x.size().to_numpy()
    idx = np.random.default_rng(seed).integers(0, len(sums), size=(reps, len(sums)))
    bs = sums[idx].sum(1) / cnt[idx].sum(1)
    return float(sums.sum() / cnt.sum()), *np.percentile(bs, [2.5, 97.5]).tolist()


def _ci(x):
    v = "better" if x[2] < 0 else ("worse" if x[1] > 0 else "not established")
    return f"{x[0]:+.4f} ({x[1]:+.4f}, {x[2]:+.4f}) {v}"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tune", default="2022,2023")
    ap.add_argument("--test", default="2024,2025")
    ap.add_argument("--out", default=str(Path(__file__).resolve().parent / "backtest_out"))
    ap.add_argument("--grid", action="store_true",
                    help="reproduce the layer-2 tuning run (slot scale x Beta concentration)")
    ap.add_argument("--grid-v11", action="store_true",
                    help="tune the share cap x the starter's QB-rush shrinkage")
    ap.add_argument("--report", default=None, help="report file name (default by mode)")
    a = ap.parse_args(argv)
    mode = "grid" if a.grid else ("grid-v11" if a.grid_v11 else "ship")
    cfgs = configs(mode)
    tune = [int(x) for x in a.tune.split(",")]
    test = [int(x) for x in a.test.split(",")]
    # every scored season needs its prior season (a test window need not follow tune)
    seasons = sorted({x for s in tune + test for x in (s, s - 1)})
    D = load(seasons)
    win = V.V1["qb_window"]
    D["starts"] = load_starts(sorted({x for s in tune + test for x in range(s - win, s + 1)}), D["qb_ids"])
    print(f"loaded: active list covers {D['cover']:.1%} of snaps; {D['slot_cover']:.1%} of actives "
          f"hold a depth-chart slot", file=sys.stderr)
    dtu, _mtu = run(D, tune, cfgs)
    dte, mte = run(D, test, cfgs)
    tune_ll = {cfg: ll(dtu, f"n|{cid(cfg)}") for cfg in cfgs}
    out = Path(a.out)
    if mode == "grid-v11":
        best = min(tune_ll, key=tune_ll.get)
        write_v11(out / (a.report or "td_v1_1_tuning.md"), D, dtu, dte, mte, tune_ll, best, tune, test)
        return 0
    # the grid CHOOSES; the default run scores what td_v1 ships, unchosen
    best = min(tune_ll, key=tune_ll.get) if mode == "grid" else SHIP
    name = a.report or ("td_layer2.md" if mode == "grid" else "td_v1.md")
    write(out / name, D, dte, mte, tune_ll, best, tune, test, shipped=mode == "ship")
    return 0


def _calib(L, d, cols, labels, bins=(0, .05, .10, .20, .30, .45, .60, 1.0)):
    """Calibration by the bins of the LAST column, with every column's mean."""
    L += ["| predicted P(score) | " + " | ".join(f"{l}: predicted" for l in labels) + " | actual rate | n |",
          "|---" * (len(cols) + 3) + "|"]
    for b, g in d.assign(_b=pd.cut(d[cols[-1]], list(bins), include_lowest=True)).groupby("_b", observed=True):
        L.append(f"| {b} | " + " | ".join(f"{g[c].mean():.3f}" for c in cols)
                 + f" | {g['scored'].mean():.3f} | {len(g)} |")


def _fixed(cfg):
    return (cfg[0], None, cfg[2], cfg[3])


def _qb_rows(L, d, pairs):
    """Starting quarterbacks, and those starting for a team they had not
    started for in the window -- the Willis case."""
    L += ["| population | n | actual rate | " + " | ".join(f"{lab}: predicted / log loss" for lab, _ in pairs)
          + " |", "|---" * (len(pairs) + 3) + "|"]
    for name, g in (("all starting QBs", d[d["starter"]]), ("QB new to his team as a starter", d[d["new_starter"]])):
        if len(g):
            L.append(f"| {name} | {len(g)} | {g['scored'].mean():.3f} | "
                     + " | ".join(f"{g[c].mean():.3f} / {ll(g, c):.4f}" for _, c in pairs) + " |")


def write(path: Path, D, d, mass, tune_ll, best, tune, test, shipped=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    prev = (FULL_ALLOC, None, 0.99, None)          # the previous best: full slot prior, fixed share
    base = (BASE_ALLOC, None, 0.99, None)
    best_fixed = _fixed(best)
    kb, kp, kbase, kbf = cid(best), cid(prev), cid(base), cid(best_fixed)
    L = [("# anytime_td_v1: layer 2 and the end-to-end test" if shipped else
          "# Layer 2 and the end-to-end test"), "",
         f"Tune {tune}, test {test}. Population: QB/RB/WR/TE on the game-day active list, {len(d)} "
         f"player-games in test, {d['scored'].mean():.1%} of whom scored. Active list covers "
         f"{D['cover']:.1%} of snaps; {D['slot_cover']:.1%} of actives hold a depth-chart slot. "
         f"Five channels on raw counts; reallocation '{MODE}'; kappa {KAPPA:g}; moved-role weight "
         f"{MOVED:g}. The engine gets the slot prior it has in production.", "",
         (f"**Shipped configuration, scored as-is: {kb}** -- the parameters in td_v1.V1, which "
          "score_game.py calls. Every rebuild number below comes out of that module." if shipped else
          f"Chosen on tune: **{kb}** (slot-prior scale x, Beta concentration c)."), "",
         "## Where the touchdown mass goes (test, per team-game)", "",
         "Summed per-touchdown share of the team's ACTIVE players, against the fraction of the team's "
         "offensive touchdowns that active players actually scored. Anything below the actual line is "
         "probability the model never gives to anyone who plays.", ""]
    mm = mass[mass["n_off"] > 0]
    actual = mm["actives_scored"].sum() / mm["n_off"].sum()
    mk = lambda cfg: qid((cfg[0], cfg[2], cfg[3]))  # noqa: E731
    L += ["| | summed share of actives | of which: players with no history |", "|---|---|---|",
          f"| actual: fraction of offensive TDs scored by actives | **{actual:.3f}** | |",
          f"| engine | {mass['sum_q_engine'].mean():.3f} | {mass['nohist_q_engine'].mean():.3f} |",
          f"| layer 2, no prior (previous spec) | {mass['sum_q|' + mk(base)].mean():.3f} | "
          f"{mass['nohist_q|' + mk(base)].mean():.3f} |",
          f"| layer 2, full slot prior | {mass['sum_q|' + mk(prev)].mean():.3f} | "
          f"{mass['nohist_q|' + mk(prev)].mean():.3f} |"]
    if shipped and V10 != best_fixed:
        L.append(f"| anytime_td_v1 as first shipped (props-v1.4) | {mass['sum_q|' + mk(V10)].mean():.3f} | "
                 f"{mass['nohist_q|' + mk(V10)].mean():.3f} |")
    L += [f"| {'shipped' if shipped else 'chosen'} | {mass['sum_q|' + mk(best)].mean():.3f} | "
          f"{mass['nohist_q|' + mk(best)].mean():.3f} |", ""]

    L += ["## Allocation, given the team's offensive touchdowns (test)", "",
          "| model | log loss | vs | change (95% CI, game-clustered) |", "|---|---|---|---|",
          f"| Engine (pass/rush, inside-10, slot prior) | {ll(d, 'eng_n'):.4f} | | baseline |",
          f"| previous spec: no prior, fixed share | {ll(d, 'n|' + kbase):.4f} | engine | {_ci(boot(d, 'n|' + kbase, 'eng_n'))} |",
          f"| full slot prior, fixed share | {ll(d, 'n|' + kp):.4f} | previous spec | {_ci(boot(d, 'n|' + kp, 'n|' + kbase))} |"]
    if shipped and V10 != best_fixed:
        k10 = cid(V10)
        L += [f"| v1 as first shipped (slot x{V10[0][1]:g}) | {ll(d, 'n|' + k10):.4f} | full slot prior | "
              f"{_ci(boot(d, 'n|' + k10, 'n|' + kp))} |",
              f"| shipped | {ll(d, 'n|' + kbf):.4f} | v1 as first shipped | {_ci(boot(d, 'n|' + kbf, 'n|' + k10))} |"]
    else:
        L.append(f"| chosen slot scale, fixed share | {ll(d, 'n|' + kbf):.4f} | full slot prior | "
                 f"{_ci(boot(d, 'n|' + kbf, 'n|' + kp))} |")
    if best != best_fixed:   # only the grid can choose a Beta share
        L.append(f"| + Beta share (chosen: {kb}) | {ll(d, 'n|' + kb):.4f} | fixed share | "
                 f"{_ci(boot(d, 'n|' + kb, 'n|' + kbf))} |")
    L += ["", f"{'Shipped' if shipped else 'Chosen'} vs engine directly: "
              f"{_ci(boot(d, 'n|' + kb, 'eng_n'))}.", "",
          "### Calibration given offensive touchdowns", ""]
    _calib(L, d, ["n|" + kp, "n|" + kb], ["full slot, fixed share", "shipped" if shipped else "chosen"])
    nh = d[d["no_history"]]
    L += ["", "### No-history players", "",
          "| model | mean predicted | actual rate | n |", "|---|---|---|---|",
          f"| engine (full slot prior) | {nh['eng_n'].mean():.3f} | {nh['scored'].mean():.3f} | {len(nh)} |",
          f"| layer 2, full slot prior | {nh['n|' + kp].mean():.3f} | {nh['scored'].mean():.3f} | {len(nh)} |",
          f"| layer 2, {'shipped' if shipped else 'chosen'} | {nh['n|' + kb].mean():.3f} | "
          f"{nh['scored'].mean():.3f} | {len(nh)} |", ""]

    e, r = "eng_e2e", "e2e|" + kb
    L += ["## END TO END: what would be deployed (test)", "",
          "Engine = implied points x league offensive TDs/point, linear, Poisson; per-TD share from "
          "pass/rush + inside-10 usage with the slot prior: the structure of anytime_td_v0. "
          f"v1 = layer 1 frozen (Binomial({L1['trials']}), gamma {L1['gamma']}) x layer 2 ({kb}).", "",
          "| model | log loss | Brier | mean predicted | vs engine (95% CI, game-clustered) |",
          "|---|---|---|---|---|",
          f"| Engine (anytime_td_v0 structure) | {ll(d, e):.4f} | {((d[e] - d['scored']) ** 2).mean():.4f} | "
          f"{d[e].mean():.3f} | baseline |"]
    if shipped and V10 != best:
        r10 = "e2e|" + cid(V10)
        L.append(f"| v1 as first shipped (props-v1.4) | {ll(d, r10):.4f} | {((d[r10] - d['scored']) ** 2).mean():.4f} | "
                 f"{d[r10].mean():.3f} | {_ci(boot(d, r10, e))} |")
    L += [f"| {'v1 shipped' if shipped else 'v1'} | {ll(d, r):.4f} | {((d[r] - d['scored']) ** 2).mean():.4f} | "
          f"{d[r].mean():.3f} | {_ci(boot(d, r, e))} |", ""]
    if shipped and V10 != best:
        L += [f"Shipped vs v1 as first shipped: {_ci(boot(d, r, 'e2e|' + cid(V10)))}.", ""]
    L += [f"Actual scoring rate {d['scored'].mean():.3f}.", "",
          "Cross terms -- each layer alone, the other as the engine has it:", "",
          "| model | log loss | mean predicted | vs engine |", "|---|---|---|---|",
          f"| layer 1 frozen, engine allocation | {ll(d, 'l1_engalloc'):.4f} | {d['l1_engalloc'].mean():.3f} | "
          f"{_ci(boot(d, 'l1_engalloc', e))} |",
          f"| engine count model, v1 allocation | {ll(d, 'engl2|' + kb):.4f} | {d['engl2|' + kb].mean():.3f} | "
          f"{_ci(boot(d, 'engl2|' + kb, e))} |", "",
          "### Calibration, end to end", ""]
    _calib(L, d, [e, r], ["engine", "v1"])
    L += ["", "The 0.2-0.3 band is where most priced anytime lines sit.", "",
          "| position | engine | v1 | n |", "|---|---|---|---|"]
    for p, g in d.groupby("pos"):
        L.append(f"| {p} | {ll(g, e):.4f} | {ll(g, r):.4f} | {len(g)} |")

    if shipped:
        pairs = [("engine", "eng_e2e")] + ([("v1 as first shipped", "e2e|" + cid(V10))] if V10 != best else []) \
            + [("shipped", r)]
        L += ["", "### Starting quarterbacks, end to end", ""]
        _qb_rows(L, d, pairs)
        L += ["", "## The Beta share on the top bins (diagnostic, not used)", "",
              "A concentration tuned on aggregate log loss can return 'no effect' even if it fixes the top "
              "bins, which are 7% of rows. Rows are binned by the SHIPPED fixed-share prediction, so every "
              "column describes the same players. c -> infinity is the fixed share.", ""]
        diag = [(best[0], c, best[2], best[3]) for c in C_DIAG]
        for tag, pre in (("End to end", "e2e|"), ("Given the team's offensive touchdowns", "n|")):
            L += [f"### {tag}", ""]
            _calib(L, d, [pre + cid(x) for x in diag] + [pre + kbf],
                   [f"c={x[1]:g}" for x in diag] + ["fixed share"])
            L.append("")
        top = d[d["e2e|" + kbf] > 0.45]
        L += ["| share | log loss, all | log loss, rows priced above 0.45 end to end | mean predicted there |",
              "|---|---|---|---|"]
        for x in diag + [best_fixed]:
            k = "e2e|" + cid(x)
            L.append(f"| {'fixed' if x[1] is None else f'c={x[1]:g}'} | {ll(d, k):.4f} | {ll(top, k):.4f} | "
                     f"{top[k].mean():.3f} |")
        L.append(f"| actual | | | {top['scored'].mean():.3f} (n {len(top)}) |")

    L += ["", "## Tuning (tune log loss, given offensive touchdowns)", "",
          "| configuration | tune log loss |", "|---|---|"]
    for k, v in sorted(tune_ll.items(), key=lambda kv: kv[1]):
        L.append(f"| {cid(k)} | {v:.4f}{' **chosen**' if k == best and not shipped else ''} |")
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"wrote {path}", file=sys.stderr)


def write_v11(path: Path, D, dtu, dte, mass, tune_ll, best, tune, test):
    """The cap x starter-QB-rush tuning run: chosen on tune, scored on test."""
    path.parent.mkdir(parents=True, exist_ok=True)
    kb, k10 = cid(best), cid(V10)
    cap_only = cid((V1_ALLOC, None, best[2], None))
    qb_only = cid((V1_ALLOC, None, 0.99, best[3]))
    fmt_b = lambda b: "team mix" if b is None else f"{b:g}"  # noqa: E731
    L = ["# anytime_td_v1.1: the share cap and the starter's QB-rush rate", "",
         f"Tune {tune}, test {test}. Everything else is anytime_td_v1 as shipped in props-v1.4 "
         f"(slot x{V1_ALLOC[1]:g}, moved {MOVED:g}, fixed share, Binomial({L1['trials']}), gamma {L1['gamma']}). "
         f"Two settings, chosen together on tune log loss given the team's offensive touchdowns:", "",
         "- **cap**: total share per channel after reallocation; the remainder is 'other'. v1 used 0.99; "
         "actives score 0.997 of offensive touchdowns.",
         f"- **QB rate**: the qb_rush weight in the channel mix. 'team mix' is v1 (the team's history); a "
         f"number is the starter's QB-rush touchdowns over his teams' offensive touchdowns in his starts over "
         f"the last {V.V1['qb_window']} seasons, shrunk toward the league fraction by that many team touchdowns.", "",
         "## Tune log loss, given offensive touchdowns", "",
         "| cap | " + " | ".join(fmt_b(b) for b in QB_BETAS) + " |", "|---" * (len(QB_BETAS) + 1) + "|"]
    for cap in CAPS:
        cells = []
        for b in QB_BETAS:
            cfg = (V1_ALLOC, None, cap, b)
            cells.append(f"**{tune_ll[cfg]:.5f}**" if cfg == best else f"{tune_ll[cfg]:.5f}")
        L.append(f"| {cap:g} | " + " | ".join(cells) + " |")
    L += ["", f"Chosen: **cap {best[2]:g}, QB rate {fmt_b(best[3])}**.", "",
          "Starting quarterbacks only, tune log loss given offensive touchdowns:", "",
          "| cap | " + " | ".join(fmt_b(b) for b in QB_BETAS) + " |", "|---" * (len(QB_BETAS) + 1) + "|"]
    st = dtu[dtu["starter"]]
    for cap in CAPS:
        L.append(f"| {cap:g} | " + " | ".join(f"{ll(st, 'n|' + cid((V1_ALLOC, None, cap, b))):.4f}"
                                              for b in QB_BETAS) + " |")

    d = dte
    L += ["", "## Test", "",
          f"{len(d)} player-games, {d['scored'].mean():.3f} scored.", "",
          "| model | given offensive TDs | vs v1 | end to end | vs v1 | mean predicted, end to end |",
          "|---|---|---|---|---|---|"]
    for lab, k in (("v1 (props-v1.4)", k10), (f"cap {best[2]:g} only", cap_only),
                   (f"QB rate {fmt_b(best[3])} only", qb_only), ("chosen, both", kb)):
        if lab.startswith("v1"):
            L.append(f"| {lab} | {ll(d, 'n|' + k):.4f} | | {ll(d, 'e2e|' + k):.4f} | | {d['e2e|' + k].mean():.3f} |")
        elif k != k10:
            L.append(f"| {lab} | {ll(d, 'n|' + k):.4f} | {_ci(boot(d, 'n|' + k, 'n|' + k10))} | "
                     f"{ll(d, 'e2e|' + k):.4f} | {_ci(boot(d, 'e2e|' + k, 'e2e|' + k10))} | {d['e2e|' + k].mean():.3f} |")
    mm = mass[mass["n_off"] > 0]
    actual = mm["actives_scored"].sum() / mm["n_off"].sum()
    q10, qb_ = qid((V1_ALLOC, 0.99, None)), qid((best[0], best[2], best[3]))
    L += ["", f"Summed share of actives per team-game: v1 {mass['sum_q|' + q10].mean():.3f}, chosen "
              f"{mass['sum_q|' + qb_].mean():.3f}; actives actually scored {actual:.3f} of offensive touchdowns.", "",
          "### Calibration, end to end (binned by the chosen model)", ""]
    _calib(L, d, ["e2e|" + k10, "e2e|" + kb], ["v1", "chosen"])
    L += ["", "### Starting quarterbacks (test)", ""]
    _qb_rows(L, d, [("engine", "eng_e2e"), ("v1", "e2e|" + k10), ("chosen", "e2e|" + kb)])
    for name, g in (("starting QBs", d[d["starter"]]), ("QBs new to their team as starter", d[d["new_starter"]])):
        if len(g) and kb != k10:
            L.append(f"\n{name}, chosen vs v1 end to end: {_ci(boot(g, 'e2e|' + kb, 'e2e|' + k10))}.")
    L += ["", "| position | v1 | chosen | n |", "|---|---|---|---|"]
    for p, g in d.groupby("pos"):
        L.append(f"| {p} | {ll(g, 'e2e|' + k10):.4f} | {ll(g, 'e2e|' + kb):.4f} | {len(g)} |")
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"wrote {path}", file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())
