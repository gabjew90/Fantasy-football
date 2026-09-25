"""Shared model core for nfl-prop-research.

Pure model logic, no network I/O and no odds fetching. `score_game.py` (live, one
game) and `backtest.py` (walk-forward validation across many games) both call this
module so the model that gets validated is exactly the model that gets used.

Everything here operates on already-loaded pandas frames built from nflverse CSVs.
"""
import numpy as np
import pandas as pd
import re

# ---------------------------------------------------------------- name matching
def norm_name(s):
    """Normalise a player name for joining across sources that disagree on
    punctuation and suffixes: 'D.J. Moore' == 'DJ Moore', 'Luther Burden III' ==
    'Luther Burden'. Used for snap counts AND the odds-API join -- the odds join
    previously used exact string match with no normalisation, so 'D.J. Moore' from
    a book would drop the prop silently."""
    if not isinstance(s, str):
        return s
    s = s.lower().replace(".", "").replace("'", "").replace("-", " ")
    s = re.sub(r"\b(jr|sr|ii|iii|iv|v)\b", "", s)
    return " ".join(s.split())


def name_key_loose(s):
    """Fallback join key: first initial + surname. Catches nickname/full-name splits
    that norm_name cannot ("Joshua Palmer" on a sportsbook vs "Josh Palmer" on the
    roster -- a real ACT receiver whose props were being silently dropped). Looser than
    norm_name, so it is only consulted after an exact normalised match fails."""
    n = norm_name(s)
    if not isinstance(n, str):
        return n
    parts = n.split()
    return f"{parts[0][0]} {parts[-1]}" if len(parts) >= 2 else n


def is_team_entry(s):
    """Sportsbooks post team defense/special-teams entries in the same player field.
    They are not players and must not be reported as name-join failures."""
    t = str(s).lower()
    return any(k in t for k in ("d/st", " dst", "defense", "special teams"))


# ---------------------------------------------------------------- shrinkage
def blend(own, n, prior, k0):
    """Shrink `own` (estimated from `n` opportunity units) toward `prior` by k0."""
    if pd.isna(prior):
        return own
    if pd.isna(own) or n <= 0:
        return prior
    w = n / (n + k0)
    return w * own + (1 - w) * prior


def blended_rate(own_prior, n_prior, slot_prior, k0, *,
                 cur_num=None, cur_den=None, cur_rate=None,
                 role_scale=1.0, scale_role=False,
                 new_team=False, opp_mult=1.0, clip=None):
    """The two-stage shrinkage every player rate goes through.

      stage 1  the player's PRIOR-SEASON rate is shrunk toward his slot's
               league prior, giving an individual prior;
      stage 2  the partial CURRENT season is shrunk toward that individual
               prior, weighted by the opportunities behind it.

    WHY THIS LIVES IN model.py. Only the live scorer implemented both stages.
    backtest.py blended the current season straight to the slot prior and never
    touched the prior-season individual rate at all -- so the component
    methodology.md flags as unvalidated ("the pre-week-5 prior blend") was
    precisely the one the backtest could not see. Two implementations of the
    same idea, one of them measured and the other one shipped. Now there is
    one, and the backtest exercises the blend that actually prices props.

    `n_prior` and `cur_den` are in OPPORTUNITY units (team targets for shares,
    own targets for catch rate and ypt, carries for ypc), matching how k0 was
    tuned. Returns (final, chain); the chain is the evidence trail the report
    renders and the ledger stores.
    """
    if new_team:
        # A rate carried over from another team is a weak prior about the role
        # here, so it is capped at half weight rather than trusted in full.
        n_prior = min(n_prior, k0)
    ind = blend(own_prior, n_prior, slot_prior, k0)
    scaled = False
    if scale_role and isinstance(ind, float) and not pd.isna(ind) and role_scale != 1.0:
        ind *= role_scale
        scaled = True
    # Callers hold the current season either as a numerator/denominator pair
    # (the scorer, counting this week's targets) or as an already-divided rate
    # with its opportunity count (the backtest, aggregating prior weeks).
    # Reconstructing a numerator just to divide it again loses precision and
    # breaks when the rate is NaN but the denominator is not.
    if cur_rate is None:
        cur_rate = (cur_num / cur_den) if (cur_den is not None and cur_den > 0) \
            else float("nan")
    if pd.isna(cur_rate):
        cur_rate = float("nan")
    n_cur = float(cur_den) if (cur_den is not None and pd.notna(cur_rate)) else 0.0
    final = ind if pd.isna(cur_rate) else blend(cur_rate, n_cur, ind, k0)
    if opp_mult != 1.0 and pd.notna(final):
        final = float(final) * opp_mult
        if clip is not None:
            final = float(np.clip(final, *clip))
    chain = dict(own_prior=own_prior, slot_prior=slot_prior, indiv_prior=ind,
                 scaled=scaled, cur_rate=cur_rate, cur_num=cur_num,
                 cur_den=cur_den, n_cur=n_cur,
                 w_cur=(n_cur / (n_cur + k0)) if pd.notna(cur_rate) else 0.0,
                 final=final, k0_used=k0)
    return final, chain


