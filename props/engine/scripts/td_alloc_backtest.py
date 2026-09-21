#!/usr/bin/env python3
"""Layer 2 backtest: who scores, GIVEN the team's actual touchdowns by channel.

  python td_alloc_backtest.py [--tune 2022,2023] [--test 2024,2025] [--out DIR]

Conditioning on the team's real touchdowns by channel isolates allocation:
layer 1's count error cannot leak in, in either direction.

For every quarterback, running back, receiver and tight end who took an
offensive snap, P(scores at least one touchdown) from:

  engine today   pass/rush shares mixing inside-the-10 and overall usage,
                 given the team's actual passing and rushing touchdowns;
  layer 2        shares within each of five offensive channels, given the
                 team's actual touchdowns in each, with an inactive player's
                 share reallocated one of three ways.

Walk-forward: shares for a game come from the prior season plus the current
season's earlier weeks only. Settings chosen on TUNE, frozen, scored on TEST.
"""

from __future__ import annotations

import argparse
import itertools
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import td_alloc as A  # noqa: E402
import td_model as T  # noqa: E402
from td_backtest import GAMES, NV, fetch  # noqa: E402

KAPPA_GRID = [0.5, 2.0, 5.0, 15.0]     # prior weight, in games of team opportunities
MODES = ["none", "all", "position"]
SKILL = {"QB": "QB", "RB": "RB", "FB": "RB", "WR": "WR", "TE": "TE"}
EPS = 1e-3


def load(seasons: list[int]):
    players = pd.read_csv(fetch(f"{NV}/players/players.csv", "players.csv"),
                          usecols=["gsis_id", "pfr_id", "position"], low_memory=False)
    qb_ids = set(players.loc[players["position"] == "QB", "gsis_id"].dropna())
    pfr = players.dropna(subset=["pfr_id", "gsis_id"]).drop_duplicates("pfr_id").set_index("pfr_id")["gsis_id"]

    opps, sc, tds, played, active, fin = [], [], [], [], [], {}
    for s in seasons:
        pbp = pd.read_csv(fetch(f"{NV}/pbp/play_by_play_{s}.csv.gz", f"pbp_{s}.csv.gz"),
                          usecols=A.PBP_COLS_L2, low_memory=False)
        opps.append(A.opportunities(pbp, qb_ids))
        sc.append(A.scorers(pbp, qb_ids))
        tds.append(T.classify_tds(pbp, qb_ids))
        # the engine's inside-10 fractions, from the plays themselves
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
        # THE GAME-DAY ACTIVE LIST, known ~90 minutes before kickoff. Snaps
        # say who PLAYED, which is fine for history but is in-game
        # information for the week being predicted: a player who dressed and
        # never took a snap would look known-out, and his share would be
        # reallocated as if the model knew in advance.
        ros = pd.read_csv(fetch(f"{NV}/weekly_rosters/roster_weekly_{s}.csv",
                                f"roster_weekly_{s}.csv"), low_memory=False)
        ros = ros[(ros["game_type"] == "REG") & (ros["status"] == "ACT")
                  & ros["position"].isin(SKILL) & ros["gsis_id"].notna()]
        active.append(pd.DataFrame({"season": ros["season"], "week": ros["week"],
                                    "team": T._norm_team(ros["team"]),
                                    "player_id": ros["gsis_id"], "pos": ros["position"].map(SKILL)}))
    opps = pd.concat(opps, ignore_index=True)
    played = pd.concat(played, ignore_index=True)
    unmapped = int(played["player_id"].isna().sum())
    played = played.dropna(subset=["player_id"]).drop_duplicates(["game_id", "player_id"])
    active = pd.concat(active, ignore_index=True).drop_duplicates(["season", "week", "player_id"])

    # A join failure here would silently zero whole teams, as the franchise
    # codes did in layer 1. Every team that ran a play must have players.
    pbp_teams = set(opps["team"].unique())
    snap_teams = set(played["team"].unique())
    if pbp_teams != snap_teams:
        raise SystemExit(f"team codes differ between play-by-play and snap counts: "
                         f"only in pbp {sorted(pbp_teams - snap_teams)}, "
                         f"only in snaps {sorted(snap_teams - pbp_teams)}")

    sched = pd.read_csv(fetch(GAMES, "games.csv"), low_memory=False)
    tg = T.team_games(sched[sched["season"].isin(seasons)], pd.concat(tds, ignore_index=True))

    # the active list must attach to the same games, and must cover the people
    # who actually played -- a gap here would silently drop scorers
    active = active.merge(tg[["season", "week", "team", "game_id"]], on=["season", "week", "team"],
                          how="inner")
    if set(active["team"]) != pbp_teams:
        raise SystemExit(f"team codes differ between play-by-play and weekly rosters: "
                         f"{sorted(pbp_teams ^ set(active['team']))}")
    both = played.merge(active[["game_id", "player_id"]], on=["game_id", "player_id"], how="left",
                        indicator=True)
    cover = float((both["_merge"] == "both").mean())
    if cover < 0.95:
        raise SystemExit(f"only {cover:.1%} of players with an offensive snap are on the game-day "
                         "active list -- the active list is not joining")
    return (A.counts(opps, "channel"), A.counts(opps, "engine"), pd.concat(sc, ignore_index=True),
            played, tg, fin, unmapped, active, cover)


