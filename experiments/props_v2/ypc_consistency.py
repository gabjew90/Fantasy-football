"""Line-consistency archive check: does Sleeper's implied yards per catch carry anything
beyond the player's own history? (docs/plans/2026-10-09-props-v2-hypotheses.md, "H1 archive
check"; the reading rule below is also written there under "Line consistency (the earlier
H1) -- the archive check, built".)

    python experiments/props_v2/ypc_consistency.py [--season 2026] [--out experiments/out]

For every player-week in the props record with both a receptions and a receiving-yards
line, Sleeper's implied yards per catch is S = yards line / receptions line. It is set
beside:
  T  the player's trailing yards per catch: last season's regular season plus this season
     before the week (nflverse weekly player stats: the file and refresh age props/settle.py
     grades from);
  T0 the same, this season only (blank before his first catch);
  E  the engine's ratio at the same capture: its receiving-yards mean / receptions mean.

Main line: each player-week's earliest surviving decision capture in which ONE engine priced
BOTH markets (so S and E come from one capture and one engine). "Surviving": a same-engine
re-run replaces rows with the same key and restamps them (props/persist.py), so this is not
always the very first capture. When a market has more than one line there, the one whose no-vig
Over is nearest 50%. A line is a median only when its price is even, so every number is
also shown on the subset where both markets' no-vig Over is within 0.45-0.55.

Population (set in code review, before any run): receptions line 3.5 or more, so the
yards median is not dragged down by zero-catch games and S approximates a per-catch rate;
and 20+ catches behind T, so the history is not noise.

ID join (gsis_resolver): membership is the team's nflverse weekly roster as of the capture
week (latest roster week up to it; never a later week; CUT / RET / EXE / TRD rows excluded).
Primary: core.ids -- Sleeper's player table -> NameIndex candidates -> gsis from the ID map,
Sleeper's own field and the roster's sleeper_id (a disagreement among them that leaves two
members is a drop, never a pick) -> exactly one candidate on that roster; else the unique
name on that roster. Fallback, when Sleeper's table cannot be fetched (some sandboxes block
api.sleeper.app): the unique name on that roster. The report names the path. The roster
decides who is kept, so a stale roster withholds the verdict; a stale Sleeper table or ID
map does not (they only name candidates). Every row dropped is
counted by reason. A player-week whose team has no row in the weekly stats yet stays in the
Derived test (it needs no outcome) and is left out of the settled comparison, counted. A
week after the last COMPLETE stats week plus one is dropped (T would miss games). E comes
from whichever engine made the capture; the engine releases behind it are listed. The
record is read from this checkout: pull first (the newest capture time is printed).

Reading rule, fixed before the first run:
- **Derived (stop):** S is mostly a function of the history. R^2 of S on T is 0.80 or more,
  or the median |S - T| / T is under 5%.
- **Surprise (build H1):** S explains realized yards per catch (settled weeks, catches > 0)
  better than both T and E: lower mean absolute error, with a 95% interval from resampling
  games excluding zero against each.
- Anything else: not derived, but no evidence its disagreements carry information. Stop
  unless the user decides otherwise.
- **No verdict** under 30 player-weeks (or under 30 settled ones, unless Derived fired), or
  when an input is stale or failed (DATA MISSING).
- **The verdict on all main lines decides.** The near-even subset is informational.
- Intervals: 20,000 game-resampling draws under each of four seeds (the four-seed rule,
  DECISIONS #202); a difference is "better" or "worse" only when all four agree. (Added after
  the code review's scratch run showed one interval's label flipping with the seed; the
  verdict did not depend on that interval.)
"""
# expires: 2026-11-08
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from core import fetch as F  # noqa: E402
from core.ids import NameIndex, load_id_map, normalize_name, sleeper_gsis  # noqa: E402
from core.manifest import Manifest  # noqa: E402

REC, YDS = "player_receptions", "player_reception_yds"
EVEN = (0.45, 0.55)
MIN_REC_LINE = 3.5
MIN_HIST_CATCHES = 20
MIN_ROWS = 30
POSITIONS = {"WR", "TE", "RB", "QB"}
STATS_COLS = ["player_id", "season", "week", "season_type", "game_id", "team", "receptions", "receiving_yards"]
STATS_MAX_AGE_S = 3 * 3600          # props/settle.py's STATS_MAX_AGE_S


