/* Yahoo "Edit Pre-Draft Ranks" driver -- LAYER 0 of the draft rig.
 *
 * Yahoo's autopick walks the manager's pre-ranked list ("My Preferred") in
 * order, skipping anyone whose position would exceed the internal balance
 * cap, and falls back to Yahoo's default ranks only when the list is empty.
 * If that list IS our board, every pick our live driver misses is still made
 * from our own valuation with Yahoo's positional balancing -- with nothing of
 * ours running. That is the floor everything else degrades into.
 *
 * THE FAST PATH IS THE IMPORT DIALOG (verified 2026-09-01, league 49649):
 * "Paste a list or upload a CSV -- never leaves your browser. One player per
 * line, comma-separated. Columns: rank,name,team,position. The name column is
 * what we match on." Pasting 240 lines and pressing the dialog's Import
 * replaced the whole list in one shot: "Imported 228 players", in exact
 * order, then Save persisted it (the API's has_preranks for our team went 1).
 *
 * The star-by-star path also works and preserves click order, but Yahoo
 * re-renders after every click and gets slower as the list grows -- 0.9s a
 * click at 50 players, 1.5s at 100 -- and a devtools eval is cut off at ~45s.
 * Kept as PR.next() for touching up single players.
 *
 * Known matcher gaps: names with initials ("DK Metcalf", "J.K. Dobbins")
 * were not matched under either spelling tried; players outside Yahoo's
 * 300-player list cannot be ranked at all. PR.unmatched() lists them so the
 * gaps are visible rather than silent.
 *
 *   (0,eval)(await (await fetch('https://127.0.0.1:8443/prerank.js')).text());
 *   const board = await (await fetch('https://127.0.0.1:8443/board.json')).json();
 *   PR.load(board);
 *   await PR.import();       // "Imported N players"
 *   await PR.dnd();          // Do-Not-Draft for availability = out
 *   PR.save();               // writes to Yahoo; reversible via the page's Reset
 *   await PR.unmatched();    // what did not land
 */
