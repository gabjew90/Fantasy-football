# expires: 2026-11-11
"""Running backs on role vs creation (the user's spec, revised 2026-10-12). A study, not a model: it changes
nothing in the calculator (frozen to 2026-11-02, DECISIONS #245). The quadrant actions are the spec's
reasoning about how the metrics behave; they are not backtested (the user's call: no backtest).

The chart
- x, role (recent, because role changes fast): the average of route participation and inside-the-10 carry
  share, counting only games he played alongside his team's current backfield, the team's last three games
  weighted double. No public feed has route participation, so offensive snap share stands in for it (on the
  same 0-100% scale the 50% cut needs). Inside-10 share is lumpy, so it is pulled toward his carry share by
  K_I10 team inside-10 carries. 'Current backfield' = the team's backs with a median snap share of 25%+ over
  two or more games who played in one of its last two games; a game one of them missed is left out when
  his median snap share is at least half the back's own. A regular back's (median snap share 40%+) game in
  which he played under half his own median AND then missed the team's next game or was listed Out or
  Doubtful the next week is left out too (he left hurt; it is not his role). Cut at 50% (the clear lead back).
- y, creation (slow, because talent changes slowly): broken tackles per touch -- Pro Football Reference's
  count on carries and catches, close to but not PFF's 'missed tackles forced' -- over 2025 and 2026 to date,
  pulled toward the qualifying backs' median rate by K pseudo-touches: (broken tackles + K x median) /
  (touches + K). K is not chosen by hand: it is set from how much the rate repeats between 2025's two halves,
  K = (average half-season touches) x (1 - r) / r, so the less the rate repeats, the harder a back is pulled
  to the middle. Cut at the median of the qualifying backs. A back with under THIN_PRIOR touches in 2025
  (mostly rookies) is flagged: his number rests on 2026 alone.
- close call: how many broken tackles would move him across the creation line, on his own touches; within
  CLOSE_EVENTS is marked. This replaces any confidence score.
Qualifying: 2025 + 2026 touches >= MIN_TOUCHES and at least two role games this season.

Columns beside the chart, shown for judgement, not scored
- creation context: NGS percent of rushes over expected (2026, where NGS lists him). Two unrelated median
  splits disagree about half the time by construction, so it is context only.
- line: the team's Next Gen Stats expected yards per carry against the league (no feed has run block win
  rate); good / bad at 0.10 either side.
- teammates: yards before contact per carry (2026, the same line) and creation against his team's other
  backs with 10+ touches this season: wins both / loses both / split.
- teammate out: a current-backfield teammate on the latest week's injury report (unless he then played that
  week) or who missed the team's latest game, with his status; the report gives a status, not a return date.

Data: role uses every week of 2026 play-by-play; the PFR measures use the weeks PFR has posted for every game
(2026) and the whole 2025 regular season. A back is a running back by his latest weekly roster listing of each
season (fullbacks out); PFR and snap ids map to gsis ids through the rosters; a back whose PFR carries miss his
play-by-play carries by more than 2 has that season left out, named. Carries leave out QB scrambles and kneels."""

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
THIN_PRIOR = 50           # fewer 2025 touches than this: creation rests on 2026 alone
CLOSE_EVENTS = 2          # within this many broken tackles of the creation line: a close call
K_I10 = 5                 # team inside-10 carries' worth of pull toward his carry share
RECENT_GAMES, RECENT_WEIGHT = 3, 2.0
CORE_BACK = 0.25          # median snap share that makes a back part of a backfield
ROLE_CUT = 50.0           # the clear lead back
MIN_TOUCHES = 50
LINE_BAND = 0.10          # expected yards a carry from league that makes a line good or bad
MIN_MATE_TOUCHES = 10
COLS = ["game_id", "season", "week", "season_type", "posteam", "yardline_100", "rush_attempt", "pass_attempt", "sack",
        "two_point_attempt", "qb_kneel", "qb_scramble", "rusher_player_id", "receiver_player_id", "complete_pass"]
