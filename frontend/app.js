/* =====================================================================
   Leads — Akquise-Cockpit Hamburg  (Vanilla JS, gegen JSON-API-Kontrakt)
   ===================================================================== */

"use strict";

/* ---------------------------------------------------------------------
   MOCK-DATEN — NUR Offline-Fallback, falls /api/state fehlschlägt.
   Gleiche Shape wie der API-Kontrakt.
   --------------------------------------------------------------------- */
const MOCK_STATE = {
  today: "2026-06-30",
  statuses: {
    cold: ["identifiziert", "analysiert", "prototyp_erstellt", "kontaktiert", "keine_antwort", "verloren", "zurückgestellt"],
    warm: ["in_klaerung", "termin_vereinbart", "angebot_raus", "gewonnen"],
    candidate: ["neu", "website_unklar", "keine_website", "hat_website", "analysiert"],
    all: ["identifiziert", "analysiert", "prototyp_erstellt", "kontaktiert", "keine_antwort", "in_klaerung", "termin_vereinbart", "angebot_raus", "gewonnen", "verloren", "zurückgestellt"],
    reihenfolge: ["identifiziert", "analysiert", "prototyp_erstellt", "kontaktiert", "keine_antwort", "in_klaerung", "termin_vereinbart", "angebot_raus", "gewonnen", "verloren", "zurückgestellt"]
  },
  leads: [
    { slug: "zahnarztpraxis-eppendorf", firma: "Zahnarztpraxis Eppendorf", status: "identifiziert", schwaeche: "Keine Website, nur Google-Eintrag", kontaktiert_am: null, wiedervorlage: null, notiz: "Über OSM gefunden", warm: false },
    { slug: "friseur-altona-schnitt", firma: "Schnitt & Stil Altona", status: "kontaktiert", schwaeche: "Veraltete Website (2014), nicht mobil", kontaktiert_am: "2026-06-10", wiedervorlage: "2026-06-29", notiz: "Erstmail raus, freundlich", warm: false },
    { slug: "tischlerei-wandsbek", firma: "Tischlerei Wandsbek GmbH", status: "keine_antwort", schwaeche: "Kein Kontaktformular, nur Telefon", kontaktiert_am: "2026-06-12", wiedervorlage: null, notiz: "Zweite Mail überlegen", warm: false },
    { slug: "physio-winterhude", firma: "Physiopraxis Winterhude", status: "analysiert", schwaeche: "Langsame Ladezeit, kein SSL", kontaktiert_am: null, wiedervorlage: null, notiz: "", warm: false },
    {
      slug: "cafe-roesterei-ottensen", firma: "Rösterei Ottensen", status: "termin_vereinbart", schwaeche: "Kein Online-Shop trotz Versandwunsch",
      kontaktiert_am: "2026-06-18", wiedervorlage: "2026-07-03", notiz: "", warm: true,
      prioritaet: "hoch", ort: "Ottensen", branche: "Gastronomie / Kaffee", website: "roesterei-ottensen.de",
      ucp: "Festpreis-Shop in 3 Wochen, Bestandskunden behalten", roi_these: "Versand bringt ~15 Bestellungen/Woche à 28€",
      prototyp: "https://proto.local/roesterei", angelegt: "2026-06-05",
      kontakt: { name: "Lena Brandt", rolle: "Inhaberin", email: "lena@roesterei-ottensen.de", quelle: "Kontaktformular" },
      historie: [
        { datum: "2026-06-18", text: "Telefonat — Termin vereinbart für 03.07." },
        { datum: "2026-06-12", text: "Prototyp verschickt" },
        { datum: "2026-06-05", text: "Lead angelegt" }
      ],
      notizen: ["Will unbedingt eigene Marke behalten", "Budget ~2.500€ angedeutet"]
    },
    {
      slug: "yogastudio-st-pauli", firma: "Yogastudio St. Pauli", status: "gewonnen", schwaeche: "Buchung nur per Mail",
      kontaktiert_am: "2026-05-20", wiedervorlage: null, notiz: "", warm: true,
      prioritaet: "mittel", ort: "St. Pauli", branche: "Fitness / Yoga", website: "yoga-stpauli.de",
      ucp: "Kursbuchung + Bezahlung online", roi_these: "Spart 5h/Woche Verwaltung",
      prototyp: "https://proto.local/yoga", angelegt: "2026-05-02",
      kontakt: { name: "Marek Wolf", rolle: "Geschäftsführer", email: "marek@yoga-stpauli.de", quelle: "Empfehlung" },
      historie: [
        { datum: "2026-06-01", text: "Auftrag erteilt — gewonnen" },
        { datum: "2026-05-20", text: "Angebot angenommen" },
        { datum: "2026-05-02", text: "Lead angelegt" }
      ],
      notizen: ["Zahlung 50/50 vereinbart"]
    }
  ],
  report: {
    keine_antwort: [
      { slug: "tischlerei-wandsbek", firma: "Tischlerei Wandsbek GmbH", status: "keine_antwort", kontaktiert_am: "2026-06-12", wiedervorlage: null, tage: 18 }
    ],
    wiedervorlage_faellig: [
      { slug: "friseur-altona-schnitt", firma: "Schnitt & Stil Altona", status: "kontaktiert", kontaktiert_am: "2026-06-10", wiedervorlage: "2026-06-29" }
    ]
  },
  discovery_runs: [
    {
      file: "2026-06-28_zahnarzt_eppendorf.json", branche: "Zahnarzt", stadtteil: "Eppendorf",
      erstellt: "2026-06-28", anzahl: 5,
      counts: { neu: 1, website_unklar: 1, keine_website: 1, hat_website: 1, analysiert: 1 }
    },
    {
      file: "2026-06-25_friseur_altona.json", branche: "Friseur", stadtteil: "Altona",
      erstellt: "2026-06-25", anzahl: 3,
      counts: { keine_website: 2, hat_website: 1 }
    }
  ]
};

