"""Brief orchestration: live league state -> waiver/lineup/early-check briefs.

Everything degrades: missing weekly projections fall back to season/16 with a
visible banner; any failed fetch lands in `stale` and the briefs still render
from last-good data (the ADP-diff pattern). Recommend-only.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import polars as pl

from . import lineup as lineup_mod
from . import playoffs, seasondata, waivers, weekly
from .lenses import scoreboard_md
from .sleeper import SleeperClient

SLOTS = {"QB": 1, "RB": 2, "WR": 2, "TE": 1, "K": 1, "DEF": 1}
FLEX = 2
POS_OK = ("QB", "RB", "WR", "TE", "K", "DEF")


def _season_cfg(cfg) -> dict:
    # "inseason" since 2026-08-29: the block's old name `season:` shadowed the
    # season-year scalar (YAML last-key-wins) and broke every int(cfg["season"]) caller
    return cfg.get("inseason", cfg.get("season", {})) or {}


def build_context(cfg) -> dict:
    """One fetch pass; every downstream brief reads from this dict."""
    stale: list[str] = []
    client = SleeperClient(cfg.path("raw"))
    state = seasondata.nfl_state()
    season, week = state["season"], state["week"]
    preseason = state["season_type"] != "regular"
    if preseason:
        week = 1

    league = client.league(cfg.league_id)
    scoring = league["scoring_settings"]
    budget = int(league["settings"].get("waiver_budget", 100))
    reserve_allow = tuple(
        s for s, ok in (("Out", league["settings"].get("reserve_allow_out", 0)),
                        ("Doubtful", league["settings"].get("reserve_allow_doubtful", 0))) if ok
    ) or ("Out",)
    rosters = client.league_rosters(cfg.league_id)
    users = {str(u["user_id"]): u.get("display_name", "?") for u in client.league_users(cfg.league_id)}
    me_user = next((uid for uid, name in users.items()
                    if name.lower() == str(cfg["me"]["username"]).lower()), None)
    my_roster = next((r for r in rosters if str(r.get("owner_id")) == me_user), rosters[0])

    players = client.players()
    injury = seasondata.injury_map(players)
    schedule = seasondata.load_schedule(cfg, int(season))
    week_byes = seasondata.byes(schedule, week)
    early = seasondata.early_games(schedule, week)

    tiers = pl.read_csv(cfg.scoped(cfg.root / "tiers.csv"), infer_schema_length=2000)
    trow = {str(r["sleeper_id"]): r for r in tiers.iter_rows(named=True)}

    weekly_proj = seasondata.weekly_projections(scoring, season, week)
    fallback = weekly_proj is None

    # defense quality (post-v2 item 2): real opponent adjustment, shrunk hard
    # early. None -> DATA MISSING banner, never a null adjustment.
    from . import defense as defense_mod
    scfg_early = _season_cfg(cfg)
    shrink_k = float(scfg_early.get("matchup_shrink_weeks", 5))
    matchup_cap = float(scfg_early.get("matchup_cap", 0.10))
    pa = defense_mod.points_allowed(int(season), scoring, through_week=max(0, week - 1))
    if pa is None:
        stale.append("defense quality (no completed weeks yet)")
    opp_of = {}
    try:
        for r in schedule.filter(pl.col("week") == week).iter_rows(named=True):
            opp_of[r["team"]] = r["opp"]
    except Exception:  # noqa: BLE001
        pass

    scfg = _season_cfg(cfg)

    def base_pts(pid: str) -> float:
        if weekly_proj and pid in weekly_proj:
            return weekly_proj[pid]
        r = trow.get(pid)
        return (r["proj_pts"] or 0.0) / 16.0 if r else 0.0

    def player_row(pid: str) -> dict | None:
        p = players.get(pid)
        if not isinstance(p, dict):
            return None
        pos = {"DST": "DEF"}.get(p.get("position"), p.get("position"))
        if pos not in POS_OK:
            return None
        team = p.get("team") or (trow.get(pid) or {}).get("team")
        status = injury.get(pid, "")
        ratio = defense_mod.allowed_ratio(pa, opp_of.get(team, ""), pos, shrink_k)             if pa is not None else None
        mult = weekly.matchup_mult(ratio, week, matchup_cap, shrink_k) if ratio else 1.0
        wk = weekly.compose(base_pts(pid), mult, 0.0, status)
        if team in week_byes:
            wk = 0.0
        name = f"{p.get('first_name','')} {p.get('last_name','')}".strip() or pid
        t = trow.get(pid) or {}
        return {"sleeper_id": pid, "name": name, "pos": pos, "team": team,
                "weekly": round(wk, 2), "status": status,
                "matchup_mult": round(mult, 3), "opp": opp_of.get(team),
                "ros": round((t.get("proj_pts") or wk * 16) or 0.0, 1),
                "backs_up": t.get("backs_up"), "stdev": 5.0}

    roster_players: dict[int, list[dict]] = {}
    for r in rosters:
        rows = [player_row(str(pid)) for pid in (r.get("players") or [])]
        roster_players[int(r["roster_id"])] = [x for x in rows if x]

    try:
        matchups = client_matchups(client, cfg.league_id, week)
    except Exception:  # noqa: BLE001
        matchups, _ = [], stale.append(f"week-{week} matchups")

    try:
        txns = get_transactions(client, cfg.league_id, week)
        seasondata.append_transactions(cfg, txns)
    except Exception:  # noqa: BLE001
        stale.append("transactions")

    return {
        "cfg": cfg, "scfg": scfg, "client": client, "state": state, "week": week,
        "preseason": preseason, "fallback": fallback, "stale": stale,
        "league": league, "budget": budget, "reserve_allow": reserve_allow,
        "rosters": rosters, "roster_players": roster_players, "users": users,
        "my_roster": my_roster, "players": players, "injury": injury,
        "schedule": schedule, "byes": week_byes, "early": early,
        "matchups": matchups, "player_row": player_row, "trow": trow,
    }


def client_matchups(client, league_id: str, week: int) -> list[dict]:
    from .sleeper import BASE, get_json
    return get_json(f"{BASE}/league/{league_id}/matchups/{week}") or []


def get_transactions(client, league_id: str, week: int) -> list[dict]:
    from .sleeper import BASE, get_json
    return get_json(f"{BASE}/league/{league_id}/transactions/{max(1, week)}") or []


def _records(rosters) -> dict[int, tuple[int, int]]:
    return {int(r["roster_id"]): (int((r.get("settings") or {}).get("wins", 0)),
                                  int((r.get("settings") or {}).get("losses", 0)))
            for r in rosters}


def _points_for(rosters) -> dict[int, float]:
    return {int(r["roster_id"]): float((r.get("settings") or {}).get("fpts", 0) or 0)
            for r in rosters}


def playoff_odds(ctx) -> tuple[float, str]:
    cfg, scfg = ctx["cfg"], ctx["scfg"]
    league = ctx["league"]
    start = int(league["settings"].get("playoff_week_start", 15))
    weeks = [w for w in range(max(ctx["week"], 1), start) if w >= ctx["week"]]
    if not weeks:
        return 1.0, "SAFE"
    schedule = ctx["schedule"]
    strengths = {}
    for rid, roster in ctx["roster_players"].items():
        strengths[rid] = {}
        for w in weeks:
            wb = seasondata.byes(schedule, w)
            strengths[rid][w] = playoffs.team_week_strength(roster, wb, SLOTS, FLEX)
    matchups_by_week = {}
    for w in weeks:
        try:
            ms = client_matchups(ctx["client"], cfg.league_id, w)
        except Exception:  # noqa: BLE001
            ms = []
        pairs, seen = [], {}
        for m in ms:
            mid = m.get("matchup_id")
            if mid in seen:
                pairs.append((seen[mid], int(m["roster_id"])))
            else:
                seen[mid] = int(m["roster_id"])
        if pairs:
            matchups_by_week[w] = pairs
    if not matchups_by_week:
        return 0.5, "BUBBLE"
    rng = np.random.default_rng(int(ctx["week"]) * 7919)
    odds = playoffs.simulate_season(
        strengths, matchups_by_week, _records(ctx["rosters"]),
        playoff_teams=int(league["settings"].get("playoff_teams", 6)),
        sims=int(scfg.get("sims", 4000)), sigma=float(scfg.get("score_sigma", 28.0)),
        rng=rng, points_for=_points_for(ctx["rosters"]),
    )
    mine = odds.get(int(ctx["my_roster"]["roster_id"]), 0.5)
    return mine, playoffs.regime(mine, scfg)


def _actual_points(cfg, users_by_roster) -> dict[str, float]:
    path = Path(cfg.path("processed")) / "season" / "actuals.jsonl"
    if not path.exists():
        return {}
    totals: dict[str, float] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            e = json.loads(line)
        except ValueError:
            continue
        name = users_by_roster.get(int(e.get("roster_id", 0)))
        if name:
            totals[name] = totals.get(name, 0.0) + float(e.get("points", 0))
    return totals


def record_actuals(ctx) -> int:
    """Persist finalized matchup points (called on refresh after each week)."""
    if ctx["preseason"] or ctx["week"] <= 1:
        return 0
    from .sleeper import BASE, get_json
    cfg = ctx["cfg"]
    path = Path(cfg.path("processed")) / "season" / "actuals.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    seen = set()
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                e = json.loads(line)
                seen.add((e["week"], e["roster_id"]))
            except (ValueError, KeyError):
                continue
    added = 0
    for w in range(1, ctx["week"]):
        ms = get_json(f"{BASE}/league/{cfg.league_id}/matchups/{w}") or []
        with open(path, "a", encoding="utf-8") as f:
            for m in ms:
                key = (w, int(m["roster_id"]))
                if key not in seen and m.get("points") is not None:
                    f.write(json.dumps({"week": w, "roster_id": int(m["roster_id"]),
                                        "points": m["points"]}) + "\n")
                    added += 1
    return added


def _users_by_roster(ctx) -> dict[int, str]:
    return {int(r["roster_id"]): ctx["users"].get(str(r.get("owner_id")), "?")
            for r in ctx["rosters"]}


def _rival_needs(ctx) -> dict[int, dict[str, int]]:
    needs = {}
    for rid, roster in ctx["roster_players"].items():
        have = {}
        for p in roster:
            have[p["pos"]] = have.get(p["pos"], 0) + 1
        needs[rid] = {pos: max(0, SLOTS[pos] - have.get(pos, 0)) for pos in SLOTS}
    return needs


def waiver_brief(cfg) -> Path:
    ctx = build_context(cfg)
    record_actuals(ctx)
    odds, reg = playoff_odds(ctx)
    my_rid = int(ctx["my_roster"]["roster_id"])
    rostered = {str(pid) for r in ctx["rosters"] for pid in (r.get("players") or [])}

    fa_pool = []
    for pid, p in ctx["players"].items():
        if str(pid) in rostered or not isinstance(p, dict) or not p.get("active"):
            continue
        row = ctx["player_row"](str(pid))
        if row and (row["weekly"] > 0 or row["ros"] > 60):
            fa_pool.append(row)
    fa_pool.sort(key=lambda p: -p["ros"])
    fa_pool = fa_pool[:200]

    budgets = seasondata.rival_budgets(ctx["rosters"], ctx["budget"])
    my_budget = budgets.get(my_rid, ctx["budget"])
    needs = _rival_needs(ctx)
    scfg_faab = ctx["scfg"].get("faab", {})
    faab = {k: scfg_faab.get(k, v) for k, v in {
        "league_winner": [0.40, 0.65], "breakout": [0.15, 0.35],
        "speculative": [0.05, 0.12], "streamer": [0.01, 0.03],
        "max_week_commit": 0.80}.items()}

    claims = waivers.classify_contingencies(fa_pool, ctx["roster_players"], ctx["injury"])[:4]
    for c in claims:
        rid_needy = [rid for rid, n in needs.items() if rid != my_rid and n.get(c["pos"], 0) > 0]
        rival_max = max((budgets[r] for r in rid_needy), default=None)
        cls = "league_winner" if c["ros"] >= 120 else "speculative"
        c["cls"] = cls if cls == "league_winner" else "contingency-speculative"
        fair, agg = waivers.bid_band(
            "league_winner" if cls == "league_winner" else "speculative",
            my_budget, reg, faab, rival_max_budget=rival_max if cls == "league_winner" else None,
            value_cap=int(c["ros"] / 2) if cls == "league_winner" else None, odds=odds)
        c["fair"], c["aggressive"] = fair, agg
        if rid_needy:
            c["rivals_note"] = (f"{len(rid_needy)} rival(s) need {c['pos']}; budgets: "
                                + ", ".join(f"${budgets[r]}" for r in sorted(rid_needy, key=lambda r: -budgets[r])[:3]))
    # streamers: best available DEF/K by weekly value
    for pos in ("DEF", "K"):
        best = next((p for p in fa_pool if p["pos"] == pos), None)
        mine_have = any(p["pos"] == pos for p in ctx["roster_players"][my_rid])
        if best and not mine_have:
            fair, agg = waivers.bid_band("streamer", my_budget, reg, faab, odds=odds)
            claims.append({**best, "cls": "streamer", "fair": fair, "aggressive": agg,
                           "evidence": f"best available {pos} this week"})

    bench_starters = {p["name"] for p in lineup_mod.optimal_lineup(
        ctx["roster_players"][my_rid], SLOTS, FLEX)}
    my_bench = [p for p in ctx["roster_players"][my_rid] if p["name"] not in bench_starters]
    ir_occ = [ctx["player_row"](str(pid)) for pid in (ctx["my_roster"].get("reserve") or [])]
    ir_occ = [x for x in ir_occ if x]
    prot = waivers.protected_drop_ids(my_bench, bench_starters,
                                      {p["sleeper_id"] for p in ir_occ})
    droppable = sorted((p for p in my_bench if p["sleeper_id"] not in prot),
                       key=lambda p: p["ros"])
    # a drop must be worth LESS than the player being claimed, and each claim
    # gets a distinct name so the list reads as a plan, not four copies
    taken: set[str] = set()
    for c in claims:
        pick = next((d for d in droppable
                     if d["name"] not in taken and d["ros"] < c.get("ros", 0)), None)
        if pick:
            taken.add(pick["name"])
            c["drop"] = pick["name"]
        else:
            c["drop"] = None
            c["drop_note"] = "no sensible drop — every bench player outranks him"

    users_by_roster = _users_by_roster(ctx)
    rec = ctx["my_roster"].get("settings") or {}
    model = {
        "week": ctx["week"], "record": f"{rec.get('wins', 0)}-{rec.get('losses', 0)}",
        "odds": odds, "regime": reg, "remaining_budget": my_budget,
        "ir_actions": waivers.ir_actions(ir_occ, ctx["roster_players"][my_rid],
                                         ctx["injury"], ctx["reserve_allow"]),
        "claims": claims, "stale": ctx["stale"],
        "preseason_note": ("PRESEASON / projections not yet published — values are "
                           "fallback baselines (season proj ÷ 16)"
                           if ctx["preseason"] or ctx["fallback"] else ""),
        "scoreboard_md": scoreboard_md(_actual_points(cfg, users_by_roster)),
    }
    out = cfg.root / "reports" / "waiver_brief.md"
    out.write_text(waivers.render_waiver_brief(model), encoding="utf-8")
    return out


def _lineup_model(ctx, teams_filter: set[str] | None = None) -> dict:
    my_rid = int(ctx["my_roster"]["roster_id"])
    roster = ctx["roster_players"][my_rid]
    if teams_filter is not None:
        roster_view = [p for p in roster if p["team"] in teams_filter]
    else:
        roster_view = roster
    current = [str(x) for x in (ctx["my_roster"].get("starters") or []) if str(x) != "0"]
    changes, my_total = lineup_mod.lineup_changes(roster, current, SLOTS, FLEX)
    if teams_filter is not None:
        changes = [c for c in changes if any(p["name"] in c for p in roster_view)]
    # opponent
    opp_total, opp_name = 0.0, "?"
    mine = next((m for m in ctx["matchups"] if int(m.get("roster_id", -1)) == my_rid), None)
    if mine:
        opp = next((m for m in ctx["matchups"]
                    if m.get("matchup_id") == mine.get("matchup_id")
                    and int(m["roster_id"]) != my_rid), None)
        if opp:
            orid = int(opp["roster_id"])
            opp_name = _users_by_roster(ctx).get(orid, "?")
            opp_total = sum(p["weekly"] for p in lineup_mod.optimal_lineup(
                ctx["roster_players"][orid], SLOTS, FLEX))
    margin = my_total - opp_total
    lean = ("favorite — prefer floor in close calls" if margin > 8 else
            "underdog — prefer ceiling in close calls" if margin < -8 else
            "close matchup — projection decides")
    kick = {r["team"]: f"{r['gameday']} {r['gametime']}"
            for r in ctx["schedule"].filter(pl.col("week") == ctx["week"]).iter_rows(named=True)}
    starters_set = {q["name"] for q in lineup_mod.optimal_lineup(roster, SLOTS, FLEX)}

    def _backup(pos, exclude):
        cands = [b for b in roster if b["pos"] == pos and b["name"] not in starters_set
                 and b["name"] != exclude and b["weekly"] > 0]
        return max(cands, key=lambda b: b["weekly"])["name"] if cands else None

    flags = [{"name": p["name"], "status": p["status"],
              "kick": kick.get(p["team"], "?"), "backup": _backup(p["pos"], p["name"])}
             for p in roster_view
             if p["status"] in ("Questionable", "Doubtful", "Out") and p["name"] in starters_set]
    early_mine = sorted(
        f"{p['name']} ({p['team']})" for p in roster
        if teams_filter is not None and p["team"] in teams_filter and p["name"] in starters_set
    )
    warnings = []
    starters_raw = ctx["my_roster"].get("starters") or []
    if "0" in [str(s) for s in starters_raw]:
        warnings.append("You have an EMPTY starting slot in Sleeper")
    for p in lineup_mod.optimal_lineup(roster, SLOTS, FLEX):
        if p["team"] in ctx["byes"]:
            warnings.append(f"{p['name']} is on BYE this week and projects 0")
    ir_occ = [ctx["player_row"](str(pid)) for pid in (ctx["my_roster"].get("reserve") or [])]
    for a in waivers.ir_actions([x for x in ir_occ if x], roster, ctx["injury"], ctx["reserve_allow"]):
        warnings.append(a)
    return {"week": ctx["week"], "opp_name": opp_name, "my_total": my_total,
            "opp_total": opp_total, "changes": changes, "lean": lean, "flags": flags,
            "matchups": [
                {"name": p["name"], "opp": p.get("opp") or "?",
                 "mult": float(p.get("matchup_mult") or 1.0),
                 "before": (p.get("weekly") or 0.0) / float(p.get("matchup_mult") or 1.0),
                 "after": p.get("weekly") or 0.0}
                for p in roster if p.get("matchup_mult")
                and abs(float(p["matchup_mult"]) - 1.0) >= 0.02
            ],
            "warnings": warnings, "stale": ctx["stale"],
            "early_teams": sorted(set(ctx["early"]["team"].to_list())),
            "early_mine": early_mine,
            "preseason_note": ("PRESEASON / projections not yet published — values are "
                               "fallback baselines" if ctx["preseason"] or ctx["fallback"] else "")}


def lineup_brief(cfg) -> Path:
    ctx = build_context(cfg)
    model = _lineup_model(ctx)
    out = cfg.root / "reports" / "lineup_brief.md"
    out.write_text(lineup_mod.render_lineup_brief(model), encoding="utf-8")
    return out


def early_check(cfg) -> Path:
    ctx = build_context(cfg)
    teams = set(ctx["early"]["team"].to_list())
    model = _lineup_model(ctx, teams_filter=teams)
    if not teams:
        model["warnings"] = [f"No early games in week {ctx['week']} — nothing locks before the weekend"]
    out = cfg.root / "reports" / "early_check.md"
    out.write_text(lineup_mod.render_early_check(model), encoding="utf-8")
    return out
