"""Research columns for the props board (props-v1.29, DECISIONS #142).

Nothing here changes a price. These functions answer the questions a person
handicapping a prop asks, using the same simulation the prices come from:

- implied workload: the targets (or carries) a posted line needs to be a fair
  50/50, next to what the model projects;
- the break-even workload at the posted prices: the workload above which the
  Over beats its price, and below which the Under beats its price -- how far
  a view of his role can be wrong before the bet stops paying;
- usage: last game's snap / target / carry share against his earlier weeks;
- the receiving role-shift flag, worded from its 2022-25 check
  (reports/role_shift_check.md).

Every simulation here runs on its OWN generator, re-created for each
evaluation (common random numbers), so the shared pricing stream in
score_game.py is never touched and the search is smooth in the multiplier.
"""
from __future__ import annotations

import re

import numpy as np

import model as MODEL

N_SEARCH = 8000
SEED = 20261003
K_LO, K_HI = 0.05, 4.0

# reports/role_shift_check.md: fixed before the check, earned for receiving only
SNAP_JUMP = 0.15
SHARE_LAG = 0.03


def _bisect(p_over_at, target=0.5, lo=K_LO, hi=K_HI, iters=14):
    """The multiplier k where p_over_at(k) = target, P(over) rising in k.
    None when the line sits outside [lo, hi]."""
    if p_over_at(lo) > target or p_over_at(hi) < target:
        return None
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        if p_over_at(mid) < target:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def breakeven(price) -> float | None:
    """The win rate an American price needs (its own vig included), or None.
    The same rule as props/journal.py breakeven(); the engine ships without
    props/, so the two are kept in step by hand."""
    try:
        a = float(price)
    except (TypeError, ValueError):
        return None
    if not np.isfinite(a) or abs(a) < 100:
        return None
    return abs(a) / (abs(a) + 100) if a < 0 else 100 / (a + 100)


def _share_over(sim_of_k, line):
    """The Over's share of the bets that do not push: wins / (wins + losses).
    On a half line it is P(stat > line); on a whole line a push refunds, so
    this is what a price is judged against."""
    def f(k):
        x = sim_of_k(k)
        gt, lt = float((x > line).mean()), float((x < line).mean())
        return gt / (gt + lt) if gt + lt > 0 else 0.5
    return f


def _break_even_ks(share_over, prices):
    """The multipliers where each side breaks even at its price. Over:
    share_over(k) = be_over. Under: share_over(k) = 1 - be_under. Returns
    (k_over, k_under); None where the workload is outside the search range or
    the side has no price (break_even_cell tells the two apart by be_over /
    be_under)."""
    be_o, be_u = (breakeven(prices[0]), breakeven(prices[1])) if prices else (None, None)
    return (None if be_o is None else _bisect(share_over, be_o),
            None if be_u is None else _bisect(share_over, 1 - be_u))


def search_edges(share_over, prices):
    """Where a failed break-even search ran out: for each side, 'max' when even
    the most work the simulation can give him is not enough (Over) or still
    pays (Under), 'min' at the other end; None when the search found a number
    or the side has no price."""
    be_o, be_u = (breakeven(prices[0]), breakeven(prices[1])) if prices else (None, None)
    hi = share_over(K_HI)

    def edge(target):
        return None if target is None else ("max" if hi < target else "min")
    return edge(be_o), edge(None if be_u is None else 1 - be_u)


def break_even_cell(x) -> str:
    """The research table's 'Pays at this price if he gets' cell: the Over beats
    its own price above over_needs, the Under at or below under_needs. A side
    with no posted price (no be_over / be_under) says so rather than reading as
    a search that ran out of range."""
    unit = x.get("unit") if isinstance(x.get("unit"), str) else ""
    blank = lambda v: v is None or bool(np.isnan(float(v)))
    o, u, bo, bu = (x.get(k) for k in ("over_needs", "under_needs", "be_over", "be_under"))
    if not unit or (blank(bo) and blank(bu)):
        return "—"

    edge = {k: x.get(k) for k in ("over_edge", "under_edge", "over_limit", "under_limit")}

    def side(v, be, word, fmt, key):
        if blank(be):
            return f"{word}: no price posted"
        if not blank(v):
            return fmt.format(v=float(v))
        e, lim = edge.get(f"{key}_edge"), edge.get(f"{key}_limit")
        if isinstance(e, str) and not blank(lim):
            # the search ran out: say where, in his units
            if key == "over":
                return (f"Over: needs more than {float(lim):.1f} {unit} (about all the work the simulation "
                        "gives him: the line rests on his efficiency or the team's volume)" if e == "max"
                        else f"Over: pays even at {float(lim):.1f} {unit}")
            return (f"Under: pays even at {float(lim):.1f} {unit}" if e == "max"
                    else f"Under: needs fewer than {float(lim):.1f} {unit}")
        return f"{word}: beyond the search range"
    cell = (f"{side(o, bo, 'Over', 'Over above {v:.1f} ' + unit, 'over')}; "
            f"{side(u, bu, 'Under', 'Under at {v:.1f} or fewer', 'under')}")
    p = x.get("projected")
    if not (blank(o) or blank(u) or blank(p) or blank(bo) or blank(bu)):
        # where OUR projection lands: the Over pays above o, the Under at or below u,
        # and between them the book's cut leaves no bet
        p = float(p)
        zone = "Over zone" if p > float(o) else "Under zone" if p <= float(u) else "no-bet zone"
        cell += f" · we project {p:.1f}: {zone}"
    return cell


