"""draftkit must reproduce the spreadsheet's own numbers, given league scoring.

The workbook caches Excel's computed result for every cell, so this is a diff
against ground truth rather than against anyone's reading of the formulas. It
is the check that makes "the projection is an INPUT" (DECISIONS #21) an
auditable claim instead of a hope.

It caught two real gaps:

  * the loader read the base stat line only, while the sheet averages the
    analyst panel's low, base and high (now `pts17_band`);
  * the sheet adds a per-position ROOKIE BUMP that the loader dropped, worth
    up to 65 season points and applied to 42 players.

Since DECISIONS #54 it runs over BOTH 2026 copies of the workbook: the 09-02
copy (16-game basis, four-way headline average) and the 09-04 default-settings
copy (17-game basis, three-way average, Scoring tab set to 12 teams). The
headline is REPRODUCED from the tab lines, ECR slots, RISK haircuts and the
Aggregate formulas, so a copy whose Scoring tab does not match the league
still yields the league's number; here both copies' scoring does match, which
is what makes the page an exact oracle.
"""

from __future__ import annotations

from pathlib import Path

import polars as pl
import pytest

from draftkit import external as X
from draftkit.config import Config

ROOT = Path(__file__).resolve().parents[1]
SHEETS = [ROOT / "data/external/DraftSheets_2026_Keefamania_10tm_halfPPR_1flex.xlsx",
          ROOT / "data/external/DraftSheets_2026_default_2026-09-04.xlsx",
          ROOT / "data/external/DraftSheets_2026_Keefamania_10tm_halfPPR_1flex_v2.xlsx"]
# what each copy's formulas say, asserted so a silent re-shape fails loudly
EXPECTED_SPEC = {SHEETS[0].name: (16.0, "low_avg_high_ecr"), SHEETS[1].name: (17.0, "mid_avg_ecr"),
                 SHEETS[2].name: (17.0, "mid_avg_ecr")}
# the 09-04 download's TE block: 49 of 50 rows still on the 16-game formula
# (a half-applied template edit, present in the default copy AND the user's
# league-settings copy); the loader names it and reproduces TE on 17
OFF_BASIS = {SHEETS[0].name: [], SHEETS[1].name: ["TE"], SHEETS[2].name: ["TE"]}

# the sheet's own AVG cell per tab (1-based column): the base line scored with
# the Scoring tab, plus the tab's rookie bump
AVG_COL = {"QB": 16, "RB": 14, "WR": 14, "TE": 10}

pytestmark = pytest.mark.skipif(not all(s.exists() for s in SHEETS), reason="draft sheets not present")


class _PassThrough:
    """Every name resolves to itself, so the diff covers the whole sheet and
    not only the players Sleeper happens to know."""

    def match(self, name, pos, team):
        return f"{pos}:{name}"


def _scoring():
    cfg = Config.load(league="keefamania")
    return cfg.get("scoring") or (cfg.get("expected") or {}).get("scoring") or {}


@pytest.fixture(scope="module", params=SHEETS, ids=lambda p: p.name)
def sheet(request):
    return request.param


@pytest.fixture(scope="module")
def loaded(sheet):
    frame, unmatched = X.from_sheet(sheet, _scoring(), _PassThrough(), as_of="test")
    return frame, unmatched, _scoring()


@pytest.fixture(scope="module")
def cached(sheet):
    import openpyxl
    wb = openpyxl.load_workbook(sheet, data_only=True)
    out = {}
    for pos, col in AVG_COL.items():
        for r in list(wb[pos].iter_rows(values_only=True))[1:]:
            n = r[0]
            if not (isinstance(n, str) and n.replace("\xa0", "").replace("Â", "").strip()):
                continue
            v = r[col - 1] if len(r) >= col else None
            if isinstance(v, (int, float)):
                out[f"{pos}:{n.strip()}"] = float(v)
    return out


def test_every_projection_matches_the_spreadsheets_own_value(loaded, cached):
    """The tab line. A mismatch means draftkit and the spreadsheet disagree
    about what the same stat line is worth in this league."""
    frame, _unmatched, _ = loaded
    mine = {r["sleeper_id"]: r["pts17"] for r in frame.iter_rows(named=True)}
    compared, bad = 0, []
    for key, theirs in cached.items():
        if key not in mine:
            continue
        compared += 1
        if abs(mine[key] - theirs) >= 0.01:
            bad.append((abs(mine[key] - theirs), key, mine[key], theirs))
    assert compared >= 480, f"only {compared} players compared; the tabs moved"
    bad.sort(reverse=True)
    assert not bad, (
        f"{len(bad)} of {compared} disagree with the spreadsheet. Worst:\n"
        + "\n".join(f"  {k}: draftkit {a:.2f} vs sheet {b:.2f}" for _d, k, a, b in bad[:10]))


