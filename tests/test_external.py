"""Projections as an input (DECISIONS 2026-09-02 #21).

Two sources into one schema, first source wins per player, one games
scaling at the end, and the one tail rule: non-starters project zero.
"""

from __future__ import annotations

import json

import polars as pl
import pytest

from draftkit import external as X

HALF = {"rec": 0.5, "pass_yd": 0.04, "pass_td": 4.0, "pass_int": -1.0,
        "rush_yd": 0.1, "rec_yd": 0.1, "rush_td": 6.0, "rec_td": 6.0, "fum_lost": -2.0}


class FakeIndex:
    def __init__(self, table):
        self.table = table

    def match(self, name, pos, team):
        return self.table.get((name, pos))


def test_sheet_tab_parses_consensus_rows_and_skips_expert_extremes():
    rows = [
        ("Player", "Team", "ATT", "YDS", "TDS", "REC", "YDS", "TDS", "FL", "FPTS"),
        ("\xa0", None, None, None, None, None, None, None, None, None),
        ("Jahmyr Gibbs", "DET", 275.2, 1383.7, 13.8, 71.3, 581.1, 4.1, 1.1, 337.4),
        (None, "high", 283.5, 1422, 15, 74, 625, 5, 1, 367.1),
        (None, "low", 260, 1300, 12, 65, 520, 3, 2, 300.0),
        ("Bijan Robinson", "ATL", 300, 1400, 12, 60, 500, 3, 1, 320.0),
    ]
    out = X.parse_sheet_tab(rows, "RB")
    assert [p["name"] for p in out] == ["Jahmyr Gibbs", "Bijan Robinson"]
    assert out[0]["line"]["rec_yd"] == 581.1 and out[0]["line"]["fum_lost"] == 1.1


def test_from_sheet_scores_in_league_settings_and_reports_unmatched(tmp_path):
    import openpyxl
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    for pos, hdr in (("QB", ["Player", "Team"] + ["x"] * 9), ("RB", ["Player", "Team"] + ["x"] * 7),
                     ("WR", ["Player", "Team"] + ["x"] * 7), ("TE", ["Player", "Team"] + ["x"] * 4)):
        ws = wb.create_sheet(pos)
        ws.append(hdr)
    wb["RB"].append(["Jahmyr Gibbs", "DET", 275.2, 1383.7, 13.8, 71.3, 581.1, 4.1, 1.1])
    wb["RB"].append([None, "high", 283.5, 1422, 15, 74, 625, 5, 1])
    wb["RB"].append(["Nobody Here", "FA", 10, 50, 0, 0, 0, 0, 0])
    p = tmp_path / "sheet.xlsx"
    wb.save(p)
    df, unmatched = X.from_sheet(p, HALF, FakeIndex({("Jahmyr Gibbs", "RB"): "4866"}), as_of="2026-09-01")
    assert unmatched == ["Nobody Here (RB)"]
    r = df.row(0, named=True)
    assert r["sleeper_id"] == "4866" and r["source"] == "fantasypros_sheet" and r["as_of"] == "2026-09-01"
    assert abs(r["pts17"] - 337.33) < 0.05        # the sheet's own half-PPR FPTS for that line
    assert json.loads(r["line"])["rush_yd"] == 1383.7


def test_from_sleeper_uses_the_common_schema_and_skips_placeholders(tmp_path):
    rows = [{"player_id": "4984", "team": "BUF", "updated_at": 1788249037361,
             "player": {"position": "QB", "first_name": "Josh", "last_name": "Allen"},
             "stats": {"gp": 18.0, "pass_yd": 3650.0, "pass_td": 28.0, "adp_half_ppr": 20.7}},
            {"player_id": "9", "team": None, "player": {"position": "QB"}, "stats": {"gp": 18.0, "adp_half_ppr": 600.0}}]

    def getter(url):
        return rows if url.endswith("=QB") else []

    df = X.from_sleeper(2026, HALF, tmp_path, getter=getter, ttl=3600)
    assert df.height == 1
    r = df.row(0, named=True)
    assert r["name"] == "Josh Allen" and r["source"] == "sleeper_rotowire" and r["as_of"] == "2026-09-01"
    assert abs(r["pts17"] - (3650 * 0.04 + 28 * 4)) < 1e-9
    assert "gp" not in json.loads(r["line"]) and "adp_half_ppr" not in json.loads(r["line"])


