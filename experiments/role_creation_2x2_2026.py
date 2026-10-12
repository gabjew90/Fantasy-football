# expires: 2026-11-11
"""Running backs on role vs creation, with the blocking as colour (the user's framework, 2026-10-12). A study,
not a model: it changes nothing in the calculator (frozen to 2026-11-02, DECISIONS #245). Its quadrant
actions (hold / candidate sell / candidate buy / drop) are labels to be TESTED, not findings: whether
creation predicts a later change of role is a separate backtest, not run here.

- x, role (this season, every week of play-by-play): one score from three of the back's shares of his
  team's work, in the games he played: carries 50%, carries inside the opponent's 10 25%, targets 25% (a stated choice; targets stand in
  for route participation, which no public feed carries). Inside-10 work is lumpy -- a team may have two
  such carries in a month -- so a back's inside-10 share is pulled toward his carry share by K_I10 team
  inside-10 carries: (his inside-10 carries + K_I10 x carry share) / (team's + K_I10). Team carries include
  quarterback designed runs (a goal-line quarterback takes real work from the back) and leave out scrambles
  and kneels. For a regular back (median snap share 40%+), a game in which he played under half his own
  median snap share AND then missed his team's next game or was on the next week's injury report (he left
  hurt) is left out of his role, and named; a quiet game with no injury after it is his role and stays in
  (a back whose role grew keeps his early quiet games). A game whose next week has not been played yet
  stays in. The same score for his most recent game (his last full one, if he left the latest hurt) is
  drawn as an arrow from the season average: a role changing midseason is the framework's trigger.
- y, creation (a trait, so measured over 2025 and this season together): the average of two standardised
  measures, so a back who makes yards by beating defenders and one who makes them by finding the hole both
  count: broken tackles per touch (Pro Football Reference's count on carries and catches; close to, not the
  same as, PFF's 'missed tackles forced') and Next Gen Stats rush yards over expected per tracked carry. Each
  is measured from its league line (every running back's rate) in units of its spread across the backs
  shown; 0 = league. A back NGS does not list (under its season minimum of carries) has the broken-tackle
  half only, and is flagged. Four weeks of broken tackles carry no repeatable signal (split-half r near zero at the first
  check), so a single season's rate is too noisy to act on. Stability is printed for each half and for the
  blend: 2025's first half against its second half (NGS weekly rows list a back only in 10+ carry games,
  so its halves are partial), and broken tackles 2025 against this season so far. A back with under 50 touches in 2025 (a rookie, mostly) has a
  creation number resting on this season alone; it is flagged. Yards after contact per carry is shown beside it as the secondary check.
- colour, the blocking: the team's Next Gen Stats expected yards per carry (run_game_2x2_2026.py, frozen at
  the handoff, so the back's own vision is not in it), against the league.
Weeks: creation this season uses only the weeks PFR has posted for every game in the play-by-play (PFR runs
behind it); role uses every week of play-by-play; 2025 is the whole regular season. A back is a running back by his latest weekly roster listing of each season, with
fullbacks (depth chart FB) left out; PFR and snap ids map to gsis ids through the rosters. A back whose PFR
carries in a season differ from his play-by-play carries by more than 2 (an id that does not map, a gap in
PFR) has that season left out of creation, and is named. A back needs 30+ touches this season. Quadrants
split at the median season role score of the backs shown (a stated choice: half the listed backs are 'high
role') and at a creation score of 0 (league)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from core import fetch as F  # noqa: E402
from experiments import run_game_2x2_2026 as rg  # noqa: E402
from props.calc import data  # noqa: E402

SEASON = 2026
PRIOR = 2025
WEIGHTS = {"carry_share": 0.50, "i10_share": 0.25, "target_share": 0.25}
K_I10 = 5                 # team inside-10 carries' worth of pull toward the carry share
PARTIAL_GAME = 0.5        # a game under this share of his own median snap share is not his role ...
REGULAR_BACK = 0.40       # ... for a back whose median snap share is at least this (a backup's quiet game is his role)
THIN_PRIOR = 50           # fewer 2025 touches than this: creation rests on this season alone
MIN_TOUCHES = 30
COLS = ["game_id", "season", "week", "season_type", "posteam", "yardline_100", "rush_attempt", "pass_attempt", "sack",
        "two_point_attempt", "qb_kneel", "qb_scramble", "rusher_player_id", "receiver_player_id", "complete_pass"]
ACTIONS = {(True, True): "Hold: lead role, creates", (True, False): "Candidate sell: role carrying him",
           (False, True): "Candidate buy: creates, small role", (False, False): "Drop: small role, little created"}


def flag(s: pd.Series) -> pd.Series:
    return s.fillna(0).astype(float) > 0


def full_pfr_weeks(p: pd.DataFrame, *pfr: pd.DataFrame) -> list[int]:
    """Weeks in which every PFR file given lists every team the play-by-play has."""
    need = p.groupby("week")["posteam"].apply(lambda s: set(s.dropna()))
    ok = set(need.index)
    for f in pfr:
        have = f.groupby("week")["team"].apply(set)
        ok &= {w for w in need.index if w in have.index and need[w] <= have[w]}
    return sorted(ok)


def season_inputs(season: int) -> dict:
    """Plays (carries, targets) restricted to the weeks PFR has in full, PFR files, rosters, the RB set."""
    age = {"max_age_s": F.CURRENT_SEASON_MAX_AGE_S} if season == SEASON else {}
    p = pd.read_csv(F.nflverse("pbp", season, **age), usecols=COLS, low_memory=False)
    p = p[p["season_type"] == "REG"]
    rush = pd.read_csv(F.nflverse("pfr_adv_rush", season, **age))
    rec = pd.read_csv(F.nflverse("pfr_adv_rec", season, **age))
    weeks = full_pfr_weeks(p, rush, rec)
    p_all = p
    p, rush, rec = (x[x["week"].isin(weeks)] for x in (p, rush, rec))
    ros = data.rosters(season)
    latest = ros.dropna(subset=["gsis_id"]).sort_values("week").drop_duplicates("gsis_id", keep="last")
    depth = pd.read_csv(F.nflverse("rosters_weekly", season, **age), usecols=["gsis_id", "week", "depth_chart_position"])
    depth = depth.dropna(subset=["gsis_id"]).sort_values("week").drop_duplicates("gsis_id", keep="last")
    fb = set(depth.loc[depth["depth_chart_position"] == "FB", "gsis_id"])
    rbs = set(latest.loc[latest["position"] == "RB", "gsis_id"]) - fb
    car_all = p_all[flag(p_all["rush_attempt"]) & ~flag(p_all["two_point_attempt"]) & ~flag(p_all["qb_kneel"])
                    & ~flag(p_all["qb_scramble"]) & p_all["rusher_player_id"].notna()]
    car_all = car_all.assign(i10=car_all["yardline_100"] <= 10)
    tgt_all = p_all[flag(p_all["pass_attempt"]) & ~flag(p_all["sack"]) & ~flag(p_all["two_point_attempt"])
                    & p_all["receiver_player_id"].notna()]
    car, tgt = car_all[car_all["week"].isin(weeks)], tgt_all[tgt_all["week"].isin(weeks)]
    ids = ros.dropna(subset=["pfr_id", "gsis_id"]).drop_duplicates("pfr_id")
    pfr_gsis = dict(zip(ids["pfr_id"], ids["gsis_id"]))
    rush = rush.assign(gsis_id=rush["pfr_player_id"].map(pfr_gsis))
    rec = rec.assign(gsis_id=rec["pfr_player_id"].map(pfr_gsis))
    for f, cols in ((rush, ["rushing_broken_tackles", "rushing_yards_after_contact", "carries"]), (rec, ["receiving_broken_tackles"])):
        bad = f[f["gsis_id"].isin(rbs)][cols].isna().any(axis=1)
        if bad.any():
            raise ValueError(f"{season}: {int(bad.sum())} running-back PFR rows with a blank in {cols}")
    return {"season": season, "p": p, "car": car, "tgt": tgt, "p_all": p_all, "car_all": car_all, "tgt_all": tgt_all, "rush": rush, "rec": rec, "ros": ros, "latest": latest,
            "rbs": rbs, "weeks": weeks,
            "unmapped": sorted(set(rush.loc[rush["gsis_id"].isna(), "pfr_player_name"]) | set(rec.loc[rec["gsis_id"].isna(), "pfr_player_name"]))}


def creation(s: dict) -> tuple[pd.DataFrame, list]:
    """Per running back, one season: touches, broken tackles (rush file: carries; receiving file: catches), yards after contact."""
    rb_car = s["car"][s["car"]["rusher_player_id"].isin(s["rbs"])].groupby("rusher_player_id").size()
    rb_rec = s["tgt"][s["tgt"]["receiver_player_id"].isin(s["rbs"])].groupby("receiver_player_id")["complete_pass"].apply(lambda x: int(flag(x).sum()))
    c = pd.DataFrame({"carries": rb_car, "receptions": rb_rec}).fillna(0)
    c["bt_rush"] = s["rush"].groupby("gsis_id")["rushing_broken_tackles"].sum().reindex(c.index).fillna(0)
    c["bt_rec"] = s["rec"].groupby("gsis_id")["receiving_broken_tackles"].sum().reindex(c.index).fillna(0)
    c["yac_sum"] = s["rush"].groupby("gsis_id")["rushing_yards_after_contact"].sum().reindex(c.index).fillna(0)
    c["pfr_carries"] = s["rush"].groupby("gsis_id")["carries"].sum().reindex(c.index).fillna(0)
    c["touches"] = c["carries"] + c["receptions"]
    gap = (c["pfr_carries"] - c["carries"]).abs() > 2
    names = s["latest"].set_index("gsis_id")["full_name"]
    left = sorted(f"{names.get(i, i)} {s['season']} ({int(a)} PFR vs {int(b)} plays)"
                  for i, a, b in zip(c.index[gap], c.loc[gap, "pfr_carries"], c.loc[gap, "carries"]))
    return c[~gap], left


def role(s: dict) -> tuple[pd.DataFrame, list]:
    """This season's role per running back, in the games he played (snaps), early exits left out; and the
    same score in his most recent full game."""
    car, tgt = s["car_all"], s["tgt_all"]
    team_g = pd.DataFrame({"t_car": car.groupby(["game_id", "posteam"]).size(),
                           "t_i10": car.groupby(["game_id", "posteam"])["i10"].sum(),
                           "t_tgt": tgt.groupby(["game_id", "posteam"]).size()}).fillna(0)
    pl = pd.DataFrame({"car": car.groupby(["game_id", "posteam", "rusher_player_id"]).size(),
                       "i10": car.groupby(["game_id", "posteam", "rusher_player_id"])["i10"].sum()})
    pl.index.names = ["game_id", "posteam", "gsis_id"]
    tg = tgt.groupby(["game_id", "posteam", "receiver_player_id"]).agg(tgt=("complete_pass", "size"),
                                                                       rec=("complete_pass", lambda x: int(flag(x).sum())))
    tg.index.names = ["game_id", "posteam", "gsis_id"]
    played = data.played(data.snaps(s["season"]), s["ros"])
    played = played[played["game_id"].isin(set(s["p_all"]["game_id"])) & played["gsis_id"].isin(s["rbs"])].copy()
    med = played.groupby("gsis_id")["offense_pct"].transform("median")
    weeks = dict(zip(s["p_all"]["game_id"], s["p_all"]["week"]))
    played["week"] = played["game_id"].map(weeks)
    low = played[(med >= REGULAR_BACK) & (played["offense_pct"] < PARTIAL_GAME * med)]
    # hurt, not quiet: he missed his team's next game, or the next week's injury report lists him
    team_weeks = s["p_all"].groupby("posteam")["week"].apply(lambda w: sorted(set(w)))
    seen = set(zip(played["gsis_id"], played["week"]))
    inj = pd.read_csv(F.nflverse("injuries", s["season"], max_age_s=F.CURRENT_SEASON_MAX_AGE_S))
    listed = set(zip(inj.loc[inj["report_status"].notna(), "gsis_id"], inj.loc[inj["report_status"].notna(), "week"]))

    def hurt(gsis, team, wk):
        nxt = [w for w in team_weeks.get(team, []) if w > wk]
        if not nxt:
            return False                                   # next game not played yet: keep the game
        return (gsis, nxt[0]) not in seen or (gsis, nxt[0]) in listed

    partial = low[[hurt(i, t, w) for i, t, w in zip(low["gsis_id"], low["team"], low["week"])]]
    names = s["latest"].set_index("gsis_id")["full_name"]
    dropped = sorted(f"{names.get(i, i)} week {weeks.get(gm, '?')} ({100 * pct:.0f}% of snaps)"
                     for i, gm, pct in zip(partial["gsis_id"], partial["game_id"], partial["offense_pct"]))
    skip = set(zip(partial["game_id"], partial["gsis_id"]))
    g = played.rename(columns={"team": "posteam"}).set_index(["game_id", "posteam", "gsis_id"])[[]]
    g = g.join(pl, how="outer").join(tg, how="outer").fillna(0).reset_index()
    g = g[g["gsis_id"].isin(s["rbs"]) & ~pd.Series([k in skip for k in zip(g["game_id"], g["gsis_id"])], index=g.index)]
    g = g.join(team_g, on=["game_id", "posteam"])
    g["week"] = g["game_id"].map(weeks)
    cs = g["car"] / g["t_car"]
    g["role_g"] = 100 * (WEIGHTS["carry_share"] * cs + WEIGHTS["i10_share"] * (g["i10"] + K_I10 * cs) / (g["t_i10"] + K_I10)
                         + WEIGHTS["target_share"] * g["tgt"] / g["t_tgt"])
    last = g.sort_values("week").groupby("gsis_id").last()
    per = g.groupby("gsis_id")
    b = pd.DataFrame({"games": per["game_id"].nunique(), "team": g.sort_values("game_id").groupby("gsis_id")["posteam"].last(),
                      "carries": per["car"].sum(), "i10": per["i10"].sum(), "targets": per["tgt"].sum(),
                      "receptions": per["rec"].sum(), "t_car": per["t_car"].sum(), "t_i10": per["t_i10"].sum(),
                      "t_tgt": per["t_tgt"].sum()})
    b["name"] = names.reindex(b.index)
    b["role_recent"] = last["role_g"].reindex(b.index)
    b["recent_week"] = last["week"].reindex(b.index)
    b["recent_carries"] = last["car"].reindex(b.index)
    b["recent_targets"] = last["tgt"].reindex(b.index)
    return b, dropped


def ngs_ryoe(season: int, weeks=None) -> pd.DataFrame:
    """Per back (gsis id): tracked carries, expected yards, yards over expected. weeks=None: the season row
    (week 0); otherwise the sum of the weekly rows (NGS lists a week only at 10+ carries)."""
    d = rg.load(season) if weeks is None else None
    if d is None:
        df = pd.read_csv(F.nflverse("ngs_rushing", max_age_s=F.CURRENT_SEASON_MAX_AGE_S))
        d = df[(df["season"] == season) & (df["season_type"] == "REG") & df["week"].isin(weeks)
               & (df["player_position"] == "RB")].copy()
    d = d.assign(tracked=rg.tracked_carries(d)[0])
    g = d.groupby("player_gsis_id")
    return pd.DataFrame({"tracked": g["tracked"].sum(), "ryoe": g["rush_yards_over_expected"].sum()})


def subset(s: dict, weeks) -> dict:
    """The same season's inputs cut to some weeks (for the half-season stability check)."""
    t = dict(s)
    for k in ("car", "tgt", "rush", "rec"):
        t[k] = s[k][s[k]["week"].isin(weeks)]
    return t


