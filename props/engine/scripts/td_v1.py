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
  channel mix  the team's, except the QB-rush weight: the starting
               quarterback's own QB-rush touchdowns over his teams' offensive
               touchdowns in his starts (3 seasons), shrunk by 40 team TDs
  P(score)     1 - sum_k P(N = k) (1 - q)^k, q = the player's per-TD share

Tuned on 2022-23, scored on 2024-25 and AS-IS on 2016-17 and 2018-19
(reports/td_v1.md, td_v1_1_tuning.md, td_v1_2016_17.md, td_v1_2018_19.md).
End to end vs the anytime_td_v0 structure, log loss -0.0043 (-0.0065,
-0.0022) on 2024-25; mean predicted scoring rate 0.145 vs actual 0.148, where
v0 gives 0.135. It is still PROTOTYPE: none of this is tested against posted
sportsbook lines, so it prices no fair odds.

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
    "cap": 0.99,                      # total share per channel; 0.99-0.999 tested, 0.99 best on tune
    "qb_beta": 40.0,                  # starter QB-rush rate shrunk by 40 team TDs (tuned 2022-23); None = team mix
    "qb_window": 3,                   # seasons of the starter's career the rate looks back over
    "qb_share": 0.92,                 # the starter share WITHIN qb_rush (tuned 2022-23); None = from history
    "top_pass": None,                 # factor on the top-q player's passing-channel shares; None = off
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


def context(hist: pd.DataFrame, alpha: float = V1["mix_alpha"],
            qb_hist: pd.DataFrame | None = None) -> dict:
    """What layer 1 and the channel mix need from the team-game history
    (prior season plus the current season's earlier weeks), and -- when
    `qb_hist` is given -- each quarterback's QB-rush record as a starter
    (qb_history)."""
    mix_team, mix_league = T.channel_shares(hist, alpha)
    off = mix_league[list(T.OFFENSIVE)]
    qb = None
    if qb_hist is not None and len(qb_hist):
        qb = qb_hist.groupby("player_id")[["qb_rush_tds", "off_tds"]].sum()
    return {"mix_team": mix_team, "mix_league": mix_league,
            "ratio_off": float(hist["off_tds"].sum() / hist["points"].sum()),
            "ref": float(hist["implied"].mean()),
            "qb": qb, "qb_league": float(off["qb_rush"] / off.sum())}


# ------------------------------------------------------------ the starter's QB-rush rate
#
# Within qb_rush only quarterback carries count, so a starter's share of that
# channel is near 1 whoever he is. What decides his price is how often the
# TEAM's touchdowns are QB rushes -- and a team mix learned from last season
# describes last season's quarterback: Miami after a pocket passer gave Malik
# Willis a qb_rush weight of 0.063. Keyed to the starter instead: his QB-rush
# touchdowns over his teams' offensive touchdowns in the games he started, over
# the last `qb_window` seasons, shrunk toward the league fraction by `qb_beta`
# team touchdowns.

def qb_starts(pbp: pd.DataFrame, qb_ids: set[str]) -> pd.DataFrame:
    """One row per team-game: the starting quarterback (most dropbacks plus
    carries), his QB-rush touchdowns, and the team's offensive touchdowns."""
    reg = pbp[pbp["season_type"] == "REG"]
    cols = ["game_id", "season", "week", "posteam"]
    drop = reg.loc[(reg["play_type"] == "pass") & reg["passer_player_id"].notna(),
                   cols + ["passer_player_id"]].rename(columns={"passer_player_id": "player_id"})
    run = reg.loc[(reg["play_type"] == "run") & reg["rusher_player_id"].isin(qb_ids),
                  cols + ["rusher_player_id"]].rename(columns={"rusher_player_id": "player_id"})
    plays = pd.concat([drop, run], ignore_index=True)
    plays["team"] = T._norm_team(plays["posteam"])
    n = plays.groupby(["season", "week", "game_id", "team", "player_id"]).size().rename("plays").reset_index()
    st = (n.sort_values(["plays", "player_id"], ascending=[False, True])
          .drop_duplicates(["game_id", "team"]).drop(columns="plays"))
    ev = T.classify_tds(pbp, qb_ids)
    ev = ev[ev["channel"].isin(T.OFFENSIVE)]
    off = ev.assign(team=T._norm_team(ev["team"])).groupby(["game_id", "team"]).size().rename("off_tds")
    sc = A.scorers(pbp, qb_ids)
    qr = (sc[sc["channel"] == "qb_rush"].groupby(["game_id", "team", "player_id"])["tds"].sum()
          .rename("qb_rush_tds"))
    st = (st.merge(off, on=["game_id", "team"], how="left")
          .merge(qr, on=["game_id", "team", "player_id"], how="left"))
    st[["off_tds", "qb_rush_tds"]] = st[["off_tds", "qb_rush_tds"]].fillna(0).astype(int)
    return st.sort_values(["season", "week", "game_id", "team"]).reset_index(drop=True)