ACTIONS = {(True, True): "Hold", (True, False): "Sell high", (False, True): "Buy low", (False, False): "Drop"}


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


def load(season: int) -> dict:
    AGE = {"max_age_s": F.CURRENT_SEASON_MAX_AGE_S} if season == SEASON else {}
    p = pd.read_csv(F.nflverse("pbp", season, **AGE), usecols=COLS, low_memory=False)
    p = p[p["season_type"] == "REG"]
    rush = pd.read_csv(F.nflverse("pfr_adv_rush", season, **AGE))
    rec = pd.read_csv(F.nflverse("pfr_adv_rec", season, **AGE))
    pfr_weeks = full_pfr_weeks(p, rush, rec)
    rush, rec = rush[rush["week"].isin(pfr_weeks)], rec[rec["week"].isin(pfr_weeks)]
    ros = data.rosters(season)
    latest = ros.dropna(subset=["gsis_id"]).sort_values("week").drop_duplicates("gsis_id", keep="last")
    depth = pd.read_csv(F.nflverse("rosters_weekly", season, **AGE), usecols=["gsis_id", "week", "depth_chart_position"])
    depth = depth.dropna(subset=["gsis_id"]).sort_values("week").drop_duplicates("gsis_id", keep="last")
    rbs = set(latest.loc[latest["position"] == "RB", "gsis_id"]) - set(depth.loc[depth["depth_chart_position"] == "FB", "gsis_id"])
    ids = ros.dropna(subset=["pfr_id", "gsis_id"]).drop_duplicates("pfr_id")
    pfr_gsis = dict(zip(ids["pfr_id"], ids["gsis_id"]))
    rush, rec = rush.assign(gsis_id=rush["pfr_player_id"].map(pfr_gsis)), rec.assign(gsis_id=rec["pfr_player_id"].map(pfr_gsis))
    for f, cols in ((rush, ["rushing_broken_tackles", "rushing_yards_after_contact", "rushing_yards_before_contact", "carries"]),
                    (rec, ["receiving_broken_tackles"])):
        bad = f[f["gsis_id"].isin(rbs)][cols].isna().any(axis=1)
        if bad.any():
            raise ValueError(f"{int(bad.sum())} running-back PFR rows with a blank in {cols}")
    car = p[flag(p["rush_attempt"]) & ~flag(p["two_point_attempt"]) & ~flag(p["qb_kneel"]) & ~flag(p["qb_scramble"])
            & p["rusher_player_id"].notna()]
    car = car.assign(i10=car["yardline_100"] <= 10)
    tgt = p[flag(p["pass_attempt"]) & ~flag(p["sack"]) & ~flag(p["two_point_attempt"]) & p["receiver_player_id"].notna()]
    played = data.played(data.snaps(season), ros)
    weeks = dict(zip(p["game_id"], p["week"]))
    played = played[played["game_id"].isin(weeks) & played["gsis_id"].isin(rbs)].copy()
    played["week"] = played["game_id"].map(weeks)
    inj = pd.read_csv(F.nflverse("injuries", season, **AGE))
    return {"p": p, "car": car, "tgt": tgt, "rush": rush, "rec": rec, "played": played, "rbs": rbs, "pfr_weeks": pfr_weeks,
            "names": latest.set_index("gsis_id")["full_name"], "inj": inj, "weeks": weeks}


