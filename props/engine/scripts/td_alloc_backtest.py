#!/usr/bin/env python3
"""Layer 2 backtest, and the end-to-end test against the engine's anytime model.

  python td_alloc_backtest.py [--tune 2022,2023] [--test 2024,2025] [--out DIR]

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

# allocation keys: (prior, scale, moved). BASE is the spec before the slot prior.
BASE_ALLOC = ("none", 1.0, 0.5)
V1_ALLOC = ("slot", V.V1["slot_scale"], MOVED)
# Default run: the SHIPPED configuration and the two references it is
# compared with. --grid reproduces the tuning run (slot scale x Beta c).
SCALES = [0.4, 0.6, 1.0]
C_GRID = [None, 80.0, 40.0, 20.0, 10.0, 5.0]
ALLOCS = [BASE_ALLOC, ("slot", 1.0, MOVED), V1_ALLOC]
CONFIGS = [(al, None) for al in ALLOCS]


def use_grid() -> None:
    global ALLOCS, CONFIGS
    ALLOCS = [BASE_ALLOC] + [("slot", s, MOVED) for s in SCALES]
    CONFIGS = [(BASE_ALLOC, None)] + [(al, c) for al in ALLOCS[1:] for c in C_GRID]


def cid(alloc, c) -> str:
    p, s, m = alloc
    return f"{p}|x{s:g}|m{m:g}|c{'inf' if c is None else f'{c:g}'}"


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
    return {"cch": A.counts(opps, "channel"), "ceng": A.counts(opps, "engine"),
            "sc": sc, "scored_n": sc.groupby(["game_id", "player_id"])["tds"].sum().to_dict(),
            "played": played, "active": active, "slots": slots, "tg": tg, "fin": fin,
            "unmapped": unmapped, "cover": cover, "slot_cover": float(active["slot"].notna().mean())}


def run(D: dict, seasons: list[int]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """(player rows, team-game mass rows). Every rebuild number here comes out
    of td_v1 -- the module score_game.py calls -- so what is validated is
    what ships. Only the ENGINE reproduction has its own code, because it
    models the other system."""
    cch, ceng, played, active, slots, tg = D["cch"], D["ceng"], D["played"], D["active"], D["slots"], D["tg"]
    scored_n = D["scored_n"]
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
            ctx = V.context(hist)
            mix_team, mix_league, ratio_off = ctx["mix_team"], ctx["mix_league"], ctx["ratio_off"]

            # engine: counts, its own half-weight convention, the slot prior it has
            sh_e = A.fill_no_history(
                A.blended_shares(cur(ceng), pri_e, pl_cur, pl_pri, A.ENGINE_CHANNELS, KAPPA, pg_e,
                                 current_team=team_now, moved_weight=0.5),
                now, sp_e, A.ENGINE_CHANNELS)
            filled, raw = {}, {}
            for al in ALLOCS:
                filled[al], raw[al[2]] = V.week_shares(cur(cch), pri_c, pl_cur, pl_pri, sl_pri, now,
                                                       moved=al[2], slot_scale=al[1],
                                                       prior=al[0] == "slot")

            for _, g in tg[(tg["season"] == s) & (tg["week"] == w)].iterrows():
                act = now[(now["game_id"] == g["game_id"]) & (now["team"] == g["team"])]
                if act.empty:
                    continue
                ids = list(act["player_id"])
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
                        "nohist_q_engine": float(q_eng[nohist_ids].sum())}
                qs = {}
                for al in ALLOCS:
                    qs[al] = V.game_q(filled[al], g["team"], ids, pos, ctx)
                    mrow[f"sum_q|{al[0]}|x{al[1]:g}"] = float(qs[al].sum())
                    mrow[f"nohist_q|{al[0]}|x{al[1]:g}"] = float(qs[al][nohist_ids].sum())
                mass.append(mrow)

                base = {"season": s, "week": w, "game_id": g["game_id"], "team": g["team"]}
                cols = {}
                for al, c in CONFIGS:
                    q = qs[al].to_numpy()
                    k = cid(al, c)
                    cols[f"n|{k}"] = A.p_score_given(q, n_off, c)
                    cols[f"e2e|{k}"] = A.p_score_dist(q, pmf_new, c)
                    cols[f"engl2|{k}"] = A.p_score_dist(q, pmf_eng, c)
                nh_set = set(nohist_ids)
                for i, pid in enumerate(ids):
                    r = {**base, "player_id": pid, "pos": pos.get(pid), "no_history": pid in nh_set,
                         "scored": int(scored_n.get((g["game_id"], pid), 0) > 0),
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
                    help="reproduce the tuning run (slot scale x Beta concentration) instead of "
                         "scoring the shipped configuration")
    a = ap.parse_args(argv)
    if a.grid:
        use_grid()
    tune = [int(x) for x in a.tune.split(",")]
    test = [int(x) for x in a.test.split(",")]
    D = load(sorted(set(tune + test) | {min(tune) - 1}))
    print(f"loaded: active list covers {D['cover']:.1%} of snaps; {D['slot_cover']:.1%} of actives "
          f"hold a depth-chart slot", file=sys.stderr)
    dtu, _mtu = run(D, tune)
    dte, mte = run(D, test)
    tune_ll = {cid(al, c): ll(dtu, f"n|{cid(al, c)}") for al, c in CONFIGS}
    # the grid CHOOSES; the default run scores what td_v1 ships, unchosen
    best = min(tune_ll, key=tune_ll.get) if a.grid else cid(V1_ALLOC, V.V1["c"])
    name = "td_layer2.md" if a.grid else "td_v1.md"
    write(Path(a.out) / name, D, dte, mte, tune_ll, best, tune, test, shipped=not a.grid)
    return 0


def _calib(L, d, cols, labels, bins=(0, .05, .10, .20, .30, .45, .60, 1.0)):
    """Calibration by the bins of the LAST column, with every column's mean."""
    L += ["| predicted P(score) | " + " | ".join(f"{l}: predicted" for l in labels) + " | actual rate | n |",
          "|---" * (len(cols) + 3) + "|"]
    for b, g in d.assign(_b=pd.cut(d[cols[-1]], list(bins), include_lowest=True)).groupby("_b", observed=True):
        L.append(f"| {b} | " + " | ".join(f"{g[c].mean():.3f}" for c in cols)
                 + f" | {g['scored'].mean():.3f} | {len(g)} |")


