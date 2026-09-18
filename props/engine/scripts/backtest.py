#!/usr/bin/env python3
"""Backtest the shared model core (model.py) against 2025, with the same rigor as
the round-4 validation: bye exclusion, ACT/INA-only population, INA voided (not
scored as zero), per-arm dispersion, full-chain determinism.

New versus round 4:
  - team environment can be market-anchored using games.csv's historical
    spread_line/total_line (nflverse carries real closing lines), instead of
    pure team-history blend
  - opponent efficiency adjustment, shrunk by plays faced, built from an
    EXPANDING (pre-week) table so no future defensive performance leaks in
  - per-rate shrinkage constants (K0 differs for target share vs catch rate vs
    yards per target, etc.), tuned by build_priors.py, instead of one K0=4 for
    everything

Data: expects NFL_BACKTEST_DATA (default /home/claude/nfl-prop-research) containing
  analysis/{games_2025,game_map,roles_2025,roster_2025,player_week_receiving_ts,
  player_week_rushing_rs,team_week_targets,team_week_carries}.pkl and data2025/pbp_2025.csv.
  These are produced by the round-4 step0-step3 scripts; a self-contained builder is a
  known gap.

Usage:
  python backtest.py --season 2025 --train-weeks 5,6,7,8 --test-weeks 9-18
                     --env history|market [--no-opponent] [--out DIR]
"""
import argparse, json, os, re, sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.special import gammaln

sys.path.insert(0, str(Path(__file__).resolve().parent))
import model as M

HERE = Path(__file__).resolve().parent
DATA = Path(os.environ.get("NFL_BACKTEST_DATA", "/home/claude/nfl-prop-research"))   # see --help: needs the round-4 analysis pickles + data2025/
RES = HERE.parent / "resources"


