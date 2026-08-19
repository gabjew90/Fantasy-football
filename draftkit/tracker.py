"""Phase 4 — live draft tracker.

Single-process terminal app. Polls the Sleeper picks endpoint (default every
5s), diffs against last state, and renders a tier board + recommendations from
precomputed tiers.csv — no model or network work in the hot path, so the
on-clock render is instant. Resumable by construction: state is rebuilt from
the full picks list on every poll, so restarting mid-draft loses nothing.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path

import polars as pl
from rich.console import Console, Group
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from . import snake
from .sleeper import SleeperClient, get_json, BASE

POS_ORDER = ["RB", "WR", "TE", "QB", "K", "DEF"]


@dataclass
class TrackerState:
    picks: list[dict] = field(default_factory=list)
    drafted_ids: set[str] = field(default_factory=set)
    last_poll_ok: float = 0.0
    last_error: str | None = None
    status: str = "unknown"


class Tracker:
    def __init__(
        self,
        cfg,
        tiers_path: Path,
        draft_id: str | None = None,
        my_slot: int | None = None,
    ):
        self.cfg = cfg
        self.client = SleeperClient(cfg.path("raw"))
        self.draft_id = draft_id or cfg.draft_id
        self.draft = self.client.draft(self.draft_id)
        self.teams = int(self.draft["settings"]["teams"])
        self.rounds = int(self.draft["settings"]["rounds"])
        self.slots = snake.roster_slots_from_draft_settings(self.draft["settings"])
        self.my_slot = my_slot
        tcfg = cfg["tracker"]
        self.poll_seconds = float(tcfg["poll_seconds"])
        self.kdef_round = int(tcfg["kdef_earliest_round"])
        self.fall_alert = int(tcfg["fall_alert_picks"])

        tiers = pl.read_csv(tiers_path, infer_schema_length=2000)
        self.players = [r for r in tiers.iter_rows(named=True)]
        for p in self.players:
            p["sleeper_id"] = str(p["sleeper_id"])
        self.by_id = {p["sleeper_id"]: p for p in self.players}
        self.state = TrackerState()

    # ---------- state ----------

    def poll(self) -> bool:
        """Fetch picks; returns True if new picks arrived. Retries with backoff."""
        try:
            picks = get_json(f"{BASE}/draft/{self.draft_id}/picks", retries=3)
            draft = get_json(f"{BASE}/draft/{self.draft_id}", retries=1)
            self.state.status = draft.get("status", "unknown")
        except Exception as e:  # noqa: BLE001
            self.state.last_error = str(e)[:120]
            return False
        self.state.last_error = None
        self.state.last_poll_ok = time.time()
        changed = len(picks) != len(self.state.picks)
        self.state.picks = picks
        self.state.drafted_ids = {str(p["player_id"]) for p in picks}
        return changed

    @property
    def current_pick(self) -> int:
        return len(self.state.picks) + 1

    def picks_for_slot(self, slot: int) -> list[dict]:
        return [p for p in self.state.picks if int(p.get("draft_slot", 0)) == slot]

    def slot_positions(self, slot: int) -> list[str]:
        out = []
        for p in self.picks_for_slot(slot):
            pos = (p.get("metadata") or {}).get("position")
            if not pos:
                info = self.by_id.get(str(p["player_id"]))
                pos = info["pos"] if info else "?"
            out.append({"DST": "DEF"}.get(pos, pos))
        return out

    def remaining(self, pos: str | None = None) -> list[dict]:
        pool = [p for p in self.players if p["sleeper_id"] not in self.state.drafted_ids]
        if pos:
            pool = [p for p in pool if p["pos"] == pos]
        return sorted(pool, key=lambda p: -(p["vorp"] if p["vorp"] is not None else -999))

    # ---------- analysis ----------

    def my_needs(self) -> dict[str, int]:
        assert self.my_slot
        return snake.starter_needs(self.slot_positions(self.my_slot), self.slots)

    def intervening_slots(self) -> list[int]:
        if not self.my_slot:
            return []
        nxt = snake.next_pick_for_slot(self.current_pick, self.my_slot, self.teams, self.rounds)
        if nxt is None:
            return []
        return [
            s
            for s in snake.slots_picking_between(self.current_pick, nxt, self.teams)
            if s != self.my_slot
        ]

    def cliff_report(self) -> dict[str, dict]:
        """Per position: picks of runway before the next cliff, vs. intervening demand."""
        inter = self.intervening_slots()
        demand: dict[str, int] = {}
        for s in inter:
            needs = snake.starter_needs(self.slot_positions(s), self.slots)
            for pos in POS_ORDER:
                if snake.needs_position(needs, pos):
                    demand[pos] = demand.get(pos, 0) + 1
        report = {}
        for pos in POS_ORDER:
            rem = self.remaining(pos)
            before_cliff = None
            for i, p in enumerate(rem):
                if p["cliff_flag"]:
                    before_cliff = i + 1  # players available at/above the cliff edge
                    break
            report[pos] = {
                "before_cliff": before_cliff,
                "intervening_demand": demand.get(pos, 0),
                "urgent": before_cliff is not None
                and demand.get(pos, 0) >= before_cliff,
            }
        return report

    def fallers(self, limit: int = 5) -> list[dict]:
        out = []
        for p in self.remaining():
            adp = p.get("adp")
            if adp is not None and self.current_pick - adp >= self.fall_alert:
                out.append(p)
        return sorted(out, key=lambda p: -(self.current_pick - p["adp"]))[:limit]

    def kdef_allowed(self, rnd: int) -> bool:
        if rnd >= self.kdef_round:
            return True
        if not self.my_slot:
            return False
        needs = self.my_needs()
        picks_left = self.rounds - len(self.picks_for_slot(self.my_slot))
        kdef_needed = needs.get("K", 0) + needs.get("DEF", 0)
        return picks_left <= kdef_needed

    def recommendations(self, top_n: int = 5) -> list[tuple[float, str, dict]]:
        """Score = VORP + escalating starter-need bonus + cliff urgency + faller bonus.

        Hard constraint: once remaining picks <= open starter slots, only
        positions that fill a starter slot are recommended (no more bench
        luxury picks while the QB slot sits empty).
        """
        rnd, _ = snake.pick_to_round_slot(self.current_pick, self.teams)
        needs = self.my_needs() if self.my_slot else {}
        cliff = self.cliff_report()
        allow_kdef = self.kdef_allowed(rnd)

        must_fill_only = False
        my_pos_counts: dict[str, int] = {}
        if self.my_slot:
            for pos in self.slot_positions(self.my_slot):
                my_pos_counts[pos] = my_pos_counts.get(pos, 0) + 1
            picks_left = self.rounds - len(self.picks_for_slot(self.my_slot))
            open_starters = sum(needs.get(k, 0) for k in ("QB", "RB", "WR", "TE", "FLEX", "K", "DEF"))
            must_fill_only = picks_left <= open_starters

        scored = []
        for p in self.remaining()[:80]:
            pos = p["pos"]
            if pos in ("K", "DEF") and not allow_kdef:
                continue
            fills_starter = not self.my_slot or snake.needs_position(needs, pos)
            if must_fill_only and not fills_starter:
                continue
            vorp = p["vorp"] or 0.0
            score = float(vorp)
            why = []
            if self.my_slot and fills_starter:
                if needs.get(pos, 0) > 0:
                    # dedicated slot still open — pressure grows with the round
                    score += 10 + 1.5 * rnd
                    why.append(f"fills {pos} starter slot")
                else:
                    score += 8
                    why.append("fills FLEX")
            elif self.my_slot:
                # bench depth: fine, but discourage hoarding one position
                starters_at_pos = self.slots.get(pos, 0) + (
                    self.slots.get("FLEX", 0) if pos in snake.FLEX_ELIGIBLE else 0
                )
                excess = my_pos_counts.get(pos, 0) - starters_at_pos
                if excess >= 0:
                    score -= 5.0 * (excess + 1)
            if cliff.get(pos, {}).get("urgent") and fills_starter:
                score += 8
                why.append(
                    f"cliff: {cliff[pos]['before_cliff']} left, "
                    f"{cliff[pos]['intervening_demand']} teams between picks need {pos}"
                )
            adp = p.get("adp")
            if adp is not None and self.current_pick - adp > 0:
                bonus = min(6.0, 0.25 * (self.current_pick - adp))
                score += bonus
                if self.current_pick - adp >= self.fall_alert:
                    why.append(f"fell {self.current_pick - adp:.0f} past ADP")
            scored.append((score, ", ".join(why) or "best value", p))
        scored.sort(key=lambda t: -t[0])
        return scored[:top_n]

    # ---------- render ----------

    def render(self) -> Layout:
        s = self.state
        cur = self.current_pick
        rnd, slot_on_clock = snake.pick_to_round_slot(min(cur, self.teams * self.rounds), self.teams)
        on_clock_me = self.my_slot is not None and slot_on_clock == self.my_slot

        header = Text()
        header.append(f" {self.draft_id}  ", style="dim")
        header.append(f"status: {s.status}  ")
        if s.status == "complete":
            header.append("DRAFT COMPLETE", style="bold green")
        else:
            header.append(f"pick {cur} (R{rnd}.{(cur - 1) % self.teams + 1})  slot {slot_on_clock} on clock  ")
        if self.my_slot:
            nxt = snake.next_pick_for_slot(cur, self.my_slot, self.teams, self.rounds)
            if on_clock_me and s.status == "drafting":
                header.append("  >>> YOU ARE ON THE CLOCK <<<", style="bold white on red")
            elif nxt:
                header.append(f"my next pick: {nxt} ({nxt - cur} away)", style="cyan")
        if s.last_error:
            header.append(f"  [poll error: {s.last_error}]", style="red")

        # positional board: top 3 remaining per position
        board = Table(show_header=True, header_style="bold", expand=True)
        board.add_column("Pos", width=4)
        board.add_column("Top remaining (tier | VORP | ADPΔ)", overflow="fold")
        cliff = self.cliff_report()
        for pos in POS_ORDER:
            rem = self.remaining(pos)[:3]
            cells = []
            for p in rem:
                adp_d = ""
                if p.get("adp") is not None:
                    d = cur - p["adp"]
                    adp_d = f" {'+' if d >= 0 else ''}{d:.0f}v" if abs(d) >= 3 else ""
                mark = "⛰" if p["cliff_flag"] else ""
                cells.append(f"[bold]{p['player']}[/bold]{mark} (T{p['tier']}|{p['vorp']:.0f}{adp_d})")
            c = cliff.get(pos, {})
            tag = ""
            if c.get("urgent"):
                tag = f" [red bold]CLIFF NOW ({c['before_cliff']} left, {c['intervening_demand']} rivals)[/red bold]"
            elif c.get("before_cliff") is not None and c["before_cliff"] <= 3:
                tag = f" [yellow]cliff in {c['before_cliff']}[/yellow]"
            board.add_row(pos, "   ".join(cells) + tag)

        panels = [Panel(header, title="draft"), Panel(board, title="board")]

        if self.my_slot:
            needs = self.my_needs()
            my_pos = self.slot_positions(self.my_slot)
            roster_line = "  ".join(
                f"{k}:{self.slots[k] - needs.get(k, 0)}/{self.slots[k]}"
                for k in ("QB", "RB", "WR", "TE", "FLEX", "K", "DEF")
            )
            bench_used = max(0, len(my_pos) - sum(self.slots[k] - needs.get(k, 0) for k in ("QB", "RB", "WR", "TE", "FLEX", "K", "DEF")))
            roster_line += f"  BN:{bench_used}/{self.slots['BN']}"
            drafted_names = ", ".join(
                (self.by_id.get(str(p["player_id"]), {}).get("player")
                 or f"{(p.get('metadata') or {}).get('first_name','?')} {(p.get('metadata') or {}).get('last_name','')}")
                for p in self.picks_for_slot(self.my_slot)
            ) or "—"
            recs = self.recommendations()
            rec_lines = []
            for score, why, p in recs:
                rec_lines.append(
                    f"[bold]{p['player']}[/bold] {p['pos']}{p['pos_rank']} "
                    f"T{p['tier']} VORP {p['vorp']:.0f} — {why}"
                )
            panels.append(
                Panel(
                    Group(
                        Text.from_markup(f"[bold]{roster_line}[/bold]"),
                        Text(f"drafted: {drafted_names}", style="dim"),
                        Text.from_markup("\n".join(rec_lines) or "no candidates"),
                    ),
                    title="my roster & picks to make",
                    border_style="red" if on_clock_me else "cyan",
                )
            )

        fallers = self.fallers()
        if fallers:
            fl = "   ".join(
                f"{p['player']} ({p['pos']}, ADP {p['adp']:.0f}, -{cur - p['adp']:.0f})"
                for p in fallers
            )
            panels.append(Panel(Text.from_markup(fl), title="value fallers (≥1 round past ADP)", border_style="yellow"))

        layout = Layout()
        layout.update(Group(*panels))
        return layout

    # ---------- loop ----------

    def run(self) -> None:
        console = Console()
        console.print(
            f"[bold]draftkit tracker[/bold] — draft {self.draft_id}, "
            f"{self.teams} teams, {self.rounds} rounds, my slot: {self.my_slot or 'unknown (spectator mode)'}"
        )
        self.poll()
        backoff = self.poll_seconds
        with Live(self.render(), console=console, refresh_per_second=2, screen=False) as live:
            while True:
                time.sleep(backoff)
                changed = self.poll()
                if self.state.last_error:
                    backoff = min(backoff * 2, 60)
                else:
                    backoff = self.poll_seconds
                if changed or True:
                    live.update(self.render())
                if self.state.status == "complete":
                    live.update(self.render())
                    break
        console.print("[green]Draft complete.[/green] Final roster above — good luck in the playoffs.")