LAST_EDGES = {}     # the latest search's edges, read by edges_for(); set by _edge_cache


def _edge_cache(share_over, prices, k_o, k_u, work):
    """Record, for a side whose search failed, which end it ran out at and the
    workload there, so the cell can say 'needs more than 19 carries' rather
    than 'beyond the search range'."""
    eo, eu = search_edges(share_over, prices)
    lim = lambda e: None if e is None else work(K_HI if e == "max" else K_LO)
    LAST_EDGES.clear()
    LAST_EDGES.update(over_edge=eo if k_o is None else None, under_edge=eu if k_u is None else None)
    LAST_EDGES.update(over_limit=lim(LAST_EDGES["over_edge"]), under_limit=lim(LAST_EDGES["under_edge"]))


def edges_for() -> dict:
    """The edges of the last implied_* call made with prices (see _edge_cache)."""
    return dict(LAST_EDGES)


def implied_targets(line, stat, team_targets_mean, targets_r, share, catch_rate, ypt,
                    per_catch_shape, width=None, prices=None):
    """Targets per game at which the line is a coin flip for a receiver (P(stat >
    line) = 0.5 on a half line; Overs and Unders equally likely on a whole line), holding
    his catch rate and yards per target. stat: 'receptions' or 'rec_yards'.
    Returns (implied targets, projected targets) or (None, projected). With
    prices=(over, under) it also returns the targets at which the Over and the
    Under break even at those prices: (implied, projected, over_needs,
    under_needs) -- the Over pays above over_needs, the Under below under_needs."""
    proj = team_targets_mean * share
    if share <= 0 or line is None:
        return (None, proj) if prices is None else (None, proj, None, None)
    col = 0 if stat == "receptions" else 1
    cache = {}

    def sim(k):      # common random numbers: one generator per k, cached
        if k not in cache:
            s = min(share * k, 0.95)
            out, _ = MODEL.simulate_team_game(np.random.default_rng(SEED), N_SEARCH, team_targets_mean,
                                              targets_r, {"p": s}, {"p": catch_rate}, {"p": ypt},
                                              per_catch_shape, other_bucket=True, width=width)
            cache[k] = out["p"][col]
        return cache[k]

    work = lambda k: None if k is None else team_targets_mean * min(share * k, 0.95)
    share_over = _share_over(sim, line)
    k = _bisect(share_over)
    if prices is None:
        return work(k), proj
    k_o, k_u = _break_even_ks(share_over, prices)
    _edge_cache(share_over, prices, k_o, k_u, work)
    return work(k), proj, work(k_o), work(k_u)


def implied_carries(line, j, team_carries_mean, carries_r, rush_shares, ypc, resid,
                    width=None, player_resid=None, player_kneel=None, qb_index=None, prices=None):
    """Carries per game at which the line is a coin flip for player j (as above),
    scaling only his share inside the FULL team call (the share rescale
    depends on every teammate). Returns (implied mean carries, projected mean
    carries), the effective carries the simulation gives him. With
    prices=(over, under) it also returns the carries at which each side breaks
    even at its price, as implied_targets does."""
    shares = [float(v) for v in rush_shares]
    cache = {}

    def run(k):
        if k not in cache:
            s = list(shares)
            s[j] = min(s[j] * k, 0.95)
            car, yds, _ = MODEL.simulate_team_rush(np.random.default_rng(SEED), N_SEARCH, team_carries_mean,
                                                   carries_r, s, ypc, resid, width=width,
                                                   player_resid=player_resid, player_kneel=player_kneel,
                                                   qb_index=qb_index)
            cache[k] = (car[j], yds[j])
        return cache[k]

    proj = float(run(1.0)[0].mean())
    if shares[j] <= 0 or line is None:
        return (None, proj) if prices is None else (None, proj, None, None)
    work = lambda k: None if k is None else float(run(k)[0].mean())
    share_over = _share_over(lambda k: run(k)[1], line)
    k = _bisect(share_over)
    if prices is None:
        return work(k), proj
    k_o, k_u = _break_even_ks(share_over, prices)
    _edge_cache(share_over, prices, k_o, k_u, work)
    return work(k), proj, work(k_o), work(k_u)


# an Out teammate is named on the board only when he had a real role (DECISIONS #155)
OUT_TARGET_SHARE, OUT_CARRY_SHARE, OUT_PASS_SHARE = 0.10, 0.15, 0.50


def is_key_teammate(prior_ts=None, prior_rs=None, season_ts=None, season_rs=None, cut=0.15) -> bool:
    """A teammate whose return (or arrival) moves work: 15%+ of the targets or
    of the carries, last season or this one (DECISIONS #157)."""
    vals_t = [v for v in (prior_ts, season_ts) if v is not None and v == v]
    vals_r = [v for v in (prior_rs, season_rs) if v is not None and v == v]
    return max(vals_t + [0.0]) >= cut or max(vals_r + [0.0]) >= cut