def role(d: dict) -> tuple[pd.DataFrame, dict]:
    car, pl, names = d["car"], d["played"], d["names"]
    team_games = d["p"].groupby("posteam")["week"].apply(lambda w: sorted(set(w)))
    # current backfield: core backs (median snap share 25%+) who played in one of the team's last two games
    med = pl.groupby(["team", "gsis_id"])["offense_pct"].median()
    n_games = pl.groupby(["team", "gsis_id"])["game_id"].nunique()
    core = med[(med >= CORE_BACK) & (n_games >= 2)].reset_index()
    seen = set(zip(pl["gsis_id"], pl["week"]))
    current = {t: sorted(g for g in grp["gsis_id"] if any((g, w) in seen for w in team_games[t][-2:]))
               for t, grp in core.groupby("team")}
    # a game counts for a back only if every other current-backfield member of his team played in it
    in_game = pl.groupby("game_id")["gsis_id"].apply(set)
    keep, left_out = [], {}
    for row in pl.itertuples():
        own = med.get((row.team, row.gsis_id), 0)
        missing = [m for m in current.get(row.team, []) if m != row.gsis_id and m not in in_game.get(row.game_id, set())
                   and med.get((row.team, m), 0) >= 0.5 * own]
        keep.append(not missing)
        if missing:
            left_out.setdefault(names.get(row.gsis_id, row.gsis_id), []).append(
                f"wk {row.week} (no {', '.join(names.get(m, m) for m in missing)})")
    # left hurt: a regular back's game under half his median snaps, then a missed next game or Out/Doubtful next week
    own_med = pl.groupby("gsis_id")["offense_pct"].transform("median")
    inj = d["inj"]
    serious = set(zip(inj.loc[inj["report_status"].isin(["Out", "Doubtful"]), "gsis_id"],
                      inj.loc[inj["report_status"].isin(["Out", "Doubtful"]), "week"]))
    hurt = []
    for row, om in zip(pl.itertuples(), own_med):
        nxt = [w for w in team_games.get(row.team, []) if w > row.week]
        h = bool(om >= 0.40 and row.offense_pct < 0.5 * om and nxt
                 and ((row.gsis_id, nxt[0]) not in seen or (row.gsis_id, nxt[0]) in serious))
        hurt.append(h)
        if h:
            left_out.setdefault(names.get(row.gsis_id, row.gsis_id), []).append(f"wk {row.week} (left hurt, {100 * row.offense_pct:.0f}% of snaps)")
    keep = [k and not h for k, h in zip(keep, hurt)]
    g = pl[keep].copy()
    rank = {(t, w): i for t, ws in team_games.items() for i, w in enumerate(reversed(ws))}
    g["wt"] = [RECENT_WEIGHT if rank.get((t, w), 99) < RECENT_GAMES else 1.0 for t, w in zip(g["team"], g["week"])]
    pg = car.groupby(["game_id", "rusher_player_id"]).agg(car=("i10", "size"), i10=("i10", "sum"))
    pg.index.names = ["game_id", "gsis_id"]
    tcar = car.groupby(["game_id", "posteam"]).agg(t_car=("i10", "size"), t_i10=("i10", "sum"))
    tcar.index.names = ["game_id", "team"]
    g = g.join(pg, on=["game_id", "gsis_id"]).join(tcar, on=["game_id", "team"])
    g[["car", "i10"]] = g[["car", "i10"]].fillna(0)
    w = g["wt"]
    per = g.assign(wsnap=g["offense_pct"] * w, wcar=g["car"] * w, wi10=g["i10"] * w, wtcar=g["t_car"] * w,
                   wti10=g["t_i10"] * w).groupby("gsis_id")
    b = pd.DataFrame({"team": g.sort_values("week").groupby("gsis_id")["team"].last(), "games": per["game_id"].nunique(),
                      "snap": per["wsnap"].sum() / per["wt"].sum(), "carry_share": per["wcar"].sum() / per["wtcar"].sum(),
                      "i10": per["i10"].sum(), "t_i10": per["t_i10"].sum(), "wi10": per["wi10"].sum(), "wti10": per["wti10"].sum()})
    b["i10_share"] = (b["wi10"] + K_I10 * b["carry_share"]) / (b["wti10"] + K_I10)
    b["role"] = 100 * (b["snap"] + b["i10_share"]) / 2
    b["name"] = names.reindex(b.index)
    return b, {"current": current, "left_out": left_out}


