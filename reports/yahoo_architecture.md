# How the Yahoo draft is actually driven (2026-09-01)

## The constraint, verified three ways

The page cannot reach a local Python server. Tested against a threaded server
with correct CORS headers that `curl` could reach throughout:

| transport | result |
|---|---|
| `fetch('http://127.0.0.1:…')` | never settles — no response, no rejection |
| `<script src="http://127.0.0.1:…">` (JSONP) | never fires |
| `new WebSocket('ws://127.0.0.1:…')` | `onerror` |

Chrome's Private Network Access blocks public→localhost. **Zero-lag Python is
impossible**, so the question is only how stale a plan we must accept.

## What was measured

Replaying a real 10-team draft, rivals held fixed, only our picks re-decided,
scored on the starting lineup we end up with (`scripts/engine_bakeoff.py`).

| approach | mean vs fresh engine | worse at |
|---|---:|---:|
| fresh Python engine (unattainable) | 0.0 | — |
| **bridge, plan 1 pick stale** | **−9.2** | 5/10 |
| JS reimplementation, fresh data | −10.1 | 6/10 |
| bridge, plan 2 picks stale | −14.2 | 4/10 |
| bridge, per-position plan, 2 stale | −21.3 | 7/10 |

Staleness decays fast: the engine's top pick is still available **89%** of the
time at 1 pick of lag, 80% at 2, 58% at 5. A 25-deep list was never exhausted.

## Two things I expected and got wrong

**A per-position plan should have beaten a flat list.** The idea was that the
page could re-pick within each position as players vanish, comparing
positions by the engine's own urgency. It came out *worse* (−21.3 vs −14.2),
because the engine's flat ordering already encodes the two-pick planner, the
Δ tiebreak and the need weighting — re-deriving order from urgency alone
throws all three away.

**Fresh-but-imperfect nearly matches perfect-but-stale.** The JS
reimplementation on live data (−10.1) is within noise of the real engine one
pick behind (−9.2).

## The decision

Ship the bridge, refreshing the plan at **"You are next"** (1 pick of lag).
Not because it measures dramatically better — it does not — but because it
leaves **one ranking implementation in the repo**. The JS engine had drifted
to 25% agreement without anyone noticing; a second implementation is a
liability that grows silently. The JS ranking stays only as a *labelled*
fallback for a missing plan.

Split of responsibility:

- **`scripts/yahoo_bridge.py`** — the engine. `tracker.recommendations()`,
  same `config.yaml` knobs as the Sleeper draft, real rationale strings.
- **`scripts/draft_driver.js`** — the hands. Row matching, star toggle,
  on-clock re-render, defenses without first names, keeping autopick from
  arming. None of this can run anywhere but the page.
