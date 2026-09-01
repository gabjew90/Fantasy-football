"""Manual projection overrides, and the freshness contract on them.

`date_checked` means ONE thing: the date the FACT was verified against a
dated source. It is not the date the row was edited, ported, rescaled or
re-typed. That distinction is the whole point of this module.

It failed once already. The five rows in overrides.keefamania.csv carried
`date_checked: 2026-08-31` while their `source` column said "porting
2026-08-19 research to half-PPR" -- the facts were twelve days old and the
only thing that happened on the 31st was a ratio rescale. A stale fact
recorded as fresh is worse than a missing one: a missing override costs a
few projection points, a falsely fresh one corrupts the record you use to
judge everything else.

So freshness is now structural rather than a matter of discipline:

    status = confirmed   the fact was re-verified on date_checked, against
                         a real dated source in `source`. Applied.
    status = candidate   plausible, not currently verified. INERT -- the
                         model's own number stands, and the row is reported
                         as pending re-verification.

A file with no `status` column at all is treated as ALL CANDIDATE. That is
deliberately the unsafe-looking default: an unmarked file predates the
contract, so nothing in it has been checked under the contract.

Promotion to `confirmed` happens only in the draft-morning research pass, by
re-verifying the fact fresh. Nothing may be promoted because time ran out.
"""

from __future__ import annotations

from pathlib import Path

import polars as pl

CONFIRMED = "confirmed"
CANDIDATE = "candidate"
STATUS_COL = "status"


def read(path: Path) -> pl.DataFrame | None:
    """The override file, or None when there isn't one."""
    if not path.exists():
        return None
    ov = pl.read_csv(path, infer_schema_length=1000)
    if "sleeper_id" not in ov.columns or "proj_pts" not in ov.columns:
        return None
    return ov


def split(ov: pl.DataFrame) -> tuple[pl.DataFrame, pl.DataFrame]:
    """(confirmed, candidate). Anything not explicitly confirmed is candidate."""
    if STATUS_COL not in ov.columns:
        return ov.clear(), ov
    norm = (
        pl.col(STATUS_COL).cast(pl.Utf8).str.strip_chars().str.to_lowercase()
    )
    ok = ov.with_columns(norm.alias("_s"))
    return (ok.filter(pl.col("_s") == CONFIRMED).drop("_s"),
            ok.filter(pl.col("_s") != CONFIRMED).drop("_s"))


def pending(path: Path) -> list[dict]:
    """Candidate rows, for the build report and the draft-day preflight."""
    ov = read(path)
    if ov is None:
        return []
    _confirmed, cand = split(ov)
    cols = [c for c in ("sleeper_id", "name", "proj_pts", "date_checked",
                        "source", "reason") if c in cand.columns]
    return list(cand.select(cols).iter_rows(named=True))
