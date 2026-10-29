// Evalia prototype interface. The pipeline's output (D) holds proposed findings and the analyses that do not depend on
// decisions. Everything that depends on the evaluator's decisions (points, scores, ranking, the report) is computed here.
"use strict";

const STAGES = [
  { id: "engagement", phase: "Prepare", title: "Engagement" },
  { id: "documents", phase: "Prepare", title: "Tender documents" },
  { id: "framework", phase: "Prepare", title: "Evaluation framework" },
  { id: "receipt", phase: "Open", title: "Receipt and opening", stream: "receipt" },
  { id: "gate", phase: "Evaluate", title: "Responsiveness", stream: "gate" },
  { id: "technical", phase: "Evaluate", title: "Technical", stream: "technical" },
  { id: "commercial", phase: "Evaluate", title: "Commercial", stream: "commercial" },
  { id: "contract", phase: "Evaluate", title: "Contract", stream: "contract" },
  { id: "integrity", phase: "Evaluate", title: "Qualification and integrity", stream: "integrity" },
  { id: "clarifications", phase: "Decide", title: "Clarifications" },
  { id: "consolidation", phase: "Decide", title: "Consolidation and ranking" },
  { id: "award", phase: "Decide", title: "Due diligence and award" },
  { id: "report", phase: "Decide", title: "Evaluation report" },
];
const DEMO = location.hash.includes("demo");
const KEY = "evalia:" + D.context.sha256.slice(0, 16);
const blank = () => ({ stage: 0, signoff: null, decisions: {}, editing: {}, tab: {}, status: {}, clar: {}, ack: false, mode: "client", bidder: 1, recommendation: null, approval: null, resolve: {}, dd: {}, method: "weighted", notices: null });
let state = blank();
try { const saved = JSON.parse(localStorage.getItem(KEY) || "null"); if (saved) state = Object.assign(blank(), saved); } catch { /* storage unavailable */ }
const save = () => { try { localStorage.setItem(KEY, JSON.stringify(state)); } catch { /* storage unavailable */ } };

const $ = (s) => document.querySelector(s);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const usd = (n) => n == null ? "" : "$" + Number(n).toLocaleString("en-US", { minimumFractionDigits: 0, maximumFractionDigits: 0 });
const fmt = (n) => n == null ? "" : (Math.round(n * 100) / 100).toString();
const pct = (x) => (x * 100).toFixed(0) + "%";
const short = (n) => String(n).replace(" (fictional)", "");
const evaluator = () => $("#evaluator").value.trim();
const nowText = () => { const d = new Date(); return `${d.getUTCDate()} ${d.toLocaleString("en-GB", { month: "long", timeZone: "UTC" })} ${d.getUTCFullYear()}, ${d.toISOString().slice(11, 16)} UTC`; };
const NAMES = D.tenderers.map(t => t.name);
const F = D.findings;
const byId = Object.fromEntries(F.map(f => [f.id, f]));
const CRIT = Object.fromEntries(D.framework.criteria.map(c => [c.id, c]));
const STREAM_MAX = Object.fromEntries(D.framework.streams.filter(s => s.scored).map(s => [s.id, s.max]));
const SEV = { critical: ["✕", "Critical"], attention: ["!", "Needs attention"], info: ["✓", "No issue"] };
const DONE = { accept: "Accepted", reject: "Rejected", modify: "Modified", score: "Scored" };
const COLORS = ["var(--p500)", "var(--a600)", "var(--r600)", "var(--gr600)"];
const rank = (s) => ({ info: 0, attention: 1, critical: 2 }[s]);

// --- decisions and scores ---------------------------------------------------------------------------------------------
function finalPoints(f) {
  const d = state.decisions[f.id];
  if (!d) return null;
  if (d.action === "score") return d.points;
  if (f.proposed_points == null) return null;
  if (d.action === "accept") return f.proposed_points;
  if (d.action === "reject") return 0;
  return d.points ?? f.proposed_points;
}
function finalValue(f) {
  const d = state.decisions[f.id];
  if (f.value == null || !d || d.action === "reject") return null;
  return d.action === "modify" && d.value != null ? d.value : f.value;
}
const clamp = (x, max) => Math.max(0, Math.min(x, max));
function criterionPoints(name, cid, proposed = false) {
  const c = CRIT[cid], fs = F.filter(f => f.subject === name && f.criterion === cid);
  let pts = c.base || 0, open = 0;
  for (const f of fs) {
    if (proposed) { if (f.score_max != null) return { pts: null, open: 1 }; pts += f.proposed_points || 0; continue; }
    const p = finalPoints(f);
    if (!state.decisions[f.id]) open++;
    if (p != null) pts += p;
  }
  return { pts: clamp(pts, c.max), open };
}
const statusOf = (name) => state.status[name] || {};
const admitted = (name) => statusOf(name).admitted !== false;
const proposedResponsive = (name) => F.some(f => f.stream === "gate" && f.subject === name && f.severity === "critical") ? "clarify" : "yes";
const responsiveStatus = (name) => statusOf(name).responsive ?? proposedResponsive(name);
const responsive = (name) => responsiveStatus(name) !== "no";
const RULES = D.rules || {};
function techPass(name) {
  const fs = F.filter(f => f.subject === name && f.stream === "technical" && f.criterion);
  if (fs.some(f => !state.decisions[f.id])) return null;
  const tech = ["T1", "T2", "T3", "T4", "T5", "T6"].reduce((a, c) => a + criterionPoints(name, c).pts, 0);
  return tech >= (RULES.technical_pass ?? 0) && criterionPoints(name, "T2").pts >= (RULES.methodology_cutoff ?? 0);
}
const eligible = (name) => admitted(name) && responsive(name) && techPass(name) !== false;
const priceFinding = (name) => F.find(f => f.subject === name && f.criterion === "P1");
function priceScores() {
  const prices = {};
  for (const n of NAMES) { const v = finalValue(priceFinding(n)); if (v != null && eligible(n)) prices[n] = v; }
  const low = Math.min(...Object.values(prices));
  return Object.fromEntries(Object.entries(prices).map(([n, v]) => [n, Math.round(CRIT.P1.max * low / v * 100) / 100]));
}
function streamPoints() {
  const ps = priceScores(), out = {};
  for (const n of NAMES) {
    const tech = ["T1", "T2", "T3", "T4", "T5", "T6"].map(c => criterionPoints(n, c));
    const k = criterionPoints(n, "K1");
    out[n] = { technical: tech.reduce((a, x) => a + x.pts, 0), commercial: ps[n] ?? 0, contract: k.pts,
               open: tech.reduce((a, x) => a + x.open, 0) + k.open + (state.decisions[priceFinding(n).id] ? 0 : 1) };
  }
  return out;
}
const total = (r) => r.technical + r.commercial + r.contract;
function reweight(points, w) {
  return Object.fromEntries(Object.entries(points).map(([n, r]) => [n, Object.keys(w).reduce((a, g) => a + w[g] * r[g] / STREAM_MAX[g], 0)]));
}
const pending = (stream) => F.filter(f => (!stream || f.stream === stream) && !state.decisions[f.id]);
const findingsOf = (stream, name) => F.filter(f => f.stream === stream && (!name || f.subject === name));

// --- layout -----------------------------------------------------------------------------------------------------------
const locked = (i) => i >= 3 && !state.signoff;
function steps() {
  if (state.mode === "bidder") { $("#steps").innerHTML = `<div class="phase">Tenderer profile</div><button aria-current="step"><span class="n">1</span><span>Pre-submission check</span></button>`; return; }
  let html = "", phase = "";
  STAGES.forEach((s, i) => {
    if (s.phase !== phase) { phase = s.phase; html += `<div class="phase">${phase}</div>`; }
    const open = s.stream ? pending(s.stream).length : 0;
    html += `<button ${locked(i) ? "disabled" : ""} ${i === state.stage ? 'aria-current="step"' : ""} data-step="${i}"><span class="n">${i + 1}</span><span>${esc(s.title)}${locked(i) ? " 🔒" : ""}</span>${s.stream && !locked(i) ? `<span class="badge">${open ? open + " open" : "✓"}</span>` : ""}</button>`;
  });
  $("#steps").innerHTML = html;
  $("#steps").querySelectorAll("[data-step]").forEach(b => b.onclick = () => go(+b.dataset.step));
}
const intro = (title, text) => `<div class="intro"><h1>${title}</h1><p>${text}</p></div>`;
const next = (i, label) => `<div class="actions"><button class="btn" onclick="go(${i})">${label}</button></div>`;
const pageLink = (doc, page, quote) => `<button class="link" data-page="${esc(doc)}|${page}" data-quote="${esc(quote || "")}">p. ${page}</button>`;
const tick = (ok) => ok ? '<span class="pill ok">✓ Yes</span>' : '<span class="pill bad">✕ No</span>';