# Per-rate shrinkage constants, in OPPORTUNITY units (targets/carries/goal-line
# touches), not games. A rate estimated from few opportunities should be trusted
# less than one estimated from many, regardless of how many games produced them.
# Values below are fit by build_priors.py's tune_k0s() on a held-out 2025 fold
# (weeks 5-6 fit / 7-8 score) and stored in priors_{season}_params.json; these are
# fallback defaults only, used if a params file lacks the key (e.g. an older
# bundle).
DEFAULT_K0 = {
    "target_share": 16.0,   # opportunity units = team targets over the games counted
    "catch_rate":    8.0,   # opportunity units = the player's own targets
    "ypt":          12.0,
    "rush_share":   10.0,   # opportunity units = team carries over the games counted
    "ypc":          20.0,
    "i10_target_share": 6.0,
    "i10_carry_share":  6.0,
}


def normalize_depth_charts(dc, kick_lookup=None):
    """Return team/week/gsis_id/slot from either nflverse depth-chart schema.

    Modern (2025+): timestamped snapshots with `dt`, `team`, `pos_abb`, `pos_rank`.
    The pre-game snapshot is the latest one strictly before kickoff, which is why
    kick_lookup {(team, week): kickoff_utc} is needed.
    Legacy (<=2024): already one row per team-week, with `club_code`, `depth_team`
    (the rank) and `position`. No timestamp, so no kickoff filter is possible; these
    are published weekly and treated as pre-game.

    Without this, any backtest on a season before 2025 dies on a missing `dt` column,
    which is what blocked the second-season validation.
    """
    cols = set(dc.columns)
    out = []
    if "dt" in cols:
        d = dc.copy()
        d["dt"] = pd.to_datetime(d["dt"], errors="coerce", utc=True)
        d = d.dropna(subset=["dt"])
        d = d[d.pos_abb.isin(["QB", "RB", "WR", "TE"])]
        for (team, wk), kt in (kick_lookup or {}).items():
            sub = d[(d.team == team) & (d.dt < kt)]
            if sub.empty:
                continue
            sub = sub[sub.dt == sub.dt.max()]
            for pos, mx in [("QB", 1), ("RB", 2), ("WR", 3), ("TE", 1)]:
                for _, x in sub[(sub.pos_abb == pos) & (sub.pos_rank <= mx)].iterrows():
                    out.append({"team": team, "week": wk, "gsis_id": x.gsis_id,
                                "slot": f"{pos}{int(x.pos_rank)}"})
    else:
        d = dc.copy()
        team_col = "club_code" if "club_code" in cols else "team"
        rank_col = "depth_team" if "depth_team" in cols else "pos_rank"
        d = d[d["position"].isin(["QB", "RB", "WR", "TE"])]
        # The legacy schema lists the SAME position across offense AND special teams:
        # a WR row with depth_team=1 may be the starting split end or the punt returner
        # (depth_position PR/KR/KOR under position WR; 921 PR rows in 2024 alone). Keep
        # only offensive rows whose depth_position equals the position, otherwise "WR1"
        # is a coin flip between a starter and a return man. This, not the K0 or the
        # priors, was the source of the 5% receptions under-prediction on 2024.
        if "formation" in d.columns:
            d = d[d["formation"].astype(str).str.strip() == "Offense"]
        if "depth_position" in d.columns:
            d = d[d["depth_position"].astype(str).str.strip() == d["position"].astype(str).str.strip()]
        d[rank_col] = pd.to_numeric(d[rank_col], errors="coerce")
        d["week"] = pd.to_numeric(d["week"], errors="coerce")
        d = d.dropna(subset=[rank_col, "gsis_id", "week"])
        # kind="mergesort" is STABLE; pandas' default quicksort is not, so ties on
        # depth_team could otherwise assign WR1 nondeterministically across runs.
        d = d.sort_values([team_col, "week", "position", rank_col], kind="mergesort")
        d = d.drop_duplicates([team_col, "week", "position", "gsis_id"])
        d["_ord"] = d.groupby([team_col, "week", "position"]).cumcount() + 1
        for pos, mx in [("QB", 1), ("RB", 2), ("WR", 3), ("TE", 1)]:
            sub = d[(d["position"] == pos) & (d["_ord"] <= mx)]
            for _, x in sub.iterrows():
                out.append({"team": x[team_col], "week": int(x["week"]), "gsis_id": x.gsis_id,
                            "slot": f"{pos}{int(x['_ord'])}"})
        return pd.DataFrame(out).drop_duplicates(["team", "week", "gsis_id"])
    return pd.DataFrame(out).drop_duplicates(["team", "week", "gsis_id"])


DRIFT_CLIP = (0.85, 1.15)   # never bound on 2024 or 2025; guards a thin early sample only


