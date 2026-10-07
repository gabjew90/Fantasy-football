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
    """The research table's 'Pays at this price if you expect' cell: the Over beats
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
                    per_catch_shape, width=None, prices=None, role=None):
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
    # round 41: the role's own yards shape; the share is moved explicitly here, so a role
    # share multiplier (applied to the projection itself) never enters the search
    w_s = {**(width or {}), "te_share_mult": None}

    def sim(k):      # common random numbers: one generator per k, cached
        if k not in cache:
            s = min(share * k, 0.95)
            out, _ = MODEL.simulate_team_game(np.random.default_rng(SEED), N_SEARCH, team_targets_mean,
                                              targets_r, {"p": s}, {"p": catch_rate}, {"p": ypt},
                                              per_catch_shape, other_bucket=True, width=w_s,
                                              player_roles={"p": role})
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
# a play past the player's OWN 97.5th percentile for that prop over his last LUCK_WINDOW games
# -- his catches for receiving yards, his runs for rushing yards -- counts as a lucky
# breakaway and is counted at that line (user, 2026-10-05, after trying the 95th and 99th: the
# 95th cut a back's ordinary 15-25-yard runs, which come most games). "Too few" = under
# LUCK_MIN_PLAYS of his plays of that kind in the window; then his longest play is left out
# instead. At 20 plays the 97.5th sits at about his longest play. A definition for a
# descriptive gauge, not a fit (reports/robust_ypc_check.md, for reference only)
LUCK_PCT = 97.5
LUCK_MIN_PLAYS = 20
# the luck-free check (luck line AND rate) reads his last this-many games, crossing into
# last season while this one is short (user, 2026-10-05)
LUCK_WINDOW = 10
QB_MIN_COMPLETIONS = 20
# a QB game with fewer completions than this is a cameo (relief, garbage time) and stays out of
# his window, so "his last 10 games" are games he played as the passer
QB_CAMEO_COMPLETIONS = 5


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


def luck_for(prior_games, current_games, gid, kind, window=LUCK_WINDOW):
    """(luck line, luck-free rate) for one player and kind ("catch" | "run") over his
    last `window` games: prior_games = {(gsis_id, kind): [[yards], ...]} oldest first
    (last season's final games, priors_*_play_yards.csv), current_games = {gsis_id:
    [[yards], ...]} this season, oldest first. Both the line and the rate read the same
    window; the returned line carries `games`, the number of games in it."""
    games = list(prior_games.get((gid, kind), []) or []) + list(current_games.get(gid, []) or [])
    if kind == "pass":
        games = [g for g in games if len(g) >= QB_CAMEO_COMPLETIONS]
    games = games[-window:]
    plays = [y for g in games for y in g]
    luck = dict(player_luck_line(plays), games=len(games))
    min_plays = {"catch": YPC_MIN_CATCHES, "run": RUN_MIN_CARRIES, "pass": QB_MIN_COMPLETIONS}[kind]
    return luck, (luck_free_rate(plays, luck) if len(plays) >= min_plays else None)


def games_by_player(df, pid, y) -> dict:
    """{gsis_id: [[yards], ...]} oldest week first, one list per week he had a play in
    df. df needs week, pid and y columns."""
    d = df[df[y].notna() & df[pid].notna()]
    return {str(g): [[float(v) for v in x[x.week == w][y]] for w in sorted(x.week.unique())]
            for g, x in d.groupby(pid)}


def luck_words(luck, unit) -> str:
    """How the report names the luck line it used."""
    if not luck:
        return ""
    plural = {"catch": "catches", "run": "runs", "completion": "completions"}.get(unit, f"{unit}s")
    if luck["own"]:
        return (f"every {unit} past {luck['cap']:.0f} yards, his own {LUCK_PCT}th percentile over his last "
                f"{luck.get('games', '?')} games with a {unit} ({luck['n']} {plural}), counted as {luck['cap']:.0f}")
    return (f"his longest {unit} left out -- only {luck['n']} {plural} in his last {luck.get('games', '?')} "
            f"games with a {unit}, too few for a percentile")


# display bands for the gauge, picked, not measured: projected volume within 15% of what
# the yards line takes reads "about what it takes"
GAUGE_BAND = 0.15
SINGULAR = {"catches": "catch", "carries": "carry", "completions": "completion"}


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


def gauge_sentence(g, rate, per, luck_clause, y_min, long_word, book_line=None, book_fav=None, book_fair=None):
    """'At 4.4 yards a carry with the luck taken out (<how>), 90 yards takes about 20.6
    carries; we project 17.5 (our volume), about what it takes. The book's own carries line
    is 19.5, Under favoured: fewer than the yards line takes, so even the book's volume
    falls short without a long run.' The book's volume line is quoted whenever it exists
    (DECISIONS #167), so the reader sees whose volume each number is."""
    if not g:
        return None
    how = f"with the luck taken out ({luck_clause})" if luck_clause else "(our figure for him)"
    s = (f"At {rate:.1f} yards a {per} {how}, {y_min} yards takes about {g['need']:.1f} {g['unit']}; "
         f"we project {g['proj']:.1f} (our volume), {g['word']}")
    if g["word"] == "fewer than it takes":
        s += f": the Over needs more {g['unit']} or {long_word}"
    s += "."
    if book_line is not None and book_line == book_line:
        fav = f", {book_fav} favoured" if book_fav else ""
        fair = f" (a coin flip at about {book_fair:.1f})" if book_fair is not None and book_fair == book_fair else ""
        s += f" The book's own {g['unit']} line is {book_line:g}{fav}{fair}: "
        # lines move in halves: within half a unit of the book's line is the book's volume
        if g["need"] > book_line + 0.5:
            s += f"fewer than the yards line takes, so even the book's volume falls short without {long_word}."
        elif g["need"] < book_line - 0.5:
            s += "the yards line takes less than the book's own volume."
        else:
            s += "about what the yards line takes."
    else:
        s += f" The book posts no {g['unit']} line for him, so this is against our volume only."
    if g["low"]:
        s += f" At this little volume one {SINGULAR.get(g['unit'], g['unit'])} either way decides it."
    return s


def fair_over(mult_over=None, mult_under=None, price_over=None, price_under=None) -> float | None:
    """The book's chance of the Over with its cut removed, from Sleeper's payout multipliers
    (1 / multiplier) or American prices (breakeven), scaled so the two sides add to 1."""
    ok = lambda v: v is not None and v == v
    if ok(mult_over) and ok(mult_under) and mult_over > 1 and mult_under > 1:
        o, u = 1.0 / float(mult_over), 1.0 / float(mult_under)
    else:
        o, u = breakeven(price_over), breakeven(price_under)
        if o is None or u is None:
            return None
    return o / (o + u)


def fair_volume(line, p_over, sd) -> float | None:
    """The volume at which the book's own price is a coin flip (DECISIONS #172): the line
    moved by sd x the normal quantile of its no-vig Over chance. sd is the game-to-game
    spread of that player's volume in our simulation."""
    from statistics import NormalDist
    ok = lambda v: v is not None and v == v
    if not (ok(line) and ok(p_over) and ok(sd)) or not 0 < p_over < 1 or sd <= 0:
        return None
    return float(line) + float(sd) * NormalDist().inv_cdf(float(p_over))


# a game state: leading or trailing by this many points or more at the snap (one score = 8)
SCRIPT_MARGIN = 8


def team_volume(pbp, team) -> list[dict]:
    """One row per game this season for `team` (DECISIONS #172): opponent, score, pass
    attempts (sacks are not attempts), sacks, designed carries (kneel-downs and QB
    scrambles out), scrambles, targets (throws aimed at a receiver -- the unit the model
    counts) and the QB who threw most."""
    need = {"week", "posteam", "home_team", "away_team", "home_score", "away_score", "play_type"}
    if pbp is None or not need.issubset(pbp.columns):
        return []
    f0 = lambda s: s.fillna(0)
    rows = []
    for w, g in pbp[(pbp.home_team == team) | (pbp.away_team == team)].groupby("week"):
        home = g.home_team.iloc[0] == team
        us = g.home_score.max() if home else g.away_score.max()
        them = g.away_score.max() if home else g.home_score.max()
        o = g[g.posteam == team]
        sack = f0(o.get("sack", 0)) == 1 if "sack" in o else o.play_type.isna()
        scr = f0(o["qb_scramble"]) == 1 if "qb_scramble" in o else o.play_type.isna()
        kneel = f0(o["qb_kneel"]) == 1 if "qb_kneel" in o else o.play_type.isna()
        # a spike is play_type qb_spike: requiring a pass play keeps it out of the attempts
        att = ((f0(o["pass_attempt"]) == 1) if "pass_attempt" in o else True) & (o.play_type == "pass") & ~sack
        qb = (o.loc[att, "passer_player_name"].mode() if "passer_player_name" in o else pd_empty())
        run_ = (o.play_type == "run") & ~kneel & ~scr
        plays = att | sack | scr | run_
        diff = o["score_differential"] if "score_differential" in o else None
        state = {}
        for name, m in (("lead", diff >= SCRIPT_MARGIN), ("close", diff.abs() < SCRIPT_MARGIN),
                        ("trail", diff <= -SCRIPT_MARGIN)) if diff is not None else ():
            m = m.fillna(False) & plays
            state[name] = {"plays": int(m.sum()), "att": int((m & att).sum()), "runs": int((m & (run_ | scr)).sum())}
        n_ = int(plays.sum())
        rows.append({"week": int(w), "opp": ("vs " if home else "at ") + str(g.away_team.iloc[0] if home else g.home_team.iloc[0]),
                     "state": state,
                     "lead_share": (state["lead"]["plays"] / n_) if state and n_ else None,
                     "trail_share": (state["trail"]["plays"] / n_) if state and n_ else None,
                     "score": f"{int(us)}-{int(them)}" if us == us and them == them else "",
                     "margin": (float(us) - float(them)) if us == us and them == them else None,
                     "att": int(att.sum()), "sacks": int(sack.sum()),
                     "carries": int(((o.play_type == "run") & ~kneel & ~scr).sum()), "scrambles": int(scr.sum()),
                     "targets": int(((o.play_type == "pass") & o.get("receiver_player_id", o.play_type).notna()).sum())
                     if "receiver_player_id" in o else None,
                     "qb": str(qb.iat[0]) if len(qb) else ""})
    return rows


def pd_empty():
    import pandas as _pd
    return _pd.Series([], dtype=object)


# a team's pass share in a game state is blended toward the league's with this many plays
# of weight: a display choice (picked, not fitted) so 17 plays ahead never set the split
SCRIPT_PRIOR_PLAYS = 60


def league_script_shares(pbp) -> dict:
    """The league's pass attempts / (attempts + runs) in each game state this season."""
    need = {"posteam", "play_type", "score_differential"}
    if pbp is None or not need.issubset(pbp.columns):
        return {}
    f0 = lambda c: pbp[c].fillna(0) if c in pbp else 0
    sack = f0("sack") == 1
    scr = f0("qb_scramble") == 1
    kneel = f0("qb_kneel") == 1
    att = ((f0("pass_attempt") == 1) if "pass_attempt" in pbp else True) & (pbp.play_type == "pass") & ~sack
    runs = ((pbp.play_type == "run") & ~kneel) | scr
    d = pbp.score_differential
    out = {}
    for name, m in (("lead", d >= SCRIPT_MARGIN), ("close", d.abs() < SCRIPT_MARGIN), ("trail", d <= -SCRIPT_MARGIN)):
        m = m.fillna(False) & pbp.posteam.notna()
        a, u = int((m & att).sum()), int((m & runs).sum())
        if a + u:
            out[name] = a / (a + u)
    return out


LINE_BUCKETS = ("big favourite", "favourite", "close", "underdog", "big underdog")


def line_bucket(team_spread) -> str | None:
    """The kind of pregame line a team played under; team_spread NEGATIVE = favoured."""
    if team_spread is None or team_spread != team_spread:
        return None
    v = -float(team_spread)
    return ("big favourite" if v >= 7 else "favourite" if v >= 3.5 else "big underdog" if v <= -7
            else "underdog" if v <= -3.5 else "close")


def league_state_mix(pbp) -> dict:
    """How a team's plays split between ahead / close / behind by SCRIPT_MARGIN, by the
    pregame line it played under (line_bucket), from this season's games league-wide:
    {bucket: {state: share}}. nflverse
    spread_line is the HOME team's margin (positive = home favoured)."""
    need = {"posteam", "home_team", "play_type", "score_differential", "spread_line"}
    if pbp is None or not need.issubset(pbp.columns):
        return {}
    f0 = lambda c: pbp[c].fillna(0) if c in pbp else 0
    plays = (((pbp.play_type == "run") & (f0("qb_kneel") != 1)) | (pbp.play_type == "pass")) & pbp.posteam.notna()
    d = pbp[plays]
    own = d.spread_line.where(d.posteam == d.home_team, -d.spread_line)       # positive = this team favoured
    bucket = own.apply(lambda v: None if v != v else line_bucket(-v))
    state = d.score_differential.apply(lambda v: None if v != v else "lead" if v >= SCRIPT_MARGIN
                                       else "trail" if v <= -SCRIPT_MARGIN else "close")
    out = {}
    for b in LINE_BUCKETS:
        s_ = state[bucket == b].dropna()
        if len(s_):
            vc = s_.value_counts(normalize=True)
            out[b] = {k: float(vc.get(k, 0.0)) for k in ("lead", "close", "trail")}
    s_ = state.dropna()
    if len(s_):
        vc = s_.value_counts(normalize=True)
        out["_all"] = {k: float(vc.get(k, 0.0)) for k in ("lead", "close", "trail")}
    return out


def script_rates(rows) -> dict:
    """His season's pass attempts and runs per play in each game state (ahead / close /
    behind by SCRIPT_MARGIN), pooled over his games: {state: (att_rate, run_rate, plays)}."""
    out = {}
    for st in ("lead", "close", "trail"):
        p = sum((r.get("state") or {}).get(st, {}).get("plays", 0) for r in rows)
        a = sum((r.get("state") or {}).get(st, {}).get("att", 0) for r in rows)
        u = sum((r.get("state") or {}).get(st, {}).get("runs", 0) for r in rows)
        if p:
            out[st] = (a / p, u / p, p)
    return out


def team_line(book_home_spread, is_home) -> float | None:
    """A team's own pregame line, NEGATIVE = favoured, from a book's home spread (NEGATIVE =
    home favoured: 'DAL -9.5')."""
    if book_home_spread is None or book_home_spread != book_home_spread:
        return None
    return float(book_home_spread) if is_home else -float(book_home_spread)


def expected_state(team_spread) -> str:
    """The game state the Vegas line points to for this team: a favourite by more than a
    field goal is expected to lead, an underdog by more than one to trail, else close.
    team_spread is the team's own line (negative = favoured)."""
    if team_spread is None or team_spread != team_spread:
        return "close"
    return "lead" if team_spread <= -3.5 else "trail" if team_spread >= 3.5 else "close"


def blended_share(att, runs, league_share, k=SCRIPT_PRIOR_PLAYS) -> float | None:
    """His pass share in a state, blended toward the league's with k plays of weight."""
    if league_share is None:
        return (att / (att + runs)) if att + runs else None
    return (att + k * league_share) / (att + runs + k)


def team_volume_check(rows, our_targets, our_runs, team_spread=None, league=None, mix=None) -> dict | None:
    """Our projection beside what the team has actually done: our targets turned into
    attempts at the team's own targets-per-attempt rate, our runs (which count scrambles,
    as the model does) against carries + scrambles. inside = within the range of his
    games this season."""
    if not rows:
        return None
    att = [r["att"] for r in rows]
    runs = [r["carries"] + r["scrambles"] for r in rows]
    tg = [r["targets"] for r in rows if r["targets"] is not None]
    rate = (sum(tg) / sum(att)) if tg and sum(att) else None
    our_att = (float(our_targets) / rate) if rate else None
    out = {"games": len(rows), "att_avg": sum(att) / len(att), "att_min": min(att), "att_max": max(att),
           "runs_avg": sum(runs) / len(runs), "runs_min": min(runs), "runs_max": max(runs),
           "our_att": our_att, "our_runs": float(our_runs), "target_rate": rate}
    out["att_inside"] = our_att is not None and min(att) - 0.5 <= our_att <= max(att) + 0.5
    out["runs_inside"] = min(runs) - 0.5 <= our_runs <= max(runs) + 0.5
    # the script Vegas expects: his own pass and run rate in that state, applied to our plays
    sr = script_rates(rows)
    st = expected_state(team_spread)
    league = league or {}
    out.update(rates=sr, state=st, script_att=None, script_runs=None, league=league, script_share=None)
    # a game is a mix of states: how teams under this kind of line spent their plays
    # (league_state_mix), each state at his own blended pass share
    shares = {}
    for s_ in ("lead", "close", "trail"):
        a_s = sum((r.get("state") or {}).get(s_, {}).get("att", 0) for r in rows)
        u_s = sum((r.get("state") or {}).get(s_, {}).get("runs", 0) for r in rows)
        shares[s_] = (blended_share(a_s, u_s, league.get(s_)), a_s + u_s)
    b_ = line_bucket(team_spread) or "close"
    # no game yet under this kind of line: every team's mix, never all snaps in one state
    w = (mix or {}).get(b_) or (mix or {}).get("_all")
    out["line_bucket"] = b_ if (mix or {}).get(b_) else ("all lines" if w else None)
    w = w or {}
    if w and all(shares[k][0] is not None for k in w if w[k] > 0):
        share = sum(w[k] * shares[k][0] for k in w if w[k] > 0) / sum(v for v in w.values() if v > 0)
    else:
        share = None
    out["state_mix"] = w
    out["state_shares"] = shares
    if share is not None and our_att is not None:
        plays = our_att + float(our_runs)
        out.update(script_share=share, script_plays=sum(n for _, n in shares.values()),
                   script_att=plays * share, script_runs=plays * (1 - share))
        out["script_inside"] = (min(att) - 0.5 <= out["script_att"] <= max(att) + 0.5
                                and min(runs) - 0.5 <= out["script_runs"] <= max(runs) + 0.5)
    return out


def team_volume_lines(team, rows, chk) -> list[str]:
    """The report's team-volume block: every game this season, then our projection
    beside the season, said plainly when it sits outside every game he has played."""
    if not rows:
        return []
    L = [f"**{team}** -- this season, game by game (attempts exclude sacks; carries are designed runs, "
         "QB scrambles counted apart):", "",
         "| Week | Opponent | Score | Plays ahead / behind by 8+ | Pass att | Sacks | Carries | Scrambles | QB |",
         "|---|---|---|---|---|---|---|---|---|"]
    pc = lambda v: "—" if v is None else f"{100 * v:.0f}%"
    for r in rows:
        L.append(f"| {r['week']} | {r['opp']} | {r['score']} | {pc(r.get('lead_share'))} / {pc(r.get('trail_share'))} | "
                 f"{r['att']} | {r['sacks']} | {r['carries']} | {r['scrambles']} | {r['qb']} |")
    if chk:
        L.append(f"| **Avg** | | | | **{chk['att_avg']:.1f}** | | **{chk['runs_avg'] - sum(r['scrambles'] for r in rows) / len(rows):.1f}** "
                 f"| {sum(r['scrambles'] for r in rows) / len(rows):.1f} | |")
        L.append("")
        a = (f"about {chk['our_att']:.0f} pass attempts" if chk["our_att"] is not None else "")
        s = (f"We project {a} ({chk['att_min']}-{chk['att_max']} in its games, {chk['att_avg']:.1f} a game) and "
             f"{chk['our_runs']:.0f} runs counting scrambles ({chk['runs_min']}-{chk['runs_max']}, {chk['runs_avg']:.1f} a game).")
        out_ = [w for w, ok in (("pass attempts", chk["att_inside"]), ("runs", chk["runs_inside"])) if not ok]
        if out_:
            s += (f" Our {' and '.join(out_)} sit outside every game this season -- the market's spread and total "
                  "pull them there; say why, or treat the player numbers built on them with care.")
        else:
            s += " Both sit inside the range of its games this season."
        L.append(s)
        sr = chk.get("rates") or {}
        words = {"lead": "ahead by 8+", "close": "within one score", "trail": "behind by 8+"}
        if sr:
            L.append("")
            L.append("Pass share of plays by game state this season: " + "; ".join(
                f"{words[k]} {100 * a / (a + u):.0f}% ({p} plays)" for k, (a, u, p) in sr.items()) + ".")
            lg = chk.get("league") or {}
            if lg:
                L.append("League this season: " + "; ".join(f"{words[k]} {100 * v:.0f}%" for k, v in lg.items()) + ".")
            if chk.get("script_att") is not None:
                lean = {"big favourite": "a favourite by 7+", "favourite": "a favourite by 3.5-7",
                        "close": "a line within 3", "underdog": "an underdog by 3.5-7",
                        "big underdog": "an underdog by 7+", "all lines": "any line (none yet under this one)"}.get(
                    chk.get("line_bucket"), "this line")
                mixw = chk.get("state_mix") or {}
                mixs = ", ".join(f"{100 * v:.0f}% {words[k]}" for k, v in mixw.items() if v > 0)
                s2 = (f"Teams playing as {lean} spent their plays {mixs} this season. At this team's own "
                      f"pass share in each state (blended toward the league's where its sample is small), that "
                      f"script is about {100 * chk['script_share']:.0f}% passes: our total plays would split into "
                      f"about {chk['script_att']:.0f} pass attempts and {chk['script_runs']:.0f} runs, against our "
                      f"{chk['our_att']:.0f} and {chk['our_runs']:.0f}.")
                if not chk.get("script_inside", True):
                    s2 += (" That split sits outside every game it has played this season, so read it as the "
                           "direction the script pushes, not a number.")
                L.append(s2)
    L.append("")
    return L


POS_GROUPS = ("RB", "WR", "TE")


def points_allowed(pbp, positions) -> dict:
    """PPR fantasy points each defence has allowed per game to RBs, WRs and TEs this
    season (DECISIONS #169): 1 a catch, 0.1 a receiving or rushing yard, 6 a receiving or
    rushing touchdown; QB kneel-downs out; fumbles and two-point plays not counted.
    positions = {gsis_id: position} (FB counts as RB). Returns {defteam: {pos: (ppg, rank)}}
    plus "_league": {pos: league mean ppg} and "_games": {defteam: games}; rank 1 = most
    allowed. Context for the narrative only: position matchups were tested as too noisy to
    move the model (methodology)."""
    need = {"game_id", "defteam", "play_type", "complete_pass", "receiver_player_id", "rusher_player_id",
            "receiving_yards", "rushing_yards", "pass_touchdown", "rush_touchdown"}
    if pbp is None or not need.issubset(pbp.columns) or not len(pbp):
        return {}
    pos = {k: ("RB" if v == "FB" else v) for k, v in positions.items()}
    f0 = lambda s: s.fillna(0).astype(float)
    rec = pbp[(pbp.play_type == "pass") & pbp.receiver_player_id.notna()]
    kneel = pbp["qb_kneel"] == 1 if "qb_kneel" in pbp else False
    run = pbp[(pbp.play_type == "run") & ~kneel & pbp.rusher_player_id.notna()]
    rows = [(rec.defteam, rec.receiver_player_id,
             f0(rec.complete_pass) + 0.1 * f0(rec.receiving_yards) + 6 * f0(rec.pass_touchdown)),
            (run.defteam, run.rusher_player_id, 0.1 * f0(run.rushing_yards) + 6 * f0(run.rush_touchdown))]
    import pandas as _pd
    a = _pd.concat([_pd.DataFrame({"defteam": d.values, "pid": p.values, "pts": x.values}) for d, p, x in rows])
    a["pos"] = a.pid.map(pos)
    unmapped = float(a.loc[a.pos.isna(), "pts"].clip(lower=0).sum())
    total = float(a.pts.clip(lower=0).sum())
    a = a[a.pos.isin(POS_GROUPS)]
    games = pbp.groupby("defteam").game_id.nunique()
    t = a.groupby(["defteam", "pos"]).pts.sum().unstack().reindex(columns=list(POS_GROUPS)).fillna(0.0)
    t = t.div(games.reindex(t.index), axis=0)
    rk = t.rank(ascending=False, method="min").astype(int)
    out = {d: {p: (float(t.loc[d, p]), int(rk.loc[d, p])) for p in POS_GROUPS} for d in t.index}
    out["_league"] = {p: float(t[p].mean()) for p in POS_GROUPS}
    out["_games"] = {d: int(games[d]) for d in t.index}
    out["_n"] = len(t.index)
    out["_unmapped_share"] = unmapped / total if total > 0 else 0.0
    return out


def points_allowed_line(pa, teams) -> str | None:
    """The game header's sentence: what each defence in this game allows by position."""
    if not pa or not all(t in pa for t in teams):
        return None
    n = pa["_n"]
    lg = pa["_league"]
    def word(rank):
        return ("most" if rank <= 8 else "fewest" if rank > n - 8 else "middle")
    parts = []
    for t in teams:
        bits = ", ".join(f"{p} {pa[t][p][0]:.1f} ({rank_words(pa[t][p][1], n)} of {n}"
                         + ("" if word(pa[t][p][1]) == "middle" else f", among the {word(pa[t][p][1])}") + ")"
                         for p in POS_GROUPS)
        parts.append(f"{t}'s defence allows {bits}")
    games = sorted(set(pa["_games"][t] for t in teams))
    return ("; ".join(parts) + ". League average: " + ", ".join(f"{p} {lg[p]:.1f}" for p in POS_GROUPS)
            + f". PPR points per game over {'/'.join(map(str, games))} games: a small sample, and position "
            "matchups were tested as too noisy to move the model, so this is context, not an adjustment."
            + (f" {100 * pa['_unmapped_share']:.0f}% of skill-player points league-wide belong to players the "
               "roster file gives no position, so these totals run a little low."
               if pa.get("_unmapped_share", 0) > 0.02 else ""))


def rank_words(rank: int, n: int, most: str = "most", fewest: str = "fewest") -> str:
    """A rank among n read the short way round: 3 of 32 -> '3rd most', 31 of 32 -> '2nd
    fewest' (the bottom half counted from the other end; ties share the lower rank)."""
    rank, n = int(rank), int(n)
    return f"{ordinal(rank)} {most}" if rank <= (n + 1) // 2 else f"{ordinal(n - rank + 1)} {fewest}"


def ordinal(n: int) -> str:
    """1 -> '1st', 2 -> '2nd', 11 -> '11th', 23 -> '23rd'."""
    n = int(n)
    suf = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suf}"


