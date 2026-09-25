#!/usr/bin/env python3
"""Build the bundled prior-season resource tables for nfl-prop-research.

Run ONCE per offseason (or after a season completes), not on every invocation.
Downloads the prior season's play-by-play and rosters, derives per-player rates,
per-slot league priors, dispersion parameters and per-carry rushing residuals,
and writes compact CSV/JSON into resources/ so a live run never has to reprocess
a ~100 MB play-by-play file.

Usage:
  python build_priors.py --season 2025 [--out ../resources]

Outputs:
  priors_{season}_players.csv   per-player season rates + games played
  priors_{season}_slots.csv     per-slot league mean rates
  priors_{season}_teams.csv     per-team per-game volume means
  priors_{season}_params.json   dispersion fits, K0, per-carry residual quantiles,
                                league TD-per-point, league mean yards per carry
"""
import argparse, json, sys
from pathlib import Path

import re
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import model as M

def norm_name(s):
    """Normalise a player name for joining across nflverse tables that disagree on
    punctuation and suffixes: 'D.J. Moore' == 'DJ Moore', 'Luther Burden III' == 'Luther Burden'."""
    if not isinstance(s, str):
        return s
    s = s.lower().replace(".", "").replace("'", "").replace("-", " ")
    s = re.sub(r"\b(jr|sr|ii|iii|iv|v)\b", "", s)
    return " ".join(s.split())

NFLVERSE = "https://github.com/nflverse/nflverse-data/releases/download"
GAMES_URL = "https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv"
K0_DEFAULT = 4.0          # tuned on 2025 held-out fold (weeks 5-6 fit / 7-8 score)
R_CLAMP = [0.5, 30.0]
RESID_QUANTILES = 2001    # per-carry yardage residual grid
KNEEL_QUANTILES = 201     # per-team-game QB kneel-yards grid, per spread bucket
KNEEL_SPREAD_EDGES = (-3.0, 3.0, 7.0)   # dog 3+ | pick +-3 | fav 3-7 | fav 7+


def fetch(url, dest):
    import urllib.request
    if Path(dest).exists() and Path(dest).stat().st_size > 0:
        print(f"  cached  {url.rsplit('/', 1)[-1]}", file=sys.stderr)
        return dest
    print(f"  fetching {url.rsplit('/', 1)[-1]}", file=sys.stderr)
    urllib.request.urlretrieve(url, dest)
    return dest


