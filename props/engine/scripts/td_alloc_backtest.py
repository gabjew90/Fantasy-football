#!/usr/bin/env python3
"""Layer 2 backtest, and the end-to-end test against the engine's anytime model.

  python td_alloc_backtest.py [--tune 2022,2023] [--test 2024,2025] [--out DIR]

Population: every QB/RB/WR/TE on the GAME-DAY ACTIVE LIST (weekly-roster
status ACT, known before kickoff). Walk-forward throughout: a game is priced
from the prior season plus the current season's earlier weeks only, and
every setting is chosen on TUNE, frozen, then scored on TEST.

Three questions:

  1. ALLOCATION, conditional. Given the team's offensive touchdowns (both
     models told the same thing), who scores? Candidates tested against the
     engine's pass/rush + inside-10 split:
       - five channels (the first null result),
       - a slot prior for players with no history (the engine has one; both
         models get it here so neither wins by the other lacking it),
       - expected-touchdown weighting: each opportunity counts by how often
         an opportunity like it scores, not as 1,
       - the weight on a role carried over from another team, tuned.
  2. REALLOCATION of an absent player's share: frozen at "all".
  3. END TO END, unconditional -- what would actually be deployed:
       engine      implied points x league offensive TDs/point, linear,
                   Poisson; per-TD share from pass/rush + inside-10 usage;
                   the structure of anytime_td_v0;
       rebuild     layer 1 frozen (Binomial(10), gamma 0.25) x the best
                   layer-2 configuration.
     Conditional tests isolate each layer but say nothing about deployed
     accuracy; this one does.
"""

from __future__ import annotations

import argparse
import itertools
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import model as M  # noqa: E402
import td_alloc as A  # noqa: E402
import td_model as T  # noqa: E402
from td_backtest import GAMES, NV, fetch  # noqa: E402

KAPPA = 5.0                      # chosen in the earlier grid at every scheme
MODE = "all"                     # reallocation, frozen by the previous run
SKILL = {"QB": "QB", "RB": "RB", "FB": "RB", "WR": "WR", "TE": "TE"}
EPS = 1e-3
PASS_CH, RUSH_CH = ("pass_rz", "pass_far"), ("rush_in5", "rush_far", "qb_rush")
MIX_ALPHA = 100.0
L1 = T.LAYER1                    # {"trials": 10, "gamma": 0.25, ...}

CONFIGS = [dict(basis=b, prior=p, moved=m)
           for b, p, m in itertools.product(["counts", "xtd"], ["none", "slot"], [0.25, 0.5, 1.0])]
BASE = dict(basis="counts", prior="none", moved=0.5)   # the previous layer-2 spec


def cid(c: dict) -> str:
    return f"{c['basis']}|{c['prior']}|{c['moved']:g}"


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

    # expected-touchdown weights, fitted on the season BEFORE each target season
    cx = {}
    for s in seasons:
        if s - 1 not in seasons:
            continue
        sub = opps[opps["season"].isin([s - 1, s])].copy()
        sub["xtd"] = A.xtd_weights(sub, A.xtd_table(opps[opps["season"] == s - 1]))
        cx[s] = A.counts(sub, "channel", weight="xtd")

    return {"cch": A.counts(opps, "channel"), "ceng": A.counts(opps, "engine"), "cx": cx,
            "sc": pd.concat(sc, ignore_index=True), "played": played, "active": active,
            "slots": slots, "tg": tg, "fin": fin, "unmapped": unmapped, "cover": cover,
            "slot_cover": float(active["slot"].notna().mean())}


def per_game(cnt: pd.DataFrame, chans) -> dict[str, float]:
    t = cnt.groupby(["game_id", "team"])[list(chans)].sum()
    return {c: max(float(t[c].mean()), 1e-6) for c in chans}


def _per_td(shares: pd.DataFrame, mix: pd.Series, chans) -> pd.Series:
    w = mix[list(chans)]
    w = w / w.sum() if w.sum() > 0 else w
    return sum(w[c] * shares[c] for c in chans)