POS_WORD = {"RB": "running backs", "WR": "wide receivers", "TE": "tight ends"}


def matchup_sentence(pa, opp, pos) -> str | None:
    """One player's matchup line (user, 2026-10-06): the PPR points a game the opposing
    defence allows to his position and its rank, 1st = most allowed. None for a QB, an
    unknown position, or no numbers for that defence."""
    pos = "RB" if pos == "FB" else pos
    if not pa or opp not in pa or pos not in POS_GROUPS:
        return None
    ppg, rank = pa[opp][pos]
    return (f"{opp} allows {ppg:.1f} PPR points a game to {POS_WORD[pos]}, the {rank_words(rank, pa['_n'])} of "
            f"{pa['_n']} (league average {pa['_league'][pos]:.1f}; {pa['_games'][opp]} games). Context, "
            "not a price input: position matchups were tested as too noisy to move the model.")


def defense_metrics(pbp) -> dict:
    """Each defence's EPA and points per drive ALLOWED (team_efficiency by defteam)."""
    return team_efficiency(pbp, "defteam")


def offense_metrics(pbp) -> dict:
    """Each offence's EPA per play and points per drive GAINED (team_efficiency by posteam)."""
    return team_efficiency(pbp, "posteam")


def team_efficiency(pbp, side="defteam") -> dict:
    """Each team's EPA per play (all, passes, runs) and points per drive this season, as the
    defence (side "defteam": allowed) or the offence ("posteam": gained), with ranks
    (1st = most -- the softest defence, the best offence). Plays: dropbacks and runs with
    an EPA by nflfastR's pass / rush flags (scrambles are dropbacks; play_type when the
    flags are absent), kneel-downs and spikes out. Drives: nflverse's fixed_drive per game,
    points = the team with the ball's score at the drive's end minus its start (touchdowns
    with their extra point or two-point try, field goals). A defensive score on the drive is
    not the offence's and does not count; a kickoff or punt RETURN touchdown sits on the
    returning team's drive and does count. Every drive counts, end-of-half kneels included.
    Returns {defteam: {metric: (value, rank)}} plus "_league", "_games", "_n";
    {} when the play-by-play lacks the columns."""
    need = {"game_id", "defteam", "posteam", "play_type", "epa"}
    if pbp is None or not len(pbp) or not need.issubset(pbp.columns):
        return {}
    import pandas as _pd
    if {"pass", "rush"}.issubset(pbp.columns):
        # nflfastR's flags, the public EPA/play convention (rbsdm): a scramble is a dropback
        # (pass = 1), and a penalty snap that would have been a pass or run still counts
        is_pass, is_rush = pbp["pass"].fillna(0) == 1, pbp["rush"].fillna(0) == 1
    else:
        is_pass, is_rush = pbp.play_type.eq("pass"), pbp.play_type.eq("run")
    keep = (is_pass | is_rush) & pbp.epa.notna() & pbp[side].notna()
    if "qb_kneel" in pbp:
        keep &= pbp.qb_kneel.fillna(0) != 1
    if "qb_spike" in pbp:
        keep &= pbp.qb_spike.fillna(0) != 1
    plays = pbp[keep]
    m = _pd.DataFrame({"epa_play": plays.groupby(side).epa.mean(),
                       "epa_pass": plays[is_pass[keep]].groupby(side).epa.mean(),
                       "epa_rush": plays[is_rush[keep] & ~is_pass[keep]].groupby(side).epa.mean()})
    dcols = {"fixed_drive", "posteam_score", "posteam_score_post"}
    if dcols.issubset(pbp.columns):
        d = pbp[pbp.fixed_drive.notna() & pbp.posteam.notna() & pbp.defteam.notna()]
        g = d.groupby(["game_id", "fixed_drive"]).agg(team=(side, "first"),
                                                      start=("posteam_score", "first"),
                                                      end=("posteam_score_post", "last"))
        g["pts"] = (g.end - g.start).clip(lower=0)
        m["pts_drive"] = g.groupby("team").pts.mean()
    cols = [c for c in ("epa_play", "epa_pass", "epa_rush", "pts_drive") if c in m]
    rk = m[cols].rank(ascending=False, method="min")
    games = pbp.groupby(side).game_id.nunique()
    out = {t: {c: (float(m.loc[t, c]), int(rk.loc[t, c])) for c in cols if m.loc[t, c] == m.loc[t, c]}
           for t in m.index}
    out["_league"] = {c: float(m[c].mean()) for c in cols}
    out["_games"] = {t: int(games.get(t, 0)) for t in m.index}
    out["_n"] = len(m.index)
    return out


