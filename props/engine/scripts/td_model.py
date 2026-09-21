"""Touchdowns as a first-class model, built around the touchdown event.

LAYER 1 (this file, so far): each team's touchdown count for a game as a
DISTRIBUTION, split into scoring channels.

  mean      = market implied points x the team's touchdowns-per-point ratio,
              shrunk toward the league ratio by a pseudo-count in points;
  shape     = negative binomial with dispersion r (r -> infinity is Poisson),
              fitted rather than assumed;
  channels  = QB rush, rush inside the 5, rush from distance, red-zone pass,
              explosive pass, and defence/special teams, with each team's mix
              shrunk toward the league's.

What this replaces: the engine converts implied points to touchdowns with ONE
league constant (0.1055 per point), treats the count as Poisson, and splits it
into pass and rush only. Each of those three is a choice the backtest in
td_backtest.py tests against the simpler version rather than assumes.

Stdlib + numpy + pandas only. This runs in the chat sandbox and on Actions,
neither of which has polars or pyarrow.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

CHANNELS = ("qb_rush", "rush_in5", "rush_far", "pass_rz", "pass_far", "dst_other")
OFFENSIVE = CHANNELS[:5]   # dst_other never reaches an offensive player's prop
MAX_TD = 15            # support for count distributions; P(16+ TDs) is ~0

# LAYER 1, FROZEN 2026-09-21: league touchdowns-per-point ratio, binomial over
# 11 trials, linear in implied points.
#
# The team-specific ratio is NOT frozen in. It beat the league ratio on the
# 2024-25 test seasons by CRPS 0.0012, but at the best setting the league
# prior carries the weight of ~130 games, so a team's own history barely
# moves it. A component worth 0.0012 that behaves like the league average is
# not worth carrying into layers 2-5.
#
# GAMMA IS PROVISIONAL. Elasticity to the implied total (0.25) was the second
# largest gain, but it rests on 2022-25 alone and could be either of two
# things with opposite meanings: high-total teams converting more of their
# points into touchdowns, or high-total teams simply outscoring their market
# total. It stays out of the frozen spec until the points decomposition and
# an older-season check say which.
LAYER1 = {"k_points": None, "trials": 11, "gamma": 0.0}
GAMMA_PROVISIONAL = 0.25

PBP_COLS = ["game_id", "season", "week", "season_type", "posteam", "defteam",
            "td_team", "touchdown", "pass_touchdown", "rush_touchdown",
            "yardline_100", "rusher_player_id", "play_type"]


# ------------------------------------------------------------------ events

def classify_tds(pbp: pd.DataFrame, qb_ids: set[str]) -> pd.DataFrame:
    """One row per touchdown, with the team that scored it and its channel.

    Channels are exclusive and exhaustive over every touchdown a team scores:
      qb_rush    a rushing TD by a quarterback, from any distance;
      rush_in5   any other rushing TD from the 5 or closer at the snap;
      rush_far   any other rushing TD from beyond the 5;
      pass_rz    a passing TD thrown from the red zone (20 or closer);
      pass_far   a passing TD from beyond the 20 -- the explosive play;
      dst_other  everything else: return and defensive TDs, plus the rare
                 offensive fumble recovery in the end zone. None of these
                 goes to an offensive skill player's anytime-TD prop.
    """
    d = pbp[(pbp["season_type"] == "REG") & (pbp["touchdown"] == 1)
            & pbp["td_team"].notna()].copy()
    own = d["td_team"] == d["posteam"]
    rush = own & (d["rush_touchdown"] == 1)
    pas = own & (d["pass_touchdown"] == 1)
    qb = rush & d["rusher_player_id"].isin(qb_ids)
    yl = d["yardline_100"]
    d["channel"] = np.select(
        [qb, rush & (yl <= 5), rush, pas & (yl <= 20), pas],
        ["qb_rush", "rush_in5", "rush_far", "pass_rz", "pass_far"],
        default="dst_other")
    return d[["game_id", "season", "week", "td_team", "channel"]].rename(
        columns={"td_team": "team"})


# FRANCHISE CODES. nflverse play-by-play uses each franchise's CURRENT code
# for every season; the schedule file uses the code of the TIME. Joined
# unnormalised, every touchdown by Oakland (2015-19), San Diego (2015-16) and
# St. Louis (2015) matched nothing and was recorded as ZERO -- and a team-
# specific ratio then "learned" that those teams never score, which looked
# like a 0.042 CRPS gain. Both sides are mapped to the current code.
TEAM_ALIASES = {"OAK": "LV", "SD": "LAC", "STL": "LA"}


def _norm_team(s: pd.Series) -> pd.Series:
    return s.replace(TEAM_ALIASES)


def team_games(schedule: pd.DataFrame, tds: pd.DataFrame) -> pd.DataFrame:
    """One row per team per regular-season game, zero-touchdown games
    included, with points scored, the market's implied points, and the
    touchdown count by channel.

    nflverse `spread_line` is positive when the HOME team is favoured, so the
    home side's implied points are (total + spread) / 2.
    """
    g = schedule[(schedule["game_type"] == "REG") & schedule["home_score"].notna()].copy()
    g["home_team"], g["away_team"] = _norm_team(g["home_team"]), _norm_team(g["away_team"])
    tds = tds.assign(team=_norm_team(tds["team"]))
    home = pd.DataFrame({"game_id": g["game_id"], "season": g["season"], "week": g["week"],
                         "team": g["home_team"], "opp": g["away_team"],
                         "points": g["home_score"],
                         "implied": (g["total_line"] + g["spread_line"]) / 2,
                         "spread": g["spread_line"]})
    away = pd.DataFrame({"game_id": g["game_id"], "season": g["season"], "week": g["week"],
                         "team": g["away_team"], "opp": g["home_team"],
                         "points": g["away_score"],
                         "implied": (g["total_line"] - g["spread_line"]) / 2,
                         "spread": -g["spread_line"]})
    tg = pd.concat([home, away], ignore_index=True)
    counts = (tds.groupby(["game_id", "team", "channel"]).size()
              .unstack("channel", fill_value=0).reindex(columns=list(CHANNELS), fill_value=0)
              .reset_index())
    tg = tg.merge(counts, on=["game_id", "team"], how="left")
    tg[list(CHANNELS)] = tg[list(CHANNELS)].fillna(0).astype(int)
    tg["tds"] = tg[list(CHANNELS)].sum(axis=1)
    return tg


# ------------------------------------------------------------ distributions

def count_pmf(mu, r=None, max_k: int = MAX_TD, n: int | None = None) -> np.ndarray:
    """P(0..max_k) for each mean in `mu`.

      n given   binomial over n trials with p = mu / n -- LESS spread than
                Poisson (variance = mu * (1 - mu/n));
      r given   negative binomial with size r -- MORE spread than Poisson;
      neither   Poisson.

    WHY BINOMIAL IS HERE. Layer 1 found team touchdown counts UNDERdispersed:
    actual variance about 0.76 of the mean in every quintile, where Poisson
    says 1.0 and a negative binomial can only say more. That is what a count
    built from ~11 drives, each of which can end in at most one touchdown,
    looks like -- a binomial -- and n is the effective number of trials.

    Built by recurrence rather than lgamma, so no scipy; the last column
    absorbs any tail so every row sums to 1."""
    mu = np.atleast_1d(np.asarray(mu, dtype=float))
    out = np.zeros((len(mu), max_k + 1))
    if n is not None:
        p = np.clip(mu / n, 1e-9, 1 - 1e-9)
        out[:, 0] = (1 - p) ** n
        for k in range(max_k):
            out[:, k + 1] = out[:, k] * max(n - k, 0) / (k + 1) * p / (1 - p)
    elif r is None:
        out[:, 0] = np.exp(-mu)
        for k in range(max_k):
            out[:, k + 1] = out[:, k] * mu / (k + 1)
    else:
        p = r / (r + mu)
        out[:, 0] = p ** r
        for k in range(max_k):
            out[:, k + 1] = out[:, k] * (k + r) / (k + 1) * (1 - p)
    out[:, -1] += np.clip(1.0 - out.sum(axis=1), 0.0, None)
    return out


def crps_count(pmf: np.ndarray, y) -> np.ndarray:
    """CRPS of a discrete distribution on 0..K: the sum over k of
    (F(k) - 1{y <= k})^2. Lower is better; it rewards putting probability
    near what happened, not just getting the mean right."""
    y = np.asarray(y, dtype=int)
    F = np.cumsum(pmf, axis=1)
    k = np.arange(pmf.shape[1])
    step = (k[None, :] >= y[:, None]).astype(float)
    return ((F - step) ** 2).sum(axis=1)


def log_score(pmf: np.ndarray, y) -> np.ndarray:
    """-log P(what happened). Lower is better."""
    y = np.clip(np.asarray(y, dtype=int), 0, pmf.shape[1] - 1)
    return -np.log(np.maximum(pmf[np.arange(len(y)), y], 1e-12))


def fit_dispersion(mu, y, grid=None) -> float | None:
    """The negative-binomial size r that best explains `y` given `mu`, by
    maximum likelihood over a grid. Returns None when Poisson fits at least as
    well -- i.e. when the data are NOT overdispersed, which is a finding, not
    a failure. The framework asserts overdispersion; this is where it is
    checked."""
    grid = np.geomspace(0.5, 500, 80) if grid is None else grid
    y = np.asarray(y, dtype=int)
    best_r, best_ll = None, log_score(count_pmf(mu), y).sum() * -1
    for r in grid:
        ll = -log_score(count_pmf(mu, r), y).sum()
        if ll > best_ll:
            best_r, best_ll = float(r), ll
    return best_r


def fit_trials(mu, y, grid=range(6, 61)) -> int | None:
    """The binomial trial count n that best explains `y` given `mu`, or None
    when Poisson (n -> infinity) fits at least as well. The counterpart of
    fit_dispersion for data with LESS spread than Poisson."""
    y = np.asarray(y, dtype=int)
    mu = np.asarray(mu, dtype=float)
    best_n, best_ll = None, -log_score(count_pmf(mu), y).sum()
    for n in grid:
        if n <= mu.max():
            continue
        ll = -log_score(count_pmf(mu, n=n), y).sum()
        if ll > best_ll:
            best_n, best_ll = int(n), ll
    return best_n


# ------------------------------------------------------------------- ratios

def ratios(history: pd.DataFrame, k_points: float | None) -> tuple[pd.Series, float]:
    """Touchdowns per point for each team, shrunk toward the league.

    ratio = (team TDs + k * league ratio) / (team points + k)

    k is a pseudo-count in POINTS: k = 300 means the league prior counts as
    much as about 13 average games. k=None returns the league ratio for every
    team -- the current engine's behaviour, and the baseline to beat.
    The denominator is points SCORED, not implied: the ratio measures how a
    team converts points into touchdowns (red-zone efficiency, fourth-down
    aggression, kicker reliance), not whether it beat its market total.
    """
    league = history["tds"].sum() / history["points"].sum()
    if k_points is None:
        return pd.Series(dtype=float), float(league)
    by = history.groupby("team")[["tds", "points"]].sum()
    return (by["tds"] + k_points * league) / (by["points"] + k_points), float(league)


def team_mean(implied, ratio, ref_implied: float, gamma: float = 0.0):
    """Expected touchdowns: implied points x TDs-per-point, with an optional
    elasticity. gamma = 0 is linear. gamma > 0 lets a high-total team convert
    a larger SHARE of its points into touchdowns -- tested because layer 1's
    linear model ran 12% low in the top quintile of implied totals. Scaled
    around the historical mean implied total so gamma bends the curve without
    moving its level."""
    implied = np.asarray(implied, dtype=float)
    return implied * np.asarray(ratio, dtype=float) * (implied / ref_implied) ** gamma


def channel_shares(history: pd.DataFrame, alpha: float | None) -> tuple[pd.DataFrame, pd.Series]:
    """Each team's channel mix, shrunk toward the league mix by a pseudo-count
    of `alpha` touchdowns. alpha=None returns the league mix for everyone."""
    league = history[list(CHANNELS)].sum()
    league = league / league.sum()
    if alpha is None:
        return pd.DataFrame(columns=list(CHANNELS)), league
    by = history.groupby("team")[list(CHANNELS)].sum()
    n = by.sum(axis=1)
    shares = (by + alpha * league) .div(n + alpha, axis=0)
    return shares, league