def run(D: dict, seasons: list[int], configs: list[dict]) -> pd.DataFrame:
    cch, ceng, played, active, slots, tg = D["cch"], D["ceng"], D["played"], D["active"], D["slots"], D["tg"]
    scored = set(zip(D["sc"]["game_id"], D["sc"]["player_id"]))
    n_tr, gam = L1["trials"], L1["gamma"]
    rows = []
    for s in seasons:
        pl_pri = played[played["season"] == s - 1]
        sl_pri = slots[slots["season"] == s - 1]
        f = D["fin"][s - 1]
        src = {"counts": cch, "xtd": D["cx"][s]}
        pri = {b: src[b][src[b]["season"] == s - 1] for b in src}
        pg = {b: per_game(pri[b], T.OFFENSIVE) for b in src}
        sp = {b: A.slot_prior(pri[b], pl_pri, sl_pri, T.OFFENSIVE) for b in src}
        pri_e = ceng[ceng["season"] == s - 1]
        pg_e, sp_e = per_game(pri_e, A.ENGINE_CHANNELS), A.slot_prior(pri_e, pl_pri, sl_pri, A.ENGINE_CHANNELS)
        for w in sorted(tg.loc[tg["season"] == s, "week"].unique()):
            cur = lambda d: d[(d["season"] == s) & (d["week"] < w)]  # noqa: E731
            pl_cur = cur(played)
            now = active[(active["season"] == s) & (active["week"] == w)]
            both = pd.concat([pl_pri, pl_cur, now])
            pos = dict(zip(both["player_id"], both["pos"]))
            team_now = dict(zip(now["player_id"], now["team"]))
            hist = tg[(tg["season"] == s - 1) | ((tg["season"] == s) & (tg["week"] < w))]
            mix_team, mix_league = T.channel_shares(hist, MIX_ALPHA)
            ratio_off = hist["off_tds"].sum() / hist["points"].sum()
            ref = hist["implied"].mean()

            # engine: counts, its own half-weight convention, slot prior as it has
            sh_e = A.fill_no_history(
                A.blended_shares(cur(ceng), pri_e, pl_cur, pl_pri, A.ENGINE_CHANNELS, KAPPA, pg_e,
                                 current_team=team_now, moved_weight=0.5),
                now, sp_e, A.ENGINE_CHANNELS)
            shares = {}
            for b, mw in {(c["basis"], c["moved"]) for c in configs}:
                shares[(b, mw)] = A.blended_shares(cur(src[b]), pri[b], pl_cur, pl_pri, T.OFFENSIVE, KAPPA,
                                                   pg[b], current_team=team_now, moved_weight=mw)
            filled = {}
            for c in configs:
                sh = shares[(c["basis"], c["moved"])]
                filled[cid(c)] = A.fill_no_history(sh, now, sp[c["basis"]], T.OFFENSIVE) if c["prior"] == "slot" else sh

            for _, g in tg[(tg["season"] == s) & (tg["week"] == w)].iterrows():
                act = now[(now["game_id"] == g["game_id"]) & (now["team"] == g["team"])]
                if act.empty:
                    continue
                ids = list(act["player_id"])
                mix = mix_team.loc[g["team"]] if g["team"] in mix_team.index else mix_league
                npass, nrush = sum(g[c] for c in PASS_CH), sum(g[c] for c in RUSH_CH)
                n_off = npass + nrush
                mu_eng = g["implied"] * ratio_off
                mu_new = float(T.team_mean(g["implied"], ratio_off, ref, gam))

                e = A.reallocate(A.candidates(sh_e, g["team"], A.ENGINE_CHANNELS), set(ids), pos,
                                 A.ENGINE_CHANNELS, "none").reindex(ids).fillna(0)
                s_pass = f["pass"] * e["tgt_i10"] + (1 - f["pass"]) * e["tgt_all"]
                s_rush = f["rush"] * e["car_i10"] + (1 - f["rush"]) * e["car_all"]
                prm = pd.Series({"pass": mix[list(PASS_CH)].sum(), "rush": mix[list(RUSH_CH)].sum()})
                q_eng = ((prm["pass"] * s_pass + prm["rush"] * s_rush) / prm.sum()).clip(upper=0.999)
                eng = {"n": 1 - (1 - q_eng) ** n_off,
                       "e2e": 1 - np.exp(-mu_eng * q_eng)}

                base = {"season": s, "week": w, "game_id": g["game_id"], "team": g["team"]}
                for c in configs:
                    m = A.reallocate(A.candidates(filled[cid(c)], g["team"], T.OFFENSIVE), set(ids), pos,
                                     T.OFFENSIVE, MODE).reindex(ids).fillna(0)
                    q = _per_td(m, mix, T.OFFENSIVE).clip(upper=0.999)
                    p_n = 1 - (1 - q) ** n_off
                    p_e2e = 1 - (1 - (mu_new / n_tr) * q) ** n_tr
                    # the two cross terms that split the end-to-end gain:
                    #   layer 1 frozen on the ENGINE's allocation, and
                    #   the ENGINE's count model on layer 2's allocation
                    p_l1_eng = 1 - (1 - (mu_new / n_tr) * q_eng) ** n_tr
                    p_eng_l2 = 1 - np.exp(-mu_eng * q)
                    for pid in ids:
                        rows.append({**base, "cfg": cid(c), "player_id": pid, "pos": pos.get(pid),
                                     "no_history": pid not in shares[(c["basis"], c["moved"])].index,
                                     "p_n": float(p_n[pid]), "p_e2e": float(p_e2e[pid]),
                                     "l1_engalloc": float(p_l1_eng[pid]), "eng_l2alloc": float(p_eng_l2[pid]),
                                     "eng_n": float(eng["n"][pid]), "eng_e2e": float(eng["e2e"][pid]),
                                     "scored": int((g["game_id"], pid) in scored)})
    return pd.DataFrame(rows)


