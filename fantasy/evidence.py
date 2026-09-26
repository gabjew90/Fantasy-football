"""The usage evidence table -- the start/sit and waiver frameworks' questions
1 and 2 (opportunity, and whether the role has changed beyond normal noise).

Per player and week, keyed by nflverse gsis id, from play-by-play and snap
counts (joined to gsis through the DynastyProcess pfr id, never by name):

  snap_pct       offensive snaps / team offensive snaps
  tgt_share      targets / team targets          (a target: a pass attempt with
                                                   a receiver, not a sack or a
                                                   two-point try)
  ay_share       air yards on targets / team air yards
  adot           air yards per target
  wopr           1.5 x tgt_share + 0.7 x ay_share
  carry_share    carries / team carries          (kneels and two-point tries out)
  i10_tgt, i10_car   targets and carries with the ball inside the opponent's 10
  two_min        targets + carries inside the last two minutes of a half

NOISE BANDS (noise_bands_v0). How much each metric moves week to week for a
player whose role has NOT changed: the standard deviation of a player-week
around his own season mean, for players with at least MIN_WEEKS weeks, by
position -- fitted on one season, checked for stability on the next. A shift
between a player's last two weeks and his earlier weeks is flagged as a role
change only when it exceeds two noise standard deviations of that difference:
    sd_diff = sd * sqrt(1/2 + 1/n_earlier)
which is what "judged against the normal week-to-week noise of that metric"
means in the user's framework. Output, not box score: fantasy points never
enter the flag.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from core import fetch as F
from core import ids as IDS
from core.manifest import Manifest

NAME = "noise_bands_v0"
ROOT = Path(__file__).resolve().parent.parent
RESOURCES = Path(__file__).resolve().parent / "resources"
METRICS = ("snap_pct", "tgt_share", "ay_share", "adot", "wopr", "carry_share", "i10_tgt", "i10_car", "two_min")
BAND_METRICS = ("snap_pct", "tgt_share", "ay_share", "wopr", "carry_share")
# The metrics that DEFINE each position's role -- the only ones a role-change
# flag is raised on, and the only ones the stability check judges. Chosen
# after the first fit (2026-09-24) failed on three bands that mean nothing for
# the position: TE carry share (~0.6% of carries; its SD moved 2.4x), QB target
# share, and RB air-yard share (dominated by negative-yard checkdowns). The
# report prints the excluded rows too.
ROLE_METRICS = {"QB": ("snap_pct", "carry_share"),
                "RB": ("snap_pct", "carry_share", "tgt_share", "wopr"),
                "WR": ("snap_pct", "tgt_share", "ay_share", "wopr"),
                "TE": ("snap_pct", "tgt_share", "ay_share", "wopr")}
MIN_WEEKS = 8
Z = 2.0                   # the fallback threshold only; each fitted band carries its CALIBRATED z
TARGET_FALSE_ALARM = 0.05
# Bands depend on the player's usage LEVEL: a 10%-share back's weeks move less
# in absolute terms than a 60% starter's, so one SD per position hid exactly
# the backup-to-starter jumps a waiver decision looks for (review 2026-09-24).
LEVEL_EDGES = {"snap_pct": (0.0, 0.5, 0.8, 1.01), "tgt_share": (0.0, 0.1, 0.2, 1.01),
               "ay_share": (0.0, 0.1, 0.25, 1.01), "wopr": (0.0, 0.25, 0.5, 10.0),
               "carry_share": (0.0, 0.15, 0.4, 1.01)}
MIN_LEVEL_N = 100
# A week under 60% of the level the player had ALREADY ESTABLISHED -- the
# median of his earlier weeks this season -- is marked "partial game": a dip,
# as an exit or a benching makes. Earlier weeks, not all other weeks, because
# a backup who takes over (25%, 30%, 85%, 90%) would otherwise have his first
# weeks read as exits and his real role change dismissed; the first week has
# no level to dip from and is never marked. 60% because a second-quarter exit
# lands near half a game: DJ Moore, 2026 week 2, 31% of snaps after 77% in
# week 1 -- the old rule (40% of a median that included that week) missed it.
PARTIAL_SNAP = 0.6
PBP_COLS = ["season", "week", "season_type", "posteam", "pass_attempt", "rush_attempt", "receiver_player_id",
            "rusher_player_id", "air_yards", "yardline_100", "half_seconds_remaining", "qb_kneel", "sack",
            "two_point_attempt"]


# ------------------------------------------------------------------ build

def usage_from_pbp(pbp: pd.DataFrame) -> pd.DataFrame:
    """Player-week usage from play-by-play: one row per (season, week, team, gsis)."""
    p = pbp[(pbp["season_type"] == "REG") & (pbp["two_point_attempt"].fillna(0) != 1)].copy()
    tg = p[(p["pass_attempt"] == 1) & (p["sack"].fillna(0) != 1) & p["receiver_player_id"].notna()].copy()
    ru = p[(p["rush_attempt"] == 1) & (p["qb_kneel"].fillna(0) != 1) & p["rusher_player_id"].notna()].copy()
    tg["ay"] = pd.to_numeric(tg["air_yards"], errors="coerce").fillna(0.0)
    # shares use air yards floored at zero: a screen-heavy week can leave the team
    # total near zero, and a raw share then runs past 100% or below zero (review)
    tg["ay_pos"] = tg["ay"].clip(lower=0.0)
    tg["i10"] = (tg["yardline_100"] <= 10).astype(int)
    ru["i10"] = (ru["yardline_100"] <= 10).astype(int)
    tg["tm"] = (tg["half_seconds_remaining"] <= 120).astype(int)
    ru["tm"] = (ru["half_seconds_remaining"] <= 120).astype(int)
    key = ["season", "week", "posteam"]
    team_t = tg.groupby(key).agg(team_tgt=("ay", "size"), team_ay=("ay_pos", "sum")).reset_index()
    team_r = ru.groupby(key).agg(team_car=("i10", "size")).reset_index()
    pt = tg.groupby(key + ["receiver_player_id"]).agg(targets=("ay", "size"), air_yards=("ay", "sum"),
                                                       ay_pos=("ay_pos", "sum"), i10_tgt=("i10", "sum"),
                                                       tm_t=("tm", "sum")).reset_index()
    pt = pt.rename(columns={"receiver_player_id": "gsis_id"})
    pr = ru.groupby(key + ["rusher_player_id"]).agg(carries=("i10", "size"), i10_car=("i10", "sum"),
                                                     tm_r=("tm", "sum")).reset_index()
    pr = pr.rename(columns={"rusher_player_id": "gsis_id"})
    u = pt.merge(pr, on=key + ["gsis_id"], how="outer").fillna(0)
    u = u.merge(team_t, on=key, how="left").merge(team_r, on=key, how="left").fillna(0)
    u["tgt_share"] = np.where(u["team_tgt"] > 0, u["targets"] / u["team_tgt"], 0.0)
    u["ay_share"] = np.where(u["team_ay"] > 0, u["ay_pos"] / u["team_ay"], 0.0)
    u["adot"] = np.where(u["targets"] > 0, u["air_yards"] / u["targets"].replace(0, np.nan), np.nan)
    u["wopr"] = 1.5 * u["tgt_share"] + 0.7 * u["ay_share"]
    u["carry_share"] = np.where(u["team_car"] > 0, u["carries"] / u["team_car"], 0.0)
    u["two_min"] = u["tm_t"] + u["tm_r"]
    u = u.rename(columns={"posteam": "team"})
    return u.drop(columns=["tm_t", "tm_r", "ay_pos"])


def with_snaps(u: pd.DataFrame, snaps: pd.DataFrame, pfr_to_gsis: dict) -> pd.DataFrame:
    s = snaps[snaps.get("game_type", "REG") == "REG"].copy() if "game_type" in snaps else snaps.copy()
    s["gsis_id"] = s["pfr_player_id"].map(pfr_to_gsis)
    s = s[s["gsis_id"].notna() & (s["offense_snaps"] > 0)]
    s = s.rename(columns={"offense_pct": "snap_pct"})[["season", "week", "team", "gsis_id", "snap_pct", "offense_snaps"]]
    # a player can have snaps and no touch (a blocking TE): keep him
    out = u.merge(s, on=["season", "week", "team", "gsis_id"], how="outer")
    for c in ("targets", "carries", "tgt_share", "ay_share", "wopr", "carry_share", "i10_tgt", "i10_car", "two_min",
              "air_yards"):
        out[c] = out[c].fillna(0.0)
    return out


def pfr_map(manifest=None) -> dict:
    idm = IDS.load_id_map(F.DEFAULT_CACHE, manifest=manifest)
    rows = idm.select(["pfr_id", "gsis_id"]).drop_nulls().iter_rows()
    return {p: g for p, g in rows}


def season_usage(season: int, *, manifest: Manifest | None = None, pfr: dict | None = None) -> pd.DataFrame:
    pbp = pd.read_csv(F.nflverse("pbp", season, manifest=manifest), usecols=PBP_COLS, low_memory=False)
    snaps = pd.read_csv(F.nflverse("snaps", season, manifest=manifest), low_memory=False)
    return with_snaps(usage_from_pbp(pbp), snaps, pfr if pfr is not None else pfr_map(manifest))


# ------------------------------------------------------------ noise bands

def _robust_sd(resid: pd.Series) -> float:
    """1.4826 x the median absolute deviation: the SD of the noise, not
    inflated by the minority of players whose role really changed mid-season
    (review 2026-09-24). Never below half the classical SD, so a metric with
    many identical weeks cannot collapse the band to zero."""
    r = resid.dropna()
    if len(r) < 3:
        return float("nan")
    mad = 1.4826 * float((r - r.median()).abs().median())
    return max(mad, 0.5 * float(r.std(ddof=1)))


def fit_bands(usage: pd.DataFrame, positions: dict) -> dict:
    """{pos: {metric: {sd, by_level, players, player_weeks}}} -- week-to-week
    spread around a player's own season mean, players with >= MIN_WEEKS
    weeks, robust to genuine role changes and split by the player's usage
    level. `positions`: gsis -> pos."""
    u = usage.copy()
    u["pos"] = u["gsis_id"].map(positions)
    out = {}
    for pos in ("QB", "RB", "WR", "TE"):
        d = u[u["pos"] == pos]
        counts = d.groupby("gsis_id")["week"].nunique()
        d = d[d["gsis_id"].isin(counts[counts >= MIN_WEEKS].index)]
        if d.empty:
            continue
        out[pos] = {}
        for m in BAND_METRICS:
            if m not in d:
                continue
            x = d[["gsis_id", m]].dropna().copy()
            x["level"] = x.groupby("gsis_id")[m].transform("mean")
            x["resid"] = x[m] - x["level"]
            overall = _robust_sd(x["resid"])
            edges = LEVEL_EDGES.get(m)
            levels = []
            if edges:
                for lo, hi in zip(edges, edges[1:]):
                    b = x[(x["level"] >= lo) & (x["level"] < hi)]
                    if len(b) >= MIN_LEVEL_N:
                        levels.append({"lo": lo, "hi": hi, "sd": round(_robust_sd(b["resid"]), 4), "n": int(len(b))})
            out[pos][m] = {"sd": round(overall, 4), "by_level": levels, "players": int(x["gsis_id"].nunique()),
                           "player_weeks": int(len(x))}
    return out


def band_sd(band: dict | float | None, level: float | None) -> float | None:
    """The noise SD for a player at usage `level`: his level's band where one
    was fitted, else the position's overall band."""
    if band is None or isinstance(band, (int, float)):
        return band
    if level is not None:
        for b in band.get("by_level") or []:
            if b["lo"] <= level < b["hi"]:
                return b["sd"]
    return band.get("sd")