// --- stages: prepare --------------------------------------------------------------------------------------------------
const V = {};
V.engagement = () => intro("Engagement", `Evaluation of ${esc(D.context.title)}, request for proposal ${esc(D.context.reference)}, for ${esc(D.context.employer)}.`)
  + `<div class="grid2"><div class="card"><div class="card-head"><h2>Who is evaluating</h2></div>
      <dl class="kv"><dt>Profile</dt><dd>Client evaluating tenders</dd><dt>Client</dt><dd>${esc(D.context.employer)}</dd><dt>Evaluator</dt><dd>${esc(evaluator() || "not named")}</dd><dt>Authority</dt><dd>The client's panel decides every finding, score and recommendation</dd></dl></div>
    <div class="card"><div class="card-head"><h2>Where the data goes</h2></div>
      <dl class="kv"><dt>Documents</dt><dd>Read on this machine</dd><dt>AI models</dt><dd>None used in this run; any model must be permitted by the engagement's residency policy, or the call is refused</dd><dt>Isolation</dt><dd>Nothing passes to or from any other engagement</dd><dt>Evalia staff</dt><dd>No access</dd></dl></div></div>
    <div class="card"><div class="card-head"><h2>Documents in this engagement</h2><span class="aside">fingerprinted on loading</span></div>
      <div class="scroll"><table><thead><tr><th>Document</th><th class="num">Pages</th><th>SHA-256</th></tr></thead><tbody>
      <tr><td>Request for proposal ${esc(D.context.reference)}</td><td class="num">${D.context.pages}</td><td class="hash tiny">${D.context.sha256.slice(0, 16)}…</td></tr>
      ${D.tenderers.map(t => `<tr><td>${esc(short(t.name))} <span class="tiny">(sealed until opening)</span></td><td class="num">${t.pages}</td><td class="hash tiny">${t.sha256.slice(0, 16)}…</td></tr>`).join("")}</tbody></table></div></div>
    <div class="card"><div class="card-head"><h2>How the evaluation runs</h2></div>
      <ul class="ticks"><li>Evalia reads the request for proposal and proposes the framework; the client signs it off before any tender is opened.</li><li>Tenders are opened and checked for responsiveness, then evaluated stream by stream: technical, commercial, contract and integrity.</li><li>Each finding cites its page and quote, and each quote is checked against the page. Arithmetic, thresholds and points are computed by code.</li><li>The evaluator accepts, rejects or modifies every finding, with a reason; clarifications go to tenderers; the panel signs the report.</li></ul></div>
    ${next(1, "Read the tender documents")}`;

V.documents = () => {
  const cats = [...new Set(D.register.map(r => r.category))];
  const ok = D.register.every(r => r.verified);
  return intro("What the tender documents require", "Evalia read the request for proposal and extracted every requirement the evaluation depends on. Each entry quotes its page; each quote was checked against that page.")
    + `<div class="stats"><div class="stat"><b>${D.register.length}</b><span>requirements extracted</span></div><div class="stat ${ok ? "ok" : "bad"}"><b>${D.register.filter(r => r.verified).length}</b><span>quotes found on their page</span></div><div class="stat"><b>${D.framework.requirements.length}</b><span>employer's requirements</span></div></div>`
    + cats.map(c => `<div class="card"><div class="card-head"><h2>${esc(c)}</h2><span class="aside">${D.register.filter(r => r.category === c).length} entries</span></div>
      <div class="scroll"><table><tbody>${D.register.filter(r => r.category === c).map(r => `<tr><td style="width:30%"><strong>${esc(r.key)}</strong></td><td>${esc(r.text)}</td><td class="num">${r.verified ? "✓ " : "✕ "}${pageLink(D.context.doc_id, r.page, r.quote)}</td></tr>`).join("")}</tbody></table></div></div>`).join("")
    + (D.rfp_issues.length ? `<div class="card" style="box-shadow:var(--sh1), inset 4px 0 0 var(--bad)"><div class="card-head"><h2>The document contradicts itself</h2><span class="aside">${D.rfp_issues.length} to resolve before sign-off</span></div>
      <p class="small muted" style="margin:0">The same requirement is stated with different values. Resolve each by addendum before tenders close, or record which value governs; you will be asked at sign-off.</p>
      ${D.rfp_issues.map(i => `<div class="clarify"><b>${esc(i.key)}:</b> ${i.values.map(v => `${esc(v.value)} (${pageLink(D.context.doc_id, v.page, v.quote)}: “${esc(v.quote)}”)`).join(" against ")}</div>`).join("")}</div>` : "")
    + (D.rfp_missing.length ? `<div class="card" style="box-shadow:var(--sh1), inset 4px 0 0 var(--warn)"><div class="card-head"><h2>Cited but not in the dossier</h2><span class="aside">${D.rfp_missing.length} missing</span></div>
      ${D.rfp_missing.map(x => `<div class="clarify"><b>Annex ${esc(x.annex)}, ${esc(x.title)}:</b> listed as ${esc(x.where)}, which the document does not contain (${pageLink(D.context.doc_id, x.page, x.quote)}). Issue it to all tenderers before they price, or the tenders will rest on different assumptions.</div>`).join("")}</div>` : "")
    + `<div class="card"><div class="card-head"><h2>Consistency check</h2><span class="aside">framework against the document</span></div>
      <div class="scroll"><table><thead><tr><th>Stream</th><th class="num">Request for proposal</th><th class="num">Framework</th><th>Consistent</th></tr></thead><tbody>
      ${D.framework.consistency.map(c => `<tr><td>${esc(c.stream)}</td><td class="num">${c.rfp}</td><td class="num">${c.framework}</td><td>${tick(c.match)}</td></tr>`).join("")}</tbody></table></div></div>`
    + next(2, "Review the evaluation framework");
};

V.framework = () => {
  const s = state.signoff, fw = D.framework;
  return intro("Evaluation framework", "Evalia proposes this framework from the request for proposal and the construction pack's defaults. Check it, then sign it off: no tender is opened until you do. In the full product every value is editable before sign-off.")
    + `<div class="card"><div class="card-head"><h2>Streams and weights</h2><span class="aside">100 points for responsive tenders</span></div>
      <div class="stack" style="height:16px">${fw.streams.filter(x => x.scored).map((x, i) => `<span style="width:${x.max}%;background:${COLORS[i]}" title="${esc(x.title)}"></span>`).join("")}</div>
      <div class="legend">${fw.streams.filter(x => x.scored).map((x, i) => `<span><span class="swatch" style="background:${COLORS[i]}"></span>${esc(x.title)} ${x.max}</span>`).join("")}<span>Receipt, responsiveness and integrity: pass, clarify or refer; not scored</span></div></div>
    <div class="card"><div class="card-head"><h2>Criteria and how each is scored</h2></div><div class="scroll"><table><thead><tr><th>Criterion</th><th class="num">Points</th><th>Method</th></tr></thead><tbody>
      ${fw.criteria.map(c => `<tr><td><strong>${c.id}</strong> ${esc(c.title)}</td><td class="num">${c.max}</td><td class="small">${esc(c.method)}</td></tr>`).join("")}</tbody></table></div></div>
    <div class="card"><div class="card-head"><h2>Contract baseline and risk heads</h2><span class="aside">deduction: material ${fw.deduction.material}, minor ${fw.deduction.minor}</span></div><div class="scroll"><table><thead><tr><th>Particular</th><th>Requirement</th><th>Risk head</th><th>Change is</th></tr></thead><tbody>
      ${Object.entries(fw.particulars).map(([k, v]) => { const r = fw.risk_heads[k] || {}; return `<tr><td>${esc(k)}</td><td class="small">${esc(v)}</td><td class="small">${esc(r.head || "")}</td><td>${r.material ? '<span class="pill bad">Material</span>' : '<span class="pill warn">Minor</span>'}</td></tr>`; }).join("")}</tbody></table></div></div>
    <div class="grid2"><div class="card"><div class="card-head"><h2>Thresholds</h2></div><dl class="kv">
      <dt>Rate outlier</dt><dd>${pct(fw.thresholds.rate_outlier)} from the median</dd><dt>Front-loading</dt><dd>over ${pct(fw.thresholds.front_loading_max)} of value in the first ${pct(fw.thresholds.front_loading_share)} of the programme</dd>
      <dt>Identical rates</dt><dd>${fw.thresholds.identical_rates_min} or more items</dd><dt>Litigation</dt><dd>over ${usd(fw.thresholds.litigation_value)}</dd>
      <dt>Abnormally low</dt><dd>below ${pct(fw.thresholds.abnormally_low)} of the estimate</dd><dt>Pre-tender estimate</dt><dd>${usd(fw.pre_tender_estimate)} (optional client input)</dd></dl></div>
    <div class="card"><div class="card-head"><h2>Commercial rules</h2></div><dl class="kv"><dt>Award basis</dt><dd>Combined offer; split award compared</dd><dt>Arithmetic</dt><dd>Lower of stated and corrected totals</dd><dt>Provisional sums</dt><dd>Restored to the Employer's amounts</dd><dt>Sensitivity</dt><dd>${Object.keys(fw.sensitivity).map(esc).join("; ")}</dd></dl></div></div>
    <div class="card"><div class="card-head"><h2>Not assessed by Evalia</h2></div><ul class="ticks docs">${fw.not_assessed.map(x => `<li>${esc(x)}</li>`).join("")}</ul></div>
    ${s ? `<div class="ok-note">Signed off by <strong>${esc(s.by)}</strong> on ${esc(s.at)}. The framework is locked for this evaluation.</div>${next(3, "Open the tenders")}`
        : `${D.rfp_issues.length ? `<div class="card"><div class="card-head"><h2>Resolve the contradictions</h2><span class="aside">required before sign-off</span></div>${D.rfp_issues.map(i => `<div class="statusrow"><div><strong>${esc(i.key)}</strong><div class="tiny">stated as ${i.values.map(v => esc(v.value)).join(" and ")}</div></div><div class="actions"><select data-resolve="${esc(i.key)}"><option value="">Choose the value that governs…</option>${[...new Set(i.values.map(v => v.value))].map(v => `<option ${state.resolve[i.key] === v ? "selected" : ""}>${esc(v)}</option>`).join("")}</select><span class="tiny">confirm it to all tenderers by addendum</span></div></div>`).join("")}</div>` : ""}
        <div class="actions"><button class="btn" id="sign">Sign off the framework</button><span class="small muted">as ${esc(evaluator() || "…")}</span></div><div class="err" id="signerr"></div>`}`;
};

