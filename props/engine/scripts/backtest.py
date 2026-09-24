#!/usr/bin/env python3
"""Backtest the shared model core (model.py): receptions, receiving yards and
rushing yards, walk-forward, graded on the joint sampler the live scorer runs.
Same rigor as the round-4 validation: bye exclusion, ACT/INA-only population,
INA voided (not scored as zero), per-arm dispersion, full-chain determinism.

TWO MODES.

Harness (docs/plans/2026-09-24-yardage-harness.md), the standard every
yardage change is judged by:

  python backtest.py --seasons 2022,2023,2024,2025 --tune 2022,2023 --test 2024,2025 \\
                     --report ../../../reports/yardage_harness

  Each season S is predicted from priors built from S-1 (the file the scorer
  would have had; built on demand into --priors-dir), with the live scorer's
  settings: team volume blended with the prior season then drift-corrected,
  team-level opponent adjustment (fixed, k0=150) on catch rate, ypt and ypc,
  and the dispersions and carry-yard grid from the priors. Nothing is fitted
  on the season under test. Weeks 2-18 are scored and reported as 2-4 (the
  early-season prior blend) and 5-18.

Single season (the round-4..9 protocol, unchanged, so old results reproduce):

  python backtest.py --season 2025 --train-weeks 5,6,7,8 --test-weeks 9-18
                     --env history|market [--no-opponent] [--out DIR]

Data comes from nflverse, cached in NFL_BACKTEST_CACHE (default: the system
temp dir /nflbt, shared with td_backtest.py).
"""
import argparse, json, os, re, subprocess, sys, tempfile
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.special import gammaln

sys.path.insert(0, str(Path(__file__).resolve().parent))
import model as M

HERE = Path(__file__).resolve().parent
RES = HERE.parent / "resources"
CACHE = Path(os.environ.get("NFL_BACKTEST_CACHE", Path(tempfile.gettempdir()) / "nflbt"))
NV = "https://github.com/nflverse/nflverse-data/releases/download"
GAMES = "https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv"
N = 1000

# market key -> (actual column, label, synthetic-line offsets for the reliability table)
MARKETS = {"rec": ("act_receptions", "receptions", [0.5, 1.5, 2.5, 3.5]),
           "yds": ("act_rec_yards", "receiving yards", [5, 10, 15, 20, 30]),
           "rush": ("act_rush_yards", "rushing yards", [5, 10, 15, 20, 30])}
# THE LIVE SCORER'S OPPONENT SETTINGS (score_game.py section 5): team level, fixed
# shrinkage k0=150 plays, applied to catch rate, ypt and ypc. The single-season
# defaults below (posgrp, k0=1000) are the round-5 ones, kept for reproduction.
LIVE_OPP = dict(level="team", mode="fixed", k0=150.0, metrics="catch_rate,ypt,ypc")
EARLY_WEEKS = (2, 3, 4)
BIAS_PIT, BIAS_RATIO = 0.03, 0.05
# WIDTH (added 2026-09-24 after the first harness run: all three markets beat
# baseline A and were unbiased on average, yet 23-31% of outcomes fell outside
# the model's 10-90 range and an 85% Over won ~77-80%). A distribution that is
# right on average but too narrow overstates every edge, so width is part of
# the bar: outcomes outside p10-p90 within 0.20 +/- WIDTH_TOL, and every
# 60-90% reliability bucket on weeks 5-18 within RELIABILITY_TOL.
WIDTH_TARGET, WIDTH_TOL, RELIABILITY_TOL = 0.20, 0.03, 0.03
RELIABILITY_BUCKETS = ("60-70", "70-80", "80-90")


def parse_weeks(s):
    if not s:
        return []
    if "-" in s:
        a, b = s.split("-"); return list(range(int(a), int(b) + 1))
    return [int(x) for x in s.split(",")]


def nb_mle(mu, y, r_clamp):
    def nll(p):
        a, b = p
        r = np.clip(np.exp(a + b * np.log(np.maximum(mu, 1e-6))), *r_clamp)
        q = r / (r + mu)
        return -np.sum(gammaln(y + r) - gammaln(r) - gammaln(y + 1) + r * np.log(q) + y * np.log1p(-q))
    c0 = minimize(lambda p: nll([p[0], 0.0]), [1.0], method="Nelder-Mead")
    res = minimize(nll, [c0.x[0], 0.0], method="Nelder-Mead", options={"xatol": 1e-6, "fatol": 1e-6, "maxiter": 5000})
    return {"a": float(res.x[0]), "b": float(res.x[1])}


def re_first_letters(slot):
    m = re.match(r"[A-Z]+", str(slot))
    return m.group(0) if m else "OTHER"


def dl(url, name):
    CACHE.mkdir(parents=True, exist_ok=True)
    dest = CACHE / name
    if not dest.exists() or dest.stat().st_size == 0:
        import urllib.request
        print(f"  fetching {name}", file=sys.stderr)
        urllib.request.urlretrieve(url, dest)
    return dest


def ensure_priors(season, priors_dir, build):
    """priors_{season}_*.* in priors_dir, built by build_priors.py when missing
    and `build` is set. The harness builds every season it needs with the
    current builder rather than mixing in committed files built by older code."""
    f = Path(priors_dir) / f"priors_{season}_params.json"
    if f.exists():
        return f
    if not build:
        sys.exit(f"priors_{season}_params.json is missing from {priors_dir}: a walk-forward test of "
                 f"{season + 1} needs the priors the live scorer would have had, which are built from "
                 f"{season}. Run build_priors.py --season {season}, or pass --build-priors.")
    print(f"building priors for {season} into {priors_dir}", file=sys.stderr)
    subprocess.run([sys.executable, str(HERE / "build_priors.py"), "--season", str(season),
                    "--out", str(priors_dir), "--workdir", str(CACHE / "priors_work")], check=True)
    return f


def crps_block(samples, y_arr):
    """Vectorized unbiased empirical CRPS across all players at once."""
    n = samples.shape[1]
    t1 = np.abs(samples - y_arr[:, None]).mean(axis=1)
    ss_ = np.sort(samples, axis=1)
    i = np.arange(1, n + 1)
    t2 = (2.0 / (n * n)) * ((2 * i - n - 1) * ss_).sum(axis=1)
    return t1 - 0.5 * t2