def _two_frames():
    a = pl.DataFrame({"sleeper_id": ["1", "2"], "name": ["A", "B"], "pos": ["RB", "RB"], "team": ["X", "X"],
                      "pts17": [200.0, 150.0], "source": ["sheet", "sheet"], "as_of": ["d", "d"],
                      "line": [json.dumps({"rush_yd": 1000.0, "rec": 50.0}), json.dumps({"rush_yd": 900.0})]},
                     schema=X.SCHEMA)
    b = pl.DataFrame({"sleeper_id": ["2", "3"], "name": ["B", "C"], "pos": ["RB", "RB"], "team": [None, "Y"],
                      "pts17": [999.0, 100.0], "source": ["sleeper", "sleeper"], "as_of": ["e", "e"],
                      "line": [json.dumps({"rush_yd": 700.0}), json.dumps({"rush_yd": 500.0})]},
                     schema=X.SCHEMA)
    return a, b


def test_combine_first_mode_is_unchanged_and_reports_one_source():
    a, b = _two_frames()
    out = X.combine([a, b])
    got = {r["sleeper_id"]: r for r in out.iter_rows(named=True)}
    assert got["2"]["pts17"] == 150.0 and got["2"]["source"] == "sheet"
    assert got["3"]["source"] == "sleeper" and out.height == 3
    assert all(r["n_sources"] == 1 and r["pts17_sd"] == 0.0 and r["pts17_hi"] == r["pts17"] for r in got.values())
    assert X.combine([X.empty(), b]).height == 2
    assert list(out.columns) == list(X.SCHEMA_COMBINED)


def test_combine_mean_averages_per_stat_with_equal_weight_and_reports_dispersion():
    """Plan A1: player 2 has rush_yd 900 in one source and 700 in the other;
    the mean LINE is 800 yards, scored once. A stat only one source carries
    counts as 0 for the other."""
    a, b = _two_frames()
    out = X.combine([a, b], mode="mean", scoring=HALF)
    got = {r["sleeper_id"]: r for r in out.iter_rows(named=True)}
    two = got["2"]
    assert json.loads(two["line"]) == {"rush_yd": 800.0}
    assert abs(two["pts17"] - X.score_projection({"rush_yd": 800.0}, HALF)) < 1e-9
    s1, s2 = X.score_projection({"rush_yd": 900.0}, HALF), X.score_projection({"rush_yd": 700.0}, HALF)
    assert abs(two["pts17"] - (s1 + s2) / 2) < 1e-9                      # linear scoring: mean of scores
    assert abs(two["pts17_sd"] - abs(s1 - s2) / 2) < 1e-9
    assert two["pts17_hi"] == max(s1, s2) and two["pts17_lo"] == min(s1, s2) and two["n_sources"] == 2
    assert two["source"] == "mean(sheet,sleeper)" and two["as_of"] == "e" and two["team"] == "X"
    one = got["1"]
    assert one["n_sources"] == 1 and one["pts17_sd"] == 0.0
    assert json.loads(one["line"]) == {"rush_yd": 1000.0, "rec": 50.0}
    rev = {r["sleeper_id"]: r["pts17"] for r in X.combine([b, a], mode="mean", scoring=HALF).iter_rows(named=True)}
    assert all(abs(rev[k] - got[k]["pts17"]) < 1e-9 for k in got)       # order-free
    c = pl.DataFrame({"sleeper_id": ["9"], "name": ["Z"], "pos": ["WR"], "team": ["Q"], "pts17": [0.0],
                      "source": ["espn"], "as_of": ["f"], "line": [json.dumps({"rec": 40.0, "rec_yd": 400.0})]},
                     schema=X.SCHEMA)
    d = pl.DataFrame({"sleeper_id": ["9"], "name": ["Z"], "pos": ["WR"], "team": ["Q"], "pts17": [0.0],
                      "source": ["sleeper"], "as_of": ["f"], "line": [json.dumps({"rec_yd": 600.0})]},
                     schema=X.SCHEMA)
    z = X.combine([c, d], mode="mean", scoring=HALF).row(0, named=True)
    assert json.loads(z["line"]) == {"rec": 20.0, "rec_yd": 500.0}     # a stat one source lacks counts as 0


