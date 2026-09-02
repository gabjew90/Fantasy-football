/* Passive network tap for the Yahoo draft client -- INSTRUMENTATION ONLY.
 *
 * Purpose (design 2026-09-01, layer 2): learn how the draft client receives
 * picks. draftstatus for a live league carries a draft_server/draft_port, so
 * there is a dedicated channel; whether it is a WebSocket, long-poll, or
 * plain polling of a JSON endpoint decides how the rig should read state
 * instead of scraping the screen.
 *
 * Hooks WebSocket (open/send/message) and fetch/XMLHttpRequest, buffers what
 * it sees with timestamps, and changes nothing. Install as early as possible
 * after the draft page loads; the client may already have connected, in which
 * case only later traffic is captured -- still enough to see the message
 * shape for each pick.
 *
 *   (0,eval)(await (await fetch('https://127.0.0.1:8443/net_tap.js')).text());
 *   NET.summary();            // counts by kind and host
 *   NET.dump({limit: 20});    // recent entries, bodies truncated
 *   NET.find(/pick|draft/i);  // entries whose body matches
 */
window.NET = (function () {
  const B = { entries: [], max: 4000, installedAt: Date.now() };
  const push = e => { B.entries.push(Object.assign({ t: Date.now() }, e)); if (B.entries.length > B.max) B.entries.shift(); };
  const short = (s, n) => { s = typeof s === 'string' ? s : (s == null ? '' : String(s)); return s.length > (n || 600) ? s.slice(0, n || 600) + '…[' + s.length + ']' : s; };
  const host = u => { try { return new URL(u, location.href).host; } catch (e) { return String(u).slice(0, 40); } };

  // --- WebSocket ---
  const RealWS = window.WebSocket;
  if (RealWS && !RealWS.__dkTapped) {
    const Tapped = function (url, protocols) {
      const ws = protocols === undefined ? new RealWS(url) : new RealWS(url, protocols);
      push({ kind: 'ws-open', url: String(url), host: host(url) });
      ws.addEventListener('message', ev => push({ kind: 'ws-in', host: host(url), body: short(ev.data) }));
      ws.addEventListener('close', ev => push({ kind: 'ws-close', host: host(url), code: ev.code }));
      const send = ws.send.bind(ws);
      ws.send = data => { push({ kind: 'ws-out', host: host(url), body: short(data) }); return send(data); };
      return ws;
    };
    Tapped.prototype = RealWS.prototype;
    Tapped.__dkTapped = true;
    ['CONNECTING', 'OPEN', 'CLOSING', 'CLOSED'].forEach(k => { Tapped[k] = RealWS[k]; });
    window.WebSocket = Tapped;
  }

  // --- fetch ---
  const realFetch = window.fetch;
  if (realFetch && !realFetch.__dkTapped) {
    const tapped = async function (input, init) {
      const url = typeof input === 'string' ? input : (input && input.url) || '';
      const started = Date.now();
      const res = await realFetch.apply(this, arguments);
      try {
        const clone = res.clone();
        clone.text().then(body => push({ kind: 'fetch', method: (init && init.method) || 'GET', url: short(url, 200), host: host(url), status: res.status, ms: Date.now() - started, body: short(body, 800) }));
      } catch (e) { push({ kind: 'fetch', url: short(url, 200), host: host(url), status: res.status, err: String(e).slice(0, 80) }); }
      return res;
    };
    tapped.__dkTapped = true;
    window.fetch = tapped;
  }

  // --- XMLHttpRequest ---
  const XO = XMLHttpRequest.prototype.open, XS = XMLHttpRequest.prototype.send;
  if (!XO.__dkTapped) {
    XMLHttpRequest.prototype.open = function (m, u) { this.__dk = { m, u: String(u) }; return XO.apply(this, arguments); };
    XMLHttpRequest.prototype.send = function (body) {
      const meta = this.__dk || {};
      this.addEventListener('loadend', () => push({ kind: 'xhr', method: meta.m, url: short(meta.u, 200), host: host(meta.u), status: this.status, body: short(this.responseText, 800) }));
      return XS.apply(this, arguments);
    };
    XMLHttpRequest.prototype.open.__dkTapped = true;
  }

  return {
    summary() {
      const by = {};
      for (const e of B.entries) { const k = e.kind + ' ' + (e.host || ''); by[k] = (by[k] || 0) + 1; }
      return { entries: B.entries.length, sinceMs: Date.now() - B.installedAt, by };
    },
    dump(opts) {
      const o = opts || {};
      let es = B.entries;
      if (o.kind) es = es.filter(e => e.kind === o.kind);
      if (o.host) es = es.filter(e => (e.host || '').includes(o.host));
      return es.slice(-(o.limit || 20)).map(e => Object.assign({}, e, { body: short(e.body, o.bodyLen || 300) }));
    },
    find(re, limit) { return B.entries.filter(e => re.test(e.body || '') || re.test(e.url || '')).slice(-(limit || 20)); },
    clear() { B.entries = []; return 'cleared'; },
    raw: () => B.entries,
  };
})();