def run_season(args, S, TRAIN, TEST, OUT, live):
    """One season, walk-forward. Returns (per-player-week results, meta)."""
    rng = np.random.default_rng(20260917 + (S - 2025 if live else 0))
    opp = dict(LIVE_OPP) if live else dict(level=args.opp_level, mode=args.opp_mode, k0=args.opp_k0,
                                           metrics=args.opp_metrics)
    dispersion = args.dispersion or ("prior" if live else "train")
    print(f"season={S} env={args.env} opponent={args.opponent} ({opp['level']}, k0={opp['k0']:g}) "
          f"historical_blend={args.historical_blend} dispersion={dispersion} live={live}", file=sys.stderr)

    # ---- self-contained data build (round 7): derive every frame from nflverse for
    # ANY season, cached so repeat runs are instant. ----
    frames_cache = OUT / f"_frames_{S}.pkl"
    pbp_full = pd.read_csv(dl(f"{NV}/pbp/play_by_play_{S}.csv.gz", f"pbp_{S}.csv.gz"), low_memory=False)
    pbp_full = pbp_full[pbp_full.season_type == "REG"]
    if frames_cache.exists():
        games, gm, roles, roster, rec, rush, twt, twc = pd.read_pickle(frames_cache)
    else:
        games_all = pd.read_csv(dl(GAMES, "games.csv"))
        games = games_all[(games_all.season == S) & (games_all.game_type == "REG")].copy()
        games["game_id2"] = games.gameday.astype(str) + "_" + games.home_team + "_" + games.away_team
        gm = pd.concat([games[["week", "home_team", "game_id2"]].rename(columns={"home_team": "team"}),
                        games[["week", "away_team", "game_id2"]].rename(columns={"away_team": "team"})],
                       ignore_index=True).drop_duplicates(["team", "week"]).rename(columns={"game_id2": "game_id"})
        roster = pd.read_csv(dl(f"{NV}/weekly_rosters/roster_weekly_{S}.csv", f"roster_weekly_{S}.csv"),
                             low_memory=False)
        roster = roster[roster.season == S][["week", "team", "gsis_id", "full_name", "position", "status"]].drop_duplicates(
            ["week", "team", "gsis_id"])
        # pre-game depth-chart slot per team-week (latest snapshot strictly before kickoff)
        dcf = pd.read_csv(dl(f"{NV}/depth_charts/depth_charts_{S}.csv", f"dc_{S}.csv"), low_memory=False)
        kick = {}
        for _, r_ in games.iterrows():
            if pd.isna(r_.gametime):
                continue
            naive = pd.Timestamp(f"{r_.gameday} {r_.gametime}")
            off = 4 if pd.Timestamp(f"{naive.year}-03-15") <= naive < pd.Timestamp(f"{naive.year}-11-01") else 5
            kt = (naive + pd.Timedelta(hours=off)).tz_localize("UTC")
            kick[(r_.home_team, r_.week)] = kt; kick[(r_.away_team, r_.week)] = kt
        roles = M.normalize_depth_charts(dcf, kick)

        psz = pbp_full[(pbp_full.play_type == "pass") & pbp_full.receiver_player_id.notna()]
        rsz = pbp_full[(pbp_full.play_type == "run") & (pbp_full.qb_kneel != 1) & pbp_full.rusher_player_id.notna()]
        twt = psz.groupby(["posteam", "week"]).size().rename("team_targets").reset_index().rename(columns={"posteam": "team"})
        twc = rsz.groupby(["posteam", "week"]).size().rename("team_carries").reset_index().rename(columns={"posteam": "team"})
        rec = psz.groupby(["posteam", "week", "receiver_player_id"]).agg(
            targets=("play_id", "size"), receptions=("complete_pass", "sum"),
            rec_yards=("receiving_yards", "sum")).reset_index().rename(
            columns={"posteam": "team", "receiver_player_id": "gsis_id"}).merge(twt, on=["team", "week"])
        rush = rsz.groupby(["posteam", "week", "rusher_player_id"]).agg(
            carries=("play_id", "size"), rush_yards=("rushing_yards", "sum")).reset_index().rename(
            columns={"posteam": "team", "rusher_player_id": "gsis_id"}).merge(twc, on=["team", "week"])
        rec["rec_yards"] = rec["rec_yards"].fillna(0.0); rush["rush_yards"] = rush["rush_yards"].fillna(0.0)
        pd.to_pickle((games, gm, roles, roster, rec, rush, twt, twc), frames_cache)

    if "spread_line" not in games.columns:
        sys.exit("games.csv has no spread_line/total_line -- cannot backtest --env market")

    # THE PRIOR SEASON, NOT THIS ONE.
    #
    # build_priors.py --season S builds priors_S FROM season S -- the season
    # under test. Reading it here would fit the shrinkage constants, league
    # rates, dispersions and market_env_fit on data that includes the test
    # weeks. The live scorer uses PRIOR = SEASON - 1; so does this.
    PRIOR = S - 1
    pdir = Path(args.priors_dir) if args.priors_dir else RES
    P0 = json.load(open(ensure_priors(PRIOR, pdir, args.build_priors)))
    pri_players = pd.read_csv(pdir / f"priors_{PRIOR}_players.csv").set_index("gsis_id")
    pri_teams = pd.read_csv(pdir / f"priors_{PRIOR}_teams.csv", index_col=0)
    print(f"priors: {PRIOR} (the season before the one under test), "
          f"{len(pri_players)} players", file=sys.stderr)
    K0R = P0.get("k0_per_rate", M.DEFAULT_K0)
    K0_TEAM = float(P0.get("K0", 4.0))
    league_pass_rate = P0.get("league_pass_rate", 0.55)
    MKT_FIT = P0.get("market_env_fit", {})
    league_plays = P0.get("league_plays_per_game", 64.0)
    carry_resid = np.array(P0["carry_residual_quantiles"])
    ypc_default = float(P0.get("league_mean_ypc", 4.2)) if live else 4.2

    role_lookup = roles.drop_duplicates("gsis_id", keep="first").set_index("gsis_id")["slot"]

    def make_population(weeks):
        played = set(zip(gm.team, gm.week))
        pop_rows = []
        for team in sorted(set(gm.team)):
            team_rec = rec[rec.team == team]; team_rush = rush[rush.team == team]
            for W in weeks:
                if (team, W) not in played:
                    continue
                elig = set(roles[(roles.team == team) & (roles.week == W)].gsis_id)
                for pid, g_ in team_rec[team_rec.week < W].groupby("gsis_id"):
                    last4 = g_.sort_values("week").tail(4)
                    if last4.team_targets.sum() > 0 and last4.targets.sum() / last4.team_targets.sum() >= 0.10:
                        elig.add(pid)
                for pid, g_ in team_rush[team_rush.week < W].groupby("gsis_id"):
                    last4 = g_.sort_values("week").tail(4)
                    if last4.team_carries.sum() > 0 and last4.carries.sum() / last4.team_carries.sum() >= 0.20:
                        elig.add(pid)
                for pid in sorted(elig):
                    st = roster[(roster.week == W) & (roster.team == team) & (roster.gsis_id == pid)]
                    status = st.status.iloc[0] if len(st) else None
                    if status not in ("ACT", "INA"):
                        continue
                    pop_rows.append({"team": team, "week": W, "gsis_id": pid, "roster_status": status})
        return pd.DataFrame(pop_rows).drop_duplicates(["team", "week", "gsis_id"])

    def make_features(pop):
        rec_agg = rec.groupby(["team", "week", "gsis_id"], as_index=False).agg(
            targets=("targets", "sum"), receptions=("receptions", "sum"), rec_yards=("rec_yards", "sum"))
        rush_agg = rush.groupby(["team", "week", "gsis_id"], as_index=False).agg(
            carries=("carries", "sum"), rush_yards=("rush_yards", "sum"))
        rec_key = rec_agg.set_index(["team", "week", "gsis_id"])
        rush_key = rush_agg.set_index(["team", "week", "gsis_id"])
        act_set = set(roster[roster.status == "ACT"].set_index(["week", "team", "gsis_id"]).index)
        played_weeks = gm.groupby("team")["week"].apply(lambda s: sorted(s)).to_dict()
        tt_by_tw = twt.set_index(["team", "week"])["team_targets"]
        tc_by_tw = twc.set_index(["team", "week"])["team_carries"]

        rows = []
        for (team, W), grp in pop.groupby(["team", "week"]):
            prior_weeks_played = [w for w in played_weeks[team] if w < W]
            for pid in grp.gsis_id:
                elig_weeks = [w for w in prior_weeks_played if (w, team, pid) in act_set]
                window = elig_weeks[-4:]
                tg = rc = ry = tt = ca = ry2 = cc = 0.0
                for w in window:
                    tt += tt_by_tw.get((team, w), 0.0); cc += tc_by_tw.get((team, w), 0.0)
                    if (team, w, pid) in rec_key.index:
                        rr_ = rec_key.loc[(team, w, pid)]; tg += rr_.targets; rc += rr_.receptions; ry += rr_.rec_yards
                    if (team, w, pid) in rush_key.index:
                        uu_ = rush_key.loc[(team, w, pid)]; ca += uu_.carries; ry2 += uu_.rush_yards
                n_games = len(window)
                slot = role_lookup.get(pid, "PROXY")
                a_ = rec_key.loc[(team, W, pid)] if (team, W, pid) in rec_key.index else None
                u_ = rush_key.loc[(team, W, pid)] if (team, W, pid) in rush_key.index else None
                rows.append(dict(team=team, week=W, gsis_id=pid, slot=slot,
                    n_games_prior=n_games, n_tt=tt, n_tg=tg, n_cc=cc, n_ca=ca,
                    own_ts=(tg / tt if tt > 0 else np.nan), own_cr=(rc / tg if tg > 0 else np.nan),
                    own_ypt=(ry / tg if tg > 0 else np.nan),
                    own_rs=(ca / cc if cc > 0 else np.nan), own_ypc=(ry2 / ca if ca > 0 else np.nan),
                    act_targets=int(a_.targets) if a_ is not None else 0,
                    act_receptions=float(a_.receptions) if a_ is not None else 0.0,
                    act_rec_yards=float(a_.rec_yards) if a_ is not None else 0.0,
                    act_carries=int(u_.carries) if u_ is not None else 0,
                    act_rush_yards=float(u_.rush_yards) if u_ is not None else 0.0))
        feat = pd.DataFrame(rows)
        feat = feat.merge(pop[["team", "week", "gsis_id", "roster_status"]], on=["team", "week", "gsis_id"], how="left")
        return feat

    def slot_priors_expanding(weeks):
        # Slot priors must include ZERO-target weeks. `rec`/`rush` only contain player-weeks
        # with >=1 stat, so a mean over them is a mean over "weeks he was involved", which
        # inflates every prior (bias diagnostic: actual/model mean 0.92 before this fix).
        # Start from `roles` (every slot player, every week) and left-join stats.
        base = roles[["team", "week", "gsis_id", "slot"]].merge(
            twt, on=["team", "week"], how="left").merge(twc, on=["team", "week"], how="left")
        rs_ = base.merge(rec[["team", "week", "gsis_id", "targets", "receptions", "rec_yards"]],
                         on=["team", "week", "gsis_id"], how="left").fillna({"targets": 0, "receptions": 0, "rec_yards": 0})
        ru_ = base.merge(rush[["team", "week", "gsis_id", "carries", "rush_yards"]],
                         on=["team", "week", "gsis_id"], how="left").fillna({"carries": 0, "rush_yards": 0})
        rs_ = rs_.dropna(subset=["team_targets"]); ru_ = ru_.dropna(subset=["team_carries"])
        out = {}
        for W in weeks:
            p_ = rs_[rs_.week < W].copy()
            p_["ts"] = p_.targets / p_.team_targets; p_["cr"] = np.where(p_.targets > 0, p_.receptions / p_.targets, np.nan)
            p_["ypt"] = np.where(p_.targets > 0, p_.rec_yards / p_.targets, np.nan)
            r_ = ru_[ru_.week < W].copy()
            r_["rs"] = r_.carries / r_.team_carries; r_["ypc"] = np.where(r_.carries > 0, r_.rush_yards / r_.carries, np.nan)
            out[W] = {"ts": p_.groupby("slot").ts.mean(), "cr": p_.groupby("slot").cr.mean(),
                      "ypt": p_.groupby("slot").ypt.mean(), "rs": r_.groupby("slot").rs.mean(),
                      "ypc": r_.groupby("slot").ypc.mean()}
        return out

    def team_hist_env(weeks):
        """Team volume environment. The single-season protocol uses the current
        season's expanding mean. The live scorer blends it with the PRIOR season's
        team rate by games played (K0 in the priors) before the drift correction,
        which is what carries weeks 2-4; live mode does the same. Expanding means
        lag within-season league drift (+3.4% in 2024, -4.2% in 2025); the
        league-wide drift ratio corrects the level."""
        out = {}
        prior_all = twt.merge(twc, on=["team", "week"])
        for W in weeks:
            pa = prior_all[prior_all.week < W]
            if args.env_window > 0:
                pa = pa.sort_values("week").groupby("team").tail(args.env_window)
            m_ = pa.groupby("team")[["team_targets", "team_carries"]].mean()
            if live:
                n_ = pa.groupby("team").size()
                teams = sorted(set(m_.index) | set(pri_teams.index))
                m_ = pd.DataFrame({
                    "team_targets": [M.blend(m_.team_targets.get(t, np.nan), float(n_.get(t, 0)),
                                             pri_teams.targets.get(t, np.nan), K0_TEAM) for t in teams],
                    "team_carries": [M.blend(m_.team_carries.get(t, np.nan), float(n_.get(t, 0)),
                                             pri_teams.carries.get(t, np.nan), K0_TEAM) for t in teams]},
                    index=teams)
            if args.drift_correct and args.env_window == 0:
                dr = M.league_drift_ratio(prior_all, W, recent_games=args.drift_recent)
                m_ = m_.assign(team_targets=m_.team_targets * dr["targets"],
                               team_carries=m_.team_carries * dr["carries"])
            out[W] = m_
        return out

    def opponent_tables_expanding(weeks):
        out = {}
        for W in sorted(set(weeks)):
            sub = pbp_full[pbp_full.week < W]
            out[W] = M.build_opponent_table(sub, roles[roles.week < W]) if len(sub) else pd.DataFrame(
                columns=["team", "posgrp", "metric", "n", "value", "league"])
        return out

    def opponent_of_row(team, week):
        row = gm[(gm.team == team) & (gm.week == week)]
        if row.empty:
            return None
        gid = row.game_id.iloc[0]
        other = gm[(gm.game_id == gid) & (gm.team != team)]
        return other.team.iloc[0] if len(other) else None

    def fit_market_slopes(train_weeks):
        """Regress team pass rate on the team's own signed spread, and team plays on
        game total, over the training weeks only."""
        tw_ = twt.merge(twc, on=["team", "week"]); tw_ = tw_[tw_.week.isin(train_weeks)].copy()
        tw_["plays"] = tw_.team_targets + tw_.team_carries; tw_["pr"] = tw_.team_targets / tw_.plays
        gl = games[games.week.isin(train_weeks)]
        rows_ = []
        for _, g_ in gl.iterrows():
            for team, own_spread in [(g_.home_team, g_.spread_line), (g_.away_team, -g_.spread_line)]:
                r_ = tw_[(tw_.team == team) & (tw_.week == g_.week)]
                if len(r_): rows_.append({"pr": float(r_.pr.iloc[0]), "plays": float(r_.plays.iloc[0]),
                                         "spread": float(own_spread), "total": float(g_.total_line)})
        d_ = pd.DataFrame(rows_)
        b_pr = np.polyfit(d_.spread, d_.pr, 1)[0]
        b_pl = np.polyfit(d_.total, d_.plays, 1)[0]
        print(f"market slopes (train): pass_rate/spread pt = {b_pr:+.4f}, plays/total pt = {b_pl:+.3f}, N={len(d_)}", file=sys.stderr)
        return float(b_pr), float(b_pl), float(d_.total.mean())

    def build_shrunk(pop, feat, weeks, env_mode):
        slot_p = slot_priors_expanding(weeks)
        hist_env = team_hist_env(weeks)
        opp_tabs = opponent_tables_expanding(weeks) if args.opponent else None
        game_lines = games.set_index(["home_team", "away_team", "week"])
        opp_team_of = {(t, w): opponent_of_row(t, w) for t, w in pop[["team", "week"]].drop_duplicates().itertuples(index=False)}
        mets = set(opp["metrics"].split(","))

        rows = []
        for _, r in feat.iterrows():
            W, slot = r.week, r.slot
            sp = slot_p[W]
            def gv(d, k, default=np.nan):
                return float(d.get(k, default)) if k in d.index else default
            # THE SAME TWO-STAGE BLEND THE SCORER RUNS (model.blended_rate):
            # prior-season own rate -> slot prior -> this season's partial
            # evidence. n is in OPPORTUNITY units on both sides, matching how K0
            # was tuned: team targets for shares, own targets for catch rate and
            # ypt, carries for ypc.
            pri = pri_players.loc[r.gsis_id] if r.gsis_id in pri_players.index else None

            def two_stage(pri_col, n_col, slot_key, default, k0_key, k0_default,
                          cur, cur_n, scale_role=False):
                # The ablation drops stage one by giving it nothing to shrink
                # from, which leaves blend() returning the slot prior -- exactly
                # the one-stage behaviour, through the same code path.
                if args.historical_blend:
                    own_pri = float(pri[pri_col]) if (pri is not None and pd.notna(pri[pri_col])) else np.nan
                    n_pri = float(pri[n_col]) if (pri is not None and pd.notna(pri[n_col])) else 0.0
                else:
                    own_pri, n_pri = np.nan, 0.0
                val, _chain = M.blended_rate(
                    own_pri, n_pri, gv(sp[slot_key], slot, default),
                    K0R.get(k0_key, k0_default),
                    cur_rate=cur, cur_den=cur_n, scale_role=scale_role)
                return val

            ts = two_stage("target_share", "team_targets_n", "ts", np.nan,
                           "target_share", 80, r.own_ts, r.n_tt)
            cr = two_stage("catch_rate", "targets_n", "cr", 0.6,
                           "catch_rate", 40, r.own_cr, r.n_tg)
            ypt = two_stage("ypt", "targets_n", "ypt", 7.0,
                            "ypt", 160, r.own_ypt, r.n_tg)
            rs_ = two_stage("rush_share", "team_carries_n", "rs", 0.03,
                            "rush_share", 20, r.own_rs, r.n_cc)
            ypc = two_stage("ypc", "carries_n", "ypc", ypc_default,
                            "ypc", 80, r.own_ypc, r.n_ca)

            opp_team = opp_team_of.get((r.team, W))
            if args.opponent and opp_team:
                posgrp = "ALL" if opp["level"] == "team" else re_first_letters(slot)
                otab = opp_tabs[W]
                if len(otab):
                    om = lambda met: M.opponent_multiplier(otab, opp_team, posgrp, met, k0_opp=opp["k0"], mode=opp["mode"])
                    if "catch_rate" in mets: cr = float(np.clip(cr * om("catch_rate"), 0.05, 1.0))
                    if "ypt" in mets: ypt = float(ypt * om("ypt"))
                    if "ypc" in mets: ypc = float(ypc * om("ypc"))

            he = hist_env[W]
            targets_env = float(he.loc[r.team, "team_targets"]) if r.team in he.index else league_plays * league_pass_rate
            carries_env = float(he.loc[r.team, "team_carries"]) if r.team in he.index else league_plays * (1 - league_pass_rate)
            if env_mode == "league":
                # ABLATION: constant league-average volume, no spread/total, no team history.
                targets_env = league_plays * league_pass_rate
                carries_env = league_plays * (1 - league_pass_rate)
            team_pr = targets_env / max(targets_env + carries_env, 1e-6)   # team's own history pass rate
            if env_mode == "market_fit" and opp_team:
                key2 = None
                if (r.team, opp_team, W) in game_lines.index: key2 = (r.team, opp_team, W); is_home2 = True
                elif (opp_team, r.team, W) in game_lines.index: key2 = (opp_team, r.team, W); is_home2 = False
                if key2 is not None:
                    sl, tl = game_lines.loc[key2, ["spread_line", "total_line"]]
                    team_spread = sl if is_home2 else -sl
                    me = M.market_environment_fitted(team_spread, tl, MKT_FIT,
                                                     targets_env + carries_env, team_pr, args.pace_weight)
                    targets_env = me["plays"] * me["pass_rate"]
                    carries_env = me["plays"] * (1 - me["pass_rate"])
            if env_mode == "market" and opp_team:
                key = None
                if (r.team, opp_team, W) in game_lines.index: key = (r.team, opp_team, W); is_home = True
                elif (opp_team, r.team, W) in game_lines.index: key = (opp_team, r.team, W); is_home = False
                if key is not None:
                    spread_line, total_line = game_lines.loc[key, ["spread_line", "total_line"]]
                    spread_home = spread_line if is_home else -spread_line
                    hp, ap_ = (team_pr, league_pass_rate) if is_home else (league_pass_rate, team_pr)
                    mkt = M.market_implied_environment(spread_home, total_line, hp, ap_, targets_env + carries_env,
                                                       pass_rate_slope=MKT_SLOPES[0], plays_slope=MKT_SLOPES[1], league_total=MKT_SLOPES[2])
                    side = mkt["home"] if is_home else mkt["away"]
                    targets_env, carries_env = side["plays"] * side["pass_rate"], side["plays"] * (1 - side["pass_rate"])

            abs_spread = np.nan
            if opp_team:
                for key in [(r.team, opp_team, W), (opp_team, r.team, W)]:
                    if key in game_lines.index:
                        abs_spread = abs(float(game_lines.loc[key, "spread_line"])); break
            rows.append(dict(r, ts=ts, cr=cr, ypt=ypt, rs=rs_, ypc=ypc,
                             team_targets_env=targets_env, team_carries_env=carries_env, abs_spread=abs_spread))
        return pd.DataFrame(rows)

    # Train weeks are needed only for the within-season fits (--dispersion train)
    # and the legacy --env market slopes. Live mode fits nothing on the season.
    need_train = dispersion == "train" or args.env == "market"
    MKT_SLOPES = fit_market_slopes(TRAIN) if args.env == "market" else None

    # Feature caching: population and raw per-player features depend only on the season
    # and week list, NOT on --env / --opponent / K0.
    def cached_features(weeks, label):
        key = f"{S}_{label}_{'-'.join(map(str, weeks))}"
        f = OUT / f"_featcache_{key}.pkl"
        if f.exists():
            return pd.read_pickle(f)
        pop = make_population(weeks); feat = make_features(pop)
        feat.to_pickle(f)
        return feat
    feat_te = cached_features(TEST, "test")
    feat_te = build_shrunk(feat_te[["team", "week", "gsis_id", "roster_status"]], feat_te, TEST, args.env)
    feat_te = feat_te[feat_te.slot != "QB1"].reset_index(drop=True)

    if dispersion == "train":
        feat_tr = cached_features(TRAIN, "train")
        feat_tr = build_shrunk(feat_tr[["team", "week", "gsis_id", "roster_status"]], feat_tr, TRAIN, args.env)
        feat_tr = feat_tr[feat_tr.slot != "QB1"].reset_index(drop=True)
        print(f"train N={len(feat_tr)}  test N={len(feat_te)}", file=sys.stderr)
        tr_act = feat_tr[feat_tr.roster_status == "ACT"]
        mu_rec_tr = np.maximum(tr_act.team_targets_env * tr_act.ts * tr_act.cr.clip(lower=0.05), 0.02).values
        rec_fit = nb_mle(mu_rec_tr, tr_act.act_receptions.values.astype(float), [0.5, 30.0])
        pos = tr_act[tr_act.act_receptions >= 1]
        ks, ss, ws = [], [], []
        for k, g_ in pos.groupby("act_receptions"):
            if len(g_) < 15 or g_.act_rec_yards.var() <= 0: continue
            Y = g_.act_rec_yards.values
            ks.append(k); ss.append((Y.mean()**2)/(k*Y.var())); ws.append(len(g_))
        shape_ypc = float(np.average(ss, weights=ws)) if ss else 1.0
        # TEAM VOLUME DISPERSION, fit on the training weeks only (never priors_S,
        # which is built from the season under test).
        def mom_r(v):
            m_, v_ = v.mean(), v.var()
            return float(m_ ** 2 / (v_ - m_)) if v_ > m_ else 30.0
        r_team_targets = mom_r(twt[twt.week.isin(TRAIN)].team_targets.values.astype(float))
        r_team_carries = mom_r(twc[twc.week.isin(TRAIN)].team_carries.values.astype(float))
    else:
        # LIVE-FAITHFUL: exactly the numbers the scorer reads from priors_{S-1}.
        print(f"test N={len(feat_te)} (dispersion from priors_{PRIOR})", file=sys.stderr)
        rec_fit = P0["receptions_dispersion"]
        shape_ypc = float(P0["shape_ypc_per_catch"])
        tvd = P0.get("team_volume_dispersion", {"targets_r": 30.0, "carries_r": 30.0})
        r_team_targets, r_team_carries = float(tvd["targets_r"]), float(tvd["carries_r"])
    print(f"dispersion: rec r={rec_fit} shape_ypc={shape_ypc:.3f} team targets r={r_team_targets:.2f} "
          f"carries r={r_team_carries:.2f}", file=sys.stderr)

    test_act = feat_te[feat_te.roster_status == "ACT"].reset_index(drop=True)

    def draw_block(mu_arr, ypc_arr, fit):
        """INDEPENDENT per-player draws. Kept only as the marginal comparator:
        it is NOT the generative model the live scorer runs."""
        r_arr = np.clip(np.exp(fit["a"] + fit["b"] * np.log(np.maximum(mu_arr, 1e-6))), 0.5, 30.0)
        p_arr = r_arr / (r_arr + mu_arr)
        rec_ = rng.negative_binomial(r_arr[:, None], p_arr[:, None], size=(len(mu_arr), N)).astype(float)
        shape_tot = np.maximum(np.clip(rec_, 0, 25) * shape_ypc, 1e-6)
        yds = np.where(rec_ > 0, rng.gamma(shape_tot, (np.maximum(ypc_arr, 0.5) / shape_ypc)[:, None]), 0.0)
        return rec_, yds

    def draw_block_joint(frame, shares, crs, ypts):
        """THE LIVE PIPELINE'S DRAW (model.simulate_team_game): one team-volume
        draw per simulation, split across that team's players."""
        rec_ = np.zeros((len(frame), N))
        yds = np.zeros((len(frame), N))
        pos_ = {ix: i for i, ix in enumerate(frame.index)}
        for (team, week), g in frame.groupby(["team", "week"], sort=False):
            tvol = float(g.team_targets_env.iloc[0])
            out, _tt = M.simulate_team_game(
                rng, N, tvol, r_team_targets,
                {ix: float(shares[pos_[ix]]) for ix in g.index},
                {ix: float(crs[pos_[ix]]) for ix in g.index},
                {ix: float(ypts[pos_[ix]]) for ix in g.index},
                shape_ypc)
            for ix, (r_, y_) in out.items():
                rec_[pos_[ix]] = r_
                yds[pos_[ix]] = y_
        return rec_, yds

    def draw_block_rush(frame, shares, ypcs):
        """THE LIVE PIPELINE'S RUSHING DRAW (model.simulate_team_rush): one team
        carries draw per simulation, split across the team's eligible players,
        each carry the player's ypc plus a residual from the prior season's
        league grid."""
        yds = np.zeros((len(frame), N))
        pos_ = {ix: i for i, ix in enumerate(frame.index)}
        for (team, week), g in frame.groupby(["team", "week"], sort=False):
            idx = [pos_[ix] for ix in g.index]
            _car, y_, _tc = M.simulate_team_rush(rng, N, float(g.team_carries_env.iloc[0]), r_team_carries,
                                                 shares[idx], ypcs[idx], carry_resid)
            for k, i in enumerate(idx):
                yds[i] = y_[k]
        return yds

    def rpit_block(samples, y_arr):
        return (samples < y_arr[:, None]).mean(1) + rng.uniform(size=len(y_arr)) * (samples == y_arr[:, None]).mean(1)

    mu_m = np.maximum(test_act.team_targets_env * test_act.ts * test_act.cr.clip(lower=0.05), 0.02).values
    ypc_m = np.maximum(test_act.ypt / test_act.cr.clip(lower=0.05), 0.5).values
    shareA = test_act.own_ts.fillna(test_act.ts).values
    crA = test_act.own_cr.fillna(test_act.cr).clip(lower=0.05).values
    yptA = test_act.own_ypt.fillna(test_act.ypt).values

    # Both arms use the joint sampler, so the model-vs-baseline comparison
    # isolates the SHRINKAGE, which is what baseline A exists to test.
    recM, ydsM = draw_block_joint(test_act, test_act.ts.values,
                                  test_act.cr.clip(lower=0.05).values, test_act.ypt.values)
    recA, ydsA = draw_block_joint(test_act, shareA, crA, yptA)
    recI, ydsI = draw_block(mu_m, ypc_m, rec_fit)
    rushM = draw_block_rush(test_act, test_act.rs.fillna(0.0).values, test_act.ypc.values)
    rushA = draw_block_rush(test_act, test_act.own_rs.fillna(test_act.rs).fillna(0.0).values,
                            test_act.own_ypc.fillna(test_act.ypc).values)
    y_rec = test_act.act_receptions.values.astype(float)
    y_yds = test_act.act_rec_yards.values.astype(float)
    y_rush = test_act.act_rush_yards.values.astype(float)
    # The rushing population is fixed before the game and identical for every
    # model version: RB depth-chart slots, plus anyone with 20%+ of the team's
    # carries over his last four games. QBs are out (their rush props settle on
    # kneel-downs, which this data drops; see rush_yds_v0).
    slot_s = test_act.slot.astype(str)
    rush_pop = ((slot_s.str.startswith("RB") | (test_act.own_rs.fillna(0.0) >= 0.20))
                & ~slot_s.str.startswith("QB")).values
    nan_ = np.full(len(test_act), np.nan)

    res_df = pd.DataFrame({
        "season": S, "team": test_act.team, "week": test_act.week, "gsis_id": test_act.gsis_id, "slot": test_act.slot,
        "abs_spread": test_act.abs_spread,
        "act_receptions": y_rec, "act_rec_yards": y_yds, "act_rush_yards": y_rush, "rush_pop": rush_pop,
        "med_rec_model": np.median(recM, axis=1), "med_yds_model": np.median(ydsM, axis=1),
        "med_rush_model": np.where(rush_pop, np.median(rushM, axis=1), nan_),
        "mean_rec_model": recM.mean(1), "mean_yds_model": ydsM.mean(1),
        "mean_rush_model": np.where(rush_pop, rushM.mean(1), nan_),
        "above_med_rec": y_rec > np.median(recM, axis=1), "above_med_yds": y_yds > np.median(ydsM, axis=1),
        "above_med_rush": y_rush > np.median(rushM, axis=1),
        "pit_rec": rpit_block(recM, y_rec), "pit_yds": rpit_block(ydsM, y_yds),
        "pit_rush": np.where(rush_pop, rpit_block(rushM, y_rush), nan_),
        "crps_rec_model": crps_block(recM, y_rec), "crps_rec_baseA": crps_block(recA, y_rec),
        "crps_yds_model": crps_block(ydsM, y_yds), "crps_yds_baseA": crps_block(ydsA, y_yds),
        "crps_rush_model": np.where(rush_pop, crps_block(rushM, y_rush), nan_),
        "crps_rush_baseA": np.where(rush_pop, crps_block(rushA, y_rush), nan_),
        "crps_rec_indep": crps_block(recI, y_rec), "crps_yds_indep": crps_block(ydsI, y_yds),
    })
    res = res_df.merge(gm, on=["team", "week"], how="left")

    # RELIABILITY AT SYNTHETIC LINES (calibration a bettor can read): lines at
    # fixed offsets from the model median (not model quantiles, which would be
    # circular); the realized hit rate per predicted-probability bucket.
    calib = []
    for mk, samples, y, keep in [("rec", recM, y_rec, np.ones(len(y_rec), bool)), ("yds", ydsM, y_yds, np.ones(len(y_yds), bool)),
                                 ("rush", rushM, y_rush, rush_pop)]:
        smp, yy = samples[keep], y[keep]
        med = np.median(smp, axis=1)
        for o in MARKETS[mk][2]:
            for side, L in [("Under", med + o), ("Over", np.maximum(med - o, 0.5))]:
                if mk == "rec":
                    L = np.floor(L) + 0.5 if side == "Under" else np.ceil(L) - 0.5
                    L = np.maximum(L, 0.5)
                p = (smp < L[:, None]).mean(1) if side == "Under" else (smp > L[:, None]).mean(1)
                hit = (yy < L) if side == "Under" else (yy > L)
                calib.append(pd.DataFrame({"season": S, "market": MARKETS[mk][1], "side": side,
                                           "week": test_act.week.values[keep], "p_model": p, "hit": hit.astype(float)}))
    meta = {"season": S, "priors": PRIOR, "dispersion": dispersion, "live": live, "opp": opp,
            "rec_dispersion": rec_fit, "shape_ypc": shape_ypc, "team_targets_r": r_team_targets,
            "team_carries_r": r_team_carries, "calib": pd.concat(calib, ignore_index=True)}
    return res, meta