def test_non_starters_go_to_zero_only_when_depth_chart_and_market_agree():
    teams = 10
    df = pl.DataFrame({
        "sleeper_id": ["qb1", "qb2", "glitch", "nomkt", "wr_deep", "rb3", "hback"],
        "name": ["Starter", "Backup", "Glitch", "NoMarket", "DeepWR", "RB3", "HBack"],
        "pos": ["QB", "QB", "QB", "QB", "WR", "RB", "TE"],
        "team": ["A", "A", "B", "C", "D", "E", "F"],
        "ecr": [3.0, 40.0, 5.0, None, 90.0, None, None],   # rb3: depth 3 and unranked
        "adp": [None, None, None, None, None, None, None],
        "proj_pts": [300.0, 200.0, 280.0, 190.0, 120.0, 90.0, 60.0],
    }, schema_overrides={"adp": pl.Float64, "ecr": pl.Float64})
    filler = pl.DataFrame({"sleeper_id": [f"f{i}" for i in range(12)], "name": [f"F{i}" for i in range(12)],
                           "pos": ["QB"] * 12, "team": ["Z"] * 12, "ecr": [10.0 + i for i in range(12)],
                           "adp": [None] * 12, "proj_pts": [250.0] * 12}, schema_overrides={"adp": pl.Float64})
    df = pl.concat([df, filler], how="diagonal_relaxed")
    depth = pl.DataFrame({"sleeper_id": ["qb1", "qb2", "glitch", "nomkt", "wr_deep", "rb3", "hback"],
                          "depth_order": [1, 2, 2, 2, 9, 3, 6],
                          "depth_pos": ["QB", "QB", "QB", "QB", "RWR", "RB", "RB"]})
    out = X.zero_non_starters(df, depth, teams)
    g = {r["sleeper_id"]: r for r in out.iter_rows(named=True)}
    assert g["qb1"]["proj_pts"] == 300.0 and g["qb1"]["non_starter"] is False
    assert g["qb2"]["proj_pts"] == 0.0 and g["qb2"]["contingent_of"] == "Starter"
    assert g["glitch"]["proj_pts"] == 280.0, "market ranks him QB3: one source is not enough"
    assert g["nomkt"]["proj_pts"] == 0.0, "no ECR/ADP at all is the market's strongest 'backup'"
    assert g["wr_deep"]["proj_pts"] == 120.0, "WR chart is per slot; never zeroed on it"
    assert g["rb3"]["proj_pts"] == 0.0 and g["rb3"]["contingent_of"] is None, "no order-1 RB known on team E"
    assert g["hback"]["proj_pts"] == 60.0, "a TE filed under the RB chart is left alone"
    assert "_mkt_rank" not in out.columns


