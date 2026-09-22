"""Cross-game anytime-TD parlay builder.

Legs in DIFFERENT GAMES are independent, so a cross-game parlay's probability
is the product of its legs' probabilities -- no joint model needed. A parlay
is +EV only if every leg is +EV on its own, and each leg's hold compounds (at
Sleeper's ~12% per leg a 3-leg entry pays ~68% of fair). So the builder only
combines legs that are already past the edge floor on their own:

  - one leg per game (and so one per team): independence holds;
  - each leg's probability is the layer-4 BLEND (model and de-vigged market,
    td_market.py) -- the provisional price, not the unblended model;
  - each leg clears the TD edge floor: blend at least 25% above the market
    (relative), and positive expected value at the posted price;
  - 2 or 3 legs.

For each combination it reports the combined fair probability, the fair
American price, the minimum decimal payout worth taking (= the Sleeper multiplier), and -- if
every leg is at one sportsbook -- the product price and its expected value.

The legs are anytime_td_v1 PROTOTYPE prices blended at a PROVISIONAL weight,
so nothing here is a validated edge; it describes what the numbers would
support if they were.
"""

from __future__ import annotations

from itertools import combinations

import numpy as np
import pandas as pd

import td_market as TM

EDGE_FLOOR_TD = 0.25       # relative edge, as the tier rules use for TD props
TOP_LEGS = 8


def candidate_legs(boards: pd.DataFrame, floor: float = EDGE_FLOOR_TD) -> pd.DataFrame:
    """The best-priced row per player, kept only if it clears the floor on its
    own. `boards` = the slate's td_board rows with a `game` column."""
    if boards.empty:
        return boards
    b = boards.copy()
    b["dec"] = b["price"].map(TM.decimal_from_american)
    b = b.sort_values("dec", ascending=False).drop_duplicates(["game", "player"])
    b["edge_rel"] = b["p_blend"] / b["p_market"] - 1
    b["ev"] = b["p_blend"] * b["dec"] - 1
    return b[(b["edge_rel"] >= floor) & (b["ev"] > 0)].sort_values("ev", ascending=False)


def build(boards: pd.DataFrame, legs=(2, 3), top: int = TOP_LEGS, floor: float = EDGE_FLOOR_TD) -> pd.DataFrame:
    """Every 2- and 3-leg combination of the top legs with one leg per game,
    ranked by combined fair probability."""
    c = candidate_legs(boards, floor).head(top)
    rows = []
    for k in legs:
        for combo in combinations(c.itertuples(), k):
            if len({x.game for x in combo}) < k:           # one leg per game: independence
                continue
            p = float(np.prod([x.p_blend for x in combo]))
            pm = float(np.prod([x.p_model for x in combo]))
            books = {x.book for x in combo}
            # a sportsbook prices a cross-game parlay as the product of its legs; Sleeper pays from a
            # fixed pick'em table, so a product there means nothing
            dec = (float(np.prod([x.dec for x in combo]))
                   if len(books) == 1 and next(iter(books)) != "sleeper" else np.nan)
            rows.append({"legs": k,
                         "players": " + ".join(f"{x.player} ({x.team})" for x in combo),
                         "games": " / ".join(x.game for x in combo),
                         "p_fair": p, "p_model_product": pm,
                         "fair_american": TM.american_from_prob(p),
                         "min_payout_decimal": round(1.0 / p, 2),
                         "book": next(iter(books)) if len(books) == 1 else "mixed",
                         "book_product_decimal": dec,
                         "ev_at_book_product": p * dec - 1 if np.isfinite(dec) else np.nan})
    out = pd.DataFrame(rows)
    return out.sort_values("p_fair", ascending=False) if len(out) else out


def markdown(parlays: pd.DataFrame, legs: pd.DataFrame, top: int = 5) -> list[str]:
    L = ["## Cross-game TD parlays (one leg per game)", "",
         "*Legs in different games are independent, so the parlay is the product of its legs. Each leg is the "
         "layer-4 blend of anytime_td_v1 and the de-vigged market at a PROVISIONAL weight, and must clear the TD "
         "edge floor (25% relative, positive EV) on its own. The legs are PROTOTYPE: this is what the numbers "
         "would support, not a validated edge.*", ""]
    if legs.empty:
        return L + ["**No anytime-TD leg on the slate clears the edge floor on its own, so no parlay is built.**", ""]
    L += [f"{len(legs)} legs clear the floor: " + ", ".join(
        f"{r.player} ({r.team}, {r.game}) blend {r.p_blend:.0%} vs market {r.p_market:.0%} at {int(r.price):+d} {r.book}"
        for r in legs.head(TOP_LEGS).itertuples()) + ".", ""]
    if parlays.empty:
        return L + ["No combination has one leg per game (every qualifying leg is in the same game).", ""]
    for k in sorted(parlays["legs"].unique()):
        g = parlays[parlays["legs"] == k].head(top)
        L += [f"### {k} legs", "", "| legs | fair probability | fair price | min payout (decimal = Sleeper multiplier) | "
              "model-only product | one-book product price | EV there |", "|---|---|---|---|---|---|---|"]
        for r in g.itertuples():
            bp = "" if not np.isfinite(r.book_product_decimal) else f"{r.book_product_decimal:.2f}x ({r.book})"
            ev = "" if not np.isfinite(r.ev_at_book_product) else f"{r.ev_at_book_product:+.0%}"
            L.append(f"| {r.players} | {r.p_fair:.1%} | {r.fair_american:+d} | {r.min_payout_decimal:.2f}x | "
                     f"{r.p_model_product:.1%} | {bp} | {ev} |")
        L.append("")
    L.append("Take a parlay only at or above its minimum price; below it, the legs' edges are gone.")
    return L