# ------------------------------------------------------------------ reporting
def game_block_ci(d, diff, reps=2000, seed=1):
    """95% interval for a mean difference, resampling whole games (players in
    one game share its environment, so they are not independent)."""
    key = d["season"].astype(str) + "_" + d["game_id"].astype(str)
    g = pd.DataFrame({"k": key.values, "diff": diff.values}).groupby("k")["diff"]
    sums, cnt = g.sum().values, g.size().values
    if len(sums) < 10:
        return float("nan"), float("nan")
    idx = np.random.default_rng(seed).integers(0, len(sums), size=(reps, len(sums)))
    boot = sums[idx].sum(1) / cnt[idx].sum(1)
    lo, hi = np.percentile(boot, [2.5, 97.5])
    return float(lo), float(hi)


def market_rows(res, mk):
    d = res if mk != "rush" else res[res.rush_pop.astype(bool)]
    return d.dropna(subset=[f"crps_{mk}_model"])


def summarize(res, mk):
    d = market_rows(res, mk)
    if d.empty:
        return None
    act = MARKETS[mk][0]
    diff = d[f"crps_{mk}_baseA"] - d[f"crps_{mk}_model"]
    lo, hi = game_block_ci(d, diff)
    ratio = float(d[act].mean() / max(d[f"mean_{mk}_model"].mean(), 1e-9))
    pitm = float(d[f"pit_{mk}"].mean())
    # WIDTH: the share of outcomes outside the model's own 10-90 range, each
    # player-week counted once. 0.20 when calibrated; above it = too narrow.
    tails = float(((d[f"pit_{mk}"] < 0.1) | (d[f"pit_{mk}"] > 0.9)).mean())
    return {"n": int(len(d)), "crps_model": float(d[f"crps_{mk}_model"].mean()),
            "crps_baseA": float(d[f"crps_{mk}_baseA"].mean()), "gain": float(diff.mean()),
            "ci": [lo, hi], "actual_over_model": ratio, "pit_mean": pitm, "outside_p10_p90": tails,
            "biased": bool(abs(pitm - 0.5) > BIAS_PIT or abs(ratio - 1) > BIAS_RATIO)}