def _headline_workbook(tmp_path, games: int, three_way: bool):
    """A two-back workbook with the tabs the headline is built from. Gibbs is
    RB1 with a low/high pair; Bijan is on the tab but NOT in the ECR list, so
    he is off the page and estimated. The Aggregate tab carries only the
    FORMULA STRINGS the loader reads (games basis, average form, rank
    window); values are not needed because the loader recomputes them."""
    import openpyxl
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    for pos, hdr in (("QB", ["Player", "Team"] + ["x"] * 9), ("RB", ["Player", "Team"] + ["x"] * 7),
                     ("WR", ["Player", "Team"] + ["x"] * 7), ("TE", ["Player", "Team"] + ["x"] * 4)):
        wb.create_sheet(pos).append(hdr)
    wb["RB"].append(["Jahmyr Gibbs", "DET", 275.2, 1383.7, 13.8, 71.3, 581.1, 4.1, 1.1])
    wb["RB"].append([None, "high", 283.5, 1422, 15, 74, 625, 5, 1])
    wb["RB"].append([None, "low", 263, 1353, 12, 67.9, 546.4, 3.4, 1.3])
    wb["RB"].append(["Bijan Robinson", "ATL", 285.8, 1391.1, 8.8, 76.9, 705.6, 3.5, 1.8])
    ecr = wb.create_sheet("ECR")
    ecr.append(["RK", "TIERS", "PLAYER NAME", "TEAM", "POS"])
    ecr.append([1, 1, "Jahmyr Gibbs", "DET", "RB1"])
    risk = wb.create_sheet("RISK")
    risk.append(["Position", "Projected Games Adjustment"])
    risk.append(["RB1", 2.5514])
    ag = wb.create_sheet("Aggregate")
    hdr = [None] * 100
    for off in (0, 14, 28, 42):
        hdr[off + 5], hdr[off + 6], hdr[off + 7], hdr[off + 8] = "LOW", "AVG", "HIGH", "Zscore Projection"
    hdr[59 - 1], hdr[64 - 1], hdr[69 - 1], hdr[74 - 1] = "QBPts", "RBPts", "WRPts", "TEPts"
    ag.append([None] * 100)
    ag.append(hdr)
    row = [None] * 100
    for pos, off in (("QB", 0), ("RB", 14), ("WR", 28), ("TE", 42)):
        row[off] = f"{pos}1"
        row[off + 5] = f"=IFERROR(VLOOKUP(X,{pos}!A:Q,15,FALSE())/17*({games}-Y),0)"
        row[off + 8] = ("=AVERAGE(AVERAGE(L,H),A,VLOOKUP(X,ECR!L:N,3,FALSE))" if three_way
                        else "=AVERAGE(L,A,H,VLOOKUP(X,ECR!L:N,3,FALSE()))")
    row[59 - 1] = "=IFERROR(LARGE($G$3:$G$52,BF3),\"\")"
    row[64 - 1] = "=IFERROR(LARGE($U$3:$U$102,BK3),\"\")"
    row[69 - 1] = "=IFERROR(LARGE($AI$3:$AI$102,BP3),\"\")"
    row[74 - 1] = "=IFERROR(LARGE($AW$3:$AW$52,BU3),\"\")"
    ag.append(row)
    sc = wb.create_sheet("Scoring")
    sc.append(["Updated:", "2026-09-04"])
    p = tmp_path / f"sheet_{games}_{int(three_way)}.xlsx"
    wb.save(p)
    return p