def blend_r(bt1, bt2, ng1, ng2, lg_bt, lg_ry, sd_bt, sd_ry, min_t=60, min_c=40) -> dict:
    """Half-vs-half stability of broken tackles, yards over expected and their blend, on the same backs."""
    j = bt1.join(bt2, lsuffix="_a", rsuffix="_b", how="inner").join(ng1.add_suffix("_a"), how="inner").join(ng2.add_suffix("_b"), how="inner")
    j = j[(j["touches_a"] >= min_t) & (j["touches_b"] >= min_t) & (j["tracked_a"] >= min_c) & (j["tracked_b"] >= min_c)]
    out = {"backs": len(j)}
    for h in ("a", "b"):
        j[f"zbt_{h}"] = ((j[f"bt_rush_{h}"] + j[f"bt_rec_{h}"]) / j[f"touches_{h}"] - lg_bt) / sd_bt
        j[f"zry_{h}"] = (j[f"ryoe_{h}"] / j[f"tracked_{h}"] - lg_ry) / sd_ry
        j[f"z_{h}"] = (j[f"zbt_{h}"] + j[f"zry_{h}"]) / 2
    for k, nm in (("zbt", "broken tackles"), ("zry", "yards over expected"), ("z", "blend")):
        out[nm] = round(float(j[f"{k}_a"].corr(j[f"{k}_b"])), 2)
    return out