def reliability_table(C):
    bins = [0.5, 0.6, 0.7, 0.8, 0.9, 1.0001]
    C = C.assign(bucket=pd.cut(C.p_model, bins, right=False, labels=["50-60", "60-70", "70-80", "80-90", "90+"]))
    return C.dropna(subset=["bucket"]).groupby(["market", "side", "bucket"], observed=True).agg(
        n=("hit", "size"), p_model_mean=("p_model", "mean"), hit_rate=("hit", "mean")).reset_index()


def harness_report(all_res, calib, metas, args, out_base):
    tune, test = parse_weeks(args.tune), parse_weeks(args.test)
    slices = [("weeks 2-4", lambda d: d[d.week.isin(EARLY_WEEKS)]),
              ("weeks 5-18", lambda d: d[d.week >= 5]), ("all weeks", lambda d: d)]
    groups = [(str(s), [s]) for s in sorted(all_res.season.unique())]
    groups += [(f"tune {'+'.join(map(str, tune))}", tune), (f"TEST {'+'.join(map(str, test))}", test)]
    summary = {}
    L = ["# Yardage harness: receptions, receiving yards, rushing yards", "",
         "*Generated by `props/engine/scripts/backtest.py` "
         f"`--seasons {args.seasons} --tune {args.tune} --test {args.test}`. Do not edit by hand.*", "",
         "Each season is predicted walk-forward from priors built from the season before, with the live "
         "scorer's settings and its joint sampler (`model.simulate_team_game`, `model.simulate_team_rush`). "
         "Nothing is fitted on the season under test. **Baseline A** is the same sampler fed each player's "
         "own recent rates with no shrinkage; **gain** is baseline A's CRPS minus the model's (positive = "
         "the model is better), with a 95% interval from resampling whole games. **Bias**: actual/model "
         "mean and the mean PIT (0.50 = calibrated); BIASED when the PIT mean is off by more than "
         f"{BIAS_PIT} or the mean ratio by more than {BIAS_RATIO:.0%}.", "",
         "Criteria for `live` (docs/plans/2026-09-24-yardage-harness.md), all on the test seasons: "
         "(1) gain above zero with an interval excluding zero on EACH test season; (2) no BIASED flag, "
         f"pooled; (3) WIDTH: outcomes outside the model's p10-p90 within {WIDTH_TARGET:.2f} +/- "
         f"{WIDTH_TOL:.2f}, pooled; (4) every {'/'.join(RELIABILITY_BUCKETS)}% reliability bucket on weeks "
         f"5-18 within {RELIABILITY_TOL:.2f} of its realized rate, both sides.", ""]
    # reliability first: the verdict reads it
    reliability, rel_frames = {}, {}
    for sname, weeks in [("weeks 5-18", lambda w: w >= 5), ("weeks 2-4", lambda w: w.isin(EARLY_WEEKS))]:
        rel_frames[sname] = reliability_table(calib[calib.season.isin(test) & weeks(calib.week)])
        reliability[sname] = rel_frames[sname].to_dict(orient="records")
    verdicts = {}
    for mk, (_act, label, _o) in MARKETS.items():
        L += [f"## {label.capitalize()}", "",
              "| Seasons | Weeks | N | CRPS model | CRPS baseline A | Gain (95% CI) | Actual/model | PIT mean "
              "| Outside p10-p90 (0.20) | |",
              "|---|---|---|---|---|---|---|---|---|---|"]
        summary[mk] = {}
        for gname, seasons in groups:
            for sname, sl in slices:
                s = summarize(sl(all_res[all_res.season.isin(seasons)]), mk)
                if s is None:
                    continue
                summary[mk][f"{gname} | {sname}"] = s
                lo, hi = s["ci"]
                sig = " **(excl. 0)**" if (lo > 0 or hi < 0) else ""
                L.append(f"| {gname} | {sname} | {s['n']} | {s['crps_model']:.3f} | {s['crps_baseA']:.3f} | "
                         f"{s['gain']:+.3f} ({lo:+.3f}, {hi:+.3f}){sig} | {s['actual_over_model']:.3f} | "
                         f"{s['pit_mean']:.3f} | {s['outside_p10_p90']:.3f} | {'BIASED' if s['biased'] else ''} |")
        per_test = [summarize(all_res[all_res.season == s], mk) for s in test]
        pooled = summarize(all_res[all_res.season.isin(test)], mk)
        beats = all(p is not None and p["ci"][0] > 0 for p in per_test)
        unbiased = pooled is not None and not pooled["biased"]
        width_ok = pooled is not None and abs(pooled["outside_p10_p90"] - WIDTH_TARGET) <= WIDTH_TOL
        r5 = rel_frames["weeks 5-18"]
        r5 = r5[(r5.market == label) & r5.bucket.astype(str).isin(RELIABILITY_BUCKETS)]
        worst_gap = float((r5.hit_rate - r5.p_model_mean).abs().max()) if len(r5) else float("nan")
        calib_ok = bool(len(r5)) and worst_gap <= RELIABILITY_TOL
        ok = beats and unbiased and width_ok and calib_ok
        verdicts[mk] = {"passes": ok, "beats_baseline_each_test_season": beats, "unbiased": unbiased,
                        "outside_p10_p90": None if pooled is None else pooled["outside_p10_p90"],
                        "width_ok": width_ok, "worst_reliability_gap": worst_gap, "calibration_ok": calib_ok}
        yn = lambda b: "yes" if b else "**no**"
        L += ["", f"**Verdict on the test seasons: {'PASSES' if ok else 'DOES NOT PASS'}** -- "
              f"beats baseline A each season: {yn(beats)}; unbiased: {yn(unbiased)}; width "
              f"({verdicts[mk]['outside_p10_p90'] or float('nan'):.3f} outside p10-p90): {yn(width_ok)}; calibration (worst "
              f"60-90% gap {worst_gap:.3f}): {yn(calib_ok)}.", ""]

    # reliability, pooled test seasons, by slice: CRPS and the mean can both
    # look fine while the distribution is too narrow, and a too-narrow
    # distribution overstates every edge at a posted line.
    L += ["## Reliability at synthetic lines, test seasons", "",
          "Lines placed at fixed offsets from the model median; a calibrated 70% bucket wins about 70%. "
          "Realized below the model on BOTH sides of the same bucket means the distribution is too narrow "
          "(overconfident), not shifted. Each player-week appears at several lines, so N overstates the "
          "evidence; the width column above counts each player-week once.", ""]
    for sname in ("weeks 5-18", "weeks 2-4"):
        rel = rel_frames[sname]
        L += [f"### {sname}", "", "| Market | Side | Model probability | N | Model mean | Realized | Gap |",
              "|---|---|---|---|---|---|---|"]
        for _, r in rel.iterrows():
            L.append(f"| {r.market} | {r.side} | {r.bucket} | {int(r.n)} | {r.p_model_mean:.3f} | "
                     f"{r.hit_rate:.3f} | {r.hit_rate - r.p_model_mean:+.3f} |")
        L.append("")
    L += ["", "## What this does not reproduce from the live scorer", "",
          "- The snap-share role scaling and the new-team cap on the prior-season rate "
          "(`blended_rate(role_scale=..., new_team=...)`): the harness has no pre-game snap feed.",
          "- The player's depth-chart slot is his first slot of the season (the round-4 convention), "
          "not the week's.",
          "- Questionable-player regimes, injury-report exclusions (the harness uses the game-day "
          "active list, which the injury report approximates before kickoff), and prices: this "
          "grades distributions against outcomes, not against posted lines.",
          "- QB rushing and passing yards (plan steps 2 and 3).", "",
          "## Settings", ""]
    for m in metas:
        L.append(f"- {m['season']}: priors {m['priors']}, dispersion from {m['dispersion']}, opponent "
                 f"{m['opp']['level']} k0={m['opp']['k0']:g} on {m['opp']['metrics']}; team targets r="
                 f"{m['team_targets_r']:.1f}, carries r={m['team_carries_r']:.1f}, per-catch shape "
                 f"{m['shape_ypc']:.3f}")
    Path(str(out_base) + ".md").write_text("\n".join(L) + "\n", encoding="utf-8")
    Path(str(out_base) + ".json").write_text(json.dumps(
        {"seasons": args.seasons, "tune": args.tune, "test": args.test, "verdicts": verdicts,
         "summary": summary, "reliability_test": reliability}, indent=1, sort_keys=True, default=str) + "\n",
        encoding="utf-8")
    print(f"wrote {out_base}.md and .json", file=sys.stderr)
    for mk, v in verdicts.items():
        print(f"  {MARKETS[mk][1]}: {'PASSES' if v['passes'] else 'does not pass'}", file=sys.stderr)


