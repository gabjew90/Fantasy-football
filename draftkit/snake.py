"""Pure snake-draft math and roster-need inference. Fully unit-tested —
the live tracker must never do this arithmetic ad hoc."""

from __future__ import annotations

FLEX_ELIGIBLE = ("RB", "WR", "TE")


def pick_to_round_slot(pick_no: int, teams: int) -> tuple[int, int]:
    """1-indexed overall pick -> (round, slot). Standard snake (no reversal)."""
    rnd = (pick_no - 1) // teams + 1
    idx = (pick_no - 1) % teams
    slot = idx + 1 if rnd % 2 == 1 else teams - idx
    return rnd, slot


def slot_pick_numbers(slot: int, teams: int, rounds: int) -> list[int]:
    """All overall pick numbers belonging to a draft slot."""
    out = []
    for rnd in range(1, rounds + 1):
        if rnd % 2 == 1:
            out.append((rnd - 1) * teams + slot)
        else:
            out.append((rnd - 1) * teams + (teams - slot + 1))
    return out


def next_pick_for_slot(current_pick: int, slot: int, teams: int, rounds: int) -> int | None:
    """First pick number >= current_pick that belongs to slot, else None."""
    for p in slot_pick_numbers(slot, teams, rounds):
        if p >= current_pick:
            return p
    return None


def slots_picking_between(current_pick: int, until_pick: int, teams: int) -> list[int]:
    """Slots that pick at [current_pick, until_pick), in order."""
    return [pick_to_round_slot(p, teams)[1] for p in range(current_pick, until_pick)]


def starter_needs(picked_positions: list[str], slots: dict[str, int]) -> dict[str, int]:
    """Remaining open starter slots given positions already drafted.

    slots: {"QB": 1, "RB": 2, "WR": 2, "TE": 1, "FLEX": 2, "K": 1, "DEF": 1}
    Returns remaining need per position plus "FLEX". A drafted RB/WR/TE fills
    its dedicated slot first, then FLEX, then bench.
    """
    remaining = {k: v for k, v in slots.items()}
    for pos in picked_positions:
        if remaining.get(pos, 0) > 0:
            remaining[pos] -= 1
        elif pos in FLEX_ELIGIBLE and remaining.get("FLEX", 0) > 0:
            remaining["FLEX"] -= 1
        # else: bench
    return remaining


def consume(needs: dict[str, int], pos: str) -> dict[str, int]:
    """Roster needs after taking one player at `pos` (dedicated slot first,
    then FLEX). Lives here so the planner and the survival simulation share
    one definition (plan B6)."""
    out = dict(needs)
    if out.get(pos, 0) > 0:
        out[pos] -= 1
    elif pos in FLEX_ELIGIBLE and out.get("FLEX", 0) > 0:
        out["FLEX"] -= 1
    return out


def needs_position(needs: dict[str, int], pos: str) -> bool:
    """Does a roster with these open slots still need a player at pos as a starter?"""
    if needs.get(pos, 0) > 0:
        return True
    return pos in FLEX_ELIGIBLE and needs.get("FLEX", 0) > 0


def roster_slots_from_draft_settings(settings: dict) -> dict[str, int]:
    return {
        "QB": settings.get("slots_qb", 0),
        "RB": settings.get("slots_rb", 0),
        "WR": settings.get("slots_wr", 0),
        "TE": settings.get("slots_te", 0),
        "FLEX": settings.get("slots_flex", 0),
        "K": settings.get("slots_k", 0),
        "DEF": settings.get("slots_def", 0),
        "BN": settings.get("slots_bn", 0),
    }
