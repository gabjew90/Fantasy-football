"""Touchdown model, LAYER 2: given a team's touchdowns BY CHANNEL, who scores.

Within each channel a player's share comes from his share of that channel's
OPPORTUNITIES -- carries from the 5 in, carries from beyond it, quarterback
carries, red-zone targets, targets beyond the 20 -- blended toward his
prior-season role, with an explicit 'other' bucket. Injury reallocation
happens here: an inactive player's share has to go somewhere, and where it
goes is one of the things the layer-2 backtest measures.

Layer 2 is scored CONDITIONAL on the team's actual touchdowns by channel, so
an allocation error cannot hide behind, or be blamed on, a layer-1 miss.

Stdlib + numpy + pandas only.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from td_model import OFFENSIVE, _norm_team, classify_tds

# Layer 2 needs, beyond layer 1's columns: who was targeted, who scored, and
# which plays to drop.
PBP_COLS_L2 = ["game_id", "season", "week", "season_type", "posteam", "defteam",
               "td_team", "touchdown", "pass_touchdown", "rush_touchdown",
               "yardline_100", "rusher_player_id", "play_type",
               "receiver_player_id", "td_player_id", "qb_kneel", "two_point_attempt"]

# The engine's current split, reproduced so the baseline is scored on the
# same plays: all targets / inside-the-10 targets, all carries / inside-10.
ENGINE_CHANNELS = ("tgt_all", "tgt_i10", "car_all", "car_i10")


def scorers(pbp: pd.DataFrame, qb_ids: set[str]) -> pd.DataFrame:
    """(game_id, team, player_id, channel) -> offensive touchdowns scored.

    The scorer is `td_player_id`: the ball carrier on a rushing TD, the
    receiver on a passing TD. Offensive channels only -- a return or
    defensive score is not what an anytime prop on an offensive player is
    priced from.
    """
    ev = classify_tds(pbp, qb_ids)
    d = ev.join(pbp.loc[ev.index, ["td_player_id"]])
    d = d[d["channel"].isin(OFFENSIVE) & d["td_player_id"].notna()]
    return (d.assign(team=_norm_team(d["team"]))
            .groupby(["game_id", "team", "td_player_id", "channel"]).size()
            .rename("tds").reset_index().rename(columns={"td_player_id": "player_id"}))


def opportunities(pbp: pd.DataFrame, qb_ids: set[str]) -> pd.DataFrame:
    """One row per opportunity, tagged with the SAME channels a touchdown is.

    A quarterback's carry is a qb_rush opportunity from anywhere; anyone
    else's is rush_in5 from the 5 or closer, rush_far beyond it. A target is
    pass_rz from the 20 or closer, pass_far beyond. Kneels and two-point
    tries are dropped. Each row also carries the engine's own split, so the
    baseline is scored on identical plays.
    """
    base = pbp[(pbp["season_type"] == "REG") & (pbp["two_point_attempt"].fillna(0) != 1)]
    car = base[(base["play_type"] == "run") & base["rusher_player_id"].notna()
               & (base["qb_kneel"].fillna(0) != 1)]
    tgt = base[(base["play_type"] == "pass") & base["receiver_player_id"].notna()]
    c = pd.DataFrame({"game_id": car["game_id"], "season": car["season"], "week": car["week"],
                      "team": _norm_team(car["posteam"]), "player_id": car["rusher_player_id"],
                      "channel": np.where(car["rusher_player_id"].isin(qb_ids), "qb_rush",
                                          np.where(car["yardline_100"] <= 5, "rush_in5", "rush_far")),
                      "engine": np.where(car["yardline_100"] <= 10, "car_i10", "car_all")})
    t = pd.DataFrame({"game_id": tgt["game_id"], "season": tgt["season"], "week": tgt["week"],
                      "team": _norm_team(tgt["posteam"]), "player_id": tgt["receiver_player_id"],
                      "channel": np.where(tgt["yardline_100"] <= 20, "pass_rz", "pass_far"),
                      "engine": np.where(tgt["yardline_100"] <= 10, "tgt_i10", "tgt_all")})
    return pd.concat([c, t], ignore_index=True)


def counts(opps: pd.DataFrame, key: str) -> pd.DataFrame:
    """(season, week, game_id, team, player_id) x channel -> count.

    For the engine key an inside-10 play ALSO counts in the `_all` column,
    because the engine's overall share is over every target or carry."""
    g = (opps.groupby(["season", "week", "game_id", "team", "player_id", key]).size()
         .unstack(key, fill_value=0).reset_index())
    g.columns.name = None
    if key == "engine":
        for a in ("tgt", "car"):
            g[f"{a}_all"] = g.get(f"{a}_all", 0) + g.get(f"{a}_i10", 0)
    return g


def _aggregate(opps: pd.DataFrame, played: pd.DataFrame, chans: list[str]) -> pd.DataFrame:
    """Per player over the given games: his opportunities, and his TEAM'S
    opportunities in the games HE played -- so a week injured does not
    dilute his share."""
    team = opps.groupby(["game_id", "team"])[chans].sum().add_prefix("T_").reset_index()
    d = (played.merge(team, on=["game_id", "team"], how="inner")
         .merge(opps[["game_id", "team", "player_id", *chans]],
                on=["game_id", "team", "player_id"], how="left"))
    d[chans] = d[chans].fillna(0)
    last = d.sort_values(["season", "week"]).groupby("player_id")["team"].last()
    s = d.groupby("player_id")[chans + [f"T_{c}" for c in chans]].sum()
    s["team"] = last
    return s