def compare_runs(res, ref_path):
    """Paired game-block bootstrap on the MODEL's own CRPS, this run vs a
    reference run's results pickle (positive = this run better)."""
    ref = pd.read_pickle(ref_path)
    if isinstance(ref, tuple):          # a harness --save-results pickle: (results, calibration, settings)
        ref = ref[0]
    keys =[k for k in ("season", "team", "week", "gsis_id") if k in res.columns and k in ref.columns]
    d0 = res.merge(ref, on=keys, suffixes=("", "_ref"))
    print(f"\n=== Paired game-block bootstrap, THIS run vs {Path(ref_path).name}, model CRPS only "
          f"(positive = this better) ===", file=sys.stderr)
    for subset_name, dd in [("all games", d0), ("|spread|>=7", d0[d0.abs_spread >= 7])]:
        if len(dd) < 50:
            continue
        print(f"  -- {subset_name}, N={len(dd)} --", file=sys.stderr)
        for mk in MARKETS:
            if f"crps_{mk}_model_ref" not in dd.columns:
                continue
            d = dd.dropna(subset=[f"crps_{mk}_model", f"crps_{mk}_model_ref"])
            if "season" not in d.columns:
                d = d.assign(season=0)
            diff = d[f"crps_{mk}_model_ref"] - d[f"crps_{mk}_model"]
            lo, hi = game_block_ci(d, diff)
            print(f"    {mk}: {diff.mean():+.4f}  95% CI ({lo:+.4f}, {hi:+.4f})  "
                  f"{'excludes 0' if lo > 0 or hi < 0 else 'includes 0'}", file=sys.stderr)


