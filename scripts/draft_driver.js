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
    board: [],          // [{n,k,p,t,v,j,a,s,u,tier}] sorted by VORP desc
    cfg: {
      slots: { QB: 1, RB: 2, WR: 2, TE: 1, FLEX: 1, K: 1, DEF: 1 },
      bench: 6,
      rounds: 15,
      teams: 10,
      qb2Round: 10,
      te2FallPicks: 12,
      queueDepth: 5,
    },
    log: [],
    lastRoster: -1,
    running: false,
    gone: new Set(),    // board entries proven undraftable (no star button)
    starred: new Set(), // players WE queued; the star is a toggle, never re-click
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
      if (!out.some(o => o.pos === 'DEF')) out.push({ disp: m[1].trim(), pos: 'DEF', team: '', k: keyAbbr(m[1]) });
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

  function guardrailOk(p, rnd, need, counts, picksLeft, top6TeFell, haveStash) {
    if (!posAllowed(p.p, rnd, counts, picksLeft, top6TeFell)) return false;
    if ((p.v || 0) <= 0 && !needsPosition(need, p.p) && haveStash) return false;
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

  /* ---------------- ranking ---------------- */

  function rank() {
    const ros = myRoster();
    if (!ros) return { err: 'no roster panel' };
    const counts = ros.counts;
    const have = ros.players.length;
    const picksLeft = S.cfg.rounds - have;
    const rnd = have + 1;
    const need = needsMap(counts);
    const mine = new Set(ros.players.map(p => p.k + '|' + p.pos));

    const haveStash = ros.players.some(p => {
      const b = S.board.find(x => x.k === p.k && x.p === p.pos);
      return b && (b.v || 0) <= 0;
    });

    /* TE2 gate. The Python engine asks "did a top-6 TE fall to us", which
     * needs a reliable drafted-set we deliberately do not have. Equivalent
     * local rule: a 2nd TE is only allowed if the candidate IS one of the
     * board's six best TEs -- same intent, no scraping. */
    const te6 = S.board.filter(x => x.p === 'TE').slice(0, 6).map(x => x.n);

    const avail = S.board.filter(x =>
      !mine.has(x.k + '|' + x.p) && !isGone(x));

    const eligible = [];
    const blocked = [];
    for (const p of avail) {
      const teOk = p.p !== 'TE' || (counts.TE || 0) < 1 || te6.includes(p.n);
      if (teOk && guardrailOk(p, rnd, need, counts, picksLeft, true, haveStash)) eligible.push(p);
      else if (blocked.length < 6) blocked.push(p.n + '(' + p.p + ')');
    }

    // need-weighted: a player filling an open starter slot outranks a
    // marginally better one who does not.
    const scored = eligible.map(p => {
      const fills = needsPosition(need, p.p);
      const urgent = picksLeft <= (['QB','RB','WR','TE','FLEX','K','DEF']
        .reduce((a, k) => a + (need[k] || 0), 0)) + 1;
      let s = p.v;
      if (fills) s += 12;
      if (fills && urgent) s += 60;
      return { p, s, fills };
    }).sort((a, b) => b.s - a.s);

    return {
      round: rnd, picksLeft, counts, need,
      openStarters: ['QB','RB','WR','TE','FLEX','K','DEF'].reduce((a,k)=>a+(need[k]||0),0),
      top: scored.slice(0, 20).map(x => ({
        n: x.p.n, p: x.p.p, t: x.p.t, v: x.p.v, s: Math.round(x.s), fills: x.fills, st: x.p.s,
      })),
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

  /* Is the player table actually rendering rows? Used to distinguish "this
   * player is drafted" from "the table is not up", so a UI problem can never
   * again be recorded as league-wide unavailability. */
  function tableLive() {
    return [...document.querySelectorAll('div,li,tr')].some(e => {
      const x = (e.innerText || '').replace(/\s+/g, ' ');
      return x.length < 260 && /Bye \d+/.test(x)
        && [...e.querySelectorAll('button')].some(b => !b.textContent.trim() && b.querySelector('svg'));
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
  function rowMatches(entry, text) {
    const initial = entry.k[0];
    const last = entry.k.slice(2);
    if (!/Bye \d+/.test(text)) return false;
    if (!new RegExp('\\b' + initial + '\\.\\s?[A-Za-z\'\\-]*' + last + '\\b', 'i').test(text)) return false;
    if (!new RegExp('\\b' + entry.p + '\\b').test(text)) return false;
    if (entry.t) {
      const want = normTeam(entry.t);
      const seen = (text.match(/\b([A-Za-z]{2,3})\b(?=\s+Bye)/) || [])[1];
      if (seen && normTeam(seen) !== want) return false;
    }
    /* ADP guard for same-name-same-team collisions. Generous tolerance: it
     * only has to separate players who are dozens of picks apart. */
    if (entry.a != null) {
      const seen = rowAdp(text);
      if (seen != null && Math.abs(seen - entry.a) > Math.max(25, entry.a * 0.5)) return false;
    }
    return true;
  }

  function findRow(entry) {
    const rows = [...document.querySelectorAll('div,li,tr')].filter(e => {
      const x = (e.innerText || '').replace(/\s+/g, ' ');
      if (x.length > 260) return false;
      if (!rowMatches(entry, x)) return false;
      // star button present => it is a player-table row, not the queue panel
      return [...e.querySelectorAll('button')].some(b => !b.textContent.trim() && b.querySelector('svg'));
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
    if (!setSearch(entry.k.slice(2))) return 'nosearch';
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
      if (x.length > 120) continue;
      const m = x.match(/^([A-Z]\.\s?[A-Za-z'\-\.]+)\s+(?:Q|IR|O|D|SUSP|PUP|CEL|NA)?\s*(QB|RB|WR|TE|K|DEF)\b/);
      if (!m) continue;
      const btn = [...e.querySelectorAll('button')].find(b => !b.textContent.trim() && b.querySelector('svg'));
      if (!btn) continue;
      const key = keyAbbr(m[1]) + '|' + m[2];
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
    const legal = new Set(r.top.map(x => keyFull(x.n) + '|' + x.p));
    const removed = [];
    for (const row of queueRows()) {
      if (legal.has(row.key)) continue;
      row.btn.click();
      removed.push(row.text.slice(0, 28));
      S.starred.forEach(id => {
        const [n, p] = id.split('|');
        if (keyFull(n) + '|' + p === row.key) S.starred.delete(id);
      });
      await sleep(350);
    }
    return { removed };
  }

  function queueNames() {
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
      const key = keyFull(id.slice(0, i)) + '|' + id.slice(i + 1);
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
    reconcileStarred();                    // free up slots taken by others
    const pruned = await pruneQueue();     // drop what is no longer legal
    const r = rank();
    if (r.err) return r;
    const have = queueNames();
    const results = [];
    let depth = have.length;
    for (const cand of r.top) {
      if (depth >= S.cfg.queueDepth) break;
      const entry = S.board.find(b => b.n === cand.n && b.p === cand.p);
      if (!entry) continue;
      const id = cand.n + '|' + cand.p;
      /* The star is a TOGGLE. Re-clicking one we already queued REMOVES the
       * player. queueNames() cannot always see the whole queue (Yahoo caps
       * the visible list), so trusting it alone made the driver re-star the
       * 5th entry every cycle, flipping them in and out. Track our own
       * clicks instead. */
      if (have.includes(keyFull(cand.n) + '|' + cand.p) || S.starred.has(id)) continue;
      const res = await starPlayer(entry);
      if (res === 'ok') { depth++; S.starred.add(id); results.push(cand.n + ':ok'); }
      else if (res === 'norow' || res === 'nostar') {
        markGone(entry); results.push(cand.n + ':' + res + '->gone');
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
  async function draftTop(maxTries) {
    const r = rank();
    if (r.err || !r.top.length) return { err: r.err || 'no candidates' };
    const before = rosterCount();
    ensurePlayersTab();
    await sleep(300);
    const attempted = [];
    let tries = 0;
    for (const cand of r.top) {
      if (tries >= (maxTries || 3)) break;
      const entry = S.board.find(b => b.n === cand.n && b.p === cand.p);
      if (!entry) continue;
      if (!setSearch(entry.k.slice(2))) continue;
      tries++;
      await sleep(700);
      const row = findRow(entry);
      if (!row) {
        const why = await diagnoseMiss();
        if (why === 'uinotready') return { err: 'ui-not-ready', attempted };
        markGone(entry);
        continue;
      }
      row.click();
      await sleep(600);
      const btns = [...document.querySelectorAll('button')].filter(b => {
        const x = b.textContent.replace(/\s+/g, ' ').trim();
        return /^Draft/i.test(x) && !b.disabled && !b.closest('[role=tablist]');
      });
      const pick = btns.find(b => /Player/i.test(b.textContent)) || btns[btns.length - 1];
      if (!pick) { attempted.push(cand.n + ':nobtn'); continue; }
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
      const after = rosterCount();
      if (!(after && before && after.have > before.have)) {
        attempted.push(cand.n + ':noland');
        continue;
      }
      return { drafted: cand.n, pos: cand.p, vorp: cand.v, verified: true };
    }
    return { err: 'no-verified-pick', attempted };
  }

  /* Yahoo tells us when it has taken the wheel. Once armed it drafts the
   * instant the turn opens, so racing it with clicks only wastes the clock --
   * and the clock expiring is what armed it. When armed, trust the queue. */
  function autopickArmed() {
    return /put into autopick mode/i.test(document.body.innerText);
  }

  /* Resident loop: this is what stops autopick from ever arming. */
  async function run(maxSeconds) {
    if (S.running) return 'already running';
    S.running = true;
    const deadline = Date.now() + (maxSeconds || 3600) * 1000;
    note('driver start');
    let lastSync = 0;
    try {
      while (Date.now() < deadline) {
        const rc = rosterCount();
        if (rc && rc.have >= S.cfg.rounds) { note('roster full'); break; }
        if (/draft results|draft complete/i.test(document.title)) { note('draft over'); break; }

        if (onClock()) {
          /* The queue head IS the engine's top pick (syncQueue keeps it so),
           * and autopick consumes it immediately. Clicking as well is pure
           * upside when it works and pure clock-burn when it does not, so
           * only try while Yahoo has not already taken over. */
          if (autopickArmed()) {
            note('ON CLOCK (autopick armed) -> queue head takes it');
          } else {
            const res = await draftTop();
            note('ON CLOCK -> ' + JSON.stringify(res));
          }
          await sleep(1200);
          lastSync = 0; // force resync after our pick
        } else {
          const rcNow = rc ? rc.have : -1;
          if (rcNow !== S.lastRoster || Date.now() - lastSync > 12000) {
            S.lastRoster = rcNow;
            lastSync = Date.now();
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

  return {
    load(board, cfg) {
      S.board = board;
      Object.assign(S.cfg, cfg || {});
      return 'loaded ' + board.length + ' players';
    },
    /* Pipe format from scripts/export_board_json.py:
     *   name|pos|team|vorp|upside|status|adp   (already VORP-desc) */
    loadCompact(txt, cfg) {
      S.board = txt.split('\n').filter(Boolean).map(function (ln) {
        const f = ln.split('|');
        return { n: f[0], k: keyFull(f[0]), p: f[1], t: f[2],
                 v: parseFloat(f[3]) || 0, u: f[4] === '1', s: f[5] || '',
                 a: f[6] ? parseFloat(f[6]) : null };
      });
      Object.assign(S.cfg, cfg || {});
      return 'loaded ' + S.board.length + ' players';
    },
    reset() {
      S.gone = new Set(); S.starred = new Set(); S.log = []; S.lastRoster = -1;
      return 'reset';
    },
    rank, syncQueue, draftTop, run,
    classifyMiss, rowMatches, normTeam, autopickArmed, // exported for tests
    reconcileStarred, reconcileStarredWith,
    /* Pure form of the post-click check in draftTop. A pick counts only when
     * the roster actually grew. */
    pickLanded: (before, after) => !!(after && before && after.have > before.have),
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
