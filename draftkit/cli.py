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
    "pick_timer": 60,  # commissioner changed 120 -> 60 on 2026-08-23 (caught by verify)
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
    # expectations live in the LEAGUE yaml (amendment A); the module-level
    # EXPECTED is only the fallback for pre-multi-league configs
    expected = cfg.get("expected") or EXPECTED

    console.print(f"[bold]{lg['name']}[/bold] — season {lg['season']}, status {lg['status']}"
                  + (f"  [dim](league: {cfg.league_name})[/dim]" if cfg.league_name else ""))
    checks = [
        ("teams", dr["settings"]["teams"], expected["teams"]),
        ("rounds", dr["settings"]["rounds"], expected["rounds"]),
        ("pick_timer", dr["settings"]["pick_timer"], expected["pick_timer"]),
        ("draft type", dr["type"], expected["type"]),
        ("reversal_round", dr["settings"].get("reversal_round", 0), 0),
    ]
    for name, actual, expected_v in checks:
        good = actual == expected_v
        ok &= good
        style = "green" if good else "bold red"
        console.print(f"  {name}: {actual} {'✓' if good else f'✗ expected {expected_v}'}", style=style)

    for key, exp in expected["scoring"].items():
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
    out = cfg.scoped(cfg.path("processed") / "market.parquet")
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
    from .tiers import (add_handcuff_info, add_upside_flags, build_disagreements,
                        build_tiers, write_tiers_csv)
    from .vorp import add_vorp
    from .board import write_board_markdown

    processed = cfg.path("processed")
    market = pl.read_parquet(cfg.scoped(processed / "market.parquet"))
    usage = pl.read_parquet(cfg.scoped(processed / "usage.parquet"))

    proj_fn = PROJECTION_FNS[args.projection]
    df = proj_fn(cfg, usage, market)
    from .tilts import apply_tilts, prior_top5_by_pos
    df, n_tilted = apply_tilts(df, cfg.get("tilts"), prior_top5_by_pos(usage))
    if n_tilted:
        console.print(f"  standing tilts applied to {n_tilted} players "
                      f"(league: {cfg.league_name})")
    df = add_vorp(df, cfg.baselines)
    tiers = build_tiers(df, cfg)
    tiers = add_handcuff_info(tiers)
    tiers = add_upside_flags(tiers)

    csv_path = cfg.scoped(cfg.root / "tiers.csv")
    write_tiers_csv(tiers, csv_path)
    board_path = cfg.scoped(cfg.root / "board.md")
    write_board_markdown(tiers, board_path)
    console.print(f"tiers: {tiers.height} players -> {csv_path} and {board_path}")
    by_src = tiers.group_by("proj_source").len().sort("len", descending=True)
    for row in by_src.iter_rows(named=True):
        console.print(f"  {row['proj_source']}: {row['len']}")

    adp_within = float(cfg["tiers"].get("adp_include_within", 180) or 180)
    dis = build_disagreements(tiers.rename({"name": "player"}), adp_within)
    dis_path = cfg.scoped(cfg.root / "reports" / "disagreements.csv")
    dis_path.parent.mkdir(parents=True, exist_ok=True)
    dis.write_csv(dis_path)
    console.print(f"  disagreements worklist: {dis.height} -> {dis_path}")


def cmd_board(cfg: Config, args) -> None:
    from .board import print_board

    tiers = pl.read_csv(cfg.scoped(cfg.root / "tiers.csv"), infer_schema_length=2000).rename(
        {"player": "name"}
    )
    print_board(tiers, console)