// --- stream stages ----------------------------------------------------------------------------------------------------
function matrix(stream, rows) {
  rows = rows || [...new Set(findingsOf(stream).map(f => f.check))];
  return `<div class="scroll"><table class="matrix"><thead><tr><th>Check</th>${NAMES.map(n => `<th>${esc(short(n))}</th>`).join("")}</tr></thead><tbody>
    ${rows.map(ch => `<tr><td>${esc(ch.replace(/^T\d /, ""))}</td>${NAMES.map(n => {
      const fs = F.filter(f => f.stream === stream && f.check === ch && f.subject === n);
      if (!fs.length) return `<td><span class="cell none">—</span></td>`;
      const worst = fs.reduce((a, f) => rank(f.severity) > rank(a) ? f.severity : a, "info");
      const done = fs.every(f => state.decisions[f.id]);
      return `<td><button class="cell ${worst} ${done ? "done" : ""}" data-jump="${fs[0].id}" title="${esc(fs.map(f => f.title).join("; "))}">${SEV[worst][0]}${fs.length > 1 ? " " + fs.length : ""}</button></td>`;
    }).join("")}</tr>`).join("")}</tbody></table></div>
    <div class="legend"><span>✓ no issue</span><span>! needs attention</span><span>✕ critical</span><span>outlined: every finding decided</span><span>select a cell to open its finding</span></div>`;
}
function findingsBlock(stream) {
  const tab = state.tab[stream] ?? 0, name = NAMES[tab];
  const fs = findingsOf(stream, name).sort((a, b) => (!!state.decisions[a.id] - !!state.decisions[b.id]) || (rank(b.severity) - rank(a.severity)));
  const infos = pending(stream).filter(f => f.severity === "info" && f.score_max == null && f.evidence.every(e => e.verified));
  return `<div class="card-head" style="margin-top:var(--s3)"><h2>Findings to decide</h2><span class="aside">${findingsOf(stream).length - pending(stream).length} of ${findingsOf(stream).length} decided</span></div>
    <div class="actions" style="justify-content:space-between"><div class="segtabs" role="tablist">${NAMES.map((x, i) => {
      const left = findingsOf(stream, x).filter(f => !state.decisions[f.id]).length;
      return `<button role="tab" aria-selected="${i === tab}" data-tab="${stream}|${i}">${esc(short(x))}<span class="count">${left ? left + " open" : "done"}</span></button>`; }).join("")}</div>
      <div class="actions">${infos.length ? `<button class="btn secondary" data-bulk="${stream}">Accept ${infos.length} findings that raise no issue</button>` : ""}
      ${DEMO && pending(stream).length ? `<button class="btn secondary demo" data-demo="${stream}">Demo only: accept the rest</button>` : ""}</div></div>
    ${fs.map(card).join("") || `<div class="card empty"><p class="muted" style="margin:0">No findings in this stream for ${esc(short(name))}.</p></div>`}`;
}
function card(f) {
  const d = state.decisions[f.id], [icon, sev] = SEV[f.severity];
  if (d && !state.editing[f.id]) {
    const p = finalPoints(f), v = finalValue(f);
    return `<article class="finding ${f.severity} collapsed" id="card-${f.id}"><div class="decided"><h3>${icon} ${esc(f.title)}</h3>
      <span class="who">${DONE[d.action]}${p != null ? `, <span class="figure">${fmt(p)}</span> pts` : ""}${v != null && d.action === "modify" ? `, ${usd(v)}` : ""} · <button class="link" data-edit="${f.id}">Change</button></span></div></article>`;
  }
  const scoreOnly = f.score_max != null, choice = d?.action || (scoreOnly ? "score" : "accept");
  if (!d && f.severity === "info" && !scoreOnly && !state.editing[f.id] && f.evidence.every(e => e.verified)) {
    const e = f.evidence[0];
    return `<article class="finding info collapsed" id="card-${f.id}"><div class="decided"><h3>✓ ${esc(f.title)}${f.proposed_points != null ? ` <span class="tiny">${fmt(f.proposed_points)} pts proposed</span>` : ""}</h3>
      <span class="who">${e ? pageLink(e.doc_id, e.page, e.quote) + " · " : ""}<button class="link" data-quick="${f.id}">Accept</button> · <button class="link" data-edit="${f.id}">Review</button></span></div></article>`;
  }
  return `<article class="finding ${f.severity}" id="card-${f.id}">
    <div class="top"><h3>${esc(f.title)}</h3><div class="tags"><span class="tag ${f.severity}">${icon} ${sev}</span><span class="tag basis">${esc(f.basis)}</span>${f.proposed_points != null ? `<span class="tag pts">${fmt(f.proposed_points)} pts proposed</span>` : ""}${scoreOnly ? `<span class="tag pts">evaluator scores 0 to ${f.score_max}</span>` : ""}</div></div>
    <div class="detail">${esc(f.detail)}</div>
    ${f.evidence.map(e => `<div class="quote"><q>${esc(e.quote)}</q><div class="src">${e.verified ? '<span class="ver">✓ Found on the page</span>' : '<span class="nover">✕ Not found on the page</span>'}<span>${esc(short(docName(e.doc_id)))}, page ${e.page}</span>${pageLink(e.doc_id, e.page, e.quote).replace(">p. ", ">View page ")}</div></div>`).join("")}
    ${f.clarify ? `<div class="clarify"><b>Draft clarification:</b> ${esc(f.clarify)}</div>` : ""}
    <div class="tiny">Method: ${esc(f.method)}</div>
    <div class="decide">
      ${scoreOnly ? "" : `<div class="choice" role="group" aria-label="Decision">${["accept", "reject", "modify"].map(a => `<button aria-pressed="${choice === a}" data-act="${a}">${a[0].toUpperCase() + a.slice(1)}</button>`).join("")}</div>`}
      <textarea id="reason-${f.id}" placeholder="${scoreOnly ? "Reason for the score, required" : "Reason, required to reject or modify"}">${esc(d?.reason || "")}</textarea>
      ${scoreOnly ? `<div class="actions small"><label for="pts-${f.id}" class="muted">Score (0 to ${f.score_max})</label><input id="pts-${f.id}" type="number" min="0" max="${f.score_max}" step="0.5" style="width:96px" value="${d?.points ?? ""}"></div>`
        : f.proposed_points != null ? `<div class="actions small"><label for="pts-${f.id}" class="muted">Points if modified</label><input id="pts-${f.id}" type="number" step="0.25" style="width:96px" value="${d?.points ?? f.proposed_points}"></div>`
        : f.value != null ? `<div class="actions small"><label for="val-${f.id}" class="muted">Evaluated price if modified</label><input id="val-${f.id}" type="number" step="1" style="width:160px" value="${d?.value ?? f.value}"></div>` : ""}
      <div class="actions"><button class="btn" data-record="${f.id}">${scoreOnly ? "Record score" : "Record decision"}</button><span class="err" id="err-${f.id}"></span></div>
    </div></article>`;
}
const docName = (doc) => doc === D.context.doc_id ? "Request for proposal" : (D.tenderers.find(t => t.doc_id === doc) || {}).name || doc;

V.receipt = () => intro("Receipt and opening", "The tenders are opened against the portal's receipt log. A late tender is opened only if the panel admits it under the request for proposal's discretion.")
  + `<div class="card"><div class="card-head"><h2>Opening register</h2><span class="aside">deadline ${esc(D.context.deadline_text)}</span></div>
    <div class="scroll"><table><thead><tr><th>Tenderer</th><th>Received</th><th>Status</th><th class="num">Pages</th><th>SHA-256</th></tr></thead><tbody>
    ${D.tenderers.map(t => { const late = t.received > D.context.deadline; return `<tr><td>${esc(short(t.name))}</td><td class="hash tiny">${esc((t.received || "").replace("T", " "))}</td><td>${late ? '<span class="pill bad">✕ Late</span>' : '<span class="pill ok">✓ On time</span>'}</td><td class="num">${t.pages}</td><td class="hash tiny">${t.sha256.slice(0, 16)}…</td></tr>`; }).join("")}</tbody></table></div></div>
  <div class="card"><div class="card-head"><h2>Admission</h2><span class="aside">the panel's decision</span></div>
    ${D.tenderers.filter(t => t.received > D.context.deadline).map(t => statusRow(t.name, "admitted", [["true", "Admit at the Employer's discretion"], ["false", "Do not admit"]], "true")).join("") || '<p class="muted small" style="margin:0">Every tender arrived on time.</p>'}</div>
  ${findingsBlock("receipt")}${next(4, "Check responsiveness")}`;

