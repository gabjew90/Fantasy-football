"""Replacement baselines derived from STREAMING, not from starter demand.

The format-derived baseline -- round(teams x starter demand) -- answers "how
many players at this position start league-wide". That is the right question
only for a position you have to draft. For a streamable one it is wrong in a
specific direction: it prices the alternative to your quarterback as the last
DRAFTED quarterback, when the real alternative is the best quarterback on
waivers in any given week, and in a 10-team 1-QB league that is a much better
player.

Keefamania's QB5/TE8 were previously hand-fitted by minimising the gap between
VORP rank and ADP rank. That works, and it is the wrong way to get there: the
residual you are fitting is the market's opinion, so the baseline stops being
a structural fact about the format and starts being a laundered copy of ADP.
This module derives the same quantity from what streaming actually returned.

The operator (per the expert review, 2026-09-01)
-----------------------------------------------
Replacement is an ORDER STATISTIC over the residual pool, not its maximum.
Taking the max assumes you get the best available player every week, which
assumes you always win the claim and always guess the right week in advance.
The k-th best absorbs both frictions in one parameter:

    k = 2   FAAB leagues (you can pay for the guy you want)
    k = 3   rolling waiver priority (claiming burns your position)

Keefamania is "Continual rolling list", so k=3.

Backtest, per position, over the prior season:

    for each week w:
        take the players NOT rostered in week w                 (see below)
        keep the ones active in week w
        rank them by prior-week form                            (ex ante)
        take the k-th; record what he actually scored in week w  (ex post)

    replacement_ppg = mean over weeks
    baseline rank   = the season-total rank whose total is nearest
                      replacement_ppg x 17

Only prior-week information selects the streamer; only the current week scores
him. Restricting to players active in week w is not lookahead -- inactives are
published before lineups lock.

The result is FLOORED at the format-derived baseline (`min` in rank space, so
a shallower/higher replacement level wins). The operator may only tighten
VORP, never inflate it: if streaming turns out to be worse than the last
drafted player, you would simply draft one, so the season-long fallback holds.

WHY THIS IS NOT WIRED IN YET (2026-09-01)
-----------------------------------------
`held_by_week` -- who is rostered -- has to be supplied. The obvious cheap
proxy, "the top N at the position by points per game to date", was tried and
is badly wrong: roster-ness is sticky from draft day, so a drafted starter
having a mediocre few weeks drops out of the top N and is scored as a waiver
pickup. On 2025 QBs that proxy put Joe Burrow, Sam Darnold, Tua Tagovailoa and
J.J. McCarthy in the "waiver pool" and duly measured streaming as returning
QB3 production. Garbage in.

Doing it properly needs one of:
  * prior-season ADP (who was drafted) -- data/raw/adp_history only goes back
    to 2026-08-19, so 2025 is not on disk, or
  * a percent-rostered time series.

Until one exists, the format-derived baselines stand and this module raises
rather than guessing. The functions below are unit-tested and correct; what is
missing is an input, not logic.
"""

from __future__ import annotations

import polars as pl

FANTASY_WEEKS = 17          # weeks 1..17; week 18 is not a fantasy week
SEASON_GAMES = 17
WAIVER_K = {"faab": 2, "rolling_priority": 3, "rolling_list": 3}
# K and DEF are deliberately absent: nflverse load_player_stats carries no
# kicking or team-defense columns, so fantasy_points_expr scores every kicker
# at exactly 0.0 and the operator would "derive" a K2 baseline off an empty
# measurement. Their format baselines stand.
STREAMABLE = ("QB", "RB", "WR", "TE")


def waiver_k(waiver_type: str | None, default: int = 3) -> int:
    """IN-SEASON claim friction as an order statistic.

    You do not land your first choice every week: someone else may win the
    claim. How often depends on the waiver FORMAT, which is why this one is
    keyed on it. Unknown type -> the PESSIMISTIC (higher-k) value, because
    assuming you always get your man is the failure mode that inflates VORP.

    NOT for draft time. See draft_k below: at the draft you are forecasting a
    pool that does not exist yet, and the uncertainty is your own projection,
    not a contested claim.
    """
    return WAIVER_K.get(str(waiver_type or "").lower().strip(), default)