def single_season_output(args, res, meta, OUT):
    """The round-4..9 console report for one season, unchanged in content."""
    print(f"\n=== Overall model vs baseline A, N={len(res)} ===", file=sys.stderr)
    for col in ["crps_rec_model", "crps_rec_baseA", "crps_rec_indep",
                "crps_yds_model", "crps_yds_baseA", "crps_yds_indep", "crps_rush_model", "crps_rush_baseA"]:
        print(f"  {col}: {res[col].mean():.4f}", file=sys.stderr)
    print("  (_indep = the old independent per-player draw, for comparison only; _model and _baseA "
          "both use the live joint sampler; rush over the rushing population only)", file=sys.stderr)
    print(f"\n=== Bias check (0.50 = unbiased median; PIT mean 0.50 = calibrated) ===", file=sys.stderr)
    for mk in MARKETS:
        d = market_rows(res, mk)
        act, mean_col = MARKETS[mk][0], f"mean_{mk}_model"
        frac = d[f"above_med_{mk}"].mean(); pitm = d[f"pit_{mk}"].mean()
        ratio = d[act].mean() / max(d[mean_col].mean(), 1e-6)
        h, _ = np.histogram(d[f"pit_{mk}"], bins=10, range=(0, 1))
        flag = "  <-- BIASED" if (abs(pitm - 0.5) > BIAS_PIT or abs(ratio - 1) > BIAS_RATIO) else ""
        print(f"  {mk}: frac actual > model median = {frac:.3f} | PIT mean = {pitm:.3f} | "
              f"actual/model mean = {ratio:.3f} | PIT deciles {h.tolist()}{flag}", file=sys.stderr)
    rel = reliability_table(meta["calib"])
    print("\n=== Reliability: model probability bucket vs realized hit rate ===", file=sys.stderr)
    for _, r in rel.iterrows():
        print(f"  {r.market:15s} {r.side:5s} {r.bucket:>6s}: n={int(r.n):5d} model {r.p_model_mean:.3f} "
              f"realized {r.hit_rate:.3f} ({r.hit_rate - r.p_model_mean:+.3f})", file=sys.stderr)
    rel.to_csv(OUT / ("reliability_%d%s.csv" % (args.season, ("_" + args.tag) if args.tag else "")), index=False)
    for mk in MARKETS:
        d = market_rows(res, mk)
        print(f"  model-A diff {MARKETS[mk][1]}: {(d[f'crps_{mk}_baseA'] - d[f'crps_{mk}_model']).mean():+.4f}",
              file=sys.stderr)
    tag = args.tag or f"{args.env}_opp{args.opponent}_{args.opp_level}_{args.opp_mode}_k{int(args.opp_k0)}"
    res.to_pickle(OUT / f"backtest_{tag}_results.pkl")
    if args.compare_to:
        compare_runs(res, args.compare_to)
    json.dump({"env": args.env, "opponent": args.opponent, "N": len(res),
               "crps_rec_model": float(res.crps_rec_model.mean()), "crps_rec_baseA": float(res.crps_rec_baseA.mean()),
               "crps_yds_model": float(res.crps_yds_model.mean()), "crps_yds_baseA": float(res.crps_yds_baseA.mean()),
               "crps_rush_model": float(market_rows(res, "rush").crps_rush_model.mean()),
               "crps_rush_baseA": float(market_rows(res, "rush").crps_rush_baseA.mean()),
               "crps_rec_indep": float(res.crps_rec_indep.mean()),
               "crps_yds_indep": float(res.crps_yds_indep.mean()),
               "sampler": "model.simulate_team_game + simulate_team_rush (joint, shared with the live scorer)",
               "team_targets_r": meta["team_targets_r"], "team_carries_r": meta["team_carries_r"],
               "rec_dispersion": meta["rec_dispersion"], "shape_ypc": meta["shape_ypc"]},
              open(OUT / f"backtest_{tag}_summary.json", "w", encoding="utf-8"), indent=2)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--season", type=int, default=2025)
    ap.add_argument("--train-weeks", default="5,6,7,8")
    ap.add_argument("--test-weeks", default="9-18")
    ap.add_argument("--seasons", default=None,
                    help="HARNESS MODE: comma list of seasons, each walk-forward with the live settings")
    ap.add_argument("--tune", default="2022,2023", help="harness: seasons settings may be chosen on")
    ap.add_argument("--test", default="2024,2025", help="harness: seasons the verdict is read from")
    ap.add_argument("--weeks", default="2-18", help="harness: weeks scored in each season")
    ap.add_argument("--report", default=None, help="harness: output path without extension (.md and .json)")
    ap.add_argument("--save-results", default=None,
                    help="harness: pickle (results, calibration rows, settings) of the whole run")
    ap.add_argument("--from-results", default=None, help="harness: re-render the report from a --save-results pickle")
    ap.add_argument("--dispersion", choices=["prior", "train"], default=None,
                    help="prior = the priors_{S-1} values the scorer reads (harness default); "
                         "train = fit on --train-weeks of the season (single-season default)")
    ap.add_argument("--priors-dir", default=None, help="where priors_{S-1}_* live (default: the engine's resources)")
    ap.add_argument("--build-priors", action="store_true", help="build missing priors with build_priors.py")
    ap.add_argument("--env", choices=["history", "market", "league", "market_fit"], default="history")
    ap.add_argument("--pace-weight", type=float, default=0.5)
    ap.add_argument("--env-window", type=int, default=0, help="0 = expanding mean; N = trailing N games for team volume")
    ap.add_argument("--drift-correct", action="store_true", default=True,
                    help="scale the expanding team mean by a league-wide recent/expanding volume ratio")
    ap.add_argument("--no-drift-correct", dest="drift_correct", action="store_false")
    ap.add_argument("--drift-recent", type=int, default=3)
    ap.add_argument("--opponent", action="store_true", default=True)
    ap.add_argument("--no-opponent", dest="opponent", action="store_false")
    ap.add_argument("--out", default=str(HERE / "backtest_out"))
    ap.add_argument("--opp-level", choices=["posgrp", "team"], default="posgrp")
    ap.add_argument("--opp-mode", choices=["fixed", "eb"], default="fixed")
    ap.add_argument("--opp-k0", type=float, default=1000.0)
    ap.add_argument("--opp-metrics", default="catch_rate,ypt,ypc")
    ap.add_argument("--historical-blend", action="store_true", default=True,
                    help="two-stage: prior-season own rate -> slot prior -> this season (what the live scorer does)")
    ap.add_argument("--no-historical-blend", dest="historical_blend", action="store_false",
                    help="ABLATION: one stage, this season -> slot prior, ignoring the prior-season individual rate")
    ap.add_argument("--tag", default=None, help="label for output files")
    ap.add_argument("--compare-to", default=None, help="results pickle of a reference run; paired game-block bootstrap on the MODEL's own CRPS")
    args = ap.parse_args(argv)
    OUT = Path(args.out); OUT.mkdir(parents=True, exist_ok=True)

    if not args.seasons:
        res, meta = run_season(args, args.season, parse_weeks(args.train_weeks), parse_weeks(args.test_weeks),
                               OUT, live=False)
        single_season_output(args, res, meta, OUT)
        return 0

    if args.priors_dir is None:
        # Every season's priors come from the CURRENT builder, not a mix of
        # committed files built by older code.
        args.priors_dir = str(CACHE / "priors")
        args.build_priors = True
    Path(args.priors_dir).mkdir(parents=True, exist_ok=True)
    if args.from_results:
        # Re-render the report from a saved run: the simulations are the slow
        # part and a report change should not need them.
        all_res, calib, metas = pd.read_pickle(args.from_results)
    else:
        frames, calibs, metas = [], [], []
        for S in parse_weeks(args.seasons):
            res, meta = run_season(args, S, parse_weeks(args.train_weeks), parse_weeks(args.weeks), OUT, live=True)
            frames.append(res); calibs.append(meta.pop("calib")); metas.append(meta)
        all_res = pd.concat(frames, ignore_index=True)
        calib = pd.concat(calibs, ignore_index=True)
    if args.save_results:
        pd.to_pickle((all_res, calib, metas), args.save_results)
    if args.compare_to:
        compare_runs(all_res, args.compare_to)
    harness_report(all_res, calib, metas, args,
                   Path(args.report) if args.report else OUT / "yardage_harness")
    return 0


if __name__ == "__main__":
    sys.exit(main())
