# expires: 2026-11-11
"""Running backs on role vs creation, with four checks (the user's spec, 2026-10-12). A study, not a model:
it changes nothing in the calculator (frozen to 2026-11-02, DECISIONS #245). The quadrant actions are the
spec's reasoning about how the metrics behave; they are not backtested (the user's call: no backtest).

The chart
- x, role: the average of route participation and inside-the-10 carry share, counting only games he played
  alongside his team's current backfield, the team's last three games weighted double. No public feed has
  route participation, so offensive snap share stands in for it (on the same 0-100% scale, which the 50%
  lead-back cutoff needs; target share would not reach it). Inside-10 share is lumpy -- a team may have two
  such carries in a month -- so it is pulled toward his carry share by K_I10 team inside-10 carries (which
  brings his carry share in where his team has few such carries).
  'Current backfield' = the team's backs with a median snap share of 25%+ who played in one of its last two
  games. A game in which one of them did not play is left out when that teammate's median snap share is at
  least half the back's own (his role there was inflated by the absence); a minor teammate's absence does not
  change a starter's role, so those games stay.
- y, creation: missed tackles forced per touch -- Pro Football Reference's broken tackles on carries and
  catches (close to, not the same as, PFF's count) -- this season, 50+ touches. A season's first weeks of
  this rate barely repeat (split-half r near zero at an earlier check), so the checks matter.
- cutoffs: role 50% (the clear lead back); creation at the median of the qualifying backs.

The checks, in order (each a column; together they set a confidence)
1. Confirm creation: NGS percent of rushes over expected where NGS lists him, else PFR yards after contact
   per carry. Above or below the qualifying backs' median, the same side as his creation or not; a
   disagreement lowers confidence.
2. Adjust for the line: no feed has run block win rate, so the team's Next Gen Stats expected yards per
   carry stands in (frozen at the handoff, the back's vision not in it). A bad line (0.10+ below league)
   strengthens a buy and softens a sell; a good line (0.10+ above) the opposite.
3. Compare teammates: yards before contact per carry and broken tackles per touch against his team's other
   backs with 10+ touches. A backup (role under 50%) who beats them on both is the strongest buy; a starter
   who loses both is the strongest sell.
4. Why the role is what it is: a current-backfield teammate on the latest week's injury report (or who
   missed the team's latest game) is named with his status; the report gives a weekly status, not a return date.

Weeks: role uses every week of play-by-play; creation and the PFR checks use the weeks PFR has posted for
every game. A back is a running back by his latest weekly roster listing (fullbacks out); PFR and snap ids
map to gsis ids through the rosters, and a back whose PFR carries miss his play-by-play carries by more than
2 is left out and named. Carries leave out quarterback scrambles and kneels."""

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
AGE = {"max_age_s": F.CURRENT_SEASON_MAX_AGE_S}


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
    core = med[med >= CORE_BACK].reset_index()
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


def creation(d: dict) -> tuple[pd.DataFrame, list]:
    rbs, pw = d["rbs"], d["pfr_weeks"]
    car = d["car"][d["car"]["week"].isin(pw) & d["car"]["rusher_player_id"].isin(rbs)]
    tgt = d["tgt"][d["tgt"]["week"].isin(pw) & d["tgt"]["receiver_player_id"].isin(rbs)]
    c = pd.DataFrame({"carries": car.groupby("rusher_player_id").size(),
                      "receptions": tgt.groupby("receiver_player_id")["complete_pass"].apply(lambda x: int(flag(x).sum()))}).fillna(0)
    r, q = d["rush"].groupby("gsis_id"), d["rec"].groupby("gsis_id")
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
    return {gid: f"{r['report_status']} wk {wk} ({r['report_primary_injury']})" for gid, r in cur.set_index("gsis_id").iterrows()}