function statusRow(name, field, options, proposed) {
  const cur = statusOf(name)[field];
  const val = cur === undefined ? proposed : String(cur);
  const needs = val !== proposed && !statusOf(name)[field + "_reason"];
  return `<div class="statusrow"><div><strong>${esc(short(name))}</strong><div class="tiny">Proposed: ${esc(options.find(o => o[0] === proposed)[1])}</div></div>
    <div class="actions" style="align-items:flex-start"><select data-status="${esc(name)}|${field}">${options.map(([v, l]) => `<option value="${v}" ${v === val ? "selected" : ""}>${esc(l)}</option>`).join("")}</select>
    <input type="text" data-sreason="${esc(name)}|${field}" placeholder="Reason, required if you depart from the proposal" value="${esc(statusOf(name)[field + "_reason"] || "")}" style="flex:1;min-width:200px">
    <span class="err">${needs ? "Give a reason for departing from the proposal." : ""}</span></div></div>`;
}

V.gate = () => {
  return intro("Responsiveness", "A tender is evaluated only if it is substantially responsive. Evalia checks signature, authority, validity, completeness, the pricing structure and qualifications outside Form G. The panel decides each tender's status.")
    + `<div class="card"><div class="card-head"><h2>Responsiveness checks</h2></div>${matrix("gate")}</div>
    <div class="card"><div class="card-head"><h2>Status of each tender</h2><span class="aside">non-responsive tenders are not ranked</span></div>
      ${NAMES.filter(admitted).map(n => statusRow(n, "responsive", [["yes", "Responsive"], ["clarify", "Responsive, subject to clarification"], ["no", "Not responsive"]], proposedResponsive(n))).join("")}</div>
    ${findingsBlock("gate")}${next(5, "Evaluate the technical submissions")}`;
};

V.technical = () => {
  const crit = ["T1", "T2", "T3", "T4", "T5", "T6"];
  const reqs = D.framework.requirements;
  return intro("Technical evaluation", "Evalia maps each methodology against the employer's requirements, checks programme, safety record, experience and key personnel, and proposes points where a signed-off rule gives them. Methodology is scored by the evaluator.")
    + `<div class="card"><div class="card-head"><h2>Points by criterion</h2><span class="aside">grey italics: proposed, not yet decided</span></div><div class="scroll"><table><thead><tr><th>Criterion</th><th class="num">Max</th>${NAMES.map(n => `<th class="num">${esc(short(n))}</th>`).join("")}</tr></thead><tbody>
      ${crit.map(c => `<tr><td>${c} ${esc(CRIT[c].title)}</td><td class="num">${CRIT[c].max}</td>${NAMES.map(n => { const r = criterionPoints(n, c), p = criterionPoints(n, c, true); return `<td class="num">${r.open ? `<span class="prop">${p.pts == null ? "evaluator" : fmt(p.pts)}</span>` : fmt(r.pts)}</td>`; }).join("")}</tr>`).join("")}
      <tr><td><strong>Technical</strong></td><td class="num"><strong>${STREAM_MAX.technical}</strong></td>${NAMES.map(n => `<td class="num"><strong>${fmt(streamPoints()[n].technical)}</strong></td>`).join("")}</tr></tbody></table></div></div>
    <div class="card"><div class="card-head"><h2>Employer's requirements in each methodology</h2><span class="aside">prototype keyword matcher; a model in production</span></div><div class="scroll"><table class="matrix"><thead><tr><th>Requirement</th>${NAMES.map(n => `<th>${esc(short(n))}</th>`).join("")}</tr></thead><tbody>
      ${reqs.map(r => `<tr><td><strong>${esc(r.ref)}</strong> <span class="small muted">${esc(r.text)}</span></td>${NAMES.map(n => { const st = D.coverage[n][r.ref]; const f = F.find(x => x.subject === n && x.check === "T2 " + r.ref); const cls = st === "addressed" ? "info" : st === "contradicted" ? "critical" : "attention"; return `<td><button class="cell ${cls} ${state.decisions[f.id] ? "done" : ""}" data-jump="${f.id}" title="${esc(st)}">${SEV[cls][0]}</button></td>`; }).join("")}</tr>`).join("")}</tbody></table></div>
      <div class="legend"><span>✓ addressed</span><span>! not demonstrated</span><span>✕ conflicts with the requirement</span></div></div>
    <div class="card"><div class="card-head"><h2>All technical checks</h2></div>${matrix("technical")}</div>
    ${findingsBlock("technical")}${next(6, "Evaluate the prices")}`;
};

function cashChart() {
  const W = 640, H = 220, P = 32, series = Object.entries(D.cashflow);
  const maxM = Math.max(...series.map(([, s]) => s.length));
  const x = (i) => P + (W - 2 * P) * i / maxM, y = (v) => H - P - (H - 2 * P) * v;
  const lines = series.map(([n, s], k) => { let c = 0; const tot = s.reduce((a, b) => a + b, 0); const pts = [[x(0), y(0)], ...s.map((v, i) => { c += v; return [x(i + 1), y(c / tot)]; })];
    return `<polyline fill="none" stroke="${COLORS[k]}" stroke-width="2.5" points="${pts.map(p => p.join(",")).join(" ")}"><title>${esc(short(n))}</title></polyline>`; }).join("");
  const grid = [0, .25, .5, .75, 1].map(v => `<line x1="${P}" x2="${W - P}" y1="${y(v)}" y2="${y(v)}" stroke="var(--line)"/><text x="${P - 6}" y="${y(v) + 4}" text-anchor="end">${v * 100}%</text>`).join("");
  const months = Array.from({ length: maxM + 1 }, (_, i) => i % 2 === 0 ? `<text x="${x(i)}" y="${H - P + 16}" text-anchor="middle">${i}</text>` : "").join("");
  return `<div class="chart"><svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Cumulative cash flow by month">${grid}${months}${lines}</svg></div>
    <div class="legend">${series.map(([n], k) => `<span><span class="swatch" style="background:${COLORS[k]}"></span>${esc(short(n))}</span>`).join("")}<span>cumulative share of value by month</span></div>`;
}
V.commercial = () => {
  const C = D.commercial, ps = priceScores();
  const items = Object.keys(D.outliers);
  const same = new Set(D.identical.flatMap(p => p.items.flatMap(i => [p.a + "|" + i, p.b + "|" + i])));
  return intro("Commercial evaluation", "Evalia checks the arithmetic under the tender's own correction rule, restores provisional sums, compares rates across tenders, reads the cash flow and computes the evaluated price. Price points follow from the evaluated prices you confirm.")
    + `<div class="card"><div class="card-head"><h2>From stated offer to evaluated price</h2><span class="aside">combined offer basis</span></div><div class="scroll"><table><thead><tr><th></th>${NAMES.map(n => `<th class="num">${esc(short(n))}</th>`).join("")}</tr></thead><tbody>
      <tr><td>Lot A as stated</td>${NAMES.map(n => `<td class="num">${usd(C[n].lots.A.stated)}</td>`).join("")}</tr>
      <tr><td>Lot B as stated</td>${NAMES.map(n => `<td class="num">${usd(C[n].lots.B.stated)}</td>`).join("")}</tr>
      <tr><td>Discount for both lots</td>${NAMES.map(n => `<td class="num">${C[n].discount_pct}%</td>`).join("")}</tr>
      <tr><td>Combined offer${RULES.words_prevail ? ", words prevailing" : " as stated"}</td>${NAMES.map(n => `<td class="num">${usd(C[n].combined_stated)}</td>`).join("")}</tr>
      <tr><td>Arithmetically corrected</td>${NAMES.map(n => `<td class="num">${usd(C[n].combined_corrected)}</td>`).join("")}</tr>
      <tr><td>Provisional sums restored</td>${NAMES.map(n => `<td class="num">${C[n].normalisation ? "+" + usd(C[n].normalisation) : "—"}</td>`).join("")}</tr>
      <tr><td><strong>Evaluated price</strong></td>${NAMES.map(n => `<td class="num"><strong>${usd(C[n].evaluated)}</strong></td>`).join("")}</tr>
      ${RULES.preference_pct ? `<tr><td>For comparison: ${RULES.preference_pct}% added outside the ${esc(RULES.home_state)}</td>${NAMES.map(n => `<td class="num">${C[n].preference ? usd(C[n].comparison) : "—"}</td>`).join("")}</tr>` : ""}
      <tr><td>Against the estimate of ${usd(D.framework.pre_tender_estimate)}</td>${NAMES.map(n => { const r = C[n].evaluated / D.framework.pre_tender_estimate - 1; return `<td class="num">${r > 0 ? "+" : ""}${(r * 100).toFixed(1)}%</td>`; }).join("")}</tr>
      <tr><td>Price points (of ${CRIT.P1.max})</td>${NAMES.map(n => `<td class="num">${ps[n] != null ? `<strong>${fmt(ps[n])}</strong>` : '<span class="prop">after decision</span>'}</td>`).join("")}</tr></tbody></table></div></div>
    <div class="card"><div class="card-head"><h2>Unit rates against the median</h2><span class="aside">tinted: more than ${pct(D.framework.thresholds.rate_outlier)} from the median; red outline: identical to another tender</span></div><div class="scroll"><table><thead><tr><th>Item</th>${NAMES.map(n => `<th class="num">${esc(short(n))}</th>`).join("")}</tr></thead><tbody>
      ${items.map(it => `<tr><td>${esc(it)}</td>${NAMES.map(n => { const dv = D.outliers[it][n]; if (dv == null) return "<td></td>"; const cls = dv > D.framework.thresholds.rate_outlier ? "hi" : dv < -D.framework.thresholds.rate_outlier ? "lo" : ""; return `<td class="num heat ${cls} ${same.has(n + "|" + it) ? "same" : ""}">${dv > 0 ? "+" : ""}${(dv * 100).toFixed(0)}%</td>`; }).join("")}</tr>`).join("")}</tbody></table></div></div>
    <div class="grid2"><div class="card"><div class="card-head"><h2>Cash flow profile</h2></div>${cashChart()}</div>
      <div class="card"><div class="card-head"><h2>Award basis</h2><span class="aside">lots against the combined offer</span></div>
        <dl class="kv"><dt>Cheapest split</dt><dd>${Object.entries(D.award.split).map(([l, n]) => `Lot ${l}: ${esc(short(n))}`).join("; ")}, ${usd(D.award.split_cost)}</dd>
        <dt>Cheapest combined</dt><dd>${esc(short(D.award.combined))}, ${usd(D.award.combined_cost)}</dd>
        <dt>Difference</dt><dd>${D.award.split_cost > D.award.combined_cost ? `A split award would cost ${usd(D.award.split_cost - D.award.combined_cost)} more than the best combined offer` : `A split award would save ${usd(D.award.combined_cost - D.award.split_cost)}`}</dd></dl>
        <p class="tiny" style="margin:0">Prices only, with provisional sums restored; technical and contract points are in the consolidation.</p></div></div>
    <div class="card"><div class="card-head"><h2>All commercial checks</h2></div>${matrix("commercial")}</div>
    ${findingsBlock("commercial")}${next(7, "Review contract deviations")}`;
};