def per_game(cnt: pd.DataFrame, chans) -> dict[str, float]:
    t = cnt.groupby(["game_id", "team"])[list(chans)].sum()
    return {c: max(float(t[c].mean()), 1e-6) for c in chans}


PASS_CH, RUSH_CH = ("pass_rz", "pass_far"), ("rush_in5", "rush_far", "qb_rush")
MIX_ALPHA = 100.0      # layer 1's tuned channel-mix pseudo-count, in touchdowns
REAL_MASS = 0.15       # a team-game "has an absence" if inactives held this much share


def _per_td(shares: pd.DataFrame, mix: pd.Series, chans) -> pd.Series:
    """Probability a single touchdown from `chans` goes to each player: his
    share in each channel weighted by how often that channel produces one."""
    w = mix[list(chans)]
    w = w / w.sum() if w.sum() > 0 else w
    return sum(w[c] * shares[c] for c in chans)


def run(data, seasons, kappas):
    """Every active skill player in `seasons`, with P(score) under the engine
    and layer 2, for each (kappa, reallocation mode), under two ways of
    conditioning on the team's result that give BOTH models the SAME
    information:

      N     the team's total offensive touchdowns; each model spreads them
            over its own expected channel mix (from layer 1, walk-forward);
      PR    the team's passing and rushing touchdowns -- the engine's own
            granularity; layer 2 splits each over its sub-channels by mix.

    WHY NOT CONDITION ON THE ACTUAL CHANNEL COUNTS. That was the first
    version, and it flattered layer 2 by construction: finer conditioning
    reveals more of the answer. Telling a model "this team scored one QB-rush
    touchdown" tells it the starting quarterback scored, and QB log loss fell
    from 0.32 to 0.08 for that reason alone. That column is still produced
    (p_chan) so the artefact stays visible, but it is not a comparison.
    """
    cch, ceng, sc, played, tg, fin, _, active, _cover = data
    scored = set(zip(sc["game_id"], sc["player_id"]))
    rows = []
    for s in seasons:
        pri_c, pri_e = cch[cch["season"] == s - 1], ceng[ceng["season"] == s - 1]
        pl_pri = played[played["season"] == s - 1]
        pg_c, pg_e = per_game(pri_c, T.OFFENSIVE), per_game(pri_e, A.ENGINE_CHANNELS)
        f = fin[s - 1]
        for w in sorted(tg.loc[tg["season"] == s, "week"].unique()):
            cur = lambda d: d[(d["season"] == s) & (d["week"] < w)]  # noqa: E731
            pl_cur = cur(played)
            # who is dressed THIS week: the game-day active list, not snaps
            now = active[(active["season"] == s) & (active["week"] == w)]
            both = pd.concat([pl_pri, pl_cur, now])
            pos = dict(zip(both["player_id"], both["pos"]))
            team_now = dict(zip(now["player_id"], now["team"]))
            games = tg[(tg["season"] == s) & (tg["week"] == w)]
            hist = tg[(tg["season"] == s - 1) | ((tg["season"] == s) & (tg["week"] < w))]
            mix_team, mix_league = T.channel_shares(hist, MIX_ALPHA)
            for k in kappas:
                sh_c = A.blended_shares(cur(cch), pri_c, pl_cur, pl_pri, T.OFFENSIVE, k, pg_c,
                                        current_team=team_now)
                sh_e = A.blended_shares(cur(ceng), pri_e, pl_cur, pl_pri, A.ENGINE_CHANNELS, k, pg_e,
                                        current_team=team_now)
                for _, g in games.iterrows():
                    act = now[(now["game_id"] == g["game_id"]) & (now["team"] == g["team"])]
                    if act.empty:
                        continue
                    ids = set(act["player_id"])
                    mix = mix_team.loc[g["team"]] if g["team"] in mix_team.index else mix_league
                    n_ch = {c: g[c] for c in T.OFFENSIVE}
                    npass, nrush = sum(g[c] for c in PASS_CH), sum(g[c] for c in RUSH_CH)
                    n_off = npass + nrush
                    cand_c = A.candidates(sh_c, g["team"], T.OFFENSIVE)
                    cand_e = A.candidates(sh_e, g["team"], A.ENGINE_CHANNELS)
                    # AN ABSENCE IS A PLAYER WHO WAS HERE LATELY AND IS NOT TODAY.
                    # The first cut counted everyone in the window who was not
                    # active -- which includes last season's players who left,
                    # retired or went unsigned, so every week 1 looked like a
                    # mass injury and 97% of player-games were "affected".
                    # Departures are real vacated share, but they are roster
                    # turnover, not injuries, and are reported separately.
                    recent = set(pl_cur.loc[(pl_cur["team"] == g["team"]) & (pl_cur["week"] >= w - 3),
                                            "player_id"])
                    absent = cand_c[cand_c.index.isin(recent - ids)]
                    chans4 = ("rush_in5", "rush_far", "pass_rz", "pass_far")
                    absence = float(max(absent[c].sum() for c in chans4)) if len(absent) else 0.0

                    # Engine today: no reallocation -- it prices the actives it finds.
                    e = A.reallocate(cand_e, ids, pos, A.ENGINE_CHANNELS, "none").reindex(list(ids)).fillna(0)
                    s_pass = f["pass"] * e["tgt_i10"] + (1 - f["pass"]) * e["tgt_all"]
                    s_rush = f["rush"] * e["car_i10"] + (1 - f["rush"]) * e["car_all"]
                    pr_mix = pd.Series({"pass": mix[list(PASS_CH)].sum(), "rush": mix[list(RUSH_CH)].sum()})
                    q_eng = (pr_mix["pass"] * s_pass + pr_mix["rush"] * s_rush) / pr_mix.sum()
                    p_eng_pr = A.p_score(pd.DataFrame({"pass": s_pass, "rush": s_rush}),
                                         {"pass": npass, "rush": nrush})
                    p_eng_n = 1 - (1 - q_eng.clip(upper=0.999)) ** n_off

                    base = {"season": s, "week": w, "game_id": g["game_id"], "team": g["team"],
                            "k": k, "absence": absence}
                    for mode in MODES:
                        m = A.reallocate(cand_c, ids, pos, T.OFFENSIVE, mode).reindex(list(ids)).fillna(0)
                        p_chan = A.p_score(m, n_ch)
                        qp, qr = _per_td(m, mix, PASS_CH), _per_td(m, mix, RUSH_CH)
                        p_pr = 1 - (1 - qp.clip(upper=0.999)) ** npass * (1 - qr.clip(upper=0.999)) ** nrush
                        q_all = _per_td(m, mix, T.OFFENSIVE)
                        p_n = 1 - (1 - q_all.clip(upper=0.999)) ** n_off
                        for pid in ids:
                            rows.append({**base, "mode": mode, "player_id": pid, "pos": pos.get(pid),
                                         "p_chan": float(p_chan[pid]),
                                         "p_model_pr": float(p_pr[pid]), "p_eng_pr": float(p_eng_pr[pid]),
                                         "p_model_n": float(p_n[pid]), "p_eng_n": float(p_eng_n[pid]),
                                         "scored": int((g["game_id"], pid) in scored)})
    return pd.DataFrame(rows)