# Draft-time k. A DIFFERENT QUANTITY that happens to share the operator.
#
# When the engine asks "what will the wire hold?" during a draft, the thing it
# is unsure about is WHICH undrafted player is really best -- its own ranking.
# Deep-band MAE is 65-70 points (DECISIONS #40); at that error the best
# undrafted RB is a coin flip among several, so the k-th best is a hedge
# against prediction error. Waiver format has nothing to do with it, and
# keying this on FAAB-vs-rolling (as waiver_k did for both callers until
# 2026-09-04) was defending it with a reason that is false here.
#
# 3 is today's value, carried over unchanged so the split ships as a no-op.
# 2 was considered and REJECTED: it is defensible under claim friction (nobody
# contests a claim at draft time) but claim friction is precisely what this
# split moves to the in-season side, and the prediction-error argument runs the
# other way -- 65-point error bars argue for hedging HARDER than 3, not softer.
# The derivation from backtest error is what should move this number.
DRAFT_K_DEFAULT = 3


def draft_k(configured: int | None = None) -> int:
    """Draft-time order statistic, hedging PREDICTION ERROR. Not waiver-typed."""
    try:
        return int(configured) if configured else DRAFT_K_DEFAULT
    except (TypeError, ValueError):
        return DRAFT_K_DEFAULT


def weekly_points(weekly: pl.DataFrame, fpts: pl.Expr) -> pl.DataFrame:
    """(player, pos, week, fpts) for the fantasy weeks of one season."""
    name = ("player_display_name" if "player_display_name" in weekly.columns
            else "player_name")
    return (
        weekly.filter(pl.col("week") <= FANTASY_WEEKS)
        .with_columns(fpts)
        .select(
            pl.col(name).alias("player"),
            pl.col("position").alias("pos"),
            pl.col("week"),
            pl.col("fpts"),
        )
        .filter(pl.col("pos").is_in(list(STREAMABLE)))
    )


class OwnershipUnavailable(RuntimeError):
    """No source identifies who was rostered. See the module docstring."""


def streaming_ppg(wk: pl.DataFrame, pos: str, held_by_week: dict[int, set[str]],
                  k: int, first_week: int = 5, form_weeks: int = 3,
                  ) -> float | None:
    """Mean weekly points of the k-th best waiver-pool player at `pos`.

    held_by_week: {week -> set of rostered player names}. REQUIRED, and
    deliberately not inferrable from box scores -- see the module docstring
    for what happens when you try.

    The streamer is chosen by form over the last `form_weeks` weeks, which
    picks up newly-starting players (the ones streaming is actually about).
    That proxy still knows nothing about matchups, so the result is a LOWER
    bound on what a manager with a projection system would get.

    first_week: earlier weeks are skipped -- one or two games of prior
    information is noise, and in the real season you are still running your
    drafted starter anyway.
    """
    if not held_by_week:
        raise OwnershipUnavailable(
            "streaming_ppg needs a rostered set per week; inferring it from "
            "scoring puts real starters in the waiver pool")
    grp = wk.filter(pl.col("pos") == pos)
    if grp.height == 0:
        return None
    scored: list[float] = []
    for w in range(first_week, FANTASY_WEEKS + 1):
        held = held_by_week.get(w)
        if held is None:
            continue
        hist = grp.filter((pl.col("week") < w) & (pl.col("week") >= w - form_weeks))
        if hist.height == 0:
            continue
        form = (
            hist.group_by("player")
            .agg(pl.col("fpts").mean().alias("m"))
            .sort("m", descending=True)
        )
        # actually playing this week: inactives are published before lineups
        # lock, so filtering on them is ex ante, not lookahead
        active = set(grp.filter(pl.col("week") == w)["player"].to_list())
        residual = [p for p in form["player"].to_list()
                    if p not in held and p in active]
        if len(residual) < k:
            continue
        streamer = residual[k - 1]
        pts = grp.filter((pl.col("week") == w) & (pl.col("player") == streamer))
        if pts.height:
            scored.append(float(pts["fpts"][0]))
    return sum(scored) / len(scored) if scored else None