def main_lines(season: int) -> tuple[pd.DataFrame, int, str]:
    """One row per (week, team, player): both markets' lines, no-vig Overs and engine means
    from one capture, plus the slot and event. Also returns how many player-weeks had both
    markets but never in one capture by one engine (dropped), and the newest row of any
snapshot or market in the record (the pull check)."""
    files = sorted((ROOT / "props" / "record" / "predictions" / str(season)).glob("wk*.jsonl"))
    if not files:
        raise SystemExit(f"no props record for {season} (props/record/predictions/{season}/wk*.jsonl)")
    rows = []
    for f in files:
        with open(f, encoding="utf-8") as fh:
            rows += [json.loads(line) for line in fh if line.strip()]
    d = pd.DataFrame(rows)
    newest = str(d["logged_at_utc"].max())      # every snapshot and market: the pull check
    d = d[(d["snapshot_type"] == "decision") & d["market"].isin([REC, YDS]) & (d["book"] == "sleeper")]
    if d.empty:
        raise SystemExit(f"no Sleeper decision rows for receptions / receiving yards in {season}")
    # no-vig Over at each line: the Over row's p_novig, else 1 - the Under row's
    d["p_over"] = np.where(d["side"] == "Over", d["p_novig"], 1 - d["p_novig"])
    pw = ["week", "team", "player"]
    any_both = d.groupby(pw)["market"].nunique()
    # one capture AND one engine priced both markets: never mix captures or average two
    # engines' means (props/persist.py keys rows on engine_hash for this reason)
    both = (d.groupby(pw + ["logged_at_utc", "engine_hash"])["market"].nunique()
            .rename("n_mkt").reset_index())
    both = both[both["n_mkt"] == 2].sort_values(pw + ["logged_at_utc", "engine_hash"])
    first = both.drop_duplicates(pw)[pw + ["logged_at_utc", "engine_hash"]]
    n_split = int((any_both == 2).sum()) - len(first)
    d = d.merge(first, on=pw + ["logged_at_utc", "engine_hash"])
    key = pw + ["market"]
    d = (d.groupby(key + ["line"], as_index=False)
         .agg(p_over=("p_over", "mean"), model_mean=("model_mean", "first"),
              event_id=("event_id", "first"), slot=("slot", "first"), game=("game", "first"),
              engine_tag=("engine_tag", "first"), logged_at_utc=("logged_at_utc", "first")))
    d["dist"] = (d["p_over"] - 0.5).abs()
    d = d.sort_values(key + ["dist", "line"]).drop_duplicates(key)
    w = d.pivot_table(index=pw, columns="market", values=["line", "p_over", "model_mean"],
                      aggfunc="first")
    w.columns = [f"{a}_{'rec' if b == REC else 'yds'}" for a, b in w.columns]
    for c in ("line_rec", "line_yds", "p_over_rec", "p_over_yds", "model_mean_rec", "model_mean_yds"):
        if c not in w.columns:
            w[c] = np.nan
    meta = d.drop_duplicates(pw).set_index(pw)[["event_id", "slot", "game", "engine_tag", "logged_at_utc"]]
    return w.join(meta).dropna(subset=["line_rec", "line_yds"]).reset_index(), n_split, newest


SLEEPER_INPUTS = {"sleeper players", "id map"}     # only name candidates: stale never withholds
GONE = {"CUT", "RET", "EXE", "TRD"}                 # roster rows that are not the team's player