def cmd_track(cfg: Config, args) -> None:
    from .tracker import Tracker

    slot = args.slot
    if slot is None:
        if args.draft_id:
            # a mock draft's seat has nothing to do with the real league's;
            # inheriting it silently would track a stranger's roster
            console.print("[yellow]mock draft: no --slot given, running as "
                          "spectator (pass --slot N for your seat)[/yellow]")
        else:
            client = SleeperClient(cfg.path("raw"))
            slot, info = resolve_my_slot(cfg, client)
            if slot is None:
                console.print(f"[yellow]warning: {info.get('error')}; running in spectator mode[/yellow]")
    tracker = Tracker(
        cfg,
        tiers_path=cfg.scoped(cfg.root / "tiers.csv"),
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



def cmd_seasonrefresh(cfg: Config, args) -> None:
    from .briefs import build_context, record_actuals

    ctx = build_context(cfg)
    n = record_actuals(ctx)
    console.print(f"season state: {ctx['state']['season']} week {ctx['week']} "
                  f"({ctx['state']['season_type']})"
                  + (" [FALLBACK projections]" if ctx['fallback'] else ""))
    console.print(f"rosters: {len(ctx['rosters'])} | byes this week: "
                  f"{', '.join(sorted(ctx['byes'])) or 'none'} | actuals recorded: {n}"
                  + (f" | stale: {ctx['stale']}" if ctx['stale'] else ""))


def cmd_waiverbrief(cfg: Config, args) -> None:
    from .briefs import waiver_brief

    out = waiver_brief(cfg)
    console.print(f"waiver brief -> {out}")
    console.print(out.read_text(encoding="utf-8").split("## Claims")[0])


def cmd_lineupbrief(cfg: Config, args) -> None:
    from .briefs import lineup_brief

    out = lineup_brief(cfg)
    console.print(f"lineup brief -> {out}")


def cmd_earlycheck(cfg: Config, args) -> None:
    from .briefs import early_check

    out = early_check(cfg)
    console.print(f"early-games check -> {out}")


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
    local = str(cfg.get("draft_id") or "").lower() in ("", "none", "null")
    if slot is None and local:
        raw = (cfg.get("me") or {}).get("draft_slot")
        slot = int(raw) if raw else None
        if slot is None:
            console.print("[yellow]local draft: no slot yet — set me.draft_slot in the "
                          "league yaml (or the footer) when the draft order is known[/yellow]")
    elif slot is None:
        client = SleeperClient(cfg.path("raw"))
        slot, info = resolve_my_slot(cfg, client)
        if slot is None:
            console.print(f"[yellow]warning: {info.get('error')}; slot unresolved[/yellow]")
    sys.exit(run_server(cfg, cfg.scoped(cfg.root / "tiers.csv"), slot, args.port))


def cmd_simulate(cfg: Config, args) -> None:
    from .simulate import run_simulation

    from . import snake

    mine, teams = run_simulation(cfg, cfg.scoped(cfg.root / "tiers.csv"), my_slot=args.slot, verbose=not args.quiet)
    console.print("\n[bold]my simulated roster:[/bold]")
    tiers = pl.read_csv(cfg.scoped(cfg.root / "tiers.csv"), infer_schema_length=2000)
    by_id = {str(r["sleeper_id"]): r for r in tiers.iter_rows(named=True)}
    for p in mine:
        info = by_id[str(p["player_id"])]
        console.print(
            f"  R{snake.pick_to_round_slot(p['pick_no'], teams)[0]:>2} pick {p['pick_no']:>3}: "
            f"{info['player']} ({info['pos']}{info['pos_rank']}, tier {info['tier']}, "
            f"proj {info['proj_pts']:.0f}, ADP {info['adp'] if info['adp'] is not None else '—'})"
        )


def cmd_onboard(args) -> None:
    from .onboard import onboard
    out = onboard(args.league_id, args.username, args.name)
    print(f"wrote {out}")
    print(f"next: python -m draftkit --league {out.stem} verify")


def main(argv: list[str] | None = None) -> None:
    # Windows: force UTF-8 on stdout/stderr so board glyphs can never crash
    # a cp1252 console or pipe mid-draft (launchers also set PYTHONIOENCODING)
    for _stream in (sys.stdout, sys.stderr):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    parser = argparse.ArgumentParser(prog="draftkit")
    parser.add_argument("--config", default=None, help="path to config.yaml")
    parser.add_argument("--league", default=None,
                        help="league name (leagues/<name>.yaml); default from config")
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
    sub.add_parser("seasonrefresh")
    sub.add_parser("waiverbrief")
    sub.add_parser("lineupbrief")
    sub.add_parser("earlycheck")
    p = sub.add_parser("log")
    p.add_argument("--draft-id", default=None, help="draft to review (default: real draft)")
    p = sub.add_parser("web")
    p.add_argument("--port", type=int, default=8723)
    p.add_argument("--slot", type=int, default=None, help="override my draft slot")
    p = sub.add_parser("simulate")
    p.add_argument("--slot", type=int, default=6, help="my draft slot in the simulation")
    p.add_argument("--quiet", action="store_true", help="only print the final roster")
    p = sub.add_parser("onboard", help="generate leagues/<name>.yaml from a Sleeper league id")
    p.add_argument("league_id")
    p.add_argument("--name", default=None, help="league slug (default: from league name)")
    p.add_argument("--username", default="farmerjamal")

    args = parser.parse_args(argv)
    if args.cmd == "onboard":
        cmd_onboard(args)
        return
    cfg = Config.load(args.config, league=args.league)
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
        "seasonrefresh": cmd_seasonrefresh,
        "waiverbrief": cmd_waiverbrief,
        "lineupbrief": cmd_lineupbrief,
        "earlycheck": cmd_earlycheck,
        "log": cmd_log,
        "web": cmd_web,
        "simulate": cmd_simulate,
    }[args.cmd](cfg, args)


if __name__ == "__main__":
    main()