const MOCK_RUNS = {
  "2026-06-28_zahnarzt_eppendorf.json": {
    branche: "Zahnarzt", stadtteil: "Eppendorf", erstellt: "2026-06-28",
    kandidaten: [
      { id: 1, firma: "Zahnzentrum Eppendorf", adresse: "Eppendorfer Landstr. 42, 20249 Hamburg", website: "", telefon: "040 1234567", osm_id: "n1", status: "keine_website", gefundene_url: "", score: 88, befund: "Kein Web-Auftritt auffindbar — nur Google-My-Business. Starker Kandidat.", lead_angelegt: false },
      { id: 2, firma: "Dr. Meier & Kollegen", adresse: "Hegestr. 11, 20249 Hamburg", website: "dr-meier-hh.de", telefon: "040 2233445", osm_id: "n2", status: "analysiert", gefundene_url: "https://dr-meier-hh.de", score: 64, befund: "Website vorhanden, aber technisch veraltet.", lead_angelegt: false,
        tier2: { https: false, mobil: false, veraltet: 2013, impressum: true, kontaktformular: false } },
      { id: 3, firma: "Kieferorthopädie Nord", adresse: "Lokstedter Weg 5, 20251 Hamburg", website: "kfo-nord.de", telefon: "", osm_id: "n3", status: "hat_website", gefundene_url: "https://kfo-nord.de", score: 22, befund: "Moderne, gepflegte Website. Lohnt vermutlich nicht.", lead_angelegt: false,
        tier2: { https: true, mobil: true, veraltet: null, impressum: true, kontaktformular: true },
        tier3: { empfehlung: "lohnt_nicht", urteil: "Seite ist aktuell, responsiv, mit Online-Terminbuchung. Kein klarer Mehrwert durch Neubau." } },
      { id: 4, firma: "Praxis am Klinikum", adresse: "Martinistr. 52, 20246 Hamburg", website: "", telefon: "040 5566778", osm_id: "n4", status: "website_unklar", gefundene_url: "", score: 55, befund: "Unklar — evtl. Subseite des Klinikums. Manuell prüfen.", lead_angelegt: false },
      { id: 5, firma: "Zahnärzte Isestraße", adresse: "Isestr. 88, 20149 Hamburg", website: "", telefon: "040 9988776", osm_id: "n5", status: "neu", gefundene_url: "", score: 0, befund: "Noch nicht bewertet.", lead_angelegt: false,
        tier3: { empfehlung: "unklar", urteil: "Tier-2-Signale uneindeutig — Sichtprüfung empfohlen." } }
    ]
  },
  "2026-06-25_friseur_altona.json": {
    branche: "Friseur", stadtteil: "Altona", erstellt: "2026-06-25",
    kandidaten: [
      { id: 1, firma: "Haarschneiderei Altona", adresse: "Ottenser Hauptstr. 3, 22765 Hamburg", website: "", telefon: "040 111222", osm_id: "n10", status: "keine_website", gefundene_url: "", score: 79, befund: "Kein Web-Auftritt — nur Instagram.", lead_angelegt: true },
      { id: 2, firma: "Schnitt & Stil Altona", adresse: "Bahrenfelder Str. 20, 22765 Hamburg", website: "schnitt-stil.de", telefon: "", osm_id: "n11", status: "keine_website", gefundene_url: "", score: 71, befund: "Domain geparkt, keine echte Seite.", lead_angelegt: false },
      { id: 3, firma: "Barbershop Ottensen", adresse: "Friedensallee 9, 22765 Hamburg", website: "barber-ottensen.de", telefon: "040 333444", osm_id: "n12", status: "hat_website", gefundene_url: "https://barber-ottensen.de", score: 30, befund: "Aktuelle One-Pager-Seite vorhanden.", lead_angelegt: false }
    ]
  }
};