def role_share(plays, pid, team, weeks=None):
    """His share of the team's plays in the weeks he was available this season:
    `weeks` (the weeks he was on the active roster) plus any week he had a play,
    so the games he played without a target still count. plays: DataFrame
    with posteam, week, pid. None when he has no play at all."""
    d = plays[plays.posteam == team]
    mine = set(d.loc[d.pid == pid, "week"])
    if not mine:
        return None
    weeks = mine | set(weeks or ())
    dd = d[d.week.isin(weeks)]
    return float((dd.pid == pid).mean()) if len(dd) else None


def out_matters(pid, team, targets, carries, dropbacks, prior_ts=None, prior_rs=None, weeks=None) -> bool:
    """True when an Out player's absence is worth a flag: this season he threw
    half the team's passes, drew 10%+ of its targets or took 15%+ of its
    carries in the weeks he played; with no play this season, last season's
    shares decide (never a slot default -- an unknown depth player is not
    news). A depth receiver with two targets in two games is not flagged."""
    shares = [(role_share(dropbacks, pid, team, weeks), OUT_PASS_SHARE),
              (role_share(targets, pid, team, weeks), OUT_TARGET_SHARE),
              (role_share(carries, pid, team, weeks), OUT_CARRY_SHARE)]
    if any(s is not None for s, _ in shares):
        return any(s is not None and s >= cut for s, cut in shares)
    return bool((prior_ts or 0) >= OUT_TARGET_SHARE or (prior_rs or 0) >= OUT_CARRY_SHARE)


# WORTH A LOOK (DECISIONS #156), fixed before any result: a story about his
# role this week, AND last game's actual workload already beyond the side's
# break-even workload by a clear margin, in the story's direction. Not a bet
# label: it marks where the user's own read has the most to work with, and the
# scorecard grades every mark at Sleeper's prices.
LOOK_MARGIN = {"targets": 2.0, "carries": 3.0}


def preview_note(diffs) -> str:
    """The team's 'was last week a preview' note (DECISIONS #157)."""
    return ("last week was a preview: same QB, same key absences" if not diffs
            else "last week differs: " + "; ".join(diffs))


def qb_change(last_week_passers, today_id, today_name):
    """'QB change (X last week, Y today)' or None. last_week_passers: the team's
    pass plays last week with passer_player_id / passer_player_name."""
    if today_id is None or last_week_passers is None or not len(last_week_passers):
        return None
    lw_id = last_week_passers.passer_player_id.value_counts().index[0]
    if lw_id == today_id:
        return None
    lw_nm = last_week_passers[last_week_passers.passer_player_id == lw_id].passer_player_name.iloc[0]
    return f"QB change ({lw_nm} last week, {today_name} today)"


def worth_a_look(x, last_week):
    """(side, why) or None for one research row (a dict). x needs flags,
    player, market, unit, over_needs, under_needs, tn / cn and usage_week."""
    unit = x.get("unit")
    if unit not in LOOK_MARGIN:
        return None
    if x.get("usage_week") is None or int(x["usage_week"]) != int(last_week):
        return None          # last game must be the game just played
    n = x.get("cn") if x.get("market") == "player_rush_yds" else x.get("tn")
    if n is None or n != n:
        return None
    flags = [f.strip() for f in str(x.get("flags") or "").split(";") if f.strip()]
    me = str(x.get("player", ""))
    outs = [re.match(r"^(.+?) out(,|$)", f) for f in flags]
    rush = x.get("market") == "player_rush_yds"
    # a teammate out hands his work on (Over) -- except the starting QB: a
    # backup thins the passing game, so a QB out is a story for the backs'
    # carries only, never for a receiver
    up = any(f == "role up" for f in flags) or (rush and "carries up" in flags) or any(
        m_ and m_.group(1).replace(" (QB)", "") != me and (rush or not m_.group(1).endswith(" (QB)")) for m_ in outs)
    down = (any(f == "role down" for f in flags) or (rush and "carries down" in flags)
            or any(" back (missed last week)" in f for f in flags))
    # a role or teammate story sets the direction; stories pulling both ways
    # (more snaps, but the star teammate is back) mark nothing; a new team
    # with no other story allows either side
    if up and down:
        return None
    if not (up or down) and any(f.startswith("new team") for f in flags):
        up = down = True
    if not (up or down):
        return None
    m = LOOK_MARGIN[unit]
    o, u = x.get("over_needs"), x.get("under_needs")
    pv = x.get("preview")
    tail = f"; {pv}" if isinstance(pv, str) and pv else ""
    if up and o is not None and o == o and n >= o + m:
        return "Over", f"last game {n:.0f} {unit}; the Over pays above {o:.1f}{tail}"
    if down and u is not None and u == u and n <= u - m:
        return "Under", f"last game {n:.0f} {unit}; the Under pays at {u:.1f} or fewer{tail}"
    return None