def _missing(v) -> bool:
    return v is None or (isinstance(v, float) and math.isnan(v))


def role_change(series: list, band, z: float = Z) -> dict | None:
    """The player's last two GAMES against his games before them, judged
    against the metric's noise at his usage level. None when there is not
    enough history (fewer than two earlier games), when either recent game has
    no value (a missing snap row must not slide an older week into the recent
    window -- review 2026-09-24), or when there is no band: 'insufficient
    sample' is an answer too. `band` is a fitted band dict or a plain SD."""
    if len(series) < 4 or any(_missing(v) for v in series[-2:]):
        return None
    recent = list(series[-2:])
    earlier = [v for v in series[:-2] if not _missing(v)]
    if len(earlier) < 2:
        return None
    sd = band_sd(band, float(np.mean(earlier)))
    if sd is None or (isinstance(sd, float) and math.isnan(sd)):
        return None
    if isinstance(band, dict) and band.get("z"):
        z = float(band["z"])
    diff = float(np.mean(recent) - np.mean(earlier))
    sd_diff = sd * math.sqrt(1 / 2 + 1 / len(earlier))
    return {"recent": round(float(np.mean(recent)), 3), "earlier": round(float(np.mean(earlier)), 3),
            "diff": round(diff, 3), "z": round(diff / sd_diff, 2) if sd_diff > 0 else None,
            "sd": round(float(sd), 4), "changed": bool(abs(diff) > z * sd_diff)}