V.contract = () => intro("Contract deviations", "Each change a tenderer proposes in Form G is set against the contract particulars, assigned to a risk head and, where it is a number, quantified at the evaluated price. Whether a change is acceptable is for the client's advisers; Evalia proposes the deduction the framework gives.")
  + `<div class="card"><div class="card-head"><h2>Deviations register</h2><span class="aside">${D.deviations.length} declared</span></div><div class="scroll"><table><thead><tr><th>Tenderer</th><th>Particular</th><th>Requirement</th><th>Proposed</th><th>Risk head</th><th></th></tr></thead><tbody>
    ${D.deviations.map(d => `<tr><td>${esc(short(d.tenderer))}</td><td>${esc(d.particular)}</td><td class="small">${esc(d.requirement)}</td><td class="small"><strong>${esc(d.proposed)}</strong></td><td class="small">${esc(d.head)}</td><td>${d.material ? '<span class="pill bad">Material</span>' : '<span class="pill warn">Minor</span>'} ${pageLink(D.tenderers.find(t => t.name === d.tenderer).doc_id, d.page, d.quote)}</td></tr>`).join("")}</tbody></table></div></div>
  <div class="card"><div class="card-head"><h2>Contract points</h2><span class="aside">10 less confirmed deductions</span></div><div class="scroll"><table><thead><tr>${NAMES.map(n => `<th class="num">${esc(short(n))}</th>`).join("")}</tr></thead><tbody><tr>${NAMES.map(n => { const r = criterionPoints(n, "K1"), p = criterionPoints(n, "K1", true); return `<td class="num">${r.open ? `<span class="prop">${fmt(p.pts)}</span>` : `<strong>${fmt(r.pts)}</strong>`}</td>`; }).join("")}</tr></tbody></table></div></div>
  ${findingsBlock("contract")}${next(8, "Run the integrity checks")}`;

V.integrity = () => intro("Integrity and due diligence", "Disclosures are checked against the framework's thresholds, and the tenders are compared with each other for indicators such as identical rates or shared subcontractors. Indicators go to the procurement integrity process; they are not findings of wrongdoing.")
  + `<div class="card"><div class="card-head"><h2>Cross-tender indicators</h2></div>
    ${D.identical.map(p => `<div class="clarify"><b>${esc(short(p.a))} and ${esc(short(p.b))}:</b> identical unit rates on ${p.items.length} items (${esc(p.items.join(", "))}).</div>`).join("") || '<p class="muted small" style="margin:0">No identical rates found.</p>'}
    ${(D.owners || []).map(o => `<div class="clarify"><b>${esc(short(o.a))} and ${esc(short(o.b))}:</b> both part-owned by ${esc(short(o.owner))}.</div>`).join("")}
    ${matrix("integrity")}</div>
  ${findingsBlock("integrity")}${next(9, "Prepare clarifications")}`;

// --- decide -----------------------------------------------------------------------------------------------------------
const clarItems = (name) => F.filter(f => f.subject === name && f.clarify && state.decisions[f.id]?.action !== "reject" && eligible(name) && admitted(name));
function letter(name) {
  const qs = clarItems(name).filter(f => (state.clar[f.id] || {}).include !== false);
  return `To: ${short(name)}\nRequest for Proposal ${D.context.reference}: request for clarification\n\nPlease respond to the following within five working days. Clarifications may not change the substance or price of your tender.\n\n`
    + qs.map((f, i) => `${i + 1}. ${f.clarify}`).join("\n\n") + `\n\n${evaluator() || "[Evaluator]"}\nfor ${short(D.context.employer)}`;
}
V.clarifications = () => {
  const all = NAMES.flatMap(clarItems);
  return intro("Clarifications", "Evalia drafts a clarification question for each finding that should be put to a tenderer. Choose which to send, record the answers, and revisit the findings they affect.")
    + `<div class="stats"><div class="stat"><b>${all.length}</b><span>draft questions</span></div><div class="stat"><b>${all.filter(f => (state.clar[f.id] || {}).status === "Sent").length}</b><span>sent</span></div><div class="stat ok"><b>${all.filter(f => (state.clar[f.id] || {}).status === "Answered").length}</b><span>answered</span></div></div>`
    + NAMES.filter(n => clarItems(n).length).map(n => `<div class="card"><div class="card-head"><h2>${esc(short(n))}</h2><span class="aside">${clarItems(n).length} questions</span></div>
      ${clarItems(n).map(f => { const c = state.clar[f.id] || {}; return `<div class="statusrow"><div><label class="small"><input type="checkbox" data-cinc="${f.id}" ${c.include === false ? "" : "checked"}> Include</label><div class="tiny">${esc(f.title)}</div></div>
        <div style="display:flex;flex-direction:column;gap:var(--s2)"><div class="small">${esc(f.clarify)}</div><div class="actions"><select data-cstat="${f.id}">${["Draft", "Sent", "Answered"].map(s => `<option ${s === (c.status || "Draft") ? "selected" : ""}>${s}</option>`).join("")}</select>
        ${c.status === "Answered" ? `<input type="text" data-cans="${f.id}" placeholder="Tenderer's answer" value="${esc(c.answer || "")}" style="flex:1;min-width:200px"><button class="link" data-edit="${f.id}" data-goto="${STAGES.findIndex(s => s.stream === f.stream)}">Revisit finding</button>` : ""}</div></div></div>`; }).join("")}
      <details><summary>Clarification letter</summary><div class="letter">${esc(letter(n))}</div></details>
      <div class="actions"><button class="btn secondary" data-copyletter="${esc(n)}">Copy letter</button><span class="small muted" data-copied="${esc(n)}"></span></div></div>`).join("")
    + next(10, "Consolidate the scores");
};