def qb_history(starts: pd.DataFrame, season: int, week: int, window: int = V1["qb_window"]) -> pd.DataFrame:
    """Starts strictly before (season, week), within `window` prior seasons."""
    s = starts
    return s[(s["season"] >= season - window)
             & ((s["season"] < season) | ((s["season"] == season) & (s["week"] < week)))]


def starter(actives_team: pd.DataFrame) -> str | None:
    """The active quarterback highest on the pre-game depth chart."""
    qb = actives_team[actives_team["pos"] == "QB"]
    if qb.empty:
        return None
    slot = qb["slot"].astype(str)
    rank = slot.where(slot.str.fullmatch(r"QB\d"), "QB9")
    return str(qb.assign(_r=rank.to_numpy()).sort_values(["_r", "player_id"])["player_id"].iloc[0])


def game_mix(ctx: dict, team: str, qb: str | None = None, beta=V1["qb_beta"]) -> pd.Series:
    """The team's offensive channel mix, normalised to 1. With `beta` set and a
    starter named, the qb_rush weight is the starter's shrunk rate and the
    other channels keep their team proportions in what remains."""
    mix = ctx["mix_team"].loc[team] if team in ctx["mix_team"].index else ctx["mix_league"]
    off = mix[list(T.OFFENSIVE)]
    off = off / off.sum()
    if beta is None or qb is None:
        return off
    h = ctx.get("qb")
    tds, n = ((float(h.loc[qb, "qb_rush_tds"]), float(h.loc[qb, "off_tds"]))
              if h is not None and qb in h.index else (0.0, 0.0))
    r = (tds + beta * ctx["qb_league"]) / (n + beta)
    rest = off.drop("qb_rush")
    out = rest / rest.sum() * (1.0 - r)
    out["qb_rush"] = r
    return out[list(T.OFFENSIVE)]


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


def game_shares(shares: pd.DataFrame, team: str, ids: list[str], pos: dict,
                mode=V1["mode"], cap=V1["cap"], qb: str | None = None,
                qb_share=V1["qb_share"]) -> pd.DataFrame:
    """Channel shares of each active player on `team`, after reallocation.

    THE STARTER'S QB-RUSH SHARE. From history it runs 0.70 against 0.88 of
    his team's QB carries in reality: shares come from games-played
    denominators, so a backup who played only while the starter was out
    carries a starter-sized share and the cap squeezes both. Depth charts do
    not mark those games (a fill-in starter is often still listed QB2), so a
    role filter cannot find them. With `qb_share` set, the named starter's
    share within qb_rush is that value and the other players' qb_rush shares
    are scaled down, if needed, to fit under the cap."""
    m = A.reallocate(A.candidates(shares, team, T.OFFENSIVE), set(ids), pos, T.OFFENSIVE,
                     mode, cap).reindex(ids).fillna(0)
    if qb_share is not None and qb is not None and qb in m.index:
        rest = m.index != qb
        tot = float(m.loc[rest, "qb_rush"].sum())
        room = max(cap - qb_share, 0.0)
        if tot > room:
            m.loc[rest, "qb_rush"] *= room / tot
        m.loc[qb, "qb_rush"] = qb_share
    return m


PASS_CHANNELS = [c for c in T.OFFENSIVE if c.startswith("pass_")]


def apply_top_pass(m: pd.DataFrame, mix: pd.Series, factor=V1["top_pass"]) -> pd.DataFrame:
    """The team's top per-TD-share player (usually the lead back) scores
    below his passing-channel shares: 0.81-0.86 of expected even after the
    end-zone split, while his rushing channels sit at ~1 (reports/
    td_diagnostics.md). With `factor` set, his pass-channel shares are
    multiplied by it and the removed share goes to his teammates in the same
    channel, pro rata -- so each channel's total is unchanged."""
    if factor is None or len(m) < 2:
        return m
    top = per_td(m, mix).idxmax()
    m = m.copy()
    for ch in PASS_CHANNELS:
        cut = float(m.loc[top, ch]) * (1.0 - factor)
        rest = m.index != top
        tot = float(m.loc[rest, ch].sum())
        if cut <= 0 or tot <= 0:
            continue
        m.loc[top, ch] -= cut
        m.loc[rest, ch] += cut * m.loc[rest, ch] / tot
    return m


