#!/usr/bin/env python3
"""One CLI for the two use cases (docs/plans/2026-09-24-consolidation-plan.md).

  python nfl.py status [--season S] [--week W] [--league L]
  python nfl.py props game AWAY@HOME [--markets td,...] [--week W]
  python nfl.py props slate [--week W] [--skip-started] [--markets ...]
  python nfl.py fantasy lineup --league L [--week W] [--record]
  python nfl.py fantasy scenario --league L --player NAME|ID --out NAME|ID [--week W]
  python nfl.py fantasy waiver --league L [--pos RB,WR,TE] [--horizon stream|season] [--week W]
  python nfl.py fantasy trade --league L --give NAMES --get NAMES [--back NAME:WEEK]
  python nfl.py log                  # the session in ONE file: review, transcript, commands

Reports and decision records go to $NFL_OUT (default /mnt/user-data/outputs).
`--record` appends to the graded ledger. A chat session never passes it (chat
is read-only, as for the props record); the scheduled runs will, from step 6.

TROUBLESHOOTING LOG (temporary, `session_log` in config.yaml; inside a chat
release only, or with NFL_SESSION_LOG=1): every command
appends one JSON line to $NFL_OUT/nfl_session_log.jsonl -- the release, the
command and its arguments, exit code, duration, the error if one was raised,
the data gate and the inputs' freshness, and the bootstrap's setup facts. No
credential ever goes in it: arguments are player and league names, and the
setup facts are booleans.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
import sys
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):  # pragma: no cover
        pass

SCRIPTS = ROOT / "props" / "engine" / "scripts"


def _season_week(season, week):
    import pandas as pd

    from core import fetch as F
    s = season or F.current_season()
    if week:
        return s, week
    g = pd.read_csv(F.schedule(), low_memory=False)
    g = g[(g.season == s) & (g.game_type == "REG")]
    unplayed = g[g.result.isna()]
    return s, int(unplayed.week.min()) if not unplayed.empty else int(g.week.max())


def cmd_status(a) -> int:
    from core import status as ST
    league = None
    if a.league:
        from draftkit.config import Config
        from fantasy.league import roster_freshness
        league = roster_freshness(Config.load(league=a.league))
    season, week = _season_week(a.season, a.week)
    print(ST.markdown(ST.week_status(season, week, league=league)))
    return 0


def cmd_props(a) -> int:
    if a.what == "game":
        if not a.game or "@" not in a.game:
            print("props game needs AWAY@HOME", file=sys.stderr)
            return 2
        away, home = a.game.split("@", 1)
        cmd = [sys.executable, str(SCRIPTS / "score_game.py"), "--away", away, "--home", home]
    else:
        cmd = [sys.executable, str(SCRIPTS / "score_week.py")]
        if a.skip_started:
            cmd.append("--skip-started")
    if a.season:
        cmd += ["--season", str(a.season)]
    if a.week:
        cmd += ["--week", str(a.week)]
    if a.markets:
        cmd += ["--markets", a.markets]
    return subprocess.run(cmd).returncode


def cmd_fantasy(a) -> int:
    if a.what == "lineup":
        from fantasy import lineup as LU
        r = LU.run(a.league, a.week, record=a.record)
    elif a.what == "trade":
        from fantasy import trade as TR
        split = lambda v: [x.strip() for x in (v or "").split(",") if x.strip()]
        try:
            r = TR.run(a.league, split(a.give), split(a.get), back=a.back or [], week=a.week)
        except TR.TradeError as ex:
            print(f"TRADE: {ex}", file=sys.stderr)
            return 2
    elif a.what == "waiver":
        from fantasy import waiver as WV
        pos = tuple(x.strip().upper() for x in (a.pos or "RB,WR,TE").split(",") if x.strip())
        r = WV.run(a.league, pos, a.horizon, a.week)
    else:
        if not (a.player and a.out):
            print("fantasy scenario needs --player and --out", file=sys.stderr)
            return 2
        from fantasy import scenario as SC
        try:
            r = SC.run(a.league, a.player, a.out, a.week)
        except SC.ScenarioError as ex:
            print(f"SCENARIO: {ex}", file=sys.stderr)
            return 2
    a._result = r
    print(r.markdown)
    print(f"report: {r.report_path}\ndecision record: {r.record_path}")
    return 0


def session_report(out: Path) -> Path:
    """The chat session in one file, for the user to download: chat's review of
    the session (session_review.md, written by chat before it runs this), the
    verbatim transcript (chat_transcript.md), and every command the session
    ran (nfl_session_log.jsonl) as a table plus the raw lines. A part that is
    missing says so; nothing is left out silently."""
    def read(name: str, nest: bool = False) -> str | None:
        p = out / name
        if not p.exists():
            return None
        text = p.read_text(encoding="utf-8").strip()
        # a part's own headings sit one level under this file's sections
        return "\n".join("#" + ln if nest and ln.startswith("#") else ln for ln in text.splitlines())

    raw = read("nfl_session_log.jsonl") or ""
    rows = []
    for line in raw.splitlines():
        try:
            rows.append(json.loads(line))
        except ValueError:
            continue
    rows = [r for r in rows if (r.get("argv") or [None])[0] != "log"]
    releases = sorted({r.get("release") or "unknown" for r in rows}) or ["unknown"]
    failed = [r for r in rows if r.get("exit") not in (0, None) or r.get("error")]
    bad_inputs = [(r, i) for r in rows for i in (r.get("inputs") or []) if i.get("status") in ("failed", "stale")]
    setup = (rows[-1].get("setup") if rows else None) or {}
    when = (f"{rows[0]['at_utc']} to {rows[-1]['at_utc']}" if rows else "no commands logged")
    L = [f"# NFL research session -- {dt.datetime.now(dt.timezone.utc):%Y-%m-%d %H:%M} UTC", "",
         f"Release {', '.join(releases)}; {len(rows)} command(s), {when}; "
         f"{len(failed)} failed; {len(bad_inputs)} input(s) failed or stale.",
         f"Setup: source {setup.get('release_source')}, packages at setup {setup.get('deps_at_setup')}, "
         f"now {setup.get('deps_now')}, versions {setup.get('versions')}.", ""]
    L += ["## Review of the session", "",
          read("session_review.md", nest=True) or "*Chat wrote no review (session_review.md is missing).*", ""]
    L += ["## Transcript (verbatim)", "",
          read("chat_transcript.md", nest=True) or "*No transcript (chat_transcript.md is missing).*", ""]
    L += ["## Commands", ""]
    if rows:
        L += ["| UTC | Command | Exit | Seconds | Gate | Failed or stale inputs | Report |", "|---|---|---|---|---|---|---|"]
        for r in rows:
            bad = "; ".join(f"{i.get('name')}: {i.get('status')}" + (f" ({i.get('detail')})" if i.get("detail") else "")
                            for i in (r.get("inputs") or []) if i.get("status") in ("failed", "stale")) or "--"
            err = f" ERROR: {r['error']}" if r.get("error") else ""
            L.append(f"| {str(r.get('at_utc', ''))[11:19]} | `{' '.join(r.get('argv') or [])}` | {r.get('exit')}{err} | "
                     f"{r.get('seconds')} | {r.get('gate') or '--'} | {bad} | {Path(str(r.get('report') or '')).name or '--'} |")
        L += ["", "<details><summary>Raw command log (nfl_session_log.jsonl)</summary>", "", "```json", raw, "```",
              "", "</details>"]
    else:
        L += ["*No commands logged (nfl_session_log.jsonl is missing or empty).*"]
    path = out / f"nfl_session_{dt.datetime.now(dt.timezone.utc):%Y-%m-%d_%H%M}.md"
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    return path


def cmd_log(a) -> int:
    out = Path(os.environ.get("NFL_OUT", "/mnt/user-data/outputs"))
    out.mkdir(parents=True, exist_ok=True)
    print(f"session report: {session_report(out)}")
    return 0


def main(argv=None) -> int:
    try:
        from dotenv import load_dotenv
        load_dotenv(ROOT / ".env")
    except ImportError:  # pragma: no cover -- the credentials simply stay absent
        pass
    ap = argparse.ArgumentParser(prog="nfl", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("status", help="what is posted for a week, and whether a run is early")
    s.add_argument("--season", type=int)
    s.add_argument("--week", type=int)
    s.add_argument("--league")
    s.set_defaults(fn=cmd_status)

    p = sub.add_parser("props", help="price a game or the slate (the props engine)")
    p.add_argument("what", choices=("game", "slate"))
    p.add_argument("game", nargs="?")
    p.add_argument("--season", type=int)
    p.add_argument("--week", type=int)
    p.add_argument("--markets", default="")
    p.add_argument("--skip-started", action="store_true")
    p.set_defaults(fn=cmd_props)

    f = sub.add_parser("fantasy", help="fantasy decisions")
    f.add_argument("what", choices=("lineup", "scenario", "waiver", "trade"))
    f.add_argument("--league", required=True)
    f.add_argument("--week", type=int)
    f.add_argument("--record", action="store_true", help="append to the graded ledger (scheduled runs only)")
    f.add_argument("--player")
    f.add_argument("--out")
    f.add_argument("--pos", help="waiver: positions, e.g. RB,WR (default RB,WR,TE)")
    f.add_argument("--give", help="trade: players leaving my roster, comma-separated")
    f.add_argument("--get", help="trade: players arriving, comma-separated, all from one roster")
    f.add_argument("--back", action="append",
                   help="trade: NAME:WEEK, the first week a player plays (repeatable); overrides the status minimum")
    f.add_argument("--horizon", choices=("stream", "season"), default="season",
                   help="waiver: stream (this week) or season (a league-winner candidate)")
    f.set_defaults(fn=cmd_fantasy)

    lg = sub.add_parser("log", help="the chat session in one file: review, transcript, commands")
    lg.set_defaults(fn=cmd_log)

    a = ap.parse_args(argv)
    started, rc, err = time.time(), None, None
    try:
        rc = a.fn(a)
        return rc
    except BaseException as ex:  # noqa: BLE001 -- logged, then re-raised unchanged
        err = "".join(traceback.format_exception_only(type(ex), ex)).strip()
        raise
    finally:
        _session_log(argv if argv is not None else sys.argv[1:], rc, err, time.time() - started,
                     getattr(a, "_result", None))


def _gate_summary(gate) -> str | None:
    """'PASS', or 'FAIL: <the failed checks>' (fantasy commands only)."""
    if not isinstance(gate, dict):
        return None
    if gate.get("passed"):
        return "PASS"
    return "FAIL: " + "; ".join(str(c.get("name")) for c in gate.get("checks") or [] if not c.get("passed"))


def _session_log(argv, rc, err, seconds, result) -> None:
    """One line per command in $NFL_OUT/nfl_session_log.jsonl, when config.yaml
    `session_log` is on. Never raises: a log must not break the command."""
    try:
        import yaml
        cfg = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8")) or {}
        stamp = ROOT.with_name(ROOT.name + ".stamp.json")     # written by the chat bootstrap, beside the release
        # a chat shakedown aid: on inside a chat release (the stamp exists) or
        # when asked for, never silently in local or scheduled runs
        if not cfg.get("session_log") or not (stamp.exists() or os.environ.get("NFL_SESSION_LOG") == "1"):
            return
        out = Path(os.environ.get("NFL_OUT", "/mnt/user-data/outputs"))
        out.mkdir(parents=True, exist_ok=True)
        # THE RELEASE. nfl.lock.json is not part of a release (it describes
        # one), so inside chat the tag comes from the bootstrap's stamp; a
        # checkout still has the lock.
        s = json.loads(stamp.read_text(encoding="utf-8")) if stamp.exists() else {}
        lock = ROOT / "nfl.lock.json"
        release = (s.get("release_tag") or s.get("lock_tag")
                   or (json.loads(lock.read_text(encoding="utf-8")).get("tag") if lock.exists() else None))
        setup = {k: s.get(k) for k in ("release_source", "yahoo", "odds_key", "fallback_reason")} if s else {}
        # packages as they are NOW, not as the bootstrap found them: chat may
        # install one after setup, and a stale "missing" misleads the audit
        import importlib.util
        mods = {"pandas": "pandas", "numpy": "numpy", "polars": "polars", "rapidfuzz": "rapidfuzz",
                "yaml": "PyYAML", "requests": "requests", "dotenv": "python-dotenv", "nflreadpy": "nflreadpy"}
        gone = [pip for mod, pip in mods.items() if importlib.util.find_spec(mod) is None]
        setup["deps_at_setup"] = s.get("deps")
        setup["deps_now"] = "ok" if not gone else "missing: " + ", ".join(gone)
        # the chat container brings its own pandas/numpy (the bootstrap does not
        # force this repo's pins), and a newer pandas can behave differently
        from importlib import metadata as _md
        setup["versions"] = {}
        for dist in ("pandas", "numpy", "polars"):
            try:
                setup["versions"][dist] = _md.version(dist)
            except _md.PackageNotFoundError:
                setup["versions"][dist] = None
        rec = getattr(result, "record", None) or {}
        line = {"at_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "release": release,
                "argv": list(argv), "exit": rc, "seconds": round(seconds, 1), "error": err, "setup": setup,
                "gate": _gate_summary(rec.get("gate")),
                "inputs": [{k: i.get(k) for k in ("name", "source", "status", "age_h", "detail")}
                           for i in ((rec.get("manifest") or {}).get("entries") or [])][:30],
                "report": str(getattr(result, "report_path", "") or "") or None}
        with (out / "nfl_session_log.jsonl").open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(line, default=str) + "\n")
    except Exception:  # noqa: BLE001
        pass


if __name__ == "__main__":
    raise SystemExit(main())