def rate_r(a: pd.DataFrame, b: pd.DataFrame, min_t: int) -> tuple[float, int]:
    j = a.join(b, lsuffix="_a", rsuffix="_b", how="inner")
    j = j[(j["touches_a"] >= min_t) & (j["touches_b"] >= min_t)]
    ra = (j["bt_rush_a"] + j["bt_rec_a"]) / j["touches_a"]
    rb = (j["bt_rush_b"] + j["bt_rec_b"]) / j["touches_b"]
    return round(float(ra.corr(rb)), 2), len(j)


def build() -> tuple[pd.DataFrame, dict]:
    cur, prior = season_inputs(SEASON), season_inputs(PRIOR)
    b, dropped = role(cur)
    c_cur, left_cur = creation(cur)
    c_pri, left_pri = creation(prior)
    cols = ["touches", "bt_rush", "bt_rec", "yac_sum", "pfr_carries"]
    pooled = c_cur[cols].add(c_pri[cols], fill_value=0)
    # stability: 2025 first half vs second half (60+ touches each), and 2025 vs this season (40+ each)
    half = len(prior["weeks"]) // 2
    h1, _ = creation(subset(prior, prior["weeks"][:half]))
    h2, _ = creation(subset(prior, prior["weeks"][half:]))
    r_half, n_half = rate_r(h1, h2, 60)
    r_yy, n_yy = rate_r(c_pri, c_cur, 40)
    ng = ngs_ryoe(SEASON).add(ngs_ryoe(PRIOR), fill_value=0)
    b = b.join(pooled.add_prefix("pool_"), how="left").join(c_cur[["bt_rush", "bt_rec"]].add_prefix("cur_"), how="left")
    b = b.join(ng.add_prefix("ngs_"), how="left")
    b["touches"] = b["carries"] + b["receptions"]
    b["prior_touches"] = c_pri["touches"].reindex(b.index).fillna(0)
    notes = {"weeks this season": cur["weeks"], f"{PRIOR} weeks": f"{prior['weeks'][0]}-{prior['weeks'][-1]}",
             "games left out of role (left hurt: under half his median snap share, then missed or on the report)": dropped,
             "seasons left out of creation (PFR carries miss the plays)": left_cur + left_pri,
             f"broken tackles per touch, {PRIOR} first half vs second half (r, 60+ touches each)": f"{r_half} on {n_half} backs",
             f"broken tackles per touch, {PRIOR} vs {SEASON} weeks so far (r, 40+ touches each)": f"{r_yy} on {n_yy} backs",
             "PFR rows with no gsis id": cur["unmapped"] + prior["unmapped"]}
    league = {"bt": float((pooled["bt_rush"] + pooled["bt_rec"]).sum() / pooled["touches"].sum()),
              "yac": float(pooled["yac_sum"].sum() / pooled["pfr_carries"].sum()),
              "ryoe": float(ng["ryoe"].sum() / ng["tracked"].sum())}
    halves = {"bt": (h1, h2), "ngs": (ngs_ryoe(PRIOR, prior["weeks"][:half]), ngs_ryoe(PRIOR, prior["weeks"][half:]))}
    return b, {"notes": notes, "league": league, "halves": halves}