def logloss(p, y):
    p = np.clip(np.asarray(p, float), EPS, 1 - EPS)
    y = np.asarray(y, float)
    return -(y * np.log(p) + (1 - y) * np.log(1 - p))


def summary(d: pd.DataFrame, col: str) -> dict:
    return {"log": float(logloss(d[col], d["scored"]).mean()),
            "brier": float(((d[col] - d["scored"]) ** 2).mean()),
            "pred": float(d[col].mean()), "rate": float(d["scored"].mean()), "n": len(d)}


def boot(d: pd.DataFrame, a: str, b: str, reps=2000, seed=5):
    """Log loss(a) - log loss(b), resampling whole games."""
    x = pd.DataFrame({"g": d["game_id"].to_numpy(),
                      "v": logloss(d[a], d["scored"]) - logloss(d[b], d["scored"])}).groupby("g")["v"]
    sums, cnt = x.sum().to_numpy(), x.size().to_numpy()
    idx = np.random.default_rng(seed).integers(0, len(sums), size=(reps, len(sums)))
    bs = sums[idx].sum(1) / cnt[idx].sum(1)
    return float(sums.sum() / cnt.sum()), *np.percentile(bs, [2.5, 97.5]).tolist()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tune", default="2022,2023")
    ap.add_argument("--test", default="2024,2025")
    ap.add_argument("--out", default=str(Path(__file__).resolve().parent / "backtest_out"))
    a = ap.parse_args(argv)
    tune = [int(x) for x in a.tune.split(",")]
    test = [int(x) for x in a.test.split(",")]
    data = load(sorted(set(tune + test) | {min(tune) - 1}))
    print(f"loaded; {data[6]} snap rows had no GSIS id and were dropped", file=sys.stderr)

    dtu, dte = run(data, tune, KAPPA_GRID), run(data, test, KAPPA_GRID)
    ks = ["game_id", "player_id"]
    pick = lambda d, k, m, col, new: (d[(d["k"] == k) & (d["mode"] == m)][ks + [col]]  # noqa: E731
                                      .rename(columns={col: new}))
    res = {}
    for scheme in ("n", "pr"):
        e_tune = {k: summary(dtu[(dtu["k"] == k) & (dtu["mode"] == "none")], f"p_eng_{scheme}")["log"]
                  for k in KAPPA_GRID}
        k_eng = min(e_tune, key=e_tune.get)
        m_tune = {k: summary(dtu[(dtu["k"] == k) & (dtu["mode"] == "none")], f"p_model_{scheme}")["log"]
                  for k in KAPPA_GRID}
        k_best = min(m_tune, key=m_tune.get)
        base = dte[(dte["k"] == k_eng) & (dte["mode"] == "none")][
            ks + ["week", "team", "scored", "pos", "absence", f"p_eng_{scheme}"]]
        d = (base.rename(columns={f"p_eng_{scheme}": "eng"})
             .merge(pick(dte, k_best, "none", f"p_model_{scheme}", "chan"), on=ks))
        for m in ("all", "position"):
            d = d.merge(pick(dte, k_best, m, f"p_model_{scheme}", m), on=ks)
        res[scheme] = {"d": d, "k_eng": k_eng, "k_best": k_best, "e_tune": e_tune, "m_tune": m_tune}

    # the artefact, kept visible: conditioning on the actual channel counts
    art = (dte[(dte["k"] == res["pr"]["k_eng"]) & (dte["mode"] == "none")][ks + ["scored", "pos", "p_eng_pr"]]
           .merge(pick(dte, res["n"]["k_best"], "none", "p_chan", "p_chan"), on=ks))
    write(Path(a.out) / "td_layer2.md", res, art, tune, test, data[6], data[8])
    return 0


