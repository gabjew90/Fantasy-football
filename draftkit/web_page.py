"""The dashboard page, embedded so `python -m draftkit web` is self-contained."""

PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>draftkit</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  :root {
    --bg: #0d1117; --panel: #161b22; --edge: #30363d; --fg: #e6edf3;
    --dim: #8b949e; --red: #f85149; --amber: #d29922; --green: #3fb950;
    --cyan: #58a6ff; --purple: #bc8cff;
  }
  * { box-sizing: border-box; margin: 0; }
  body { background: var(--bg); color: var(--fg);
         font: 16px/1.45 "Segoe UI", system-ui, sans-serif; padding: 14px; }
  .banner { border-radius: 10px; padding: 18px 24px; text-align: center;
            font-size: 34px; font-weight: 800; letter-spacing: .5px;
            border: 2px solid var(--edge); background: var(--panel); }
  .banner.me { background: #67060c; border-color: var(--red); color: #fff;
               animation: pulse 1s infinite; font-size: 44px; }
  .banner.err { background: #4d3800; border-color: var(--amber); color: #ffd970; }
  .banner.done { background: #0f5323; border-color: var(--green); }
  .banner small { display: block; font-size: 15px; font-weight: 400; color: inherit; opacity: .85; }
  @keyframes pulse { 50% { filter: brightness(1.35); } }
  .cols { display: grid; grid-template-columns: 5fr 4fr; gap: 14px; margin-top: 14px; }
  @media (max-width: 1100px) { .cols { grid-template-columns: 1fr; } }
  .panel { background: var(--panel); border: 1px solid var(--edge);
           border-radius: 10px; padding: 14px 16px; }
  .panel h2 { font-size: 13px; text-transform: uppercase; letter-spacing: 1px;
              color: var(--dim); margin-bottom: 10px; }
  .rec1 { font-size: 30px; font-weight: 800; }
  .rec1 .why, .rec .why { color: var(--dim); font-size: 15px; font-weight: 400; }
  .rec { font-size: 19px; padding: 7px 0; border-top: 1px solid var(--edge); }
  .tag { font-size: 13px; padding: 1px 8px; border-radius: 999px;
         border: 1px solid var(--edge); color: var(--dim); margin-left: 6px; }
  .pos-row { display: flex; gap: 10px; padding: 8px 0; border-top: 1px solid var(--edge);
             align-items: baseline; flex-wrap: wrap; }
  .pos-row:first-of-type { border-top: 0; }
  .pos-name { font-weight: 800; width: 44px; color: var(--cyan); font-size: 18px; }
  .pp { white-space: nowrap; }
  .pp b { font-size: 17px; }
  .pp .meta { color: var(--dim); font-size: 13px; }
  .cliffnow { color: #fff; background: var(--red); font-weight: 700;
              padding: 1px 8px; border-radius: 6px; font-size: 14px; }
  .cliffsoon { color: var(--amber); font-weight: 600; font-size: 14px; }
  .mountain { color: var(--purple); }
  .strip { margin-top: 14px; }
  .roster b { font-size: 18px; }
  .roster .full { color: var(--green); }
  .roster .open { color: var(--amber); }
  .drafted { color: var(--dim); margin-top: 6px; font-size: 15px; }
  .faller { margin-right: 18px; white-space: nowrap; }
  .faller .drop { color: var(--amber); font-weight: 700; }
  footer { display: flex; gap: 14px; align-items: center; flex-wrap: wrap;
           margin-top: 14px; color: var(--dim); font-size: 14px; }
  footer input { background: var(--bg); color: var(--fg); border: 1px solid var(--edge);
                 border-radius: 6px; padding: 6px 8px; font-size: 14px; }
  #draftId { width: 200px; }
  #slot { width: 52px; }
  footer button { background: #21262d; color: var(--fg); border: 1px solid var(--edge);
                  border-radius: 6px; padding: 6px 14px; font-size: 14px; cursor: pointer; }
  .stale { color: var(--amber); font-weight: 700; }
  #inputErr { color: var(--red); }
</style>
</head>
<body>
<div id="banner" class="banner">connecting…</div>
<div class="cols">
  <div class="panel"><h2>Pick now — one per position, ranked by what waiting costs</h2><div id="recs">—</div></div>
  <div class="panel"><h2>Board — top remaining by position</h2><div id="board">—</div></div>
</div>
<div class="panel strip roster" id="roster" style="display:none">
  <h2>My roster</h2><div id="rosterFill"></div><div class="drafted" id="drafted"></div>
</div>
<div class="panel strip" id="fallersPanel" style="display:none">
  <h2>Value fallers (≥ 1 round past ADP)</h2><div id="fallers"></div>
</div>
<footer>
  <label>mock draft ID (blank = real draft): <input id="draftId" placeholder=""></label>
  <label>slot: <input id="slot" type="number" min="1" max="12"></label>
  <button id="apply">apply</button>
  <button id="reload">reload tiers.csv</button>
  <span id="target"></span>
  <a id="logLink" href="/log" target="_blank" style="color:var(--cyan)">view log</a>
  <span id="tiersAt"></span>
  <span id="heartbeat"></span>
  <span id="inputErr"></span>
</footer>
<script>
const $ = id => document.getElementById(id);
let fails = 0, lastOk = null, seq = 0;

const store = {
  get draftId() { return localStorage.getItem("dk_draft_id") || ""; },
  set draftId(v) { v ? localStorage.setItem("dk_draft_id", v) : localStorage.removeItem("dk_draft_id"); },
  get slot() { return localStorage.getItem("dk_slot") || ""; },
  set slot(v) { v ? localStorage.setItem("dk_slot", v) : localStorage.removeItem("dk_slot"); },
};
$("draftId").value = store.draftId;
$("slot").value = store.slot;
$("apply").onclick = () => { store.draftId = $("draftId").value.trim(); store.slot = $("slot").value.trim(); tick(); };
$("reload").onclick = async () => { await fetch("/reload", {method: "POST"}); tick(); };

function esc(t) { const d = document.createElement("div"); d.textContent = t ?? ""; return d.innerHTML; }

function render(s) {
  const b = $("banner");
  if (!s.ok) {
    $("inputErr").textContent = s.error;
    if (!lastOk) {  // nothing good on screen yet: surface the error large
      b.className = "banner err";
      b.textContent = s.error;
      document.title = "⚠ draftkit";
    }
    return;
  }
  $("inputErr").textContent = "";

  if (s.poll_error) {
    b.className = "banner err";
    b.innerHTML = `RECONNECTING… <small>Sleeper poll failing (${esc(s.poll_error)}) — data may be ${esc(s.last_poll_age_s)}s old. Nothing is lost; it recovers by itself.</small>`;
    document.title = "⚠ draftkit";
  } else if (s.status === "complete") {
    b.className = "banner done";
    b.textContent = "DRAFT COMPLETE — good luck in the playoffs";
    document.title = "✅ draftkit";
  } else if (s.on_clock_me) {
    b.className = "banner me";
    b.innerHTML = `YOU ARE ON THE CLOCK <small>pick ${s.current_pick} · round ${s.round}</small>`;
    document.title = "🔴 YOUR PICK";
  } else if (s.status !== "drafting") {
    b.className = "banner";
    b.innerHTML = `waiting — draft status: ${esc(s.status)} <small>pick ${s.current_pick} · slot ${s.on_clock_slot} first on the clock</small>`;
    document.title = "draftkit";
  } else {
    b.className = "banner";
    const away = s.picks_away === null ? "no picks left" : `your turn in ${s.picks_away} pick${s.picks_away === 1 ? "" : "s"}`;
    b.innerHTML = `pick ${s.current_pick} (R${s.round}.${s.pick_in_round}) — slot ${s.on_clock_slot} on the clock <small>${away}${s.my_next_pick ? " (pick " + s.my_next_pick + ")" : ""}</small>`;
    document.title = `${s.picks_away} away · draftkit`;
  }

  $("recs").innerHTML = (s.recommendations || []).map((r, i) => `
    <div class="${i === 0 ? "rec1" : "rec"}">${esc(r.player)}
      <span class="tag">${esc(r.pos)}${esc(r.pos_rank)} · T${esc(r.tier)} · VORP ${esc(r.vorp)}</span>
      <div class="why">${esc(r.why)}</div>
    </div>`).join("") || "no candidates";

  $("board").innerHTML = (s.board || []).map(row => {
    let tag = "";
    if (row.urgent) tag = `<span class="cliffnow">CLIFF NOW — ${row.before_cliff} left, ${row.demand} rivals</span>`;
    else if (row.before_cliff !== null && row.before_cliff <= 3) tag = `<span class="cliffsoon">cliff in ${row.before_cliff}</span>`;
    const ps = row.players.map(p => {
      const d = p.adp_delta_live;
      const dtxt = d !== null && Math.abs(d) >= 3 ? ` ${d > 0 ? "+" : ""}${d}v` : "";
      return `<span class="pp"><b>${esc(p.player)}</b>${p.cliff ? '<span class="mountain">⛰</span>' : ""} <span class="meta">T${p.tier}·${p.vorp}${dtxt}</span></span>`;
    }).join(" ");
    return `<div class="pos-row"><span class="pos-name">${row.pos}</span>${ps} ${tag}</div>`;
  }).join("");

  if (s.roster) {
    $("roster").style.display = "";
    $("rosterFill").innerHTML = Object.keys(s.roster.slots).map(k => {
      const f = s.roster.filled[k], m = s.roster.slots[k];
      return `<b class="${f >= m ? "full" : "open"}">${k} ${f}/${m}</b>&nbsp;&nbsp;`;
    }).join("") + `<b>BN ${s.roster.bench_used}/${s.roster.bench_total}</b>`;
    $("drafted").textContent = "drafted: " + (s.roster.drafted.join(", ") || "—");
  }

  const f = s.fallers || [];
  $("fallersPanel").style.display = f.length ? "" : "none";
  $("fallers").innerHTML = f.map(x =>
    `<span class="faller"><b>${esc(x.player)}</b> (${esc(x.pos)}, ADP ${x.adp}, <span class="drop">−${x.fell}</span>)</span>`).join("");

  const stale = s.tiers_built_at && (Date.now() - new Date(s.tiers_built_at.replace(" ", "T")).getTime() > 12 * 3600e3);
  $("tiersAt").innerHTML = s.tiers_built_at
    ? (stale ? `<span class="stale">⚠ tiers built ${esc(s.tiers_built_at)} — consider refreshing</span>` : `tiers built ${esc(s.tiers_built_at)}`)
    : "";
}

async function tick() {
  const my = ++seq;  // response-ordering guard: never paint a stale snapshot
  // unmissable: which draft is this page actually tracking? (a mock id left
  // in the box from Saturday would otherwise silently hijack draft day)
  $("target").innerHTML = store.draftId
    ? '<span class="stale">⚠ tracking MOCK …' + esc(store.draftId.slice(-6)) + '</span>'
    : "tracking: REAL draft";
  const q = new URLSearchParams();
  if (store.draftId) q.set("draft_id", store.draftId);
  if (store.slot) q.set("slot", store.slot);
  $("logLink").href = "/log" + (store.draftId ? "?draft_id=" + encodeURIComponent(store.draftId) : "");
  try {
    const r = await fetch("/state?" + q, {cache: "no-store"});
    const s = await r.json();
    if (my !== seq) return;  // a newer tick already resolved
    fails = 0; lastOk = Date.now();
    render(s);
  } catch (e) {
    if (my !== seq) return;
    if (++fails >= 2) {
      $("banner").className = "banner err";
      $("banner").innerHTML = `RECONNECTING… <small>dashboard server not answering — the launcher restarts it automatically; if this persists 15s, double-click DRAFT DAY again.</small>`;
      document.title = "⚠ draftkit";
    }
  }
  $("heartbeat").textContent = lastOk ? `updated ${Math.round((Date.now() - lastOk) / 1000)}s ago` : "";
}
tick();
setInterval(tick, 2000);
</script>
</body>
</html>
"""
