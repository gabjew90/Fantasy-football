"""Yahoo's "Your Mock Draft Results" email -> the trail shape.

Yahoo does not store mock draft data; the email is the only official record
of every pick in a room. The user's Gmail holds one per mock (2026-09-02:
five, all from 2026-08-31, before any trail existed). Saved as
data/logs/mocks/email_<message id>.txt (a small header, then the email's
"Round by Round results" section), this turns each into the same JSON the
driver's trail produces -- picks with team ids, managers, our seat -- so
scripts/mock_trail.py renders it and scripts/fit_survival.py replays it.
Our pick records (engine reasons) do not exist for these rooms; the fit
does not need them.

    venv\\Scripts\\python.exe scripts\\yahoo_mock_email.py data\\logs\\mocks\\email_*.txt
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from draftkit import snake  # noqa: E402

ROUND = re.compile(r"^\*Round (\d+)\*\s*$")
PICK = re.compile(r"^\((\d+)\)\s+(.*?)\s+-\s+(.*?)\s+\((\w+) - (\w+)\)\s*$")
OURS = ("Gabriel", "My Team")


def display_name(yahoo: str, pos: str) -> str:
    """'Cook III, James' -> 'James Cook III'; 'Jacksonville' (DEF) stays."""
    if pos == "DEF" or "," not in yahoo:
        return yahoo.strip()
    last, first = [x.strip() for x in yahoo.split(",", 1)]
    return f"{first} {last}"


def parse_email(text: str) -> dict:
    """The trail dict for one results email."""
    header = {}
    for line in text.splitlines():
        m = re.match(r"^(Date|Message-Id|Note):\s*(.*)$", line)
        if m:
            header[m.group(1)] = m.group(2).strip()
    teams = None
    picks, managers = [], {}
    rnd = None
    my_team = None
    for line in text.splitlines():
        m = ROUND.match(line.strip())
        if m:
            rnd = int(m.group(1))
            continue
        m = PICK.match(line.strip())
        if not m or rnd is None:
            continue
        idx, manager, player, team, pos = int(m.group(1)), m.group(2), m.group(3), m.group(4), m.group(5)
        if rnd == 1:
            teams = max(teams or 0, idx)
    if not teams:
        raise ValueError("no round 1 picks found")
    rnd = None
    for line in text.splitlines():
        m = ROUND.match(line.strip())
        if m:
            rnd = int(m.group(1))
            continue
        m = PICK.match(line.strip())
        if not m or rnd is None:
            continue
        idx, manager, player, team, pos = int(m.group(1)), m.group(2), m.group(3), m.group(4), m.group(5)
        slot = idx if rnd % 2 == 1 else teams + 1 - idx       # snake: even rounds run backwards
        pick_no = (rnd - 1) * teams + idx
        assert snake.pick_to_round_slot(pick_no, teams) == (rnd, slot)
        picks.append({"pick_no": pick_no, "team_id": str(slot), "name": display_name(player, pos),
                      "pos": pos, "team": team.upper()})
        managers[str(slot)] = {"nickname": manager, "teamId": str(slot), "away": None}
        if manager in OURS:
            my_team = str(slot)
    mid = header.get("Message-Id", "email")
    return {"room": f"email{mid}", "room_name": f"Yahoo mock (results email {mid})", "source": "yahoo_email",
            "captured_at": header.get("Date"), "teams": teams, "my_team": my_team,
            "note": header.get("Note"), "picks": picks, "managers": managers, "our_records": []}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    a = ap.parse_args()
    for f in a.files:
        t = parse_email(Path(f).read_text(encoding="utf-8"))
        out = Path(f).parent / f"mock_{t['room']}.json"
        out.write_text(json.dumps(t, indent=1), encoding="utf-8")
        ours = [p for p in t["picks"] if p["team_id"] == t["my_team"]]
        print(f"{Path(f).name}: {t['teams']} teams, {len(t['picks'])} picks, our seat {t['my_team']}, "
              f"our picks {len(ours)} -> {out.name}")


if __name__ == "__main__":
    main()
