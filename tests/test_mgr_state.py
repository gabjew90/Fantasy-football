"""The committed-state store: kv survives a reopen.

The FAAB, alert-dedup and delivery tests went with the cron stack they
covered (DECISIONS #212); the kv store stays because the fantasy commands
read the consensus cache and write the ledger through it.
"""

from manager.store import Store


def test_store_state_survives_reopen(tmp_path):
    Store(tmp_path / "state").set("k", {"a": 1})
    s2 = Store(tmp_path / "state")   # fresh instance = fresh process
    assert s2.get("k") == {"a": 1}


def test_a_read_only_store_writes_nothing(tmp_path):
    s = Store(tmp_path / "state", read_only=True)
    s.set("k", 1)
    assert s.get("k") is None and s.suppressed == ["kv"]
    assert not (tmp_path / "state").exists()