def gsis_resolver(manifest, season: int):
    """(name, slot, team, week) -> gsis_id, and the path used (rules: module docstring)."""
    ros = pd.read_csv(F.nflverse("rosters_weekly", season, manifest=manifest), low_memory=False,
                      usecols=["week", "team", "full_name", "gsis_id", "sleeper_id", "status"])
    ros = ros[ros["gsis_id"].notna() & ~ros["status"].isin(GONE)]
    ros = ros.assign(nk=ros["full_name"].astype(str).map(normalize_name))
    rost: dict[str, dict[int, tuple[set, dict]]] = {}
    for (team, wk), g in ros.groupby(["team", "week"]):
        names = g.groupby("nk")["gsis_id"].agg(lambda x: x.iloc[0] if x.nunique() == 1 else None)
        rost.setdefault(team, {})[int(wk)] = (set(g["gsis_id"]), names.dropna().to_dict())
    roster_sid = {}
    for x, gid in zip(ros["sleeper_id"], ros["gsis_id"]):
        try:
            roster_sid[str(int(float(x)))] = gid
        except (TypeError, ValueError):
            pass

    def roster_at(team: str, week: int):
        """(members, unique name -> gsis) as of the capture week, or None: never a later week."""
        upto = [k for k in rost.get(team, {}) if k <= int(week)]
        return rost[team][max(upto)] if upto else None

    def by_name(name, team, week):
        r = roster_at(team, week)
        return r[1].get(normalize_name(str(name))) if r else None

    try:
        players = json.loads(Path(F.sleeper_players(manifest=manifest)).read_text(encoding="utf-8"))
    except Exception as exc:
        # only a failed fetch falls back; a code or schema error raises
        if not any(e["status"] == "failed" and e["name"] == "sleeper players" for e in manifest.entries):
            raise
        why = f"{type(exc).__name__}: {str(exc)[:120]}"
        return (lambda name, slot, team, week: by_name(name, team, week),
                f"FALLBACK: the team's weekly roster by name (Sleeper's table failed: {why})")

    try:
        id_map = load_id_map(F.DEFAULT_CACHE, manifest=manifest)
    except Exception:
        if not any(e["status"] == "failed" and e["name"] == "id map" for e in manifest.entries):
            raise
        id_map = None
    idx = NameIndex(players)
    s2g, _ = sleeper_gsis(id_map, players)

    def resolve(name, slot, team, week):
        r = roster_at(team, week)
        if r is None:
            return None
        pos = "".join(c for c in str(slot or "") if c.isalpha())
        for p_ in ((pos, None) if pos in POSITIONS else (None,)):
            hit = set()
            for sid in idx.candidates(str(name), p_):
                hit |= {s2g.get(sid), roster_sid.get(sid)} & r[0]
            if len(hit) == 1:
                return hit.pop()
            if len(hit) > 1:
                return None         # the sources disagree: drop, never pick
        return by_name(name, team, week)
    return resolve, ("core.ids (Sleeper player table -> sleeper_gsis" + ("" if id_map is not None else
                     "; ID map unavailable") + "), membership from the weekly roster as of the capture week")


def catches(season: int, manifest, current: bool) -> pd.DataFrame:
    """Receptions and receiving yards per (week, gsis_id), regular season, from the weekly
    player stats props/settle.py grades from. attrs: the (week, team) pairs present and the
number of games per week."""
    kw = {"max_age_s": STATS_MAX_AGE_S} if current else {}     # a finished season keeps core's age
    p = pd.read_csv(F.nflverse("player_stats_week", season, manifest=manifest, **kw),
                    usecols=STATS_COLS, low_memory=False)
    p = p[(p["season_type"] == "REG") & p["player_id"].notna()]
    out = (p.groupby(["week", "player_id"])
           .agg(rec=("receptions", "sum"), yds=("receiving_yards", "sum"))
           .reset_index().rename(columns={"player_id": "gsis_id"}))
    out.attrs["team_weeks"] = set(zip(p["week"].astype(int), p["team"]))
    out.attrs["games_by_week"] = p.groupby("week")["game_id"].nunique().to_dict()
    return out