def evidence_for(gsis_ids, usage: pd.DataFrame, positions: dict, bands: dict | None) -> dict:
    """gsis -> {pos, team, weeks, per-metric series and season means, role flags}."""
    out = {}
    for g in gsis_ids:
        d = usage[usage["gsis_id"] == g].sort_values("week")
        pos = positions.get(g)
        if d.empty:
            out[g] = {"pos": pos, "weeks": 0, "note": "no snaps or touches this season"}
            continue
        row = {"pos": pos, "team": d["team"].iloc[-1], "weeks": int(d["week"].nunique()),
               "series": {m: [None if pd.isna(v) else round(float(v), 3) for v in d[m]] for m in METRICS if m in d},
               "week_list": [int(w) for w in d["week"]],
               "mean": {m: (None if d[m].dropna().empty else round(float(d[m].mean()), 3)) for m in METRICS if m in d},
               "totals": {"targets": int(d["targets"].sum()), "carries": int(d["carries"].sum()),
                          "i10_tgt": int(d["i10_tgt"].sum()), "i10_car": int(d["i10_car"].sum())}}
        flags = {}
        for m in ROLE_METRICS.get(pos, ()):
            rc = role_change(row["series"].get(m, []), ((bands or {}).get(pos) or {}).get(m))
            if rc is not None:
                flags[m] = rc
        row["role_change"] = flags
        row["trajectory"] = ("INSUFFICIENT_SAMPLE" if not flags else
                             "CHANGED" if any(f["changed"] for f in flags.values()) else "STABLE")
        # A game with unusually few snaps is MARKED, not dropped: an in-game
        # injury and a benching look the same in snap counts, and hiding either
        # would be wrong. The verdict says a partial game is in the window.
        series = row["series"].get("snap_pct", [])
        row["partial_weeks"] = []
        for i, (w, v) in enumerate(zip(row["week_list"], series)):
            before = [x for x in series[:i] if not _missing(x)]
            if _missing(v) or not before:
                continue
            med = float(np.median(before))
            if med and v < PARTIAL_SNAP * med:
                row["partial_weeks"].append(w)
        if row["trajectory"] == "CHANGED" and set(row["partial_weeks"]) & set(row["week_list"][-2:]):
            row["trajectory"] = "CHANGED (includes a partial game)"
        out[g] = row
    return out