def logloss(p, y):
    p = np.clip(np.asarray(p, float), EPS, 1 - EPS)
    y = np.asarray(y, float)
    return -(y * np.log(p) + (1 - y) * np.log(1 - p))


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


def wide(d: pd.DataFrame, col: str, cfgs: list[str], eng: str) -> pd.DataFrame:
    """One row per player-game: the engine column plus one column per config."""
    ks = ["game_id", "player_id"]
    first = d[d["cfg"] == cfgs[0]][ks + ["week", "pos", "scored", "no_history", eng]].rename(columns={eng: "engine"})
    for c in cfgs:
        first = first.merge(d[d["cfg"] == c][ks + [col]].rename(columns={col: c}), on=ks)
    return first


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tune", default="2022,2023")
    ap.add_argument("--test", default="2024,2025")
    ap.add_argument("--out", default=str(Path(__file__).resolve().parent / "backtest_out"))
    a = ap.parse_args(argv)
    tune = [int(x) for x in a.tune.split(",")]
    test = [int(x) for x in a.test.split(",")]
    D = load(sorted(set(tune + test) | {min(tune) - 1}))
    print(f"loaded: active list covers {D['cover']:.1%} of snaps; {D['slot_cover']:.1%} of actives have a "
          f"depth-chart slot", file=sys.stderr)
    ids = [cid(c) for c in CONFIGS]
    dtu, dte = run(D, tune, CONFIGS), run(D, test, CONFIGS)
    tune_ll = {c: float(logloss(dtu.loc[dtu["cfg"] == c, "p_n"], dtu.loc[dtu["cfg"] == c, "scored"]).mean())
               for c in ids}
    best = min(tune_ll, key=tune_ll.get)
    write(Path(a.out) / "td_layer2.md", D, dte, tune_ll, best, tune, test)
    return 0


