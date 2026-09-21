"""anytime_td_v1: the ONE implementation of the anytime-touchdown model.

The backtest (td_alloc_backtest.py) and the live scorer (score_game.py) both
call these functions, so the number validated is the number shipped -- the
same rule the yardage model follows since the pipelines were unified.

  team count   offensive touchdowns ~ Binomial(10), mean = implied points x
               league offensive TDs per point x (implied / mean implied)^0.25
  who scores   each active player's share of five opportunity channels
               (QB rush, rush from the 5 in, rush beyond, red-zone targets,
               targets beyond the 20), blended toward last season's role; a
               role from another team counts 0.25; a player with no history
               gets 0.4 x his depth-chart slot's league share; an absent
               player's share is reallocated across the active roster
  P(score)     1 - sum_k P(N = k) (1 - q)^k, q = the player's per-TD share

Validated on 2024-25, tuned on 2022-23 (reports/td_layer1_frozen.md,
reports/td_layer2.md). End to end vs the anytime_td_v0 structure, log loss
-0.0032 (-0.0055, -0.0011); mean predicted scoring rate 0.142 vs actual
0.148, where v0 gives 0.135. It is still PROTOTYPE: none of this is tested
against posted sportsbook lines, so it prices no fair odds.

Stdlib + numpy + pandas only.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

import model as M
import td_alloc as A
import td_model as T

V1 = {
    "trials": T.LAYER1["trials"],     # 10
    "gamma": T.LAYER1["gamma"],       # 0.25
    "kappa": 5.0,                     # prior weight, in games of team opportunities
    "moved": 0.25,                    # weight of a role from another team (0.25-1.0 within 0.001)
    "slot_scale": 0.4,                # the full slot share ran 2.5x high on no-history players
    "mode": "all",                    # reallocation of an absent player's share
    "mix_alpha": 100.0,               # channel-mix pseudo-count, touchdowns
    "c": None,                        # Beta share concentration: tested, no effect, not used
}
SKILL = {"QB": "QB", "RB": "RB", "FB": "RB", "WR": "WR", "TE": "TE"}
LABEL = "anytime_td_v1"


# ------------------------------------------------------------ shared core

def per_game(cnt: pd.DataFrame, chans=T.OFFENSIVE) -> dict[str, float]:
    t = cnt.groupby(["game_id", "team"])[list(chans)].sum()
    return {c: max(float(t[c].mean()), 1e-6) for c in chans}


def per_td(shares: pd.DataFrame, mix: pd.Series, chans=T.OFFENSIVE) -> pd.Series:
    """A player's probability of scoring any one team touchdown: his share in
    each channel, weighted by how often the team's touchdowns come from it."""
    w = mix[list(chans)]
    w = w / w.sum() if w.sum() > 0 else w
    return sum(w[c] * shares[c] for c in chans)


def context(hist: pd.DataFrame, alpha: float = V1["mix_alpha"]) -> dict:
    """What layer 1 and the channel mix need from the team-game history
    (prior season plus the current season's earlier weeks)."""
    mix_team, mix_league = T.channel_shares(hist, alpha)
    return {"mix_team": mix_team, "mix_league": mix_league,
            "ratio_off": float(hist["off_tds"].sum() / hist["points"].sum()),
            "ref": float(hist["implied"].mean())}


def week_shares(cnt_cur, cnt_pri, played_cur, played_pri, slots_pri, actives: pd.DataFrame,
                kappa=V1["kappa"], moved=V1["moved"], slot_scale=V1["slot_scale"],
                prior=True) -> tuple[pd.DataFrame, pd.DataFrame]:
    """(filled shares, raw shares) for every player, for one week.
    `actives` has player_id, team, slot for the week being priced."""
    raw = A.blended_shares(cnt_cur, cnt_pri, played_cur, played_pri, T.OFFENSIVE, kappa,
                           per_game(cnt_pri), current_team=dict(zip(actives["player_id"], actives["team"])),
                           moved_weight=moved)
    if not prior:
        return raw, raw
    sp = A.slot_prior(cnt_pri, played_pri, slots_pri, T.OFFENSIVE)
    return A.fill_no_history(raw, actives, sp, T.OFFENSIVE, scale=slot_scale), raw


def game_q(shares: pd.DataFrame, team: str, ids: list[str], pos: dict, ctx: dict,
           mode=V1["mode"]) -> pd.Series:
    """Per-touchdown share of each active player on `team`."""
    m = A.reallocate(A.candidates(shares, team, T.OFFENSIVE), set(ids), pos, T.OFFENSIVE,
                     mode).reindex(ids).fillna(0)
    mix = ctx["mix_team"].loc[team] if team in ctx["mix_team"].index else ctx["mix_league"]
    return per_td(m, mix).clip(upper=0.999)


def team_pmf(implied: float, ctx: dict, trials=V1["trials"], gamma=V1["gamma"]) -> np.ndarray:
    mu = float(T.team_mean(implied, ctx["ratio_off"], ctx["ref"], gamma))
    return T.count_pmf([mu], n=trials)[0]


def game_detail(shares, team, ids, pos, ctx, implied, c=V1["c"]) -> pd.DataFrame:
    """For each active player on `team`: P(at least one touchdown), his
    per-touchdown share q, and the team's expected offensive touchdowns mu --
    the three numbers the report needs to explain the price."""
    q = game_q(shares, team, ids, pos, ctx)
    pmf = team_pmf(implied, ctx)
    mu = float((pmf * np.arange(len(pmf))).sum())
    return pd.DataFrame({"p": A.p_score_dist(q.to_numpy(), pmf, c), "q": q.to_numpy(),
                         "mu": mu, "team": team}, index=ids)