/* ---------------------------------------------------------------------
   STATUS-FARB-MAPPING  (Status -> Badge-Klasse)
   --------------------------------------------------------------------- */
const STATUS_CLASS = {
  identifiziert: "s-ink", analysiert: "s-cool", prototyp_erstellt: "s-cool",
  kontaktiert: "s-accent", keine_antwort: "s-danger",
  in_klaerung: "s-accent", termin_vereinbart: "s-warn", angebot_raus: "s-warn",
  gewonnen: "s-ok", verloren: "s-muted", "zurückgestellt": "s-muted"
};
const CAND_STATUS_CLASS = {
  neu: "s-ink", website_unklar: "s-warn", keine_website: "s-accent",
  hat_website: "s-cool", analysiert: "s-cool"
};
const CAND_STATUSES = ["neu", "website_unklar", "keine_website", "hat_website", "analysiert"];
const STATUS_LABEL = {
  identifiziert: "Identifiziert", analysiert: "Analysiert", prototyp_erstellt: "Prototyp erstellt",
  kontaktiert: "Kontaktiert", keine_antwort: "Keine Antwort", in_klaerung: "In Klärung",
  termin_vereinbart: "Termin vereinbart", angebot_raus: "Angebot raus", gewonnen: "Gewonnen",
  verloren: "Verloren", "zurückgestellt": "Zurückgestellt",
  neu: "Neu", website_unklar: "Website unklar", keine_website: "Keine Website", hat_website: "Hat Website"
};
const T3_CLASS = { lohnt: "s-ok", lohnt_nicht: "s-muted", unklar: "s-warn" };
const T3_LABEL = { lohnt: "Lohnt sich", lohnt_nicht: "Lohnt nicht", unklar: "Unklar" };

function statusLabel(s) { return STATUS_LABEL[s] || s; }

/* ---------------------------------------------------------------------
   APP-STATE
   --------------------------------------------------------------------- */
const App = {
  state: null,
  offline: false,
  activeView: "pipeline",
  activeRunFile: null,
  activeRun: null,
  openLead: null
};

/* ---------------------------------------------------------------------
   API-HELPER
   Basis-URL kommt aus config.js (window.LEADGEN_API_BASE). Leer = gleiche
   Origin; absolute URL = entkoppeltes Backend (CORS aktiv).
   --------------------------------------------------------------------- */
const API_BASE = (typeof window !== "undefined" && window.LEADGEN_API_BASE) || "";
async function api(path, opts) {
  const res = await fetch(API_BASE + path, opts);
  let body = null;
  try { body = await res.json(); } catch (e) { /* leer */ }
  if (!res.ok) {
    const err = new Error((body && body.error) || ("HTTP " + res.status));
    err.status = res.status; err.body = body;
    throw err;
  }
  return body;
}
function post(path, data) {
  return api(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data) });
}

/* ---------------------------------------------------------------------
   STATE LADEN
   --------------------------------------------------------------------- */
async function loadState() {
  try {
    App.state = await api("/api/state");
    App.offline = false;
  } catch (e) {
    App.state = structuredClone(MOCK_STATE);
    App.offline = true;
  }
  document.getElementById("offline-badge").hidden = !App.offline;
  render();
}

async function loadRun(file) {
  if (App.offline) {
    App.activeRun = structuredClone(MOCK_RUNS[file]) || null;
    App.activeRunFile = file;
    renderRunDetail();
    return;
  }
  try {
    App.activeRun = await api("/api/discovery/run?file=" + encodeURIComponent(file));
    App.activeRunFile = file;
  } catch (e) {
    toast("Lauf konnte nicht geladen werden", "error");
    App.activeRun = null;
  }
  renderRunDetail();
}