def _v(x):
    return "better" if x[2] < 0 else ("worse" if x[1] > 0 else "not established")


def _ci(x):
    return f"{x[0]:+.4f} ({x[1]:+.4f}, {x[2]:+.4f}) {_v(x)}"


def write(path: Path, res, art, tune, test, unmapped, cover=float("nan")):
    path.parent.mkdir(parents=True, exist_ok=True)
    n0 = res["n"]["d"]
    L = ["# Layer 2: player allocation", "",
         f"Tune {tune}, test {test}. Population: every QB/RB/WR/TE on the GAME-DAY ACTIVE LIST "
         f"(known before kickoff, not who took a snap), {len(n0)} player-games in test, "
         f"{n0['scored'].mean():.1%} of whom scored. The active list covers {cover:.1%} of players "
         f"who took an offensive snap. {unmapped} snap rows had no GSIS id and were dropped from "
         "the history.", "",
         "Both models are given the SAME information about the team's result, so the comparison "
         "is allocation and nothing else.", ""]
    names = {"n": "Given the team's total offensive touchdowns",
             "pr": "Given the team's passing and rushing touchdowns (the engine's own granularity)"}
    for scheme in ("n", "pr"):
        r = res[scheme]; d = r["d"]
        se, sc = summary(d, "eng"), summary(d, "chan")
        L += [f"## {names[scheme]}", "",
              "| model | log loss | Brier | mean predicted | vs engine today (95% CI, game-clustered) |",
              "|---|---|---|---|---|",
              f"| Engine today (kappa={r['k_eng']:g}) | {se['log']:.4f} | {se['brier']:.4f} | {se['pred']:.3f} | baseline |",
              f"| Layer 2, five channels (kappa={r['k_best']:g}) | {sc['log']:.4f} | {sc['brier']:.4f} | "
              f"{sc['pred']:.3f} | {_ci(boot(d, 'chan', 'eng'))} |", "",
              "| position | engine today | layer 2 | n |", "|---|---|---|---|"]
        for p, g in d.groupby("pos"):
            L.append(f"| {p} | {logloss(g['eng'], g['scored']).mean():.4f} | "
                     f"{logloss(g['chan'], g['scored']).mean():.4f} | {len(g)} |")
        L.append("")

    d = res["n"]["d"]
    L += ["## Injury reallocation, where it can matter", ""]
    subsets = [
        (d[d["absence"] >= REAL_MASS],
         f"In-season absences: team-games where a player who had played for the team in the last "
         f"three weeks was inactive and had held at least {REAL_MASS:.0%} of a rushing or receiving "
         "channel."),
        (d[d["week"] <= 3],
         "Weeks 1-3, all games: dominated by OFFSEASON departures -- last season's players who are "
         "no longer on the team, whose share has to go somewhere."),
    ]
    for sub, desc in subsets:
        teams = sub[["game_id", "team"]].drop_duplicates().shape[0]
        L += [desc, f"{teams} team-games, {len(sub)} player-games in test.", "",
              "| reallocation | log loss | vs none (95% CI, game-clustered) |", "|---|---|---|",
              f"| none: the share goes to other | {summary(sub, 'chan')['log']:.4f} | baseline |"]
        for m, lab in (("all", "all: spread over every active teammate"),
                       ("position", "position: to active teammates at his position")):
            L.append(f"| {lab} | {summary(sub, m)['log']:.4f} | {_ci(boot(sub, m, 'chan'))} |")
        L.append("")

    L += ["", "## Calibration, layer 2 given total touchdowns (test)", "",
          "| predicted P(score) | mean predicted | actual rate | n |", "|---|---|---|---|"]
    bins = [0, .05, .10, .20, .30, .45, .60, 1.0]
    for b, g in d.assign(b=pd.cut(d["chan"], bins, include_lowest=True)).groupby("b", observed=True):
        L.append(f"| {b} | {g['chan'].mean():.3f} | {g['scored'].mean():.3f} | {len(g)} |")

    sa, se = summary(art, "p_chan"), summary(art, "p_eng_pr")
    L += ["", "## The artefact this replaced", "",
          "The first version conditioned layer 2 on the team's actual touchdowns IN EACH CHANNEL "
          "while the engine got only pass and rush. Finer conditioning reveals more of the answer: "
          "one QB-rush touchdown means the starting quarterback scored.", "",
          "| | log loss | QB log loss |", "|---|---|---|",
          f"| engine, given pass/rush | {se['log']:.4f} | {logloss(art.loc[art['pos'] == 'QB', 'p_eng_pr'], art.loc[art['pos'] == 'QB', 'scored']).mean():.4f} |",
          f"| layer 2, given each channel | {sa['log']:.4f} | {logloss(art.loc[art['pos'] == 'QB', 'p_chan'], art.loc[art['pos'] == 'QB', 'scored']).mean():.4f} |",
          "", "Not a comparison. Kept so the flattering number cannot be quoted without its reason.", "",
          "## Tuning (tune log loss, no reallocation)", "",
          "| kappa (games) | engine, total TDs | layer 2, total TDs | engine, pass/rush | layer 2, pass/rush |",
          "|---|---|---|---|---|"]
    for k in KAPPA_GRID:
        L.append(f"| {k:g} | {res['n']['e_tune'][k]:.4f} | {res['n']['m_tune'][k]:.4f} | "
                 f"{res['pr']['e_tune'][k]:.4f} | {res['pr']['m_tune'][k]:.4f} |")
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"wrote {path}", file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())