def write(path: Path, D, dte, tune_ll, best, tune, test):
    path.parent.mkdir(parents=True, exist_ok=True)
    ids = list(tune_ll)
    Wn, We = wide(dte, "p_n", ids, "eng_n"), wide(dte, "p_e2e", ids, "eng_e2e")
    b0 = cid(BASE)
    bs, bx = "counts|slot|0.5", "xtd|slot|0.5"
    L = ["# Layer 2 and the end-to-end test", "",
         f"Tune {tune}, test {test}. Population: QB/RB/WR/TE on the game-day active list, {len(Wn)} "
         f"player-games in test, {Wn['scored'].mean():.1%} of whom scored. Active list covers "
         f"{D['cover']:.1%} of snaps; {D['slot_cover']:.1%} of actives hold a depth-chart slot. "
         f"Reallocation '{MODE}', kappa {KAPPA:g}. The engine is given the slot prior it has in "
         "production, so neither side wins by the other lacking it.", "",
         "## Allocation, given the team's offensive touchdowns (test)", "",
         "| step | log loss | change vs row above (95% CI, game-clustered) |", "|---|---|---|",
         f"| Engine today (pass/rush, inside-10, slot prior) | {logloss(Wn['engine'], Wn['scored']).mean():.4f} | baseline |"]
    # Each row is compared with the configuration it actually modifies. A
    # rejected branch (expected-TD weighting) is scored against the row it
    # would have replaced, not chained into the next step.
    steps = [(b0, "five channels, raw counts, no prior (previous spec)", "engine"),
             (bs, "+ slot prior for players with no history", b0),
             (bx, "  alternative: + expected-touchdown weighting (on top of the slot prior)", bs)]
    if best not in (b0, bs, bx):
        steps.append((best, f"+ moved-role weight tuned (chosen on tune: {best})", bs))
    for c, lab, ref in steps:
        L.append(f"| {lab} | {logloss(Wn[c], Wn['scored']).mean():.4f} | vs {ref}: {_ci(boot(Wn, c, ref))} |")
    L += ["", f"Best on tune vs engine directly: {_ci(boot(Wn, best, 'engine'))}.", "",
          "### The no-history players the review flagged", "",
          "| model | mean predicted | actual rate | log loss | n |", "|---|---|---|---|---|"]
    nh = Wn[Wn["no_history"]]
    for c, lab in (("engine", "engine (slot prior)"), (b0, "previous spec (no share)"), (bs, "slot prior")):
        L.append(f"| {lab} | {nh[c].mean():.3f} | {nh['scored'].mean():.3f} | "
                 f"{logloss(nh[c], nh['scored']).mean():.4f} | {len(nh)} |")
    L += ["", "### Calibration, best configuration, given offensive touchdowns", "",
          "| predicted P(score) | previous spec: predicted | best: predicted | actual rate | n |",
          "|---|---|---|---|---|"]
    bins = [0, .05, .10, .20, .30, .45, .60, 1.0]
    for bb, g in Wn.assign(b=pd.cut(Wn[best], bins, include_lowest=True)).groupby("b", observed=True):
        L.append(f"| {bb} | {g[b0].mean():.3f} | {g[best].mean():.3f} | {g['scored'].mean():.3f} | {len(g)} |")

    L += ["", "## END TO END: what would be deployed (test)", "",
          "Unconditional. Engine = implied points x league offensive TDs/point, linear, Poisson, "
          "per-TD share from pass/rush + inside-10 usage with the slot prior: the structure of "
          f"anytime_td_v0. Rebuild = layer 1 frozen (Binomial({L1['trials']}), gamma {L1['gamma']}) "
          f"x layer 2 ({best}).", "",
          "| model | log loss | Brier | mean predicted | vs engine (95% CI, game-clustered) |",
          "|---|---|---|---|---|",
          f"| Engine (anytime_td_v0 structure) | {logloss(We['engine'], We['scored']).mean():.4f} | "
          f"{((We['engine'] - We['scored']) ** 2).mean():.4f} | {We['engine'].mean():.3f} | baseline |",
          f"| Layer 1 frozen x previous layer 2 | {logloss(We[b0], We['scored']).mean():.4f} | "
          f"{((We[b0] - We['scored']) ** 2).mean():.4f} | {We[b0].mean():.3f} | {_ci(boot(We, b0, 'engine'))} |",
          f"| Layer 1 frozen x best layer 2 | {logloss(We[best], We['scored']).mean():.4f} | "
          f"{((We[best] - We['scored']) ** 2).mean():.4f} | {We[best].mean():.3f} | {_ci(boot(We, best, 'engine'))} |",
          f"", f"Actual scoring rate {We['scored'].mean():.3f}.", "",
          "### Where the end-to-end difference comes from", "",
          "The two cross terms: each layer swapped in alone, the other left as the engine has it.", "",
          "| model | log loss | mean predicted | vs engine (95% CI, game-clustered) |", "|---|---|---|---|"]
    X = dte[dte["cfg"] == best][["game_id", "player_id", "scored", "eng_e2e", "l1_engalloc", "eng_l2alloc", "p_e2e"]]
    for col, lab in (("l1_engalloc", "layer 1 frozen, ENGINE allocation"),
                     ("eng_l2alloc", "ENGINE count model, layer 2 allocation"),
                     ("p_e2e", "both (the rebuild)")):
        L.append(f"| {lab} | {logloss(X[col], X['scored']).mean():.4f} | {X[col].mean():.3f} | "
                 f"{_ci(boot(X, col, 'eng_e2e'))} |")
    L += ["",
          "| predicted P(score) | engine: predicted | engine: actual | rebuild: predicted | rebuild: actual |",
          "|---|---|---|---|---|"]
    for bb in pd.IntervalIndex.from_breaks(bins, closed="right"):
        ge = We[(We["engine"] > bb.left) & (We["engine"] <= bb.right)]
        gr = We[(We[best] > bb.left) & (We[best] <= bb.right)]
        L.append(f"| {bb} | {ge['engine'].mean():.3f} ({len(ge)}) | {ge['scored'].mean():.3f} | "
                 f"{gr[best].mean():.3f} ({len(gr)}) | {gr['scored'].mean():.3f} |")
    L += ["", "| position | engine | rebuild | n |", "|---|---|---|---|"]
    for p, g in We.groupby("pos"):
        L.append(f"| {p} | {logloss(g['engine'], g['scored']).mean():.4f} | "
                 f"{logloss(g[best], g['scored']).mean():.4f} | {len(g)} |")
    L += ["", "## Tuning (tune log loss, given offensive touchdowns)", "",
          "| basis | no-history prior | moved-role weight | tune log loss |", "|---|---|---|---|"]
    for c, v in sorted(tune_ll.items(), key=lambda kv: kv[1]):
        b, p, m = c.split("|")
        L.append(f"| {b} | {p} | {m} | {v:.4f}{' **chosen**' if c == best else ''} |")
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"wrote {path}", file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())