V.consolidation = () => {
  const P = streamPoints(), open = pending().length;
  const ranked = NAMES.filter(eligible).sort((a, b) => total(P[b]) - total(P[a]));
  const scen = Object.entries(D.framework.sensitivity).map(([name, w]) => { const t = reweight(Object.fromEntries(ranked.map(n => [n, P[n]])), w); return [name, Object.keys(t).sort((a, b) => t[b] - t[a]), t]; });
  const stable = scen.every(s => s[1][0] === scen[0][1][0]);
  const lowest = ranked.slice().sort((a, b) => D.commercial[a].comparison - D.commercial[b].comparison)[0];
  return intro("Consolidation and ranking", "Points come only from decided findings, under the framework signed off before opening. Tenders that were not admitted or not responsive are not ranked.")
    + (open ? `<div class="notice" style="margin:0">${open} findings are still undecided. They carry no points, so this ranking is provisional.</div>` : "")
    + `<div class="card"><div class="card-head"><h2>Scores</h2><span class="aside">out of 100</span></div><div class="scroll"><table><thead><tr><th>Tenderer</th><th>Status</th><th class="num">Technical</th><th class="num">Commercial</th><th class="num">Contract</th><th class="num">Total</th><th class="num">Rank</th></tr></thead><tbody>
      ${NAMES.map(n => { const r = P[n], el = eligible(n); return `<tr class="${el ? "" : "excluded"}"><td>${esc(short(n))}</td><td>${!admitted(n) ? '<span class="pill bad">Not admitted</span>' : !responsive(n) ? '<span class="pill bad">Not responsive</span>' : techPass(n) === false ? '<span class="pill bad">Below technical threshold</span>' : responsiveStatus(n) === "clarify" ? '<span class="pill warn">Subject to clarification</span>' : '<span class="pill ok">Responsive</span>'}</td>
        <td class="num">${fmt(r.technical)}</td><td class="num">${fmt(r.commercial)}</td><td class="num">${fmt(r.contract)}</td><td class="num"><strong>${el ? fmt(total(r)) : "—"}</strong></td><td class="num">${el ? ranked.indexOf(n) + 1 : "—"}</td></tr>`; }).join("")}</tbody></table></div>
      <div class="bars">${ranked.map(n => `<div class="rankbar"><span>${esc(short(n))}</span><div class="stack">${["technical", "commercial", "contract"].map((g, i) => `<span style="width:${P[n][g]}%;background:${COLORS[i]}"></span>`).join("")}</div><span class="num">${fmt(total(P[n]))}</span></div>`).join("")}</div>
      <div class="legend">${["Technical", "Commercial", "Contract"].map((g, i) => `<span><span class="swatch" style="background:${COLORS[i]}"></span>${g}</span>`).join("")}</div></div>
    <div class="card"><div class="card-head"><h2>Sensitivity to the weights</h2><span class="aside">${stable ? "first place does not change" : "first place depends on the weights"}</span></div><div class="scroll"><table><thead><tr><th>Weighting</th><th>First</th><th>Second</th><th>Third</th></tr></thead><tbody>
      ${scen.map(([name, order, t]) => `<tr><td>${esc(name)}</td>${[0, 1, 2].map(i => `<td>${order[i] ? `${esc(short(order[i]))} <span class="tiny">${fmt(t[order[i]])}</span>` : ""}</td>`).join("")}</tr>`).join("")}</tbody></table></div>
      <p class="small muted" style="margin:0">${ranked[0] && lowest && ranked[0] !== lowest ? `The highest-scoring tender is not the lowest-priced: ${esc(short(lowest))} has the lowest evaluated price.` : "The highest-scoring tender is also the lowest-priced."}</p></div>
    <div class="card"><div class="card-head"><h2>Award method</h2><span class="aside">same decisions, different rules</span></div>
      <div class="scroll"><table><thead><tr><th>Method</th><th>Preferred tenderer</th><th>Basis</th></tr></thead><tbody>
      <tr><td>Weighted score, as published${state.method === "weighted" ? " <span class=\"pill ok\">in use</span>" : ""}</td><td>${ranked[0] ? esc(short(ranked[0])) : "—"}</td><td class="small">${ranked[0] ? fmt(total(P[ranked[0]])) + " of 100 points" : ""}</td></tr>
      <tr><td>Lowest evaluated price among technically compliant tenders</td><td>${lowest ? esc(short(lowest)) : "—"}</td><td class="small">${lowest ? usd(D.commercial[lowest].comparison) + " for comparison" : ""}</td></tr></tbody></table></div>
      <p class="small muted" style="margin:0">The request for proposal fixes the method; the comparison shows the panel how much the choice matters. Tenders below the technical threshold of ${RULES.technical_pass} points (${RULES.methodology_cutoff} for methodology) are excluded under both.</p></div>
    ${next(11, "Due diligence and award")}`;
};

V.award = () => {
  const P = streamPoints(), ranked = NAMES.filter(eligible).sort((a, b) => total(P[b]) - total(P[a])), top = ranked[0];
  if (!top) return intro("Due diligence and award", "No tender is eligible for award.");
  const done = D.framework.due_diligence.filter((_, i) => (state.dd[i] || {}).ok).length;
  const reason = (n) => !admitted(n) ? "it was not admitted, having been received after the deadline" : !responsive(n) ? "it was not substantially responsive" : techPass(n) === false ? `it scored below the technical threshold of ${RULES.technical_pass} points` : `it ranked ${ranked.indexOf(n) + 1} of ${ranked.length}, with ${fmt(total(P[n]))} points against ${fmt(total(P[top]))}`;
  const until = (() => { if (!state.notices) return null; const d = new Date(state.notices.iso); d.setUTCDate(d.getUTCDate() + (RULES.standstill_days || 0)); return `${d.getUTCDate()} ${d.toLocaleString("en-GB", { month: "long", timeZone: "UTC" })} ${d.getUTCFullYear()}`; })();
  return intro("Due diligence and award", `Before award, the panel verifies what the evaluation relied on for the preferred tenderer, ${esc(short(top)).replace(/\.$/, "")}. Then every tenderer is notified, and the contract is not signed until the standstill period of ${RULES.standstill_days} days has passed.`)
    + `<div class="card"><div class="card-head"><h2>Due diligence on ${esc(short(top))}</h2><span class="aside">${done} of ${D.framework.due_diligence.length} confirmed</span></div>
      ${D.framework.due_diligence.map((item, i) => { const r = state.dd[i] || {}; return `<div class="statusrow"><label class="small"><input type="checkbox" data-dd="${i}" ${r.ok ? "checked" : ""}> ${esc(item)}</label><input type="text" data-ddnote="${i}" placeholder="Note or reference" value="${esc(r.note || "")}"></div>`; }).join("")}</div>
    ${RULES.negotiation === false ? `<div class="notice" style="margin:0">The request for proposal rules out negotiation: the award is made on the tender as evaluated, with clarifications only.</div>` : ""}
    <div class="card"><div class="card-head"><h2>Award notices</h2><span class="aside">${state.notices ? `issued ${esc(state.notices.at)}` : "drafts"}</span></div>
      ${NAMES.map(n => `<details><summary>${esc(short(n))}: ${n === top ? "preferred tenderer" : "unsuccessful"}</summary><div class="letter">${esc(n === top
        ? `To: ${short(n)}\n\nThe Employer intends to award the Contract for ${D.context.title} to you, at your Combined Offer, subject to the standstill period of ${RULES.standstill_days} days${until ? ", ending " + until : ""}. This notice is not acceptance; the Contract is formed only on signature.`
        : `To: ${short(n)}\n\nThe Employer intends to award the Contract for ${D.context.title} to ${short(top)}. Your tender was not successful because ${reason(n)}. The Contract will not be signed before the end of the standstill period of ${RULES.standstill_days} days${until ? ", ending " + until : ""}. You may ask for a debriefing within that period.`)}</div></details>`).join("")}
      ${state.notices ? `<div class="ok-note">Notices recorded as issued on ${esc(state.notices.at)}. Standstill ends ${esc(until)}; signature may follow.</div>`
        : `<div class="actions"><button class="btn" id="issue" ${done < D.framework.due_diligence.length ? "disabled" : ""}>Record the notices as issued</button><span class="small muted">${done < D.framework.due_diligence.length ? "Complete the due diligence first." : ""}</span></div>`}</div>
    ${next(12, "Draft the evaluation report")}`;
};

