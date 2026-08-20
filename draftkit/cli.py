"""CLI: python -m draftkit <command>.

Commands map to build phases:
  verify   — re-pull league/draft from Sleeper, diff against expectations
  players  — refresh the cached Sleeper player universe
  market   — build the ECR/ADP market table (Phase 1)
  dataset  — pull nflverse data, compute usage metrics (Phase 2)
  tiers    — projections + VORP + tiers.csv + printable board (Phase 3)
  board    — print the tier board to the terminal
  track    — run the live draft tracker (Phase 4); --draft-id for mock drafts
"""

from __future__ import annotations

import argparse
import json
import sys

import polars as pl
from rich.console import Console

from .config import Config
from .sleeper import SleeperClient, resolve_my_slot

console = Console()

EXPECTED = {
    "teams": 12,
    "rounds": 15,
    "pick_timer": 120,
    "type": "snake",
    "scoring": {"rec": 1.0, "pass_yd": 0.04, "pass_td": 4.0, "pass_int": -1.0,
                "rush_yd": 0.1, "rec_yd": 0.1, "rush_td": 6.0, "rec_td": 6.0,
                "fum_lost": -2.0},
}


def cmd_verify(cfg: Config, args) -> None:
    client = SleeperClient(cfg.path("raw"))
    lg = client.league(cfg.league_id)
    dr = client.draft(cfg.draft_id)
    ok = True

    console.print(f"[bold]{lg['name']}[/bold] — season {lg['season']}, status {lg['status']}")
    checks = [
        ("teams", dr["settings"]["teams"], EXPECTED["teams"]),
        ("rounds", dr["settings"]["rounds"], EXPECTED["rounds"]),
        ("pick_timer", dr["settings"]["pick_timer"], EXPECTED["pick_timer"]),
        ("draft type", dr["type"], EXPECTED["type"]),
        ("reversal_round", dr["settings"].get("reversal_round", 0), 0),
    ]
    for name, actual, expected in checks:
        good = actual == expected
        ok &= good
        style = "green" if good else "bold red"
        console.print(f"  {name}: {actual} {'✓' if good else f'✗ expected {expected}'}", style=style)

    for key, exp in EXPECTED["scoring"].items():
        actual = lg["scoring_settings"].get(key)
        good = actual == exp
        ok &= good
        console.print(
            f"  scoring {key}: {actual} {'✓' if good else f'✗ expected {exp}'}",
            style="green" if good else "bold red",
        )

    console.print(f"  roster: {lg['roster_positions']}")
    reserve = lg["settings"].get("reserve_slots", 0)
    console.print(
        f"  IR/reserve slots: {reserve}"
        + (" — NOTE: handoff doc said no IR; league actually has one" if reserve else "")
    )
    console.print(f"  draft status: {dr['status']}")

    slot, info = resolve_my_slot(cfg, client)
    if slot:
        console.print(f"  my draft slot: [bold cyan]{slot}[/bold cyan] ({info.get('source')})")
    else:
        console.print(f"  my draft slot: [yellow]unresolved — {info.get('error')}[/yellow]")
    order = dr.get("draft_order") or {}
    console.print(f"  draft_order: {len(order)}/{dr['settings']['teams']} teams claimed")
    sys.exit(0 if ok else 1)


def cmd_players(cfg: Config, args) -> None:
    client = SleeperClient(cfg.path("raw"))
    players = client.players(refresh=args.refresh)
    console.print(f"player universe cached: {len(players)} players")


def cmd_market(cfg: Config, args) -> None:
    from .market import build_market

    client = SleeperClient(cfg.path("raw"))
    players = client.players()
    market, report = build_market(cfg, players)
    out = cfg.path("processed") / "market.parquet"
    market.write_parquet(out)
    console.print(f"market table: {market.height} players -> {out}")
    console.print(f"  ECR source: {report.get('ecr_source')} "
                  f"(scraped {report.get('ecr_scrape_date', 'n/a')})")
    for key in ("ecr_unmatched", "ffc_unmatched"):
        missed = report.get(key) or []
        if missed:
            console.print(f"  [yellow]{key}: {len(missed)}[/yellow] {missed[:8]}")


