"""python -m props.calc <command>

  capture                 save the current Sleeper lines (four markets)
  settle --season 2026    add actual workloads and results to logged legs
  summary --season 2026   needed vs actual workload, legs won vs break-even, by gap
"""

from __future__ import annotations

import argparse
import sys

from . import capture, data, log, settings


def _utf8() -> None:
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass


def main(argv: list[str] | None = None) -> int:
    _utf8()
    ap = argparse.ArgumentParser(prog="python -m props.calc", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("capture")
    for name in ("settle", "summary"):
        sub.add_parser(name).add_argument("--season", type=int, required=True)
    a = ap.parse_args(argv)

    if a.cmd == "capture":
        r = capture.run()
        print(f"Saved {r['rows']} lines captured at {r['captured_at_utc']} to {r['path']}.")
        if r["misses"]:
            print(f"{r['misses']} players could not be matched; see {capture.MISSES_PATH}.")
        return 0
    if a.cmd == "settle":
        games = data.player_games(data.pbp(a.season))
        n = log.settle(a.season, games)
        print(f"Settled {n} legs.")
        return 0
    if a.cmd == "summary":
        edges = settings.load()["fixed"]["gap_edges"]
        rows = log.summary(a.season, edges)
        if not rows:
            print("No settled legs yet.")
        for r in rows:
            print(f"{r['market']}, gap {r['gap']}: {r['won']} of {r['legs']} won "
                  f"(break-even {r['break_even']:.0%}); needed {r['needed']:.1f}, got {r['actual']:.1f} on average")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