/* =====================================================================
   RENDER — KOPF + KPIs
   ===================================================================== */
function render() {
  const s = App.state;
  document.getElementById("today").textContent = "Heute · " + fmtDate(s.today);
  renderKpis();
  renderBoard();
  renderRunList();
}

function renderKpis() {
  const s = App.state;
  const total = s.leads.length;
  const warm = s.leads.filter(l => l.warm === true).length;
  const due = (s.report.wiedervorlage_faellig || []).length;
  const stale = (s.report.keine_antwort || []).length;

  const host = document.getElementById("kpis");
  host.innerHTML = "";
  const cards = [
    { cls: "k-total", label: "Leads gesamt", value: total, sub: "in der Pipeline", d: 3 },
    { cls: "k-warm", label: "Davon warm", value: warm, sub: "qualifiziert / im Gespräch", d: 4 },
    { cls: "k-due", label: "Wiedervorlagen fällig", value: due, sub: "heute oder überfällig", alert: due > 0, d: 5 },
    { cls: "k-stale", label: "Keine Antwort > 14 Tage", value: stale, sub: "Nachfassen prüfen", alert: stale > 0, d: 6 }
  ];
  cards.forEach(c => {
    const el = document.createElement("div");
    el.className = "kpi reveal " + c.cls + (c.alert ? " alert" : "") + (c.value === 0 ? " zero" : "");
    el.style.setProperty("--d", c.d);
    el.innerHTML = `<div class="kpi-label">${c.label}</div>
      <div class="kpi-value">${c.value}</div>
      <div class="kpi-sub">${c.sub}</div>`;
    host.appendChild(el);
  });
}

/* =====================================================================
   RENDER — KANBAN-BOARD
   ===================================================================== */
function renderBoard() {
  const s = App.state;
  const board = document.getElementById("board");
  board.innerHTML = "";

  const dueSet = new Set((s.report.wiedervorlage_faellig || []).map(r => r.slug));
  const staleSet = new Set((s.report.keine_antwort || []).map(r => r.slug));

  if (!s.leads.length) {
    board.innerHTML = emptyState("🌱", "Noch keine Leads", "Lege deinen ersten Lead an oder übernimm Kandidaten aus der Discovery.");
    return;
  }

  // Nur Status-Spalten zeigen, die in der Reihenfolge stehen
  const order = s.statuses.reihenfolge;
  const byStatus = {};
  order.forEach(st => byStatus[st] = []);
  s.leads.forEach(l => { (byStatus[l.status] = byStatus[l.status] || []).push(l); });

  // Spalten ohne Reihenfolge-Eintrag ans Ende
  const cols = order.filter(st => byStatus[st] !== undefined);
  Object.keys(byStatus).forEach(st => { if (!cols.includes(st)) cols.push(st); });

  cols.forEach((st, i) => {
    const leads = byStatus[st] || [];
    const col = document.createElement("div");
    col.className = "column reveal";
    col.style.setProperty("--d", 7 + i);
    col.innerHTML = `<div class="col-head"><span class="col-title">${statusLabel(st)}</span><span class="col-count">${leads.length}</span></div>`;
    const body = document.createElement("div");
    body.className = "col-body";
    if (!leads.length) {
      body.innerHTML = `<div class="col-empty">—</div>`;
    } else {
      leads.forEach(l => body.appendChild(leadCard(l, dueSet.has(l.slug), staleSet.has(l.slug))));
    }
    col.appendChild(body);
    board.appendChild(col);
  });
}

function leadCard(l, isDue, isStale) {
  const card = document.createElement("div");
  let cls = "card";
  if (l.warm) cls += " warm";
  if (isStale) cls += " flag-danger";
  else if (isDue) cls += " flag";
  card.className = cls;
  card.tabIndex = 0;

  const flag = isStale
    ? `<span class="flag-dot danger" title="Keine Antwort > 14 Tage"></span>`
    : (isDue ? `<span class="flag-dot warn" title="Wiedervorlage fällig"></span>` : "");
  const warmBadge = l.warm ? `<span class="warm-badge">warm</span>` : "";

  const meta = [];
  if (l.kontaktiert_am) meta.push(`<span><b>Kontakt:</b> ${fmtDate(l.kontaktiert_am)}</span>`);
  if (l.wiedervorlage) meta.push(`<span><b>WV:</b> ${fmtDate(l.wiedervorlage)}</span>`);

  card.innerHTML = `
    <div class="card-top">
      <div class="card-firma">${esc(l.firma)}</div>
      <div style="display:flex;gap:6px;align-items:center">${flag}${warmBadge}</div>
    </div>
    <span class="badge ${STATUS_CLASS[l.status] || "s-ink"}" style="margin-top:9px">${statusLabel(l.status)}</span>
    ${l.schwaeche ? `<div class="card-schwaeche">${esc(l.schwaeche)}</div>` : ""}
    ${meta.length ? `<div class="card-meta">${meta.join("")}</div>` : ""}
  `;
  card.addEventListener("click", () => openDrawer(l.slug));
  card.addEventListener("keydown", e => { if (e.key === "Enter") openDrawer(l.slug); });
  return card;
}