def for_sleeper(pids, info: dict, season: int, *, manifest: Manifest | None = None) -> dict:
    """sleeper_id -> evidence row, for the fantasy commands: Sleeper ids are
    joined to gsis through core.ids (the ID map, then Sleeper's own gsis_id),
    this season's usage is built once, and a player with no gsis id says so."""
    players = json.loads(F.sleeper_players(manifest=manifest).read_text(encoding="utf-8"))
    gmap, _ = IDS.sleeper_gsis(IDS.load_id_map(F.DEFAULT_CACHE, manifest=manifest), players)
    try:
        usage = season_usage(season, manifest=manifest)
    except Exception as ex:  # noqa: BLE001 -- evidence is context; its absence is reported, never fatal
        return {str(p): {"note": f"usage unavailable ({type(ex).__name__})"} for p in pids}
    bands = load_bands()
    want = {str(p): gmap.get(str(p)) for p in pids}
    pos = {g: (info.get(p) or {}).get("pos") for p, g in want.items() if g}
    ev = evidence_for([g for g in want.values() if g], usage, pos, bands)
    return {p: (ev.get(g) if g else {"note": "no nflverse id for this player"}) for p, g in want.items()}


def shuffled_z(usage: pd.DataFrame, positions: dict, bands: dict, *, shuffles: int = 20,
               min_games: int = 6, seed: int = 7) -> dict:
    """|z| of the recent-vs-earlier change when NO role changed: each player's
    games are shuffled (destroying any trend, keeping his distribution) and
    the statistic is taken at the end of the shuffled season.
    {pos: {metric: [|z|, ...]}}."""
    rng = np.random.default_rng(seed)
    u = usage.copy()
    u["pos"] = u["gsis_id"].map(positions)
    out = {}
    for pos, metrics in ROLE_METRICS.items():
        d = u[u["pos"] == pos]
        out[pos] = {}
        for m in metrics:
            zs = []
            band = ((bands or {}).get(pos) or {}).get(m)
            for _, g in d.groupby("gsis_id"):
                vals = [float(v) for v in g.sort_values("week")[m] if not _missing(v)]
                if len(vals) < min_games:
                    continue
                for _ in range(shuffles):
                    rc = role_change(list(rng.permutation(vals)), band)
                    if rc is not None and rc["z"] is not None:
                        zs.append(abs(rc["z"]))
            out[pos][m] = zs
    return out