def cmd_dataset(cfg: Config, args) -> None:
    from . import dataset

    stats = dataset.run(cfg)
    console.print(f"usage metrics: {stats['players']} players "
                  f"({stats['with_sleeper_id']} matched to Sleeper), {stats['teams']} teams")


def cmd_tiers(cfg: Config, args) -> None:
    from .projections import PROJECTION_FNS
    from .tiers import add_handcuff_info, build_disagreements, build_tiers, write_tiers_csv
    from .vorp import add_vorp
    from .board import write_board_markdown

    processed = cfg.path("processed")
    market = pl.read_parquet(processed / "market.parquet")
    usage = pl.read_parquet(processed / "usage.parquet")

    proj_fn = PROJECTION_FNS[args.projection]
    df = proj_fn(cfg, usage, market)
    df = add_vorp(df, cfg.baselines)
    tiers = build_tiers(df, cfg)
    tiers = add_handcuff_info(tiers)

    csv_path = cfg.root / "tiers.csv"
    write_tiers_csv(tiers, csv_path)
    board_path = cfg.root / "board.md"
    write_board_markdown(tiers, board_path)
    console.print(f"tiers: {tiers.height} players -> {csv_path} and {board_path}")
    by_src = tiers.group_by("proj_source").len().sort("len", descending=True)
    for row in by_src.iter_rows(named=True):
        console.print(f"  {row['proj_source']}: {row['len']}")

    adp_within = float(cfg["tiers"].get("adp_include_within", 180) or 180)
    dis = build_disagreements(tiers.rename({"name": "player"}), adp_within)
    dis_path = cfg.root / "reports" / "disagreements.csv"
    dis_path.parent.mkdir(parents=True, exist_ok=True)
    dis.write_csv(dis_path)
    console.print(f"  disagreements worklist: {dis.height} -> {dis_path}")


def cmd_board(cfg: Config, args) -> None:
    from .board import print_board

    tiers = pl.read_csv(cfg.root / "tiers.csv", infer_schema_length=2000).rename(
        {"player": "name"}
    )
    print_board(tiers, console)


def cmd_track(cfg: Config, args) -> None:
    from .tracker import Tracker

    slot = args.slot
    if slot is None:
        client = SleeperClient(cfg.path("raw"))
        slot, info = resolve_my_slot(cfg, client)
        if slot is None and not args.draft_id:
            console.print(f"[yellow]warning: {info.get('error')}; running in spectator mode[/yellow]")
    tracker = Tracker(
        cfg,
        tiers_path=cfg.root / "tiers.csv",
        draft_id=args.draft_id,
        my_slot=slot,
    )
    tracker.run()


def cmd_rivals(cfg: Config, args) -> None:
    from .rivals import build_seeds

    client = SleeperClient(cfg.path("raw"))
    payload = build_seeds(cfg, client)
    console.print(f"rival seeds: {len(payload['users'])} users from "
                  f"{payload['history_drafts']} historical drafts -> "
                  f"{cfg.path('processed') / 'rival_seeds.json'}")


def cmd_adpdiff(cfg: Config, args) -> None:
    from .adpdiff import run as adp_run

    result = adp_run(cfg)
    console.print(f"ADP snapshot {result['date']}: {result['players']} players "
                  f"(baseline: {result['baseline'] or 'none'})")
    movers = result["movers"]
    if movers:
        console.print(f"[bold]{len(movers)} movers[/bold] -> reports/adp_movers.md")
        for m in movers[:10]:
            d = f"{'+' if m['delta'] and m['delta'] > 0 else ''}{m['delta']}" if m["delta"] is not None else m["kind"].upper()
            console.print(f"  {m['name']} ({m['pos']}) ADP {m['adp']:.1f} [{d}]")
    else:
        console.print("no movers past threshold" if result["baseline"] else "first snapshot recorded")