def rank_for_season_total(wk: pl.DataFrame, pos: str, total: float) -> int | None:
    """The positional rank whose prior-season TOTAL is nearest `total`.

    Working in rank space is what makes the answer portable: point levels do
    not survive a change of season or scoring, but "streaming this position
    returns about what the Nth best player returns" does.
    """
    totals = (
        wk.filter(pl.col("pos") == pos)
        .group_by("player")
        .agg(pl.col("fpts").sum().alias("total"))
        .sort("total", descending=True)
    )
    if totals.height == 0:
        return None
    vals = totals["total"].to_list()
    best, best_rank = None, None
    for i, v in enumerate(vals, start=1):
        d = abs(v - total)
        if best is None or d < best:
            best, best_rank = d, i
    return best_rank


def rostered_counts(board: list[dict], teams: int, rounds: int) -> dict[str, int]:
    """How many players at each position the market actually drafts.

    Read off ADP rather than assumed from roster slots: bench composition is a
    behavioural fact, not a format one, and ADP is the cheapest honest
    measurement of it. This uses the market for AVAILABILITY (who is left),
    never for value -- which is the distinction that keeps the derivation from
    collapsing back into fitting ADP.

    Take the top `teams x rounds` BY ADP, not everyone whose ADP is inside the
    last pick. ADP is a mean over many drafts, so those are different sets and
    only the first has the right size: on the Keefamania board 214 players
    carry an ADP of 150 or better, into a draft that makes 150 picks. Counting
    that way put 28 quarterbacks in a 10-team 1-QB league and pushed the
    residual pool down to QB29, which then "measured" streaming as worthless.
    """
    ranked = sorted((p for p in board if p.get("adp") is not None),
                    key=lambda p: float(p["adp"]))[: teams * rounds]
    out: dict[str, int] = {}
    for p in ranked:
        out[p["pos"]] = out.get(p["pos"], 0) + 1
    return out


def derive(wk: pl.DataFrame, held_by_week: dict[str, dict[int, set[str]]],
           k: int, format_baselines: dict[str, int]) -> dict[str, dict]:
    """Per position: the streaming baseline, the format baseline, and the
    floored result actually to be used.

    held_by_week is keyed by position, then week.

    `format_baselines` must be the FORMAT derivation -- round(teams x starter
    demand) with the flex split -- and not whatever is currently in the league
    yaml. The point of this module is to replace a hand-fitted number, so
    comparing against that hand-fitted number would just re-derive it.
    """
    out: dict[str, dict] = {}
    for pos in STREAMABLE:
        fmt = format_baselines.get(pos)
        if not fmt:
            continue
        row = {"format": fmt, "streaming_ppg": None, "streaming_rank": None,
               "baseline": fmt,
               "why": "no ownership data — format baseline stands"}
        held = held_by_week.get(pos) or {}
        if held:
            ppg = streaming_ppg(wk, pos, held, k)
            if ppg is not None:
                rank = rank_for_season_total(wk, pos, ppg * SEASON_GAMES)
                row["streaming_ppg"] = round(ppg, 2)
                row["streaming_rank"] = rank
                if rank is not None:
                    # floor in RANK space: a smaller rank is a HIGHER
                    # replacement level, which lowers VORP
                    row["baseline"] = min(fmt, rank)
                    row["why"] = (
                        f"streaming the #{k} waiver {pos} returned "
                        f"{ppg:.1f} ppg = {pos}{rank} production"
                        + ("" if rank <= fmt else
                           f"; worse than {pos}{fmt}, so the format "
                           f"baseline holds")
                    )
        out[pos] = row
    return out


def held_from_ownership(rows: list[dict], pos_of: dict[str, str],
                        threshold: float = 50.0) -> dict[str, dict[int, set[str]]]:
    """Build held_by_week from a percent-rostered feed.

    rows: {"player", "week", "pct_rostered"}. A player above `threshold` is
    treated as rostered that week, so not available to stream.
    """
    out: dict[str, dict[int, set[str]]] = {}
    for r in rows:
        try:
            pct = float(r.get("pct_rostered"))
            week = int(r.get("week"))
        except (TypeError, ValueError):
            continue
        if pct < threshold:
            continue
        pos = pos_of.get(str(r.get("player")))
        if pos not in STREAMABLE:
            continue
        out.setdefault(pos, {}).setdefault(week, set()).add(str(r["player"]))
    return out