def to_clear(line) -> int:
    """The smallest whole number that wins the Over. Lines move in halves: 3.5 needs
    4; a whole-number line of 4 needs 5 (4 pushes)."""
    return int(np.floor(float(line))) + 1


# a display band, picked, not measured: the lines' yards a catch within this much of
# ours reads "about even". The read is arithmetic about the lines, never a claim that
# one leg wins more often (DECISIONS #164)
YPC_BAND = 1.0
YPC_MIN_CATCHES = 8
# THE LUCK LINE for the achievability gauge (user's design, 2026-10-05; DECISIONS #167):
# a play past the player's OWN 95th percentile for that prop -- his catches for receiving
# yards, his runs for rushing yards, last season and this one together -- counts as a lucky
# breakaway and is counted at that line. "Too few" = under LUCK_MIN_PLAYS of his own plays of
# that kind (at 20 the 95th percentile still sits between his two longest; below it the line
# would just be his single longest play); then his longest play this season is left out
# instead (user's call). A definition for a descriptive gauge, not a fit
# (reports/robust_ypc_check.md, for reference only)
LUCK_PCT = 95
LUCK_MIN_PLAYS = 20


def player_luck_line(plays) -> dict:
    """The luck line for one player and one kind of play: {cap, own, n}. own: his
    LUCK_PCT percentile play sets the cap. Otherwise (too few plays) cap is None and the
    caller leaves his longest play out instead (luck_free_rate)."""
    v = [float(x) for x in (plays or []) if x == x]
    if len(v) >= LUCK_MIN_PLAYS:
        return {"cap": float(np.percentile(v, LUCK_PCT)), "own": True, "n": len(v)}
    return {"cap": None, "own": False, "n": len(v)}


def luck_free_rate(season_plays, luck) -> float | None:
    """His yards a play this season with the luck taken out: each play counted at most
    the luck line, or -- when he has too few plays for one -- his longest play left out."""
    v = [float(x) for x in (season_plays or []) if x == x]
    if not v or not luck:
        return None
    if luck["own"]:
        return sum(min(x, luck["cap"]) for x in v) / len(v)
    return (sum(v) - max(v)) / (len(v) - 1) if len(v) >= 2 else None


def luck_words(luck, unit) -> str:
    """How the report names the luck line it used."""
    if not luck:
        return ""
    plural = f"{unit}es" if unit == "catch" else f"{unit}s"
    if luck["own"]:
        return (f"every {unit} past {luck['cap']:.0f} yards, his own {LUCK_PCT}th percentile over "
                f"{luck['n']} {plural}, counted as {luck['cap']:.0f}")
    return f"his longest {unit} left out ({luck['n']} {plural} of his own is too few for a percentile)"


# display bands for the gauge, picked, not measured: projected volume within 15% of what
# the yards line takes reads "about what it takes"
GAUGE_BAND = 0.15
SINGULAR = {"catches": "catch", "carries": "carry"}


def volume_gauge(y_min, rate, proj, unit, low_volume):
    """The achievability gauge (DECISIONS #166): the volume the yards line takes at a
    typical yards a play (long plays capped, so one breakaway does not set the bar),
    against the volume we project. Volume times rate is an AVERAGE game and averages are
    pulled up by big games, so the gauge is phrased as volume needed vs projected and
    never as "his usual game clears it". Description, not a price."""
    ok = lambda v: v is not None and v == v
    if not (ok(rate) and ok(proj)) or rate <= 0 or proj <= 0:
        return None
    need = y_min / float(rate)
    ratio = float(proj) / need
    word = ("comfortably more than it takes" if ratio >= 1 + GAUGE_BAND
            else "fewer than it takes" if ratio <= 1 - GAUGE_BAND else "about what it takes")
    return {"need": need, "proj": float(proj), "ratio": ratio, "word": word, "unit": unit,
            "low": float(proj) < low_volume}


def gauge_sentence(g, rate, per, luck_clause, y_min, long_word):
    """'At 4.4 yards a carry with the luck taken out (<how>), 90 yards takes about ...'."""
    if not g:
        return None
    how = f"with the luck taken out ({luck_clause})" if luck_clause else "(our figure for him)"
    s = (f"At {rate:.1f} yards a {per} {how}, {y_min} yards takes about {g['need']:.1f} {g['unit']}; "
         f"we project {g['proj']:.1f}, {g['word']}")
    if g["word"] == "fewer than it takes":
        s += f": the Over needs more {g['unit']} or {long_word}"
    s += "."
    if g["low"]:
        s += f" At this little volume one {SINGULAR.get(g['unit'], g['unit'])} either way decides it."
    return s


# Sleeper's lines that are read beside the priced ones, never priced (DECISIONS #164, #166)
EXTRA_KINDS = ("longest_reception", "longest_rush", "rushing_attempts")