def rates(b: pd.DataFrame, league: dict, halves: dict, notes: dict) -> tuple[pd.DataFrame, dict]:
    r = b[(b["touches"] >= MIN_TOUCHES) & b["pool_touches"].notna()].copy()
    r["carry_share"] = r["carries"] / r["t_car"]
    r["i10_share"] = (r["i10"] + K_I10 * r["carry_share"]) / (r["t_i10"] + K_I10)
    r["i10_raw"] = (r["i10"] / r["t_i10"]).where(r["t_i10"] > 0)
    r["target_share"] = r["targets"] / r["t_tgt"]
    r["role"] = 100 * sum(w * r[k] for k, w in WEIGHTS.items())
    r["bt"] = r["pool_bt_rush"] + r["pool_bt_rec"]
    r["mtf_per_touch"] = r["bt"] / r["pool_touches"]
    r["ryoe_pc"] = r["ngs_ryoe"] / r["ngs_tracked"]            # NaN: NGS does not list him
    sd_bt, sd_ry = float(r["mtf_per_touch"].std()), float(r["ryoe_pc"].std())
    r["z_bt"] = (r["mtf_per_touch"] - league["bt"]) / sd_bt
    r["z_ryoe"] = (r["ryoe_pc"] - league["ryoe"]) / sd_ry
    r["creation"] = r[["z_bt", "z_ryoe"]].mean(axis=1)          # one half only when NGS does not list him
    r["bt_only"] = r["z_ryoe"].isna()
    st = blend_r(*halves["bt"], *halves["ngs"], league["bt"], league["ryoe"], sd_bt, sd_ry)
    notes[f"{PRIOR} first half vs second half, same backs (r)"] = st
    r["cur_bt"] = r["cur_bt_rush"] + r["cur_bt_rec"]          # NaN when this season's creation was left out
    r["cur_per_touch"] = r["cur_bt"] / r["touches"]
    r["yac_per_carry"] = r["pool_yac_sum"] / r["pool_pfr_carries"]
    r["touches_pg"] = r["touches"] / r["games"]
    r["thin_creation"] = r["prior_touches"] < THIN_PRIOR
    role_mid = float(r["role"].median())
    r["action"] = [ACTIONS[(x >= role_mid, y >= 0)] for x, y in zip(r["role"], r["creation"])]
    tb, mid, _ = rg.backs(rg.load(SEASON))
    tt = rg.teams(tb, mid)
    r["team_exp_ypc"] = r["team"].map(tt["exp_ypc"])
    r["block_vs_league"] = r["team_exp_ypc"] - mid
    if r["team_exp_ypc"].isna().any():
        raise ValueError(f"teams with no NGS expected yards: {sorted(r.loc[r['team_exp_ypc'].isna(), 'team'])}")
    lines = {"role_median": role_mid, "league_mtf_per_touch": league["bt"], "league_yac_per_carry": league["yac"],
             "league_ryoe_pc": league["ryoe"], "sd_bt": sd_bt, "sd_ryoe": sd_ry, "league_exp_ypc": float(mid)}
    keep = ["name", "team", "games", "carries", "i10", "targets", "receptions", "touches", "touches_pg", "carry_share",
            "i10_share", "i10_raw", "target_share", "role", "role_recent", "recent_week", "recent_carries", "recent_targets", "bt", "pool_touches", "prior_touches", "mtf_per_touch", "cur_bt",
            "cur_per_touch", "yac_per_carry", "ryoe_pc", "z_bt", "z_ryoe", "creation", "bt_only", "team_exp_ypc", "block_vs_league",
            "thin_creation", "action"]
    return r[keep].sort_values("role", ascending=False).reset_index(names="gsis_id"), lines


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=ROOT / "experiments" / "out" / "role_creation_2x2_2026")
    a = ap.parse_args(argv)
    b, meta = build()
    notes = meta["notes"]
    r, lines = rates(b, meta["league"], meta["halves"], notes)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.with_suffix(".json").write_text(json.dumps({"lines": lines, "weights": WEIGHTS, "k_i10": K_I10, "notes": notes,
                                                      "rows": r.round(4).to_dict("records")}, indent=1, default=str),
                                          encoding="utf-8")
    wk = notes["weeks this season"]
    st = notes[f"{PRIOR} first half vs second half, same backs (r)"]
    L = [f"# Role vs creation, {SEASON}: role every week so far, creation {PRIOR} + {SEASON} (PFR weeks {wk[0]}-{wk[-1]})", "",
         f"{len(r)} running backs with {MIN_TOUCHES}+ touches. Role = carries {WEIGHTS['carry_share']:.0%}, inside-10 carries "
         f"{WEIGHTS['i10_share']:.0%} (pulled toward the carry share by {K_I10} team inside-10 carries), targets "
         f"{WEIGHTS['target_share']:.0%} of the team's, in his games; split at the median {lines['role_median']:.1f}; the most recent "
         f"full game's score beside it. Creation = the average of broken tackles per touch (league {lines['league_mtf_per_touch']:.3f}) "
         f"and NGS yards over expected per carry (league {lines['league_ryoe_pc']:+.2f}), each in units of its spread across these "
         f"backs; 0 = league. {PRIOR} first half vs second half on the same {st['backs']} backs: broken tackles r = "
         f"{st['broken tackles']}, yards over expected r = {st['yards over expected']}, blend r = {st['blend']}. "
         f"Backs marked * have under {THIN_PRIOR} touches in {PRIOR}: their creation rests on {SEASON} alone; + : NGS does not list "
         f"him, broken tackles only. Colour = team NGS "
         f"expected yards per carry vs {lines['league_exp_ypc']:.2f}. The actions are candidates until a backtest tests them.", ""]
    for act in ACTIONS.values():
        names = [f"{x['name']}{'*' if x['thin_creation'] else ''}{'+' if x['bt_only'] else ''} ({x['team']}, role {x['role']:.0f}"
                 f" -> {x['role_recent']:.0f} wk {int(x['recent_week'])}, creation {x['creation']:+.2f})"
                 for x in r.to_dict("records") if x["action"] == act]
        L += [f"**{act}** ({len(names)}): " + ", ".join(names), ""]
    L += ["Notes: " + "; ".join(f"{k}: {v}" for k, v in notes.items())]
    a.out.with_suffix(".md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