def nb_mle(mu, y, r_clamp):
    """Fit log r = a + b*log(mu) by maximum likelihood (NB2)."""
    from scipy.optimize import minimize
    from scipy.special import gammaln

    def nll(p):
        a, b = p
        r = np.clip(np.exp(a + b * np.log(np.maximum(mu, 1e-6))), *r_clamp)
        q = r / (r + mu)
        return -np.sum(gammaln(y + r) - gammaln(r) - gammaln(y + 1)
                       + r * np.log(q) + y * np.log1p(-q))

    c0 = minimize(lambda p: nll([p[0], 0.0]), [1.0], method="Nelder-Mead")
    res = minimize(nll, [c0.x[0], 0.0], method="Nelder-Mead",
                   options={"xatol": 1e-6, "fatol": 1e-6, "maxiter": 5000})
    return {"a": float(res.x[0]), "b": float(res.x[1])}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--season", type=int, required=True)
    ap.add_argument("--out", default=str(Path(__file__).resolve().parent.parent / "resources"))
    ap.add_argument("--workdir", default="/tmp/nflpriors")
    args = ap.parse_args()
    S = args.season
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    wd = Path(args.workdir); wd.mkdir(parents=True, exist_ok=True)

    print(f"building priors for {S}", file=sys.stderr)
    pbp_f = fetch(f"{NFLVERSE}/pbp/play_by_play_{S}.csv", wd / f"pbp_{S}.csv")
    ros_f = fetch(f"{NFLVERSE}/weekly_rosters/roster_weekly_{S}.csv", wd / f"ros_{S}.csv")
    dc_f = fetch(f"{NFLVERSE}/depth_charts/depth_charts_{S}.csv", wd / f"dc_{S}.csv")
    snap_f = fetch(f"{NFLVERSE}/snap_counts/snap_counts_{S}.csv", wd / f"snap_{S}.csv")
    games_f = fetch(GAMES_URL, wd / "games.csv")

    pbp = pd.read_csv(pbp_f, low_memory=False)
    pbp = pbp[pbp.season_type == "REG"]
    games = pd.read_csv(games_f)
    g = games[(games.season == S) & (games.game_type == "REG")].copy()

    passes = pbp[(pbp.play_type == "pass") & pbp.receiver_player_id.notna()]
    rushes = pbp[(pbp.play_type == "run") & (pbp.qb_kneel != 1) & pbp.rusher_player_id.notna()]

    # ---- team per-week volumes -------------------------------------------
    tw = pd.DataFrame({
        "targets": passes.groupby(["posteam", "week"]).size(),
        "carries": rushes.groupby(["posteam", "week"]).size(),
        "i10_targets": passes[passes.yardline_100 <= 10].groupby(["posteam", "week"]).size(),
        "i10_carries": rushes[rushes.yardline_100 <= 10].groupby(["posteam", "week"]).size(),
        "pass_td": passes.groupby(["posteam", "week"])["pass_touchdown"].sum(),
        "rush_td": rushes.groupby(["posteam", "week"])["rush_touchdown"].sum(),
    }).fillna(0).reset_index().rename(columns={"posteam": "team"})
    teams = tw.groupby("team")[["targets", "carries", "i10_targets", "i10_carries",
                                "pass_td", "rush_td"]].mean().round(4)
    teams.to_csv(out / f"priors_{S}_teams.csv")

    # ---- player per-week ---------------------------------------------------
    rec = passes.groupby(["posteam", "week", "receiver_player_id"]).agg(
        targets=("play_id", "size"), receptions=("complete_pass", "sum"),
        rec_yards=("receiving_yards", "sum")).reset_index().rename(
        columns={"receiver_player_id": "gsis_id", "posteam": "team"})
    rec_i10 = passes[passes.yardline_100 <= 10].groupby(
        ["posteam", "week", "receiver_player_id"]).size().rename("i10_targets").reset_index().rename(
        columns={"receiver_player_id": "gsis_id", "posteam": "team"})
    ru = rushes.groupby(["posteam", "week", "rusher_player_id"]).agg(
        carries=("play_id", "size"), rush_yards=("rushing_yards", "sum")).reset_index().rename(
        columns={"rusher_player_id": "gsis_id", "posteam": "team"})
    ru_i10 = rushes[rushes.yardline_100 <= 10].groupby(
        ["posteam", "week", "rusher_player_id"]).size().rename("i10_carries").reset_index().rename(
        columns={"rusher_player_id": "gsis_id", "posteam": "team"})
    pw = (rec.merge(rec_i10, how="outer", on=["team", "week", "gsis_id"])
             .merge(ru, how="outer", on=["team", "week", "gsis_id"])
             .merge(ru_i10, how="outer", on=["team", "week", "gsis_id"]).fillna(0))
    pw = pw.merge(tw, on=["team", "week"], suffixes=("", "_team"))

    # ---- snap share --------------------------------------------------------
    snaps = pd.read_csv(snap_f)
    snaps = snaps[(snaps.season == S) & (snaps.game_type == "REG")]
    # snap_counts keys on pfr id, not gsis; aggregate by player name + team as a
    # per-player season mean only (used as a role prior, never as usage evidence)
    snaps = snaps.copy(); snaps["key"] = snaps["player"].map(norm_name)
    snap_season = snaps.groupby(["team", "key"])["offense_pct"].mean().rename("snap_pct_25")

    # ---- per-player season rates ------------------------------------------
    agg = pw.groupby("gsis_id").agg(
        targets=("targets", "sum"), receptions=("receptions", "sum"), rec_yards=("rec_yards", "sum"),
        team_targets=("targets_team", "sum"), carries=("carries", "sum"),
        rush_yards=("rush_yards", "sum"), team_carries=("carries_team", "sum"),
        i10_targets=("i10_targets", "sum"), team_i10_targets=("i10_targets_team", "sum"),
        i10_carries=("i10_carries", "sum"), team_i10_carries=("i10_carries_team", "sum"))
    roster = pd.read_csv(ros_f, low_memory=False)
    roster = roster[roster.season == S]
    n_act = roster[roster.status == "ACT"].groupby("gsis_id").size().rename("n_games")
    main_team = roster[roster.status == "ACT"].groupby("gsis_id")["team"].agg(
        lambda s: s.mode().iloc[0] if len(s.mode()) else None).rename("team_prior")
    names = roster.drop_duplicates("gsis_id").set_index("gsis_id")["full_name"]

    P = pd.DataFrame(index=agg.index)
    P["target_share"] = agg.targets / agg.team_targets
    P["catch_rate"] = np.where(agg.targets > 0, agg.receptions / agg.targets, np.nan)
    P["ypt"] = np.where(agg.targets > 0, agg.rec_yards / agg.targets, np.nan)
    P["rush_share"] = agg.carries / agg.team_carries
    P["ypc"] = np.where(agg.carries > 0, agg.rush_yards / agg.carries, np.nan)
    P["i10_target_share"] = np.where(agg.team_i10_targets > 0,
                                     agg.i10_targets / agg.team_i10_targets, np.nan)
    P["i10_carry_share"] = np.where(agg.team_i10_carries > 0,
                                    agg.i10_carries / agg.team_i10_carries, np.nan)
    P["targets_n"] = agg.targets; P["team_targets_n"] = agg.team_targets
    P["carries_n"] = agg.carries; P["team_carries_n"] = agg.team_carries
    P["i10_targets_n"] = agg.team_i10_targets; P["i10_carries_n"] = agg.team_i10_carries
    P = P.join(n_act).join(main_team).join(names)
    P["n_games"] = P["n_games"].fillna(0).astype(int)
    P = P.reset_index()
    P["key"] = P["full_name"].map(norm_name)
    P = P.merge(snap_season.reset_index().rename(columns={"team": "team_prior"}),
                on=["team_prior", "key"], how="left").drop(columns="key")
    P.round(5).to_csv(out / f"priors_{S}_players.csv", index=False)

    # ---- per-slot league priors (per-week depth-chart slot) ----------------
    dc = pd.read_csv(dc_f, low_memory=False)
    g["kick"] = pd.to_datetime(g.gameday.astype(str) + " " + g.gametime.astype(str), errors="coerce")
    kick_lookup = {}
    for _, r_ in g.iterrows():
        if pd.isna(r_.kick):
            continue
        off = 4 if pd.Timestamp(f"{r_.kick.year}-03-15") <= r_.kick < pd.Timestamp(f"{r_.kick.year}-11-01") else 5
        kt = (r_.kick + pd.Timedelta(hours=off)).tz_localize("UTC")
        kick_lookup[(r_.home_team, r_.week)] = kt; kick_lookup[(r_.away_team, r_.week)] = kt
    roles = M.normalize_depth_charts(dc, kick_lookup)
    roles.to_csv(out / f"priors_{S}_roles.csv", index=False)

    # Slot priors over ALL slot player-weeks, zero-filled (see backtest.py note): pw only has
    # player-weeks with a recorded stat, so a mean over pw alone inflates every prior.
    stat_cols = ["targets", "receptions", "rec_yards", "carries", "rush_yards", "i10_targets", "i10_carries"]
    rs_slot = roles.merge(pw[["team", "week", "gsis_id"] + stat_cols], on=["team", "week", "gsis_id"], how="left")
    rs_slot = rs_slot.merge(tw, on=["team", "week"], suffixes=("", "_team"))
    for c in stat_cols:
        rs_slot[c] = rs_slot[c].fillna(0)
    # keep the stat-bearing PROXY rows too (players outside the 7 slots who did record stats)
    rs_proxy = pw.merge(roles, on=["team", "week", "gsis_id"], how="left")
    rs_proxy = rs_proxy[rs_proxy.slot.isna()].assign(slot="PROXY")
    rs = pd.concat([rs_slot, rs_proxy], ignore_index=True)
    rs["slot"] = rs["slot"].fillna("PROXY")
    rs["target_share"] = rs.targets / rs.targets_team
    rs["rush_share"] = rs.carries / rs.carries_team
    rs["catch_rate"] = np.where(rs.targets > 0, rs.receptions / rs.targets, np.nan)
    rs["ypt"] = np.where(rs.targets > 0, rs.rec_yards / rs.targets, np.nan)
    rs["ypc"] = np.where(rs.carries > 0, rs.rush_yards / rs.carries, np.nan)
    rs["i10_target_share"] = np.where(rs.i10_targets_team > 0, rs.i10_targets / rs.i10_targets_team, np.nan)
    rs["i10_carry_share"] = np.where(rs.i10_carries_team > 0, rs.i10_carries / rs.i10_carries_team, np.nan)
    slots = rs.groupby("slot")[["target_share", "rush_share", "catch_rate", "ypt", "ypc",
                                "i10_target_share", "i10_carry_share"]].mean().round(5)
    slots.to_csv(out / f"priors_{S}_slots.csv")

    # ---- dispersion + residuals -------------------------------------------
    act = set(roster[roster.status == "ACT"].set_index(["week", "team", "gsis_id"]).index)
    fit_rows = rs[[(w, t, p) in act for w, t, p in zip(rs.week, rs.team, rs.gsis_id)]].copy()

    # Dispersion must be fit under the SAME information condition as deployment.
    #   - Same-week share makes mu collapse onto y (no apparent overdispersion, r pins
    #     at the clamp).
    #   - Leave-one-week-out SEASON rates use 16+ games, far more than a live run has;
    #     under that mu receptions are even under-dispersed in the low bins, which
    #     would ship intervals that are too tight in production.
    # A live run has prior-season rates plus a handful of current-season games, so fit
    # on an expanding prior-weeks-only rate shrunk toward the slot prior with K0, which
    # is exactly what the scorer does.
    fit_rows = fit_rows.sort_values(["gsis_id", "week"])
    for num, den, out_col in [("targets", "targets_team", "prior_ts"),
                              ("receptions", "targets", "prior_cr"),
                              ("carries", "carries_team", "prior_rs")]:
        cn = fit_rows.groupby("gsis_id")[num].transform(lambda s: s.shift().expanding().sum())
        cd = fit_rows.groupby("gsis_id")[den].transform(lambda s: s.shift().expanding().sum())
        fit_rows[out_col] = np.where(cd > 0, cn / cd, np.nan)
    fit_rows["n_prior"] = fit_rows.groupby("gsis_id").cumcount()

    slot_mean = fit_rows.groupby("slot")[["target_share", "catch_rate", "rush_share"]].mean()
    def shrink(col, slot_col, default):
        prior = fit_rows["slot"].map(slot_mean[slot_col]).fillna(default)
        own = fit_rows[col]
        w = fit_rows["n_prior"] / (fit_rows["n_prior"] + K0_DEFAULT)
        return np.where(own.isna(), prior, w * own.fillna(0) + (1 - w) * prior)

    ts_hat = shrink("prior_ts", "target_share", 0.05)
    cr_hat = np.clip(shrink("prior_cr", "catch_rate", 0.6), 0.05, 1.0)
    rs_hat = shrink("prior_rs", "rush_share", 0.05)

    mu_rec = (fit_rows.targets_team * ts_hat * cr_hat).clip(lower=0.02).values
    rec_fit = nb_mle(mu_rec, fit_rows.receptions.values.astype(float), R_CLAMP)
    mu_car = (fit_rows.carries_team * rs_hat).clip(lower=0.02).values
    rush_fit = nb_mle(mu_car, fit_rows.carries.values.astype(float), R_CLAMP)
    for nm, fit, mu in [("receptions", rec_fit, mu_rec), ("carries", rush_fit, mu_car)]:
        rr = np.clip(np.exp(fit["a"] + fit["b"] * np.log(np.maximum(mu, 1e-6))), *R_CLAMP)
        if np.allclose(rr, R_CLAMP[1]) or np.allclose(rr, R_CLAMP[0]):
            print(f"  WARNING: {nm} dispersion pinned at clamp -- fit is not usable",
                  file=sys.stderr)

    # per-catch Gamma shape, method of moments conditional on k
    pos_ = fit_rows[fit_rows.receptions >= 1]
    ks, ss, ws = [], [], []
    for k, grp in pos_.groupby("receptions"):
        if len(grp) < 25 or grp.rec_yards.var() <= 0:
            continue
        Y = grp.rec_yards.values
        ks.append(int(k)); ss.append((Y.mean() ** 2) / (k * Y.var())); ws.append(len(grp))
    shape_ypc = float(np.average(ss, weights=ws))

    ry = rushes.rushing_yards.dropna().values
    resid = np.quantile(ry - ry.mean(), np.linspace(0, 1, RESID_QUANTILES))

    # ---- QB rushing (docs/plans/2026-09-24-yardage-harness.md, step 3) --------
    # A QB's carries are not shaped like a running back's: scrambles run long
    # and a QB rarely loses yards (2022-24: 5th percentile 0 vs -2 league-wide).
    # So QBs get their own carry grid, the same length as the league grid (the
    # sampler's draw count is then unchanged for everyone else). And the book
    # settles a QB's rushing yards WITH his kneel-downs, which the carry data
    # drops: the per-team-game kneel yards are kept by the team's pregame spread
    # (a favourite kneels more often), as quantile grids the sampler draws from.
    qb_ids = set(roster.loc[roster.position == "QB", "gsis_id"].dropna())
    qy = rushes[rushes.rusher_player_id.isin(qb_ids)].rushing_yards.dropna().values
    qb_resid = np.quantile(qy - qy.mean(), np.linspace(0, 1, RESID_QUANTILES))
    kneels = pbp[(pbp.play_type == "qb_kneel") & pbp.rusher_player_id.notna()]
    kn = kneels.groupby(["game_id", "posteam"]).rushing_yards.sum()
    kneel_rows = []
    for _, r in g.iterrows():
        if pd.isna(r.spread_line):
            continue
        for team, own in ((r.home_team, r.spread_line), (r.away_team, -r.spread_line)):
            kneel_rows.append({"spread": float(own), "yds": float(kn.get((r.game_id, team), 0.0))})
    kr = pd.DataFrame(kneel_rows)
    edges = list(KNEEL_SPREAD_EDGES)
    kr["bucket"] = np.digitize(kr.spread, edges)
    kneel_grids = [np.round(np.quantile(kr[kr.bucket == b].yds, np.linspace(0, 1, KNEEL_QUANTILES)), 3).tolist()
                   for b in range(len(edges) + 1)]
    # for a game priced before any spread is posted: every team-game, any spread
    kneel_pooled = np.round(np.quantile(kr.yds, np.linspace(0, 1, KNEEL_QUANTILES)), 3).tolist()
    print(f"QB carries: {len(qy)} (ypc {qy.mean():.2f}); kneel yards per team-game by spread bucket: "
          + ", ".join(f"{np.mean(gr):+.2f}" for gr in kneel_grids), file=sys.stderr)

    pts = g.home_score.sum() + g.away_score.sum()
    td_per_pt = float((tw.rush_td.sum() + tw.pass_td.sum()) / pts)
    # Fraction of TDs scored on plays starting inside the 10. The rest are long
    # touchdowns, which the goal-line allocation cannot see. Verified 2025: 42% of all
    # offensive TDs, 52% of passing TDs, came from outside the 10.
    pass_td_all = passes[passes.pass_touchdown == 1]; rush_td_all = rushes[rushes.rush_touchdown == 1]
    f_pass_in10 = float((pass_td_all.yardline_100 <= 10).mean())
    f_rush_in10 = float((rush_td_all.yardline_100 <= 10).mean())

    # ---- team volume dispersion (for the joint per-sim team-target/carry draw) ----
    def nb_dispersion_pooled(counts):
        mean, var = counts.mean(), counts.var()
        return float(mean**2 / (var - mean)) if var > mean else 30.0
    r_team_targets = nb_dispersion_pooled(tw.targets.values)
    r_team_carries = nb_dispersion_pooled(tw.carries.values)
    league_pass_rate = float(tw.targets.sum() / (tw.targets.sum() + tw.carries.sum()))
    league_plays = float((tw.targets + tw.carries).mean())
    print(f"team volume dispersion: targets r={r_team_targets:.2f}, carries r={r_team_carries:.2f}", file=sys.stderr)
    print(f"league pass rate: {league_pass_rate:.3f}, plays/game: {league_plays:.1f}", file=sys.stderr)

    # ---- market->environment coefficients, fit on this season ----
    # Regress team plays and pass rate on the team's own spread and the game total.
    # Replaces a hand-set 0.015-per-7-points pass-rate shift. Reporting R^2 matters:
    # if the market explains almost none of the variance in team volume, a
    # market-anchored environment cannot help much, and that is the honest result.
    _rows = []
    for _, r in g.iterrows():
        for team, is_home in [(r.home_team, 1), (r.away_team, 0)]:
            # the team's own spread: nflverse spread_line is the HOME side's and
            # POSITIVE when home is favoured, so this is positive = favoured
            sp = r.spread_line if is_home else -r.spread_line
            t_ = tw[(tw.team == team) & (tw.week == r.week)]
            if len(t_) and pd.notna(r.spread_line) and pd.notna(r.total_line):
                pl = float(t_.targets.iloc[0] + t_.carries.iloc[0])
                _rows.append((sp, float(r.total_line), pl, float(t_.targets.iloc[0]) / pl))
    mkt_fit = {}
    if len(_rows) > 50:
        _d = np.array(_rows)
        A = np.c_[np.ones(len(_d)), _d[:, 0], _d[:, 1]]
        for j, nm in [(2, "plays"), (3, "pass_rate")]:
            y = _d[:, j]
            b, *_ = np.linalg.lstsq(A, y, rcond=None)
            pred = A @ b
            r2 = float(1 - ((y - pred) ** 2).sum() / ((y - y.mean()) ** 2).sum())
            mkt_fit[nm] = {"intercept": float(b[0]), "per_spread_pt": float(b[1]),
                           "per_total_pt": float(b[2]), "r2": r2, "n": int(len(_d))}
            print(f"market->{nm}: {b[0]:.4f} {b[1]:+.5f}*spread {b[2]:+.5f}*total  R2={r2:.4f}", file=sys.stderr)

    # ---- opponent efficiency table ----
    opp = M.build_opponent_table(pbp, roles)
    opp.to_csv(out / f"priors_{S}_opponent.csv", index=False)
    print(f"opponent table: {len(opp)} team/posgroup/metric rows", file=sys.stderr)

    # ---- per-rate K0, tuned on a held-out fold within the SAME season (weeks
    # 5-6 fit, 7-8 score), by minimising out-of-sample squared error of the RATE
    # ITSELF -- not a full CRPS resimulation per candidate, which would require a
    # combinatorial grid across 5 rates. Same fit/score split as the round-4
    # dispersion and K0 tuning, generalised per rate. ----
    def tune_rate_k0(df, own_col, prior_col, num_c, den_c, candidates, n_col):
        best_k0, best_mse = candidates[0], np.inf
        score = df[df.week.isin([7, 8])]
        for k0 in candidates:
            errs = []
            for _, r in score.iterrows():
                pred = M.blend(r[own_col], r[n_col], r[prior_col], k0)   # n in OPPORTUNITY units
                if pd.isna(pred) or r[den_c] <= 0:
                    continue
                actual = r[num_c] / r[den_c]
                errs.append((pred - actual) ** 2)
            mse = float(np.mean(errs)) if errs else np.inf
            if mse < best_mse:
                best_k0, best_mse = k0, mse
        return best_k0, best_mse

    slot_ypt_mean = rs.groupby("slot").ypt.mean()
    slot_ypc_mean = rs.groupby("slot").ypc.mean()
    act_lookup = set(roster[roster.status == "ACT"].set_index(["week", "team", "gsis_id"]).index)
    rs_act = rs[[(w, t, p) in act_lookup for w, t, p in zip(rs.week, rs.team, rs.gsis_id)]]
    tune_rows = []
    for (team, pid), grp in rs[rs.week.isin([5, 6, 7, 8])].groupby(["team", "gsis_id"]):
        grp = grp.sort_values("week")
        for _, row in grp.iterrows():
            prior_games = rs_act[(rs_act.team == team) & (rs_act.gsis_id == pid) & (rs_act.week < row.week)]
            n_prior = len(prior_games)
            slot = row.slot
            def rate(num, den):
                d = prior_games[den].sum()
                return prior_games[num].sum() / d if d > 0 else np.nan
            def nopp(den): return float(prior_games[den].sum())
            tune_rows.append(dict(week=row.week, n_prior=n_prior,
                n_ts=nopp("targets_team"), n_cr=nopp("targets"), n_ypt=nopp("targets"),
                n_rs=nopp("carries_team"), n_ypc=nopp("carries"),
                own_ts=rate("targets", "targets_team"),
                prior_ts=(slot_mean.loc[slot, "target_share"] if slot in slot_mean.index else np.nan),
                own_cr=rate("receptions", "targets"),
                prior_cr=(slot_mean.loc[slot, "catch_rate"] if slot in slot_mean.index else np.nan),
                own_ypt=rate("rec_yards", "targets"), prior_ypt=slot_ypt_mean.get(slot, np.nan),
                own_rs=rate("carries", "carries_team"),
                prior_rs=(slot_mean.loc[slot, "rush_share"] if slot in slot_mean.index else np.nan),
                own_ypc=rate("rush_yards", "carries"), prior_ypc=slot_ypc_mean.get(slot, np.nan),
                targets=row.targets, targets_team=row.targets_team,
                receptions=row.receptions, rec_yards=row.rec_yards,
                carries=row.carries, carries_team=row.carries_team, rush_yards=row.rush_yards))
    tune_df = pd.DataFrame(tune_rows)
    # K0 in OPPORTUNITY units (team targets for shares, player targets for catch rate /
    # ypt, carries for ypc). Wide log-spaced grid; an edge hit is reported as such.
    CANDS = [5, 10, 20, 40, 80, 160, 320, 640, 1280, 2560]
    k0_fit = {}
    for name, own_c, prior_c, num_c, den_c, n_col in [
        ("target_share", "own_ts", "prior_ts", "targets", "targets_team", "n_ts"),
        ("catch_rate", "own_cr", "prior_cr", "receptions", "targets", "n_cr"),
        ("ypt", "own_ypt", "prior_ypt", "rec_yards", "targets", "n_ypt"),
        ("rush_share", "own_rs", "prior_rs", "carries", "carries_team", "n_rs"),
        ("ypc", "own_ypc", "prior_ypc", "rush_yards", "carries", "n_ypc"),
    ]:
        k0, mse = tune_rate_k0(tune_df, own_c, prior_c, num_c, den_c, CANDS, n_col)
        k0_fit[name] = k0
        edge = " (GRID EDGE -- treat as unresolved)" if k0 in (CANDS[0], CANDS[-1]) else ""
        print(f"K0[{name}] = {k0} opportunities  (held-out MSE {mse:.5f}){edge}", file=sys.stderr)
    # i10 shares reuse the rush_share/target_share constants -- too few goal-line
    # opportunities in a half-season fold to tune independently without noise.
    for name, k0 in list(k0_fit.items()):
        if k0 in (CANDS[0], CANDS[-1]):
            k0_fit[name] = 80   # unresolved on this sample; documented default (~2-3 games of opportunities)
            print(f"  K0[{name}] was at grid edge; set to default 80", file=sys.stderr)
    # i10 shares reuse the share constants but must be rescaled to goal-line volume: K0 is in
    # opportunity units and a team has ~5 goal-line carries per game vs ~27 carries. Reusing 40
    # unscaled made goal-line share shrink ~5x SLOWER than rush share (a reviewer caught this
    # from an RB2 projected at 19% of goal-line carries on 0-of-5 this season).
    _i10c = float(tw.i10_carries.mean()) / max(float(tw.carries.mean()), 1e-6)
    _i10t = float(tw.i10_targets.mean()) / max(float(tw.targets.mean()), 1e-6)
    k0_fit["i10_target_share"] = max(2, round(k0_fit["target_share"] * _i10t))
    k0_fit["i10_carry_share"] = max(2, round(k0_fit["rush_share"] * _i10c))
    print(f"K0[i10_target_share] = {k0_fit['i10_target_share']}  K0[i10_carry_share] = {k0_fit['i10_carry_share']} (rescaled to goal-line volume)", file=sys.stderr)

    params = {
        "season": S, "K0": K0_DEFAULT, "k0_per_rate": k0_fit, "k0_units": "opportunities", "r_clamp": R_CLAMP,
        "team_volume_dispersion": {"targets_r": r_team_targets, "carries_r": r_team_carries},
        "league_pass_rate": league_pass_rate, "league_plays_per_game": league_plays,
        "market_env_fit": mkt_fit,
        "receptions_dispersion": rec_fit, "carries_dispersion": rush_fit,
        "shape_ypc_per_catch": shape_ypc,
        "league_mean_ypc": float(ry.mean()),
        "carry_residual_quantiles": [round(float(x), 4) for x in resid],
        "qb_mean_ypc": float(qy.mean()),
        "qb_carry_residual_quantiles": [round(float(x), 4) for x in qb_resid],
        # the team's own pregame spread, POSITIVE = favoured (nflverse's
        # spread_line is the home side's); grid b covers [edges[b-1], edges[b])
        "qb_kneel_yards_by_spread": {"edges": edges, "grids": kneel_grids, "pooled": kneel_pooled},
        "league_td_per_point": td_per_pt,
        "pass_td_frac_inside10": f_pass_in10, "rush_td_frac_inside10": f_rush_in10,
        "note": ("Built by build_priors.py. Rates are prior-season season-long and are used "
                 "as individual priors shrunk toward the slot prior, then blended toward "
                 "current-season observation with K0. shape_ypc is PER CATCH, not per game."),
    }
    json.dump(params, open(out / f"priors_{S}_params.json", "w"), indent=1)

    print(f"\nwrote to {out}:", file=sys.stderr)
    for f in sorted(out.glob(f"priors_{S}_*")):
        print(f"  {f.name}  {f.stat().st_size/1024:.0f} KB", file=sys.stderr)
    print(f"\nreceptions dispersion: log r = {rec_fit['a']:.4f} + {rec_fit['b']:.4f} log(mu)", file=sys.stderr)
    print(f"carries dispersion:    log r = {rush_fit['a']:.4f} + {rush_fit['b']:.4f} log(mu)", file=sys.stderr)
    print(f"per-catch gamma shape: {shape_ypc:.4f}   league ypc: {ry.mean():.3f}", file=sys.stderr)
    print(f"league TD per point:   {td_per_pt:.5f}", file=sys.stderr)


if __name__ == "__main__":
    main()
