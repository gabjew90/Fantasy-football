from draftkit.adpdiff import diff_snapshots


OLD = [
    {"name": "A", "pos": "RB", "adp": 10.0},
    {"name": "B", "pos": "WR", "adp": 50.0},
    {"name": "C", "pos": "WR", "adp": 100.0},
]
NEW = [
    {"name": "A", "pos": "RB", "adp": 12.0},   # +2: noise, not flagged
    {"name": "B", "pos": "WR", "adp": 30.0},   # -20: riser
    {"name": "D", "pos": "TE", "adp": 90.0},   # new entrant
]


def test_movers_threshold():
    movers = diff_snapshots(OLD, NEW, threshold=15)
    by_name = {m["name"]: m for m in movers}
    assert "A" not in by_name
    assert by_name["B"]["delta"] == -20.0
    assert by_name["B"]["kind"] == "riser"


def test_entrants_and_dropouts_flagged():
    movers = diff_snapshots(OLD, NEW, threshold=15)
    by_name = {m["name"]: m for m in movers}
    assert by_name["D"]["kind"] == "entered"
    assert by_name["C"]["kind"] == "left"


def test_sorted_by_magnitude():
    movers = diff_snapshots(OLD, NEW, threshold=15)
    deltas = [abs(m["delta"]) for m in movers if m["delta"] is not None]
    assert deltas == sorted(deltas, reverse=True)