def league_drift_ratio(team_week_volume, target_week, recent_games=3, min_prior_weeks=4):
    """League-wide recent-to-expanding volume ratio, for correcting within-season drift.

    A per-team expanding mean is the low-variance way to estimate a team's volume, but it
    LAGS league-wide drift: total targets/game rose 3.4% inside 2024 and fell 4.2% inside
    2025, so an expanding mean read ~4% low in one season and ~2% high in the other. A
    trailing per-team window fixes the bias but adds real noise (per-team 4-game means are
    volatile), which cost CRPS when tested.

    This separates the two problems: keep the expanding mean per team for the LEVEL, and
    scale it by a single league-wide ratio for the DRIFT. The ratio is estimated across
    all 32 teams at once, so it is nearly noise-free compared with a per-team window.

    team_week_volume: DataFrame with columns week, team_targets, team_carries (all teams).
    Returns {"targets": ratio, "carries": ratio}, clipped to [0.85, 1.15] so a thin early
    sample cannot produce a wild correction. Returns 1.0 before min_prior_weeks.
    """
    prior = team_week_volume[team_week_volume.week < target_week]
    weeks_avail = sorted(prior.week.unique())
    if len(weeks_avail) < min_prior_weeks:
        return {"targets": 1.0, "carries": 1.0}
    recent_weeks = weeks_avail[-recent_games:]
    out = {}
    for col, key in [("team_targets", "targets"), ("team_carries", "carries")]:
        exp_mean = prior[col].mean()
        rec_mean = prior[prior.week.isin(recent_weeks)][col].mean()
        r = (rec_mean / exp_mean) if exp_mean > 0 else 1.0
        out[key] = float(np.clip(r, *DRIFT_CLIP))
    return out


# ---------------------------------------------------------------- team environment
def market_environment_fitted(team_spread, total, mkt_fit, team_pace_blend, team_pr_blend,
                               pace_weight=0.5):
    """Team plays and pass rate from FITTED market coefficients (build_priors.py) rather
    than a hand-set shift, blended with the team's own pace/pass-rate history.

    team_spread: this team's own spread (negative = favored).
    team_pace_blend / team_pr_blend: the team's history-blended plays and pass rate.
    pace_weight: how much of the market's fitted prediction to take vs the team's own
    history. The fit's R^2 on 2025 is ~0.02 for plays and ~0.04 for pass rate: the market
    explains almost none of the between-game variance in team volume, so an aggressive
    weight is not justified by the data.
    """
    if not mkt_fit:
        return {"plays": team_pace_blend, "pass_rate": team_pr_blend,
                "implied_points": None, "source": "history (no market fit available)"}
    fp, fr = mkt_fit["plays"], mkt_fit["pass_rate"]
    mkt_plays = fp["intercept"] + fp["per_spread_pt"] * team_spread + fp["per_total_pt"] * total
    mkt_pr = fr["intercept"] + fr["per_spread_pt"] * team_spread + fr["per_total_pt"] * total
    w = float(np.clip(pace_weight, 0.0, 1.0))
    return {"plays": (1 - w) * team_pace_blend + w * mkt_plays,
            "pass_rate": float(np.clip((1 - w) * team_pr_blend + w * mkt_pr, 0.35, 0.75)),
            "implied_points": (total - team_spread) / 2, "source": "market-fitted"}


def market_implied_environment(spread_home, total, home_pass_rate, away_pass_rate,
                                league_plays_per_game, pass_rate_slope=None,
                                plays_slope=None, league_total=None):
    """Convert a same-book spread/total into implied per-team scoring, then plays
    and pass rate. `spread_home` is the home team's spread (negative = favored),
    matching both nflverse `spread_line` and Odds API `point` sign convention.

    Returns {team_side: {'implied_points':..., 'plays':..., 'pass_rate':...}} for
    'home' and 'away'. Plays are apportioned using the classic pace-and-script
    heuristic: a bigger favorite runs more, faces the same total plays roughly
    evenly, so we hold plays close to league average and shift pass rate by score
    differential rather than inventing a plays model we cannot validate.
    """
    implied_home = (total - spread_home) / 2
    implied_away = (total + spread_home) / 2
    # home_pass_rate / away_pass_rate MUST be the teams' own (history-blended) rates,
    # not the league rate. Round-5 first version passed the league rate for both,
    # which erased team identity (a pass-heavy offense projected the same as a
    # run-heavy one) and is one reason "market" showed no CRPS gain over a constant.
    # pass_rate_slope: change in a team's pass rate per point of ITS OWN spread
    # (positive spread = underdog = passes more). Fit by build_priors/backtest from
    # prior-season data; the hand-set 0.015-per-7-points default is used only if
    # no fit is supplied. plays_slope: change in a team's plays per point of game
    # total above league average.
    slope = pass_rate_slope if pass_rate_slope is not None else 0.015 / 7.0
    shift_home = np.clip(spread_home, -14, 14) * slope
    plays_h = plays_a = league_plays_per_game
    if plays_slope is not None and league_total is not None:
        plays_h = plays_a = league_plays_per_game + plays_slope * (total - league_total)
    return {
        "home": {"implied_points": implied_home, "plays": plays_h,
                 "pass_rate": np.clip(home_pass_rate + shift_home, 0.35, 0.75)},
        "away": {"implied_points": implied_away, "plays": plays_a,
                 "pass_rate": np.clip(away_pass_rate - shift_home, 0.35, 0.75)},
    }


