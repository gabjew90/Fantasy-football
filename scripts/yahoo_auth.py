"""Yahoo Fantasy OAuth, step by step.

    python scripts/yahoo_auth.py url          # print the URL to open and approve
    python scripts/yahoo_auth.py code XXXXXXX # exchange the code Yahoo shows you
    python scripts/yahoo_auth.py test         # game/nfl, then the Keefamania league
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.stdout.reconfigure(encoding="utf-8")
from dotenv import load_dotenv  # noqa: E402

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from manager import yahoo_api  # noqa: E402

LEAGUE = "nfl.l.49649"


def main(argv: list[str]) -> int:
    cmd = argv[1] if len(argv) > 1 else "url"
    if cmd == "url":
        print(yahoo_api.auth_url())
        return 0
    if cmd == "code":
        tok = yahoo_api.exchange(argv[2])
        print(f"token saved to {yahoo_api.TOKEN_PATH}; expires_in {tok.get('expires_in')}s; "
              f"refresh token {'present' if tok.get('refresh_token') else 'MISSING'}")
        return 0
    if cmd == "test":
        try:
            g = yahoo_api.get("game/nfl")
            game = g["fantasy_content"]["game"][0]
            print(f"game/nfl OK: {game.get('name')} {game.get('season')} (game_key {game.get('game_key')})")
        except yahoo_api.YahooScopeError as e:
            print(f"NOT APPROVED: {e}")
            return 2
        lg = yahoo_api.get(f"league/{LEAGUE}")
        meta = lg["fantasy_content"]["league"][0]
        print(f"league OK: {meta.get('name')} — {meta.get('num_teams')} teams, week {meta.get('current_week')}, "
              f"scoring {meta.get('scoring_type')}")
        tm = yahoo_api.get(f"league/{LEAGUE}/teams")
        teams = tm["fantasy_content"]["league"][1]["teams"]
        names = [v["team"][0][2]["name"] for k, v in teams.items() if k != "count"]
        print(f"teams ({teams.get('count')}): {names}")
        return 0
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