def parse_weeks(s):
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--season", type=int, default=2025)
    ap.add_argument("--train-weeks", default="5,6,7,8")
    ap.add_argument("--test-weeks", default="9-18")
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
    ap.add_argument("--compare-to", default=None, help="results.pkl of a reference run; paired game-block bootstrap on the MODEL's own CRPS")
    args = ap.parse_args()
    S = args.season
    TRAIN = parse_weeks(args.train_weeks); TEST = parse_weeks(args.test_weeks)
    OUT = Path(args.out); OUT.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(20260917)
    N = 1000

    print(f"env={args.env} opponent={args.opponent} "
          f"historical_blend={args.historical_blend}", file=sys.stderr)

    # ---- self-contained data build (round 7): derive every frame from nflverse for
    # ANY season, instead of depending on the round-4 pickles that only existed for
    # 2025 in one container. Cached to OUT so repeat runs are instant. ----
    WD = Path(os.environ.get("NFL_BACKTEST_CACHE", "/tmp/nflbt")); WD.mkdir(parents=True, exist_ok=True)
    NV = "https://github.com/nflverse/nflverse-data/releases/download"

    def dl(url, dest):
        import urllib.request
        if not Path(dest).exists() or Path(dest).stat().st_size == 0:
            print(f"  fetching {Path(dest).name}", file=sys.stderr)
            urllib.request.urlretrieve(url, dest)
        return dest

    frames_cache = OUT / f"_frames_{S}.pkl"
    if frames_cache.exists():
        games, gm, roles, roster, rec, rush, twt, twc = pd.read_pickle(frames_cache)
        pbp_full = pd.read_csv(dl(f"{NV}/pbp/play_by_play_{S}.csv", WD / f"pbp_{S}.csv"), low_memory=False)
        pbp_full = pbp_full[pbp_full.season_type == "REG"]
    else:
        pbp_full = pd.read_csv(dl(f"{NV}/pbp/play_by_play_{S}.csv", WD / f"pbp_{S}.csv"), low_memory=False)
        pbp_full = pbp_full[pbp_full.season_type == "REG"]
        games_all = pd.read_csv(dl("https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv",
                                   WD / "games.csv"))
        games = games_all[(games_all.season == S) & (games_all.game_type == "REG")].copy()
        games["game_id2"] = games.gameday.astype(str) + "_" + games.home_team + "_" + games.away_team
        gm = pd.concat([games[["week", "home_team", "game_id2"]].rename(columns={"home_team": "team"}),
                        games[["week", "away_team", "game_id2"]].rename(columns={"away_team": "team"})],
                       ignore_index=True).drop_duplicates(["team", "week"]).rename(columns={"game_id2": "game_id"})
        roster = pd.read_csv(dl(f"{NV}/weekly_rosters/roster_weekly_{S}.csv", WD / f"ros_{S}.csv"), low_memory=False)
        roster = roster[roster.season == S][["week", "team", "gsis_id", "full_name", "position", "status"]].drop_duplicates(
            ["week", "team", "gsis_id"])
        # pre-game depth-chart slot per team-week (latest snapshot strictly before kickoff)
        dcf = pd.read_csv(dl(f"{NV}/depth_charts/depth_charts_{S}.csv", WD / f"dc_{S}.csv"), low_memory=False)
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
    # This used to read priors_{S}, and build_priors.py --season S builds that
    # file FROM season S -- the season under test. So the shrinkage constants
    # K0R, the league rates, and market_env_fit (which turns spread/total into
    # the team volume behind every mu) were all fitted on data that includes
    # the test weeks. The walk-forward was clean in player evidence and leaky
    # in hyperparameters, and the leak flattered exactly the environment model
    # the harness exists to judge.
    #
    # The live scorer uses PRIOR = SEASON - 1. Matching it fixes the leak and,
    # because priors_{PRIOR}_players.csv carries per-player prior-season rates,
    # is also what makes the two-stage historical blend possible here at all.
    PRIOR = S - 1
    prior_params = RES / f"priors_{PRIOR}_params.json"
    if not prior_params.exists():
        sys.exit(f"priors_{PRIOR}_params.json is missing: a walk-forward test of "
                 f"{S} needs the priors the live scorer would have had, which are "
                 f"built from {PRIOR}. Run build_priors.py --season {PRIOR}.")
    P0 = json.load(open(prior_params))
    pri_players = pd.read_csv(RES / f"priors_{PRIOR}_players.csv").set_index("gsis_id")
    print(f"priors: {PRIOR} (the season before the one under test), "
          f"{len(pri_players)} players", file=sys.stderr)
    K0R = P0.get("k0_per_rate", M.DEFAULT_K0)
    league_pass_rate = P0.get("league_pass_rate", 0.55)
    MKT_FIT = P0.get("market_env_fit", {})
    league_plays = P0.get("league_plays_per_game", 64.0)

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
        """Team volume environment. Expanding mean (default) lags within-season drift in
        league passing volume (+3.4% in 2024, -4.2% in 2025), producing a ~3-4% bias in
        opposite directions. --env-window N uses the trailing N games instead."""
        out = {}
        prior_all = twt.merge(twc, on=["team", "week"])
        for W in weeks:
            pa = prior_all[prior_all.week < W]
            if args.env_window > 0:
                pa = pa.sort_values("week").groupby("team").tail(args.env_window)
            m_ = pa.groupby("team")[["team_targets", "team_carries"]].mean()
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

        rows = []
        for _, r in feat.iterrows():
            W, slot = r.week, r.slot
            sp = slot_p[W]
            def gv(d, k, default=np.nan):
                return float(d.get(k, default)) if k in d.index else default
            # THE SAME TWO-STAGE BLEND THE SCORER RUNS (model.blended_rate):
            # prior-season own rate -> slot prior -> this season's partial
            # evidence. This used to be a single M.blend of the current season
            # straight onto the slot prior, with the prior-season individual
            # rate never read at all -- so "the pre-week-5 prior blend", the
            # component methodology.md flags as unvalidated, was the one thing
            # the backtest structurally could not measure.
            #
            # n is in OPPORTUNITY units on both sides, matching how K0 was
            # tuned: team targets for shares, own targets for catch rate and
            # ypt, carries for ypc.
            pri = pri_players.loc[r.gsis_id] if r.gsis_id in pri_players.index else None

            def two_stage(pri_col, n_col, slot_key, default, k0_key, k0_default,
                          cur, cur_n, scale_role=False):
                # The ablation drops stage one by giving it nothing to shrink
                # from, which leaves blend() returning the slot prior -- exactly
                # the one-stage behaviour, through the same code path, so the
                # comparison cannot be confounded by a second implementation.
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
            ypc = two_stage("ypc", "carries_n", "ypc", 4.2,
                            "ypc", 80, r.own_ypc, r.n_ca)

            opp_team = opp_team_of.get((r.team, W))
            if args.opponent and opp_team:
                posgrp = "ALL" if args.opp_level == "team" else re_first_letters(slot)
                otab = opp_tabs[W]
                mets = set(args.opp_metrics.split(","))
                if len(otab):
                    om = lambda met: M.opponent_multiplier(otab, opp_team, posgrp, met, k0_opp=args.opp_k0, mode=args.opp_mode)
                    if "catch_rate" in mets: cr = float(np.clip(cr * om("catch_rate"), 0.05, 1.0))
                    if "ypt" in mets: ypt = float(ypt * om("ypt"))
                    if "ypc" in mets: ypc = float(ypc * om("ypc"))

            he = hist_env[W]
            targets_env = float(he.loc[r.team, "team_targets"]) if r.team in he.index else league_plays * league_pass_rate
            carries_env = float(he.loc[r.team, "team_carries"]) if r.team in he.index else league_plays * (1 - league_pass_rate)
            if env_mode == "league":
                # ABLATION: constant league-average volume, no spread/total, no team history.
                # If this matches "market", the market win was really just variance reduction
                # from dropping noisy team-history volume, not information from the odds.
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
                    # team's own pass rate goes in for THIS team; the opponent's slot gets league
                    # (its value is unused for this row). Plays = this team's history plays,
                    # not league constant, so team pace identity survives too.
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

    MKT_SLOPES = fit_market_slopes(TRAIN)
    # Feature caching: population and raw per-player features depend only on the season
    # and week list, NOT on --env / --opponent / K0. Ablation matrices re-derived them
    # every run, which is most of the runtime. Cache to pickle keyed by the week list.
    def cached_features(weeks, label):
        key = f"{S}_{label}_{'-'.join(map(str, weeks))}"
        f = OUT / f"_featcache_{key}.pkl"
        if f.exists():
            return pd.read_pickle(f)
        pop = make_population(weeks); feat = make_features(pop)
        feat.to_pickle(f)
        return feat
    feat_tr = cached_features(TRAIN, "train")
    feat_te = cached_features(TEST, "test")
    pop_tr = feat_tr[["team", "week", "gsis_id", "roster_status"]]
    pop_te = feat_te[["team", "week", "gsis_id", "roster_status"]]
    feat_tr = build_shrunk(pop_tr, feat_tr, TRAIN, args.env)
    feat_te = build_shrunk(pop_te, feat_te, TEST, args.env)
    feat_tr = feat_tr[feat_tr.slot != "QB1"].reset_index(drop=True)
    feat_te = feat_te[feat_te.slot != "QB1"].reset_index(drop=True)
    print(f"train N={len(feat_tr)}  test N={len(feat_te)}", file=sys.stderr)

    tr_act = feat_tr[feat_tr.roster_status == "ACT"]
    mu_rec_tr = np.maximum(tr_act.team_targets_env * tr_act.ts * tr_act.cr.clip(lower=0.05), 0.02).values
    rec_fit = nb_mle(mu_rec_tr, tr_act.act_receptions.values.astype(float), [0.5, 30.0])
    # per-arm dispersion (round-3 review #3; regressed in the first round-5 harness)
    shareA_tr = tr_act.own_ts.fillna(tr_act.ts); crA_tr = tr_act.own_cr.fillna(tr_act.cr).clip(lower=0.05)
    mu_rec_trA = np.maximum(tr_act.team_targets_env * shareA_tr * crA_tr, 0.02).values
    rec_fit_A = nb_mle(mu_rec_trA, tr_act.act_receptions.values.astype(float), [0.5, 30.0])
    pos = tr_act[tr_act.act_receptions >= 1]
    ks, ss, ws = [], [], []
    for k, g_ in pos.groupby("act_receptions"):
        if len(g_) < 15 or g_.act_rec_yards.var() <= 0: continue
        Y = g_.act_rec_yards.values
        ks.append(k); ss.append((Y.mean()**2)/(k*Y.var())); ws.append(len(g_))
    shape_ypc = float(np.average(ss, weights=ws)) if ss else 1.0
    print(f"model dispersion: rec r={rec_fit}  shape_ypc={shape_ypc:.3f}", file=sys.stderr)

    # TEAM VOLUME DISPERSION, fit on the training weeks only.
    # The live scorer takes this from the prior-season priors file; the
    # backtest must not, because priors_{S} is built from season S -- the very
    # season under test. Fitting it on train weeks keeps the walk-forward
    # honest and matches build_priors.nb_dispersion_pooled exactly.
    _tt_train = twt[twt.week.isin(TRAIN)].team_targets.values.astype(float)
    _m, _v = _tt_train.mean(), _tt_train.var()
    r_team_targets = float(_m ** 2 / (_v - _m)) if _v > _m else 30.0
    print(f"team target dispersion (train weeks): r={r_team_targets:.2f}", file=sys.stderr)

    def r_of(mu, fit, clamp=(0.5, 30.0)):
        return float(np.clip(np.exp(fit["a"] + fit["b"]*np.log(max(mu, 1e-6))), *clamp))
    def draw(mu, ypc, fit):
        rr = r_of(mu, fit)
        rec_ = rng.negative_binomial(rr, rr/(rr+mu), size=N).astype(float)
        yds = np.where(rec_ > 0, rng.gamma(np.maximum(np.clip(rec_,0,25)*shape_ypc, 1e-6), max(ypc,0.5)/shape_ypc), 0.0)
        return rec_, yds
    def crps(s, y):
        n=len(s); t1=np.mean(np.abs(s-y)); ss_=np.sort(s); i=np.arange(1,n+1)
        return t1 - 0.5*((2.0/(n*n))*np.sum((2*i-n-1)*ss_))
    def rpit(s, y):   # randomized PIT, valid for counts / point mass at 0
        return float(np.mean(s < y) + rng.uniform()*np.mean(s == y))

    test_act = feat_te[feat_te.roster_status == "ACT"].reset_index(drop=True)

    def draw_block(mu_arr, ypc_arr, fit):
        """INDEPENDENT per-player draws. Kept only as the marginal comparator.

        This is what the backtest used to score, and it is NOT the generative
        model the live scorer runs: it gives each player his own negative
        binomial, so two receivers on one team can both post a career day in
        the same simulation off a team that only threw 24 times. Retained
        because the difference between this and the joint draw below is itself
        a measurement worth printing.
        """
        r_arr = np.clip(np.exp(fit["a"] + fit["b"] * np.log(np.maximum(mu_arr, 1e-6))), 0.5, 30.0)
        p_arr = r_arr / (r_arr + mu_arr)
        rec = rng.negative_binomial(r_arr[:, None], p_arr[:, None], size=(len(mu_arr), N)).astype(float)
        shape_tot = np.maximum(np.clip(rec, 0, 25) * shape_ypc, 1e-6)
        yds = np.where(rec > 0, rng.gamma(shape_tot, (np.maximum(ypc_arr, 0.5) / shape_ypc)[:, None]), 0.0)
        return rec, yds

    def draw_block_joint(frame, shares, crs, ypts):
        """THE LIVE PIPELINE'S DRAW: one team-volume draw per simulation, split
        across that team's players, catches binomial on each player's own
        targets, yards a sum of per-catch gammas.

        Same call the scorer makes (model.simulate_team_game), so the CRPS this
        backtest reports finally describes the sampler that prices the props.
        Teammates end up negatively correlated within a simulation and every
        player inherits the team's play-count variance -- both true of football
        and both absent from the independent draw above.

        Players are grouped by (team, week) because that is one team's game.
        Arrays come back in `frame` row order.
        """
        rec = np.zeros((len(frame), N))
        yds = np.zeros((len(frame), N))
        pos = {ix: i for i, ix in enumerate(frame.index)}
        for (team, week), g in frame.groupby(["team", "week"], sort=False):
            # team_targets_env is a team-week property, so every row in the
            # group carries the same value; take the first rather than a mean
            # that would silently hide a data error.
            tvol = float(g.team_targets_env.iloc[0])
            out, _tt = M.simulate_team_game(
                rng, N, tvol, r_team_targets,
                {ix: float(shares[pos[ix]]) for ix in g.index},
                {ix: float(crs[pos[ix]]) for ix in g.index},
                {ix: float(ypts[pos[ix]]) for ix in g.index},
                shape_ypc)
            for ix, (r_, y_) in out.items():
                rec[pos[ix]] = r_
                yds[pos[ix]] = y_
        return rec, yds

    def crps_block(samples, y_arr):
        """Vectorized unbiased empirical CRPS across all players at once."""
        n = samples.shape[1]
        t1 = np.abs(samples - y_arr[:, None]).mean(axis=1)
        ss_ = np.sort(samples, axis=1)
        i = np.arange(1, n + 1)
        t2 = (2.0 / (n * n)) * ((2 * i - n - 1) * ss_).sum(axis=1)
        return t1 - 0.5 * t2

    mu_m = np.maximum(test_act.team_targets_env * test_act.ts * test_act.cr.clip(lower=0.05), 0.02).values
    ypc_m = np.maximum(test_act.ypt / test_act.cr.clip(lower=0.05), 0.5).values
    shareA = test_act.own_ts.fillna(test_act.ts).values
    crA = test_act.own_cr.fillna(test_act.cr).clip(lower=0.05).values
    yptA = test_act.own_ypt.fillna(test_act.ypt).values
    mu_a = np.maximum(test_act.team_targets_env.values * shareA * crA, 0.02)
    ypc_a = np.maximum(yptA / crA, 0.5)

    # Both arms use the joint sampler, so the model-vs-baseline comparison
    # isolates the SHRINKAGE, which is what baseline A exists to test. Mixing
    # samplers across arms would confound the two.
    ypt_m = test_act.ypt.values
    recM, ydsM = draw_block_joint(test_act, test_act.ts.values,
                                  test_act.cr.clip(lower=0.05).values, ypt_m)
    recA, ydsA = draw_block_joint(test_act, shareA, crA, yptA)
    # The old independent draw, kept as a diagnostic: the gap between these and
    # the joint numbers is the cost of the sampler that was being measured
    # instead of the one that ships.
    recI, ydsI = draw_block(mu_m, ypc_m, rec_fit)
    y_rec = test_act.act_receptions.values.astype(float)
    y_yds = test_act.act_rec_yards.values.astype(float)

    def rpit_block(samples, y_arr):
        return (samples < y_arr[:, None]).mean(1) + rng.uniform(size=len(y_arr)) * (samples == y_arr[:, None]).mean(1)

    res_df = pd.DataFrame({
        "team": test_act.team, "week": test_act.week, "gsis_id": test_act.gsis_id, "slot": test_act.slot,
        "act_receptions": y_rec, "act_rec_yards": y_yds,
        "med_rec_model": np.median(recM, axis=1), "med_yds_model": np.median(ydsM, axis=1),
        "mean_rec_model": recM.mean(1), "mean_yds_model": ydsM.mean(1),
        "above_med_rec": y_rec > np.median(recM, axis=1), "above_med_yds": y_yds > np.median(ydsM, axis=1),
        "pit_rec": rpit_block(recM, y_rec), "pit_yds": rpit_block(ydsM, y_yds),
        "crps_rec_model": crps_block(recM, y_rec), "crps_rec_baseA": crps_block(recA, y_rec),
        "crps_yds_model": crps_block(ydsM, y_yds), "crps_yds_baseA": crps_block(ydsA, y_yds),
        "crps_rec_indep": crps_block(recI, y_rec), "crps_yds_indep": crps_block(ydsI, y_yds),
    })
    out_rows = res_df
    res = out_rows.merge(gm, on=["team", "week"], how="left")

    # ---- bias diagnostic (reviewer, round 6): CRPS cannot see a one-directional shift.
    # A model 15% low everywhere still posts a plausible CRPS. Report, per market, the
    # fraction of outcomes above the model MEDIAN (should be ~0.5, less for zero-heavy
    # counts) and a 10-bin PIT histogram (should be flat). ----
    print(f"\n=== Overall model vs baseline A, N={len(res)} ===", file=sys.stderr)
    for col in ["crps_rec_model", "crps_rec_baseA", "crps_rec_indep",
                "crps_yds_model", "crps_yds_baseA", "crps_yds_indep"]:
        print(f"  {col}: {res[col].mean():.4f}", file=sys.stderr)
    print("  (_indep = the old independent per-player draw, for comparison "
          "only; _model and _baseA both use the live joint sampler)",
          file=sys.stderr)
    # ---- BIAS DIAGNOSTIC (reviewer request): CRPS cannot see a one-directional shift ----
    print(f"\n=== Bias check (0.50 = unbiased median; PIT mean 0.50 = calibrated) ===", file=sys.stderr)
    for mk, act, mean_col in [("rec", "act_receptions", "mean_rec_model"), ("yds", "act_rec_yards", "mean_yds_model")]:
        frac = res[f"above_med_{mk}"].mean(); pitm = res[f"pit_{mk}"].mean()
        ratio = res[act].mean() / max(res[mean_col].mean(), 1e-6)
        h, _ = np.histogram(res[f"pit_{mk}"], bins=10, range=(0, 1))
        # for count markets "actual > median" excludes ties, so only PIT mean and mean ratio are used
        flag = "  <-- BIASED" if (abs(pitm - 0.5) > 0.03 or abs(ratio - 1) > 0.05) else ""
        print(f"  {mk}: frac actual > model median = {frac:.3f} | PIT mean = {pitm:.3f} | "
              f"actual/model mean = {ratio:.3f} | PIT deciles {h.tolist()}{flag}", file=sys.stderr)
    # ---- RELIABILITY BY PROBABILITY BUCKET (calibration a bettor can read) ----
    # For each player-week, place synthetic prop lines at fixed offsets from the model
    # median (NOT at model quantiles, which would be circular), compute the model's
    # P(under line) and P(over line), bucket by predicted probability, and report the
    # realized hit rate per bucket. A calibrated 72% bucket should win ~72%.
    calib = []
    for mk, S, y, offs in [("receptions", recM, y_rec, [0.5, 1.5, 2.5, 3.5]),
                           ("rec_yards", ydsM, y_yds, [5, 10, 15, 20, 30])]:
        med = np.median(S, axis=1)
        for o in offs:
            for side, L, in [("Under", med + o), ("Over", np.maximum(med - o, 0.5))]:
                if mk == "receptions":
                    L = np.floor(L) + 0.5 if side == "Under" else np.ceil(L) - 0.5
                    L = np.maximum(L, 0.5)
                p = (S < L[:, None]).mean(1) if side == "Under" else (S > L[:, None]).mean(1)
                hit = (y < L) if side == "Under" else (y > L)
                calib.append(pd.DataFrame({"market": mk, "side": side, "p_model": p, "hit": hit.astype(float)}))
    C = pd.concat(calib, ignore_index=True)
    bins = [0.5, 0.6, 0.7, 0.8, 0.9, 1.0001]
    C["bucket"] = pd.cut(C.p_model, bins, right=False, labels=["50-60", "60-70", "70-80", "80-90", "90+"])
    rel = C.dropna(subset=["bucket"]).groupby(["market", "side", "bucket"], observed=True).agg(
        n=("hit", "size"), p_model_mean=("p_model", "mean"), hit_rate=("hit", "mean")).reset_index()
    print("\n=== Reliability: model probability bucket vs realized hit rate ===", file=sys.stderr)
    for _, r in rel.iterrows():
        print(f"  {r.market:10s} {r.side:5s} {r.bucket:>6s}: n={int(r.n):5d} model {r.p_model_mean:.3f} realized {r.hit_rate:.3f} ({r.hit_rate - r.p_model_mean:+.3f})", file=sys.stderr)
    rel_out = Path(args.out); rel_out.mkdir(parents=True, exist_ok=True)
    rel.to_csv(rel_out / ("reliability_%d%s.csv" % (args.season, ("_" + args.tag) if args.tag else "")), index=False)
    diff_rec = (res.crps_rec_baseA - res.crps_rec_model).mean()
    diff_yds = (res.crps_yds_baseA - res.crps_yds_model).mean()
    print(f"  model-A diff receptions: {diff_rec:+.4f}   yards: {diff_yds:+.4f}", file=sys.stderr)

    tag = args.tag or f"{args.env}_opp{args.opponent}_{args.opp_level}_{args.opp_mode}_k{int(args.opp_k0)}"
    res.to_pickle(OUT / f"backtest_{tag}_results.pkl")
    if args.compare_to:
        ref = pd.read_pickle(args.compare_to)
        d = res.merge(ref, on=["team", "week", "gsis_id"], suffixes=("", "_ref"))
        brng = np.random.default_rng(1)
        print(f"\n=== Paired game-block bootstrap, THIS run vs {Path(args.compare_to).name}, model CRPS only (positive = this better) ===", file=sys.stderr)
        for subset_name, dd in [("all games", d), ("|spread|>=7", d[d.abs_spread >= 7])]:
          if len(dd) < 50: continue
          print(f"  -- {subset_name}, N={len(dd)} --", file=sys.stderr)
          for mk in ["rec", "yds"]:
            d = dd
            diff = d[f"crps_{mk}_model_ref"] - d[f"crps_{mk}_model"]
            # `include_groups` is pandas 2.2+; this repo pins 1.5.3, where it is a TypeError.
            # Selecting the two columns before apply() is equivalent and works on both.
            cols = [f"crps_{mk}_model_ref", f"crps_{mk}_model"]
            g = d.groupby("game_id")
            sums = g[cols].apply(lambda x: (x[cols[0]] - x[cols[1]]).sum())
            cnt = g.size()
            idx = brng.integers(0, len(sums), size=(2000, len(sums)))
            boot = sums.values[idx].sum(1) / cnt.values[idx].sum(1)
            lo, hi = np.percentile(boot, [2.5, 97.5])
            print(f"    {mk}: {diff.mean():+.4f}  95% CI ({lo:+.4f}, {hi:+.4f})  {'excludes 0' if lo > 0 or hi < 0 else 'includes 0'}", file=sys.stderr)
    json.dump({"env": args.env, "opponent": args.opponent, "N": len(res),
               "crps_rec_model": float(res.crps_rec_model.mean()), "crps_rec_baseA": float(res.crps_rec_baseA.mean()),
               "crps_yds_model": float(res.crps_yds_model.mean()), "crps_yds_baseA": float(res.crps_yds_baseA.mean()),
               "crps_rec_indep": float(res.crps_rec_indep.mean()),
               "crps_yds_indep": float(res.crps_yds_indep.mean()),
               "sampler": "model.simulate_team_game (joint, shared with the live scorer)",
               "team_targets_r": r_team_targets,
               "rec_dispersion": rec_fit, "shape_ypc": shape_ypc},
              open(OUT / f"backtest_{tag}_summary.json", "w"), indent=2)


if __name__ == "__main__":
    main()