def team_environment(team, cur_team_row, cur_n, pri_team_row, k0_volume,
                      market=None, league_pass_rate=0.58, league_plays=64.0):
    """Blend prior-season and current-season team volume, optionally re-centring
    on a market-implied total when one is supplied.

    market, if given: {'implied_points':..., 'plays':..., 'pass_rate':...} for
    THIS team, from market_implied_environment(). When supplied, targets/carries
    are built from plays x pass_rate instead of the pure history blend, and the
    history blend is used only for the pass/rush split's stability check.
    Disclosure required wherever this is used: the environment then comes from
    the same book's own price, so it cannot itself be cited as an edge on the
    total or spread -- only player-level allocation within that total can be.
    """
    out = {}
    for c in ["targets", "carries", "i10_targets", "i10_carries", "pass_td", "rush_td"]:
        own = cur_team_row.get(c, np.nan) if cur_team_row is not None else np.nan
        pri = pri_team_row.get(c, np.nan) if pri_team_row is not None else np.nan
        out[c] = blend(own, cur_n, pri, k0_volume)
    out["source"] = "history"
    if market is not None:
        plays = market["plays"]
        pass_rate = market["pass_rate"]
        out["targets"] = plays * pass_rate
        out["carries"] = plays * (1 - pass_rate)
        # touchdowns scale with implied points at the league rate; goal-line shares
        # of targets/carries carry over unchanged from the history blend since the
        # market doesn't speak to WHERE on the field a team's plays happen
        td_per_pt = out.get("_league_td_per_point", 0.1055)
        total_td = market["implied_points"] * td_per_pt
        # keep the history blend's pass/rush TD split ratio, apply to the new total
        hist_total_td = out["pass_td"] + out["rush_td"]
        if hist_total_td > 0:
            out["pass_td"] = total_td * out["pass_td"] / hist_total_td
            out["rush_td"] = total_td * out["rush_td"] / hist_total_td
        out["source"] = "market"
    return out


# ---------------------------------------------------------------- opponent adjustment
def build_opponent_table(pbp, roles):
    """Per-team, per-position-group defensive efficiency allowed, relative to
    league average, from a season of play-by-play. Position group, not full
    position, to keep the sample size usable (a full season is still only ~17
    games per defense).
    """
    passes = pbp[(pbp.play_type == "pass") & pbp.receiver_player_id.notna()].copy()
    rushes = pbp[(pbp.play_type == "run") & (pbp.qb_kneel != 1) & pbp.rusher_player_id.notna()].copy()
    role_pos = roles.set_index("gsis_id")["slot"].str.extract(r"([A-Z]+)")[0].to_dict()
    passes["posgrp"] = passes.receiver_player_id.map(role_pos).fillna("OTHER")
    rushes["posgrp"] = rushes.rusher_player_id.map(role_pos).fillna("OTHER")

    def agg(df, ycol):
        df = df.assign(**{ycol: df[ycol].fillna(0.0)})   # per-target, incompletions count as 0
        g = df.groupby(["defteam", "posgrp"]).agg(
            plays=("play_id", "size"), yards=(ycol, "sum"), var_play=(ycol, "var"),
            completions=("complete_pass", "sum") if ycol == "receiving_yards" else ("play_id", "size"))
        return g

    passes_all = passes.copy(); passes_all["posgrp"] = "ALL"
    rushes_all = rushes.copy(); rushes_all["posgrp"] = "ALL"
    passes = pd.concat([passes, passes_all]); rushes = pd.concat([rushes, rushes_all])
    pass_def = agg(passes, "receiving_yards")
    rush_def = agg(rushes, "rushing_yards")
    # receiving_yards is NaN on incompletions in nflverse PBP, so .mean() silently
    # returns yards per COMPLETION. The per-team value is yards per TARGET. Mixing them
    # gave every defense a ratio near 0.67 and cut every receiving-yards projection
    # 12-18% regardless of opponent (caught by a reviewer from the report's Under lean).
    # Fill NaN with 0 so numerator and denominator are both per target.
    _p = passes.assign(_ry=passes.receiving_yards.fillna(0.0))
    league_ypt = _p.groupby("posgrp")._ry.sum() / _p.groupby("posgrp").size()
    league_cr = passes.groupby("posgrp").complete_pass.mean()
    league_ypc = rushes.assign(_ry=rushes.rushing_yards.fillna(0.0)).groupby("posgrp")._ry.mean()

    rows = []
    for (team, pg), r in pass_def.iterrows():
        if r.plays < 20 or pg not in league_ypt.index:
            continue
        rows.append({"team": team, "posgrp": pg, "metric": "ypt",
                     "n": int(r.plays), "value": r.yards / r.plays,
                     "league": float(league_ypt[pg]), "var_play": float(r.var_play)})
        rows.append({"team": team, "posgrp": pg, "metric": "catch_rate",
                     "n": int(r.plays), "value": r.completions / r.plays,
                     "league": float(league_cr[pg])})
    for (team, pg), r in rush_def.iterrows():
        if r.plays < 20 or pg not in league_ypc.index:
            continue
        rows.append({"team": team, "posgrp": pg, "metric": "ypc",
                     "n": int(r.plays), "value": r.yards / r.plays,
                     "league": float(league_ypc[pg]), "var_play": float(r.var_play)})
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    # Empirical-Bayes shrinkage constant per (posgrp, metric): k_eb = within / between.
    # within = mean per-play variance of the metric (binomial for catch rate, sample
    # variance of yards for ypt/ypc); between = variance of team ratios minus the
    # sampling noise. If between <= 0 there is no detectable team signal and k_eb is
    # set very large (adjustment becomes a no-op), which is the honest outcome.
    ks = []
    for (pg, met), g in df.groupby(["posgrp", "metric"]):
        ratio = g.value / g.league
        if met == "catch_rate":
            within = float((g.league * (1 - g.league)).mean()) / float(g.league.mean() ** 2)
        else:
            within = float(g["var_play"].mean()) / float(g.league.mean() ** 2) if "var_play" in g else 1.0
        samp_noise = float((within / g.n).mean())
        between = float(ratio.var(ddof=1)) - samp_noise if len(g) > 2 else 0.0
        k_eb = within / between if between > 1e-6 else 1e9
        ks.append({"posgrp": pg, "metric": met, "k_eb": k_eb, "between_var": max(between, 0.0)})
    return df.merge(pd.DataFrame(ks), on=["posgrp", "metric"], how="left")


