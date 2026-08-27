"""FAAB from transaction history, diff-based alerting, delivery idempotency."""

from manager.deliver import deliver
from manager.faab import crosscheck, spent_from_transactions
from manager.store import Store


def _store(tmp_path):
    return Store(tmp_path / "state.db")


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


def test_delivery_is_idempotent_without_webhook(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("DISCORD_WEBHOOK_URL", raising=False)
    s = _store(tmp_path)
    assert deliver(s, "waivers:3", "t", "body A") == "disabled"
    assert deliver(s, "waivers:3", "t", "body A") == "unchanged"  # no double-post
    assert deliver(s, "waivers:3", "t", "body B") == "disabled"   # changed -> again


def test_dry_run_prints_and_never_records(tmp_path, capsys):
    s = _store(tmp_path)
    assert deliver(s, "k", "Title", "Body", dry_run=True) == "printed"
    out = capsys.readouterr().out
    assert "Title" in out and "Body" in out
    assert s.message("k") == (None, None)  # dry-run leaves no delivery state