def write(path: Path, D, d, mass, tune_ll, best, tune, test, shipped=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    prev = cid(("slot", 1.0, MOVED), None)          # the previous best: full slot prior, fixed share
    base = cid(BASE_ALLOC, None)
    bal = best.rsplit("|c", 1)[0]
    best_fixed = f"{bal}|cinf"
    L = ["# Layer 2 and the end-to-end test", "",
         f"Tune {tune}, test {test}. Population: QB/RB/WR/TE on the game-day active list, {len(d)} "
         f"player-games in test, {d['scored'].mean():.1%} of whom scored. Active list covers "
         f"{D['cover']:.1%} of snaps; {D['slot_cover']:.1%} of actives hold a depth-chart slot. "
         f"Five channels on raw counts; reallocation '{MODE}'; kappa {KAPPA:g}; moved-role weight "
         f"{MOVED:g}. The engine gets the slot prior it has in production.", "",
         (f"**Shipped configuration, scored as-is: {best}** -- the parameters in td_v1.V1, which "
          "score_game.py calls. Every rebuild number below comes out of that module." if shipped else
          f"Chosen on tune: **{best}** (slot-prior scale x, Beta concentration c)."), "",
         "## Where the touchdown mass goes (test, per team-game)", "",
         "Summed per-touchdown share of the team's ACTIVE players, against the fraction of the team's "
         "offensive touchdowns that active players actually scored. Anything below the actual line is "
         "probability the model never gives to anyone who plays.", ""]
    mm = mass[mass["n_off"] > 0]
    actual = mm["actives_scored"].sum() / mm["n_off"].sum()
    key_prev, key_best = "|slot|x1", f"|{bal.split('|')[0]}|{bal.split('|')[1]}"
    L += ["| | summed share of actives | of which: players with no history |", "|---|---|---|",
          f"| actual: fraction of offensive TDs scored by actives | **{actual:.3f}** | |",
          f"| engine | {mass['sum_q_engine'].mean():.3f} | {mass['nohist_q_engine'].mean():.3f} |",
          f"| layer 2, no prior (previous spec) | {mass['sum_q|none|x1'].mean():.3f} | "
          f"{mass['nohist_q|none|x1'].mean():.3f} |",
          f"| layer 2, full slot prior | {mass[f'sum_q{key_prev}'].mean():.3f} | {mass[f'nohist_q{key_prev}'].mean():.3f} |",
          f"| layer 2, chosen slot scale | {mass[f'sum_q{key_best}'].mean():.3f} | "
          f"{mass[f'nohist_q{key_best}'].mean():.3f} |", ""]

    L += ["## Allocation, given the team's offensive touchdowns (test)", "",
          "| model | log loss | vs | change (95% CI, game-clustered) |", "|---|---|---|---|",
          f"| Engine (pass/rush, inside-10, slot prior) | {ll(d, 'eng_n'):.4f} | | baseline |",
          f"| previous spec: no prior, fixed share | {ll(d, 'n|' + base):.4f} | engine | {_ci(boot(d, 'n|' + base, 'eng_n'))} |",
          f"| full slot prior, fixed share | {ll(d, 'n|' + prev):.4f} | previous spec | {_ci(boot(d, 'n|' + prev, 'n|' + base))} |",
          f"| chosen slot scale, fixed share | {ll(d, 'n|' + best_fixed):.4f} | full slot prior | "
          f"{_ci(boot(d, 'n|' + best_fixed, 'n|' + prev))} |"]
    if best != best_fixed:   # only the grid has a Beta row; the shipped share is fixed
        L.append(f"| + Beta share (chosen: {best}) | {ll(d, 'n|' + best):.4f} | fixed share | "
                 f"{_ci(boot(d, 'n|' + best, 'n|' + best_fixed))} |")
    L += ["", f"{'Shipped' if shipped else 'Chosen'} vs engine directly: "
              f"{_ci(boot(d, 'n|' + best, 'eng_n'))}.", "",
          "### Calibration given offensive touchdowns", ""]
    _calib(L, d, ["n|" + prev, "n|" + best], ["full slot, fixed share", "chosen"])
    nh = d[d["no_history"]]
    L += ["", "### No-history players", "",
          "| model | mean predicted | actual rate | n |", "|---|---|---|---|",
          f"| engine (full slot prior) | {nh['eng_n'].mean():.3f} | {nh['scored'].mean():.3f} | {len(nh)} |",
          f"| layer 2, full slot prior | {nh['n|' + prev].mean():.3f} | {nh['scored'].mean():.3f} | {len(nh)} |",
          f"| layer 2, chosen | {nh['n|' + best].mean():.3f} | {nh['scored'].mean():.3f} | {len(nh)} |", ""]

    e, r = "eng_e2e", "e2e|" + best
    L += ["## END TO END: what would be deployed (test)", "",
          "Engine = implied points x league offensive TDs/point, linear, Poisson; per-TD share from "
          "pass/rush + inside-10 usage with the slot prior: the structure of anytime_td_v0. "
          f"v1 = layer 1 frozen (Binomial({L1['trials']}), gamma {L1['gamma']}) x layer 2 ({best}).", "",
          "| model | log loss | Brier | mean predicted | vs engine (95% CI, game-clustered) |",
          "|---|---|---|---|---|",
          f"| Engine (anytime_td_v0 structure) | {ll(d, e):.4f} | {((d[e] - d['scored']) ** 2).mean():.4f} | "
          f"{d[e].mean():.3f} | baseline |",
          f"| v1 | {ll(d, r):.4f} | {((d[r] - d['scored']) ** 2).mean():.4f} | {d[r].mean():.3f} | "
          f"{_ci(boot(d, r, e))} |", "", f"Actual scoring rate {d['scored'].mean():.3f}.", "",
          "Cross terms -- each layer alone, the other as the engine has it:", "",
          "| model | log loss | mean predicted | vs engine |", "|---|---|---|---|",
          f"| layer 1 frozen, engine allocation | {ll(d, 'l1_engalloc'):.4f} | {d['l1_engalloc'].mean():.3f} | "
          f"{_ci(boot(d, 'l1_engalloc', e))} |",
          f"| engine count model, v1 allocation | {ll(d, 'engl2|' + best):.4f} | {d['engl2|' + best].mean():.3f} | "
          f"{_ci(boot(d, 'engl2|' + best, e))} |", "",
          "### Calibration, end to end", ""]
    _calib(L, d, [e, r], ["engine", "v1"])
    L += ["", "The 0.2-0.3 band is where most priced anytime lines sit.", "",
          "| position | engine | v1 | n |", "|---|---|---|---|"]
    for p, g in d.groupby("pos"):
        L.append(f"| {p} | {ll(g, e):.4f} | {ll(g, r):.4f} | {len(g)} |")
    L += ["", "## Tuning (tune log loss, given offensive touchdowns)", "",
          "| configuration | tune log loss |", "|---|---|"]
    for k, v in sorted(tune_ll.items(), key=lambda kv: kv[1]):
        L.append(f"| {k} | {v:.4f}{' **chosen**' if k == best else ''} |")
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"wrote {path}", file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())