def opponent_multiplier(opp_table, defteam, posgrp, metric, k0_opp=150.0, mode="fixed"):
    """Multiplicative opponent-efficiency adjustment, shrunk toward 1.0 (league average)
    by plays faced.

    History worth keeping: earlier rounds concluded this adjustment was useless or
    actively harmful (fixed shrinkage measured -0.34 CRPS on reception yards). That
    conclusion was an artifact of a bug in build_opponent_table: the league YPT
    reference was computed with .mean() on a column that is NaN for incompletions,
    which silently returned yards per COMPLETION (10.9) against a per-TARGET team
    value (7.3). Every defense therefore got a ratio near 0.67, and every
    receiving-yards projection was cut 12-18% regardless of opponent. With that
    fixed (2025, team level, k0=150): reception yards +0.056 CRPS, 95% CI
    (+0.006, +0.108), excludes zero. The adjustment helps.

    Defaults: team level, fixed k0=150 plays. Position-group level was retested after
    the fix and remains indistinguishable from no adjustment -- the per-position
    samples are genuinely too thin. mode="eb" uses the empirical-Bayes constant from
    build_opponent_table instead; it also helps (+0.052) but fixed k0=150 is simpler
    and marginally better, so it is the default.
    """
    row = opp_table[(opp_table.team == defteam) & (opp_table.posgrp == posgrp)
                    & (opp_table.metric == metric)]
    if row.empty or row.iloc[0].league <= 0:
        return 1.0
    r = row.iloc[0]
    raw_ratio = r.value / r.league
    k = float(r.k_eb) if (mode == "eb" and "k_eb" in row and pd.notna(r.k_eb)) else k0_opp
    w = r.n / (r.n + k)
    return 1.0 * (1 - w) + raw_ratio * w


# ---------------------------------------------------------------- TD allocation
def td_lambda(env_team, i10_target_share, i10_carry_share, target_share, rush_share,
              f_pass_in10, f_rush_in10):
    """Expected TDs for a player. Goal-line TDs (plays starting inside the 10) are
    allocated by inside-the-10 share; the rest -- roughly half of passing TDs and
    a quarter of rushing TDs league-wide -- by overall target/carry share, since
    that is what a long touchdown actually depends on. Allocating everything by
    goal-line share under-rates explosive/high-volume players and over-rates
    goal-line specialists (verified on 2025: Gibbs 9/18 and J.Williams 8/20 TDs
    came from outside the 10)."""
    return (env_team["pass_td"] * (f_pass_in10 * i10_target_share + (1 - f_pass_in10) * target_share)
            + env_team["rush_td"] * (f_rush_in10 * i10_carry_share + (1 - f_rush_in10) * rush_share))


# ---------------------------------------------------------------- questionable regime
QUESTIONABLE_WEIGHTS = {"normal": 0.55, "limited": 0.30, "out": 0.15}
QUESTIONABLE_SCALE = {"normal": 1.0, "limited": 0.6, "out": 0.0}
# Base rates: of players tagged Questionable in 2025, what fraction played a normal
# snap share, a limited one, or sat out. Stored here as the documented default;
# build_priors.py can refresh QUESTIONABLE_WEIGHTS from data if desired.