def build() -> tuple[pd.DataFrame, dict]:
    d = load(SEASON)
    b, meta = role(d)
    c, left = creation(d)
    r = b.join(c[["touches", "bt", "mtf", "ybc", "yac", "pfr_carries"]], how="inner")
    q = r[r["touches"] >= MIN_TOUCHES].copy()
    mtf_mid = float(q["mtf"].median())
    q["action"] = [ACTIONS[(x >= ROLE_CUT, y >= mtf_mid)] for x, y in zip(q["role"], q["mtf"])]

    # check 1: NGS percent of rushes over expected where listed, else yards after contact per carry
    ngs_rows = rg.load(SEASON)
    ngs = ngs_rows.set_index("player_gsis_id")
    q["pct_over_exp"] = ngs["rush_pct_over_expected"].reindex(q.index)
    q["check_src"] = q["pct_over_exp"].notna().map({True: "% rushes over expected", False: "yards after contact"})
    poe_mid, yac_mid = float(q["pct_over_exp"].median()), float(q["yac"].median())
    side = [(p >= poe_mid) if pd.notna(p) else (y >= yac_mid) for p, y in zip(q["pct_over_exp"], q["yac"])]
    q["check1_agrees"] = [bool(s == (m >= mtf_mid)) for s, m in zip(side, q["mtf"])]

    # check 2: the line (NGS team expected yards per carry vs league; run block win rate is not in any feed)
    tb, lg_mid, _ = rg.backs(ngs_rows)
    tt = rg.teams(tb, lg_mid)
    q["team_exp_ypc"] = q["team"].map(tt["exp_ypc"])
    if q["team_exp_ypc"].isna().any():
        raise ValueError(f"teams with no NGS expected yards: {sorted(q.loc[q['team_exp_ypc'].isna(), 'team'])}")
    q["block_vs_league"] = q["team_exp_ypc"] - lg_mid
    q["line"] = ["good" if v >= LINE_BAND else "bad" if v <= -LINE_BAND else "average" for v in q["block_vs_league"]]

    # check 3: teammates (10+ touches) on yards before contact and broken tackles per touch
    pool = r[r["touches"] >= MIN_MATE_TOUCHES]
    res, txt = [], []
    for gid, row in q.iterrows():
        mates = pool[(pool["team"] == row["team"]) & (pool.index != gid)]
        if mates.empty:
            res.append("")
            txt.append("")
            continue
        my = mates["ybc"].dropna()                     # a teammate with catches but no carries has no before-contact rate
        better = bool((row["ybc"] > my).all() and (row["mtf"] > mates["mtf"]).all())
        worse = bool((row["ybc"] < my).all() and (row["mtf"] < mates["mtf"]).all())
        res.append("wins both" if better else "loses both" if worse else "split")
        txt.append(", ".join(f"{m} ({y:.2f} before contact, {100 * t:.1f} BT/100)" for m, y, t in
                             zip(mates["name"], mates["ybc"], mates["mtf"])))
    q["check3"], q["teammates"] = res, txt

    # check 4: is the role propped up by a current-backfield teammate's absence?
    status = latest_status(d)
    team_last = d["played"].groupby("team")["week"].max()          # the latest week with snap counts posted
    seen = set(zip(d["played"]["gsis_id"], d["played"]["week"]))
    flags = []
    for gid, row in q.iterrows():
        notes = []
        for m in meta["current"].get(row["team"], []):
            if m == gid:
                continue
            missed = (m, team_last.get(row["team"])) not in seen
            if missed or m in status:
                notes.append(f"{d['names'].get(m, m)}: {status.get(m, 'missed the latest game')}")
        flags.append("; ".join(notes))
    q["check4"] = flags
    q["own_status"] = [status.get(i, "") for i in q.index]

    # confidence: medium to start; check 1 disagreement lowers it; checks 2-3 move buys and sells by the spec;
    # a teammate on the report lowers it until his return is known
    conf = []
    for row in q.itertuples():
        s = 0 if row.check1_agrees else -1
        if row.action == "Buy low":
            s += {"bad": 1, "good": -1}.get(row.line, 0) + (1 if row.check3 == "wins both" else 0)
        elif row.action == "Sell high":
            s += {"bad": -1, "good": 1}.get(row.line, 0) + (1 if row.check3 == "loses both" else 0)
        if row.check4:
            s -= 1
        conf.append("high" if s >= 1 else "low" if s <= -1 else "medium")
    q["confidence"] = conf
    lines = {"role_cut": ROLE_CUT, "mtf_median": mtf_mid, "poe_median": poe_mid, "yac_median": yac_mid,
             "league_exp_ypc": float(lg_mid)}
    notes = {"role weeks": sorted(set(d["weeks"].values())), "creation weeks (PFR in full)": d["pfr_weeks"],
             "games left out of role (a current-backfield teammate did not play)": meta["left_out"],
             "backs left out (PFR carries miss the plays)": left, "qualifying backs": len(q)}
    return q, {"lines": lines, "notes": notes}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=ROOT / "experiments" / "out" / "role_creation_2x2_2026")
    a = ap.parse_args(argv)
    q, meta = build()
    keep = ["name", "team", "games", "snap", "carry_share", "i10", "t_i10", "i10_share", "role", "touches", "bt", "mtf", "ybc",
            "yac", "pct_over_exp", "check_src", "check1_agrees", "team_exp_ypc", "block_vs_league", "line", "check3", "teammates",
            "check4", "own_status", "action", "confidence"]
    rows = q[keep].sort_values("role", ascending=False).reset_index(names="gsis_id")
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.with_suffix(".json").write_text(json.dumps({**meta, "rows": rows.round(4).to_dict("records")}, indent=1, default=str),
                                          encoding="utf-8")
    L, N = meta["lines"], meta["notes"]
    out = [f"# Role vs creation, {SEASON} (role weeks {N['role weeks'][0]}-{N['role weeks'][-1]}; creation weeks "
           f"{N['creation weeks (PFR in full)'][0]}-{N['creation weeks (PFR in full)'][-1]})", "",
           f"{N['qualifying backs']} backs with {MIN_TOUCHES}+ touches. Role = average of snap share (for route participation) and "
           f"inside-10 carry share, games with the current backfield only, last {RECENT_GAMES} games x{RECENT_WEIGHT:g}; cut at "
           f"{ROLE_CUT:.0f}%. Creation = broken tackles per touch (PFR); cut at the median {100 * L['mtf_median']:.1f} per 100 touches. "
           "Not backtested.", "",
           "| Back | Team | Role | BT/100 | Action | Check 1 | Line | Teammates | Teammate out | Confidence |",
           "|---|---|---|---|---|---|---|---|---|---|"]
    for x in rows.to_dict("records"):
        c1 = ("agrees" if x["check1_agrees"] else "DISAGREES") + f" ({x['check_src']})"
        out.append(f"| {x['name']} | {x['team']} | {x['role']:.0f} | {100 * x['mtf']:.1f} | {x['action']} | {c1} | {x['line']} | "
                   f"{x['check3'] or '-'} | {x['check4'] or '-'} | {x['confidence']} |")
    out += ["", "Notes: " + "; ".join(f"{k}: {v}" for k, v in N.items() if k != "qualifying backs")]
    a.out.with_suffix(".md").write_text("\n".join(out) + "\n", encoding="utf-8")
    print("\n".join(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