def creation(d: dict, weeks=None) -> tuple[pd.DataFrame, list]:
    """Per running back: touches, broken tackles, yards before/after contact, over PFR's full weeks (or a subset)."""
    rbs, pw = d["rbs"], d["pfr_weeks"] if weeks is None else [w for w in d["pfr_weeks"] if w in set(weeks)]
    car = d["car"][d["car"]["week"].isin(pw) & d["car"]["rusher_player_id"].isin(rbs)]
    tgt = d["tgt"][d["tgt"]["week"].isin(pw) & d["tgt"]["receiver_player_id"].isin(rbs)]
    c = pd.DataFrame({"carries": car.groupby("rusher_player_id").size(),
                      "receptions": tgt.groupby("receiver_player_id")["complete_pass"].apply(lambda x: int(flag(x).sum()))}).fillna(0)
    rush, rec = d["rush"][d["rush"]["week"].isin(pw)], d["rec"][d["rec"]["week"].isin(pw)]
    r, q = rush.groupby("gsis_id"), rec.groupby("gsis_id")
    c["bt"] = r["rushing_broken_tackles"].sum().reindex(c.index).fillna(0) + q["receiving_broken_tackles"].sum().reindex(c.index).fillna(0)
    c["ybc_sum"] = r["rushing_yards_before_contact"].sum().reindex(c.index).fillna(0)
    c["yac_sum"] = r["rushing_yards_after_contact"].sum().reindex(c.index).fillna(0)
    c["pfr_carries"] = r["carries"].sum().reindex(c.index).fillna(0)
    c["touches"] = c["carries"] + c["receptions"]
    gap = (c["pfr_carries"] - c["carries"]).abs() > 2
    left = sorted(f"{d['names'].get(i, i)} ({int(a)} PFR vs {int(b)} plays)" for i, a, b in
                  zip(c.index[gap], c.loc[gap, "pfr_carries"], c.loc[gap, "carries"]))
    c = c[~gap].copy()
    c["mtf"] = c["bt"] / c["touches"]
    c["ybc"] = c["ybc_sum"] / c["pfr_carries"]
    c["yac"] = c["yac_sum"] / c["pfr_carries"]
    return c, left


def latest_status(d: dict) -> dict:
    """Status per gsis id on the LATEST injury report only (an older listing is not today's status)."""
    inj = d["inj"][d["inj"]["report_status"].notna()]
    if inj.empty:
        return {}
    wk = int(inj["week"].max())
    cur = inj[inj["week"] == wk]
    seen = set(zip(d["played"]["gsis_id"], d["played"]["week"]))
    return {gid: f"{r['report_status']} wk {wk} ({r['report_primary_injury']})" for gid, r in cur.set_index("gsis_id").iterrows()
            if (gid, wk) not in seen}                         # he played that week's game: the tag was pre-game