def questionable_regimes(mu_base):
    """Return {regime: (probability, adjusted_mu)} for a Questionable player.
    Per modeling_framework.md: run normal/limited/out regimes with stated weights;
    if the regimes disagree enough to change the betting decision, the market_read
    layer should mark the line for the PASS-because-flip rule rather than pricing
    an average of the three."""
    return {reg: (w, mu_base * QUESTIONABLE_SCALE[reg]) for reg, w in QUESTIONABLE_WEIGHTS.items()}


def questionable_flip_check(samples_by_regime, line):
    """True if the Over/Under recommendation would flip depending which
    Questionable regime is realised -- the case where PASS is mandatory regardless
    of the blended number."""
    sides = set()
    for regime, s in samples_by_regime.items():
        p_over = float(np.mean(s > line))
        sides.add(p_over >= 0.5)
    return len(sides) > 1


# ---------------------------------------------------------------- joint simulation
# WIDTH SETTINGS (docs/plans/2026-09-24-yardage-harness.md, step 2). The 2022-25
# harness found every yardage market right on average and too NARROW: shares,
# catch rates and yards per touch were fixed within a game. Each setting below
# lets one of them vary game to game, mean-preserving. None / 0.0 is the old
# sampler EXACTLY (no extra random draws, so output is byte-identical); the
# values the scorer uses are tuned on 2022-23 by backtest.py --tune-width.
#   share_conc  Dirichlet concentration of the split of team targets / carries
#               (a player's share varies around its mean; smaller = wider)
#   catch_conc  Beta concentration of each player's catch rate
#   eff_sd      log-sd of a per-game multiplier on yards per catch / per carry
#   share_conc_qb  the starting QB's share of carries, varied on its own (Beta)
#               while the rest split what is left; None = he is one more
#               component of the carries Dirichlet, as before
#   eff_sd_qb   his own yards-per-carry swing; None = eff_sd_rush
WIDTH_OFF = {"share_conc_targets": None, "share_conc_carries": None, "catch_conc": None,
             "eff_sd_rec": 0.0, "eff_sd_rush": 0.0, "share_conc_qb": None, "eff_sd_qb": None}


def validate_width(w):
    """The width settings a file or flag may carry, checked: concentrations
    None or > 0, log-sds >= 0. Documentation keys (note, tuned_on) pass through
    unused; anything else is an error, never silently ignored. Returns the
    settings dict. A concentration of 0 is NOT "off" (it would hand every
    target to one player); off is null."""
    unknown = set(w) - set(WIDTH_OFF) - {"note", "tuned_on"}
    if unknown:
        raise ValueError(f"unknown width settings {sorted(unknown)}; known: {sorted(WIDTH_OFF)}")
    out = {k: w[k] for k in WIDTH_OFF if k in w}
    for k, v in out.items():
        if k.startswith(("share_conc", "catch_conc")):
            if v is not None and not (isinstance(v, (int, float)) and v > 0):
                raise ValueError(f"{k} must be null (off) or > 0, got {v!r}")
        elif k == "eff_sd_qb" and v is None:
            continue                                   # None = inherit eff_sd_rush
        elif not (isinstance(v, (int, float)) and v >= 0):
            raise ValueError(f"{k} must be >= 0, got {v!r}")
    return out


def _allocate(rng, totals, p_norm, conc, fill_last):
    """Split each simulation's team total across the players (+ 'other').

    conc None: fixed shares, sequential conditional binomials (the original
    sampler, call for call). conc > 0: each simulation first draws its own
    shares from Dirichlet(conc * p_norm), so a player's share swings from game
    to game around the same mean."""
    k = len(p_norm)
    alloc = np.zeros((len(totals), k), dtype=int)
    remaining = totals.copy()
    if conc is None:
        rem_p = 1.0
        for j in range(k - 1):
            pj = np.clip(p_norm[j] / rem_p, 0.0, 1.0) if rem_p > 0 else 0.0
            alloc[:, j] = rng.binomial(remaining, pj); remaining = remaining - alloc[:, j]; rem_p -= p_norm[j]
    else:
        g = rng.gamma(np.maximum(conc * p_norm, 1e-9), size=(len(totals), k))
        P = g / g.sum(axis=1, keepdims=True)
        rem_p = np.ones(len(totals))
        for j in range(k - 1):
            pj = np.clip(np.divide(P[:, j], rem_p, out=np.zeros(len(totals)), where=rem_p > 0), 0.0, 1.0)
            alloc[:, j] = rng.binomial(remaining, pj); remaining = remaining - alloc[:, j]; rem_p = rem_p - P[:, j]
    if fill_last:
        alloc[:, -1] = remaining
    return alloc