def defense_line(dm, teams, verb="allows") -> str | None:
    """The game header's defence read: EPA per play and points per drive each defence in
    this game allows, ranked 1st = most allowed. verb "gains" reads an offense_metrics dict
    the same way (1st = most gained)."""
    if not dm or not all(t in dm for t in teams):
        return None
    n, lg = dm["_n"], dm["_league"]
    lab = {"epa_play": "EPA a play", "epa_pass": "EPA a pass", "epa_rush": "EPA a run", "pts_drive": "points a drive"}
    # (EPA explained once, in the brief's unit table; "a pass" counts sacks and scrambles)
    fmt = lambda c, v: f"{v:+.2f}" if c.startswith("epa") else f"{v:.2f}"
    parts = []
    for t in teams:
        bits = ", ".join(f"{fmt(c, dm[t][c][0])} {lab[c]} ({ordinal(dm[t][c][1])})"
                         for c in lab if c in dm[t])
        parts.append(f"{t} {verb} {bits}")
    games = sorted(set(dm["_games"][t] for t in teams))
    return ("; ".join(parts) + ". League average: "
            + ", ".join(f"{fmt(c, lg[c])} {lab[c]}" for c in lab if c in lg)
            + f". Rank among {n} teams: 1st = most {'allowed' if verb == 'allows' else 'gained'}; over "
            f"{'/'.join(map(str, games))} games, from nflverse "
            "play-by-play (EPA is nflfastR's expected-points model). Context only: no price reads it.")


