/* Yahoo in-page draft driver.
 *
 * WHY THIS EXISTS (mock 2026-08-31 post-mortem):
 *   Every Python round-trip costs 30-60s of wall clock. Two failures follow:
 *     1. Yahoo arms "autopick mode due to inactivity" during the dead time,
 *        and once armed it drafts INSTANTLY when your turn opens -- the
 *        wait-for-clock-then-click protocol is structurally void.
 *     2. A queue built once goes stale; it does not re-rank as the roster
 *        changes, which is how a 3rd QB got queued behind two rostered QBs.
 *
 *   So the whole decision loop lives in the page. The board is injected once;
 *   the driver stays resident (which also keeps the client "active"), and
 *   rebuilds the queue against the CURRENT roster every cycle.
 *
 * GUARDRAILS are a port of draftkit/tracker.py::_pos_allowed. That function is
 * the single source of truth in Python; this is the only sanctioned copy, and
 * it must be updated in lockstep. The Purdy mistake happened precisely because
 * the hand-driven queue ranked on raw VORP and never called it.
 */
window.DK = (function () {
  const S = {
    records: [],        // every pickRecord() this session, for trail()
    board: [],          // [{n,k,p,t,v,j,a,s,u,tier}] sorted by VORP desc
    cfg: {
      slots: { QB: 1, RB: 2, WR: 2, TE: 1, FLEX: 1, K: 1, DEF: 1 },
      bench: 6,
      rounds: 15,
      teams: 10,
      qb2Round: 10,
      te2FallPicks: 12,
      upsideFromRound: 8,
      upsideMult: 1.15,
      queueDepth: 5,
      bridge: 'https://127.0.0.1:8443',
      mySlot: null,
    },
    log: [],
    lastRoster: -1,
    running: false,
    gone: new Set(),    // board entries proven undraftable (no star button)
    starred: new Set(), // players WE queued; the star is a toggle, never re-click
    ctx: null,          // shared ranking context (te6 / bestFlexAlt / need) for te2Ok
    plan: null,         // ranked list from the REAL engine (yahoo_bridge.py)
    planNeeds: null,
    planPick: null,     // pick number the plan was computed at
    planErr: null,
    planAt: 0,
    seenPicks: new Map(),  // accumulated; the Picks panel virtualises
  };

  const FLEX_OK = { RB: 1, WR: 1, TE: 1 };
  const SUFFIX = { jr: 1, sr: 1, ii: 1, iii: 1, iv: 1, v: 1 };

  function note(msg) {
    const line = new Date().toISOString().slice(11, 19) + ' ' + msg;
    S.log.push(line);
    if (S.log.length > 400) S.log.shift();
    return line;
  }

  /* ---- name keying: must match scripts/export_board_json.py::key() ---- */
  function norm(s) {
    return (s || '')
      .normalize('NFKD').replace(/[̀-ͯ]/g, '')
      .toLowerCase().replace(/[^a-z0-9 ]/g, ' ').replace(/\s+/g, ' ').trim();
  }
  function keyFull(name) {
    let parts = norm(name).split(' ').filter(Boolean);
    const stripped = parts.filter(p => !SUFFIX[p]);
    if (stripped.length) parts = stripped;
    if (!parts.length) return '';
    if (parts.length === 1) return parts[0];
    return parts[0][0] + ' ' + parts[parts.length - 1];
  }
  /* Yahoo renders "J. Gibbs" / "B. Thomas Jr." -> same key shape */
  function keyAbbr(disp) {
    let parts = norm(disp).split(' ').filter(Boolean);
    const stripped = parts.filter(p => !SUFFIX[p]);
    if (stripped.length) parts = stripped;
    if (!parts.length) return '';
    if (parts.length === 1) return parts[0];
    return parts[0][0] + ' ' + parts[parts.length - 1];
  }

  /* THE identity key, used by every comparison in this file.
   *
   * A team defense has no first name: the board says "Minnesota Vikings",
   * the queue row says "Vikings", the player table says "Vikings DEF". Any
   * function that keys defenses differently from the others silently stops
   * matching them -- which has now cost two separate bugs (unmatchable in the
   * player table, then invisible in the queue). One function, everywhere. */
  function idKey(name, pos) {
    if (pos === 'DEF') {
      const parts = (name || '').trim().split(/\s+/);
      return (parts[parts.length - 1] || '').toLowerCase();
    }
    return keyFull(name);
  }

  /* ---------------- DOM readers ---------------- */

  function rosterCount() {
    const m = document.body.innerText.match(/YOUR TEAM \((\d+)\/(\d+)\)/);
    return m ? { have: +m[1], of: +m[2] } : null;
  }

  /* My roster as position counts. Parsed from the YOUR TEAM panel: each
   * rostered player line carries "<Name> <POS> <TEAM> Bye <n>". */
  function myRoster() {
    const t = document.body.innerText;
    const i = t.indexOf('YOUR TEAM');
    if (i < 0) return null;
    const seg = t.slice(i, i + 1400).replace(/\s+/g, ' ');
    const out = [];
    const re = /([A-Z]\.\s?[A-Za-z'\-\.]+(?:\s+Jr\.|\s+Sr\.|\s+II|\s+III)?)\s+(?:Q|IR|O|D|SUSP|PUP|CEL|NA)?\s*(QB|RB|WR|TE|K|DEF)\s+([A-Za-z]{2,3})\s+Bye/g;
    let m;
    while ((m = re.exec(seg))) out.push({ disp: m[1].trim(), pos: m[2], team: m[3], k: keyAbbr(m[1]) });
    // team defenses render without an initial
    const dre = /([A-Z][A-Za-z]+(?:\s[A-Z][A-Za-z]+)?)\s+DEF\s+Bye/g;
    while ((m = dre.exec(seg))) {
      if (!out.some(o => o.pos === 'DEF')) out.push({ disp: m[1].trim(), pos: 'DEF', team: '', k: idKey(m[1], 'DEF') });
    }
    const counts = {};
    out.forEach(p => { counts[p.pos] = (counts[p.pos] || 0) + 1; });
    return { players: out, counts };
  }

  /* Availability is NOT scraped.
   *
   * The obvious implementation -- regex the page for drafted names -- is
   * wrong: the page also renders the player table, which is full of
   * UNDRAFTED players, so it marks everyone visible as gone. An earlier
   * version of this file shipped that bug.
   *
   * Ground truth instead: a drafted player's row has no star button. So we
   * attempt the action and treat failure as "gone", memoising into S.gone so
   * we never retry a name. Self-correcting, and it needs no feed parsing. */
  function markGone(entry) { S.gone.add(entry.n + '|' + entry.p); }
  function isGone(entry) { return S.gone.has(entry.n + '|' + entry.p); }

  /* Every pick made so far, for the bridge to rebuild engine state.
   *
   * Read from the Results tab's round-by-round list, which prints
   * "Round 3, Pick 2 (22nd Overall) Brock Bowers LV - TE". That is the one
   * place Yahoo states the pick NUMBER, and the number is what the engine
   * needs -- the roster panel is slot-ordered, which already caused one
   * wrong report to the user. */
  /* Every pick made so far, accumulated.
   *
   * Yahoo's Picks panel is the only place that states pick NUMBERS during a
   * live draft (the Results tab is empty until it ends, and the roster panel
   * is slot-ordered -- which already caused one wrong report). Its shape is
   * newline-separated:
   *
   *     50 / You / D. Adams / WR / LAR / Bye 11
   *
   * Two things matter. It VIRTUALISES -- mid-draft it held picks 8-50 and had
   * dropped 1-7 -- so the feed is accumulated across cycles and never
   * forgotten. And it labels our own picks "You", which is authoritative in a
   * way snake arithmetic is not: this very draft reshuffled us from slot 3 to
   * slot 10 before it began. */
  /* The LEFT panel has two tabs, Queue and Picks, and only the visible one
   * is in the page text. The room opens on Queue. Mock 11 (2026-09-01) ran
   * its first two picks with an EMPTY feed for exactly that reason: the
   * bridge was told it was pick 1 with nothing drafted, and planned
   * accordingly. Assert the tab before reading, the same way
   * ensurePlayersTab asserts the right-hand pane before a row search. */
  function ensureLeftTab(name) {
    const tab = [...document.querySelectorAll('button')]
      .find(b => b.textContent.replace(/\d+/g, '').trim() === name);
    if (!tab) return false;
    // aria-selected is the only reliable signal; absent counts as "not"
    if (tab.getAttribute('aria-selected') !== 'true') tab.click();
    return true;
  }

  function parsePicksPanel() {
    ensureLeftTab('Picks');
    const L = document.body.innerText.split(String.fromCharCode(10)).map(s => s.trim());
    const POS = /^(QB|RB|WR|TE|K|DEF)$/;
    const out = [];
    for (let i = 0; i < L.length - 4; i++) {
      if (!/^\d{1,3}$/.test(L[i])) continue;
      const pick = +L[i];
      if (pick < 1 || pick > 400) continue;
      const mgr = L[i + 1];
      if (!mgr || /^\d/.test(mgr)) continue;
      let j = i + 2;
      const name = L[j];
      if (!name || !/^[A-Z]\.\s?[A-Za-z]/.test(name)) continue;
      j++;
      if (L[j] && !POS.test(L[j])) j++;            // optional Q / IR tag
      if (!L[j] || !POS.test(L[j])) continue;
      const pos = L[j], team = L[j + 1];
      if (!L[j + 2] || !/^Bye/.test(L[j + 2])) continue;
      out.push({ pick_no: pick, name, pos, team, mine: /^you$/i.test(mgr) });
    }
    return out;
  }

  /* The accumulated feed survives a page reload via sessionStorage (keyed
   * by the draft URL), because the Picks panel does not: after a reload it
   * shows only the last few picks, and mock 11 briefly planned as if it were
   * pick 4 in round 14. The bridge keeps its own union too; this is the
   * page-side half so a fresh driver is never blind. */
  // guarded: the node test harness has no location or sessionStorage
  const FEED_KEY = 'dk.seenPicks:' + (typeof location !== 'undefined' ? location.pathname : '');
  function restoreFeed() {
    if (S.seenPicks.size) return;
    try {
      const raw = sessionStorage.getItem(FEED_KEY);
      if (!raw) return;
      for (const p of JSON.parse(raw)) S.seenPicks.set(p.pick_no, p);
    } catch (e) { /* storage unavailable: live reads still work */ }
  }
  function persistFeed() {
    try {
      sessionStorage.setItem(FEED_KEY, JSON.stringify([...S.seenPicks.values()]));
    } catch (e) { /* quota or private mode: not fatal */ }
  }

  function draftedFeed() {
    restoreFeed();
    for (const p of parsePicksPanel()) {
      const prev = S.seenPicks.get(p.pick_no);
      if (!prev || (p.mine && !prev.mine)) S.seenPicks.set(p.pick_no, p);
    }
    persistFeed();
    return [...S.seenPicks.values()].sort((a, b) => a.pick_no - b.pick_no);
  }

  /* The header states it outright: "YOUR TURN - ROUND 6, PICK 51". */
  function currentPickNo() {
    const m = document.body.innerText.match(/ROUND\s+(\d+),\s*PICK\s+(\d+)/i);
    return m ? +m[2] : null;
  }

  /* Why a row lookup missed. Pure so it can be tested directly -- this is the
   * exact judgement that cost mock 2 thirty-six elite players by reading a
   * dead UI as league-wide unavailability. Absence only counts when the
   * table is demonstrably rendering other players. */
  function classifyMiss(rowFound, isTableLive) {
    if (rowFound) return 'found';
    return isTableLive ? 'gone' : 'uinotready';
  }

  function onClock() { return /YOUR TURN, DRAFT NOW/i.test(document.title); }

  function picksUntil() {
    const m = document.title.match(/(\d+) picks? until/i);
    if (m) return +m[1];
    if (onClock()) return 0;
    if (/You are next/i.test(document.title)) return 1;
    return null;
  }

  function currentRound() {
    const r = rosterCount();
    return r ? r.have + 1 : 1;
  }

  /* ---------------- survival + urgency (port of urgency.py) ----------------
   *
   * The Python engine estimates, by Monte Carlo over every intervening rival
   * pick, the chance each player is still on the board at our next turn, then
   * shrinks the raw probability through a map fitted to the Omnibeta CLV
   * retro. This driver originally replaced all of that with a binary guess
   * (`adp >= nextPick + 5`), which is what left it unable to see that two
   * elite TEs would not both survive -- the failure planner.py was written to
   * fix at picks #26/#47 of the real draft.
   *
   * Ported here as a closed form rather than a simulation: P(survive) is the
   * normal tail of (adp - nextPick) / sigma, with sigma growing by round the
   * same way tracker._sigma does. Same shape, no RNG, cheap enough to run
   * every cycle in the page.
   */
  // 1.0 = no shrink (DECISIONS #26, 2026-09-02): the 0.55 map was fitted to
  // mis-scored data; re-scored, the raw simulation is calibrated from 50% up.
  const SURVIVAL_SHRINK = 1.0;
  const NEED_DAMP = 0.6;          // planner.py: position filling no starter slot

  function normCdf(z) {           // Abramowitz-Stegun 7.1.26
    const s = z < 0 ? -1 : 1, x = Math.abs(z) / Math.SQRT2;
    const t = 1 / (1 + 0.3275911 * x);
    const y = 1 - ((((1.061405429 * t - 1.453152027) * t + 1.421413741) * t
              - 0.284496736) * t + 0.254829592) * t * Math.exp(-x * x);
    return 0.5 * (1 + s * y);
  }
  function calibrate(p) { return 0.5 + (p - 0.5) * SURVIVAL_SHRINK; }

  /* sigma: ADP noise in picks, widening as the draft goes on (tracker._sigma) */
  function sigmaFor(rnd) { return 6.0 + 1.5 * Math.max(0, rnd - 1); }

  /* Survival is RANK-based, not ADP-based.
   *
   * The first version used the normal tail of (adp - nextPick), which gives
   * nonsense for anyone who has already fallen. In the bake-off at slot 5,
   * Jaxon Smith-Njigba was still on the board at pick 16 with an ADP of 7.2:
   * absolute ADP said he was long gone, so his survival read as near zero and
   * WR looked urgent. Python does not have this problem because it simulates
   * rivals choosing from the CURRENT pool.
   *
   * Model instead: rivals take roughly the top of the remaining board with
   * noise, so over k intervening picks a player sitting at market rank r
   * among the available survives with P(r > k), smeared by sigma. Being a
   * faller helps him -- a low current rank is exactly why he is still here.
   */
  function survivalProb(rankAmongAvail, picksBetween, rnd) {
    const z = (picksBetween - rankAmongAvail) / sigmaFor(rnd);
    return Math.min(0.99, Math.max(0.01, calibrate(1 - normCdf(z))));
  }

  /* E[VORP of the best player still available at `pos` on our next turn].
   * Walks the position in VORP order: the best survivor is the first player
   * who lasts, so weight each by the chance everyone above him is gone. */
  function eBestNext(avail, pos, nextPick, rnd, curPick) {
    /* Market rank among the available: how rivals actually order the board. */
    const byMarket = avail.slice().sort((a, b) =>
      ((a.a == null ? 9999 : a.a) - (b.a == null ? 9999 : b.a)));
    const rankOf = new Map();
    byMarket.forEach((p, i) => rankOf.set(p, i + 1));
    const k = Math.max(0, nextPick - curPick);

    let carry = 1.0, exp = 0.0;
    for (const p of avail) {                 // avail is VORP-descending
      if (p.p !== pos) continue;
      const s = survivalProb(rankOf.get(p) || 9999, k, rnd);
      exp += carry * s * p.v;
      carry *= (1 - s);
      if (carry < 0.01) break;
    }
    return exp;
  }

  /* ---------------- guardrails (port of _pos_allowed) ---------------- */

  function needsMap(counts) {
    const need = {};
    for (const p of ['QB', 'RB', 'WR', 'TE', 'K', 'DEF']) {
      need[p] = Math.max(0, (S.cfg.slots[p] || 0) - (counts[p] || 0));
    }
    // FLEX consumes surplus RB/WR/TE
    let surplus = 0;
    for (const p of ['RB', 'WR', 'TE']) {
      surplus += Math.max(0, (counts[p] || 0) - (S.cfg.slots[p] || 0));
    }
    need.FLEX = Math.max(0, S.cfg.slots.FLEX - surplus);
    return need;
  }

  function needsPosition(need, pos) {
    if ((need[pos] || 0) > 0) return true;
    if (FLEX_OK[pos] && (need.FLEX || 0) > 0) return true;
    return false;
  }

  function posAllowed(pos, rnd, counts, picksLeft, top6TeFell) {
    if (pos === 'K' || pos === 'DEF') {
      if (picksLeft > 2) return false;
      if ((counts[pos] || 0) >= 1) return false;
    }
    if (pos === 'QB') {
      if ((counts.QB || 0) >= 2) return false;
      if ((counts.QB || 0) >= 1 && rnd < S.cfg.qb2Round) return false;
    }
    if (pos === 'TE') {
      if ((counts.TE || 0) >= 2) return false;
      if ((counts.TE || 0) >= 1 && !top6TeFell) return false;
    }
    return true;
  }

  /* A second TE can only start in FLEX, competing with the RB/WR who would
   * otherwise hold that slot, so it must clear the best flex alternative by a
   * margin. This lived only inside rank()'s filter, which meant syncQueue's
   * simulated re-check -- which calls guardrailOk directly -- did not apply
   * it, and mock 7 queued McBride AND Bowers back to back. One rule, one
   * place, consulted by every caller. */
  /* Python's TE2 rule (tracker.recommendations): a second TE is allowed only
   * when a top-6 TE has FALLEN te2_fall picks past his ADP -- an unexpected
   * bargain, not a general licence.
   *
   * The driver had substituted an invented margin ("beat the best available
   * RB/WR by 10 VORP"), which is stricter in some spots and looser in others.
   * The bake-off (scripts/engine_bakeoff.py) showed the driver losing to the
   * Python engine at 8 of 10 slots; deviations like this are why. Match the
   * engine rather than improvise. */
  function te2Ok(p, counts) {
    if (p.p !== 'TE' || (counts.TE || 0) < 1) return true;
    return !!(S.ctx && S.ctx.top6TeFell);
  }

  /* Structural rules only. There used to be a fourth: "no non-negative-VORP
   * bench pick once we hold a stash". By round 9 every remaining RB/WR is
   * below replacement, so at pick 86 of mock 13 (2026-09-02) it refused all
   * 24 candidates the engine sent -- bench-insurance rows the engine prices
   * ABOVE zero on purpose -- and the clock ran out. Whether a bench player is
   * worth the pick is the engine's call (bench.py); the driver only keeps the
   * roster legal. */
  function guardrailOk(p, rnd, need, counts, picksLeft, top6TeFell) {
    if (!te2Ok(p, counts)) return false;
    if (!posAllowed(p.p, rnd, counts, picksLeft, top6TeFell)) return false;
    const openStarters = ['QB', 'RB', 'WR', 'TE', 'FLEX', 'K', 'DEF']
      .reduce((a, k) => a + (need[k] || 0), 0);
    if (picksLeft <= openStarters && !needsPosition(need, p.p)) return false;

    /* K/DEF reservation. Every other slot has many eligible players; a K slot
     * can only ever be filled by a kicker. So the final picks must be RESERVED
     * for the unfilled K/DEF slots, or the draft ends with an empty mandatory
     * slot. Without this, a high-VORP RB outscores a kicker on the last pick
     * and we field an incomplete lineup -- caught by the driver's own test,
     * not by the Python engine, whose must-fill rule is not position-aware. */
    const kdefOpen = (need.K || 0) + (need.DEF || 0);
    if (kdefOpen > 0 && picksLeft <= kdefOpen && p.p !== 'K' && p.p !== 'DEF') {
      return false;
    }
    return true;
  }

  /* ---------------- the client's own state (design 2026-09-01, layer 2) ------
   *
   * The draft client is React + Redux. Its store holds everything the screen
   * shows and more, as data: draftPicks.order[{id, teamId, playerId}],
   * players.byId[pid]{fname, lname, primary_pos, team_abbr, bye, inj},
   * draftOrder{currentPick, currentTeam}, league.managers[id]{teamId, away,
   * loggedin}, context.managerId, countdown.seconds. Reading that instead of
   * page text removes the feed parser, the roster parser and the header regex
   * -- three of the four things that broke in mock 11 -- and it does not care
   * which tab or layout is showing. Found by walking the React fiber tree for
   * a Provider whose props carry a store (mock 12, 2026-09-01).
   *
   * If the store cannot be found (Yahoo restructures the app), everything
   * below returns null and the DOM readers take over, loudly. */
  function findStore() {
    if (S.store && typeof S.store.getState === 'function') return S.store;
    const queue = [];
    for (const el of document.querySelectorAll('body, body *')) {
      for (const k of Object.keys(el)) {
        if (k.startsWith('__reactContainer$')) queue.push(el[k]);
      }
      if (el._reactRootContainer && el._reactRootContainer._internalRoot) {
        queue.push(el._reactRootContainer._internalRoot.current);
      }
      if (queue.length) break;
    }
    const seen = new Set();
    let n = 0;
    while (queue.length && n < 200000) {
      const f = queue.shift();
      if (!f || seen.has(f)) continue;
      seen.add(f); n++;
      const p = f.memoizedProps || {};
      if (p.store && typeof p.store.getState === 'function') { S.store = p.store; return p.store; }
      if (p.value && p.value.store && typeof p.value.store.getState === 'function') { S.store = p.value.store; return p.value.store; }
      if (f.child) queue.push(f.child);
      if (f.sibling) queue.push(f.sibling);
    }
    return null;
  }

  /* One structured snapshot, or null. Positions come as Yahoo's codes; DEF is
   * "DEF" there already. Names are "First Last" -- the bridge keys on
   * first-initial + surname, so that matches the board. */
  function storeState() {
    const store = findStore();
    if (!store) return null;
    let s;
    try { s = store.getState(); } catch (e) { return null; }
    if (!s || !s.draftPicks || !s.players || !s.draftOrder) return null;
    const byId = s.players.byId || {};
    const managers = (s.league && s.league.managers) || {};
    const me = s.context && managers[String(s.context.managerId)];
    const myTeam = me ? String(me.teamId) : null;
    const drafted = (s.draftPicks.order || []).filter(o => o && o.playerId).map(o => {
      const p = byId[o.playerId] || {};
      return { pick_no: +o.id, name: ((p.fname || '') + ' ' + (p.lname || '')).trim(),
               pos: p.primary_pos || p.display_pos || '', team: p.team_abbr || '',
               team_id: String(o.teamId),      // plan B5: lets the bridge map away managers to draft slots
               slot: null, mine: myTeam != null && String(o.teamId) === myTeam };
    });
    const away = Object.values(managers).filter(m => m.away).map(m => String(m.teamId));
    // draftOrder.currentPick is the count of picks MADE (null before pick 1,
    // 5 while pick 6 is on the clock), so the pick on the clock is +1. Found
    // in mock 13 when the on-clock gate refused to click at pick 6 because the
    // plan said 6 and the store said 5.
    const made = s.draftOrder.currentPick;
    const onClockPick = Number.isFinite(+made) && made !== null ? (+made + 1) : null;
    return {
      current_pick: onClockPick,
      current_team: s.draftOrder.currentTeam != null ? String(s.draftOrder.currentTeam) : null,
      my_team: myTeam,
      on_clock: myTeam != null && String(s.draftOrder.currentTeam) === myTeam,
      seconds: s.countdown ? s.countdown.seconds : null,
      state: s.draft && s.draft.state,
      drafted,
      my_roster: drafted.filter(d => d.mine).map(d => ({ name: d.name, pos: d.pos })),
      away_teams: away,
      queue: (s.queue || []).map(String),
    };
  }

  /* test hook: hand storeState() a store without a React tree to walk */
  function _setStore(store) { S.store = store; return !!store; }

  /* ---------------- ranking ---------------- */

  /* Ask the real engine, from inside the page, at the moment of the pick.
   *
   * This is what makes staleness zero. Chrome silently drops an HTTPS page's
   * request to http://127.0.0.1 -- verified with an instrumented server that
   * logged curl and nothing from Chrome -- but over TLS with an accepted
   * certificate it is a normal cross-origin fetch. Measured round trip from
   * the live draft page: 10ms for /ping, 614ms for a full plan including the
   * Monte Carlo. Against a 60-second clock that is free.
   *
   * If the bridge is not running the driver keeps working on its own weaker
   * ranking, and says so, because a silent downgrade is the failure this
   * whole exercise was about. */
  async function refreshPlan() {
    if (!S.cfg.bridge) return 'no bridge configured';
    const slot = S.cfg.mySlot || slotFromUrl();
    if (!slot) return 'unknown draft slot';
    try {
      /* Three views of the same draft, because each one fails alone:
       *   drafted   -- the Picks panel, which VIRTUALISES (after a reload it
       *                shows only the last few picks) and whose "You" label
       *                is missing on autopicks;
       *   my_roster -- the roster panel, authoritative for what WE hold;
       *   current_pick -- the header, authoritative for WHERE we are.
       * The bridge reconciles them (yahoo_bridge.build_tracker). Mock 11
       * drafted from a plan that believed it was pick 4 with an empty roster
       * after a mid-draft reload, because only `drafted` was sent. */
      /* Prefer the client's own store; fall back to the page readers and say
       * so. The two must agree when both exist -- a disagreement is logged,
       * and the store wins, because it is the data the screen was drawn from. */
      const snap = storeState();
      const ros = myRoster();
      const domDrafted = draftedFeed();
      const domRoster = (ros ? ros.players : []).map(p => ({ name: p.disp, pos: p.pos }));
      S.source = snap ? 'store' : 'dom';
      if (snap && domDrafted.length && Math.abs(domDrafted.length - snap.drafted.length) > 3) {
        note('store/dom disagree: store has ' + snap.drafted.length + ' picks, page text ' + domDrafted.length);
      }
      const body = JSON.stringify({
        my_slot: slot, teams: S.cfg.teams, rounds: S.cfg.rounds,
        depth: 25,
        drafted: snap ? snap.drafted : domDrafted,
        my_roster: snap ? snap.my_roster : domRoster,
        current_pick: snap && snap.current_pick ? snap.current_pick : currentPickNo(),
        draft_key: location.pathname,   // the bridge keeps a per-draft union of the feed
        source: S.source,
        away_teams: snap ? snap.away_teams : [],   // plan B5: managers on autopick right now
      });
      const r = await fetch(S.cfg.bridge + '/plan', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body,
      });
      const j = await r.json();
      if (j.err) { S.planErr = j.err; return 'engine error: ' + j.err; }
      S.plan = j.plan; S.planNeeds = j.needs; S.planPick = j.current_pick;
      S.planErr = null; S.planAt = Date.now();
      return 'plan ' + (j.plan || []).length + ' deep @pick ' + j.current_pick + ' via ' + S.source;
    } catch (e) {
      S.planErr = String(e).slice(0, 120);
      return 'bridge unreachable: ' + S.planErr;
    }
  }

  function slotFromUrl() {
    const m = location.pathname.match(/\/draftclient\/f1\/\d+\/(\d+)/);
    return m ? +m[1] : null;
  }

  /* THE PLAN comes from the real engine.
   *
   * scripts/yahoo_bridge.py runs draftkit/tracker.py -- the same
   * recommendations() the Sleeper draft used -- and hands the page a ranked
   * list. The page walks it and clicks. There is no second ranking
   * implementation to drift.
   *
   * Everything below rank() is still needed and still lives here: matching a
   * board entry to a Yahoo row, the star toggle, the on-clock re-render, team
   * defenses having no first name. That is actuation, and it genuinely cannot
   * run anywhere but the page.
   *
   * The local ranking is kept ONLY as a fallback for a stale or missing plan,
   * and says so in the output, because a silent fallback to the weaker
   * ranking is exactly the failure this whole exercise was about. */
  function rankFromPlan() {
    const ros = myRoster();
    if (!ros || !S.plan || !S.plan.length) return null;
    const mine = new Set(ros.players.map(p => p.k + '|' + p.pos));
    const have = ros.players.length;
    const out = [];
    for (const e of S.plan) {
      const b = S.board.find(x => x.n === e.n && x.p === e.p)
             || { n: e.n, p: e.p, t: e.t, v: e.v, a: e.a, k: idKey(e.n, e.p) };
      if (mine.has(b.k + '|' + b.p) || isGone(b)) continue;
      // s / sr / e: the engine's shown survival, raw survival and expected
      // best-at-next-turn for this candidate's market, kept structured so the
      // trail never has to parse them back out of the why string
      out.push({ n: b.n, p: b.p, t: b.t, v: b.v, why: e.why, fromEngine: true,
                 s: e.s == null ? null : e.s, sr: e.sr == null ? null : e.sr, e: e.e == null ? null : e.e });
    }
    if (!out.length) return null;
    return {
      round: have + 1, picksLeft: S.cfg.rounds - have,
      counts: ros.counts, need: S.planNeeds || {},
      source: 'engine', planAge: S.planPick == null ? null : S.planPick,
      top: out, availCount: out.length, goneCount: S.gone.size,
    };
  }

  function rank() {
    const fromEngine = rankFromPlan();
    if (fromEngine) return fromEngine;
    const ros = myRoster();
    if (!ros) return { err: 'no roster panel' };
    const counts = ros.counts;
    const have = ros.players.length;
    const picksLeft = S.cfg.rounds - have;
    const rnd = have + 1;
    const need = needsMap(counts);
    const mine = new Set(ros.players.map(p => p.k + '|' + p.pos));


    /* TE2 gate. The Python engine asks "did a top-6 TE fall to us", which
     * needs a reliable drafted-set we deliberately do not have. Equivalent
     * local rule: a 2nd TE is only allowed if the candidate IS one of the
     * board's six best TEs -- same intent, no scraping. */
    const te6 = S.board.filter(x => x.p === 'TE').slice(0, 6).map(x => x.n);

    const avail = S.board.filter(x =>
      !mine.has(x.k + '|' + x.p) && !isGone(x));

    /* A second TE can only ever start in FLEX, competing with an RB/WR who
     * would otherwise hold that slot. Mock 4 took McBride AND Bowers in the
     * first three rounds and went into round 4 with no running back, because
     * "top-6 TE" alone was too easy a gate. Require a clear margin over the
     * best flex-eligible alternative instead of a bare ranking. */
    const bestFlexAlt = Math.max(...avail
      .filter(x => x.p === 'RB' || x.p === 'WR')
      .map(x => x.v), -Infinity);
    /* Shared context for te2Ok, so the queue planner enforces the same rule
     * this ranking does. */
    const curPick = S.cfg.myNextPick || rnd * (S.cfg.teams || 10);
    const top6TeFell = S.board.some(x =>
      x.p === 'TE' && !isGone(x) && !mine.has(x.k + '|' + x.p)
      && te6.includes(x.n) && x.a != null && (curPick - x.a) >= S.cfg.te2FallPicks);
    S.ctx = { te6, bestFlexAlt, need, top6TeFell };

    const eligible = [];
    const blocked = [];
    for (const p of avail) {
      if (guardrailOk(p, rnd, need, counts, picksLeft, true)) eligible.push(p);
      else if (blocked.length < 6) blocked.push(p.n + '(' + p.p + ')');
    }

    /* STASH-MUTE FALLBACK.
     *
     * Once every starter slot is filled, needsPosition() is false for
     * everyone, so the "at most one zero-role stash" rule silences the entire
     * board and rank() returns nothing. draftTop then reports "no candidates",
     * the clock runs out, and Yahoo takes the pick -- which is how autopick
     * armed in mock 7 at roster 9/15.
     *
     * The Python engine hit this exact bug on shallow boards and fixed it
     * with a labelled fallback; this port reintroduced it, then relaxed the
     * rule here when the list came back empty. draftTop had no such relief
     * and refused all 24 candidates at pick 86 of mock 13, so the rule is
     * gone from guardrailOk altogether: eligible is empty only when the
     * board truly is. */

    /* VONA -- value over NEXT AVAILABLE, not over a fixed replacement.
     *
     * VORP asks "how much better than a replacement-level player?". Draft day
     * asks a different question: "how much better than whoever I could still
     * get at this position at my NEXT turn?". On a flat position those are
     * wildly different numbers.
     *
     * Measured spread of each position's top 10 (mock 8):
     *   RB 82.3 pts (4.84/gm) · TE 67.5 (3.97) · QB 35.0 (2.06) · WR 33.6 (1.98)
     *
     * Every top-10 QB sits within 35 points of every other. VORP still handed
     * Mahomes +21.1, so the engine took him at pick 42 against an ADP of 102
     * -- a 60-pick reach to gain 0.72/game over Purdy, who was duly still
     * available at 99. The cost landed on the bench: four WRs at or below
     * replacement, because a mid-round pick went to a position where waiting
     * was nearly free.
     *
     * Within a position VORP differences ARE projection differences (shared
     * baseline), so VONA is simply the gap to the best player expected to
     * survive until our next turn. A flat position self-discounts; a scarce
     * one (RB, TE) does not. */
    const gap = S.cfg.teams || 10;               // average wait between turns
    const curPickNo = S.cfg.myNextPick || rnd * gap;
    const nextPickNo = curPickNo + gap;

    /* Expected best at each position on our next turn, and the second-best
     * on the board NOW. planner.py caps a same-position partner at
     * second_best_now, because the expectation does not know the candidate
     * himself was just taken -- that cap is exactly what stops the driver
     * assuming it can have BOTH elite tight ends. */
    const vonaBase = {}, secondBestNow = {};
    for (const pos of ['QB', 'RB', 'WR', 'TE', 'K', 'DEF']) {
      vonaBase[pos] = eBestNext(avail, pos, nextPickNo, rnd, curPickNo);
      const at = avail.filter(x => x.p === pos);
      secondBestNow[pos] = at.length > 1 ? at[1].v : 0;
    }

    /* ---- FAITHFUL PORT of tracker.recommendations() ----
     *
     * A parity harness (scripts/engine_parity.py) replayed identical board
     * states through both engines and found they agreed on the top pick only
     * 25% of the time. The driver was not a port, it was a different
     * algorithm wearing the same board. Four substantive divergences, now
     * corrected:
     *
     *   1. Python builds ONE candidate per position (best of the top 3 there),
     *      then ranks positions. The driver ranked all ~240 players directly.
     *   2. Python scores by the POSITION's urgency, not a per-player value.
     *   3. Python applies need weighting ONLY as the planner's 0.6 damp on a
     *      position that fills no slot. The driver's flat +12/+60 bonuses were
     *      an invention that distorted the order.
     *   4. Python breaks near-ties (within 2.0 VORP of the position's top
     *      candidate) by adp_delta, and from round 8 sorts the position by
     *      upside-boosted VORP before truncating. The driver did neither.
     */
    const POS_ORDER = ['RB', 'WR', 'TE', 'QB', 'K', 'DEF'];
    const byPos = {};
    for (const p of eligible) (byPos[p.p] = byPos[p.p] || []).push(p);

    const scored = [];
    for (const pos of POS_ORDER) {
      let rem = byPos[pos];
      if (!rem || !rem.length) continue;
      // v2 item 1.5: from upside_from_round, rank the position on an
      // upside-boosted proxy BEFORE truncating, so a gated player ranked 4th
      // by median can still surface.
      if (rnd >= S.cfg.upsideFromRound) {
        rem = rem.slice().sort((a, b) =>
          -( (a.v || 0) * (a.u ? S.cfg.upsideMult : 1) )
          + ( (b.v || 0) * (b.u ? S.cfg.upsideMult : 1) ));
      }
      const pool = rem.slice(0, 3);
      const anchor = pool[0];
      let best = anchor;
      for (const q of pool.slice(1)) {
        if (Math.abs((anchor.v || 0) - (q.v || 0)) <= 2.0
            && (q.d === undefined ? -999 : q.d) > (best.d === undefined ? -999 : best.d)) {
          best = q;
        }
      }
      const urgency = (rem[0].v || 0) - (vonaBase[pos] || 0);  // unclipped, as Python
      scored.push({
        p: best,
        s: urgency + 0.001 * (best.v || 0),   // stable ordering, as in Python
        fills: needsPosition(need, pos),
      });
    }
    scored.sort((a, b) => b.s - a.s);
    for (const x of scored) x.p._vona = Math.round(x.s * 10) / 10;


    /* TWO-PICK JOINT PLANNER (port of planner.py).
     *
     * Greedy urgency "won the pick and lost the round at #26/#47" in the real
     * Omnibeta draft, and cost this driver slot 9 of the replay sweep: it
     * took one elite TE when taking both was worth more, because it never
     * asked what PAIR of picks maximises value.
     *
     * pair(c) = need-weighted VORP(c now) + best partner expected at our next
     * turn, where a same-position partner is capped at second-best-now. */
    function needsAfter(taken) {
      const out = Object.assign({}, need);
      if ((out[taken] || 0) > 0) out[taken] -= 1;
      else if (FLEX_OK[taken] && (out.FLEX || 0) > 0) out.FLEX -= 1;
      return out;
    }
    function partnerValue(posTaken, countsAfter) {
      const after = needsAfter(posTaken);
      let bestV = 0, bestP = null;
      for (const pos2 of ['QB', 'RB', 'WR', 'TE', 'K', 'DEF']) {
        if (!posAllowed(pos2, rnd + 1, countsAfter, picksLeft - 1, true)) continue;
        let e = vonaBase[pos2] || 0;
        if (pos2 === posTaken) e = Math.min(e, secondBestNow[pos2] || 0);
        const v = needsPosition(after, pos2) ? e : e * NEED_DAMP;
        if (v > bestV) { bestV = v; bestP = pos2; }
      }
      return { v: bestV, pos: bestP };
    }
    for (const x of scored) {
      const cAfter = Object.assign({}, counts);
      cAfter[x.p.p] = (cAfter[x.p.p] || 0) + 1;
      const partner = partnerValue(x.p.p, cAfter);
      const own = x.p.v * (needsPosition(need, x.p.p) ? 1 : NEED_DAMP);
      x.pair = own + partner.v;
      x.partner = partner.pos;
    }
    scored.sort((a, b) => (b.pair - a.pair) || (b.s - a.s));

    return {
      round: rnd, picksLeft, counts, need,
      openStarters: ['QB','RB','WR','TE','FLEX','K','DEF'].reduce((a,k)=>a+(need[k]||0),0),
      top: scored.slice(0, 20).map(x => ({
        n: x.p.n, p: x.p.p, t: x.p.t, v: x.p.v, vona: x.p._vona,
        pair: Math.round((x.pair || 0) * 10) / 10, partner: x.partner,
        s: Math.round(x.s), fills: x.fills, st: x.p.s,
      })),
      vonaBase, secondBestNow,
      blockedSample: blocked,
      availCount: avail.length,
      goneCount: S.gone.size,
    };
  }

  /* ---------------- actuation ---------------- */

  /* The right panel has Queue / Players / Board tabs. On load it can be on
   * Queue, where a search matches no player rows at all. Mock 2 (2026-08-31)
   * failed exactly here: every findRow returned null, the code read that as
   * "drafted" and marked 36 elite players gone, then burned the 60s clock --
   * which is what armed autopick. Always assert the tab before searching. */
  function ensurePlayersTab() {
    const tab = [...document.querySelectorAll('button')]
      .find(b => b.textContent.trim() === 'Players');
    if (tab) { tab.click(); return true; }
    return false;
  }

  /* A row's controls.
   *
   * THE BIG ONE (found by screenshotting mock 4 while on the clock): Yahoo
   * re-renders every player row the moment it is your turn, replacing the
   * star with an explicit "Draft" button. Keying only on the star meant that
   * during our own turn -- the one moment that matters -- no row was ever
   * recognised. tableLive() then reported a dead UI and every pick aborted.
   * That single mistake explains the on-clock failures in mocks 2, 3 AND 4.
   *
   * So: a row is a player row if it carries EITHER control. */
  function starButton(row) {
    return [...row.querySelectorAll('button')]
      .find(b => !b.textContent.trim() && b.querySelector('svg')) || null;
  }
  function draftButton(row) {
    return [...row.querySelectorAll('button')]
      .find(b => /^Draft$/i.test(b.textContent.replace(/\s+/g, ' ').trim())) || null;
  }
  function isPlayerRow(row) {
    return !!(starButton(row) || draftButton(row));
  }

  /* Is the player table actually rendering rows? Used to distinguish "this
   * player is drafted" from "the table is not up", so a UI problem can never
   * again be recorded as league-wide unavailability. */
  function tableLive() {
    return [...document.querySelectorAll('div,li,tr')].some(e => {
      const x = (e.innerText || '').replace(/\s+/g, ' ');
      return x.length < 260 && /Bye \d+/.test(x) && isPlayerRow(e);
    });
  }

  function searchBox() {
    return document.querySelector('input[type="search"], input[placeholder*="earch"]');
  }
  function setSearch(v) {
    const el = searchBox();
    if (!el) return false;
    const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
    setter.call(el, v);
    el.dispatchEvent(new Event('input', { bubbles: true }));
    return true;
  }
  const sleep = ms => new Promise(r => setTimeout(r, ms));

  /* Yahoo and the board spell teams differently (SFO/SF, JAC/Jax, GBP/GB).
   * Both sides normalise here so the team check is meaningful. */
  const TEAM_ALIAS = {
    GBP: 'GB', GNB: 'GB', JAC: 'JAX', KCC: 'KC', LVR: 'LV', OAK: 'LV',
    NEP: 'NE', NWE: 'NE', NOS: 'NO', NOR: 'NO', SFO: 'SF', TBB: 'TB',
    TAM: 'TB', ARZ: 'ARI', BLT: 'BAL', CLV: 'CLE', HST: 'HOU', WSH: 'WAS',
  };
  function normTeam(t) {
    const s = (t || '').toUpperCase().replace(/[^A-Z]/g, '');
    return TEAM_ALIAS[s] || s;
  }

  /* Pull the ADP Yahoo prints in each row ("ADP: 46.4"), used to tell apart
   * two players who share an initial, surname, position AND team. */
  function rowAdp(text) {
    const m = text.match(/ADP:\s*([\d.]+)/);
    return m ? parseFloat(m[1]) : null;
  }

  /* Decide whether a rendered row really is this board entry.
   *
   * Pure, and tested. Mock 2 queued Brian Robinson Jr. (ATL RB, ADP 119.6,
   * VORP -72) believing it was Bijan Robinson (ATL RB, ADP 3, VORP +92):
   * identical initial, surname, position and team. The comment above the old
   * findRow claimed it checked team; the code never did, which also let
   * "J. Taylor" match a Jacksonville back instead of Jonathan Taylor of
   * Indianapolis. Name+position is not an identity. */
  /* Team defenses have no first name.
   *
   * The board calls them "Houston Texans", which keys to "h texans", so the
   * matcher looked for "H. Texans". Yahoo renders the row as plain
   * "Texans DEF Bye 8" -- no initial -- so NO defense could ever match. The
   * driver was structurally incapable of drafting one: mock 6 finished with
   * an empty DEF slot and Yahoo's fallback padding the end with a SECOND
   * kicker and a third TE. Match defenses on the nickname alone. */
  function defNickname(name) {
    const parts = (name || '').trim().split(/\s+/);
    return parts[parts.length - 1] || '';
  }

  /* What to type into the player search for this entry. */
  function searchTerm(entry) {
    return entry.p === 'DEF' ? defNickname(entry.n) : entry.k.slice(2);
  }

  function rowMatches(entry, text) {
    if (!/Bye \d+/.test(text)) return false;
    if (entry.p === 'DEF') {
      if (!/\bDEF\b/.test(text)) return false;
      return new RegExp('\\b' + defNickname(entry.n) + '\\b', 'i').test(text);
    }
    const initial = entry.k[0];
    const last = entry.k.slice(2);
    if (!new RegExp('\\b' + initial + '\\.\\s?[A-Za-z\'\\-]*' + last + '\\b', 'i').test(text)) return false;
    if (!new RegExp('\\b' + entry.p + '\\b').test(text)) return false;
    if (entry.t) {
      const want = normTeam(entry.t);
      const seen = (text.match(/\b([A-Za-z]{2,3})\b(?=\s+Bye)/) || [])[1];
      if (seen && normTeam(seen) !== want) return false;
    }
    /* ADP guard for same-name-same-team collisions.
     *
     * For a COLLIDING entry (another board row shares initial+surname+
     * position+team) ADP is the only thing that tells them apart, so an
     * unreadable ADP must REFUSE the row, not wave it through. Mock 7 drafted
     * Brian Robinson Jr. (grade D) instead of Bijan because the old guard was
     * written `if (seen != null)` and Yahoo had printed no ADP on that row --
     * the check silently skipped itself on exactly the rows it existed for.
     * Refusing costs one pick to a safe alternative; guessing wrong costs the
     * whole slot. */
    const colliding = S.collisions && S.collisions.has(entry.k + '|' + entry.p + '|' + normTeam(entry.t));
    const seen = rowAdp(text);
    if (colliding) {
      if (entry.a == null || seen == null) return false;
      return Math.abs(seen - entry.a) <= Math.max(25, entry.a * 0.5);
    }
    if (entry.a != null && seen != null
        && Math.abs(seen - entry.a) > Math.max(25, entry.a * 0.5)) return false;
    return true;
  }

  /* The length cap exists only to skip page-sized containers; the smallest
   * element that matches AND carries a star/Draft button is the row. It was
   * 260, tuned to the compact layout. Mock 11 (2026-09-01) opened in Yahoo's
   * EXPANDED stats layout, where a row's text runs to ~400 chars, so no row
   * ever passed, every recommended player was recorded "gone" (other rows
   * were visibly rendering), and the driver drafted four tight ends off the
   * unfiltered tail of the plan. */
  const ROW_TEXT_CAP = 1500;
  function findRow(entry) {
    const rows = [...document.querySelectorAll('div,li,tr')].filter(e => {
      const x = (e.innerText || '').replace(/\s+/g, ' ');
      if (x.length > ROW_TEXT_CAP) return false;
      if (!rowMatches(entry, x)) return false;
      return isPlayerRow(e);      // star OR Draft button; see isPlayerRow
    }).sort((a, b) => (a.innerText || '').length - (b.innerText || '').length);
    return rows[0] || null;
  }

  /* Why did a lookup miss, given the search filter is still applied?
   *
   * tableLive() alone is not enough: while a query is active the table shows
   * only matches, so a genuinely drafted player yields an empty view and
   * looks identical to a dead UI. Mock 3 aborted a whole pick that way.
   * Resolve it by clearing the filter and re-checking. */
  async function diagnoseMiss() {
    if (tableLive()) return 'norow';    // other rows visible -> player is gone
    setSearch('');
    await sleep(600);
    return tableLive() ? 'norow' : 'uinotready';
  }

  async function starPlayer(entry) {
    ensurePlayersTab();
    if (!setSearch(searchTerm(entry))) return 'nosearch';
    await sleep(700);
    const row = findRow(entry);
    if (!row) return await diagnoseMiss();
    const star = [...row.querySelectorAll('button')].find(b => !b.textContent.trim() && b.querySelector('svg'));
    if (!star) return 'nostar';
    star.click();
    await sleep(350);
    return 'ok';
  }

  function queuePanel() {
    return [...document.querySelectorAll('div')]
      .filter(e => /Autodraft will pick/i.test(e.innerText || '') && (e.innerText || '').length < 2000)
      .sort((a, b) => (b.innerText || '').length - (a.innerText || '').length)[0] || null;
  }

  /* Queue rows paired with their remove control (the same star, toggled). */
  function queueRows() {
    const qp = queuePanel();
    if (!qp) return [];
    const out = [];
    const seen = new Set();
    for (const e of qp.querySelectorAll('div,li')) {
      const x = (e.innerText || '').replace(/\s+/g, ' ').trim();
      if (x.length > 140) continue;
      /* Tolerate a leading "Draft" label: on our turn Yahoo prefixes every
       * queue row with its own Draft button, which made the old anchored
       * regex match nothing and report an EMPTY queue while five players
       * were plainly sitting in it (mock 4 screenshot). */
      /* Two shapes: "J. Gibbs RB Det ..." and, for a team defense with no
       * first name, "Texans DEF Bye 8 ...". Missing the second shape made
       * queued defenses INVISIBLE, so reconcileStarred concluded a rival had
       * taken them and marked them gone -- starving the DEF slot even after
       * defenses became matchable at all. Same identity assumption, second
       * hiding place. */
      const m = x.match(/(?:^|^Draft\s+)([A-Z]\.\s?[A-Za-z'\-\.]+)\s+(?:Q|IR|IR-R|O|D|SUSP|PUP|CEL|NA)?\s*(QB|RB|WR|TE|K|DEF)\b/)
        || x.match(/(?:^|^Draft\s+)([A-Z][A-Za-z]+(?:\s[A-Z][A-Za-z]+)*)\s+(DEF)\b/);
      if (!m) continue;
      const btn = starButton(e);
      if (!btn) continue;
      const key = idKey(m[1], m[2]) + '|' + m[2];
      if (seen.has(key)) continue;
      seen.add(key);
      out.push({ el: e, btn, key, pos: m[2], text: x });
    }
    return out;
  }

  /* Remove queued players the guardrails no longer allow.
   *
   * syncQueue only ever ADDED, so the queue drifted out of step with the
   * roster. Mock 3 sat with Mahomes AND Hurts queued in round 5: legal while
   * QB count was 0, but the moment the first landed the second became an
   * illegal QB2 that autopick would happily take -- the mock 1 mistake
   * reappearing through a different door. Re-ranking is only honest if it can
   * also take things off. */
  async function pruneQueue() {
    const r = rank();
    if (r.err) return { err: r.err };
    /* Legality, not top-N membership.
     *
     * Keying off r.top (the best 20 by score) made prune churn: a player who
     * merely slipped out of the top 20 was un-starred and then re-starred by
     * the fill pass in the same cycle. Every one of those is a wasted click
     * on a TOGGLE, which risks leaving the queue in the opposite state to
     * what we think. Only remove what the guardrails actually forbid. */
    const legal = new Set();
    for (const p of S.board) {
      if (guardrailOk(p, r.round, r.need, r.counts, r.picksLeft, false)) {
        legal.add(p.k + '|' + p.p);
      }
    }
    const removed = [];
    for (const row of queueRows()) {
      if (legal.has(row.key)) continue;
      row.btn.click();
      removed.push(row.text.slice(0, 28));
      S.starred.forEach(id => {
        const [n, p] = id.split('|');
        if (idKey(n, p) + '|' + p === row.key) S.starred.delete(id);
      });
      await sleep(350);
    }
    return { removed };
  }

  function queueNames() {
    ensureLeftTab('Queue');           // the other left-panel tab; see parsePicksPanel
    const qp = [...document.querySelectorAll('div')]
      .filter(e => /Autodraft will pick/i.test(e.innerText || '') && (e.innerText || '').length < 2000)
      .sort((a, b) => (b.innerText || '').length - (a.innerText || '').length)[0];
    if (!qp) return [];
    const t = (qp.innerText || '').replace(/\s+/g, ' ');
    const re = /([A-Z]\.\s?[A-Za-z'\-\.]+)\s+(?:Q|IR|O|D|SUSP|PUP|CEL)?\s*(QB|RB|WR|TE|K|DEF)\s/g;
    const out = []; let m;
    while ((m = re.exec(t))) out.push(keyAbbr(m[1]) + '|' + m[2]);
    return out;
  }

  /* Rebuild the queue against the CURRENT roster every cycle.
   *
   * This is the fix for the stale-queue bug class. We do not append to what
   * is already queued -- we re-rank from scratch, so a position that filled
   * since last cycle stops being wanted. (The 3rd-QB mistake was exactly an
   * append against a roster snapshot that had moved on.)
   *
   * Walks DOWN the ranked list, not just the top N, so unavailable players
   * are skipped rather than leaving the queue short. */
  /* Reconcile our "already starred" memo against reality.
   *
   * S.starred exists so we never re-click a star and toggle a player back OUT
   * of the queue. But an entry that has left the queue without joining our
   * roster was drafted by somebody else, and leaving it in the memo means
   * syncQueue skips it forever and stops refilling. Mock 3 drained 5 -> 2 ->
   * 1 that way, and once the queue ran dry Yahoo's own fallback list took
   * over and handed us a THIRD tight end -- a guardrail violation produced
   * entirely by starvation. */
  function reconcileStarredWith(queueKeys, rosterKeys) {
    const inQueue = new Set(queueKeys);
    const mine = new Set(rosterKeys);
    const dropped = [];
    for (const id of [...S.starred]) {
      const i = id.lastIndexOf('|');
      const key = idKey(id.slice(0, i), id.slice(i + 1)) + '|' + id.slice(i + 1);
      if (inQueue.has(key) || mine.has(key)) continue;
      S.starred.delete(id);
      const entry = S.board.find(b => b.n + '|' + b.p === id);
      if (entry) markGone(entry);          // someone else took them
      dropped.push(id);
    }
    return dropped;
  }

  function reconcileStarred() {
    const ros = myRoster();
    return reconcileStarredWith(
      queueNames(),
      (ros ? ros.players : []).map(p => p.k + '|' + p.pos)
    );
  }

  async function syncQueue() {
    S.cfg.myNextPick = myNextPick();       // for the queue's ADP filter
    reconcileStarred();                    // free up slots taken by others
    const pruned = await pruneQueue();     // drop what is no longer legal
    const r = rank();
    if (r.err) return r;
    const have = queueNames();
    const results = [];
    let depth = have.length;

    /* The queue is a PLAN for the next N picks, not a top-N list.
     *
     * Filling it with the highest scorers clusters by position: mock 4 queued
     * FIVE quarterbacks in round 6. Only one was legally draftable (QB2 is
     * gated until round 10), so the moment one landed the other four were
     * pruned and the queue collapsed -- starvation again, by a new route.
     *
     * So each candidate is checked against a roster that already contains
     * everything queued ahead of it. After one QB is planned, the simulated
     * roster has a QB and the gate blocks the rest, which diversifies the
     * queue for free instead of by an arbitrary per-position cap. */
    const simCounts = Object.assign({}, r.counts);
    let simHave = S.cfg.rounds - r.picksLeft;
    for (const key of have) {          // already-queued players count too
      const pos = key.slice(key.lastIndexOf('|') + 1);
      simCounts[pos] = (simCounts[pos] || 0) + 1;
      simHave++;
    }

    for (const cand of r.top) {
      if (depth >= S.cfg.queueDepth) break;
      const entry = S.board.find(b => b.n === cand.n && b.p === cand.p);
      if (!entry) continue;
      const simNeed = needsMap(simCounts);
      const simRound = simHave + 1;
      const simLeft = S.cfg.rounds - simHave;
      if (!guardrailOk(entry, simRound, simNeed, simCounts, simLeft, false)) continue;
      /* Do not queue players who will obviously be gone -- but ONLY while the
       * queue is otherwise healthy.
       *
       * The filter was added because from slot 7 the driver queued the
       * consensus top 6 in round 1, all six went in picks 1-6, and Yahoo's
       * fallback took the pick. But applied unconditionally it starves the
       * late rounds: by round 12 every player still on the board has an ADP
       * earlier than the current pick -- being a faller is precisely why they
       * are still available. Mock 7 sat at queue depth 1 for four rounds
       * because of this, with K and DEF unfilled.
       *
       * markGone() already removes players who really are drafted, so this is
       * only a preference. Drop it the moment the queue is thin. */
      const queueThin = depth < 3;
      if (!queueThin && entry.a != null && S.cfg.myNextPick
          && entry.a < S.cfg.myNextPick - 40) continue;
      const id = cand.n + '|' + cand.p;
      /* The star is a TOGGLE. Re-clicking one we already queued REMOVES the
       * player. queueNames() cannot always see the whole queue (Yahoo caps
       * the visible list), so trusting it alone made the driver re-star the
       * 5th entry every cycle, flipping them in and out. Track our own
       * clicks instead. */
      if (have.includes(idKey(cand.n, cand.p) + '|' + cand.p) || S.starred.has(id)) continue;
      const res = await starPlayer(entry);
      if (res === 'ok') {
        depth++;
        S.starred.add(id);
        simCounts[cand.p] = (simCounts[cand.p] || 0) + 1;   // planned
        simHave++;
        results.push(cand.n + ':ok');
      }
      else if (res === 'norow') {
        markGone(entry); results.push(cand.n + ':' + res + '->gone');
      } else if (res === 'nostar') {
        /* The row IS there (findRow saw a star or a Draft button) but the
         * star specifically is not -- Yahoo swaps it for "Draft" on our turn.
         * That is a UI state, not a drafted player; recording it as gone was
         * one more way a present player left the plan (mock 11). */
        results.push(cand.n + ':' + res);
      } else {
        results.push(cand.n + ':' + res);   // UI not ready: never mark gone
        break;
      }
    }
    setSearch('');
    return { round: r.round, picksLeft: r.picksLeft, counts: r.counts,
             need: r.need, queued: results, pruned: (pruned.removed || []),
             queueNow: queueNames(),
             top: r.top.slice(0, 5).map(x => x.n + '(' + x.p + ' ' + x.v + ')') };
  }

  /* Try to click the pick ourselves.
   *
   * Best-effort ONLY. The queue is the guaranteed actuator (see run()): its
   * head is kept equal to the engine's top choice, so whoever pulls the
   * trigger, the pick is the engine's. draftTop just gets there sooner.
   *
   * Bounded to a few candidates: mock 3 spent the entire 60s clock walking 20
   * of them, which is what armed autopick in the first place. */
  /* ---------------- the client's own actions (design 2026-09-02, layer 2b) ------
   *
   * The Draft button calls a Redux thunk, makePick(playerId), which sends one
   * pipe-delimited frame on the client's socket: "0|league|manager|pickNo|
   * playerId" (react-draft-client bundle, sendMakePick). The Autodraft toggle
   * is setAwayStatus(bool) -> "5"/"6". The top-level connected component's
   * props carry those thunks as bound dispatchers, reachable by walking the
   * React tree from the store's provider -- the same walk findStore does.
   *
   * Calling makePick ourselves runs Yahoo's own code path end to end, minus
   * the analytics beacon: no search box, no row, no button, no confirm
   * dialog. The click path stays as the fallback, and the store still
   * verifies every pick (pickLandedStore) whichever path made it. */
  function clientActions(force) {
    const WANT = ['makePick', 'setAwayStatus', 'addToQueue', 'setCurrentPlayerId'];
    // a registry that has anything is reused for a minute; a partial one is
    // still a registry (the test hook hands over one action at a time, and a
    // Yahoo deploy could rename one prop without the others)
    if (!force && S.actions && Object.keys(S.actions).length
        && S.actionsAt && Date.now() - S.actionsAt < 60000) return S.actions;
    // a walk that found NOTHING is remembered too, briefly: keepAlive runs
    // every cycle, and a room without the props (click-path fallback, or a
    // Yahoo rename) must not pay a 200k-fiber walk once a second
    if (!force && !S.actions && S.actionsMissAt && Date.now() - S.actionsMissAt < 10000) return null;
    const found = {};
    const queue = [];
    for (const el of document.querySelectorAll('body, body *')) {
      for (const k of Object.keys(el)) {
        if (k.startsWith('__reactContainer$')) queue.push(el[k]);
      }
      if (el._reactRootContainer && el._reactRootContainer._internalRoot) {
        queue.push(el._reactRootContainer._internalRoot.current);
      }
      if (queue.length) break;
    }
    const seen = new Set();
    let n = 0;
    while (queue.length && n < 200000 && WANT.some(k => !found[k])) {
      const f = queue.shift();
      if (!f || seen.has(f)) continue;
      seen.add(f); n++;
      const p = f.memoizedProps;
      if (p && typeof p === 'object') {
        for (const k of WANT) if (!found[k] && typeof p[k] === 'function') found[k] = p[k];
      }
      if (f.child) queue.push(f.child);
      if (f.sibling) queue.push(f.sibling);
    }
    S.actions = Object.keys(found).length ? found : null;
    S.actionsAt = Date.now();
    S.actionsMissAt = S.actions ? null : Date.now();
    return S.actions;
  }

  /* Yahoo's player id for a board candidate, from the store's player table
   * (exact ids, no name matching beyond the same key the feed uses). */
  function playerIdFor(cand) {
    const store = findStore();
    let s;
    try { s = store && store.getState(); } catch (e) { return null; }
    const byId = (s && s.players && s.players.byId) || {};
    // full names first: the store has them, so Bijan and Brian Robinson (same
    // initial, surname, position AND team) resolve without a tie-break;
    // the first-initial key is the fallback for spelling variants
    const full = (n) => String(n || '').toLowerCase().replace(/[.'’]/g, '').replace(/[-/]/g, ' ')
      .replace(/\s+(jr|sr|ii|iii|iv|v)$/, '').replace(/\s+/g, ' ').trim();
    const wantFull = full(cand.n);
    const want = idKey(cand.n, cand.p);
    const exact = [], loose = [];
    for (const [pid, p] of Object.entries(byId)) {
      const pos = p.primary_pos || p.display_pos || '';
      if (pos !== cand.p) continue;
      const name = ((p.fname || '') + ' ' + (p.lname || '')).trim();
      const rec = { pid, team: p.team_abbr || '' };
      if (full(name) === wantFull) exact.push(rec);
      else if (idKey(name, pos) === want) loose.push(rec);
    }
    for (const hits of [exact, loose]) {
      if (hits.length === 1) return hits[0].pid;
      if (hits.length > 1 && cand.t) {
        const t = hits.filter(h => normTeam(h.team) === normTeam(cand.t));
        if (t.length === 1) return t[0].pid;
      }
      if (hits.length > 1) return null;   // ambiguous: the click path handles it
    }
    return null;
  }

  /* Make the pick through the client's own makePick and wait for the store
   * to record it at OUR pick number. Returns {status: 'landed'|'notours'|
   * 'timeout'|'noaction'|'noid'|'error', ...}. Never claims success without
   * the store's word. */
  async function pickViaAction(cand, waitMs) {
    const acts = clientActions();
    if (!acts || typeof acts.makePick !== 'function') return { status: 'noaction' };
    const pid = playerIdFor(cand);
    if (!pid) return { status: 'noid' };
    const turn = S.planPick != null ? S.planPick : (storeState() || {}).current_pick;
    try { acts.makePick(pid); } catch (e) { return { status: 'error', why: String(e).slice(0, 120) }; }
    const t0 = Date.now();
    while (Date.now() - t0 < (waitMs || 3000)) {
      await sleep(250);
      const landed = pickLandedStore(cand, turn);
      if (landed === true) return { status: 'landed', pid, ms: Date.now() - t0 };
      if (landed === false) return { status: 'notours', pid, landed: lastOwnPickName() };
    }
    return { status: 'timeout', pid };
  }

  /* Proof-of-engine record for every pick: the engine's stated reason for
   * the player it chose, and who the best AVAILABLE player by raw projection
   * was at that moment. When the two differ, the pick log shows the engine
   * doing something projections alone would not (slot value, urgency,
   * survival odds, bench insurance), with its reason attached. */
  function bestByProjection() {
    const snap = storeState();
    const gone = new Set(snap ? snap.drafted.map(d => idKey(d.name, d.pos)) : []);
    let best = null;
    for (const b of S.board) {
      if (b.p === 'K' || b.p === 'DEF') continue;
      if (S.gone.has(b.k + '|' + b.p) || gone.has(idKey(b.n, b.p))) continue;
      if (!best || (b.j || 0) > (best.j || 0)) best = b;
    }
    return best ? { n: best.n, p: best.p, proj: best.j, vorp: best.v } : null;
  }

  /* The record of one pick, for the narration and the end-of-draft trail.
   * `top` is the ranked list the pick was CHOSEN from (draftTop's rank()
   * result), so passed_on is the decision-time list, not a re-rank of the
   * post-pick state. Every record is retained in S.records for trail(). */
  function pickRecord(cand, extra, top) {
    const b = S.board.find(x => x.n === cand.n && x.p === cand.p) || {};
    const alt = bestByProjection();
    const passed = (top || []).filter(x => !(x.n === cand.n && x.p === cand.p)).slice(0, 3)
      .map(x => ({ n: x.n, p: x.p, v: x.v, why: (x.why || '').slice(0, 120),
                   s: x.s == null ? null : x.s, e: x.e == null ? null : x.e }));
    const rec = Object.assign({ drafted: cand.n, pos: cand.p, vorp: cand.v, proj: b.j,
                                why: (cand.why || '').slice(0, 220),
                                s: cand.s == null ? null : cand.s, sr: cand.sr == null ? null : cand.sr,
                                e: cand.e == null ? null : cand.e,
                                top_proj_available: alt,
                                took_top_projection: !!(alt && alt.n === cand.n),
                                passed_on: passed,
                                pick_no: S.planPick != null ? S.planPick : null }, extra);
    S.records.push(rec);
    return rec;
  }

  async function draftTop(maxTries) {
    const r = rank();
    if (r.err || !r.top.length) return { err: r.err || 'no candidates' };
    const before = rosterCount();
    ensurePlayersTab();
    await sleep(300);
    const attempted = [];
    let tries = 0;
    /* Local guardrails on every candidate, whatever list it came from. The
     * plan's depth tail used to be unguarded (mock 11: TE3, TE4, a DEF in
     * round 3), and a stale plan can name a position we have since filled.
     * The engine remains the ranking; this only refuses what the roster
     * makes illegal. Same predicate syncQueue applies. */
    const need = r.need || {}, counts = r.counts || {};
    const picksLeft = r.picksLeft != null ? r.picksLeft : S.cfg.rounds;
    const rnd = r.round || 1;
    const top6TeFell = !!(S.ctx && S.ctx.top6TeFell);
    for (const cand of r.top) {
      if (tries >= (maxTries || 3)) break;
      const entry = S.board.find(b => b.n === cand.n && b.p === cand.p);
      if (!entry) continue;
      if (!guardrailOk(entry, rnd, need, counts, picksLeft, top6TeFell)) {
        attempted.push(cand.n + ':guardrail');
        continue;
      }
      /* First choice: the client's own makePick (no DOM). The store confirms
       * or denies within a few hundred ms. 'notours' means someone else's
       * pick landed at our number (autopick beat us) -- stop, do not click.
       * 'timeout' / 'noaction' / 'noid' fall through to the click path for
       * the same candidate; a late-landing action then shows up in the
       * store check below as landed, and a second click is rejected by
       * Yahoo as "not the current pick", harmlessly. */
      if (S.cfg.useActions !== false) {
        tries++;
        const via = await pickViaAction(cand);
        if (via.status === 'landed') {
          return pickRecord(cand, { verified: 'store', via: 'action', ms: via.ms }, r.top);
        }
        if (via.status === 'notours') {
          attempted.push(cand.n + ':notours(' + (via.landed || '?') + ')');
          return { err: 'pick-made-by-other-means', attempted, landed: via.landed };
        }
        attempted.push(cand.n + ':action-' + via.status + (via.why ? '(' + via.why + ')' : ''));
        tries--;   // the click attempt below is the one that counts
      }
      if (!setSearch(searchTerm(entry))) continue;
      tries++;
      await sleep(700);
      const row = findRow(entry);
      if (!row) {
        const why = await diagnoseMiss();
        if (why === 'uinotready') return { err: 'ui-not-ready', attempted };
        markGone(entry);
        continue;
      }
      /* Prefer the row's OWN Draft button. Hunting the document for a
       * /^Draft/ button matched the nav tab named "Draft" (mock 1) and, when
       * it did not, clicked something unrelated that silently no-opped
       * (mock 3's phantom "drafted Bijan Robinson"). The row's button is
       * unambiguous. */
      let pick = draftButton(row);
      if (!pick) {
        row.click();
        await sleep(600);
        pick = draftButton(row) || [...document.querySelectorAll('button')].filter(b => {
          const x = b.textContent.replace(/\s+/g, ' ').trim();
          return /^Draft Player$/i.test(x) && !b.disabled && !b.closest('[role=tablist]');
        })[0];
      }
      if (!pick || pick.disabled) { attempted.push(cand.n + ':nobtn'); continue; }
      pick.click();
      await sleep(1100);
      const conf = [...document.querySelectorAll('button')]
        .find(b => /^(Yes|Confirm|Draft Player)$/i.test(b.textContent.trim()) && !b.disabled);
      if (conf) { conf.click(); await sleep(900); }
      setSearch('');
      /* NEVER report a pick we cannot see on the roster. Mock 3 logged
       * "drafted Bijan Robinson" twice while the roster showed neither: the
       * click path silently no-opped and the queue was quietly making every
       * real pick. An unverified success hides the very failure we hunt. */
      await sleep(700);
      /* "The roster grew" is not "OUR click landed THIS player". At pick 135
       * of mock 13 Yahoo's autopick had already taken Cam Little the instant
       * the turn opened; our Seattle click was rejected ("not the current
       * pick") and the roster count still went up by one, so the log said
       * Seattle, verified. With the store readable, verify the pick itself. */
      const landed = pickLandedStore(cand);
      if (landed === false) {
        attempted.push(cand.n + ':notours(' + (lastOwnPickName() || '?') + ')');
        return { err: 'pick-made-by-other-means', attempted, landed: lastOwnPickName() };
      }
      const after = rosterCount();
      if (landed !== true && !(after && before && after.have > before.have)) {
        attempted.push(cand.n + ':noland');
        continue;
      }
      return pickRecord(cand, { verified: landed === true ? 'store' : 'roster-count', via: 'click' }, r.top);
    }
    return { err: 'no-verified-pick', attempted };
  }

  /* Did the store just record OUR pick of this candidate? true / false, or
   * null when the store cannot say (no store, or our newest pick predates
   * this turn). Pure given storeState(); tested through _setStore. */
  function pickLandedStore(cand, turn) {
    const snap = storeState();
    if (!snap || !snap.my_team) return null;
    const at = turn != null ? turn : S.planPick;      // the pick we were on the clock for
    if (at == null) return null;
    const ours = snap.drafted.find(d => d.mine && d.pick_no === at);
    if (!ours) return null;                            // not recorded yet
    return ours.pos === cand.p && idKey(ours.name, ours.pos) === idKey(cand.n, cand.p);
  }

  function lastOwnPickName() {
    const snap = storeState();
    const mine = snap ? snap.drafted.filter(d => d.mine) : [];
    return mine.length ? mine[mine.length - 1].name : null;
  }

  /* Yahoo tells us when it has taken the wheel. Once armed it drafts the
   * instant the turn opens, so racing it with clicks only wastes the clock --
   * and the clock expiring is what armed it. When armed, trust the queue. */
  function bannerSaysArmed() {
    return /put into autopick mode/i.test(document.body.innerText);
  }

  /* Store first: the banner is inert and outlives the disarm (mock 13), so
   * on its own it would stand the driver down for the rest of the draft. */
  function autopickArmed() {
    const snap = storeState();
    if (snap && snap.my_team) return snap.away_teams.includes(snap.my_team);
    return bannerSaysArmed();
  }

  /* Overall pick number of our next turn, read off the header ("You're up in
   * 2 Picks • Round 4, Pick 32" / "ROUND 1, PICK 7"). Feeds the queue's
   * ADP filter so we stop queueing players who cannot possibly last. */
  function myNextPick() {
    const t = document.body.innerText.replace(/\s+/g, ' ');
    const up = t.match(/up in (\d+) Picks?/i);
    const cur = t.match(/Round \d+,\s*Pick (\d+)/i);
    if (cur) return parseInt(cur[1], 10) + (up ? parseInt(up[1], 10) : 0);
    const mine = t.match(/YOUR TURN - (\d+)(?:ST|ND|RD|TH) PICK/i);
    return mine ? parseInt(mine[1], 10) : null;
  }

  /* Resident loop: this is what stops autopick from ever arming. */
  /* A HIDDEN TAB IS THROTTLED.
   *
   * Chrome clamps timers in a background tab to roughly one tick a minute,
   * which stalls this loop and, worse, stalls Yahoo's own countdown: a mock
   * waiting room read 08:21 while the server was actually at 04:15. A
   * throttled driver silently misses picks and lets autopick arm.
   *
   * There is no way to opt out from inside the page, so the loop reports it
   * loudly and keeps going -- externally driven calls (refreshPlan, draftTop)
   * are unaffected, so a supervised draft still works. For an unsupervised
   * one the draft tab has to stay visible. */
  function throttleRisk() {
    return typeof document.hidden === 'boolean' && document.hidden;
  }

  /* Do the driver's readings agree with each other? Pure enough to call from
   * outside as a preflight. Each check is a way mock 11 went wrong:
   *   header pick   -- if we cannot read where we are, we cannot judge a plan
   *   plan @pick    -- a plan computed for another pick is a plan for another
   *                    draft (the bridge pads from the header, so these should
   *                    match exactly whenever the header is readable)
   *   plan age      -- older than 20s means refreshPlan failed quietly
   *   gone set      -- 25+ "gone" between picks is the row lookup failing,
   *                    not 25 players vanishing; clear it and refuse this cycle
   */
  function gatesOk() {
    const why = [];
    const snap = storeState();
    const hdr = (snap && snap.current_pick) || currentPickNo();
    if (!hdr) why.push('current pick unreadable (no store, no header)');
    if (!S.plan || !S.plan.length) why.push('no plan');
    if (hdr && S.planPick != null && S.planPick !== hdr) {
      why.push('plan is for pick ' + S.planPick + ', header says ' + hdr);
    }
    if (S.planAt && Date.now() - S.planAt > 20000) why.push('plan stale (' + Math.round((Date.now() - S.planAt) / 1000) + 's)');
    /* Per cycle, not absolute: over a whole draft the plan legitimately names
     * many players who are then found drafted (it is padded from a header
     * pick number, so it cannot know), and each of those is a correct "gone".
     * What is NOT plausible is many in ONE cycle -- mock 11 marked 44 between
     * two of our picks because no row could match. */
    const added = S.gone.size - (S.goneAtGate || 0);
    if (added >= 12) {
      why.push('gone jumped by ' + added + ' since last gate -> cleared');
      S.gone = new Set();
    }
    S.goneAtGate = S.gone.size;
    return { ok: why.length === 0, why, headerPick: hdr, planPick: S.planPick, gone: S.gone.size, goneAdded: added };
  }

  /* In-room preflight (design 2026-09-01, layer 2): everything the loop will
   * rely on, checked before the clock matters, in one readable report. Any
   * `false` means do not arm the loop on that reading alone. */
  async function preflight() {
    const out = {};
    const snap = storeState();
    out.store = !!snap;
    out.my_team = snap ? snap.my_team : null;
    out.store_picks = snap ? snap.drafted.length : null;
    out.store_current_pick = snap ? snap.current_pick : null;
    out.header_pick = currentPickNo();
    const ros = myRoster();
    out.roster_panel = !!ros;
    out.roster_have = ros ? ros.players.length : null;
    out.picks_panel = parsePicksPanel().length;
    out.table_live = tableLive();
    out.plan = await refreshPlan();
    out.gates = gatesOk();
    // can we find a row for the plan's first UNDRAFTED candidate? (Mock 16:
    // injected mid-round, the plan head had just been taken and preflight
    // reported the row lookup broken when it was the player who was gone.)
    const r = rank();
    const pfSnap = storeState();
    const pfGone = new Set(pfSnap ? pfSnap.drafted.map(d => idKey(d.name, d.pos)) : []);
    const first = r && r.top && (r.top.find(c => !pfGone.has(idKey(c.n, c.p))) || r.top[0]);
    if (first) {
      const entry = S.board.find(b => b.n === first.n && b.p === first.p);
      ensurePlayersTab();
      if (entry && setSearch(searchTerm(entry))) {
        await sleep(700);
        out.row_lookup = { player: first.n, found: !!findRow(entry) };
        setSearch('');
      } else {
        out.row_lookup = { player: first.n, found: null, why: 'no search box' };
      }
    }
    out.autopick_armed = autopickArmed();
    // the client's own actions (makePick / setAwayStatus): the no-DOM pick path
    const acts = clientActions(true);
    out.client_actions = acts ? Object.keys(acts) : [];
    if (first && acts && typeof acts.makePick === 'function') {
      out.player_id_lookup = { player: first.n, id: playerIdFor({ n: first.n, p: first.p, t: first.t }) };
    }
    out.ok = !!(out.store || (out.roster_panel && out.header_pick)) && !!(out.row_lookup && out.row_lookup.found !== false) && !out.autopick_armed;
    return out;
  }

  /* Yahoo marks a manager "away" after a stretch without user activity and
   * arms autopick for them -- mock 12 (2026-09-01) lost live control from
   * round 11 that way with the driver working perfectly, because programmatic
   * clicks are not the activity Yahoo counts. Two defences: fake the activity
   * every cycle, and if the store says we are away anyway (or the modal is
   * up), flip the Autodraft toggle back off and say so. */
  async function keepAlive() {
    try {
      const x = 200 + Math.floor(Math.random() * 400), y = 200 + Math.floor(Math.random() * 200);
      for (const type of ['mousemove', 'pointermove']) {
        document.dispatchEvent(new MouseEvent(type, { bubbles: true, clientX: x, clientY: y }));
      }
      document.dispatchEvent(new KeyboardEvent('keydown', { bubbles: true, key: 'Shift' }));
      document.dispatchEvent(new KeyboardEvent('keyup', { bubbles: true, key: 'Shift' }));
      window.dispatchEvent(new Event('focus'));
    } catch (e) { /* synthetic events are best effort */ }

    /* The store's away flag is the truth when we can read it. The page's
     * "put into autopick mode" notice is NOT: it is an inert banner that
     * stays up after autodraft is switched back off, and the Autodraft
     * control is a toggle. Acting on the banner, mock 13 (2026-09-02) clicked
     * that toggle every cycle -- off, on, off, on -- for two rounds, and two
     * of our picks went to Yahoo's autodraft while the flag happened to be
     * on. Without a store the banner is all we have, so then act on it at
     * most once per 30 s, and verify. */
    /* HEARTBEAT (mock 20, 2026-09-02). Yahoo's idle timer counts user
     * activity the client reports, not our synthetic events and not
     * makePick. On the click path our typing and clicking happened to count,
     * so `away` never flipped in 45-minute drafts; on the action path
     * nothing counts, and at 16 minutes Yahoo flagged us away and autopicked
     * pick 129 the instant the turn opened -- three seconds before keepAlive
     * saw the flag. Clearing after the fact is too late by construction, so
     * send Yahoo's own "not away" (setAwayStatus(false) -> "6|league|
     * manager") every few minutes whether or not the flag is up. */
    const hbEvery = (S.cfg.heartbeatSec != null ? S.cfg.heartbeatSec : 240) * 1000;
    if (S.lastHeartbeat == null) S.lastHeartbeat = Date.now();   // first beat one interval after start
    let acts = null;                       // looked up only when a beat is due (or the flag is up)
    if (Date.now() - S.lastHeartbeat >= hbEvery) {
      acts = clientActions();
      if (acts && typeof acts.setAwayStatus === 'function') {
        // stamp BEFORE the call: a thunk that throws must wait for the next
        // interval like one that worked, not retry every cycle and flood the log
        S.lastHeartbeat = Date.now();
        try { acts.setAwayStatus(false); note('heartbeat: setAwayStatus(false)'); }
        catch (e) { note('heartbeat threw (next in ' + (hbEvery / 1000) + 's): ' + String(e).slice(0, 80)); }
      }
    }

    const snap = storeState();
    const awayByStore = !!(snap && snap.my_team && snap.away_teams.includes(snap.my_team));
    const armed = snap ? awayByStore : autopickArmed();
    if (!armed) return { away: false };
    if (!snap && S.lastDisarm && Date.now() - S.lastDisarm < 30000) {
      return { away: true, toggled: false, why: 'banner only; disarm attempted <30s ago' };
    }
    // Disarm, first choice: the client's own setAwayStatus(false) -- the
    // exact thunk the Autodraft toggle dispatches ("6|league|manager"),
    // with no toggle to misread. Verified against the store; the click path
    // below only runs when the action is unavailable or did not stick.
    acts = acts || clientActions();
    if (acts && typeof acts.setAwayStatus === 'function') {
      try { acts.setAwayStatus(false); } catch (e) { note('setAwayStatus threw: ' + String(e).slice(0, 80)); }
      S.lastDisarm = Date.now();
      await sleep(800);
      const after = storeState();
      const stillAway = !!(after && after.my_team && after.away_teams.includes(after.my_team));
      note('AWAY detected (store=' + awayByStore + ') -> setAwayStatus(false); away now '
        + (after ? stillAway : 'unknown'));
      if (after && !stillAway) return { away: true, action: true, cleared: true };
    }
    // Disarm, fallback: the Queue panel carries an "Autodraft" toggle
    ensureLeftTab('Queue');
    await sleep(500);
    const toggle = [...document.querySelectorAll('button,[role=switch]')]
      .find(b => /^Autodraft$/i.test((b.textContent || '').trim()) || /autodraft/i.test(b.getAttribute('aria-label') || ''));
    if (toggle) {
      toggle.click();
      S.lastDisarm = Date.now();
      await sleep(600);
      const after = storeState();
      const stillAway = !!(after && after.my_team && after.away_teams.includes(after.my_team));
      note('AWAY/AUTOPICK detected (store=' + awayByStore + ', banner=' + bannerSaysArmed()
        + ') -> clicked Autodraft toggle; away now ' + (after ? stillAway : 'unknown'));
      if (after && stillAway && !awayByStore) {
        // we just armed it: undo at once rather than wait a cycle
        toggle.click();
        await sleep(600);
        note('toggle had ARMED autodraft -> clicked again');
      }
    } else {
      note('AWAY/AUTOPICK detected but no Autodraft toggle found');
    }
    // a "turn off" control inside the modal, if Yahoo offers one
    const off = [...document.querySelectorAll('button,a')].find(b => /turn off autopick/i.test(b.textContent || ''));
    if (off) { off.click(); await sleep(400); note('clicked "turn off autopick"'); }
    return { away: true, toggled: !!toggle, off: !!off };
  }

  async function run(maxSeconds) {
    if (S.running) return 'already running';
    S.running = true;
    const deadline = Date.now() + (maxSeconds || 3600) * 1000;
    note('driver start' + (throttleRisk()
      ? ' — WARNING: tab is hidden, Chrome throttles timers; keep it visible'
      : ''));
    let lastSync = 0;
    try {
      while (Date.now() < deadline) {
        const rc = rosterCount();
        if (rc && rc.have >= S.cfg.rounds) { note('roster full'); break; }
        if (/draft results|draft complete/i.test(document.title)) { note('draft over'); break; }

        if (onClock()) {
          await keepAlive();     // clear a fresh away flag BEFORE the pick attempt, not after
          await refreshPlan();   // zero-lag: ask the engine now
          /* CONSISTENCY GATES (design 2026-09-01). A layer may act only when
           * its readings agree; otherwise it does nothing and the queue /
           * Yahoo's own list catches the pick. Never a confident click on a
           * doubtful state -- mock 11's four tight ends were exactly that. */
          const gate = gatesOk();
          if (!gate.ok) {
            note('GATE FAILED -> not clicking: ' + gate.why.join('; '));
            await sleep(1200);
            lastSync = 0;
            continue;
          }
          /* LIVE PICK IS PRIMARY.
           *
           * A 60-second clock is enormous next to a ~3s decision, and a pick
           * computed at our turn sees the real board -- unlike a queue built
           * minutes earlier, which from slot 7 held six players who were all
           * gone by pick 7. The queue stays as the backup that catches us if
           * every click fails.
           *
           * Retry: one failed attempt used to surrender the whole clock. */
          if (autopickArmed()) {
            note('ON CLOCK (autopick armed) -> queue head takes it');
          } else {
            let res = await draftTop(4);
            if (res.err && !onClock()) {
              note('ON CLOCK -> turn ended: ' + JSON.stringify(res));
            } else if (res.err) {
              await sleep(800);
              res = await draftTop(4);     // second bite while time remains
              note('ON CLOCK retry -> ' + JSON.stringify(res));
            } else {
              note('ON CLOCK -> ' + JSON.stringify(res));
            }
          }
          await sleep(1200);
          lastSync = 0; // force resync after our pick
        } else {
          await keepAlive();     // Yahoo's inactivity timer counts human activity, not our clicks
          const rcNow = rc ? rc.have : -1;
          if (rcNow !== S.lastRoster || Date.now() - lastSync > 12000) {
            S.lastRoster = rcNow;
            lastSync = Date.now();
            await refreshPlan();
            const q = await syncQueue();
            note('sync r' + (q.round || '?') + ' queued=' + JSON.stringify(q.queued || []) +
                 ' depth=' + ((q.queueNow || []).length));
          }
        }
        // short poll keeps the client active
        await sleep(900);
      }
    } catch (e) {
      note('ERROR ' + (e && e.message));
    }
    S.running = false;
    note('driver stop');
    return S.log.slice(-12);
  }

  /* The complete trail of a draft, composed from the store (every pick with
   * its team id, every manager) and our retained pick records, POSTed to the
   * bridge's /trail; scripts/mock_trail.py renders it. Requested 2026-09-02
   * ("a complete trail of each manager's picks and roster"); until the
   * review the same day this lived in a console snippet, not the driver.
   * `extra` merges into the dump (e.g. { room_name }). Pure given the store
   * and a fetch: tested through _setStore with fetch stubbed. */
  function trailDump(extra) {
    const store = findStore();
    let s;
    try { s = store && store.getState(); } catch (e) { s = null; }
    if (!s || !s.draftPicks || !s.players) return null;
    const byId = s.players.byId || {};
    const managers = (s.league && s.league.managers) || {};
    const me = s.context && managers[String(s.context.managerId)];
    const picks = (s.draftPicks.order || []).filter(o => o && o.playerId).map(o => {
      const p = byId[o.playerId] || {};
      return { pick_no: +o.id, team_id: String(o.teamId),
               name: ((p.fname || '') + ' ' + (p.lname || '')).trim(),
               pos: p.primary_pos || p.display_pos || '', team: p.team_abbr || '' };
    });
    const mgrs = {};
    for (const m of Object.values(managers)) {
      mgrs[String(m.teamId)] = { nickname: m.nickname || '', teamId: String(m.teamId), away: !!m.away };
    }
    const room = (s.context && String(s.context.leagueId))
      || ((typeof location !== 'undefined' && (location.pathname.match(/\/(\d+)\/\d+/) || [])[1]) || 'room');
    const isHeartbeat = l => /heartbeat: setAwayStatus/.test(String(l));
    const isIssue = l => /GATE FAILED|notours|retry|ERROR|noland|nobtn/.test(String(l));
    return Object.assign({
      room, room_name: (typeof document !== 'undefined' && document.title) || '',
      teams: S.cfg.teams, my_team: me ? String(me.teamId) : null,
      captured_at: new Date().toISOString(),
      picks, managers: mgrs, our_records: S.records.slice(),
      heartbeats: S.log.filter(isHeartbeat).length, issues: S.log.filter(isIssue).length,
    }, extra || {});
  }

  async function trail(extra) {
    const dump = trailDump(extra);
    if (!dump) return { err: 'no store' };
    try {
      const r = await fetch(S.cfg.bridge + '/trail', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(dump) });
      const j = await r.json();
      note('trail: ' + dump.picks.length + ' picks, ' + dump.our_records.length + ' records -> ' + (j.path || JSON.stringify(j)));
      return j;
    } catch (e) {
      return { err: 'bridge: ' + (e && e.message) };
    }
  }

  /* Which entries are indistinguishable from another by everything the
   * Yahoo row shows except ADP. rowMatches refuses to guess on these.
   * Computed for BOTH load paths: the JSON path used to skip it, which
   * silently switched the Bijan/Brian Robinson guard off (found 2026-09-01
   * while loading the board from the bridge instead of a compact paste). */
  function markCollisions() {
    const seen = {};
    S.collisions = new Set();
    for (const p of S.board) {
      const id = p.k + '|' + p.p + '|' + normTeam(p.t);
      if (seen[id]) S.collisions.add(id); else seen[id] = 1;
    }
    return S.collisions.size;
  }

  return {
    load(board, cfg) {
      S.board = board.map(function (p) {
        return Object.assign({}, p, { k: p.k || idKey(p.n, p.p) });
      });
      Object.assign(S.cfg, cfg || {});
      return 'loaded ' + S.board.length + ' players, '
             + markCollisions() + ' name collision(s)';
    },
    /* Pipe format from scripts/export_board_json.py:
     *   name|pos|team|vorp|upside|status|adp   (already VORP-desc) */
    loadCompact(txt, cfg) {
      S.board = txt.split('\n').filter(Boolean).map(function (ln) {
        const f = ln.split('|');
        return { n: f[0], k: idKey(f[0], f[1]), p: f[1], t: f[2],
                 v: parseFloat(f[3]) || 0, u: f[4] === '1', s: f[5] || '',
                 a: f[6] ? parseFloat(f[6]) : null,
                 d: f[7] !== undefined && f[7] !== '' ? parseFloat(f[7]) : undefined };
      });
      Object.assign(S.cfg, cfg || {});
      return 'loaded ' + S.board.length + ' players, '
             + markCollisions() + ' name collision(s)';
    },
    /* Accept a plan from scripts/yahoo_bridge.py. */
    refreshPlan,
    planStatus: () => ({ have: !!(S.plan && S.plan.length), err: S.planErr,
                         atPick: S.planPick, ageMs: S.planAt ? Date.now() - S.planAt : null }),
    loadPlan(obj) {
      S.plan = (obj && obj.plan) || null;
      S.planNeeds = (obj && obj.needs) || null;
      S.planPick = (obj && obj.current_pick) != null ? obj.current_pick : null;
      return S.plan ? ('plan ' + S.plan.length + ' deep @pick ' + S.planPick) : 'no plan';
    },
    /* Everything the bridge needs to rebuild engine state, read off the page. */
    exportState(mySlot, teams, rounds) {
      const ros = myRoster();
      return {
        my_slot: mySlot, teams: teams || S.cfg.teams, rounds: rounds || S.cfg.rounds,
        my_roster: (ros ? ros.players : []).map(p => ({ name: p.disp, pos: p.pos })),
        drafted: draftedFeed(),
        on_clock: onClock(), armed: autopickArmed(),
        roster_count: rosterCount(),
      };
    },
    reset() {
      S.gone = new Set(); S.starred = new Set(); S.log = []; S.lastRoster = -1;
      return 'reset';
    },
    rank, syncQueue, draftTop, run, gatesOk, storeState, findStore, keepAlive, preflight, _setStore,
    classifyMiss, rowMatches, normTeam, autopickArmed, idKey, // exported for tests
    findRow, parsePicksPanel, myRoster, tableLive, currentPickNo, // offline DOM tests (jsdom + fixtures)
    survivalProb, eBestNext, calibrate,
    reconcileStarred, reconcileStarredWith,
    /* Human-readable rationale for the pick we intend to make. Exists so the
     * run can be narrated: a board that cannot explain itself is impossible
     * to audit mid-draft, and every mock bug so far was caught by noticing a
     * pick that did not make sense. */
    why() {
      const r = rank();
      if (r.err) return { err: r.err };
      const t = r.top[0];
      if (!t) return { err: 'no eligible candidate' };
      const runnerUp = r.top[1];
      const openSlots = Object.entries(r.need)
        .filter(([, n]) => n > 0).map(([k, n]) => n > 1 ? `${k}x${n}` : k);
      const samePos = r.top.filter(x => x.p === t.p);
      const nextBestOther = r.top.find(x => x.p !== t.p);
      return {
        round: r.round,
        picksLeft: r.picksLeft,
        roster: r.counts,
        openStarters: openSlots,
        pick: `${t.n} (${t.p}, VORP ${t.v})`,
        fillsNeed: t.fills,
        overNextAtPosition: samePos[1]
          ? `${(t.v - samePos[1].v).toFixed(1)} over next ${t.p} (${samePos[1].n})`
          : `only ${t.p} left on board`,
        overNextOtherPosition: nextBestOther
          ? `${(t.v - nextBestOther.v).toFixed(1)} over best ${nextBestOther.p} (${nextBestOther.n})`
          : null,
        runnerUp: runnerUp ? `${runnerUp.n} (${runnerUp.p}, ${runnerUp.v})` : null,
        alsoConsidered: r.top.slice(1, 5).map(x => `${x.n} ${x.p} ${x.v}`),
        blockedByGuardrails: r.blockedSample,
      };
    },
    /* Pure form of the queue-row parser, so the on-clock "Draft" prefix that
     * made mock 4 report an empty queue stays covered. */
    /* Pure form of the queue planner: which of the ranked candidates would
     * actually be queued, given each one is checked against a roster holding
     * everything planned ahead of it. */
    planQueue: (counts, have, depth) => {
      const r = rank();
      if (r.err) return [];
      const sim = Object.assign({}, counts || r.counts);
      let simHave = have == null ? (S.cfg.rounds - r.picksLeft) : have;
      const out = [];
      for (const cand of r.top) {
        if (out.length >= (depth || S.cfg.queueDepth)) break;
        const entry = S.board.find(b => b.n === cand.n && b.p === cand.p);
        if (!entry) continue;
        if (!guardrailOk(entry, simHave + 1, needsMap(sim), sim,
                         S.cfg.rounds - simHave, false)) continue;
        out.push(cand.n + '|' + cand.p);
        sim[cand.p] = (sim[cand.p] || 0) + 1;
        simHave++;
      }
      return out;
    },
    parseQueueRow: (text) => {
      const x = (text || '').replace(/\s+/g, ' ').trim();
      const m = x.match(/(?:^|^Draft\s+)([A-Z]\.\s?[A-Za-z'\-\.]+)\s+(?:Q|IR|IR-R|O|D|SUSP|PUP|CEL|NA)?\s*(QB|RB|WR|TE|K|DEF)\b/);
      return m ? keyFull(m[1]) + '|' + m[2] : null;
    },
    /* Pure form of the post-click check in draftTop. A pick counts only when
     * the roster actually grew. */
    pickLanded: (before, after) => !!(after && before && after.have > before.have),
    pickLandedStore, bannerSaysArmed,
    clientActions, playerIdFor, pickViaAction,
    /* test hook: hand the driver bound actions without a React tree */
    _setActions(acts) { S.actions = acts || null; S.actionsAt = Date.now(); S.actionsMissAt = null; return !!acts; },
    trail, trailDump,
    records() { return S.records.slice(); },
    _starred: () => [...S.starred],
    _markStarred: (id) => S.starred.add(id),
    _isStarred: (id) => S.starred.has(id),
    state: () => ({ roster: rosterCount(), counts: (myRoster() || {}).counts,
                    queue: queueNames(), title: document.title.slice(0, 40),
                    running: S.running }),
    logs: (n) => S.log.slice(-(n || 30)),
    stop() { S.running = false; return 'stopping'; },
  };
})();