def extra_lines(markets, players, teams, kinds=EXTRA_KINDS) -> list[dict]:
    """Sleeper's unpriced lines for this game: [{name, team, kind, line, mult_over,
    mult_under}] (a list, so the scenario snapshot can store it as JSON). markets =
    Sleeper's available-lines feed and players its player map, both fetched by
    score_game; teams = the two Sleeper team codes. Read beside the catches, carries
    and yards lines only; never priced."""
    out = []
    for m in markets or []:
        if (m.get("sport") != "nfl" or m.get("wager_type") not in kinds
                or m.get("line_type", "normal") != "normal"):
            continue
        opts = m.get("options") or []
        if not opts or opts[0].get("subject_team") not in teams or opts[0].get("game_status") != "pre_game":
            continue
        info = players.get(m.get("subject_id"), {})
        name = info.get("full_name") or f'{info.get("first_name", "")} {info.get("last_name", "")}'.strip()
        side = lambda o_: next((o for o in opts if o.get("outcome") == o_ and o.get("status") == "active"), None)
        over, under = side("over"), side("under")
        if name and over is not None:
            out.append({"name": name, "team": opts[0]["subject_team"], "kind": m["wager_type"],
                        "line": float(over["outcome_value"]),
                        "mult_over": float(over["payout_multiplier"]) if over.get("payout_multiplier") else None,
                        "mult_under": (float(under["payout_multiplier"])
                                       if under is not None and under.get("payout_multiplier") else None)})
    return out


def extra_index(extra, sleeper_team=None) -> dict:
    """extra_lines rows keyed for lookup: {(kind, norm_name, OUR team code): row}.
    sleeper_team maps our codes to Sleeper's ({"LA": "LAR"}); the index turns
    Sleeper's back into ours so callers look up with the code the report uses."""
    back = {v: k for k, v in (sleeper_team or {}).items()}
    return {(x["kind"], MODEL.norm_name(x["name"]), back.get(x["team"], x["team"])): x for x in extra or []}


def extra_summary(extra) -> str:
    """The sources-table detail for the unpriced lines: a count per kind."""
    if not extra:
        return "none posted for this game"
    n = {}
    for x in extra:
        n[x["kind"]] = n.get(x["kind"], 0) + 1
    words = {"longest_reception": "longest catch", "longest_rush": "longest run", "rushing_attempts": "carries"}
    return ", ".join(f"{words.get(k, k)} {v}" for k, v in sorted(n.items()))


def favoured(mult_over, mult_under, gap=0.05):
    """Which side of a Sleeper line the book favours, from its payout multipliers:
    the side paying less, when the two differ by more than `gap`; None when even."""
    ok = lambda v: v is not None and v == v
    if not (ok(mult_over) and ok(mult_under)) or abs(mult_over - mult_under) <= gap:
        return None
    return "Under" if mult_under < mult_over else "Over"


def catch_yards_read(catches_line=None, yards_line=None, season_rec=None, season_yds=None,
                     model_ypc=None, longest_line=None, season_luckfree_ypc=None,
                     proj_catches=None, luck=None) -> dict | None:
    """How the book's catches, receiving-yards and longest-catch lines fit together
    (DECISIONS #164). Every line is a half-point step, so each Over is read at the
    whole number that wins it: 3.5 catches and 44.5 yards mean 4 catches for 45.
    need_ypc is what those 4 catches must average to clear the yards (both Overs at
    the minimum -- the fact behind stacking one player's two legs). mid_ypc = yards
    line / catches line is the book's own yards a catch, and the read compares it
    with OUR yards a catch for him (the blended estimate: a raw season figure on 15
    catches carries a standard error near 2.5 yards, wider than the band). His season
    figure is context, used only when we have none, shown beside its capped version
    (season_luckfree_ypc: research.luck_free_rate). A
    longest-catch line of 17.5 means
    one catch of 18; rest_ypc is what the other catches must average if he gets
    exactly that one. Nothing here is a model price."""
    ok = lambda v: v is not None and v == v
    if not ok(yards_line):
        return None
    y_min = to_clear(yards_line)
    out = {"yards_line": float(yards_line), "y_min": y_min, "catches_line": None, "c_min": None,
           "need_ypc": None, "mid_ypc": None, "season_ypc": None, "season_rec": None, "model_ypc": None,
           "ref": None, "longest_line": None, "long_min": None, "long_share": None, "rest_ypc": None,
           "read": None, "season_ypc_cap": None, "gauge": None, "gauge_rate": None, "luck": luck}
    if ok(season_rec) and ok(season_yds) and season_rec >= YPC_MIN_CATCHES:
        out.update(season_ypc=float(season_yds) / float(season_rec), season_rec=int(season_rec))
        if ok(season_luckfree_ypc):
            out["season_ypc_cap"] = float(season_luckfree_ypc)
    if ok(model_ypc) and model_ypc > 0:
        out["model_ypc"] = float(model_ypc)
    if ok(catches_line) and float(catches_line) > 0:
        c_min = to_clear(catches_line)
        out.update(catches_line=float(catches_line), c_min=c_min, need_ypc=y_min / c_min,
                   mid_ypc=float(yards_line) / float(catches_line))
    if ok(longest_line):
        l_min = to_clear(longest_line)
        out.update(longest_line=float(longest_line), long_min=l_min, long_share=l_min / y_min)
        if out["c_min"] and out["c_min"] >= 2 and l_min < y_min:
            out["rest_ypc"] = (y_min - l_min) / (out["c_min"] - 1)
    out["ref"] = ("model" if out["model_ypc"] is not None
                  else "season" if out["season_ypc"] is not None else None)
    rate = out["season_ypc_cap"] if out["season_ypc_cap"] is not None else out["model_ypc"]
    if rate is not None:
        out.update(gauge_rate=rate, gauge=volume_gauge(y_min, rate, proj_catches, "catches", 3.0))
    ref = out["model_ypc"] if out["ref"] == "model" else out["season_ypc"]
    if out["mid_ypc"] is not None and ref is not None:
        gap = out["mid_ypc"] - ref
        out["read"] = ("yards line rich" if gap >= YPC_BAND
                       else "yards line lean" if gap <= -YPC_BAND else "about even")
    return out