window.PR = (function () {
  const OUT = new Set(['out', 'ir', 'pup', 'sus', 'suspended']);
  const TEAM = { SFO: 'SF', GBP: 'GB', GNB: 'GB', JAC: 'JAX', KCC: 'KC', LVR: 'LV',
                 NEP: 'NE', NWE: 'NE', NOS: 'NO', NOR: 'NO', TBB: 'TB', TAM: 'TB',
                 ARZ: 'ARI', BLT: 'BAL', CLV: 'CLE', HST: 'HOU', WSH: 'WAS' };
  const S = { order: [], dnd: [], done: [], miss: [], log: [], variants: {} };
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const vis = el => !!(el && (el.offsetWidth || el.offsetHeight));
  function note(m) { S.log.push(new Date().toISOString().slice(11, 19) + ' ' + m); return m; }

  /* Same normalisation on BOTH sides; defenses match on the nickname. */
  function norm(name, pos) {
    if (pos === 'DEF') return String(name).trim().split(/\s+/).pop().toUpperCase();
    return String(name).toUpperCase()
      .replace(/\s+(JR\.?|SR\.?|II|III|IV|V)$/, '')
      .replace(/[^A-Z' .-]/g, '').replace(/\s+/g, ' ').trim();
  }
  /* A row is the button's parent; its textContent is short:
   * "James Cook IIIRB·Buf·Bye 7XRank #9·ADP 9.5". Cheap on purpose. */
  function parseRow(btn) {
    const m = ((btn.parentElement && btn.parentElement.textContent) || '').match(/^(.*?)(QB|RB|WR|TE|K|DEF)\b/);
    return m ? { name: m[1].trim(), pos: m[2] } : null;
  }
  function index(labelRe) {
    const out = {};
    for (const b of document.querySelectorAll('button[aria-label]')) {
      if (!labelRe.test(b.getAttribute('aria-label') || '')) continue;
      const r = parseRow(b);
      if (r) out[norm(r.name, r.pos) + '|' + r.pos] = b;
    }
    return out;
  }
  const STAR = /My Preferred/i, DND = /Do Not Draft/i;

  function tab(name) {
    const t = [...document.querySelectorAll('[role=tab],button')]
      .find(b => new RegExp('^' + name).test((b.textContent || '').trim()));
    if (!t) return false;
    if (t.getAttribute('aria-selected') !== 'true') t.click();
    return true;
  }
  function setValue(el, text) {   // React-controlled: native setter + input event
    Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set.call(el, text);
    el.dispatchEvent(new Event('input', { bubbles: true }));
  }
  function displayName(p) {
    if (p.p === 'DEF') return p.n.trim().split(/\s+/).pop();
    return S.variants[p.n] || p.n;
  }

  return {
    /* board: the bridge's /board.json (VORP-desc, s = availability status). */
    load(board, opts) {
      S.variants = (opts && opts.variants) || {};
      const skill = board.filter(p => !['K', 'DEF'].includes(p.p) && !OUT.has((p.s || '').toLowerCase()));
      const kdef = board.filter(p => ['K', 'DEF'].includes(p.p));
      // K/DEF last: Yahoo fills starters first, and a kicker high on the list
      // would otherwise be taken the moment a mid-round pick has no better use
      S.order = skill.concat(kdef);
      S.dnd = board.filter(p => OUT.has((p.s || '').toLowerCase()));
      S.done = []; S.miss = [];
      return note('loaded ' + S.order.length + ' to rank, ' + S.dnd.length + ' do-not-draft');
    },
    csv() {
      return 'rank,name,team,position\n' + S.order.map((p, i) =>
        [i + 1, displayName(p), TEAM[p.t] || p.t, p.p].join(',')).join('\n');
    },
    /* One-shot: open the Import dialog, paste, submit. Replaces the list. */
    async import() {
      if (tab('All Players')) await sleep(700);
      const imp = [...document.querySelectorAll('button')].find(b => b.textContent.trim() === 'Import');
      if (!imp) return note('no Import button');
      imp.click(); await sleep(900);
      const ta = document.querySelector('textarea');
      if (!vis(ta)) return note('import dialog did not open');
      setValue(ta, this.csv()); await sleep(800);
      const btns = [...document.querySelectorAll('button')].filter(b => vis(b) && b.textContent.trim() === 'Import');
      const submit = btns[btns.length - 1];      // the dialog's Import comes after the page's
      if (!submit || submit === imp) return note('no dialog Import button');
      submit.click(); await sleep(4000);
      const msg = (document.body.innerText.match(/Imported \d+ players/) || [''])[0];
      return note(msg || 'import: no confirmation seen');
    },
    async dnd(delayMs) {
      if (tab('All Players')) await sleep(800);
      const idx = index(DND);
      const res = [];
      for (const p of S.dnd) {
        const key = norm(p.n, p.p) + '|' + p.p;
        const b = idx[key];
        if (!b) { res.push(key + ':missing'); continue; }
        if (/Remove/i.test(b.getAttribute('aria-label') || '')) { res.push(key + ':already'); continue; }
        b.click(); res.push(key + ':ok');
        await sleep(delayMs || 200);
      }
      return res;
    },
    /* Star the next n in order that are not already starred. Slow; use to
     * touch up after import(), not to build the list. */
    async next(n, delayMs) {
      if (tab('All Players')) await sleep(800);
      const idx = index(STAR);
      let clicked = 0;
      for (const p of S.order) {
        if (clicked >= (n || 10)) break;
        const key = norm(p.n, p.p) + '|' + p.p;
        if (S.done.includes(key) || S.miss.includes(key)) continue;
        const b = idx[key];
        if (!b) { S.miss.push(key); continue; }   // not shown: starred already, or not on Yahoo's list
        b.click(); S.done.push(key); clicked++;
        await sleep(delayMs || 100);
      }
      return note('starred ' + clicked);
    },
    /* Read the list back as Yahoo holds it. */
    async preferred() {
      if (!tab('My Preferred')) return { err: 'no My Preferred tab' };
      await sleep(1300);
      const names = [...document.querySelectorAll('button[aria-label]')]
        .filter(b => STAR.test(b.getAttribute('aria-label') || ''))
        .map(b => (parseRow(b) || {}).name).filter(Boolean);
      return { count: names.length, head: names.slice(0, 5), tail: names.slice(-3), names };
    },
    async unmatched() {
      const pref = await this.preferred();
      if (pref.err) return pref;
      const have = new Set(pref.names.map(n => norm(n, 'X')));
      const out = S.order.filter(p => !have.has(norm(displayName(p), p.p === 'DEF' ? 'DEF' : 'X')))
        .map(p => p.n + ' ' + p.p + ' ' + p.t);
      tab('All Players');
      return { preferred: pref.count, ordered: S.order.length, unmatched: out };
    },
    save() {
      const b = [...document.querySelectorAll('button')].find(x => x.textContent.trim() === 'Save');
      if (!b) return 'no Save button';
      if (b.disabled) return 'Save disabled (nothing to save)';
      b.click(); return note('Save clicked');
    },
    status() { return { ordered: S.order.length, dnd: S.dnd.length, log: S.log.slice(-5) }; },
    norm, log: () => S.log.slice(-10),
  };
})();