def blended_shares(cur: pd.DataFrame, pri: pd.DataFrame, played_cur: pd.DataFrame,
                   played_pri: pd.DataFrame, chans, kappa_games: float,
                   per_game: dict[str, float],
                   current_team: dict[str, str] | None = None) -> pd.DataFrame:
    """Each player's share of each channel's opportunities, blended toward his
    prior-season role:

      share = (his opps + k * prior share) / (team opps in his games + k)

    k is kappa_games x the league's opportunities per team-game in that
    channel, so the prior means the same thing in a channel with 1.5 chances
    a game (rush_in5) as in one with 27 (pass_far). A prior from another team
    counts half. A player with no history at all gets no share, and so falls
    to 'other' until he builds one.

    `current_team` is who he plays for THIS week, from the game-day active
    list -- known before kickoff. Without it the team had to be inferred
    from his past games, which in week 1 (and in the first game after a
    trade) is his OLD team: an offseason mover's old role then entered his
    new team at full weight, not half, and he also stayed a candidate for the
    team he had left. The output also carries his prior team and prior
    shares, so the team he left can treat that share as vacated.
    """
    chans = list(chans)
    c = _aggregate(cur, played_cur, chans) if len(played_cur) else None
    p = _aggregate(pri, played_pri, chans)
    ids = p.index.union(c.index) if c is not None else p.index
    out = pd.DataFrame(index=ids)
    team_now = c["team"].reindex(ids) if c is not None else pd.Series(index=ids, dtype=object)
    team_now = team_now.fillna(p["team"].reindex(ids))
    if current_team:
        team_now = pd.Series(ids.map(lambda i: current_team.get(i)), index=ids).fillna(team_now)
    out["team"] = team_now
    out["pri_team"] = p["team"].reindex(ids)
    moved = (out["pri_team"].notna() & (out["pri_team"] != out["team"])).to_numpy()
    for ch in chans:
        k = kappa_games * per_game[ch] * np.where(moved, 0.5, 1.0)
        pri_s = (p[ch] / p[f"T_{ch}"]).reindex(ids).to_numpy()
        n_c = (c[ch].reindex(ids).fillna(0) if c is not None else pd.Series(0.0, index=ids)).to_numpy()
        N_c = (c[f"T_{ch}"].reindex(ids).fillna(0) if c is not None else pd.Series(0.0, index=ids)).to_numpy()
        with np.errstate(invalid="ignore", divide="ignore"):
            cur_s = np.where(N_c > 0, n_c / N_c, np.nan)
            blended = (n_c + k * np.nan_to_num(pri_s)) / (N_c + k)
        out[ch] = np.where(np.isnan(pri_s), cur_s, np.where(N_c > 0, blended, pri_s))
        out[f"pri_{ch}"] = pri_s
    out[chans] = out[chans].fillna(0.0).clip(0, 1)
    out[[f"pri_{ch}" for ch in chans]] = out[[f"pri_{ch}" for ch in chans]].fillna(0.0)
    return out


def candidates(shares: pd.DataFrame, team: str, chans) -> pd.DataFrame:
    """Everyone whose share belongs to `team` this week.

    Players on the team now (active or not), plus players who were on it last
    season and have LEFT -- carried at their prior-season share, because that
    is the share their departure vacated. They are never active for this team,
    so reallocation decides where it goes; with no reallocation it goes to
    'other'. The same departed player is priced for his new team from his
    blended share, so his mass is never counted twice.
    """
    chans = list(chans)
    here = shares[shares["team"] == team]
    left = shares[(shares["pri_team"] == team) & (shares["team"] != team)].copy()
    for ch in chans:
        left[ch] = left[f"pri_{ch}"]
    return pd.concat([here, left])


def reallocate(shares: pd.DataFrame, active: set[str], pos: dict[str, str], chans,
               mode: str) -> pd.DataFrame:
    """Keep only the active players, and decide where an inactive player's
    share goes.

      none      to 'other': the model forgets he existed;
      all       spread over every active teammate, pro rata;
      position  to active teammates at HIS position, pro rata: the RB1 is
                out, so the RB2 inherits the goal-line work.

    Total share per channel is capped at 0.99 -- there is always an 'other'.
    """
    chans = list(chans)
    s = shares.copy()
    s["pos"] = s.index.map(pos).fillna("OTHER")
    act = s[s.index.isin(active)].copy()
    gone_rows = s[~s.index.isin(active)]
    if mode != "none" and len(act):
        for ch in chans:
            if mode == "all":
                gone, have = gone_rows[ch].sum(), act[ch].sum()
                if have > 0:
                    act[ch] *= (have + gone) / have
            else:
                for p, grp in gone_rows.groupby("pos"):
                    gone = grp[ch].sum()
                    m = act["pos"] == p
                    have = act.loc[m, ch].sum()
                    if gone > 0 and have > 0:
                        act.loc[m, ch] *= (have + gone) / have
    for ch in chans:
        tot = act[ch].sum()
        if tot > 0.99:
            act[ch] *= 0.99 / tot
    return act[chans]


def p_score(shares: pd.DataFrame, n_by_channel: dict[str, float]) -> pd.Series:
    """P(at least one touchdown) given the team's touchdowns by channel. Each
    touchdown in a channel independently goes to the player with probability
    equal to his share, so P(none) = product over channels of (1 - share)^n."""
    log_none = pd.Series(0.0, index=shares.index)
    for ch, n in n_by_channel.items():
        if n and ch in shares.columns:
            log_none = log_none + n * np.log1p(-shares[ch].clip(upper=0.999))
    return 1.0 - np.exp(log_none)