def catch_yards_sentence(d) -> str | None:
    """The report's one-paragraph read of catch_yards_read."""
    if not d or (d["need_ypc"] is None and d["long_min"] is None and d.get("gauge") is None):
        return None
    bits = []
    if d["need_ypc"] is not None:
        s = f"The lines ask {d['mid_ypc']:.1f} yards a catch ({d['yards_line']:g} over {d['catches_line']:g})"
        his = []
        if d["model_ypc"] is not None:
            his.append(f"we expect {d['model_ypc']:.1f} from him")
        if d["season_ypc"] is not None:
            h = f"he has {d['season_ypc']:.1f} this season on {d['season_rec']} catches"
            if d["season_ypc_cap"] is not None:
                h += f" ({d['season_ypc_cap']:.1f} with the luck taken out)"
            his.append(h)
        bits.append(s + (f"; {', '.join(his)}" if his else "") + ".")
        ours = "ours" if d["ref"] == "model" else "his season figure"
        if d["read"] == "yards line rich":
            bits.append(f"That is more per catch than {ours}: past the catches line, his yards Over still needs "
                        "an extra catch or a long play.")
        elif d["read"] == "yards line lean":
            bits.append(f"That is less per catch than {ours}: if he clears the catches line, the yards line "
                        "usually comes with it.")
        elif d["read"] == "about even":
            bits.append(f"That is about {ours}: the two lines ask the same of him.")
        bits.append(f"Both Overs at the minimum -- {d['c_min']} catches for {d['y_min']} yards -- "
                    f"need {d['need_ypc']:.1f} a catch.")
    if d.get("gauge") is not None:
        lc = luck_words(d.get("luck"), "catch") if d["season_ypc_cap"] is not None else None
        bits.append(gauge_sentence(d["gauge"], d["gauge_rate"], "catch", lc, d["y_min"], "a long catch"))
    if d["long_min"] is not None:
        if d["long_min"] >= d["y_min"]:
            bits.append(f"The longest-catch line ({d['longest_line']:g}) sits at or above his yards line: "
                        "the book sees one catch carrying all of his yards.")
        else:
            s = (f"The longest-catch line ({d['longest_line']:g}) means one catch of {d['long_min']}, "
                 f"{100 * d['long_share']:.0f}% of the {d['y_min']} yards")
            if d["rest_ypc"] is not None:
                n_ = d["c_min"] - 1
                s += (f"; with that one, his other catch needs {d['rest_ypc']:.1f}" if n_ == 1 else
                      f"; with that one, his other {n_} catches need {d['rest_ypc']:.1f} each")
            bits.append(s + ".")
    return " ".join(bits)


# yards a carry within this much of ours reads "about even": a display band, picked, not
# measured, tighter than receiving because a carry gains about a third of a catch
RUN_BAND = 0.5
RUN_MIN_CARRIES = 10      # context only (it carries no verdict), always shown with its count


def carry_yards_read(carries_line=None, yards_line=None, model_ypc=None, proj_carries=None,
                     season_car=None, season_yds=None, season_luckfree_ypc=None, longest_line=None,
                     carries_fav=None, luck=None) -> dict | None:
    """The runner's version of catch_yards_read (DECISIONS #166): the book's carries,
    rushing-yards and longest-run lines read together at the whole numbers that win
    them, against OUR yards a carry. His season figure is shown with its count and a
    warning: three games of yards a carry predicted later games WORSE than the league
    average in 2022-25, raw, capped or without the longest run alike
    (reports/robust_ypc_check.md). The book's carries line is shown beside our
    projected carries, with the side it favours."""
    ok = lambda v: v is not None and v == v
    if not ok(yards_line):
        return None
    y_min = to_clear(yards_line)
    out = {"yards_line": float(yards_line), "y_min": y_min, "carries_line": None, "c_min": None,
           "carries_fav": carries_fav, "proj_carries": float(proj_carries) if ok(proj_carries) else None,
           "need_ypc": None, "mid_ypc": None, "model_ypc": None, "season_ypc": None, "season_car": None,
           "season_ypc_cap": None, "gauge": None, "gauge_rate": None, "luck": luck,
           "longest_line": None, "long_min": None,
           "long_share": None, "rest_ypc": None, "read": None}
    if ok(model_ypc) and model_ypc > 0:
        out["model_ypc"] = float(model_ypc)
    if ok(season_car) and ok(season_yds) and season_car >= RUN_MIN_CARRIES:
        out.update(season_ypc=float(season_yds) / float(season_car), season_car=int(season_car))
        if ok(season_luckfree_ypc):
            out["season_ypc_cap"] = float(season_luckfree_ypc)
    if ok(carries_line) and float(carries_line) > 0:
        c_min = to_clear(carries_line)
        out.update(carries_line=float(carries_line), c_min=c_min, need_ypc=y_min / c_min,
                   mid_ypc=float(yards_line) / float(carries_line))
    if ok(longest_line):
        l_min = to_clear(longest_line)
        out.update(longest_line=float(longest_line), long_min=l_min, long_share=l_min / y_min)
        if out["c_min"] and out["c_min"] >= 2 and l_min < y_min:
            out["rest_ypc"] = (y_min - l_min) / (out["c_min"] - 1)
    rate = out["season_ypc_cap"] if out["season_ypc_cap"] is not None else out["model_ypc"]
    if rate is not None:
        out.update(gauge_rate=rate, gauge=volume_gauge(y_min, rate, out["proj_carries"], "carries", 6.0))
    if out["mid_ypc"] is not None and out["model_ypc"] is not None:
        gap = out["mid_ypc"] - out["model_ypc"]
        out["read"] = ("yards line rich" if gap >= RUN_BAND
                       else "yards line lean" if gap <= -RUN_BAND else "about even")
    return out


