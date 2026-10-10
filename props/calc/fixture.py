"""Write the CI fixture: a compact, exact summary of the real per-play pools
for two seasons, so the sanity tests run in CI without downloading anything.

    python -m props.calc.fixture 2022 2023

RB carry yards are kept as a histogram (every carry, order dropped). Other
positions' carries and every target are kept as counts and sums per position
(and depth bucket), enough to rebuild frames whose pool averages equal the
real ones exactly (`frames`).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from . import settings
from .checks import DataError
from .player import Bundle, depth_buckets

FIXTURES = Path(__file__).resolve().parents[1] / "tests_ci" / "fixtures"   # PR-only tests: never the capture gate
FIXTURE_SEASONS = [2022, 2023]          # tuning years only: 2024-25 are held out (design note)


def fixture_path(seasons: list[int]) -> Path:
    return FIXTURES / f"calc_pools_{'_'.join(str(s) for s in seasons)}.json"


FIXTURE = fixture_path(FIXTURE_SEASONS)


def bucket_air(fixed: dict) -> dict:
    """An air-yards value inside each depth bucket, from settings.yaml's cut
    points, used only to rebuild frames."""
    lo, hi = fixed["depth_short_below"], fixed["depth_deep_from"]
    return {"short": lo - 1.0, "medium": (lo + hi) / 2, "deep": hi + 1.0}


def summarise(seasons: list[int]) -> dict:
    fixed = settings.load()["fixed"]
    b = Bundle(seasons, fixed)
    return summarise_frames(b.with_position(b.carries), b.with_position(b.targets), fixed, seasons)


def summarise_frames(c: pd.DataFrame, t: pd.DataFrame, fixed: dict, seasons: list[int]) -> dict:
    """The fixture from carries (yards, position) and targets (yards, caught,
    air_yards, position): known-answer tested in test_calc_sanity.py."""
    missing = int(c["position"].isna().sum() + t["position"].isna().sum())
    if missing:                      # make_pools would refuse these; so does the fixture
        raise DataError(f"{missing} plays have no roster position")
    t = t.assign(bucket=depth_buckets(t["air_yards"], fixed["depth_short_below"], fixed["depth_deep_from"]))
    rb = c.loc[c["position"] == "RB", "yards"].astype(int).value_counts().sort_index()
    other = c[c["position"] != "RB"].groupby("position")["yards"].agg(["size", "sum"])
    tg = t.dropna(subset=["bucket"]).groupby(["position", "bucket"]).agg(
        n=("caught", "size"), caught=("caught", "sum"), yards=("yards", "sum"))
    return {
        "seasons": seasons,
        "rb_carry_yards": {str(k): int(v) for k, v in rb.items()},
        "other_carries": {p: [int(r["size"]), float(r["sum"])] for p, r in other.iterrows()},
        "targets": [[p, bk, int(r["n"]), int(r["caught"]), float(r["yards"])] for (p, bk), r in tg.iterrows()],
        # make_pools leaves these out of the depth groups but counts them in the league averages
        "targets_without_depth": [[p, int(g["caught"].size), int(g["caught"].sum()), float(g["yards"].sum())]
                                  for p, g in t[t["bucket"].isna()].groupby("position")],
    }


def frames(fx: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Carries and targets frames rebuilt from the fixture."""
    air = bucket_air(settings.load()["fixed"])
    rb = np.repeat([float(k) for k in fx["rb_carry_yards"]], list(fx["rb_carry_yards"].values()))
    parts = [pd.DataFrame({"yards": rb, "position": "RB"})]
    for pos, (n, total) in fx["other_carries"].items():
        parts.append(pd.DataFrame({"yards": np.full(n, total / n), "position": pos}))
    c = pd.concat(parts, ignore_index=True)
    groups = fx["targets"] + [[p, None, n, c_, y] for p, n, c_, y in fx.get("targets_without_depth", [])]
    rows = []
    for pos, bk, n, caught, yards in groups:          # bk None: no recorded depth
        per = yards / caught if caught else 0.0
        rows.append(pd.DataFrame({"yards": [per] * caught + [0.0] * (n - caught),
                                  "caught": [True] * caught + [False] * (n - caught),
                                  "air_yards": air[bk] if bk else np.nan, "position": pos}))
    return c, pd.concat(rows, ignore_index=True)


if __name__ == "__main__":
    from .__main__ import _utf8
    _utf8()                                        # repo rule: UTF-8 console on the Windows host
    yrs = [int(x) for x in sys.argv[1:]] or FIXTURE_SEASONS
    out = fixture_path(yrs)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summarise(yrs), indent=0, sort_keys=True), encoding="utf-8")
    print(f"wrote {out}")
