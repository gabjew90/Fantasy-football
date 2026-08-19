from draftkit.ids import SleeperIndex, normalize_name


def test_normalize_strips_suffixes_and_punctuation():
    assert normalize_name("Marvin Harrison Jr.") == "marvin harrison"
    assert normalize_name("Kenneth Walker III") == "kenneth walker"
    assert normalize_name("De'Von Achane") == "devon achane"
    assert normalize_name("Amon-Ra St. Brown") == "amon ra st brown"


def make_index():
    players = {
        "1234": {"position": "WR", "full_name": "Marvin Harrison", "team": "ARI", "active": True},
        "5678": {"position": "RB", "full_name": "Kenneth Walker", "team": "SEA", "active": True},
        "SF": {"position": "DEF", "first_name": "San Francisco", "last_name": "49ers"},
        "PHI": {"position": "DEF", "first_name": "Philadelphia", "last_name": "Eagles"},
    }
    return SleeperIndex(players)


def test_exact_and_suffix_match():
    idx = make_index()
    assert idx.match("Marvin Harrison Jr.", "WR") == "1234"
    assert idx.match("Kenneth Walker III", "RB") == "5678"


def test_dst_variants():
    idx = make_index()
    assert idx.match("San Francisco 49ers", "DST") == "SF"
    assert idx.match("49ers D/ST", "DEF") == "SF"
    assert idx.match("Philadelphia Eagles", "DEF") == "PHI"


def test_no_false_positive_across_position():
    idx = make_index()
    assert idx.match("Marvin Harrison Jr.", "RB") is None