# ---- the matchup brief (user, 2026-10-06): tables first, read second ----
# Modelled on the user's TB at DAL brief: each section a small table the narrative then
# interprets. Context only: nothing below is a price input.
DEF_POS = {"DE", "DT", "NT", "DL", "LB", "ILB", "OLB", "MLB", "CB", "S", "SS", "FS", "DB"}
SCORE_EPA_WEIGHT = 2 / 3         # the unit score: two parts EPA per play, one part success rate


def unit_efficiency(pbp, wp_lo=0.10, wp_hi=0.90) -> dict:
    """Each team's EPA per play and success rate on dropbacks and runs, as the offence and
    as the defence (allowed), with garbage time removed (win probability wp_lo-wp_hi when
    the play-by-play carries it), plus neutral-situation pace (seconds between snaps on the
    same drive, quarters 1-3, score within 7). Ranks: offence 1st = best, defence 1st = most
    allowed, pace 1st = fastest. {} without EPA."""
    need = {"game_id", "posteam", "defteam", "epa"}
    if pbp is None or not len(pbp) or not need.issubset(pbp.columns):
        return {}
    import pandas as _pd
    f0 = lambda c: pbp[c].fillna(0) if c in pbp else _pd.Series(0, index=pbp.index)
    if {"pass", "rush"}.issubset(pbp.columns):
        is_pass, is_rush = f0("pass") == 1, (f0("rush") == 1) & (f0("pass") != 1)
    else:
        is_pass, is_rush = pbp.play_type.eq("pass"), pbp.play_type.eq("run")
    keep = (is_pass | is_rush) & pbp.epa.notna() & pbp.posteam.notna() & pbp.defteam.notna()
    keep &= (f0("qb_kneel") != 1) & (f0("qb_spike") != 1)
    filt = "all plays"
    if "wp" in pbp:
        keep &= pbp.wp.between(wp_lo, wp_hi)
        filt = f"win probability {100 * wp_lo:.0f}-{100 * wp_hi:.0f}%"
    d = pbp[keep].assign(_pass=is_pass[keep], _succ=(pbp.loc[keep, "success"] if "success" in pbp
                                                    else (pbp.loc[keep, "epa"] > 0).astype(float)))
    out = {"off": {}, "def": {}, "pace": {}, "_league": {}, "_filter": filt}
    for kind, m in (("pass", d._pass), ("run", ~d._pass)):
        x = d[m]
        out["_league"][kind] = (float(x.epa.mean()), float(x._succ.mean()))
        for side, key in (("off", "posteam"), ("def", "defteam")):
            g = x.groupby(key).agg(epa=("epa", "mean"), sr=("_succ", "mean"), n=("epa", "size"))
            er, sr = g.epa.rank(ascending=False, method="min"), g.sr.rank(ascending=False, method="min")
            for t, r in g.iterrows():
                out[side].setdefault(t, {})[kind] = (float(r.epa), int(er[t]), float(r.sr), int(sr[t]), int(r.n))
    out["_n"] = len(set(out["off"]) | set(out["def"]))
    # THE UNIT SCORE (user, 2026-10-06: "blend EPA and success into a score and tier it"):
    # each team's EPA per play and success rate standardised across the league and blended two
    # parts EPA to one part success (user, 2026-10-06: weight EPA more -- big plays count), then
    # put on a 50 +/- 10 scale (50 = league average, 10 = one standard deviation),
    # oriented so higher is better for offences AND defences (a defence allowing less scores high)
    out["score"] = {"off": {"pass": {}, "run": {}}, "def": {"pass": {}, "run": {}}}
    for side in ("off", "def"):
        for kind in ("pass", "run"):
            teams = [t for t, v in out[side].items() if kind in v]
            if len(teams) < 3:
                continue
            e = np.array([out[side][t][kind][0] for t in teams])
            r = np.array([out[side][t][kind][2] for t in teams])
            z = lambda a: (a - a.mean()) / a.std() if a.std() > 0 else a * 0.0
            comp = (SCORE_EPA_WEIGHT * z(e) + (1 - SCORE_EPA_WEIGHT) * z(r)) * (1 if side == "off" else -1)
            comp = z(comp)
            for t, c in zip(teams, comp):
                out["score"][side][kind][t] = float(50 + 10 * c)
    pc = {"game_seconds_remaining", "qtr", "score_differential", "play_id"}
    if pc.issubset(pbp.columns):
        q = pbp[(is_pass | is_rush) & pbp.posteam.notna()].sort_values(["game_id", "play_id"])
        drv = q["fixed_drive"] if "fixed_drive" in q else q["drive"] if "drive" in q else None
        same = (q.game_id.eq(q.game_id.shift()) & q.posteam.eq(q.posteam.shift())
                & (drv.eq(drv.shift()) if drv is not None else True))
        dt = q.game_seconds_remaining.shift() - q.game_seconds_remaining
        neutral = q.qtr.le(3) & q.score_differential.abs().le(7) & same & dt.between(1, 60)
        sec = dt[neutral].groupby(q.loc[neutral, "posteam"]).mean()
        rk = sec.rank(ascending=True, method="min")
        out["pace"] = {t: (float(v), int(rk[t])) for t, v in sec.items()}
    return out