V.report = () => {
  const open = pending().length;
  if (open) return intro("Evaluation report", "") + `<div class="card empty"><div class="glyph">▤</div><h2 style="margin:0;font-size:var(--t18)">${open} findings still need a decision</h2><p class="muted" style="margin:0;max-width:48ch">The report is built only from decided findings. Finish the review in each stage; the step list shows what is open.</p></div>`;
  const P = streamPoints(), ranked = NAMES.filter(eligible).sort((a, b) => total(P[b]) - total(P[a]));
  if (state.recommendation == null) state.recommendation = ranked[0] ? `The panel recommends award of the combined offer to ${short(ranked[0])}, the highest-scoring responsive tender at ${fmt(total(P[ranked[0]]))} points, subject to satisfactory answers to the outstanding clarifications.` : "";
  return intro("Evaluation report", "A draft for the evaluation panel, built from the decided findings. The recommendation is the panel's: edit it, then the panel chair approves the report.")
    + `<div class="card"><label class="actions small" for="ack" style="gap:var(--s2)"><input type="checkbox" id="ack" ${state.ack ? "checked" : ""}> I understand that AI-assisted findings can be wrong, and I have reviewed every finding.</label></div>
    ${state.ack ? `<div class="card"><div class="card-head"><h2>Recommendation</h2><span class="aside">the panel's words</span></div><textarea id="recommendation" style="min-height:96px">${esc(state.recommendation)}</textarea>
      ${state.approval ? `<div class="ok-note">Approved by <strong>${esc(state.approval.by)}</strong>, panel chair, on ${esc(state.approval.at)}.</div>`
        : `<div class="actions"><input type="text" id="chair" placeholder="Panel chair's name" style="max-width:260px"><button class="btn" id="approve">Approve the report</button><span class="err" id="apperr"></span></div>`}</div>
    <div class="card">${reportHTML(P, ranked)}<div class="actions"><button class="btn secondary" id="copymd">Copy as Markdown</button><button class="btn secondary" id="savejson">Download the decision record</button><span class="small muted" id="copied"></span></div></div>` : ""}`;
};
function reportHTML(P, ranked) {
  const log = Object.entries(state.decisions).map(([id, d]) => ({ id, ...d })).sort((a, b) => a.at.localeCompare(b.at));
  const section = (stream, title) => `<h3>${title}</h3>` + NAMES.map(n => { const fs = findingsOf(stream, n).filter(f => f.severity !== "info" || state.decisions[f.id].action !== "accept"); return fs.length ? `<p style="margin:0"><strong>${esc(short(n))}</strong></p><ul>${fs.map(f => { const d = state.decisions[f.id]; return `<li>${esc(f.title)}. <span class="tiny">(${esc(f.basis)}; ${DONE[d.action].toLowerCase()}${d.reason ? ": " + esc(d.reason) : ""})</span>${f.evidence.slice(0, 1).map(e => `<div class="q">p. ${e.page}: “${esc(e.quote)}”</div>`).join("")}</li>`; }).join("")}</ul>` : ""; }).join("");
  return `<div class="report"><div class="eyebrow">Draft for the evaluation panel · ${esc(D.context.reference)}</div>
    <p style="margin:0">Evalia proposed the findings; ${esc(evaluator())} decided every one. Points are computed by code from those decisions under the framework signed off by ${esc(state.signoff.by)} on ${esc(state.signoff.at)}, before any tender was opened. The panel is responsible for the evaluation and any award.</p>
    <h3>Recommendation</h3><p style="margin:0">${esc(state.recommendation)}</p>
    <h3>Ranking</h3><div class="scroll"><table><thead><tr><th>Tenderer</th><th class="num">Technical</th><th class="num">Commercial</th><th class="num">Contract</th><th class="num">Total</th></tr></thead><tbody>${ranked.map(n => `<tr><td>${esc(short(n))}</td><td class="num">${fmt(P[n].technical)}</td><td class="num">${fmt(P[n].commercial)}</td><td class="num">${fmt(P[n].contract)}</td><td class="num"><strong>${fmt(total(P[n]))}</strong></td></tr>`).join("")}</tbody></table></div>
    ${NAMES.filter(n => !eligible(n)).map(n => `<p class="small" style="margin:0">${esc(short(n))}: ${!admitted(n) ? "not admitted" : "not responsive"}${statusOf(n)[!admitted(n) ? "admitted_reason" : "responsive_reason"] ? ": " + esc(statusOf(n)[!admitted(n) ? "admitted_reason" : "responsive_reason"]) : ""}.</p>`).join("")}
    ${section("receipt", "Receipt")}${section("gate", "Responsiveness")}${section("technical", "Technical")}${section("commercial", "Commercial")}${section("contract", "Contract")}${section("integrity", "Integrity")}
    <h3>Tender documents</h3><ul>${D.rfp_missing.map(x => `<li>Annex ${esc(x.annex)}, ${esc(x.title)}, is cited but was not in the dossier.</li>`).join("")}${D.rfp_issues.map(i => `<li>${esc(i.key)} was stated as ${i.values.map(v => esc(v.value)).join(" and ")}; the panel recorded ${esc(state.resolve[i.key] || "no decision")} as governing.</li>`).join("") || "<li>No contradictions found.</li>"}</ul>
    <h3>Due diligence</h3><ul>${D.framework.due_diligence.map((item, i) => `<li>${(state.dd[i] || {}).ok ? "✓" : "✕ Not confirmed:"} ${esc(item)}${(state.dd[i] || {}).note ? ` <span class="tiny">(${esc(state.dd[i].note)})</span>` : ""}</li>`).join("")}</ul>
    <p class="small" style="margin:0">${state.notices ? `Award notices issued on ${esc(state.notices.at)}; standstill of ${RULES.standstill_days} days.` : "Award notices not yet issued."}</p>
    <h3>Clarifications</h3><ul>${NAMES.flatMap(clarItems).filter(f => (state.clar[f.id] || {}).include !== false).map(f => { const c = state.clar[f.id] || {}; return `<li>${esc(short(f.subject))}: ${esc(f.clarify)} <span class="tiny">(${esc(c.status || "Draft")}${c.answer ? "; answer: " + esc(c.answer) : ""})</span></li>`; }).join("")}</ul>
    <h3>Decision log</h3><div class="scroll"><table><thead><tr><th>Time (UTC)</th><th>Finding</th><th>Decision</th><th class="num">Points</th></tr></thead><tbody>${log.map(d => `<tr><td class="hash tiny">${esc(d.at.slice(11, 19))}</td><td>${esc(short(byId[d.id].subject))}: ${esc(byId[d.id].title)}${d.reason ? `<div class="tiny">${esc(d.reason)}</div>` : ""}</td><td>${DONE[d.action]}</td><td class="num">${fmt(finalPoints(byId[d.id]))}</td></tr>`).join("")}</tbody></table></div>
    <h3>Not assessed</h3><ul>${D.framework.not_assessed.map(x => `<li>${esc(x)}</li>`).join("")}</ul>
    <h3>Method</h3><ul><li>Every quote was checked against the page it cites.</li><li>Arithmetic, thresholds, points and ranking were computed by code, never by a model.</li><li>Methods used: ${esc([...new Set(F.map(f => f.method))].join("; "))}.</li><li>The evaluator acknowledged that AI-assisted findings can be wrong before producing this draft.</li></ul></div>`;
}
function markdown() {
  const P = streamPoints(), ranked = NAMES.filter(eligible).sort((a, b) => total(P[b]) - total(P[a]));
  const L = [`# Draft evaluation report: ${D.context.title}`, "", `Request for proposal ${D.context.reference}. Framework signed off by ${state.signoff.by} on ${state.signoff.at}.`, "", "## Recommendation", "", state.recommendation, "",
    state.approval ? `Approved by ${state.approval.by}, panel chair, on ${state.approval.at}.` : "Not yet approved by the panel chair.", "", "## Ranking", "", "| Tenderer | Technical | Commercial | Contract | Total |", "|---|---:|---:|---:|---:|"];
  for (const n of ranked) L.push(`| ${n} | ${fmt(P[n].technical)} | ${fmt(P[n].commercial)} | ${fmt(P[n].contract)} | ${fmt(total(P[n]))} |`);
  L.push("", "## Findings");
  for (const f of F) { const d = state.decisions[f.id]; L.push("", `- **${f.subject}, ${f.stream}: ${f.title}** (${f.basis}; ${d.action}${d.reason ? ": " + d.reason : ""})`, `  ${f.detail}`); for (const e of f.evidence) L.push(`  - p. ${e.page}: "${e.quote}"`); }
  return L.join("\n");
}

// --- tenderer profile -------------------------------------------------------------------------------------------------
const OWN_ONLY = new Set(["Identical rates", "Shared ownership", "One tender per tenderer", "Letter of authority at opening", "Shared subcontractors", "Rate outliers", "Receipt time", "Evaluated price", "Pre-tender estimate", "T2 Methodology score"]);
function bidderView() {
  const name = NAMES[state.bidder];
  const fs = F.filter(f => f.subject === name && !OWN_ONLY.has(f.check) && f.severity !== "info");
  const groups = ["gate", "technical", "commercial", "contract", "integrity"];
  return intro("Pre-submission check", "A tenderer runs the same checks on its own draft before lodging it. This profile reads only the published tender documents and the tenderer's own draft: it never sees another tender, and it does not score.")
    + `<div class="card"><div class="actions"><label for="bsel" class="small muted">Draft tender of</label><select id="bsel">${NAMES.map((n, i) => `<option value="${i}" ${i === state.bidder ? "selected" : ""}>${esc(short(n))}</option>`).join("")}</select></div>
      <div class="stats"><div class="stat bad"><b>${fs.filter(f => f.severity === "critical").length}</b><span>could make the tender non-compliant or cost points</span></div><div class="stat warn"><b>${fs.filter(f => f.severity === "attention").length}</b><span>worth fixing before submission</span></div><div class="stat"><b>${F.filter(f => f.subject === name && !OWN_ONLY.has(f.check) && f.severity === "info").length}</b><span>checks passed</span></div></div></div>`
    + groups.map(g => { const gs = fs.filter(f => f.stream === g); return gs.length ? `<div class="card"><div class="card-head"><h2>${esc(D.framework.streams.find(s => s.id === g).title)}</h2><span class="aside">${gs.length} to fix</span></div>
      ${gs.map(f => `<div class="finding ${f.severity}" style="box-shadow:none;padding:var(--s3) var(--s4)"><h3>${SEV[f.severity][0]} ${esc(f.title)}</h3><div class="detail small">${esc(f.detail)}</div>${f.evidence.slice(0, 1).map(e => `<div class="tiny">Your page ${e.page}: “${esc(e.quote)}”</div>`).join("")}</div>`).join("")}</div>` : ""; }).join("")
    + `<p class="tiny">Not shown in this profile: anything that compares one tender with another (rate outliers, identical rates, shared subcontractors, price points), receipt, and scores.</p>`;
}

