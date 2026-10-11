"""CHAT.md's game-read rule (DECISIONS #235): a game read is the calculator's -- `nfl.py status
--game` then calculator cards -- and the engine's matchup guide runs only when the engine is named.
The 2026-10-10 chat test found the two rules contradicting each other."""
from __future__ import annotations

import re
from pathlib import Path

CHAT = (Path(__file__).resolve().parents[1] / "CHAT.md").read_text(encoding="utf-8")


def test_a_game_read_is_status_then_the_calculator():
    assert "**A game read is the calculator's**" in CHAT
    rule = CHAT[CHAT.index("**A game read is the calculator's**"):][:700]
    assert "nfl.py status --game AWAY@HOME" in rule and "calculator's cards" in rule
    assert "only when the user asks for the engine by name" in rule


def test_the_routing_table_sends_a_game_read_to_status_and_the_calculator():
    row = next(ln for ln in CHAT.splitlines() if ln.startswith("| break down this game"))
    assert "`nfl.py status --game AWAY@HOME`" in row and "props.calc" in row
    assert "only when the engine is named" in row


def test_no_rule_still_sends_every_game_read_to_the_engine_guide():
    # the contradicting sentence (#157): a game read follows the engine's matchup guide EXACTLY
    assert not re.search(r"A game read follows the props engine's team matchup guide", CHAT)
    assert '"break down this game"' not in CHAT.split("## Routing")[0], \
        "the full-report sentence no longer points a game breakdown at props game"