@pytest.mark.parametrize("games,three_way", [(16, False), (17, True)])
def test_from_sheet_headline_is_reproduced_from_the_workbooks_inputs(tmp_path, games, three_way):
    """line="headline" (DECISIONS #54): the DraftSheet PTS rebuilt from the
    tab lines, the ECR slot, the RISK haircut and the workbook's own
    formulas, in LEAGUE scoring; the row carries the workbook's games basis;
    a tab player off the page is estimated at the position's median ratio."""
    from draftkit.seasondata import score_projection
    p = _headline_workbook(tmp_path, games, three_way)
    idx = FakeIndex({("Jahmyr Gibbs", "RB"): "4866", ("Bijan Robinson", "RB"): "9509"})
    rep = {}
    df, unmatched = X.from_sheet(p, HALF, idx, as_of="cfg", line="headline", report=rep)
    assert unmatched == []
    assert rep["sheet_as_of"] == "2026-09-04" and rep["headline_spec"]["games"] == games
    assert rep["headline_spec"]["avg_form"] == ("mid_avg_ecr" if three_way else "low_avg_high_ecr")
    assert rep["headline_spec"]["off_basis_positions"] == []
    rows = {r["name"]: r for r in df.iter_rows(named=True)}
    g = rows["Jahmyr Gibbs"]
    # by hand, the way the workbook does it (no bump column in this fixture)
    base = score_projection({"rush_att": 275.2, "rush_yd": 1383.7, "rush_td": 13.8, "rec": 71.3, "rec_yd": 581.1, "rec_td": 4.1, "fum_lost": 1.1}, HALF)
    hi = score_projection({"rush_att": 283.5, "rush_yd": 1422, "rush_td": 15, "rec": 74, "rec_yd": 625, "rec_td": 5, "fum_lost": 1}, HALF)
    lo = score_projection({"rush_att": 263, "rush_yd": 1353, "rush_td": 12, "rec": 67.9, "rec_yd": 546.4, "rec_td": 3.4, "fum_lost": 1.3}, HALF)
    f = (games - 2.5514) / 17.0
    ecr_pts = base * f                      # RB1 is the largest AVG in a one-man block
    want = (((lo + hi) / 2 * f + base * f + ecr_pts) / 3) if three_way else ((lo * f + base * f + hi * f + ecr_pts) / 4)
    assert g["source"] == "fantasypros_sheet_headline" and abs(g["pts17"] - want) < 1e-6
    assert g["pts_basis"] == float(games)
    # the band rides along in the headline's units: same relative spread
    tab = X.from_sheet(p, HALF, idx, as_of="x", line="tab")[0].filter(pl.col("name") == "Jahmyr Gibbs").row(0, named=True)
    assert abs(g["pts17_band"] / g["pts17"] - tab["pts17_band"] / tab["pts17"]) < 1e-9
    assert tab["pts_basis"] is None
    # the panel's own high and low lines ride to the board as the ceiling and
    # the floor (DECISIONS #55): combine() folds them into pts17_hi / pts17_lo
    one = X.combine([df]).filter(pl.col("name") == "Jahmyr Gibbs").row(0, named=True)
    assert abs(one["pts17_hi"] - hi * want / base) < 1e-6 and abs(one["pts17_lo"] - lo * want / base) < 1e-6
    # not on the page (no ECR slot): the tab line brought onto the headline
    # basis by the position's median headline/tab ratio (Gibbs alone sets it)
    b = rows["Bijan Robinson"]
    assert b["source"] == "fantasypros_sheet_headline" and b["pts_basis"] == float(games)
    assert abs(b["pts17"] - 318.32 * want / base) < 0.1


def test_the_workbooks_own_scoring_is_reported_not_used(tmp_path):
    """A default-settings copy scored at full PPR: the lines are still scored
    with the LEAGUE settings and the difference is reported, never applied."""
    import openpyxl
    p = _headline_workbook(tmp_path, 17, True)
    wb = openpyxl.load_workbook(p)
    sc = wb["Scoring"]
    for label, v in (("PassYDS", 25), ("PassTDs", 4), ("INTS", -1), ("RushYDS", 10), ("RushTDS", 6),
                     ("RB PPR", 1.0), ("WR PPR", 1.0), ("TE PPR", 1.0), ("RecYDS", 10), ("RecTDS", 6), ("FL", -2)):
        sc.append([label, v])
    wb.save(p)
    idx = FakeIndex({("Jahmyr Gibbs", "RB"): "4866", ("Bijan Robinson", "RB"): "9509"})
    rep = {}
    df, _ = X.from_sheet(p, HALF, idx, as_of="cfg", line="tab", report=rep)
    assert rep["sheet_scoring_diffs"] == {"rec": (1.0, HALF["rec"])}
    g = df.filter(pl.col("name") == "Jahmyr Gibbs").row(0, named=True)
    from draftkit.seasondata import score_projection
    assert abs(g["pts17"] - score_projection({"rush_att": 275.2, "rush_yd": 1383.7, "rush_td": 13.8, "rec": 71.3, "rec_yd": 581.1, "rec_td": 4.1, "fum_lost": 1.1}, HALF)) < 1e-9


def test_a_block_left_on_the_old_basis_is_named_and_not_followed(tmp_path):
    """The 09-04 copy: TE rows 4-52 still say 16 while everything else says
    17. The loader takes the majority for every position and names the block."""
    import openpyxl
    p = _headline_workbook(tmp_path, 17, True)
    wb = openpyxl.load_workbook(p)
    ag = wb["Aggregate"]
    for r in range(4, 54):
        ag.cell(row=r, column=42 + 6, value="=IFERROR(VLOOKUP(X,TE!A:K,9,FALSE())/17*(16-Y),0)")
    wb.save(p)
    import openpyxl as _o
    spec = X.sheet_headline_spec(_o.load_workbook(p, read_only=True, data_only=False))
    assert spec["games"] == 17.0 and spec["games_by_pos"]["TE"] == 16.0 and spec["off_basis_positions"] == ["TE"]


