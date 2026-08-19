from draftkit import snake


def test_pick_to_round_slot_first_round():
    assert snake.pick_to_round_slot(1, 12) == (1, 1)
    assert snake.pick_to_round_slot(12, 12) == (1, 12)


def test_pick_to_round_slot_snakes_back():
    assert snake.pick_to_round_slot(13, 12) == (2, 12)
    assert snake.pick_to_round_slot(24, 12) == (2, 1)
    assert snake.pick_to_round_slot(25, 12) == (3, 1)


def test_slot_pick_numbers_slot6():
    picks = snake.slot_pick_numbers(6, 12, 15)
    assert picks[:4] == [6, 19, 30, 43]
    assert len(picks) == 15
    # turn picks: gap alternates 13/11 for slot 6
    assert picks[1] - picks[0] == 13
    assert picks[2] - picks[1] == 11


def test_next_pick_for_slot():
    assert snake.next_pick_for_slot(1, 6, 12, 15) == 6
    assert snake.next_pick_for_slot(6, 6, 12, 15) == 6  # on the clock
    assert snake.next_pick_for_slot(7, 6, 12, 15) == 19
    # slot 6's last pick is 14*12+6 = 174 (round 15 is odd); past that -> None
    assert snake.next_pick_for_slot(174, 6, 12, 15) == 174
    assert snake.next_pick_for_slot(175, 6, 12, 15) is None


def test_slots_picking_between():
    # pick 7 -> my next at 19: slots 7..12 then 12..8 descending? snake round 2
    between = snake.slots_picking_between(7, 19, 12)
    assert between == [7, 8, 9, 10, 11, 12, 12, 11, 10, 9, 8, 7]


def test_starter_needs_flex_overflow():
    slots = {"QB": 1, "RB": 2, "WR": 2, "TE": 1, "FLEX": 2, "K": 1, "DEF": 1, "BN": 5}
    needs = snake.starter_needs(["RB", "RB", "RB", "WR"], slots)
    assert needs["RB"] == 0
    assert needs["FLEX"] == 1  # third RB ate one flex spot
    assert needs["WR"] == 1
    assert snake.needs_position(needs, "RB")  # still flex-eligible
    assert snake.needs_position(needs, "QB")


def test_starter_needs_bench_overflow():
    slots = {"QB": 1, "RB": 1, "WR": 1, "TE": 1, "FLEX": 1, "K": 1, "DEF": 1, "BN": 5}
    needs = snake.starter_needs(["RB", "RB", "RB", "QB", "QB"], slots)
    assert needs["RB"] == 0
    assert needs["FLEX"] == 0
    assert needs["QB"] == 0  # second QB goes to bench, need stays filled
    assert not snake.needs_position(needs, "RB")
