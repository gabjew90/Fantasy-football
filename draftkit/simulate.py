"""Dry-run draft simulation through the real Tracker code path.

Rival slots pick by ADP (ECR fallback); my slot takes the tracker's #1
recommendation. Prints the board at each of my picks and the final roster.
This exercises everything except the HTTP polling loop — for that, point
`python -m draftkit track --draft-id <mock_id>` at a Sleeper mock draft lobby.
"""

from __future__ import annotations

from rich.console import Console

from . import snake
from .tracker import Tracker


class SimTracker(Tracker):
    """Tracker with the network poll replaced by an injected pick list."""

    def poll(self) -> bool:  # pragma: no cover - trivial
        return True

    def inject(self, picks: list[dict], status: str = "drafting") -> None:
        self.state.picks = picks
        self.state.drafted_ids = {str(p["player_id"]) for p in picks}
        self.state.status = status


def run_simulation(cfg, tiers_path, my_slot: int, verbose: bool = True) -> list[dict]:
    console = Console()
    t = SimTracker(cfg, tiers_path=tiers_path, my_slot=my_slot)
    total = t.teams * t.rounds
    by_adp = sorted(
        t.players,
        key=lambda p: (
            p["adp"] if p.get("adp") is not None else (p["ecr"] if p.get("ecr") is not None else 999)
        ),
    )
    picks: list[dict] = []

    def take(player: dict, pick_no: int, slot: int) -> None:
        picks.append(
            {
                "player_id": player["sleeper_id"],
                "draft_slot": slot,
                "pick_no": pick_no,
                "metadata": {"position": player["pos"]},
            }
        )

    for pick_no in range(1, total + 1):
        t.inject(picks)
        rnd, slot = snake.pick_to_round_slot(pick_no, t.teams)
        if slot == my_slot:
            recs = t.recommendations(top_n=1)
            if not recs:
                remaining = [p for p in by_adp if p["sleeper_id"] not in t.state.drafted_ids]
                choice, why = remaining[0], "adp fallback"
            else:
                score, why, choice = recs[0]
            if verbose:
                console.rule(f"MY PICK {pick_no} (R{rnd})")
                console.print(t.render())
                console.print(f"[bold green]-> {choice['player']} ({choice['pos']}) — {why}[/bold green]")
            take(choice, pick_no, slot)
        else:
            # rivals draft by ADP but respect basic roster limits and lateness
            needs = snake.starter_needs(t.slot_positions(slot), t.slots)
            remaining = [p for p in by_adp if p["sleeper_id"] not in t.state.drafted_ids]
            choice = None
            for p in remaining:
                pos = p["pos"]
                if pos in ("K", "DEF"):
                    if rnd < 13 or not snake.needs_position(needs, pos):
                        continue
                choice = p
                break
            choice = choice or remaining[0]
            take(choice, pick_no, slot)

    t.inject(picks, status="complete")
    if verbose:
        console.rule("FINAL")
        console.print(t.render())
    mine = [p for p in picks if p["draft_slot"] == my_slot]
    return mine