def carry_yards_sentence(d) -> str | None:
    """The report's one-paragraph read of carry_yards_read."""
    if not d or (d["carries_line"] is None and d["long_min"] is None and d.get("gauge") is None):
        return None
    bits = []
    if d["carries_line"] is not None:
        fav = f", {d['carries_fav']} favoured" if d["carries_fav"] else ""
        we = f"; we project {d['proj_carries']:.1f}" if d["proj_carries"] is not None else ""
        bits.append(f"The book's carries line is {d['carries_line']:g}{fav}{we}.")
        s = f"The lines ask {d['mid_ypc']:.1f} yards a carry ({d['yards_line']:g} over {d['carries_line']:g})"
        his = []
        if d["model_ypc"] is not None:
            his.append(f"we expect {d['model_ypc']:.1f}")
        if d["season_ypc"] is not None:
            h = f"he has {d['season_ypc']:.1f} this season on {d['season_car']} carries"
            if d["season_ypc_cap"] is not None:
                h += f" ({d['season_ypc_cap']:.1f} with the luck taken out)"
            his.append(h + " -- mostly noise this early: the league average predicts later games better")
        bits.append(s + (f"; {', '.join(his)}" if his else "") + ".")
        if d["read"] == "yards line rich":
            bits.append("That is more per carry than ours: past the carries line, his yards Over still needs "
                        "extra carries or a long run.")
        elif d["read"] == "yards line lean":
            bits.append("That is less per carry than ours: if he clears the carries line, the yards usually "
                        "come with it, so his yards Over is mostly a bet on the carries.")
        elif d["read"] == "about even":
            bits.append("That is about ours: his yards Over is a bet on the carries.")
        bits.append(f"Both Overs at the minimum -- {d['c_min']} carries for {d['y_min']} yards -- "
                    f"need {d['need_ypc']:.1f} a carry.")
    if d.get("gauge") is not None:
        lc = luck_words(d.get("luck"), "run") if d["season_ypc_cap"] is not None else None
        bits.append(gauge_sentence(d["gauge"], d["gauge_rate"], "carry", lc, d["y_min"], "a long run"))
    if d["long_min"] is not None:
        if d["long_min"] >= d["y_min"]:
            bits.append(f"The longest-run line ({d['longest_line']:g}) sits at or above his yards line: "
                        "the book sees one run carrying all of his yards.")
        else:
            s = (f"The longest-run line ({d['longest_line']:g}) means one run of {d['long_min']}, "
                 f"{100 * d['long_share']:.0f}% of the {d['y_min']} yards")
            if d["rest_ypc"] is not None:
                n_ = d["c_min"] - 1
                s += (f"; with that one, his other carry needs {d['rest_ypc']:.1f}" if n_ == 1 else
                      f"; with that one, his other {n_} carries need {d['rest_ypc']:.1f} each")
            bits.append(s + ".")
    return " ".join(bits)


# a questionable player worth a flag on his teammates' rows, priced or not (DECISIONS #163)
WATCH_TARGET_SHARE, WATCH_CARRY_SHARE, WATCH_SNAPS = 0.05, 0.10, 0.30


def worth_watching(target_share=None, carry_share=None, snap_share=None) -> bool:
    """A questionable player whose absence would move his teammates' work: 5%+ of
    the targets, 10%+ of the carries or 30%+ of the snaps this season. Lower than
    the pricing rule on purpose -- a TE2 with 10% of the targets (Noah Fant, NO
    week 4) is not priced but his status still nudges the TE1."""
    v = lambda x: x is not None and x == x
    return ((v(target_share) and target_share >= WATCH_TARGET_SHARE)
            or (v(carry_share) and carry_share >= WATCH_CARRY_SHARE)
            or (v(snap_share) and snap_share >= WATCH_SNAPS))