def cmd_log(cfg: Config, args) -> None:
    draft_id = args.draft_id or cfg.draft_id
    path = cfg.path("logs") / f"draft_{draft_id}.jsonl"
    if not path.exists():
        console.print(f"[yellow]no log yet for draft {draft_id}[/yellow]")
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        e = json.loads(line)
        at = e.get("at", "")
        if e["type"] == "status":
            console.print(f"[yellow]{at}  draft status: {e['status']}[/yellow]")
        elif e["type"] == "pick":
            mine = " [bold cyan]<- MY PICK[/bold cyan]" if e.get("my_pick") else ""
            vs = e.get("vs_adp")
            vs_s = f" {'+' if vs >= 0 else ''}{vs:.0f} vs ADP" if vs is not None else ""
            console.print(
                f"{at}  P{e['pick_no']:>3} R{e['round']:>2} slot {e['slot']:>2}: "
                f"[bold]{e['player']}[/bold] ({e.get('pos')}, T{e.get('tier')}{vs_s}){mine}"
            )
        elif e["type"] == "recs":
            console.print(f"[dim]{at}  engine before pick {e['current_pick']}:[/dim]")
            for i, r in enumerate(e.get("recommendations", []), 1):
                console.print(f"[dim]        {i}. {r['player']} ({r['pos']}) — {r['why']}[/dim]")


def cmd_web(cfg: Config, args) -> None:
    from .web import run_server

    slot = args.slot
    if slot is None:
        client = SleeperClient(cfg.path("raw"))
        slot, info = resolve_my_slot(cfg, client)
        if slot is None:
            console.print(f"[yellow]warning: {info.get('error')}; slot unresolved[/yellow]")
    sys.exit(run_server(cfg, cfg.root / "tiers.csv", slot, args.port))


def cmd_simulate(cfg: Config, args) -> None:
    from .simulate import run_simulation

    mine = run_simulation(cfg, cfg.root / "tiers.csv", my_slot=args.slot, verbose=not args.quiet)
    console.print("\n[bold]my simulated roster:[/bold]")
    tiers = pl.read_csv(cfg.root / "tiers.csv", infer_schema_length=2000)
    by_id = {str(r["sleeper_id"]): r for r in tiers.iter_rows(named=True)}
    for p in mine:
        info = by_id[str(p["player_id"])]
        console.print(
            f"  R{(p['pick_no'] - 1) // 12 + 1:>2} pick {p['pick_no']:>3}: "
            f"{info['player']} ({info['pos']}{info['pos_rank']}, tier {info['tier']}, "
            f"proj {info['proj_pts']:.0f}, ADP {info['adp'] if info['adp'] is not None else '—'})"
        )


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="draftkit")
    parser.add_argument("--config", default=None, help="path to config.yaml")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("verify")
    p = sub.add_parser("players")
    p.add_argument("--refresh", action="store_true")
    sub.add_parser("market")
    sub.add_parser("dataset")
    p = sub.add_parser("tiers")
    p.add_argument("--projection", default="default")
    sub.add_parser("board")
    p = sub.add_parser("track")
    p.add_argument("--draft-id", default=None, help="override draft id (mock draft testing)")
    p.add_argument("--slot", type=int, default=None, help="override my draft slot")
    sub.add_parser("rivals")
    sub.add_parser("adpdiff")
    p = sub.add_parser("log")
    p.add_argument("--draft-id", default=None, help="draft to review (default: real draft)")
    p = sub.add_parser("web")
    p.add_argument("--port", type=int, default=8723)
    p.add_argument("--slot", type=int, default=None, help="override my draft slot")
    p = sub.add_parser("simulate")
    p.add_argument("--slot", type=int, default=6, help="my draft slot in the simulation")
    p.add_argument("--quiet", action="store_true", help="only print the final roster")

    args = parser.parse_args(argv)
    cfg = Config.load(args.config)
    {
        "verify": cmd_verify,
        "players": cmd_players,
        "market": cmd_market,
        "dataset": cmd_dataset,
        "tiers": cmd_tiers,
        "board": cmd_board,
        "track": cmd_track,
        "rivals": cmd_rivals,
        "adpdiff": cmd_adpdiff,
        "log": cmd_log,
        "web": cmd_web,
        "simulate": cmd_simulate,
    }[args.cmd](cfg, args)


if __name__ == "__main__":
    main()