def half_r(d: dict) -> tuple[float, float, int]:
    """2025's first half vs second half: the broken-tackle rate's repeat r, average half touches, backs."""
    wk = d["pfr_weeks"]
    h1, _ = creation(d, wk[: len(wk) // 2])
    h2, _ = creation(d, wk[len(wk) // 2:])
    j = h1.join(h2, lsuffix="_a", rsuffix="_b", how="inner")
    j = j[(j["touches_a"] >= 60) & (j["touches_b"] >= 60)]
    return float(j["mtf_a"].corr(j["mtf_b"])), float((j["touches_a"] + j["touches_b"]).mean() / 2), len(j)


def build() -> tuple[pd.DataFrame, dict]:
    d, dp = load(SEASON), load(PRIOR)
    b, meta = role(d)
    c_cur, left_cur = creation(d)
    c_pri, left_pri = creation(dp)
    cols = ["touches", "bt"]
    pooled = c_cur[cols].add(c_pri[cols], fill_value=0)
    r_half, half_t, n_half = half_r(dp)
    k = half_t * (1 - r_half) / r_half if r_half > 0.02 else 50 * half_t      # no repeat at all: pull nearly to the middle
    r = b[b["games"] >= 2].join(pooled.add_prefix("pool_"), how="inner")
    r = r.join(c_cur[["touches", "bt", "ybc"]].add_prefix("cur_"), how="left")
    r["prior_touches"] = c_pri["touches"].reindex(r.index).fillna(0)
    q = r[r["pool_touches"] >= MIN_TOUCHES].copy()
    q["raw"] = q["pool_bt"] / q["pool_touches"]
    m = float(q["raw"].median())
    q["creation"] = (q["pool_bt"] + k * m) / (q["pool_touches"] + k)
    cut = float(q["creation"].median())
    # broken tackles that would move him across the line on his own touches: solve (bt + x + k m) / (n + k) = cut
    q["to_flip"] = cut * (q["pool_touches"] + k) - k * m - q["pool_bt"]
    q["close_call"] = q["to_flip"].abs() <= CLOSE_EVENTS
    q["thin"] = q["prior_touches"] < THIN_PRIOR
    q["action"] = [ACTIONS[(x >= ROLE_CUT, y >= cut)] for x, y in zip(q["role"], q["creation"])]

    # context: NGS percent of rushes over expected (2026), shown, not scored
    ngs_rows = rg.load(SEASON)
    q["pct_over_exp"] = ngs_rows.set_index("player_gsis_id")["rush_pct_over_expected"].reindex(q.index)

    # the line (NGS team expected yards per carry vs league; run block win rate is not in any feed)
    tb, lg_mid, _ = rg.backs(ngs_rows)
    tt = rg.teams(tb, lg_mid)
    q["team_exp_ypc"] = q["team"].map(tt["exp_ypc"])
    if q["team_exp_ypc"].isna().any():
        raise ValueError(f"teams with no NGS expected yards: {sorted(q.loc[q['team_exp_ypc'].isna(), 'team'])}")
    q["block_vs_league"] = q["team_exp_ypc"] - lg_mid
    q["line"] = ["good" if v >= LINE_BAND else "bad" if v <= -LINE_BAND else "average" for v in q["block_vs_league"]]

    # teammates (10+ touches this season): 2026 yards before contact (same line) and creation
    allr = r.copy()
    allr["creation"] = (allr["pool_bt"] + k * m) / (allr["pool_touches"] + k)
    pool = allr[allr["cur_touches"].fillna(0) >= MIN_MATE_TOUCHES]
    res, txt = [], []
    for gid, row in q.iterrows():
        mates = pool[(pool["team"] == row["team"]) & (pool.index != gid)]
        if mates.empty:
            res.append("")
            txt.append("")
            continue
        my = mates["cur_ybc"].dropna()
        better = bool((row["cur_ybc"] > my).all() and (row["creation"] > mates["creation"]).all())
        worse = bool((row["cur_ybc"] < my).all() and (row["creation"] < mates["creation"]).all())
        res.append("wins both" if better else "loses both" if worse else "split")
        txt.append(", ".join(f"{n} ({y:.2f} before contact, {100 * c:.1f} creation)" for n, y, c in
                             zip(mates["name"], mates["cur_ybc"], mates["creation"])))
    q["teammates_result"], q["teammates"] = res, txt

    # teammate out
    status = latest_status(d)
    team_last = d["played"].groupby("team")["week"].max()
    seen = set(zip(d["played"]["gsis_id"], d["played"]["week"]))
    flags = []
    for gid, row in q.iterrows():
        notes = [f"{d['names'].get(mm, mm)}: {status.get(mm, 'missed the latest game')}"
                 for mm in meta["current"].get(row["team"], [])
                 if mm != gid and ((mm, team_last.get(row["team"])) not in seen or mm in status)]
        flags.append("; ".join(notes))
    q["teammate_out"] = flags
    q["own_status"] = [status.get(i, "") for i in q.index]
    no_role = sorted(d["names"].get(i, i) for i in c_cur.index[(c_cur["touches"] >= 10) & ~c_cur.index.isin(b.index)])
    lines = {"role_cut": ROLE_CUT, "creation_cut": cut, "raw_median": m, "k": k, "league_exp_ypc": float(lg_mid)}
    notes = {"role weeks": sorted(set(d["weeks"].values())), "creation": f"{PRIOR} weeks 1-{dp['pfr_weeks'][-1]} + {SEASON} weeks "
             f"{d['pfr_weeks'][0]}-{d['pfr_weeks'][-1]}",
             f"{PRIOR} half vs half repeat": f"r = {r_half:.2f} on {n_half} backs (60+ touches each half), "
                                             f"{half_t:.0f} touches a half on average -> K = {k:.0f} pseudo-touches",
             "games left out of role (a current-backfield teammate did not play)": meta["left_out"],
             "seasons left out of creation (PFR carries miss the plays)": left_cur + left_pri,
             "backs with 10+ touches this season but no role game": no_role, "qualifying backs": len(q)}
    return q, {"lines": lines, "notes": notes}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=ROOT / "experiments" / "out" / "role_creation_2x2_2026")
    a = ap.parse_args(argv)
    q, meta = build()
    keep = ["name", "team", "games", "snap", "carry_share", "i10", "t_i10", "i10_share", "role", "pool_touches", "pool_bt",
            "prior_touches", "cur_touches", "cur_bt", "raw", "creation", "to_flip", "close_call", "thin", "cur_ybc", "pct_over_exp",
            "team_exp_ypc", "block_vs_league", "line", "teammates_result", "teammates", "teammate_out", "own_status", "action"]
    rows = q[keep].sort_values("role", ascending=False).reset_index(names="gsis_id")
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.with_suffix(".json").write_text(json.dumps({**meta, "rows": rows.round(4).to_dict("records")}, indent=1, default=str),
                                          encoding="utf-8")
    L, N = meta["lines"], meta["notes"]
    out = [f"# Role vs creation, {SEASON}: role weeks {N['role weeks'][0]}-{N['role weeks'][-1]} (recent weighted); creation "
           f"{N['creation']}", "",
           f"{N['qualifying backs']} backs ({MIN_TOUCHES}+ touches over {PRIOR}-{SEASON}, 2+ role games). Role cut {ROLE_CUT:.0f}%. "
           f"Creation = broken tackles per touch pulled toward the median {100 * L['raw_median']:.1f} per 100 by K = {L['k']:.0f} "
           f"pseudo-touches ({N[f'{PRIOR} half vs half repeat']}); cut at the median {100 * L['creation_cut']:.2f}. Close call = "
           f"within {CLOSE_EVENTS} broken tackles of the line ('To flip': + = that many more to reach the line, - = that many above "
           f"it). * = under {THIN_PRIOR} touches in {PRIOR}. Not backtested.", "",
           "| Back | Team | Role | Creation /100 | BT on touches | To flip | Action | % runs over exp. | Line | Teammates | Teammate out | Own status |",
           "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for x in rows.to_dict("records"):
        flip = f"{x['to_flip']:+.1f}" + (" close" if x["close_call"] else "")
        poe = "" if pd.isna(x["pct_over_exp"]) else f"{100 * x['pct_over_exp']:.0f}%"
        out.append(f"| {x['name']}{'*' if x['thin'] else ''} | {x['team']} | {x['role']:.0f} | {100 * x['creation']:.2f} | "
                   f"{int(x['pool_bt'])} on {int(x['pool_touches'])} | {flip} | {x['action']} | {poe} | {x['line']} | "
                   f"{x['teammates_result'] or '-'} | {x['teammate_out'] or '-'} | {x['own_status'] or '-'} |")
    out += ["", "Notes: " + "; ".join(f"{k}: {v}" for k, v in N.items() if k != "qualifying backs")]
    a.out.with_suffix(".md").write_text("\n".join(out) + "\n", encoding="utf-8")
    print("\n".join(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