TIER_STEPS = (0.5, 1, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10)
MAX_TIERS = 6
TIER_LETTERS = "SABCDF"          # user, 2026-10-06: S, A, B, C, D, F from the best band down


def tier_letter(k: int) -> str:
    """Band k (1 = best) as its letter; a letter always means the same band position, so a
    list whose spread needs only five bands has no F."""
    return TIER_LETTERS[min(max(int(k), 1), len(TIER_LETTERS)) - 1]


def tiers(values: dict, higher_is_better=True, max_tiers=MAX_TIERS, steps=TIER_STEPS) -> dict:
    """Equal-width tiers counted from the best team down (user, 2026-10-06). The width is the
    smallest round step that keeps the league inside max_tiers bands, so a tight league gets
    narrow bands and a spread-out one wide bands, and every band means the same number of
    points. Returns {"step", "n", "tier": {team: k}, "bands": [(k, lo, hi)]} with bands in
    the values' own units (1 = best)."""
    if not values:
        return {"step": None, "n": 0, "tier": {}, "bands": []}
    g = {t: (v if higher_is_better else -v) for t, v in values.items()}
    best, worst = max(g.values()), min(g.values())
    span = best - worst
    step = next((st for st in steps if span <= st * max_tiers), steps[-1])
    n = max(1, min(max_tiers, int(-(-span // step)) if span > 0 else 1))
    tier = {t: min(n, 1 + int((best - x) // step)) for t, x in g.items()}
    _values = dict(values)
    bands = []
    for k in range(1, n + 1):
        hi_g, lo_g = best - (k - 1) * step, best - k * step
        if k == n:
            lo_g = min(lo_g, worst)          # the last band always reaches the worst team
        lo, hi = (lo_g, hi_g) if higher_is_better else (-hi_g, -lo_g)
        bands.append((k, lo, hi))
    return {"step": step, "n": n, "tier": tier, "bands": bands, "best": best,
            "higher_is_better": higher_is_better, "_values": _values}


def tier_grade(t: dict, team) -> str:
    """The team's letter with + / - for where it sits inside its band (user, 2026-10-06):
    top third +, bottom third -, middle plain -- so a C- and a D+ read as the neighbours they
    are instead of a full grade apart."""
    k = t["tier"][team]
    return tier_letter(k) + _band_mod(t, team)


def _band_mod(t: dict, team) -> str:
    x = t.get("_values", {}).get(team)
    if x is None or not t.get("step"):
        return ""
    g = x if t.get("higher_is_better", True) else -x
    step = t["step"]
    down = (t["best"] - g) - (t["tier"][team] - 1) * step      # distance below the band's top
    if float(step).is_integer() and float(down).is_integer():
        # whole-number scores: the band holds `step` scores; the top and bottom ceil(step/3) of
        # them get + and -, the middle plain -- symmetric (8 -> 3 / 2 / 3)
        edge = -(-int(step) // 3)
        return "+" if down < edge else "-" if down >= step - edge else ""
    if down < step / 3:
        return "+"
    if down >= 2 * step / 3:
        return "-"
    return ""


def unit_tiers(ue) -> dict:
    """The four tier scales on the unit score (higher is better on all four)."""
    sc = (ue or {}).get("score") or {}
    # tiered on the WHOLE-NUMBER scores the table shows, in whole-number bands, so a printed
    # score always sits inside its tier's printed range (code review)
    return {(side, kind): tiers({t: round(v) for t, v in sc.get(side, {}).get(kind, {}).items()},
                                higher_is_better=True, steps=INT_STEPS)
            for side in ("off", "def") for kind in ("pass", "run")}


INT_STEPS = (2, 3, 4, 5, 6, 8, 10, 12, 15, 20)


def band_label(b, last=False) -> str:
    """A whole-number band (k, lo, hi] as 'lo+1-hi' (the last band includes its low edge)."""
    lo, hi = int(round(b[1])), int(round(b[2]))
    return f"{lo if last else lo + 1}-{hi}"


def unit_table(ue, away, home) -> list[str]:
    """Each offence against the defence it faces, passes and runs, as one blended score and
    its tier per unit; the tier ladder below shows what each tier spans (user, 2026-10-06)."""
    if not ue or not ue.get("score") or not all(
            t in ue["score"]["off"]["pass"] and t in ue["score"]["def"]["pass"] for t in (away, home)):
        return []
    T = unit_tiers(ue)
    sc = ue["score"]
    L = ["| Matchup | Offence score | Offence tier | Defence faced: score | Defence tier |", "|---|---|---|---|---|"]
    letters = tier_grade
    for o, d_ in ((away, home), (home, away)):
        for k in ("pass", "run"):
            if o in sc["off"][k] and d_ in sc["def"][k]:
                to, td = T[("off", k)], T[("def", k)]
                L.append(f"| {o} {k} vs. {d_} | {round(sc['off'][k][o])} | {letters(to, o)} | "
                         f"{round(sc['def'][k][d_])} | {letters(td, d_)} |")
    L += ["", "**Score**: how well a unit does per play, blending EPA per play (points added against an average "
              "play from the same down, distance and field position) and success rate (share of plays that added "
              "points), two parts EPA to one part success. 50 is the league average and every 10 points is one standard deviation; higher is "
              "better for offences and defences alike. Passes include sacks and scrambles; garbage time removed ("
              + ue["_filter"] + "). **Tiers** S, A, B, C, D, F: equal bands of score counted down from the "
              "league's best team (S = the top band); a list whose spread needs fewer bands stops before F. "
              "**+ / -** mark the top and bottom third of a band, so a C- and a D+ are neighbours.",
          "", "| Tier | Passing offence | Running offence | Pass defence | Run defence |", "|---|---|---|---|---|"]
    n = max(T[k]["n"] for k in T)
    for k in range(1, n + 1):
        cells = []
        for key in (("off", "pass"), ("off", "run"), ("def", "pass"), ("def", "run")):
            b = next((x for x in T[key]["bands"] if x[0] == k), None)
            cells.append(band_label(b, last=(k == T[key]["n"])) if b else "")
        L.append(f"| {tier_letter(k)}{' (best)' if k == 1 else ''} | " + " | ".join(cells) + " |")
    pace = ue.get("pace") or {}
    if all(t in pace for t in (away, home)):
        L.append("")
        L.append(f"Pace in neutral situations (seconds between snaps; 1st = fastest): "
                 + "; ".join(f"{t} {pace[t][0]:.1f} ({ordinal(pace[t][1])})" for t in (away, home)) + ".")
    return L


def market_table(away, home, home_spread, total) -> list[str]:
    """The spread and implied points per team."""
    if home_spread is None or total is None:
        return ["Spread and total: not available in this run."]
    hp, ap = (total - home_spread) / 2, (total + home_spread) / 2
    return ["| Market | " + away + " | " + home + " |", "|---|---|---|",
            f"| Spread | {-home_spread:+g} | {home_spread:+g} |",
            f"| Implied team points | {ap:.1f} | {hp:.1f} |",
            "", f"Game total {total:g}."]


def outlook_table(chk: dict, away, home) -> list[str]:
    """Our expected passes and runs against each team's season (team_volume_check)."""
    rows = [(t, chk.get(t)) for t in (away, home) if chk.get(t)]
    if not rows:
        return []
    close = lambda c: (lambda a: f"{100 * a[0] / (a[0] + a[1]):.0f}%" if a and (a[0] + a[1]) else "—")(
        (c.get("rates") or {}).get("close"))
    L = ["| Team | Expected passes | Expected runs | Season avg passes / runs | Close-game pass rate |",
         "|---|---|---|---|---|"]
    for t, c in rows:
        att = f"{c['our_att']:.0f}" if c.get("our_att") is not None else "—"
        L.append(f"| {t} | {att} | {c['our_runs']:.0f} | {c['att_avg']:.1f} / {c['runs_avg']:.1f} | {close(c)} |")
    lg = (rows[0][1].get("league") or {}).get("close")
    if lg is not None:
        L += ["", f"League close-game pass rate: {100 * lg:.0f}%. Passes are attempts (sacks out); runs count "
                  "scrambles, as the model does."]
    return L


def positional_table(pa, teams) -> list[str]:
    """PPR points a game each defence allows by position, with rank."""
    if not pa or not all(t in pa for t in teams):
        return []
    n = pa["_n"]
    L = ["| Defence | RBs | WRs | TEs |", "|---|---|---|---|"]
    for t in teams:
        L.append(f"| {t} | " + " | ".join(f"{pa[t][p][0]:.1f} ({ordinal(pa[t][p][1])})" for p in POS_GROUPS) + " |")
    L.append("| League average | " + " | ".join(f"{pa['_league'][p]:.1f}" for p in POS_GROUPS) + " |")
    g = sorted(set(pa["_games"][t] for t in teams))
    L += ["", f"PPR fantasy points allowed per game over {'/'.join(map(str, g))} games. Rank among {n} teams: 1st "
              "= most points allowed. Touchdowns included; shaped by the opponents faced."]
    return L


def personnel_table(cells: dict, away, home) -> list[str]:
    """cells: {team: {"Quarterback": str, "Offensive line": str, "Pass catchers / backs": str,
    "Defence": str}}."""
    units = ["Quarterback", "Offensive line", "Pass catchers / backs", "Defence"]
    L = [f"| Unit | {away} | {home} |", "|---|---|---|"]
    for u in units:
        L.append(f"| {u} | {cells.get(away, {}).get(u, '—')} | {cells.get(home, {}).get(u, '—')} |")
    return L


def known_gaps_table(gaps) -> list[str]:
    """[(gap, consequence)] -> the 'where this baseline may miss' table."""
    if not gaps:
        return ["No known gap applies to this game beyond the general ones in 'Reading the numbers'."]
    return ["| Gap in this run | Consequence for this matchup |", "|---|---|"] + [f"| {g} | {c} |" for g, c in gaps]


def known_gaps(ctx: dict) -> list[tuple[str, str]]:
    """The model's known blind spots that apply to THIS game, from facts the scorer has.
    ctx keys (all optional): qb_change {team: text}, fav (team), spread (abs), new_team
    [names], questionable [names], has_pass_lines, has_rush_lines, oline_out {team: n},
    wind_mph, roof, roof_note."""
    g = []
    for t, txt in (ctx.get("qb_change") or {}).items():
        g.append((f"{t}'s quarterback: {txt}",
                  "Receiver and back prices do not adjust for who throws (they run on each player's shares and "
                  "rates); a lower-volume or lower-efficiency passing game belongs beside the baseline."))
    if ctx.get("fav") and (ctx.get("spread") or 0) >= 7:
        g.append((f"{ctx['fav']}'s expected lead ({ctx['spread']:g} points)",
                  "The carry forecast does not follow the score: a favourite's late carries can run above it and "
                  "the underdog's passes too. The market-carries number beside a back's rushing line shows the "
                  "direction; who gets the late work still decides the player."))
    if ctx.get("new_team"):
        g.append(("New roles: " + ", ".join(ctx["new_team"]),
                  "Thin new-team evidence: their shares are less settled than the projection's single number."))
    if ctx.get("questionable"):
        g.append(("Questionable: " + ", ".join(ctx["questionable"]),
                  "Priced as playing his normal role; 'If a Questionable player is out' prices the other case."))
    if ctx.get("has_pass_lines"):
        g.append(("QB passing width",
                  "The passing distribution is too wide (14% of games outside the 80% range): a passing chance sits "
                  "too close to 50%, so a 60% Over is likely a little better than 60."))
    if ctx.get("has_rush_lines"):
        g.append(("Rushing tails",
                  "Rushing and rushing + receiving run narrow in the tails: a line far from the projection reads "
                  "more confident than it should; the main line is unaffected."))
    for t, k in (ctx.get("oline_out") or {}).items():
        if k >= 2:
            g.append((f"{t} offensive line ({k} of 5 regulars out)", "Line absences are not a price input."))
    if (ctx.get("wind_mph") or 0) > 15 and ctx.get("roof") not in ("closed", "dome"):
        g.append((f"Wind to {ctx['wind_mph']:.0f} mph", "The model has no wind adjustment."))
    if ctx.get("roof_note"):
        g.append(("Roof", ctx["roof_note"] + "."))
    return g


def margin_flags(projected, over_needs, under_needs, unit="", thin=0.10) -> list[str]:
    """The research table's margin flag at OUR projection (user, 2026-10-06): the side that
    pays at our volume, flagged when it clears its break-even volume by under 10% ("thin")."""
    o = thin_margin(projected, over_needs, True, thin)
    u = thin_margin(projected, under_needs, False, thin)
    unit = f" {unit}" if unit else ""
    if o and o[0] >= 0:
        return [f"thin: the Over needs {float(over_needs):.1f}{unit}, we project {float(projected):.1f}"] if o[1] else []
    if u and u[0] >= 0:
        return [f"thin: the Under needs {float(under_needs):.1f}{unit} or fewer, we project {float(projected):.1f}"] if u[1] else []
    return []          # neither side pays: the break-even cell already says so ("no-bet zone")


def thin_margin(projected, needs, side_over=True, thin=0.10):
    """Whether a volume read clears a side's break-even volume by under `thin` (10%):
    Over needs volume >= needs, Under volume <= needs. None when either is missing."""
    try:
        v, k = float(projected), float(needs)
    except (TypeError, ValueError):
        return None
    if not (v == v and k == k) or k <= 0:
        return None
    margin = (v - k) / k if side_over else (k - v) / k
    return margin, (0 <= margin < thin)


# Sleeper's lines that are read beside the priced ones, never priced (DECISIONS #164, #166)
EXTRA_KINDS = ("longest_reception", "longest_rush", "rushing_attempts",
               "pass_completions", "passing_attempts", "longest_passing_completion",
               "rushing_and_receiving_yards")


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
                     model_ypc=None, longest_line=None, luckfree_ypc=None,
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
    (luckfree_ypc: research.luck_for, his last LUCK_WINDOW games). A
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
           "read": None, "season_ypc_luckfree": None, "gauge": None, "gauge_rate": None, "luck": luck}
    if ok(season_rec) and ok(season_yds) and season_rec >= YPC_MIN_CATCHES:
        out.update(season_ypc=float(season_yds) / float(season_rec), season_rec=int(season_rec))
    if ok(luckfree_ypc):
        out["season_ypc_luckfree"] = float(luckfree_ypc)
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
    rate = out["season_ypc_luckfree"] if out["season_ypc_luckfree"] is not None else out["model_ypc"]
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
            his.append(f"he has {d['season_ypc']:.1f} this season on {d['season_rec']} catches")
        if d["season_ypc_luckfree"] is not None:
            his.append(f"{d['season_ypc_luckfree']:.1f} luck-free over his last {(d.get('luck') or {}).get('games', '?')} games")
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
        lc = luck_words(d.get("luck"), "catch") if d["season_ypc_luckfree"] is not None else None
        bits.append(gauge_sentence(d["gauge"], d["gauge_rate"], "catch", lc, d["y_min"], "a long catch",
                                   book_line=d["catches_line"], book_fair=d.get("book_fair")))
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
                     season_car=None, season_yds=None, luckfree_ypc=None, longest_line=None,
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
           "season_ypc_luckfree": None, "gauge": None, "gauge_rate": None, "luck": luck,
           "longest_line": None, "long_min": None,
           "long_share": None, "rest_ypc": None, "read": None}
    if ok(model_ypc) and model_ypc > 0:
        out["model_ypc"] = float(model_ypc)
    if ok(season_car) and ok(season_yds) and season_car >= RUN_MIN_CARRIES:
        out.update(season_ypc=float(season_yds) / float(season_car), season_car=int(season_car))
    if ok(luckfree_ypc):
        out["season_ypc_luckfree"] = float(luckfree_ypc)
    if ok(carries_line) and float(carries_line) > 0:
        c_min = to_clear(carries_line)
        out.update(carries_line=float(carries_line), c_min=c_min, need_ypc=y_min / c_min,
                   mid_ypc=float(yards_line) / float(carries_line))
    if ok(longest_line):
        l_min = to_clear(longest_line)
        out.update(longest_line=float(longest_line), long_min=l_min, long_share=l_min / y_min)
        if out["c_min"] and out["c_min"] >= 2 and l_min < y_min:
            out["rest_ypc"] = (y_min - l_min) / (out["c_min"] - 1)
    rate = out["season_ypc_luckfree"] if out["season_ypc_luckfree"] is not None else out["model_ypc"]
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
            his.append(f"he has {d['season_ypc']:.1f} this season on {d['season_car']} carries "
                       "(mostly noise this early: the league average predicts later games better)")
        if d["season_ypc_luckfree"] is not None:
            his.append(f"{d['season_ypc_luckfree']:.1f} luck-free over his last {(d.get('luck') or {}).get('games', '?')} games")
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
        lc = luck_words(d.get("luck"), "run") if d["season_ypc_luckfree"] is not None else None
        bits.append(gauge_sentence(d["gauge"], d["gauge_rate"], "carry", lc, d["y_min"], "a long run",
                                   book_line=d["carries_line"], book_fav=d["carries_fav"], book_fair=d.get("book_fair")))
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


def projected_completions(receiver_catch_means, other_targets_mean, other_catch_rate, starter_share_mean):
    """Our projected completions for the starter: his receivers' simulated catches, plus the
    depth bucket's targets caught at the depth rate, times his usual share of the team's
    passing -- the mean of what model.simulate_qb_completions draws."""
    other = (float(other_targets_mean) * float(other_catch_rate)
             if other_targets_mean is not None and other_catch_rate is not None else 0.0)
    return (float(sum(receiver_catch_means)) + other) * float(starter_share_mean)


def qb_yards_read(completions_line=None, yards_line=None, proj_completions=None, model_ypc=None,
                  luck=None, luckfree_ypc=None, longest_line=None, completions_fav=None,
                  attempts_line=None) -> dict | None:
    """The quarterback's version of the catches/carries reads (DECISIONS #170): the book's
    completions, passing-yards and longest-completion lines read together at the whole
    numbers that win them; his luck-free yards per completion over his last LUCK_WINDOW
    games (each completion past his own LUCK_PCT percentile counted at it); the
    completions the yards line takes at that rate, against our projected completions and
    the book's completions line. Report text only."""
    ok = lambda v: v is not None and v == v
    if not ok(yards_line):
        return None
    y_min = to_clear(yards_line)
    out = {"yards_line": float(yards_line), "y_min": y_min, "completions_line": None, "c_min": None,
           "mid_ypc": None, "model_ypc": float(model_ypc) if ok(model_ypc) and model_ypc > 0 else None,
           "luckfree_ypc": float(luckfree_ypc) if ok(luckfree_ypc) else None, "luck": luck,
           "completions_fav": completions_fav, "attempts_line": float(attempts_line) if ok(attempts_line) else None,
           "proj": float(proj_completions) if ok(proj_completions) else None,
           "longest_line": None, "long_min": None, "gauge": None, "gauge_rate": None}
    if ok(completions_line) and float(completions_line) > 0:
        out.update(completions_line=float(completions_line), c_min=to_clear(completions_line),
                   mid_ypc=float(yards_line) / float(completions_line))
    if ok(longest_line):
        out.update(longest_line=float(longest_line), long_min=to_clear(longest_line))
    rate = out["luckfree_ypc"] if out["luckfree_ypc"] is not None else out["model_ypc"]
    if rate is not None:
        out.update(gauge_rate=rate, gauge=volume_gauge(y_min, rate, out["proj"], "completions", 12.0))
    out["read"] = None
    if out["mid_ypc"] is not None and out["model_ypc"] is not None:
        gap = out["mid_ypc"] - out["model_ypc"]
        out["read"] = ("yards line rich" if gap >= YPC_BAND
                       else "yards line lean" if gap <= -YPC_BAND else "about even")
    return out


def qb_yards_sentence(d) -> str | None:
    if not d or (d["completions_line"] is None and d.get("gauge") is None):
        return None
    bits = []
    if d["completions_line"] is not None:
        fav = f", {d['completions_fav']} favoured" if d["completions_fav"] else ""
        att = f" (attempts {d['attempts_line']:g})" if d["attempts_line"] is not None else ""
        we = f"; we project {d['proj']:.1f}" if d["proj"] is not None else ""
        bits.append(f"The book's completions line is {d['completions_line']:g}{fav}{att}{we}.")
        his = []
        if d["model_ypc"] is not None:
            his.append(f"we expect {d['model_ypc']:.1f}")
        if d["luckfree_ypc"] is not None:
            his.append(f"{d['luckfree_ypc']:.1f} luck-free over his last {(d.get('luck') or {}).get('games', '?')} games")
        bits.append(f"The lines ask {d['mid_ypc']:.1f} yards a completion ({d['yards_line']:g} over "
                    f"{d['completions_line']:g})" + (f"; {', '.join(his)}" if his else "") + ".")
        if d.get("read") == "yards line rich":
            bits.append("That is more per completion than ours: past the completions line, his yards Over still "
                        "needs extra completions or a long one.")
        elif d.get("read") == "yards line lean":
            bits.append("That is less per completion than ours: if he clears the completions line, the yards "
                        "usually come with it.")
        elif d.get("read") == "about even":
            bits.append("That is about ours: his yards Over is a bet on the completions.")
    if d.get("gauge") is not None:
        lc = luck_words(d.get("luck"), "completion") if d["luckfree_ypc"] is not None else None
        bits.append(gauge_sentence(d["gauge"], d["gauge_rate"], "completion", lc, d["y_min"], "a long completion",
                                   book_line=d["completions_line"], book_fav=d["completions_fav"],
                                   book_fair=d.get("book_fair")))
    if d["long_min"] is not None:
        bits.append(f"The longest-completion line ({d['longest_line']:g}) means one completion of "
                    f"{d['long_min']}, {100 * d['long_min'] / d['y_min']:.0f}% of the {d['y_min']} yards.")
    return " ".join(b for b in bits if b)


def rush_rec_read(line=None, mult_over=None, mult_under=None, proj_carries=None, proj_catches=None,
                  run_rate=None, catch_rate=None, run_luck=None, catch_luck=None, sd=None,
                  book_carries=None, book_catches=None, rates_luck_free=True, p_model_over=None) -> dict | None:
    """The book's rushing + receiving yards line read against his touches (DECISIONS #173):
    the no-vig Over chance and the coin-flip yards (sd = the game-to-game spread of his
    simulated rushing + receiving yards); his luck-free yards a touch -- carries and catches
    at their own luck-free rates (research.luck_for), weighted by our projected carries and
    catches; the touches the line takes at that rate against ours and the book's carries +
    catches lines; and the share of his yards that come through the air, the part that holds
    up when his team falls behind; and our model's Over chance (priced since it passed its
    calibration check, DECISIONS #187)."""
    ok = lambda v: v is not None and v == v
    if not ok(line):
        return None
    y_min = to_clear(line)
    out = {"line": float(line), "y_min": y_min, "p_over": fair_over(mult_over, mult_under),
           "fav": favoured(mult_over, mult_under), "coin": None, "touch_rate": None, "need": None,
           "proj_touches": None, "book_touches": None, "air_share": None, "word": None,
           "proj_carries": float(proj_carries) if ok(proj_carries) else None,
           "proj_catches": float(proj_catches) if ok(proj_catches) else None,
           "run_rate": float(run_rate) if ok(run_rate) else None,
           "catch_rate": float(catch_rate) if ok(catch_rate) else None,
           "run_luck": run_luck, "catch_luck": catch_luck, "rates_luck_free": bool(rates_luck_free),
           "p_model_over": float(p_model_over) if ok(p_model_over) else None}
    out["coin"] = fair_volume(line, out["p_over"], sd)
    c, k, rr, cr = out["proj_carries"], out["proj_catches"], out["run_rate"], out["catch_rate"]
    if c is not None and k is not None and rr is not None and cr is not None and c + k > 0:
        yards = c * rr + k * cr
        out.update(touch_rate=yards / (c + k), proj_touches=c + k,
                   air_share=(k * cr / yards) if yards > 0 else None)
        g = volume_gauge(y_min, out["touch_rate"], c + k, "touches", 8.0)
        if g:
            out.update(need=g["need"], word=g["word"])
    if ok(book_carries) and ok(book_catches):
        out["book_touches"] = float(book_carries) + float(book_catches)
    return out


def rush_rec_sentence(d) -> str | None:
    if not d:
        return None
    fav = f", {d['fav']} favoured" if d["fav"] else ""
    coin = f" (a coin flip at about {d['coin']:.0f} yards)" if d["coin"] is not None else ""
    bits = [f"The book's line is {d['line']:g}{fav}{coin}."]
    if d["need"] is not None:
        whose = "his luck-free yards a touch" if d.get("rates_luck_free", True) else "our yards a touch (too few of his own plays)"
        bits.append(f"At {whose} ({d['run_rate']:.1f} a carry, {d['catch_rate']:.1f} a catch, "
                    f"{d['touch_rate']:.1f} a touch at our mix), {d['y_min']} yards takes about {d['need']:.1f} touches; "
                    f"we project {d['proj_touches']:.1f} ({d['proj_carries']:.1f} carries, {d['proj_catches']:.1f} "
                    f"catches), {d['word']}.")
        if d["book_touches"] is not None:
            bits.append(f"The book's own carries and catches lines add to {d['book_touches']:g} touches.")
        if d["air_share"] is not None:
            bits.append(f"About {100 * d['air_share']:.0f}% of his projected yards come from catches: if his team falls "
                        "behind, that part holds up while the carries shrink.")
    if d.get("p_model_over") is not None:
        bits.append(f"Our model gives the Over {100 * d['p_model_over']:.0f}% (the combined market is priced since "
                    "it passed its calibration check, DECISIONS #187).")
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


# ---- offensive line: how many of a team's five regular linemen are out (DECISIONS #178) ----
# Context only, never a price input: the reader judges it. Whether missing starters
# predict the model's misses is a separate, later test (queued behind conditional
# calibration and the implied team total).
OL_POS = ("T", "G", "C", "OL")
LINE_SLOTS = 5


def line_regulars(snaps, team, week, n=LINE_SLOTS) -> list[dict]:
    """The team's regular offensive line: the n linemen with the most offensive snaps
    this season before this week (snap counts: player, pfr_player_id, position, team,
    week, offense_snaps). Empty when the team has no lineman snaps yet."""
    s = snaps[(snaps.team == team) & (snaps.week < week) & snaps.position.isin(OL_POS)]
    if s.empty:
        return []
    g = s.groupby("pfr_player_id").agg(name=("player", "last"), pos=("position", "last"),
                                       snaps=("offense_snaps", "sum"),
                                       games=("offense_snaps", lambda v: int((v > 0).sum())))
    g = g[g.snaps > 0].sort_values(["snaps", "name"], ascending=[False, True]).head(n)
    return [{"pfr_id": i, "name": r["name"], "pos": r.pos, "snaps": int(r.snaps), "games": int(r.games)}
            for i, r in g.iterrows()]


def line_status(regulars, team, pfr_to_gsis, roster, report, not_playing, name_to_gsis=None) -> list[dict]:
    """Each regular's status this week: 'out' (Out / Doubtful on the report, a not-playing
    roster status, or off the team's roster), 'questionable', 'playing', or 'unmatched'
    (no roster id found: never counted as out). Ids come from pfr_to_gsis, else from
    name_to_gsis {(team, norm_name): gsis_id} (the roster file lacks many pfr ids).
    roster: {gsis_id: (team, roster status)} for this week; report: {gsis_id: status}."""
    out = []
    for r in regulars:
        gid = pfr_to_gsis.get(r["pfr_id"]) or (name_to_gsis or {}).get((team, MODEL.norm_name(r["name"])))
        on = roster.get(gid) if gid else None
        rep = report.get(gid) if gid else None
        if gid is None:
            why, state = "not matched to the roster", "unmatched"
        elif on is None or on[0] != team:
            why, state = "no longer on the roster", "out"
        elif on[1] in not_playing:
            why, state = {"INA": "inactive"}.get(on[1], "on reserve"), "out"
        elif rep in ("Out", "Doubtful"):
            why, state = rep, "out"
        elif rep == "Questionable":
            why, state = rep, "questionable"
        else:
            why, state = None, "playing"
        out.append({**r, "state": state, "why": why})
    return out


def line_sentence(team, status, report_out=True, feed=False) -> str | None:
    """The game header's line read for one team; None without five regulars.
    report_out False: this week's injury report is not published yet; feed True: Sleeper's
    injury feed filled in where it was silent (the players' own statuses, #183)."""
    if len(status) < LINE_SLOTS:
        return None
    out = [s for s in status if s["state"] == "out"]
    q = [s for s in status if s["state"] == "questionable"]
    name = lambda s: f"{s['name']} ({s['pos']}, {s['why']})"
    head = (f"{team}: all five regular linemen available" if not out else
            f"{team}: {len(out)} of 5 regular linemen out -- " + ", ".join(map(name, out)))
    um = [s for s in status if s["state"] == "unmatched"]
    if not out and um:
        head = f"{team}: no regular lineman reported out"
    if not report_out:
        head += (" (no injury report yet this week: roster status and Sleeper's injury feed)" if feed else
                 " (no injury report yet this week: roster status only)")
    return (head + (f"; questionable: " + ", ".join(map(name, q)) if q else "")
            + (f"; not matched to the roster, status unknown: " + ", ".join(s["name"] for s in um) if um else "")
            + ".")


# ---- the automatic what-if range: 'carries=auto' (DECISIONS #179) ----
# Not his game-to-game swing (the simulation already prices that): how sure we are of
# his AVERAGE share, one standard error either side of our projection.
AUTO_GAMES = LUCK_WINDOW        # last 10 games, the luck-free check's window
AUTO_MIN_GAMES = 3


def auto_range(this_season, last_season, proj, team_volume, this_season_only=False):
    """Low / expected / high volume for an automatic range. this_season / last_season:
    his per-game shares (oldest first) of the team's throws or runs; the last AUTO_GAMES
    games are used, topped up from last season unless this_season_only (a role change).
    proj: our projected volume; team_volume: the team's projected throws or runs.
    Returns {values, n, se, from_last} or None under AUTO_MIN_GAMES games."""
    shares = [float(v) for v in this_season if v == v][-AUTO_GAMES:]
    from_last = 0
    if not this_season_only and len(shares) < AUTO_GAMES:
        tail = [float(v) for v in last_season if v == v]
        take = tail[-(AUTO_GAMES - len(shares)):]
        from_last = len(take)
        shares = take + shares
    n = len(shares)
    if n < AUTO_MIN_GAMES or proj is None or team_volume is None:
        return None
    se = float(np.std(shares, ddof=1) / np.sqrt(n) * team_volume)
    return {"values": [max(0.0, proj - se), float(proj), proj + se], "n": n, "se": se, "from_last": from_last}


# ---- the book's quarterback against the engine's starter (DECISIONS #181) ----
QB_KINDS = ("passing_attempts", "pass_completions", "longest_passing_completion", "passing_yards")


def book_qb_mismatch(extra, starters, sleeper_team=None) -> list[dict]:
    """Teams whose book posts passing lines for a QB other than the engine's starter and
    none for the starter: the depth chart may be stale (the backtest graded the wrong
    QB in 27% of backup starts, 2022-25). starters: {our team code: engine starter's
    name}. Returns [{team, engine, book}]."""
    back = {v: k for k, v in (sleeper_team or {}).items()}
    posted = {}
    for x in extra or []:
        if x["kind"] in QB_KINDS:
            posted.setdefault(back.get(x["team"], x["team"]), set()).add(x["name"])
    out = []
    for team, names in posted.items():
        eng = starters.get(team)
        if eng and MODEL.norm_name(eng) not in {MODEL.norm_name(n) for n in names}:
            out.append({"team": team, "engine": eng, "book": sorted(names)})
    return out