// --- events -----------------------------------------------------------------------------------------------------------
function go(i) { if (locked(i)) i = 2; state.stage = i; save(); render(); window.scrollTo({ top: 0 }); }
window.go = go;
function showPage(doc, page, quote) {
  const text = (D.pages[doc] || {})[page] || "";
  let html = esc(text);
  const words = (quote || "").split(/\s+/).filter(Boolean).map(w => esc(w).replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));
  if (words.length) html = html.replace(new RegExp(words.join("\\s+")), m => `<mark>${m}</mark>`);
  $("#pagetitle").textContent = `${short(docName(doc))}, page ${page}`;
  $("#pagetext").innerHTML = html; $("#pagebox").hidden = false; $("#closepage").focus();
}
$("#closepage").onclick = () => { $("#pagebox").hidden = true; };
$("#pagebox").onclick = (e) => { if (e.target.id === "pagebox") $("#pagebox").hidden = true; };
document.addEventListener("keydown", (e) => { if (e.key === "Escape") $("#pagebox").hidden = true; });
$("#mode-client").onclick = () => { state.mode = "client"; save(); render(); };
$("#mode-bidder").onclick = () => { state.mode = "bidder"; save(); render(); };
const decide = (id, d) => { state.decisions[id] = { action: d.action, reason: d.reason || "", evaluator: evaluator(), at: new Date().toISOString(), points: d.points ?? null, value: d.value ?? null }; delete state.editing[id]; };

function render() {
  $("#mode-client").setAttribute("aria-pressed", state.mode === "client");
  $("#mode-bidder").setAttribute("aria-pressed", state.mode === "bidder");
  steps();
  $("#main").innerHTML = state.mode === "bidder" ? bidderView() : V[STAGES[state.stage].id]();
  const on = (sel, ev, fn) => document.querySelectorAll(sel).forEach(el => el[ev] = () => fn(el));
  const sign = $("#sign");
  on("[data-resolve]", "onchange", el => { state.resolve[el.dataset.resolve] = el.value; save(); });
  if (sign) sign.onclick = () => { if (!evaluator()) { $("#signerr").textContent = "Enter your name under Evaluator before signing off."; return; }
    if (D.rfp_issues.some(i => !state.resolve[i.key])) { $("#signerr").textContent = "Choose the value that governs for each contradiction first."; return; } state.signoff = { by: evaluator(), at: nowText() }; save(); render(); };
  on("[data-tab]", "onclick", b => { const [s, i] = b.dataset.tab.split("|"); state.tab[s] = +i; save(); render(); });
  on("[data-act]", "onclick", b => b.parentElement.querySelectorAll("button").forEach(x => x.setAttribute("aria-pressed", x === b)));
  on("[data-edit]", "onclick", b => { state.editing[b.dataset.edit] = true; if (b.dataset.goto) { state.stage = +b.dataset.goto; state.tab[byId[b.dataset.edit].stream] = NAMES.indexOf(byId[b.dataset.edit].subject); } save(); render(); if (b.dataset.goto) setTimeout(() => document.getElementById("card-" + b.dataset.edit)?.scrollIntoView({ block: "center" }), 0); });
  on("[data-jump]", "onclick", b => { const f = byId[b.dataset.jump]; state.tab[f.stream] = NAMES.indexOf(f.subject); state.editing[f.id] = !!state.decisions[f.id] && state.editing[f.id]; save(); render(); document.getElementById("card-" + f.id)?.scrollIntoView({ block: "center", behavior: "smooth" }); });
  on("[data-record]", "onclick", b => {
    const id = b.dataset.record, f = byId[id], err = $(`#err-${id}`);
    const pressed = document.querySelector(`#card-${id} .choice [aria-pressed="true"]`);
    const act = f.score_max != null ? "score" : pressed.dataset.act, reason = $(`#reason-${id}`).value.trim();
    if (!evaluator()) { err.textContent = "Enter your name under Evaluator first."; return; }
    if (act !== "accept" && !reason) { err.textContent = act === "score" ? "Give a reason for the score." : "Give a reason to reject or modify."; return; }
    const pts = $(`#pts-${id}`) ? parseFloat($(`#pts-${id}`).value) : null, val = $(`#val-${id}`) ? parseFloat($(`#val-${id}`).value) : null;
    if (act === "score" && (isNaN(pts) || pts < 0 || pts > f.score_max)) { err.textContent = `Enter a score from 0 to ${f.score_max}.`; return; }
    decide(id, { action: act, reason, points: act === "score" || act === "modify" ? pts : null, value: act === "modify" ? val : null }); save(); render();
  });
  on("[data-quick]", "onclick", b => { if (!evaluator()) return; decide(b.dataset.quick, { action: "accept" }); save(); render(); });
  on("[data-bulk]", "onclick", b => { if (!evaluator()) return; for (const f of pending(b.dataset.bulk).filter(f => f.severity === "info" && f.score_max == null && f.evidence.every(e => e.verified))) decide(f.id, { action: "accept", reason: "Accepted in bulk: verified, no issue raised" }); save(); render(); });
  on("[data-demo]", "onclick", b => { for (const f of pending(b.dataset.demo)) { if (f.score_max != null) { const cov = Object.values(D.coverage[f.subject]); const r = cov.filter(x => x === "addressed").length / cov.length; decide(f.id, { action: "score", reason: "Demo score set from requirement coverage", points: Math.round(f.score_max * r * 2) / 2 }); } else decide(f.id, { action: "accept", reason: f.severity === "info" ? "" : "Demo: accepted as proposed" }); } save(); render(); });
  on("[data-page]", "onclick", b => { const [doc, page] = b.dataset.page.split("|"); showPage(doc, page, b.dataset.quote); });
  on("[data-status]", "onchange", el => { const [n, field] = el.dataset.status.split("|"); state.status[n] = { ...statusOf(n), [field]: field === "admitted" ? el.value === "true" : el.value }; save(); render(); });
  on("[data-sreason]", "onchange", el => { const [n, field] = el.dataset.sreason.split("|"); state.status[n] = { ...statusOf(n), [field + "_reason"]: el.value.trim() }; save(); render(); });
  on("[data-cinc]", "onchange", el => { state.clar[el.dataset.cinc] = { ...(state.clar[el.dataset.cinc] || {}), include: el.checked }; save(); render(); });
  on("[data-cstat]", "onchange", el => { state.clar[el.dataset.cstat] = { ...(state.clar[el.dataset.cstat] || {}), status: el.value }; save(); render(); });
  on("[data-cans]", "onchange", el => { state.clar[el.dataset.cans] = { ...(state.clar[el.dataset.cans] || {}), answer: el.value }; save(); });
  on("[data-copyletter]", "onclick", async b => { const n = b.dataset.copyletter; try { await navigator.clipboard.writeText(letter(n)); document.querySelector(`[data-copied="${CSS.escape(n)}"]`).textContent = "Copied."; } catch { document.querySelector(`[data-copied="${CSS.escape(n)}"]`).textContent = "Copying is blocked here; open the letter above and select it."; } });
  const ack = $("#ack"); if (ack) ack.onchange = () => { state.ack = ack.checked; save(); render(); };
  const rec = $("#recommendation"); if (rec) rec.onchange = () => { state.recommendation = rec.value; save(); render(); };
  const approve = $("#approve"); if (approve) approve.onclick = () => { const by = $("#chair").value.trim(); if (!by) { $("#apperr").textContent = "Enter the panel chair's name."; return; } state.approval = { by, at: nowText() }; save(); render(); };
  const cp = $("#copymd"); if (cp) cp.onclick = async () => { try { await navigator.clipboard.writeText(markdown()); $("#copied").textContent = "Copied."; } catch { $("#copied").textContent = "Copying is blocked here."; } };
  const sj = $("#savejson"); if (sj) sj.onclick = async () => {
    const record = JSON.stringify({ engagement: D.context, signoff: state.signoff, status: state.status, decisions: state.decisions, clarifications: state.clar, recommendation: state.recommendation, approval: state.approval }, null, 1);
    if (window.top !== window) { try { await navigator.clipboard.writeText(record); $("#copied").textContent = "Decision record copied (downloads are not available in this viewer)."; } catch { $("#copied").textContent = "Copying is blocked here."; } return; }
    const a = document.createElement("a"); a.href = URL.createObjectURL(new Blob([record], { type: "application/json" })); a.download = `evalia-decisions-${D.context.reference}.json`; a.click();
  };
  on("[data-dd]", "onchange", el => { state.dd[el.dataset.dd] = { ...(state.dd[el.dataset.dd] || {}), ok: el.checked }; save(); render(); });
  on("[data-ddnote]", "onchange", el => { state.dd[el.dataset.ddnote] = { ...(state.dd[el.dataset.ddnote] || {}), note: el.value }; save(); });
  const issue = $("#issue"); if (issue) issue.onclick = () => { state.notices = { at: nowText(), iso: new Date().toISOString(), by: evaluator() }; save(); render(); };
  const bsel = $("#bsel"); if (bsel) bsel.onchange = () => { state.bidder = +bsel.value; save(); render(); };
}
render();