def game_q(shares: pd.DataFrame, team: str, ids: list[str], pos: dict, ctx: dict,
           mode=V1["mode"], cap=V1["cap"], qb: str | None = None, beta=V1["qb_beta"],
           top_pass=V1["top_pass"]) -> pd.Series:
    """Per-touchdown share of each active player on `team`; `qb` is the
    starting quarterback (starter())."""
    m = game_shares(shares, team, ids, pos, mode, cap, qb=qb)
    mix = game_mix(ctx, team, qb, beta)
    return per_td(apply_top_pass(m, mix, top_pass), mix).clip(upper=0.999)


def team_pmf(implied: float, ctx: dict, trials=V1["trials"], gamma=V1["gamma"]) -> np.ndarray:
    mu = float(T.team_mean(implied, ctx["ratio_off"], ctx["ref"], gamma))
    return T.count_pmf([mu], n=trials)[0]


def game_detail(shares, team, ids, pos, ctx, implied, c=V1["c"], qb=None) -> pd.DataFrame:
    """For each active player on `team`: P(at least one touchdown), his
    per-touchdown share q, and the team's expected offensive touchdowns mu --
    the three numbers the report needs to explain the price."""
    mix = game_mix(ctx, team, qb)
    m = apply_top_pass(game_shares(shares, team, ids, pos, qb=qb), mix, V1["top_pass"])
    q = per_td(m, mix).clip(upper=0.999)                  # = game_q, spelled out to keep m and mix
    pmf = team_pmf(implied, ctx)
    mu = float((pmf * np.arange(len(pmf))).sum())
    out = pd.DataFrame({"p": A.p_score_dist(q.to_numpy(), pmf, c), "q": q.to_numpy(),
                        "mu": mu, "team": team}, index=ids)
    # channel shares and the team mix, for layer 3 (joint prices in shadow)
    for ch in T.OFFENSIVE:
        out[f"s_{ch}"] = m[ch].to_numpy()
        out[f"w_{ch}"] = float(mix[ch])
    return out


def game_probabilities(shares, team, ids, pos, ctx, implied, c=V1["c"], qb=None) -> pd.Series:
    """P(at least one touchdown) for each active player on `team`."""
    return game_detail(shares, team, ids, pos, ctx, implied, c, qb)["p"]


# ------------------------------------------------------------ live inputs

def load_bundled(res: Path, season: int) -> dict:
    """The prior season's raw inputs, bundled by build_td_priors.py. Raw, not
    derived, so the live path runs the same functions the backtest does."""
    r = lambda n: pd.read_csv(res / f"priors_{season}_td_{n}.csv", low_memory=False)  # noqa: E731
    out = {"cnt": r("counts"), "played": r("played"), "slots": r("slots"), "tg": r("teamgames")}
    qs = res / f"priors_{season}_td_qbstarts.csv"
    out["qbstarts"] = pd.read_csv(qs) if qs.exists() else None
    return out


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
    starts = qb_starts(before, qb_ids) if len(before) else None
    return {"cnt": cnt, "played": played, "tg": tg, "actives": act.drop_duplicates("player_id"),
            "qbstarts": starts, "season": season, "week": week}


def anytime_probabilities(bundled: dict, cur: dict, implied_by_team: dict[str, float]) -> pd.DataFrame:
    """Indexed by gsis_id: p (P(at least one touchdown)), q, mu, team -- for
    every active player on the teams in `implied_by_team`. The live entry point."""
    hist = bundled["tg"] if cur["tg"] is None else pd.concat([bundled["tg"], cur["tg"]], ignore_index=True)
    qh = None
    if V1["qb_beta"] is not None:
        parts = [x for x in (bundled.get("qbstarts"), cur.get("qbstarts")) if x is not None]
        if not parts:
            raise ValueError("qb_beta is set but no quarterback starts are bundled")
        qh = qb_history(pd.concat(parts, ignore_index=True), cur["season"], cur["week"])
    ctx = context(hist, qb_hist=qh)
    act = cur["actives"]
    shares, _ = week_shares(cur["cnt"], bundled["cnt"], cur["played"], bundled["played"],
                            bundled["slots"], act)
    pos = dict(zip(pd.concat([bundled["played"], cur["played"], act])["player_id"],
                   pd.concat([bundled["played"], cur["played"], act])["pos"]))
    out = []
    for team, implied in implied_by_team.items():
        here = act[act["team"] == team]
        ids = list(here["player_id"])
        if ids and implied is not None and np.isfinite(implied):
            out.append(game_detail(shares, team, ids, pos, ctx, implied, qb=starter(here)))
    return pd.concat(out) if out else pd.DataFrame(columns=["p", "q", "mu", "team"])