def test_source_basis_expr_takes_the_rows_own_basis_and_falls_back_to_17():
    df = pl.DataFrame({"source": ["fantasypros_sheet", "fantasypros_sheet_headline", "fantasypros_sheet_headline", "sleeper_rotowire", None],
                       "pts_basis": [None, 16.0, 17.0, None, None]})
    assert df.select(X.source_basis_expr().alias("b"))["b"].to_list() == [17.0, 16.0, 17.0, 17.0, 17.0]
    assert "fantasypros_sheet_headline" in X.DISCOUNTED_SOURCES


def test_the_headline_block_holds_tab_players_the_index_cannot_match(tmp_path):
    """Review 2026-09-05: the workbook's LARGE() block ranks every tab player
    at the position; a name Sleeper cannot resolve must still occupy his slot
    or everyone ranked below him shifts. Bijan is RB1 in ECR but unknown to
    the index; Gibbs at RB2 must see Bijan's AVG as the largest in the block."""
    import openpyxl
    from draftkit.seasondata import score_projection
    p = _headline_workbook(tmp_path, 17, True)
    wb = openpyxl.load_workbook(p)
    ecr = wb["ECR"]
    ecr.delete_rows(2)
    ecr.append([1, 1, "Bijan Robinson", "ATL", "RB1"])
    ecr.append([2, 1, "Jahmyr Gibbs", "DET", "RB2"])
    wb["RISK"].append(["RB2", 2.5514])
    wb.save(p)
    idx = FakeIndex({("Jahmyr Gibbs", "RB"): "4866"})          # Bijan unmatched
    df, unmatched = X.from_sheet(p, HALF, idx, as_of="cfg", line="headline")
    assert unmatched == ["Bijan Robinson (RB)"]
    g = df.filter(pl.col("name") == "Jahmyr Gibbs").row(0, named=True)
    f = (17 - 2.5514) / 17.0
    base_g = score_projection({"rush_att": 275.2, "rush_yd": 1383.7, "rush_td": 13.8, "rec": 71.3, "rec_yd": 581.1, "rec_td": 4.1, "fum_lost": 1.1}, HALF)
    base_b = score_projection({"rush_att": 285.8, "rush_yd": 1391.1, "rush_td": 8.8, "rec": 76.9, "rec_yd": 705.6, "rec_td": 3.5, "fum_lost": 1.8}, HALF)
    hi = score_projection({"rush_att": 283.5, "rush_yd": 1422, "rush_td": 15, "rec": 74, "rec_yd": 625, "rec_td": 5, "fum_lost": 1}, HALF)
    lo = score_projection({"rush_att": 263, "rush_yd": 1353, "rush_td": 12, "rec": 67.9, "rec_yd": 546.4, "rec_td": 3.4, "fum_lost": 1.3}, HALF)
    ecr_pts_rb2 = sorted([base_g * f, base_b * f], reverse=True)[1]     # the 2nd largest, Bijan counted
    want = ((lo + hi) / 2 * f + base_g * f + ecr_pts_rb2) / 3
    assert abs(g["pts17"] - want) < 1e-6


def test_an_unrecognised_rank_window_raises(tmp_path):
    import openpyxl
    import pytest
    p = _headline_workbook(tmp_path, 17, True)
    wb = openpyxl.load_workbook(p)
    wb["Aggregate"].cell(row=3, column=64, value="=IFERROR(LARGE(RBAVG,BK3),\"\")")   # a named range the reader does not know
    wb.save(p)
    with pytest.raises(ValueError, match="RB"):
        X.sheet_headline_spec(openpyxl.load_workbook(p, read_only=True, data_only=False))


def test_slot_parsing_tolerates_stray_spaces():
    assert X._split_slot(" WR 14 ") == ("WR", 14) and X._slot_key("rb1") == "RB1"
    assert X._split_slot("FLEX") is None and X._slot_number("WR14", "RB") is None
