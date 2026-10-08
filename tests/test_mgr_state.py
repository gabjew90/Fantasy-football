"""FAAB from transaction history and diff-based alerting.

(The delivery and trade-watch tests went with the retired cron stack,
DECISIONS #212.)
"""

from manager.faab import crosscheck, spent_from_transactions
from manager.store import Store


def _store(tmp_path):
    return Store(tmp_path / "state")


def test_faab_spent_from_transactions():
    txns = [
        [  # week 1
            {"type": "waiver", "status": "complete",
             "settings": {"waiver_bid": 40}, "adds": {"p1": 4}, "roster_ids": [4]},
            {"type": "waiver", "status": "failed",
             "settings": {"waiver_bid": 55}, "adds": {"p1": 7}, "roster_ids": [7]},
            {"type": "free_agent", "status": "complete", "adds": {"p2": 4},
             "roster_ids": [4]},
        ],
        [  # week 2
            {"type": "waiver", "status": "complete",
             "settings": {"waiver_bid": 12}, "adds": {"p3": 4}, "roster_ids": [4]},
            {"type": "waiver", "status": "complete",
             "settings": {"waiver_bid": 1}, "adds": {"p4": 9}, "roster_ids": [9]},
        ],
    ]
    spent = spent_from_transactions(txns)
    assert spent == {4: 52, 9: 1}  # failed claims and free agents cost nothing


def test_faab_crosscheck_reports_mismatch():
    rosters = [{"roster_id": 4, "settings": {"waiver_budget_used": 52}},
               {"roster_id": 9, "settings": {"waiver_budget_used": 6}}]
    notes = crosscheck({4: 52, 9: 1}, rosters)
    assert len(notes) == 1 and "roster 9" in notes[0] and "using the field" in notes[0]


def test_alert_fires_exactly_once(tmp_path):
    s = _store(tmp_path)
    assert s.first_time("inj:123:Out") is True
    assert s.first_time("inj:123:Out") is False       # same fact -> silent
    assert s.first_time("inj:123:Questionable") is True  # changed fact -> alert


def test_store_state_survives_reopen(tmp_path):
    Store(tmp_path / "state").set("k", {"a": 1})
    s2 = Store(tmp_path / "state")   # fresh instance = fresh process
    assert s2.get("k") == {"a": 1}
    assert s2.first_time("x") and not Store(tmp_path / "state").first_time("x")


def test_live_fa_replacement_levels():
    from manager.waiver_brief import fa_replacement_levels, value_over_fa
    pool = [
        {"sleeper_id": "a", "pos": "RB", "ros": 120.0},
        {"sleeper_id": "b", "pos": "RB", "ros": 60.0},
        {"sleeper_id": "c", "pos": "WR", "ros": 110.0},
        {"sleeper_id": "d", "pos": "WR", "ros": 105.0},
    ]
    lv = fa_replacement_levels(pool)
    # the leader is carried BY ID: an exact tie at the top must not let two
    # players both price themselves against second-best
    assert lv["RB"] == (120.0, 60.0, "a") and lv["WR"] == (110.0, 105.0, "c")
    # scarce RB: best RB is worth his gap to the next one (+60); deep WR: +5
    assert value_over_fa(pool[0], lv) == 60.0
    assert value_over_fa(pool[2], lv) == 5.0
    # a non-best player is measured against the best still available
    assert value_over_fa(pool[1], lv) == -60.0


def test_overreaction_damper_discriminates():
    from manager.usage import overreaction
    usage = {"spike guy": {2: {"targets": 4, "target_share": 0.12, "rec_yards": 30},
                           3: {"targets": 5, "target_share": 0.13, "rec_yards": 140}},
             "role guy": {2: {"targets": 3, "target_share": 0.10, "rec_yards": 25},
                          3: {"targets": 9, "target_share": 0.24, "rec_yards": 110}}}
    snaps = {"spike guy": {2: 0.55, 3: 0.57}, "role guy": {2: 0.40, 3: 0.78}}
    note = overreaction("Spike Guy", usage, snaps, 3)
    assert note and "flat usage" in note      # 30->140 yds on the same role
    assert overreaction("Role Guy", usage, snaps, 3) is None  # genuine role change
    assert overreaction("Spike Guy", usage, snaps, 1) is None  # needs two weeks


def test_ir_aware_stash_budget():
    from manager.waiver_brief import bench_stash_count, stash_note
    ctx = {
        "my_rid": 2, "current_starters": ["s1"],
        "my_roster": {"reserve": []},
        "reserve_allow": ("Out", "Doubtful"),
        "roster_players": {2: [
            {"sleeper_id": "s1", "name": "Starter", "pos": "RB", "weekly": 15.0},
            {"sleeper_id": "b1", "name": "Stash One", "pos": "RB", "weekly": 0.5},
            {"sleeper_id": "b2", "name": "Hurt Guy", "pos": "WR", "weekly": 0.0,
             "status": "Out"},
        ]},
    }
    # Hurt Guy counts as a bench stash now (IR empty), so bench holds 2 -> but
    # he is IR-eligible, so a new stash is OK via the IR exemption
    assert bench_stash_count(ctx) == 2
    note = stash_note(ctx, {"weekly": 0.0}, contingent=True)
    assert note and "can move to IR" in note
    # once he's ON IR: exempt from the count, and the budget is spent
    ctx["my_roster"]["reserve"] = ["b2"]
    assert bench_stash_count(ctx) == 1
    note2 = stash_note(ctx, {"weekly": 0.0}, contingent=False)
    assert note2 and "over budget" in note2
    # a claim WITH a role is never a stash question
    assert stash_note(ctx, {"weekly": 9.0}, contingent=False) is None