def history(w: pd.DataFrame, prev: pd.DataFrame, cur: pd.DataFrame) -> pd.DataFrame:
    """Adds hist_rec/hist_yds (last season + this season before the week), cur_rec/cur_yds
    (this season before the week) and a_rec/a_yds (the week itself)."""
    cur = cur.sort_values(["gsis_id", "week"]).copy()
    cur[["cum_rec", "cum_yds"]] = cur.groupby("gsis_id")[["rec", "yds"]].cumsum()
    left = w.reset_index().rename(columns={"index": "_row"}).sort_values("week")
    before = pd.merge_asof(left, cur[["week", "gsis_id", "cum_rec", "cum_yds"]].sort_values("week"),
                           on="week", by="gsis_id", allow_exact_matches=False)
    before = before.set_index("_row").sort_index()
    out = w.copy()
    out["cur_rec"] = before["cum_rec"].fillna(0.0)
    out["cur_yds"] = before["cum_yds"].fillna(0.0)
    p = prev.groupby("gsis_id")[["rec", "yds"]].sum()
    out["hist_rec"] = out["cur_rec"] + out["gsis_id"].map(p["rec"]).fillna(0.0)
    out["hist_yds"] = out["cur_yds"] + out["gsis_id"].map(p["yds"]).fillna(0.0)
    act = cur.set_index(["week", "gsis_id"])[["rec", "yds"]]
    a = act.reindex(pd.MultiIndex.from_arrays([out["week"], out["gsis_id"]]))
    out["a_rec"], out["a_yds"] = a["rec"].to_numpy(), a["yds"].to_numpy()
    return out


SEEDS = (7, 11, 42, 2026)


def boot_mae_diff(df: pd.DataFrame, a: str, b: str, reps=20000):
    """Mean |a - actual| minus mean |b - actual|; the 95% interval from resampling games,
    under each of four seeds. Returns (mean, lowest lower bound, highest upper bound): an
    interval excludes zero only when all four seeds' intervals do."""
    e = df.assign(d=(df[a] - df["ypc_act"]).abs() - (df[b] - df["ypc_act"]).abs())
    g = e.groupby("event_id")["d"].agg(["sum", "size"])
    s, n = g["sum"].to_numpy(), g["size"].to_numpy()
    los, his = [], []
    for seed in SEEDS:
        idx = np.random.default_rng(seed).integers(0, len(s), size=(reps, len(s)))
        lo, hi = np.percentile(s[idx].sum(1) / n[idx].sum(1), [2.5, 97.5])
        los.append(lo)
        his.append(hi)
    return s.sum() / n.sum(), min(los), max(his)


def r2(y, x):
    ok = np.isfinite(y) & np.isfinite(x)
    if ok.sum() < 3:
        return float("nan")
    return float(np.corrcoef(y[ok], x[ok])[0, 1] ** 2)


def summarize(df: pd.DataFrame, label: str) -> tuple[list[str], dict]:
    """The report section and the numbers the verdict reads."""
    st = {"n": len(df), "boot": {}, "n_settled": 0}
    L = [f"### {label} ({len(df)} player-weeks)", ""]
    if len(df) < MIN_ROWS:
        return L + [f"Under {MIN_ROWS} player-weeks; nothing computed.", ""], st
    S, T, T0, E = (df[c].to_numpy(float) for c in ("S", "T", "T0", "E"))
    st["r2_ST"], st["med_rel_ST"] = r2(S, T), float(np.median(np.abs(S - T) / T))
    L += ["| | mean | sd |", "|---|---|---|"]
    for name, v in (("S Sleeper", S), ("T trailing", T), ("T0 this season", T0), ("E engine", E)):
        L.append(f"| {name} | {np.nanmean(v):.2f} | {np.nanstd(v):.2f} |")
    L += ["", f"- R^2 of S on T: {st['r2_ST']:.3f}; on T0: {r2(S, T0):.3f}; on E: {r2(S, E):.3f}; "
              f"E on T: {r2(E, T):.3f}.",
          f"- Median |S - T| / T: {st['med_rel_ST']:.1%}; median |S - E| / E: "
          f"{np.median(np.abs(S - E) / E):.1%}.", ""]
    s = df.dropna(subset=["ypc_act"])
    st["n_settled"] = len(s)
    pl = df[df["played"]]
    L += [f"Of {len(df)}: {int((~df['played']).sum())} in games not played or not in the stats yet; of the "
          f"{len(pl)} played, {int(pl['a_rec'].isna().sum())} have no stats row (inactive) and "
          f"{int((pl['a_rec'] == 0).sum())} had no catch; {len(s)} settled.", ""]
    if len(s) < MIN_ROWS:
        return L + [f"Settled player-weeks with a catch: {len(s)} (under {MIN_ROWS}; no error comparison).", ""], st
    L += [f"Settled player-weeks with a catch: {len(s)}, {s['event_id'].nunique()} games. "
          "Mean absolute error against realized yards per catch:", "", "| | MAE |", "|---|---|"]
    for c in ("S", "T", "E"):
        L.append(f"| {c} | {(s[c] - s['ypc_act']).abs().mean():.2f} |")
    L.append("")
    for other in ("T", "E"):
        m, lo, hi = st["boot"][other] = boot_mae_diff(s, "S", other)
        L.append(f"- S minus {other}: {m:+.4f} (widest of four seeds' 95% intervals: {lo:+.4f}, {hi:+.4f}) "
                 f"({'S better' if hi < 0 else 'S worse' if lo > 0 else 'not established'})")
    return L + [""], st