def test_the_league_scoring_matches_the_sheets_own_inputs(sheet):
    """Both 2026 copies were exported with the league's scoring, which is
    what lets the page serve as an exact oracle below. sheet_scoring() is the
    loader's own reading of the Scoring tab; the terms the sheet can score
    and draftkit cannot must all be zero, or parity is accidental."""
    import openpyxl
    scoring = _scoring()
    wb = openpyxl.load_workbook(sheet, data_only=True)
    theirs = X.sheet_scoring(wb)
    for k in ("pass_yd", "rush_yd", "rec_yd", "pass_td", "rush_td", "rec_td", "pass_int", "fum_lost", "rec"):
        assert theirs[k] == pytest.approx(scoring[k]), k
    assert not [k for k in theirs if k.startswith("rec_") and k not in ("rec_yd", "rec_td")], "per-position PPR"
    ws = wb["Scoring"]
    sheet_in = {}
    for r in ws.iter_rows(min_row=1, max_row=26, values_only=True):
        if isinstance(r[0], str) and isinstance(r[1], (int, float)):
            sheet_in[r[0].strip()] = float(r[1])
    for k in ("PassCMP", "PassINCMP", "SACKS", "RushATT", "Pass1D", "Rush1D", "Rec1D"):
        assert sheet_in[k] == 0.0, (
            f"the sheet scores {k} at {sheet_in[k]} and draftkit's stat line does "
            "not carry it; parity above is accidental until it does")


def test_the_workbooks_settings_do_not_enter_the_headline(sheet):
    """The 09-04 copy's Scoring tab says 12 teams; Keefamania is 10. Team
    count, roster and auction cells move VBD and PS on the page and nothing
    else, so the reproduction must not read them. The loader reports the
    scoring diff (none here) and the workbook's own as-of instead."""
    rep = {}
    X.from_sheet(sheet, _scoring(), _PassThrough(), as_of="fallback", line="headline", report=rep)
    assert rep["sheet_scoring_diffs"] == {}
    assert rep["sheet_as_of"] in ("2026-09-02", "2026-09-04"), rep["sheet_as_of"]
    games, form = EXPECTED_SPEC[sheet.name]
    assert rep["headline_spec"]["games"] == games and rep["headline_spec"]["avg_form"] == form
    assert rep["headline_spec"]["rank_window"] == {"QB": 50, "RB": 100, "WR": 100, "TE": 50}
    assert rep["headline_spec"]["off_basis_positions"] == OFF_BASIS[sheet.name]


def test_the_rookie_bump_is_applied_and_is_large(sheet, loaded, cached):
    """Not applying it under-projects rookies by up to 65 points against the
    sheet. This asserts the size so a silent regression to 'no bump' fails
    loudly rather than shifting the deep board by tens of points."""
    import openpyxl
    wb_v = openpyxl.load_workbook(sheet, data_only=True)
    wb_f = openpyxl.load_workbook(sheet, data_only=False)
    total, n = 0.0, 0
    for pos in ("RB", "WR"):
        col = X.sheet_bump_column(wb_f[pos])
        assert col is not None, f"{pos}: the bump column moved"
        for r in list(wb_v[pos].iter_rows(values_only=True))[1:]:
            nm = r[0]
            if not (isinstance(nm, str) and nm.replace("\xa0", "").replace("Â", "").strip()):
                continue
            b = r[col] if len(r) > col else None
            if isinstance(b, (int, float)) and b > 0:
                total += float(b)
                n += 1
    assert n >= 40, f"only {n} bumped players found; the sheet's rookie set changed"
    assert total / n > 30.0, "the mean bump collapsed; check the coefficients"


def test_qb_and_te_have_no_bump_column(sheet):
    """The bump is RB and WR only. Finding one at QB or TE would mean the
    formula-shape locator is matching something else."""
    import openpyxl
    wb_f = openpyxl.load_workbook(sheet, data_only=False)
    for pos in ("QB", "TE"):
        assert X.sheet_bump_column(wb_f[pos]) is None


def test_the_band_is_carried_and_zero_means_the_panel_agreed(loaded):
    """Deep players get high and low rows that just repeat the base line, so a
    band of exactly zero is the sheet saying "no spread published for him",
    not a missing column. Both read as no evidence downstream."""
    frame, _u, _s = loaded
    rows = list(frame.iter_rows(named=True))
    banded = [r for r in rows if r["pts17_band"] is not None]
    assert len(banded) == len(rows), "the high/low rows stopped being attached"
    assert all(r["pts17_band"] >= 0 for r in banded)
    spread = [r for r in banded if r["pts17_band"] > 0]
    assert len(spread) >= 300, (
        f"only {len(spread)} players carry a real spread; the panel's high/low "
        "rows are probably no longer being read")