def calibrate(bands: dict, zs: dict, target: float = TARGET_FALSE_ALARM) -> dict:
    """Each band's threshold set so the shuffled (no-change) seasons fire at
    `target`. A fixed 2-SD rule fired on 8-36% of them (QB snap share is
    nearly all-or-nothing, not normal; review 2026-09-24), so the threshold is
    measured, not assumed."""
    out = {p: {m: dict(b) for m, b in ms.items()} for p, ms in bands.items()}
    for pos, ms in zs.items():
        for m, z in ms.items():
            if z and m in out.get(pos, {}):
                out[pos][m]["z"] = round(float(np.quantile(z, 1 - target)), 2)
    return out


def false_alarm_rate(zs: dict, bands: dict) -> dict:
    """The share of no-change shuffles whose |z| clears each band's threshold."""
    return {pos: {m: (round(float(np.mean(np.array(z) > float(((bands.get(pos) or {}).get(m) or {}).get("z", Z)))), 3)
                      if z else None) for m, z in ms.items()} for pos, ms in zs.items()}


def load_bands() -> dict | None:
    p = RESOURCES / f"{NAME}.json"
    return json.loads(p.read_text(encoding="utf-8")).get("bands") if p.exists() else None


# ------------------------------------------------------------------- CLI

def _positions(manifest=None) -> dict:
    players = pd.read_csv(F.nflverse("players", manifest=manifest), low_memory=False)
    col = "gsis_id" if "gsis_id" in players.columns else "player_id"
    pos = "position_group" if "position_group" in players.columns else "position"
    return {g: ("RB" if p == "FB" else p) for g, p in zip(players[col], players[pos]) if isinstance(g, str)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m fantasy.evidence")
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("bands", help="fit noise bands on one season, check stability on the next")
    b.add_argument("--fit-season", type=int, default=2024)
    b.add_argument("--test-season", type=int, default=2025)
    a = ap.parse_args(argv)
    m = Manifest(f"{NAME} fit")
    pfr = pfr_map(m)
    pos = _positions(m)
    fit_usage = season_usage(a.fit_season, manifest=m, pfr=pfr)
    test_usage = season_usage(a.test_season, manifest=m, pfr=pfr)
    # thresholds calibrated on the FIT season's shuffles, judged on the TEST season's
    fit = calibrate(fit_bands(fit_usage, pos), shuffled_z(fit_usage, pos, fit_bands(fit_usage, pos)))
    test = fit_bands(test_usage, pos)
    # stability: the same metric's band in the next season, as a ratio
    stab = {p: {k: round(test.get(p, {}).get(k, {}).get("sd", float("nan")) / v["sd"], 3) if v["sd"] else None
                for k, v in ms.items()} for p, ms in fit.items()}
    worst = max((abs(r - 1) for p, ms in stab.items() for k, r in ms.items()
                 if k in ROLE_METRICS.get(p, ()) and r is not None and r == r), default=0)
    # the flag's false-alarm rate on the season the bands were NOT fitted to
    far = false_alarm_rate(shuffled_z(test_usage, pos, fit, seed=11), fit)
    worst_far = max((r for ms in far.values() for r in ms.values() if r is not None), default=0)
    ok = worst <= 0.20 and worst_far <= 0.10
    RESOURCES.mkdir(parents=True, exist_ok=True)
    (RESOURCES / f"{NAME}.json").write_text(json.dumps(
        {"model": NAME, "fit_season": a.fit_season, "test_season": a.test_season, "min_weeks": MIN_WEEKS, "z": Z,
         "built": dt.date.today().isoformat(), "bands": fit, "test_bands": test, "stability": stab,
         "false_alarm_rate": far,
         "validation": {"passed": ok, "worst_ratio_off": round(worst, 3), "worst_false_alarm": worst_far}},
        indent=1), encoding="utf-8")
    L = [f"# {NAME}", "", f"*Built {dt.date.today().isoformat()} by `python -m fantasy.evidence bands`. Week-to-week "
         f"standard deviation of each usage metric around a player's own season mean, players with >= {MIN_WEEKS} "
         f"weeks; fitted on {a.fit_season}, re-measured on {a.test_season}. A role change is flagged when the last "
         f"two weeks differ from the earlier weeks by more than {Z:g} noise SDs of that difference.*", "",
         f"**Verdict: {'PASS' if ok else 'FAIL'}.** Stability: every role-defining band within {worst:.0%} of its "
         f"{a.test_season} value (limit 20%). False alarms: each threshold is set so shuffled {a.fit_season} "
         f"seasons (no role change) fire 5% of the time; on shuffled {a.test_season} seasons the worst metric "
         f"fires {worst_far:.1%} (limit 10%). A fixed 2-SD rule fired on 8-36% of them.", "",
         "**False-alarm rate by metric** (each player's games shuffled 20 times, so no role changed; the share of "
         "shuffles the flag fires on): " + "; ".join(f"{p} " + ", ".join(f"{k} {v:.1%}" for k, v in ms.items()
                                                                           if v is not None)
                                                      for p, ms in far.items()) + ".",
         "", "Role-defining metrics per position (the only ones flagged or judged): "
         + "; ".join(f"{p} {', '.join(ms)}" for p, ms in ROLE_METRICS.items())
         + ". Chosen after the first fit failed on three metrics that mean nothing for the position -- TE carry "
         "share, QB target share, RB air-yard share -- which are shown below, marked excluded.", "",
         "| Position | Metric | SD (fit) | SD (next season) | ratio | players | calibrated z | role metric |",
         "|---|---|---|---|---|---|---|---|"]
    for p, ms in fit.items():
        for k, v in ms.items():
            t = test.get(p, {}).get(k, {})
            L.append(f"| {p} | {k} | {v['sd']:.3f} | {t.get('sd', float('nan')):.3f} | {stab[p][k]} | {v['players']} | "
                     f"{v.get('z', '—')} | {'yes' if k in ROLE_METRICS.get(p, ()) else 'excluded'} |")
    L += ["", "Bands are the robust SD (1.4826 x MAD, never below half the classical SD) of a player-week "
          "around his own season mean, split by his usage level where a level has 100+ player-weeks:", ""]
    for p_, ms in fit.items():
        for k, v in ms.items():
            if k in ROLE_METRICS.get(p_, ()) and v.get("by_level"):
                L.append(f"- {p_} {k}: " + ", ".join(f"{b['lo']:g}-{b['hi']:g} sd {b['sd']:.3f} (n {b['n']})"
                                                     for b in v["by_level"]))
    (ROOT / "reports" / f"{NAME}.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"{NAME}: {'PASS' if ok else 'FAIL'} (worst season-to-season band change {worst:.0%})")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
