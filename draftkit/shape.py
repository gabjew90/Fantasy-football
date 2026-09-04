"""The league's STARTING LINEUP shape, from data rather than a literal.

`draftkit/briefs.py` carried `SLOTS = {QB 1, RB 2, WR 2, TE 1, K 1, DEF 1}` and
`FLEX = 2` as module constants, and the manager imported them. Those are
Omnibeta's facts, so every lineup the manager optimised for any other league
filled ten starters into a nine-starter roster: start/sit, the swap list, the
scout margin and the opponent projection were all computed against a lineup
that could not legally be set. `tests/test_multileague.py`'s hygiene guard only
greps for names and ids, so shape literals slipped straight through it.

This module is the one place that turns a roster-position list into integer
starting slots. `draftkit/onboard.py::slot_counts` answers a different question
(fractional DRAFT demand, flex spread across positions) and cannot be reused
for a lineup, but its slot vocabulary can be and is.

Resolution prefers the live league object, because it is what the platform will
actually enforce this week, and falls back to the league yaml's `expected:`
block for a league with no pollable API. Both missing is a loud error: a guessed
lineup shape is the defect this module exists to remove.
"""

from __future__ import annotations

from dataclasses import dataclass, field


NON_DEMAND = ("BN", "BENCH", "IR", "IR+", "NA", "TAXI")
DEDICATED = ("QB", "RB", "WR", "TE", "K", "DEF")

# A flex slot is its ELIGIBILITY SET, not a name. draftkit/onboard.py keeps its
# own name lists for fractional DRAFT demand and puts "W/T" (a WR/TE slot) in
# FLEX_NAMES and "W/R" (a WR/RB slot) in REC_FLEX_NAMES; that conflation is
# harmless when the answer is a demand weight and wrong when the answer is who
# may legally start. So the lineup vocabulary is spelled out here.
FLEX_ELIGIBILITY: dict[str, frozenset[str]] = {}
for _names, _elig in (
    (("FLEX", "W/R/T", "WRT", "R/W/T"), ("RB", "WR", "TE")),
    (("REC_FLEX", "W/T", "WT"), ("WR", "TE")),
    (("WRRB_FLEX", "W/R", "R/W"), ("RB", "WR")),
    (("SUPER_FLEX", "SUPERFLEX", "Q/W/R/T", "W/R/T/QB", "OP"), ("QB", "RB", "WR", "TE")),
):
    for _n in _names:
        FLEX_ELIGIBILITY[_n] = frozenset(_elig)

STANDARD_FLEX = frozenset(("RB", "WR", "TE"))
REC_FLEX = frozenset(("WR", "TE"))
SUPER_FLEX = frozenset(("QB", "RB", "WR", "TE"))


@dataclass(frozen=True)
class LeagueShape:
    slots: dict[str, int] = field(default_factory=dict)
    #: one entry per flex slot, holding the positions that slot may start.
    #: A tuple of sets rather than a count per variety: a league that invents
    #: a fourth flex kind needs no new field, and the lineup filler needs no
    #: new branch.
    flex_slots: tuple[frozenset[str], ...] = ()
    bench: int = 0
    source: str = "?"

    @property
    def flex(self) -> int:
        return sum(1 for e in self.flex_slots if e == STANDARD_FLEX)

    @property
    def rec_flex(self) -> int:
        return sum(1 for e in self.flex_slots if e == REC_FLEX)

    @property
    def superflex(self) -> int:
        return sum(1 for e in self.flex_slots if e == SUPER_FLEX)

    @property
    def n_starters(self) -> int:
        return sum(self.slots.values()) + len(self.flex_slots)


def starting_slots(roster_positions, source: str = "?") -> LeagueShape:
    """Integer starting slots from a roster-position list.

    Bench and IR carry no lineup slot. An unrecognised STARTING slot raises,
    matching onboard.slot_counts: silently dropping one understates the lineup
    and the failure is invisible downstream.
    """
    slots = {p: 0 for p in DEDICATED}
    flex_slots: list[frozenset[str]] = []
    bench = 0
    unknown: list[str] = []
    for raw in (roster_positions or []):
        s = str(raw).upper().strip()
        if s in slots:
            slots[s] += 1
        elif s in FLEX_ELIGIBILITY:
            flex_slots.append(FLEX_ELIGIBILITY[s])
        elif s in ("BN", "BENCH"):
            bench += 1
        elif s in NON_DEMAND:
            pass
        else:
            unknown.append(s)
    if unknown:
        raise ValueError(
            f"unrecognised roster slots {sorted(set(unknown))} in the starting "
            "lineup -- add them to shape.FLEX_ELIGIBILITY with the positions "
            "they may start (or to NON_DEMAND) rather than letting them drop "
            "out of the lineup shape")
    # most restrictive first, so the filler can stay a simple greedy pass
    return LeagueShape(slots=dict(slots),
                       flex_slots=tuple(sorted(flex_slots, key=len)),
                       bench=bench, source=source)


def shape_for(cfg, league: dict | None = None) -> tuple[LeagueShape, list[str]]:
    """(shape, warnings). Live `league["roster_positions"]` wins; the league
    yaml's `expected.roster` is the fallback. A disagreement is reported, not
    resolved: that is what `draftkit verify` is for."""
    warnings: list[str] = []
    live = list((league or {}).get("roster_positions") or [])
    yaml_roster = list(((cfg.get("expected") or {}).get("roster")) or [])

    live_shape = starting_slots(live, "sleeper roster_positions") if live else None
    yaml_shape = (starting_slots(yaml_roster, f"leagues/{cfg.league_name}.yaml expected.roster")
                  if yaml_roster else None)

    if live_shape and yaml_shape and (
            live_shape.slots != yaml_shape.slots
            or live_shape.flex_slots != yaml_shape.flex_slots):
        warnings.append(
            f"roster shape disagrees: live says {live_shape.n_starters} starters "
            f"{live_shape.slots} flex {live_shape.flex}, "
            f"leagues/{cfg.league_name}.yaml says {yaml_shape.n_starters} starters "
            f"{yaml_shape.slots} flex {yaml_shape.flex}. Using live; run verify.")
    shape = live_shape or yaml_shape
    if shape is None:
        raise ValueError(
            f"no roster shape for league {cfg.league_name!r}: the live league object "
            "carries no roster_positions and expected.roster is empty in "
            f"leagues/{cfg.league_name}.yaml. A guessed lineup shape is exactly the "
            "defect this refuses to reintroduce.")
    return shape, warnings