def watch_applies(absent_pos, market, row_pos) -> bool:
    """Which rows a questionable teammate's flag belongs on: a QB on every row; a
    back on rushing rows and other backs' receiving rows; a receiver or tight end on
    receiving rows. His position first -- that is who absorbs the work."""
    a = str(absent_pos or "").upper()
    if a == "QB":
        return True
    if a in ("RB", "FB", "HB"):
        return market == "player_rush_yds" or str(row_pos).upper() in ("RB", "FB", "HB")
    if a in ("WR", "TE"):
        return market in ("player_receptions", "player_reception_yds")
    return False


def usage_change(weeks):
    """weeks: list of (week, snap_share, target_share, carry_share[, targets,
    carries]), sorted, the player's weeks before this one with this team. LAST
    = the latest week, BASE = the mean of the earlier ones (at least two). With
    the counts, tn / cn are last game's targets and carries and tn_base /
    cn_base the earlier weeks' per-game average. None when too few weeks."""
    if len(weeks) < 3:
        return None
    last = weeks[-1]
    base = weeks[:-1]
    mean = lambda i: float(np.nanmean([w[i] for w in base]))
    out = {"week": int(last[0]),
           "snap": last[1], "snap_base": mean(1),
           "ts": last[2], "ts_base": mean(2),
           "cs": last[3], "cs_base": mean(3)}
    if all(len(w) >= 6 for w in weeks):
        out.update(tn=float(last[4]), tn_base=mean(4), cn=float(last[5]), cn_base=mean(5))
    return out


def role_flag(u, last_week_expected):
    """The role-shift flag (reports/role_shift_check.md), or None. It needs last
    week to be the week before this one. Since round 23 (model.SNAP_REACT) the
    projection already moves his target share for this; the flag points the
    research at the role change, it no longer claims the model misses it."""
    if u is None or u["week"] != last_week_expected:
        return None
    if not (u["snap_base"] >= 0.05):
        return None     # the snap rule does not act below 5% of earlier snaps; neither does the flag
    d_snap = u["snap"] - u["snap_base"]
    d_ts = u["ts"] - u["ts_base"]
    if d_snap >= SNAP_JUMP and d_ts < SHARE_LAG:
        return ("role up", "snaps jumped while his targets lagged; the projection already raises his "
                           "target share for it (snap-change rule)")
    if d_snap <= -SNAP_JUMP and d_ts > -SHARE_LAG:
        return ("role down", "snaps fell while his targets held; the projection already lowers his "
                             "target share for it (snap-change rule)")
    return None


# reports/rb_takeover_check.md: fixed before the check, earned for backs on carries
CARRY_JUMP = 0.20


def carry_change(weeks):
    """The backfield flag's inputs, on the TESTED definition
    (reports/rb_takeover_check.md): only weeks in which he carried. weeks:
    usage_change's tuples with the counts (week, snap, ts, cs, targets,
    carries). Returns {week, cs, cs_base} or None (fewer than three carry weeks)."""
    w = [x for x in weeks if len(x) >= 6 and x[5] and x[5] > 0]
    if len(w) < 3:
        return None
    return {"week": int(w[-1][0]), "cs": float(w[-1][3]),
            "cs_base": float(np.nanmean([x[3] for x in w[:-1]]))}


def carry_flag(u, last_week_expected):
    """The backfield flag (reports/rb_takeover_check.md), or None: his carry share
    last week against his earlier weeks. A takeover (+20 points or more) beat the
    model's carry projection by about two carries the next week in 2022-25; a
    demotion missed it by about two. Needs last week to be the week before this one."""
    if u is None or u["week"] != last_week_expected:
        return None
    cs, base = u.get("cs"), u.get("cs_base")
    if cs is None or base is None or cs != cs or base != base:
        return None
    if cs - base >= CARRY_JUMP:
        return ("carries up", "his share of the carries jumped last week; backs who take over a backfield got about "
                              "two more carries than the model projected the next week (2022-25)")
    if cs - base <= -CARRY_JUMP:
        return ("carries down", "his share of the carries fell last week; backs who lose the job got about two "
                                "fewer carries than the model projected the next week (2022-25)")
    return None


def backfield_jobs(weeks):
    """A back's three jobs, last game against his earlier weeks. weeks: sorted
    list of (week, early-down carry share, passing-down target share, inside-5
    carry share, inside-5 carries, team inside-5 carries) for the weeks he
    played this season with this team. Passing downs are 3rd/4th down or the
    last two minutes of a half. None with fewer than three weeks (the same
    LAST/BASE as usage_change)."""
    if len(weeks) < 3:
        return None
    last, base = weeks[-1], weeks[:-1]
    mean = lambda i: float(np.nanmean([w[i] for w in base])) if any(np.isfinite(w[i]) for w in base) else np.nan
    return {"week": int(last[0]),
            "early": last[1], "early_base": mean(1),
            "passdown": last[2], "passdown_base": mean(2),
            "i5": last[3], "i5_base": mean(3),
            "i5_n": int(last[4]), "i5_team": int(last[5])}
