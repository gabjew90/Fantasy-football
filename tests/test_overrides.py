"""Override freshness contract (Phase 1 item 1).

overrides.keefamania.csv carried date_checked 2026-08-31 on five rows whose
facts were the 2026-08-19 research, ratio-scaled to half-PPR. Nothing was
verified on the 31st. Freshness is now structural: only `confirmed` rows are
applied, and promotion requires re-verifying the fact.
"""

import polars as pl

from draftkit import overrides as OV


def _ov(status_col=True, statuses=("confirmed", "candidate")):
    rows = [{"sleeper_id": "1", "name": "a", "proj_pts": 100.0},
            {"sleeper_id": "2", "name": "b", "proj_pts": 200.0}]
    if status_col:
        for r, s in zip(rows, statuses):
            r["status"] = s
    return pl.DataFrame(rows)


def test_only_confirmed_rows_are_applied():
    ok, cand = OV.split(_ov())
    assert ok["sleeper_id"].to_list() == ["1"]
    assert cand["sleeper_id"].to_list() == ["2"]


def test_a_file_without_a_status_column_is_entirely_candidate():
    """An unmarked file predates the contract, so nothing in it has been
    checked under the contract. Fail closed, loudly, rather than applying
    unverified numbers because an old file happens to lack a column."""
    ok, cand = OV.split(_ov(status_col=False))
    assert ok.height == 0
    assert cand.height == 2


def test_status_matching_tolerates_case_and_whitespace():
    ok, _ = OV.split(_ov(statuses=("  CONFIRMED ", "candidate")))
    assert ok["sleeper_id"].to_list() == ["1"]


def test_an_unknown_status_is_treated_as_candidate():
    """Typos must not silently activate a row."""
    ok, cand = OV.split(_ov(statuses=("confirmd", "candidate")))
    assert ok.height == 0
    assert cand.height == 2


def test_pending_is_empty_when_there_is_no_file(tmp_path):
    assert OV.pending(tmp_path / "nope.csv") == []


def test_pending_reports_the_fact_date_not_the_edit_date(tmp_path):
    p = tmp_path / "overrides.csv"
    p.write_text("sleeper_id,name,proj_pts,status,date_checked\n"
                 "9,Player,120,candidate,2026-08-19\n", encoding="utf-8")
    got = OV.pending(p)
    assert got == [{"sleeper_id": 9, "name": "Player", "proj_pts": 120,
                    "date_checked": "2026-08-19"}]


def test_read_rejects_a_file_missing_the_required_columns(tmp_path):
    p = tmp_path / "overrides.csv"
    p.write_text("name,notes\nPlayer,hello\n", encoding="utf-8")
    assert OV.read(p) is None


def test_the_shipped_keefamania_overrides_are_all_inert():
    """The five rows that started this. They stay inert until the draft-morning
    pass re-verifies them; none may be promoted for lack of time."""
    ov = OV.read(__import__("pathlib").Path(
        "data/external/overrides.keefamania.csv"))
    assert ov is not None
    ok, cand = OV.split(ov)
    assert ok.height == 0, "no Keefamania override is verified yet"
    assert cand.height == 5
    assert set(cand["date_checked"].to_list()) == {"2026-08-19"}