/* =====================================================================
   DRAWER — LEAD-DETAIL
   ===================================================================== */
function openDrawer(slug) {
  const l = App.state.leads.find(x => x.slug === slug);
  if (!l) return;
  App.openLead = slug;

  const drawer = document.getElementById("drawer");
  const scrim = document.getElementById("drawer-scrim");
  const allStatuses = App.state.statuses.all;

  const statusOpts = allStatuses.map(st =>
    `<option value="${st}" ${st === l.status ? "selected" : ""}>${statusLabel(st)}</option>`).join("");

  let warmFields = "";
  if (l.warm) {
    const k = l.kontakt || {};
    const rows = [
      ["Priorität", l.prioritaet], ["Ort", l.ort], ["Branche", l.branche],
      ["Website", l.website ? `<a href="https://${l.website.replace(/^https?:\/\//, "")}" target="_blank" rel="noopener">${esc(l.website)}</a>` : null],
      ["UCP", l.ucp], ["ROI-These", l.roi_these], ["Prototyp", l.prototyp ? `<a href="${esc(l.prototyp)}" target="_blank" rel="noopener">öffnen ↗</a>` : null],
      ["Kontakt", k.name ? `${esc(k.name)}${k.rolle ? " · " + esc(k.rolle) : ""}` : null],
      ["E-Mail", k.email ? `<a href="mailto:${esc(k.email)}">${esc(k.email)}</a>` : null],
      ["Quelle", k.quelle]
    ].filter(r => r[1]);
    warmFields = `
      <div class="drawer-section">
        <h3>Qualifizierung</h3>
        <div class="field-grid">
          ${rows.map(r => `<div class="frow"><span class="fk">${r[0]}</span><span class="fv">${r[1]}</span></div>`).join("")}
        </div>
      </div>`;

    if (Array.isArray(l.historie) && l.historie.length) {
      warmFields += `<div class="drawer-section"><h3>Historie</h3><ul class="hist">${
        l.historie.map(h => `<li><span class="ht">${fmtDate(h.datum)}</span>${esc(h.text)}</li>`).join("")
      }</ul></div>`;
    }
    if (Array.isArray(l.notizen) && l.notizen.length) {
      warmFields += `<div class="drawer-section"><h3>Notizen</h3><div class="notes">${
        l.notizen.map(n => `<div class="note-item">${esc(n)}</div>`).join("")
      }</div></div>`;
    }
  } else if (l.notiz) {
    warmFields = `<div class="drawer-section"><h3>Notiz</h3><div class="notes"><div class="note-item">${esc(l.notiz)}</div></div></div>`;
  }

  drawer.innerHTML = `
    <div class="drawer-inner">
      <div class="drawer-head">
        <div>
          <h2>${esc(l.firma)}</h2>
          <div class="drawer-badges">
            <span class="badge ${STATUS_CLASS[l.status] || "s-ink"}">${statusLabel(l.status)}</span>
            ${l.warm ? `<span class="warm-badge">warm</span>` : ""}
          </div>
        </div>
        <button class="drawer-close" id="drawer-close" aria-label="Schließen">×</button>
      </div>

      ${l.schwaeche ? `<div class="drawer-section"><h3>Schwäche</h3><p style="margin:0;font-size:14.5px;color:var(--ink-soft);line-height:1.5">${esc(l.schwaeche)}</p></div>` : ""}

      <div class="drawer-section">
        <h3>Stammdaten</h3>
        <div class="field-grid">
          <div class="frow"><span class="fk">Kontaktiert am</span><span class="fv">${l.kontaktiert_am ? fmtDate(l.kontaktiert_am) : "—"}</span></div>
          <div class="frow"><span class="fk">Wiedervorlage</span><span class="fv">${l.wiedervorlage ? fmtDate(l.wiedervorlage) : "—"}</span></div>
        </div>
      </div>

      ${warmFields}

      <div class="drawer-section">
        <h3>Aktionen</h3>
        <div class="field" style="margin-bottom:14px">
          <span>Status ändern</span>
          <div class="action-row">
            <select id="act-status">${statusOpts}</select>
            <button class="btn btn-accent btn-sm" id="act-status-btn">Setzen</button>
          </div>
        </div>
        <div class="field" style="margin-bottom:14px">
          <span>Wiedervorlage setzen</span>
          <div class="action-row">
            <input type="date" id="act-wv" value="${l.wiedervorlage || ""}" />
            <button class="btn btn-accent btn-sm" id="act-wv-btn">Setzen</button>
          </div>
        </div>
        <div class="field">
          <span>Notiz hinzufügen</span>
          <textarea id="act-note" placeholder="Notiz…"></textarea>
          <div style="margin-top:8px;text-align:right"><button class="btn btn-accent btn-sm" id="act-note-btn">Hinzufügen</button></div>
        </div>
      </div>
    </div>`;

  drawer.hidden = false; scrim.hidden = false;
  document.getElementById("drawer-close").onclick = closeDrawer;

  document.getElementById("act-status-btn").onclick = async () => {
    const status = document.getElementById("act-status").value;
    await doAction(() => post(`/api/leads/${slug}/status`, { status }), "Status aktualisiert");
  };
  document.getElementById("act-wv-btn").onclick = async () => {
    const datum = document.getElementById("act-wv").value;
    if (!datum) { toast("Bitte ein Datum wählen", "error"); return; }
    await doAction(() => post(`/api/leads/${slug}/wiedervorlage`, { datum }), "Wiedervorlage gesetzt");
  };
  document.getElementById("act-note-btn").onclick = async () => {
    const text = document.getElementById("act-note").value.trim();
    if (!text) { toast("Notiz ist leer", "error"); return; }
    await doAction(() => post(`/api/leads/${slug}/note`, { text }), "Notiz hinzugefügt");
  };
}

