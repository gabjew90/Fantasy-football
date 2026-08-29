"""FAAB from transaction history, diff-based alerting, delivery idempotency."""

from manager.deliver import deliver
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
    s2 = Store(tmp_path / "state")   # fresh instance = fresh Actions run
    assert s2.get("k") == {"a": 1}
    assert s2.first_time("x") and not Store(tmp_path / "state").first_time("x")


def test_delivery_is_idempotent_without_smtp(tmp_path, monkeypatch):
    for var in ("SMTP_USER", "SMTP_APP_PASSWORD", "ALERT_EMAIL_TO",
                "GITHUB_TOKEN", "GITHUB_REPOSITORY"):
        monkeypatch.delenv(var, raising=False)
    s = _store(tmp_path)
    assert deliver(s, "waivers:3", "subj", "body A") == "disabled"
    assert deliver(s, "waivers:3", "subj", "body A") == "unchanged"  # no double-send
    assert deliver(s, "waivers:3", "subj", "body B") == "disabled"   # changed -> again


def test_subject_prefixes(tmp_path, capsys):
    s = _store(tmp_path)
    deliver(s, "a", "Warren OUT — start Harvey — locks in 74 min", "x",
            dry_run=True, act_now=True)
    deliver(s, "b", "Waivers wk 3", "y", dry_run=True)
    out = capsys.readouterr().out
    assert "[ACT NOW] Warren OUT — start Harvey — locks in 74 min" in out
    assert "[BRIEF] Waivers wk 3" in out


def test_dry_run_never_records(tmp_path):
    s = _store(tmp_path)
    assert deliver(s, "k", "T", "Body", dry_run=True) == "printed"
    assert s.message("k") == (None, None)  # dry-run leaves no delivery state


def test_github_issue_delivery_and_threading(tmp_path, monkeypatch):
    """First send opens an issue with an @mention; the update comments on it."""
    import manager.deliver as dl

    calls = []

    class FakeResp:
        status_code = 201
        def raise_for_status(self): pass
        def json(self): return {"number": 7}

    def fake_post(url, headers=None, timeout=None, json=None):
        calls.append((url, json))
        return FakeResp()

    monkeypatch.setenv("GITHUB_TOKEN", "t")
    monkeypatch.setenv("GITHUB_REPOSITORY", "gabjew90/Fantasy-football")
    monkeypatch.setattr(dl.requests, "post", fake_post)
    s = Store(tmp_path / "state")

    assert dl.deliver(s, "lineup:1", "Lineup wk 1 — 2 change(s)", "body",
                      act_now=True) == "sent"
    url, payload = calls[0]
    assert url.endswith("/repos/gabjew90/Fantasy-football/issues")
    assert payload["title"] == "[ACT NOW] Lineup wk 1 — 2 change(s)"
    assert payload["body"].startswith("@gabjew90")  # mention -> notification

    assert dl.deliver(s, "lineup:1", "Lineup wk 1 — 2 change(s)", "body",
                      act_now=True) == "unchanged"
    assert dl.deliver(s, "lineup:1", "Lineup wk 1 — 1 change", "new body") == "updated"
    url2, payload2 = calls[1]
    assert url2.endswith("/issues/7/comments")  # same event -> same thread


def test_trade_watch_alerts_once_per_status(tmp_path, monkeypatch):
    from manager import trade_watch

    txns = [{"type": "trade", "status": "pending", "transaction_id": "t1",
             "adds": {"p1": 4, "p2": 9}, "roster_ids": [4, 9]}]
    monkeypatch.setattr("draftkit.briefs.get_transactions", lambda c, l, w: txns)
    monkeypatch.setattr(trade_watch, "values", lambda store: ({"p1": 5000, "p2": 2000}, None))
    ctx = {"week": 1, "client": None,
           "cfg": type("C", (), {"league_id": "x"})(),
           "users_by_rid": {4: "bankerkyle", 9: "DihtrickCohones"},
           "player_row": lambda pid: {"name": f"Player {pid}"}}
    s = Store(tmp_path / "state")
    alerts = trade_watch.scan(ctx, s)
    assert len(alerts) == 1
    subject, body, urgent = alerts[0]
    assert urgent and "pending review" in subject
    assert "LOPSIDED" in body          # 2000/5000 = 0.4 < 0.7
    assert trade_watch.scan(ctx, s) == []   # same status -> silent
    txns[0]["status"] = "complete"          # processed -> one more, non-urgent
    alerts2 = trade_watch.scan(ctx, s)
    assert len(alerts2) == 1 and not alerts2[0][2]