def test_nothing_is_dropped_when_every_name_resolves(loaded):
    _f, unmatched, _s = loaded
    assert unmatched == []


def test_the_headline_line_reproduces_the_draftsheet_page(sheet, cached):
    """sheet_line: headline. proj_pts must be the number the sheet's reader
    sees: DraftSheet PTS, rebuilt from the workbook's inputs (DECISIONS #54),
    and carried on the workbook's own games basis with no further scaling."""
    import openpyxl
    rep = {}
    frame, _ = X.from_sheet(sheet, _scoring(), _PassThrough(), as_of="test", line="headline", report=rep)
    page = X.parse_draftsheet(list(openpyxl.load_workbook(sheet, data_only=True)["DraftSheet"].iter_rows(values_only=True)))
    assert len(page) >= 200
    hl = frame.filter(pl.col("source") == "fantasypros_sheet_headline")
    assert hl.height == frame.height, "every tab row is on the headline source"
    on_page = [r for r in hl.iter_rows(named=True) if r["name"].strip() in page]
    assert len(on_page) >= 180, f"only {len(on_page)} tab players found on the DraftSheet"
    # a block the workbook itself left on another basis is reproduced on the
    # majority basis, so its page numbers are the stale ones, not ours
    off = set(OFF_BASIS[sheet.name])
    on_basis = [r for r in on_page if r["pos"] not in off]
    # the rest are estimated at the position's median ratio: exactly the tab
    # players the DraftSheet does not list (no ECR slot at the tab position,
    # or one beyond the ranked block), and on the production board that is
    # a handful of deep players, never a drafted name
    est = hl.filter(~pl.col("name").str.strip_chars().is_in(list(page)))
    assert est["pts17"].null_count() == 0
    gaps = sorted(((abs(r["pts17"] - page[r["name"].strip()]), r["name"], r["pts17"], page[r["name"].strip()])
                   for r in on_basis), reverse=True)
    # exact to the cent for every player the page puts at 20 points or more.
    # In the deep tail (Ty Simpson QB40, Justin Fields) one VLOOKUP miss
    # inside the workbook's own block shifts a k-th-largest by a few tenths;
    # those rows are 10-15 point players nobody drafts
    drafted = [g for g in gaps if g[3] >= 20.0]
    assert drafted and drafted[0][0] < 0.01, f"worst among page >= 20: {drafted[:6]}"
    assert gaps[0][0] < 0.5, f"worst overall {gaps[:6]}"
    assert rep["headline_parity"]["compared"] == len(on_basis) and rep["headline_parity"]["over_0_05"] <= 2
    assert rep["headline_parity"]["skipped_positions"] == sorted(off)
    if off:
        # and the skipped block IS the stale one: its page numbers sit on the
        # old basis, ours on the workbook majority, by the ratio of the two
        games, _ = EXPECTED_SPEC[sheet.name]
        te = [(r["pts17"], page[r["name"].strip()]) for r in on_page if r["pos"] in off and page[r["name"].strip()] > 100]
        stale = [t / m for m, t in te if 0.85 < t / m < 0.96]
        assert te and len(stale) >= 0.8 * len(te), te[:5]     # all but the one row already on 17 (TE1)
    # the basis: the page number is `games` less a haircut, never rescaled
    games, _form = EXPECTED_SPEC[sheet.name]
    assert set(hl["pts_basis"].to_list()) == {games}
    scaled = frame.with_columns(X.source_basis_expr().alias("b"))
    assert set(scaled["b"].to_list()) == {games}


def test_the_league_settings_copy_and_the_default_copy_give_one_board():
    """The user's ask (2026-09-05): the loader applies the league's rules to
    whatever copy it is handed. The default download (Scoring tab at 12
    teams) and the same download with Keefamania's settings entered must
    yield the same headline for every player, to the cent."""
    a, _ = X.from_sheet(SHEETS[1], _scoring(), _PassThrough(), as_of="x", line="headline")
    b, _ = X.from_sheet(SHEETS[2], _scoring(), _PassThrough(), as_of="x", line="headline")
    ma = {r["sleeper_id"]: r for r in a.iter_rows(named=True)}
    mb = {r["sleeper_id"]: r for r in b.iter_rows(named=True)}
    assert set(ma) == set(mb) and len(ma) >= 480
    for k in ma:
        for col in ("pts17", "pts17_band", "pts17_line_lo", "pts17_line_hi", "pts_basis"):
            va, vb = ma[k][col], mb[k][col]
            assert (va is None and vb is None) or abs(va - vb) < 1e-9, (k, col, va, vb)
