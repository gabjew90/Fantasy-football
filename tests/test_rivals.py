from draftkit.rivals import tendencies_from_picks


def _pick(user, rnd, pos):
    return {"picked_by": user, "round": rnd, "metadata": {"position": pos}}


def test_first_position_rounds():
    picks = [
        _pick("u1", 1, "RB"), _pick("u1", 2, "WR"), _pick("u1", 5, "QB"),
        _pick("u1", 9, "TE"), _pick("u1", 14, "K"), _pick("u1", 15, "DEF"),
    ]
    t = tendencies_from_picks(picks)["u1"]
    assert t["first_round"]["QB"] == 5
    assert t["first_round"]["K"] == 14


def test_bucket_shares_sum_to_one():
    picks = [_pick("u1", r, p) for r, p in
             [(1, "RB"), (2, "RB"), (3, "WR"), (4, "WR"), (5, "QB"), (6, "TE")]]
    t = tendencies_from_picks(picks)["u1"]
    for bucket in t["bucket_share"]:
        total = sum(t["bucket_share"][bucket].values())
        assert abs(total - 1.0) < 1e-9 or total == 0


def test_multiple_drafts_average_first_rounds():
    a, b = _pick("u1", 4, "QB"), _pick("u1", 8, "QB")
    t = tendencies_from_picks([a, b], drafts=[[a], [b]])["u1"]
    assert t["first_round"]["QB"] == 6


def test_dst_normalized_and_bad_rows_skipped():
    picks = [
        {"picked_by": "u1", "round": 14, "metadata": {"position": "DST"}},
        {"picked_by": None, "round": 1, "metadata": {"position": "RB"}},
        {"picked_by": "u1", "round": 0, "metadata": {"position": "WR"}},
    ]
    t = tendencies_from_picks(picks)
    assert t["u1"]["first_round"]["DEF"] == 14
    assert set(t.keys()) == {"u1"}
