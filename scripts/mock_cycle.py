"""Rehearsal cycle: Yahoo Picks-feed entries -> local pick file -> engine.
Usage: mock_cycle.py <entries.json> <my_slot> [teams] [rounds]
entries.json: [{"n":1,"name":"J. Gibbs","pos":"RB","team":"Det"}, ...]
Merges by pick number (feed may trim old entries); resolves abbreviated
names against the board by last name + first initial + pos."""
import json, os, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("DRAFTKIT_LEAGUE", "keefamania")
from draftkit.config import Config
from draftkit.tracker import Tracker
import draftkit.snake as snake

entries = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
my_slot = int(sys.argv[2])
teams = int(sys.argv[3]) if len(sys.argv) > 3 else None
rounds = int(sys.argv[4]) if len(sys.argv) > 4 else None

cfg = Config.load()
t = Tracker(cfg, tiers_path=cfg.scoped(cfg.root / "tiers.csv"), my_slot=my_slot)
if teams:
    t.teams = teams
    t.rounds = rounds or t.rounds     # rounds is optional; keep the yaml value
    t.source.teams, t.source.rounds = t.teams, t.rounds

def resolve_full(name, pos):
    m = re.match(r"^([A-Z])[.\s]+(.+)$", name.strip())
    if not m:
        return name
    raw_last = m.group(2).strip()
    # strip trailing ALL-CAPS status tags the feed appends (CEL, PUP, SUSP)
    parts = raw_last.split()
    while len(parts) > 1 and parts[-1].isupper() and len(parts[-1]) <= 4:
        parts.pop()
    initial, last = m.group(1).lower(), " ".join(parts).lower()
    last = re.sub(r"\s+(jr\.?|sr\.?|i{2,4}|iv|v)$", "", last)
    cands = [p for p in t.players
             if p["player"].lower().split()[0][0] == initial
             and re.sub(r"[^a-z]", "", " ".join(p["player"].lower().split()[1:]))
                 .startswith(re.sub(r"[^a-z]", "", last))]
    strict = [c for c in cands if c["pos"] == pos]
    pick = (strict or cands)
    return pick[0]["player"] if len(pick) >= 1 else name

# merge with existing state by pick number
state_path = Path(os.environ.get("MOCK_STATE", "")) if os.environ.get("MOCK_STATE") \
    else Path(cfg.path("logs")) / "mock_feed_state.json"
seen = {}
if state_path.exists():
    seen = {int(k): v for k, v in json.loads(state_path.read_text(encoding="utf-8")).items()}
for e in entries:
    seen[int(e["n"])] = {"name": resolve_full(e["name"], e.get("pos", "")), "pos": e.get("pos", "")}
state_path.write_text(json.dumps({str(k): v for k, v in seen.items()}), encoding="utf-8")

max_n = max(seen) if seen else 0
gaps = [i for i in range(1, max_n + 1) if i not in seen]
# a missed feed entry still occupies its pick slot — placeholder keeps every
# later pick attributed to the right snake slot
ordered = [{"name": seen[i]["name"], "pos": seen[i].get("pos", "")} if i in seen
           else {"name": f"Unknown Pick{i}"} for i in range(1, max_n + 1)]
t.source.set_picks(ordered)
t.poll()
cur = t.current_pick
total = t.teams * t.rounds
rnd, slot = snake.pick_to_round_slot(min(cur, total), t.teams)
unknown = [f'{p["metadata"]["first_name"]} {p["metadata"]["last_name"]}'
           for p in t.state.picks if str(p["player_id"]).startswith("unknown")]
my_next = snake.next_pick_for_slot(cur, my_slot, t.teams, t.rounds) if cur <= total else None
print(f"pick={cur} R{rnd}.{(cur-1)%t.teams+1} on_clock=slot{slot} me={my_slot} "
      f"MY_TURN={'YES' if slot==my_slot else 'no'} my_next={my_next} "
      f"gaps={gaps} unknowns={len(unknown)}")
if unknown:
    print("  UNRESOLVED (board degraded):", ", ".join(unknown[:6]))
if t.state.status != "complete":
    label = "PICK NOW" if slot == my_slot else f"QUEUE PLAN for pick {my_next}"
    print(f"  {label}:")
    for i, (score, why, p) in enumerate(t.recommendations()[:5], 1):
        print(f"   {i}. {p['player']} ({p['pos']}{p['pos_rank']}, T{p['tier']}, "
              f"vorp {p['vorp']:.0f}) — {why[:120]}")