def verdict(st: dict, stale: bool, decides: bool = True) -> str:
    if stale:
        return "NO VERDICT: DATA MISSING (an input is stale or failed; see above)."
    if st["n"] < MIN_ROWS:
        return f"NO VERDICT: INSUFFICIENT DATA (under {MIN_ROWS} player-weeks)."
    if st["r2_ST"] >= 0.80 or st["med_rel_ST"] < 0.05:
        return "DERIVED: Sleeper's ratio tracks the player's history; the check would rarely fire. Stop."
    if st["n_settled"] < MIN_ROWS:
        return f"NO VERDICT: INSUFFICIENT SETTLED DATA (under {MIN_ROWS} settled player-weeks; Derived did not fire)."
    if all(st["boot"][o][2] < 0 for o in ("T", "E")):
        return ("SURPRISE: Sleeper's ratio beats both history and the engine on realized yards per catch."
                + (" Build H1." if decides else " (Informational: does not decide.)"))
    return "NEITHER: not derived, but no evidence its disagreements carry information. Stop."


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--season", type=int, default=2026)
    ap.add_argument("--out", default=str(ROOT / "experiments" / "out"))
    a = ap.parse_args(argv)
    s = a.season
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    man = Manifest("ypc_consistency")
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    for f in ("ypc_consistency.md", "ypc_consistency.csv", "ypc_consistency.manifest.json"):
        (out / f).unlink(missing_ok=True)     # never leave an earlier run's verdict behind

    w, n_split, newest = main_lines(s)
    n0 = len(w)
    try:
        resolve, id_path = gsis_resolver(man, s)
        prev = catches(s - 1, man, current=(s - 1) >= F.current_season())
        cur = catches(s, man, current=s >= F.current_season())
        sched = pd.read_csv(F.schedule(manifest=man), low_memory=False,
                            usecols=["season", "game_type", "week", "gameday", "result"])
    except Exception as exc:
        failed = [e for e in man.entries if e["status"] == "failed" and e["name"] not in SLEEPER_INPUTS]
        if not failed:      # a code or schema error, not missing data
            raise
        # DATA MISSING: a failed input with no copy in hand
        man.write(out / "ypc_consistency.manifest.json")
        msg = (f"# Line-consistency archive check, {s}\n\n**DATA MISSING:** {exc}\n\n"
               f"{man.summary_line()}\n\nNO VERDICT.\n")
        (out / "ypc_consistency.md").write_text(msg, encoding="utf-8")
        print(msg)
        return 1
    w["gsis_id"] = [resolve(p, sl, t, wk) for p, sl, t, wk in zip(w["player"], w["slot"], w["team"], w["week"])]
    unmatched = sorted(w.loc[w["gsis_id"].isna(), "player"].unique())
    w = w.dropna(subset=["gsis_id"])
    n1 = len(w)

    # Coverage. A row after the last complete week plus one is dropped (T would miss games).
    # A row whose team has no stats row that week has no outcome yet; it stays in the
    # Derived test. A week is complete when the stats hold every game with a result AND the week is over:
    # every game has a result, or its last game day is 2+ days past (so a cancelled game,
    # which never gets a result, cannot keep the week open for good).
    sc = sched[(sched["season"] == s) & (sched["game_type"] == "REG")].copy()
    sc["gameday"] = pd.to_datetime(sc["gameday"])
    wkt = sc.groupby("week").agg(n_all=("result", "size"), n_res=("result", "count"), last_day=("gameday", "max"))
    over = (wkt["n_res"] == wkt["n_all"]) | (wkt["last_day"] <= pd.Timestamp.now().normalize() - pd.Timedelta(days=2))
    gbw = cur.attrs["games_by_week"]
    complete = [int(k) for k, r in wkt.iterrows() if over[k] and gbw.get(k, 0) >= r["n_res"] and r["n_res"] > 0]
    last = 0
    while last + 1 in complete:
        last += 1
    far = w["week"] > last + 1
    n_far, far_weeks = int(far.sum()), sorted(int(x) for x in w.loc[far, "week"].unique())
    w = w[~far]
    tw = cur.attrs["team_weeks"]
    played = np.array([(int(wk), t) in tw for wk, t in zip(w["week"], w["team"])], dtype=bool)
    w = history(w, prev, cur)
    w["T"] = w["hist_yds"] / w["hist_rec"].where(w["hist_rec"] > 0)
    w["T0"] = w["cur_yds"] / w["cur_rec"].where(w["cur_rec"] > 0)
    w["ypc_act"] = (w["a_yds"] / w["a_rec"].where(w["a_rec"] > 0)).where(played)
    w["played"] = played
    w["S"] = w["line_yds"] / w["line_rec"]
    w["E"] = w["model_mean_yds"] / w["model_mean_rec"].where(w["model_mean_rec"] > 0)

    keep_rec = w["line_rec"] >= MIN_REC_LINE
    keep_hist = w["hist_rec"] >= MIN_HIST_CATCHES
    finite = np.isfinite(w[["S", "E", "T"]]).all(axis=1) & (w["T"] > 0) & (w["E"] > 0)
    n_low, n_thin = int((~keep_rec).sum()), int((keep_rec & ~keep_hist).sum())
    n_bad = int((keep_rec & keep_hist & ~finite).sum())
    w = w[keep_rec & keep_hist & finite]
    even = w[w["p_over_rec"].between(*EVEN) & w["p_over_yds"].between(*EVEN)]

    # the Sleeper table and ID map serve only the ID join: a stale copy is still a fine join,
    # and a failed one is replaced by the fallback (named in the report). Every other stale
    # or failed input withholds the verdict.
    bad = [e for e in man.stale() if e["name"] not in SLEEPER_INPUTS]
    stale = bool(bad)
    tags = w["engine_tag"].fillna("untagged").value_counts()
    L = [f"# Line-consistency archive check: Sleeper's implied yards per catch, {s}", "",
         f"Record read from this checkout; its newest row is {newest} (pull first if that is older "
         f"than the latest props capture on main).", "", f"ID join: {id_path}.", "",
         f"Player-weeks with both lines in one capture: {n0} ({n_split} more had both markets only in "
         f"different captures, not used). Dropped: {n0 - n1} not resolved to an ID "
         f"({', '.join(unmatched) or 'none'}); {n_far} in weeks after the last complete stats week {last} "
         f"plus one ({far_weeks or 'none'}); {n_low} with a receptions line "
         f"under {MIN_REC_LINE}; {n_thin} with under {MIN_HIST_CATCHES} catches of history; {n_bad} "
         f"with a non-finite or non-positive ratio. Kept: {len(w)}, weeks "
         f"{sorted(int(x) for x in w['week'].unique())}; {int((~w['played']).sum())} of them in games "
         f"not played or not yet in the stats (Derived test only, no outcome).", "",
         "E comes from these engine releases (player-weeks): "
         + ", ".join(f"{k} {v}" for k, v in tags.items()) + ".", "", man.summary_line(), ""]
    if stale:
        L += ["**DATA MISSING:** " + "; ".join(f"{e['name']} {e['status']} {e['detail']}"
                                              for e in bad), ""]
    La, sa = summarize(w, "All main lines")
    Le, se = summarize(even, "Both lines near even (no-vig Over 0.45-0.55)")
    L += La + Le
    L += ["## Verdict (rule fixed in the module docstring before the run)", "",
          f"All main lines (decides): {verdict(sa, stale)}", "",
          f"Near-even subset (informational): {verdict(se, stale, decides=False)}", ""]

    (out / "ypc_consistency.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    w.to_csv(out / "ypc_consistency.csv", index=False, encoding="utf-8")
    man.write(out / "ypc_consistency.manifest.json")
    print("\n".join(L))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