function closeDrawer() {
  document.getElementById("drawer").hidden = true;
  document.getElementById("drawer-scrim").hidden = true;
  App.openLead = null;
}

/* Aktion ausführen -> state neu laden -> ggf. Drawer neu öffnen */
async function doAction(fn, okMsg) {
  if (App.offline) { toast("Offline (Demo-Daten) — keine echte Aktion", "error"); return; }
  try {
    await fn();
    toast(okMsg, "ok");
    const reopen = App.openLead;
    await loadState();
    if (reopen && App.state.leads.find(l => l.slug === reopen)) openDrawer(reopen);
  } catch (e) {
    toast(e.message || "Fehler", "error");
  }
}

/* =====================================================================
   NEUER LEAD — MODAL
   ===================================================================== */
function openModal() {
  document.getElementById("modal-scrim").hidden = false;
  document.getElementById("new-lead-error").hidden = true;
  const form = document.getElementById("new-lead-form");
  form.reset();
  setTimeout(() => form.querySelector("input[name=firma]").focus(), 50);
}
function closeModal() { document.getElementById("modal-scrim").hidden = true; }

async function submitNewLead(e) {
  e.preventDefault();
  const form = e.target;
  const firma = form.firma.value.trim();
  const schwaeche = form.schwaeche.value.trim();
  const errEl = document.getElementById("new-lead-error");
  errEl.hidden = true;
  if (!firma || !schwaeche) { errEl.textContent = "Bitte beide Felder ausfüllen."; errEl.hidden = false; return; }

  if (App.offline) {
    closeModal();
    toast("Offline (Demo-Daten) — Lead nicht gespeichert", "error");
    return;
  }
  try {
    await post("/api/leads", { firma, schwaeche });
    closeModal();
    toast("Lead angelegt", "ok");
    await loadState();
  } catch (e2) {
    if (e2.status === 409) { errEl.textContent = "Existiert bereits."; errEl.hidden = false; }
    else { errEl.textContent = e2.message || "Fehler beim Anlegen."; errEl.hidden = false; }
  }
}

/* =====================================================================
   DISCOVERY — RUN-LISTE
   ===================================================================== */