def _allocate_qb_first(rng, totals, p_norm, qb, conc_qb, conc_rest):
    """Split carries with the starting QB's share varying on its own.

    His share each simulation ~ Beta(conc_qb * q, conc_qb * (1 - q)); everyone
    else (and 'other') splits the remainder in proportion to their shares,
    through a Dirichlet at conc_rest when it is set. Means are preserved: a QB
    scramble does not come out of a running back's carries the way two backs
    compete for the same ones, so the RB-tuned concentration overstated his
    swing (2022-25: 15% of his outcomes outside p10-p90, 26% with none)."""
    n, k = len(totals), len(p_norm)
    q = float(p_norm[qb])
    P = np.zeros((n, k))
    P[:, qb] = rng.beta(max(conc_qb * q, 1e-9), max(conc_qb * (1.0 - q), 1e-9), size=n)
    rest = [j for j in range(k) if j != qb]
    base = p_norm[rest] / max(1.0 - q, 1e-12)
    if conc_rest is not None:
        g = rng.gamma(np.maximum(conc_rest * base, 1e-9), size=(n, len(rest)))
        D = g / g.sum(axis=1, keepdims=True)
    else:
        D = np.broadcast_to(base, (n, len(rest)))
    P[:, rest] = (1.0 - P[:, [qb]]) * D
    alloc = np.zeros((n, k), dtype=int)
    remaining = totals.copy()
    rem_p = np.ones(n)
    for j in range(k - 1):
        pj = np.clip(np.divide(P[:, j], rem_p, out=np.zeros(n), where=rem_p > 0), 0.0, 1.0)
        alloc[:, j] = rng.binomial(remaining, pj); remaining = remaining - alloc[:, j]; rem_p = rem_p - P[:, j]
    return alloc


def _game_multiplier(rng, n_sim, sd):
    """Mean-one lognormal multiplier, one per simulation (a player's game)."""
    return np.exp(sd * rng.standard_normal(n_sim) - 0.5 * sd * sd)


def simulate_team_rush(rng, n_sim, team_carries_mean, carries_r, rush_shares, ypc, carry_resid,
                       width=None, player_resid=None, player_kneel=None, qb_index=None):
    """One team's carries, drawn jointly, and each player's rushing yards.

    1. Team carries ~ NegBinomial(team_carries_mean, carries_r), one draw per
       simulation shared by every player on the team.
    2. Split across the players, plus an 'other' bucket for the share the
       eligible set does not cover, by sequential conditional binomials.
    3. Each carry gains the player's mean yards per carry plus a residual drawn
       from the prior season's league carry-yardage grid, so heavy tails and
       negative runs survive.

    score_game.py and backtest.py both call this, so the harness grades the
    sampler that prices the props. The RNG call order is the one the scorer
    ran inline before it moved here (its output is byte-identical).
    Returns (carries per player, yards per player, team carries), the lists
    in `rush_shares` order.

    QB RUSHING (plan step 3). `qb_index` names the starting QB, for the
    QB-only width settings (share_conc_qb, eff_sd_qb). `player_resid[j]`, when given, replaces the league
    carry grid for player j (a QB's carries are shaped differently); it must be
    the league grid's length, so the draw consumes the same randomness and
    every other player's numbers are unchanged. `player_kneel[j]`, when given,
    is a grid of per-game kneel-down yards added to player j's total -- the
    book settles a QB's rushing yards with them. Kneels come from a child
    stream (`rng.spawn`), which does not advance `rng`: adding them moves no
    one else's draws.
    """
    w = {**WIDTH_OFF, **(width or {})}
    if player_resid is not None and any(
            r is not None and len(r) != len(carry_resid) for r in player_resid):
        raise ValueError("a per-player carry grid must be the league grid's length")
    rs = np.clip(np.asarray(rush_shares, dtype=float), 0, None)
    rest = max(1.0 - rs.sum(), 0.0)
    p_norm = np.append(rs, rest); p_norm = p_norm / p_norm.sum()
    mu_c = max(team_carries_mean, 1e-6)
    tc_draw = rng.negative_binomial(carries_r, carries_r / (carries_r + mu_c), size=n_sim)
    if qb_index is not None and w["share_conc_qb"]:
        alloc = _allocate_qb_first(rng, tc_draw, p_norm, int(qb_index), w["share_conc_qb"], w["share_conc_carries"])
    else:
        alloc = _allocate(rng, tc_draw, p_norm, w["share_conc_carries"], fill_last=False)
    carries, yards = [], []
    for j in range(len(rs)):
        car = alloc[:, j]
        rush = np.zeros(n_sim)
        if car.max() > 0:
            mx = int(car.max())
            grid = carry_resid if player_resid is None or player_resid[j] is None else player_resid[j]
            draws = rng.choice(grid, size=(n_sim, mx)) + float(ypc[j])
            rush = (draws * (np.arange(mx)[None, :] < car[:, None])).sum(1)
        sd = w["eff_sd_rush"]
        if qb_index is not None and j == int(qb_index) and w["eff_sd_qb"] is not None:
            sd = w["eff_sd_qb"]
        if sd:
            # the game's yards per carry = ypc x a mean-one multiplier; the
            # carry residuals stay as drawn
            rush = rush + car * float(ypc[j]) * (_game_multiplier(rng, n_sim, sd) - 1.0)
        carries.append(car.astype(float)); yards.append(rush)
    if player_kneel is not None and any(k is not None for k in player_kneel):
        kneel_rng = rng.spawn(1)[0]
        for j, grid in enumerate(player_kneel):
            if grid is not None:
                yards[j] = yards[j] + kneel_rng.choice(np.asarray(grid, dtype=float), size=n_sim)
    return carries, yards, tc_draw


