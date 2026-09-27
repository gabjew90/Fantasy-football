"""model.normalize_depth_charts, modern (timestamped) schema.

props-v1.26 replaced a loop that filtered the whole depth-chart table once per
(team, week) -- 8 of a live game's 11 seconds -- with a per-team snapshot
lookup. The contract is that nothing changes: each (team, week) takes the
team's LATEST snapshot STRICTLY before kickoff, its QB1 / RB1-2 / WR1-3 / TE1
in the table's row order. The old loop is kept here as the reference and both
are run on the same table, edge cases included.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ENGINE = Path(__file__).resolve().parents[1] / "engine" / "scripts"
sys.path.insert(0, str(ENGINE))

import model as M  # noqa: E402


def reference(dc, kick_lookup):
    """The pre-v1.26 loop, verbatim in effect."""
    d = dc.copy()
    d["dt"] = pd.to_datetime(d["dt"], errors="coerce", utc=True)
    d = d.dropna(subset=["dt"])
    d = d[d.pos_abb.isin(["QB", "RB", "WR", "TE"])]
    out = []
    for (team, wk), kt in (kick_lookup or {}).items():
        sub = d[(d.team == team) & (d.dt < kt)]
        if sub.empty:
            continue
        sub = sub[sub.dt == sub.dt.max()]
        for pos, mx in [("QB", 1), ("RB", 2), ("WR", 3), ("TE", 1)]:
            for _, x in sub[(sub.pos_abb == pos) & (sub.pos_rank <= mx)].iterrows():
                out.append({"team": team, "week": wk, "gsis_id": x.gsis_id, "slot": f"{pos}{int(x.pos_rank)}"})
    return pd.DataFrame(out).drop_duplicates(["team", "week", "gsis_id"])


T = lambda s: pd.Timestamp(s, tz="UTC")   # noqa: E731


def _table():
    rows = []
    # KC: two snapshots; the later one promotes a new WR1 and lists ranks out of order
    for dt, wrs in (("2026-09-10T12:00Z", ["kc_wr_a", "kc_wr_b", "kc_wr_c", "kc_wr_d"]),
                    ("2026-09-17T12:00Z", ["kc_wr_b", "kc_wr_a", "kc_wr_c"])):
        rows += [dict(dt=dt, team="KC", pos_abb="QB", pos_rank=1, gsis_id="kc_qb"),
                 dict(dt=dt, team="KC", pos_abb="QB", pos_rank=2, gsis_id="kc_qb2"),
                 dict(dt=dt, team="KC", pos_abb="TE", pos_rank=1, gsis_id="kc_te"),
                 dict(dt=dt, team="KC", pos_abb="K", pos_rank=1, gsis_id="kc_k")]
        rows += [dict(dt=dt, team="KC", pos_abb="WR", pos_rank=r + 1, gsis_id=g) for r, g in enumerate(wrs)][::-1]
        rows += [dict(dt=dt, team="KC", pos_abb="RB", pos_rank=2, gsis_id="kc_rb2"),
                 dict(dt=dt, team="KC", pos_abb="RB", pos_rank=1, gsis_id="kc_rb1")]
    rows += [dict(dt="2026-09-12T00:00Z", team="BUF", pos_abb="QB", pos_rank=1, gsis_id="buf_qb"),
             dict(dt="not a time", team="BUF", pos_abb="QB", pos_rank=1, gsis_id="junk"),
             dict(dt="2026-09-12T00:00Z", team="BUF", pos_abb="RB", pos_rank=None, gsis_id="buf_rb_norank"),
             dict(dt="2026-09-12T00:00Z", team=None, pos_abb="QB", pos_rank=1, gsis_id="no_team")]
    return pd.DataFrame(rows)


KICKS = {("KC", 1): T("2026-09-11T00:00Z"),          # between the two snapshots: the first
         ("KC", 2): T("2026-09-17T12:00Z"),          # EXACTLY at the second: strictly-before takes the first
         ("KC", 3): T("2026-09-20T00:00Z"),          # after both: the second
         ("KC", 0): T("2026-09-01T00:00Z"),          # before any snapshot: nothing
         ("BUF", 1): T("2026-09-14T00:00Z"),         # an unparseable dt is dropped, a missing rank never seats
         ("NYJ", 1): T("2026-09-14T00:00Z")}         # a team the table lacks


def test_the_snapshot_lookup_matches_the_old_loop_row_for_row():
    dc = _table()
    new, old = M.normalize_depth_charts(dc, KICKS), reference(dc, KICKS)
    assert new.to_csv() == old.to_csv()


def test_it_takes_the_latest_snapshot_strictly_before_kickoff():
    out = M.normalize_depth_charts(_table(), KICKS)
    wr1 = {wk: g.loc[g.slot == "WR1", "gsis_id"].item() for wk, g in out[out.team == "KC"].groupby("week")}
    assert wr1 == {1: "kc_wr_a", 2: "kc_wr_a", 3: "kc_wr_b"}
    assert 0 not in set(out[out.team == "KC"].week), "no snapshot before kickoff, no roles"
    assert set(out[out.team == "BUF"].gsis_id) == {"buf_qb"}
    assert "NYJ" not in set(out.team) and "no_team" not in set(out.gsis_id), "a row without a team seats nobody"
    assert "kc_wr_d" not in set(out.gsis_id) and "kc_qb2" not in set(out.gsis_id) and "kc_k" not in set(out.gsis_id)