function renderRunList() {
  const host = document.getElementById("run-list");
  const runs = App.state.discovery_runs || [];
  host.innerHTML = "";
  if (!runs.length) {
    document.getElementById("run-detail").innerHTML =
      emptyState("🔭", "Keine Scan-Läufe", "Starte einen Discovery-Scan, um Kandidaten zu finden.");
    return;
  }
  runs.forEach(r => {
    const btn = document.createElement("button");
    btn.className = "run-card" + (r.file === App.activeRunFile ? " is-active" : "");
    btn.innerHTML = `
      <div class="rc-title">${esc(r.branche)} · ${esc(r.stadtteil)}</div>
      <div class="rc-sub">${fmtDate(r.erstellt)}</div>
      <div class="rc-foot"><span class="n">${r.anzahl}</span> Kandidaten</div>`;
    btn.onclick = () => { loadRun(r.file); document.querySelectorAll(".run-card").forEach(c => c.classList.remove("is-active")); btn.classList.add("is-active"); };
    host.appendChild(btn);
  });

  // Auto-Auswahl des ersten Laufs
  if (!App.activeRunFile && runs.length) {
    loadRun(runs[0].file);
    host.firstChild.classList.add("is-active");
  } else if (App.activeRunFile && !App.activeRun) {
    renderRunDetail();
  }
}

function renderRunDetail() {
  const host = document.getElementById("run-detail");
  const run = App.activeRun;
  if (!run) { host.innerHTML = emptyState("🔭", "Lauf wählen", "Wähle links einen Scan-Lauf aus."); return; }

  const file = App.activeRunFile;
  const kand = run.kandidaten || [];

  host.innerHTML = `
    <div class="run-detail-head">
      <div>
        <h2>${esc(run.branche)} · ${esc(run.stadtteil)}</h2>
        <div class="rh-sub">${fmtDate(run.erstellt)} · ${kand.length} Kandidaten</div>
      </div>
    </div>
    <div class="bulk-bar"><button class="btn btn-accent btn-sm" id="bulk-uebernehmen">Alle „keine_website“ übernehmen →</button></div>
    <div id="cand-list"></div>`;

  const list = document.getElementById("cand-list");
  if (!kand.length) {
    list.innerHTML = emptyState("📭", "Keine Kandidaten", "Dieser Lauf enthält keine Einträge.");
  } else {
    kand.forEach(c => list.appendChild(candCard(c, file)));
  }

  document.getElementById("bulk-uebernehmen").onclick = async () => {
    await doDiscoveryAction(
      () => post("/api/discovery/uebernehmen", { file, which: "auto" }),
      res => `${res.angelegt} angelegt, ${res.uebersprungen} übersprungen`
    );
  };
}

function candCard(c, file) {
  const el = document.createElement("div");
  el.className = "cand";

  const statusOpts = CAND_STATUSES.map(st =>
    `<option value="${st}" ${st === c.status ? "selected" : ""}>${statusLabel(st)}</option>`).join("");

  let chips = "";
  if (c.tier2) {
    const t = c.tier2;
    const chip = (ok, yes, no) => `<span class="chip ${ok ? "yes" : "no"}">${ok ? "✓" : "✗"} ${ok ? yes : no}</span>`;
    // Backend liefert viewport (bool) + copyright_jahr + veraltet (bool); Mock nutzt mobil + veraltet (Jahr).
    const mobilOk = t.viewport ?? t.mobil;
    const veraltetJahr = t.copyright_jahr ?? (typeof t.veraltet === "number" ? t.veraltet : null);
    chips = `<div class="chips">
      ${chip(t.https, "HTTPS", "kein HTTPS")}
      ${chip(mobilOk, "mobil", "nicht mobil")}
      ${t.veraltet ? `<span class="chip no">⚠ veraltet${veraltetJahr ? ` (${veraltetJahr})` : ""}</span>` : `<span class="chip yes">aktuell</span>`}
      ${chip(t.impressum, "Impressum", "kein Impressum")}
      ${chip(t.kontaktformular, "Kontaktform.", "kein Formular")}
    </div>`;
  }

  let t3 = "";
  if (c.tier3) {
    t3 = `<div class="tier3">
      <span class="badge ${T3_CLASS[c.tier3.empfehlung] || "s-ink"}">${T3_LABEL[c.tier3.empfehlung] || c.tier3.empfehlung}</span>
      <span class="t3-text">${esc(c.tier3.urteil || "")}</span>
    </div>`;
  }

  const scoreW = Math.max(0, Math.min(100, c.score || 0));

  const actions = c.lead_angelegt
    ? `<span class="cand-done">✓ als Lead angelegt</span>`
    : `<button class="btn btn-accent btn-sm" data-uebernehmen>→ Lead</button>`;

  el.innerHTML = `
    <div class="cand-top">
      <div>
        <div class="cand-firma">${esc(c.firma)}</div>
        <div class="cand-addr">${esc(c.adresse || "")}</div>
        <span class="badge ${CAND_STATUS_CLASS[c.status] || "s-ink"}" style="margin-top:8px">${statusLabel(c.status)}</span>
      </div>
      <div class="cand-score">
        <div class="sv">${c.score != null ? c.score : "–"}</div>
        <div class="sl">Score</div>
        <div class="score-bar"><i style="width:${scoreW}%"></i></div>
      </div>
    </div>
    ${c.befund ? `<div class="cand-befund">${esc(c.befund)}</div>` : ""}
    ${chips}
    ${t3}
    <div class="cand-actions">
      <div class="field"><span>Status</span><select data-status>${statusOpts}</select></div>
      <div class="field url"><span>URL (optional)</span><input type="text" data-url placeholder="https://…" value="${esc(c.gefundene_url || "")}" /></div>
      <button class="btn btn-ghost btn-sm" data-setstatus>Speichern</button>
      ${actions}
    </div>`;

  el.querySelector("[data-setstatus]").onclick = async () => {
    const status = el.querySelector("[data-status]").value;
    const url = el.querySelector("[data-url]").value.trim();
    await doDiscoveryAction(
      () => post("/api/discovery/setstatus", { file, id: c.id, status, url }),
      () => "Status gespeichert"
    );
  };
  const ueb = el.querySelector("[data-uebernehmen]");
  if (ueb) ueb.onclick = async () => {
    await doDiscoveryAction(
      () => post("/api/discovery/uebernehmen", { file, which: [c.id] }),
      res => `${res.angelegt} angelegt, ${res.uebersprungen} übersprungen`
    );
  };
  return el;
}