def kneel_grid(params, team_spread):
    """The per-game kneel-down yards grid for a team's QB, by the team's own
    pregame spread (POSITIVE = favoured). No spread yet: the grid over every
    team-game. None only when the priors predate the QB model."""
    k = params.get("qb_kneel_yards_by_spread")
    if not k:
        return None
    if team_spread is None or pd.isna(team_spread):
        return k.get("pooled")
    return k["grids"][int(np.digitize([float(team_spread)], k["edges"])[0])]


def own_spread_from_book(book_home_spread, is_home):
    """The team's own pregame spread, POSITIVE = favoured, from a book's home
    spread (NEGATIVE = home favoured: 'KC -7'). nflverse's spread_line is the
    opposite sign; the kneel grids and market fits use positive = favoured."""
    if book_home_spread is None or pd.isna(book_home_spread):
        return None
    return -float(book_home_spread) if is_home else float(book_home_spread)


def starter_qb_index(positions, rush_shares):
    """Which of a team's active players is the starting QB: the QB with the
    largest expected carry share. Not the depth-chart slot -- when QB1 is ruled
    out, the backup who starts keeps his QB2 slot."""
    qbs = [j for j, pos in enumerate(positions) if str(pos).startswith("QB")]
    if not qbs:
        return None
    return max(qbs, key=lambda j: float(rush_shares[j]) if rush_shares[j] == rush_shares[j] else -1.0)


def simulate_team_game(rng, n_sim, team_volume_mean, team_volume_r, player_shares,
                        player_catch_rates, player_ypt, per_catch_shape, other_bucket=True, width=None):
    """Draw one team's targets jointly with all eligible receivers in one pass.

    1. Team targets ~ NegBinomial(team_volume_mean, team_volume_r) -- one draw per
       simulation, shared by every player on the team this simulation.
    2. Those targets are split across players (plus an 'other' bucket absorbing
       the share the eligible set doesn't cover) via Multinomial(shares).
    3. Each player's catches | his own targets ~ Binomial(his catch rate).
    4. Yards | catches ~ sum of per-catch Gamma draws.

    This makes teammates' receptions NEGATIVELY correlated within a simulation
    (more targets to A means fewer available for B, for a fixed team total) and
    makes every player's outcome share the team's own play-count variance --
    both true of real football and both absent from independent per-player draws.
    Returns {player_index: (receptions_array, yards_array)}, plus team_targets_array.
    """
    w = {**WIDTH_OFF, **(width or {})}
    names = list(player_shares.keys())
    shares = np.array([player_shares[n] for n in names], dtype=float)
    shares = np.clip(shares, 0, None)
    if other_bucket:
        rest = max(1.0 - shares.sum(), 0.0)
        shares = np.append(shares, rest)
    else:
        s = shares.sum()
        shares = shares / s if s > 0 else shares

    p = team_volume_r / (team_volume_r + max(team_volume_mean, 1e-6))
    team_targets = rng.negative_binomial(team_volume_r, p, size=n_sim)

    # vectorized multinomial: sequential conditional binomials, no Python loop
    p_norm = shares / shares.sum()
    alloc = _allocate(rng, team_targets, p_norm, w["share_conc_targets"], fill_last=True)

    out = {}
    for j, name in enumerate(names):
        cr = max(player_catch_rates.get(name, 0.3), 0.05)
        if w["catch_conc"]:
            # this game's catch rate ~ Beta around the player's rate
            c = w["catch_conc"]
            cr_game = rng.beta(max(c * cr, 1e-3), max(c * (1.0 - cr), 1e-3), size=n_sim)
            rec = rng.binomial(alloc[:, j], cr_game).astype(float)
        else:
            rec = rng.binomial(alloc[:, j], cr).astype(float)
        ypt = max(player_ypt.get(name, 7.0), 0.5)
        ypc = ypt / cr
        shape_total = np.clip(rec, 0, 25) * per_catch_shape
        yds = np.where(rec > 0, rng.gamma(np.maximum(shape_total, 1e-6), ypc / per_catch_shape), 0.0)
        if w["eff_sd_rec"]:
            yds = yds * _game_multiplier(rng, n_sim, w["eff_sd_rec"])
        out[name] = (rec, yds)
    return out, team_targets
