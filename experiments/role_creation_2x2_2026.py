# expires: 2026-11-11
"""Running backs on role vs creation, with the blocking as colour (the user's framework, 2026-10-12). A study,
not a model: it changes nothing in the calculator (frozen to 2026-11-02, DECISIONS #245). Its quadrant
actions (hold / candidate sell / candidate buy / drop) are labels to be TESTED, not findings: whether
creation predicts a later change of role is a separate backtest, not run here.

- x, role (this season): one score from three of the back's shares of his team's work, in the games he
  played: carries 50%, carries inside the opponent's 10 25%, targets 25% (a stated choice; targets stand in
  for route participation, which no public feed carries). Inside-10 work is lumpy -- a team may have two
  such carries in a month -- so a back's inside-10 share is pulled toward his carry share by K_I10 team
  inside-10 carries: (his inside-10 carries + K_I10 x carry share) / (team's + K_I10). Team carries include
  quarterback designed runs (a goal-line quarterback takes real work from the back) and leave out scrambles
  and kneels. For a regular back (median snap share 40%+), a game in which he played under half his own
  median snap share (he left hurt) is left out of his role, and named; a backup's quiet games are his role
  and stay in.
- y, creation (a trait, so measured over 2025 and this season together): broken tackles (Pro Football
  Reference's count on carries and catches; close to, not the same as, PFF's 'missed tackles forced') per
  touch. Four weeks of broken tackles carry no repeatable signal (split-half r near zero at the first
  check), so a single season's rate is too noisy to act on. Two stability checks are printed: 2025's
  first half against its second half (a full season's trait), and 2025 against this season's weeks (the
  second limited by the short 2026 sample). A back with under 50 touches in 2025 (a rookie, mostly) has a
  creation number resting on this season alone; it is flagged. Yards after contact per carry is shown beside it as the secondary check.
- colour, the blocking: the team's Next Gen Stats expected yards per carry (run_game_2x2_2026.py, frozen at
  the handoff, so the back's own vision is not in it), against the league.
Weeks: this season, only those PFR has posted for every game in the play-by-play (PFR runs behind it); 2025,
the whole regular season. A back is a running back by his latest weekly roster listing of each season, with
fullbacks (depth chart FB) left out; PFR and snap ids map to gsis ids through the rosters. A back whose PFR
carries in a season differ from his play-by-play carries by more than 2 (an id that does not map, a gap in
PFR) has that season left out of creation, and is named. A back needs 30+ touches this season. Quadrants
split at the median role score of the backs shown (a stated choice: half the listed backs are 'high role')
and at the league's broken tackles per touch over every running back's touches in the same seasons."""

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
    p, rush, rec = (x[x["week"].isin(weeks)] for x in (p, rush, rec))
    ros = data.rosters(season)
    latest = ros.dropna(subset=["gsis_id"]).sort_values("week").drop_duplicates("gsis_id", keep="last")
    depth = pd.read_csv(F.nflverse("rosters_weekly", season, **age), usecols=["gsis_id", "week", "depth_chart_position"])
    depth = depth.dropna(subset=["gsis_id"]).sort_values("week").drop_duplicates("gsis_id", keep="last")
    fb = set(depth.loc[depth["depth_chart_position"] == "FB", "gsis_id"])
    rbs = set(latest.loc[latest["position"] == "RB", "gsis_id"]) - fb
    car = p[flag(p["rush_attempt"]) & ~flag(p["two_point_attempt"]) & ~flag(p["qb_kneel"]) & ~flag(p["qb_scramble"])
            & p["rusher_player_id"].notna()]
    car = car.assign(i10=car["yardline_100"] <= 10)
    tgt = p[flag(p["pass_attempt"]) & ~flag(p["sack"]) & ~flag(p["two_point_attempt"]) & p["receiver_player_id"].notna()]
    ids = ros.dropna(subset=["pfr_id", "gsis_id"]).drop_duplicates("pfr_id")
    pfr_gsis = dict(zip(ids["pfr_id"], ids["gsis_id"]))
    rush = rush.assign(gsis_id=rush["pfr_player_id"].map(pfr_gsis))
    rec = rec.assign(gsis_id=rec["pfr_player_id"].map(pfr_gsis))
    for f, cols in ((rush, ["rushing_broken_tackles", "rushing_yards_after_contact", "carries"]), (rec, ["receiving_broken_tackles"])):
        bad = f[f["gsis_id"].isin(rbs)][cols].isna().any(axis=1)
        if bad.any():
            raise ValueError(f"{season}: {int(bad.sum())} running-back PFR rows with a blank in {cols}")
    return {"season": season, "p": p, "car": car, "tgt": tgt, "rush": rush, "rec": rec, "ros": ros, "latest": latest,
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
    """This season's role per running back, in the games he played (snaps), early exits left out."""
    car, tgt = s["car"], s["tgt"]
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
    played = played[played["game_id"].isin(set(s["p"]["game_id"])) & played["gsis_id"].isin(s["rbs"])].copy()
    med = played.groupby("gsis_id")["offense_pct"].transform("median")
    partial = played[(med >= REGULAR_BACK) & (played["offense_pct"] < PARTIAL_GAME * med)]
    names = s["latest"].set_index("gsis_id")["full_name"]
    weeks = dict(zip(s["p"]["game_id"], s["p"]["week"]))
    dropped = sorted(f"{names.get(i, i)} week {weeks.get(gm, '?')} ({100 * pct:.0f}% of snaps)"
                     for i, gm, pct in zip(partial["gsis_id"], partial["game_id"], partial["offense_pct"]))
    skip = set(zip(partial["game_id"], partial["gsis_id"]))
    g = played.rename(columns={"team": "posteam"}).set_index(["game_id", "posteam", "gsis_id"])[[]]
    g = g.join(pl, how="outer").join(tg, how="outer").fillna(0).reset_index()
    g = g[g["gsis_id"].isin(s["rbs"]) & ~pd.Series([k in skip for k in zip(g["game_id"], g["gsis_id"])], index=g.index)]
    g = g.join(team_g, on=["game_id", "posteam"])
    per = g.groupby("gsis_id")
    b = pd.DataFrame({"games": per["game_id"].nunique(), "team": g.sort_values("game_id").groupby("gsis_id")["posteam"].last(),
                      "carries": per["car"].sum(), "i10": per["i10"].sum(), "targets": per["tgt"].sum(),
                      "receptions": per["rec"].sum(), "t_car": per["t_car"].sum(), "t_i10": per["t_i10"].sum(),
                      "t_tgt": per["t_tgt"].sum()})
    b["name"] = names.reindex(b.index)
    return b, dropped


def subset(s: dict, weeks) -> dict:
    """The same season's inputs cut to some weeks (for the half-season stability check)."""
    t = dict(s)
    for k in ("car", "tgt", "rush", "rec"):
        t[k] = s[k][s[k]["week"].isin(weeks)]
    return t


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
    b = b.join(pooled.add_prefix("pool_"), how="left").join(c_cur[["bt_rush", "bt_rec"]].add_prefix("cur_"), how="left")
    b["touches"] = b["carries"] + b["receptions"]
    b["prior_touches"] = c_pri["touches"].reindex(b.index).fillna(0)
    notes = {"weeks this season": cur["weeks"], f"{PRIOR} weeks": f"{prior['weeks'][0]}-{prior['weeks'][-1]}",
             "games left out of role (under half his median snap share)": dropped,
             "seasons left out of creation (PFR carries miss the plays)": left_cur + left_pri,
             f"broken tackles per touch, {PRIOR} first half vs second half (r, 60+ touches each)": f"{r_half} on {n_half} backs",
             f"broken tackles per touch, {PRIOR} vs {SEASON} weeks so far (r, 40+ touches each)": f"{r_yy} on {n_yy} backs",
             "PFR rows with no gsis id": cur["unmapped"] + prior["unmapped"]}
    league = {"bt": float((pooled["bt_rush"] + pooled["bt_rec"]).sum() / pooled["touches"].sum()),
              "yac": float(pooled["yac_sum"].sum() / pooled["pfr_carries"].sum())}
    return b, {"notes": notes, "league": league}


def rates(b: pd.DataFrame, league: dict) -> tuple[pd.DataFrame, dict]:
    r = b[(b["touches"] >= MIN_TOUCHES) & b["pool_touches"].notna()].copy()
    r["carry_share"] = r["carries"] / r["t_car"]
    r["i10_share"] = (r["i10"] + K_I10 * r["carry_share"]) / (r["t_i10"] + K_I10)
    r["i10_raw"] = (r["i10"] / r["t_i10"]).where(r["t_i10"] > 0)
    r["target_share"] = r["targets"] / r["t_tgt"]
    r["role"] = 100 * sum(w * r[k] for k, w in WEIGHTS.items())
    r["bt"] = r["pool_bt_rush"] + r["pool_bt_rec"]
    r["mtf_per_touch"] = r["bt"] / r["pool_touches"]
    r["cur_bt"] = r["cur_bt_rush"] + r["cur_bt_rec"]          # NaN when this season's creation was left out
    r["cur_per_touch"] = r["cur_bt"] / r["touches"]
    r["yac_per_carry"] = r["pool_yac_sum"] / r["pool_pfr_carries"]
    r["touches_pg"] = r["touches"] / r["games"]
    r["thin_creation"] = r["prior_touches"] < THIN_PRIOR
    role_mid = float(r["role"].median())
    r["action"] = [ACTIONS[(x >= role_mid, y >= league["bt"])] for x, y in zip(r["role"], r["mtf_per_touch"])]
    tb, mid, _ = rg.backs(rg.load(SEASON))
    tt = rg.teams(tb, mid)
    r["team_exp_ypc"] = r["team"].map(tt["exp_ypc"])
    r["block_vs_league"] = r["team_exp_ypc"] - mid
    if r["team_exp_ypc"].isna().any():
        raise ValueError(f"teams with no NGS expected yards: {sorted(r.loc[r['team_exp_ypc'].isna(), 'team'])}")
    lines = {"role_median": role_mid, "league_mtf_per_touch": league["bt"], "league_yac_per_carry": league["yac"],
             "league_exp_ypc": float(mid)}
    keep = ["name", "team", "games", "carries", "i10", "targets", "receptions", "touches", "touches_pg", "carry_share",
            "i10_share", "i10_raw", "target_share", "role", "bt", "pool_touches", "prior_touches", "mtf_per_touch", "cur_bt",
            "cur_per_touch", "yac_per_carry", "team_exp_ypc", "block_vs_league", "thin_creation", "action"]
    return r[keep].sort_values("role", ascending=False).reset_index(names="gsis_id"), lines


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=ROOT / "experiments" / "out" / "role_creation_2x2_2026")
    a = ap.parse_args(argv)
    b, meta = build()
    r, lines = rates(b, meta["league"])
    notes = meta["notes"]
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.with_suffix(".json").write_text(json.dumps({"lines": lines, "weights": WEIGHTS, "k_i10": K_I10, "notes": notes,
                                                      "rows": r.round(4).to_dict("records")}, indent=1, default=str),
                                          encoding="utf-8")
    wk = notes["weeks this season"]
    L = [f"# Role vs creation, {SEASON}: role weeks {wk[0]}-{wk[-1]} (the weeks PFR has in full); creation {PRIOR} + {SEASON}", "",
         f"{len(r)} running backs with {MIN_TOUCHES}+ touches. Role = carries {WEIGHTS['carry_share']:.0%}, inside-10 carries "
         f"{WEIGHTS['i10_share']:.0%} (pulled toward the carry share by {K_I10} team inside-10 carries), targets "
         f"{WEIGHTS['target_share']:.0%} of the team's, in his games; split at the median {lines['role_median']:.1f}. Creation = "
         f"broken tackles (PFR) per touch over {PRIOR} and {SEASON}; league {lines['league_mtf_per_touch']:.3f} (yards after "
         f"contact {lines['league_yac_per_carry']:.2f} a carry). Stability of the rate: "
         f"{PRIOR} first half vs second half r = {notes[f'broken tackles per touch, {PRIOR} first half vs second half (r, 60+ touches each)']}; "
         f"{PRIOR} vs {SEASON} so far r = {notes[f'broken tackles per touch, {PRIOR} vs {SEASON} weeks so far (r, 40+ touches each)']}. "
         f"Backs marked * have under {THIN_PRIOR} touches in {PRIOR}: their creation rests on {SEASON} alone. Colour = team NGS "
         f"expected yards per carry vs {lines['league_exp_ypc']:.2f}. The actions are candidates until a backtest tests them.", ""]
    for act in ACTIONS.values():
        names = [f"{x['name']}{'*' if x['thin_creation'] else ''} ({x['team']}, role {x['role']:.0f}, {x['mtf_per_touch']:.3f} broken tackles/touch on "
                 f"{int(x['pool_touches'])} touches)" for x in r.to_dict("records") if x["action"] == act]
        L += [f"**{act}** ({len(names)}): " + ", ".join(names), ""]
    L += ["Notes: " + "; ".join(f"{k}: {v}" for k, v in notes.items())]
    a.out.with_suffix(".md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