async function doDiscoveryAction(fn, msgFn) {
  if (App.offline) { toast("Offline (Demo-Daten) — keine echte Aktion", "error"); return; }
  try {
    const res = await fn();
    toast(msgFn(res || {}), "ok");
    await loadState();          // KPIs + Funnel-Counts aktualisieren
    await loadRun(App.activeRunFile);
  } catch (e) {
    toast(e.message || "Fehler", "error");
  }
}

/* =====================================================================
   HELPERS
   ===================================================================== */
function esc(s) {
  return String(s == null ? "" : s).replace(/[&<>"']/g, m =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[m]));
}
function fmtDate(iso) {
  if (!iso) return "—";
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(iso);
  if (!m) return iso;
  return `${m[3]}.${m[2]}.${m[1]}`;
}
function emptyState(emoji, title, text) {
  return `<div class="empty"><div class="emoji">${emoji}</div><h3>${esc(title)}</h3><p>${esc(text)}</p></div>`;
}
function toast(msg, kind) {
  const host = document.getElementById("toast-host");
  const t = document.createElement("div");
  t.className = "toast " + (kind || "");
  t.textContent = msg;
  host.appendChild(t);
  setTimeout(() => { t.style.transition = "opacity .3s, transform .3s"; t.style.opacity = "0"; t.style.transform = "translateY(10px)"; setTimeout(() => t.remove(), 320); }, 3200);
}

/* =====================================================================
   TABS + GLOBAL EVENTS
   ===================================================================== */
function switchView(view) {
  App.activeView = view;
  document.querySelectorAll(".tab").forEach(t => t.classList.toggle("is-active", t.dataset.view === view));
  document.getElementById("view-pipeline").classList.toggle("is-active", view === "pipeline");
  document.getElementById("view-discovery").classList.toggle("is-active", view === "discovery");
}

function init() {
  document.querySelectorAll(".tab").forEach(t => t.addEventListener("click", () => switchView(t.dataset.view)));
  document.getElementById("btn-new-lead").addEventListener("click", openModal);
  document.getElementById("modal-cancel").addEventListener("click", closeModal);
  document.getElementById("new-lead-form").addEventListener("submit", submitNewLead);
  document.getElementById("drawer-scrim").addEventListener("click", closeDrawer);
  document.getElementById("modal-scrim").addEventListener("click", e => { if (e.target.id === "modal-scrim") closeModal(); });
  document.addEventListener("keydown", e => {
    if (e.key === "Escape") { closeDrawer(); closeModal(); }
  });
  loadState();
}

document.addEventListener("DOMContentLoaded", init);
