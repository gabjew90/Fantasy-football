"""Local pick source (Yahoo draft-day rig): resolution, snake mapping, dedupe."""

from draftkit.picksource import LocalDraft, norm

BOARD = [
    {"sleeper_id": "1", "player": "Jahmyr Gibbs", "pos": "RB"},
    {"sleeper_id": "2", "player": "James Cook III", "pos": "RB"},
    {"sleeper_id": "3", "player": "Josh Allen", "pos": "QB"},
    {"sleeper_id": "4", "player": "Lamar Jackson", "pos": "QB"},
]


def _src(tmp_path, teams=10, rounds=2):
    return LocalDraft(tmp_path / "picks.json", BOARD, teams, rounds)


def test_name_resolution_handles_suffixes_and_case(tmp_path):
    s = _src(tmp_path)
    assert s.resolve({"name": "james cook"})["sleeper_id"] == "2"     # suffix-free input
    assert s.resolve({"name": "James Cook III"})["sleeper_id"] == "2"
    unk = s.resolve({"name": "Totally Unknown"})
    assert unk["sleeper_id"].startswith("unknown:") and unk["player"] == "Totally Unknown"


def test_snake_slot_mapping_and_unknowns_occupy_slots(tmp_path):
    s = _src(tmp_path, teams=10)
    for i in range(11):
        s.add_pick(f"Nobody Number{i}")   # 11 unknown picks still advance the draft
    picks = s.picks()
    assert picks[0]["draft_slot"] == 1 and picks[9]["draft_slot"] == 10
    assert picks[10]["draft_slot"] == 10 and picks[10]["round"] == 2  # snake turn
    assert s.status() == "drafting"


def test_double_draft_refused_and_undo(tmp_path):
    s = _src(tmp_path)
    assert s.add_pick("Jahmyr Gibbs")["ok"]
    dup = s.add_pick("jahmyr gibbs")
    assert not dup["ok"] and "already drafted" in dup["error"]
    assert s.undo()["ok"]
    assert s.add_pick("Jahmyr Gibbs")["ok"]  # undone -> draftable again


def test_complete_status_and_cap(tmp_path):
    s = _src(tmp_path, teams=2, rounds=1)
    s.add_pick("Jahmyr Gibbs")
    s.add_pick("Josh Allen")
    assert s.status() == "complete"
    assert not s.add_pick("Lamar Jackson")["ok"]


def test_abbreviated_yahoo_feed_names_resolve(tmp_path):
    """Validated in the 2026-08-30 live mock: the Yahoo Picks feed uses
    'J. Gibbs'-style names, sometimes with status tags appended."""
    s = _src(tmp_path)
    assert s.resolve({"name": "J. Gibbs", "pos": "RB"})["sleeper_id"] == "1"
    assert s.resolve({"name": "J. Cook III", "pos": "RB"})["sleeper_id"] == "2"
    assert s.resolve({"name": "J. Allen", "pos": "QB"})["sleeper_id"] == "3"
    # ALL-CAPS status tag stripped (Josh Jacobs CEL case from the mock)
    assert s.resolve({"name": "J. Allen CEL", "pos": "QB"})["sleeper_id"] == "3"
    # pos disambiguates same initial+similar surnames when needed
    assert s.resolve({"name": "L. Jackson", "pos": "QB"})["sleeper_id"] == "4"


def test_picks_cache_invalidates_on_rapid_rewrite(tmp_path):
    board = [{"sleeper_id": "1", "player": "Alpha Back", "pos": "RB"},
             {"sleeper_id": "2", "player": "Beta Back", "pos": "RB"}]
    s = LocalDraft(tmp_path / "p.json", board, 10, 15)
    s.add_pick("Alpha Back")
    assert len(s.picks()) == 1
    s.add_pick("Beta Back")
    assert len(s.picks()) == 2   # size differs even if mtime ties