def game_probabilities(shares, team, ids, pos, ctx, implied, c=V1["c"]) -> pd.Series:
    """P(at least one touchdown) for each active player on `team`."""
    return game_detail(shares, team, ids, pos, ctx, implied, c)["p"]


# ------------------------------------------------------------ live inputs

def load_bundled(res: Path, season: int) -> dict:
    """The prior season's raw inputs, bundled by build_td_priors.py. Raw, not
    derived, so the live path runs the same functions the backtest does."""
    r = lambda n: pd.read_csv(res / f"priors_{season}_td_{n}.csv", low_memory=False)  # noqa: E731
    return {"cnt": r("counts"), "played": r("played"), "slots": r("slots"), "tg": r("teamgames")}


def _kick_lookup(games: pd.DataFrame) -> dict:
    out = {}
    for _, g in games.dropna(subset=["gametime"]).iterrows():
        naive = pd.Timestamp(f"{g['gameday']} {g['gametime']}")
        off = 4 if pd.Timestamp(f"{naive.year}-03-15") <= naive < pd.Timestamp(f"{naive.year}-11-01") else 5
        kt = (naive + pd.Timedelta(hours=off)).tz_localize("UTC")
        out[(g["home_team"], g["week"])] = kt
        out[(g["away_team"], g["week"])] = kt
    return out


def current_inputs(pbp: pd.DataFrame, ros: pd.DataFrame, snaps: pd.DataFrame, dc: pd.DataFrame,
                   games: pd.DataFrame, inj: pd.DataFrame | None, season: int, week: int) -> dict:
    """This season's inputs for pricing week `week`, from the files the live
    scorer already loads. History strictly before `week`; the active list and
    depth chart for `week` itself.

    ACTIVE, live: the weekly roster's ACT players at skill positions, minus
    anyone the injury report lists Out or Doubtful. The backtest used the
    game-day ACT list; before kickoff the injury report is the part of that
    information that exists.
    """
    ros = ros[ros["season"] == season]
    qb_ids = set(ros.loc[ros["position"] == "QB", "gsis_id"].dropna())
    pfr = ros.dropna(subset=["pfr_id", "gsis_id"]).drop_duplicates("pfr_id").set_index("pfr_id")["gsis_id"]
    before = pbp[(pbp["season"] == season) & (pbp["week"] < week)]
    cnt = A.counts(A.opportunities(before, qb_ids), "channel") if len(before) else pd.DataFrame(
        columns=["season", "week", "game_id", "team", "player_id", *T.OFFENSIVE])
    sn = snaps[(snaps["season"] == season) & (snaps["week"] < week) & (snaps["game_type"] == "REG")
               & (snaps["offense_snaps"] > 0) & snaps["position"].isin(SKILL)]
    played = pd.DataFrame({"season": sn["season"], "week": sn["week"], "game_id": sn["game_id"],
                           "team": T._norm_team(sn["team"]), "player_id": sn["pfr_player_id"].map(pfr),
                           "pos": sn["position"].map(SKILL)}).dropna(subset=["player_id"])
    g = games[(games["season"] == season) & (games["game_type"] == "REG")]
    tg = T.team_games(g[g["week"] < week], T.classify_tds(before, qb_ids)) if len(before) else None

    wk = ros[(ros["week"] == week) & (ros["status"] == "ACT") & ros["position"].isin(SKILL)
             & ros["gsis_id"].notna()]
    act = pd.DataFrame({"player_id": wk["gsis_id"], "team": T._norm_team(wk["team"]),
                        "pos": wk["position"].map(SKILL)})
    if inj is not None and len(inj):
        out = inj[(inj["season"] == season) & (inj["week"] == week)
                  & inj["report_status"].isin(["Out", "Doubtful"])]["gsis_id"]
        act = act[~act["player_id"].isin(set(out))]
    roles = M.normalize_depth_charts(dc, _kick_lookup(g))
    sl = pd.DataFrame({"team": T._norm_team(roles["team"]), "week": roles["week"],
                       "player_id": roles["gsis_id"], "slot": roles["slot"]})
    sl = sl[sl["week"] == week].drop_duplicates(["team", "player_id"])
    act = act.merge(sl[["team", "player_id", "slot"]], on=["team", "player_id"], how="left")
    return {"cnt": cnt, "played": played, "tg": tg, "actives": act.drop_duplicates("player_id")}


def anytime_probabilities(bundled: dict, cur: dict, implied_by_team: dict[str, float]) -> pd.DataFrame:
    """Indexed by gsis_id: p (P(at least one touchdown)), q, mu, team -- for
    every active player on the teams in `implied_by_team`. The live entry point."""
    hist = bundled["tg"] if cur["tg"] is None else pd.concat([bundled["tg"], cur["tg"]], ignore_index=True)
    ctx = context(hist)
    act = cur["actives"]
    shares, _ = week_shares(cur["cnt"], bundled["cnt"], cur["played"], bundled["played"],
                            bundled["slots"], act)
    pos = dict(zip(pd.concat([bundled["played"], cur["played"], act])["player_id"],
                   pd.concat([bundled["played"], cur["played"], act])["pos"]))
    out = []
    for team, implied in implied_by_team.items():
        ids = list(act.loc[act["team"] == team, "player_id"])
        if ids and implied is not None and np.isfinite(implied):
            out.append(game_detail(shares, team, ids, pos, ctx, implied))
    return pd.concat(out) if out else pd.DataFrame(columns=["p", "q", "mu", "team"])
