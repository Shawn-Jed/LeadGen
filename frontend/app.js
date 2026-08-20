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
  gewonnen: "s-ok", verloren: "s-muted", "zurückgestellt": "s-muted", inaktiv: "s-muted"
};
const CAND_STATUS_CLASS = {
  neu: "s-ink", website_unklar: "s-warn", keine_website: "s-accent",
  hat_website: "s-cool", analysiert: "s-cool", abgelehnt: "s-muted"
};
const CAND_STATUSES = ["neu", "website_unklar", "keine_website", "hat_website", "analysiert"];

// Festes Schwäche-Tag-Set für die Lead-Anlage (+ eigene Tags ad hoc). Tags = schwaeche-Liste.
const SCHWAECHE_TAGS = [
  "Altes Design", "Nicht mobil", "Keine/nur Google", "Fehlende Funktionalität",
  "Langsam", "Kein SSL", "Schlechtes SEO", "Kein Impressum"
];
// schwaeche kommt als kommagetrennter String (kalt) bzw. Liste→String (warm, app.py) → in Tags splitten.
function splitTags(raw) {
  return String(raw || "").split(/[;,]/).map(s => s.trim()).filter(Boolean);
}
// Schwäche-String als Badge-Pills rendern.
function tagBadges(raw) {
  const tags = splitTags(raw);
  if (!tags.length) return "";
  return `<div class="tag-pills">${tags.map(t => `<span class="tag-pill">${esc(t)}</span>`).join("")}</div>`;
}

// Deterministischer Google-Maps-Suchlink aus Firma (+ Adresse) — Fallback, wenn kein Feld geliefert.
function googleMapsLink(firma, adresse = "") {
  const teile = [firma, adresse].map(t => (t || "").trim()).filter(Boolean);
  if (!teile.length) return "";
  if (!teile.some(t => /hamburg/i.test(t))) teile.push("Hamburg");
  return "https://www.google.com/maps/search/?api=1&query=" + encodeURIComponent(teile.join(" "));
}
const STATUS_LABEL = {
  identifiziert: "Identifiziert", analysiert: "Analysiert", prototyp_erstellt: "Prototyp erstellt",
  kontaktiert: "Kontaktiert", keine_antwort: "Keine Antwort", in_klaerung: "In Klärung",
  termin_vereinbart: "Termin vereinbart", angebot_raus: "Angebot raus", gewonnen: "Gewonnen",
  verloren: "Verloren", "zurückgestellt": "Zurückgestellt", inaktiv: "Inaktiv",
  neu: "Neu", website_unklar: "Website unklar", keine_website: "Keine Website", hat_website: "Hat Website",
  abgelehnt: "Abgelehnt"
};
const T3_CLASS = { lohnt: "s-ok", lohnt_nicht: "s-muted", unklar: "s-warn" };
const T3_LABEL = { lohnt: "Lohnt sich", lohnt_nicht: "Lohnt nicht", unklar: "Unklar" };

// Nächste Aktion: Label + Klasse für Badge
const NEXT_ACTION_LABEL = {
  pruefen: "Prüfen",
  qualifizieren: "Qualifizieren",
  demo_beauftragen: "Demo beauftragen",
  kontaktieren: "Kontaktieren",
  nachfassen: "Nachfassen",
};
const NEXT_ACTION_CLASS = {
  pruefen: "na-pruefen",
  qualifizieren: "na-qualifizieren",
  demo_beauftragen: "na-demo",
  kontaktieren: "na-kontaktieren",
  nachfassen: "na-nachfassen",
};

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
  openLead: null,
  showRejected: false,  // Discovery: abgelehnte Kandidaten einblenden?
  candFilter: { mode: "alle", minScore: 0 },  // Discovery-Filter: alle|keine_website|veraltet + Score-Schwelle
  dragSlug: null,       // Board: aktuell gezogener Lead
  newLeadTags: new Set(),   // Neuer-Lead-Modal: aktuell gewählte Schwäche-Tags
  ueberTags: new Set(),     // Übernahme-Dialog: gewählte Schwäche-Tags (optional, sonst Auto-Schwäche)
  leadTagFilter: new Set(),  // Pipeline: aktive Tag-Filter (OR-Match, leer = alle)
  leadSearch: ""             // Pipeline: Freitext-Suche (Name/Ort/Branche), lowercase
};

// Prüft, ob ein Kandidat den aktiven Discovery-Filter erfüllt.
function candMatchesFilter(c) {
  const f = App.candFilter;
  if ((c.score || 0) < f.minScore) return false;
  if (f.mode === "keine_website") return c.status === "keine_website";
  if (f.mode === "mit_website")
    return c.status !== "keine_website"
      && (c.status === "hat_website" || c.status === "analysiert" || !!c.website || !!c.gefundene_url || !!c.tier2);
  if (f.mode === "veraltet") return !!(c.tier2 && c.tier2.veraltet);
  return true;
}

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
  renderLeadTagbar();
  renderBoard();
  renderFokus();
  renderRunList();
}

// Pipeline-Filterleiste: alle real vorkommenden Schwäche-Tags als Toggle-Chips (OR-Match).
function renderLeadTagbar() {
  const host = document.getElementById("lead-tagbar");
  if (!host) return;
  const counts = new Map();
  (App.state.leads || []).forEach(l => splitTags(l.schwaeche).forEach(t => counts.set(t, (counts.get(t) || 0) + 1)));
  // Aktive Filter, die es nicht mehr gibt, verwerfen.
  [...App.leadTagFilter].forEach(t => { if (!counts.has(t)) App.leadTagFilter.delete(t); });
  if (!counts.size) { host.hidden = true; host.innerHTML = ""; return; }
  host.hidden = false;
  const tags = [...counts.keys()].sort((a, b) => a.localeCompare(b, "de"));
  host.innerHTML =
    `<span class="tagbar-label">Filter</span>` +
    tags.map(t => `<button type="button" class="tag-chip${App.leadTagFilter.has(t) ? " on" : ""}" data-tag="${esc(t)}">${esc(t)}<span class="tag-count">${counts.get(t)}</span></button>`).join("") +
    (App.leadTagFilter.size ? `<button type="button" class="tagbar-clear" id="tagbar-clear">× zurücksetzen</button>` : "");
  host.querySelectorAll(".tag-chip").forEach(b => b.addEventListener("click", () => {
    const t = b.dataset.tag;
    if (App.leadTagFilter.has(t)) App.leadTagFilter.delete(t); else App.leadTagFilter.add(t);
    renderLeadTagbar();
    renderBoard();
  }));
  const clear = document.getElementById("tagbar-clear");
  if (clear) clear.addEventListener("click", () => { App.leadTagFilter.clear(); renderLeadTagbar(); renderBoard(); });
}

// Lead erfüllt den aktiven Tag-Filter (leer = alle; sonst mind. ein Tag muss passen).
function leadMatchesTagFilter(l) {
  if (!App.leadTagFilter.size) return true;
  return splitTags(l.schwaeche).some(t => App.leadTagFilter.has(t));
}

// Lead erfüllt die Freitext-Suche (leer = alle; sonst Teilstring in Name/Ort/Branche/Adresse).
function leadMatchesSearch(l) {
  const q = App.leadSearch;
  if (!q) return true;
  const haystack = [l.firma, l.ort, l.branche, l.adresse].filter(Boolean).join(" ").toLowerCase();
  return haystack.includes(q);
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
  s.leads.filter(l => leadMatchesTagFilter(l) && leadMatchesSearch(l)).forEach(l => { (byStatus[l.status] = byStatus[l.status] || []).push(l); });

  // Suche/Filter aktiv, aber nichts übrig → klarer Leerzustand statt lauter leerer Spalten.
  const sichtbar = Object.values(byStatus).reduce((n, arr) => n + arr.length, 0);
  if (!sichtbar && (App.leadSearch || App.leadTagFilter.size)) {
    board.innerHTML = emptyState("🔍", "Kein Treffer", "Kein Lead passt zu Suche und Filter. Suchbegriff ändern oder Filter zurücksetzen.");
    return;
  }

  // Spalten ohne Reihenfolge-Eintrag ans Ende
  const cols = order.filter(st => byStatus[st] !== undefined);
  Object.keys(byStatus).forEach(st => { if (!cols.includes(st)) cols.push(st); });

  cols.forEach((st, i) => {
    const leads = byStatus[st] || [];
    const col = document.createElement("div");
    col.className = "column reveal";
    col.style.setProperty("--d", 7 + i);
    col.dataset.status = st;
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

    // Drop-Ziel: Karte fallen lassen → Statuswechsel auf diese Spalte
    col.addEventListener("dragover", e => {
      if (!App.dragSlug) return;
      e.preventDefault();
      e.dataTransfer.dropEffect = "move";
      col.classList.add("drop-target");
    });
    col.addEventListener("dragleave", e => {
      if (!col.contains(e.relatedTarget)) col.classList.remove("drop-target");
    });
    col.addEventListener("drop", e => {
      e.preventDefault();
      col.classList.remove("drop-target");
      const slug = e.dataTransfer.getData("text/plain") || App.dragSlug;
      if (slug) moveLeadToStatus(slug, st);
    });
  });
}

/* Karte per Drag-and-drop in eine Status-Spalte verschieben — mit Guards:
   - gleicher Status → ignorieren
   - warm → kalt: blockiert (CRM-Regel 6, kein Zurückziehen)
   - kalt → warm: Bestätigung (Graduierung legt eigene Datei an) */
async function moveLeadToStatus(slug, targetStatus) {
  const l = App.state.leads.find(x => x.slug === slug);
  if (!l || l.status === targetStatus) return;

  const warmSet = new Set(App.state.statuses.warm || []);
  const sourceWarm = l.warm === true;
  const targetWarm = warmSet.has(targetStatus);

  if (sourceWarm && !targetWarm) {
    toast("Warme Leads können nicht zurück in die kalte Pipeline (CRM-Regel).", "error");
    return;
  }
  if (!sourceWarm && targetWarm) {
    if (!confirm(`„${l.firma}“ zu „${statusLabel(targetStatus)}“ (warm) verschieben?\n\nDer Lead graduiert und bekommt eine eigene Datei.`)) return;
  }
  await doAction(() => post(`/api/leads/${slug}/status`, { status: targetStatus }),
    `„${l.firma}“ → ${statusLabel(targetStatus)}`);
}

function leadCard(l, isDue, isStale) {
  const card = document.createElement("div");
  let cls = "card";
  if (l.warm) cls += " warm";
  if (isStale) cls += " flag-danger";
  else if (isDue) cls += " flag";
  card.className = cls;
  card.tabIndex = 0;
  card.draggable = !App.offline;      // Offline: keine echten Mutationen
  card.dataset.slug = l.slug;
  card.dataset.status = l.status;
  card.dataset.warm = l.warm ? "1" : "";
  card.addEventListener("dragstart", e => {
    card.classList.add("dragging");
    e.dataTransfer.effectAllowed = "move";
    e.dataTransfer.setData("text/plain", l.slug);
    App.dragSlug = l.slug;
  });
  card.addEventListener("dragend", () => {
    card.classList.remove("dragging");
    App.dragSlug = null;
    document.querySelectorAll(".column.drop-target").forEach(c => c.classList.remove("drop-target"));
  });

  const flag = isStale
    ? `<span class="flag-dot danger" title="Keine Antwort > 14 Tage"></span>`
    : (isDue ? `<span class="flag-dot warn" title="Wiedervorlage fällig"></span>` : "");
  const warmBadge = l.warm ? `<span class="warm-badge">warm</span>` : "";

  const meta = [];
  if (l.kontaktiert_am) meta.push(`<span><b>Kontakt:</b> ${fmtDate(l.kontaktiert_am)}</span>`);
  if (l.wiedervorlage) meta.push(`<span><b>WV:</b> ${fmtDate(l.wiedervorlage)}</span>`);

  const na = l.next_action || "";
  const naLabel = NEXT_ACTION_LABEL[na] || "";
  const naClass = NEXT_ACTION_CLASS[na] || "na-pruefen";
  card.innerHTML = `
    <div class="card-top">
      <div class="card-firma">${esc(l.firma)}</div>
      <div style="display:flex;gap:6px;align-items:center">${flag}${warmBadge}</div>
    </div>
    <span class="badge ${STATUS_CLASS[l.status] || "s-ink"}" style="margin-top:9px">${statusLabel(l.status)}</span>
    ${naLabel ? `<span class="na-badge ${naClass}">${esc(naLabel)}</span>` : ""}
    ${l.schwaeche ? tagBadges(l.schwaeche) : ""}
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

  const warm = l.warm === true;
  const email = (l.kontakt && l.kontakt.email) || "";
  const missing = warm ? missingInfo(l) : [];
  const readyToSend = warm && outreachReadinessOk(l);
  const btnDisabledAttr = readyToSend ? "" :
    `disabled title="${missing.length ? esc(missing[0]) : 'Lead erst qualifizieren'}"`;
  const outreachBlock = warm ? `
      <div class="whatsmissing">
        <span class="wm-label">Kontakt-Readiness</span>
        ${missing.length
          ? missing.map(m => `<span class="wm-chip">${esc(m)}</span>`).join("")
          : `<span class="wm-ok">vollständig — bereit zum Anschreiben</span>`}
      </div>
      <div class="field" style="margin-bottom:14px">
        <span>E-Mail</span>
        <div class="action-row">
          <input type="email" id="act-email" value="${esc(email)}" placeholder="info@betrieb.de" />
          <button class="btn btn-ghost btn-sm" id="act-email-btn">Speichern</button>
        </div>
      </div>
      <div class="field" style="margin-bottom:14px">
        <button class="btn btn-accent" id="act-outreach-btn" ${btnDisabledAttr}>Anschreiben vorbereiten</button>
      </div>` : `
      <div class="whatsmissing">
        <span class="wm-label">Anschreiben</span>
        <span class="wm-hint">Lead erst qualifizieren (Status ≥ in_klärung), dann anschreiben.</span>
      </div>`;

  let warmFields = "";
  if (l.warm) {
    const k = l.kontakt || {};
    const gmaps = l.google_eintrag || googleMapsLink(l.firma, l.adresse || l.ort || "");
    const rows = [
      ["Priorität", l.prioritaet], ["Ort", l.ort], ["Branche", l.branche],
      ["Website", l.website ? `<a href="https://${l.website.replace(/^https?:\/\//, "")}" target="_blank" rel="noopener">${esc(l.website)}</a>` : null],
      ["Google-Eintrag", gmaps ? `<a href="${esc(gmaps)}" target="_blank" rel="noopener">Eintrag ↗</a>` : null],
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

  const ps = l.prototyp_state || { status: "none", url: null };
  // URL nur anzeigen wenn tatsächlich published
  const protoUrl = (ps.status === "published" && ps.url) ? ps.url : "";
  // Status-Label für Cockpit-Anzeige
  const PROTO_STATUS_LABEL = {
    none: "Kein Auftrag",
    pending: "Auftrag offen",
    draft_ready: "Entwurf lokal bereit",
    approved_local: "Lokal freigegeben",
    published: "Veröffentlicht",
    rework: "Überarbeitung nötig",
    archived: "Archiviert",
  };
  const protoStatusLabel = PROTO_STATUS_LABEL[ps.status] || ps.status;
  // Aktions-Buttons je nach aktuellem Status
  const protoActionBtns = (() => {
    const s = ps.status;
    const btns = [];
    // Manuelle Fallback: Design-Prompt kopieren (immer sichtbar, markiert als manuell)
    btns.push(`<button class="btn btn-ghost btn-sm" id="act-proto-copy-btn" title="Manueller Fallback: Prompt in Claude Design einfügen, HTML zurück per Auftrag einspeisen">📋 Design-Prompt (manuell)</button>`);
    if (s === "none" || s === "rework") {
      btns.push(`<button class="btn btn-accent btn-sm" id="act-proto-request-btn">Auftrag anlegen</button>`);
    }
    if (s === "draft_ready") {
      btns.push(`<button class="btn btn-accent btn-sm" id="act-proto-approve-btn">Lokal freigeben</button>`);
      btns.push(`<button class="btn btn-ghost btn-sm" id="act-proto-rework-btn">Überarbeitung</button>`);
    }
    if (s === "approved_local") {
      btns.push(`<button class="btn btn-accent btn-sm" id="act-proto-publish-btn">Oeffentlichen Link erstellen</button>`);
    }
    if (protoUrl) {
      btns.push(`<a class="btn btn-ghost btn-sm" href="${esc(protoUrl)}" target="_blank" rel="noopener">Demo öffnen ↗</a>`);
    }
    if (s !== "none" && s !== "archived") {
      btns.push(`<button class="btn btn-ghost btn-sm" id="act-proto-archive-btn">Archivieren</button>`);
    }
    return btns.join(" ");
  })();
  const prototypBlock = `
      <div class="field" style="margin-bottom:14px">
        <span>Prototyp <small style="font-weight:normal;opacity:.7">${esc(protoStatusLabel)}</small></span>
        <div class="action-row" style="flex-wrap:wrap;gap:6px">
          ${protoActionBtns}
        </div>
        ${ps.status === "none" ? `<div class="field-hint" style="margin-top:6px">Auftrag anlegen → HTML aus Claude Design einspeisen → lokal prüfen → freigeben.</div>` : ""}
      </div>`;

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

      ${buildPriorityBlock(l)}
      ${l.schwaeche ? `<div class="drawer-section"><h3>Schwäche</h3>${tagBadges(l.schwaeche)}</div>` : ""}

      <div class="drawer-section">
        <h3>Stammdaten</h3>
        <div class="field-grid">
          ${(!warm && l.website) ? `<div class="frow"><span class="fk">Website</span><span class="fv"><a href="https://${l.website.replace(/^https?:\/\//, "")}" target="_blank" rel="noopener">${esc(l.website)}</a></span></div>` : ""}
          ${(!warm && l.google_eintrag) ? `<div class="frow"><span class="fk">Google-Eintrag</span><span class="fv"><a href="${esc(l.google_eintrag)}" target="_blank" rel="noopener">Eintrag ↗</a></span></div>` : ""}
          ${(!warm && l.adresse) ? `<div class="frow"><span class="fk">Adresse</span><span class="fv">${esc(l.adresse)}</span></div>` : ""}
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
        ${outreachBlock}
        ${prototypBlock}
        <div class="field">
          <span>Notiz hinzufügen</span>
          <textarea id="act-note" placeholder="Notiz… (bei „inaktiv“ = Grund)"></textarea>
          <div class="note-actions">
            ${l.status === "inaktiv"
              ? ""
              : `<button class="btn btn-ghost btn-sm" id="act-inaktiv-btn" title="Setzt Status auf „inaktiv“ und speichert die Notiz als Grund">⏸ Auf inaktiv setzen</button>`}
            <button class="btn btn-accent btn-sm" id="act-note-btn">Hinzufügen</button>
          </div>
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
  const inaktivBtn = document.getElementById("act-inaktiv-btn");
  if (inaktivBtn) inaktivBtn.onclick = async () => {
    const grund = document.getElementById("act-note").value.trim();
    if (!grund) {
      toast("Bitte kurz den Grund als Notiz eintragen", "error");
      document.getElementById("act-note").focus();
      return;
    }
    // Erst Grund als Notiz sichern, dann Status setzen — beide über die App (kein direkter Datei-Zugriff).
    await doAction(async () => {
      await post(`/api/leads/${slug}/note`, { text: `Inaktiv: ${grund}` });
      await post(`/api/leads/${slug}/status`, { status: "inaktiv" });
    }, "Auf inaktiv gesetzt");
  };

  const emailBtn = document.getElementById("act-email-btn");
  if (emailBtn) emailBtn.onclick = async () => {
    const em = document.getElementById("act-email").value.trim();
    if (!em) { toast("E-Mail ist leer", "error"); return; }
    await doAction(() => post(`/api/leads/${slug}/email`, { email: em }), "E-Mail gespeichert");
  };
  const outreachBtn = document.getElementById("act-outreach-btn");
  if (outreachBtn) outreachBtn.onclick = () => openOutreach(slug);
  // Prototyp-Buttons
  const protoCopyBtn = document.getElementById("act-proto-copy-btn");
  if (protoCopyBtn) protoCopyBtn.onclick = () => copyPrototypPrompt(slug);

  const protoRequestBtn = document.getElementById("act-proto-request-btn");
  if (protoRequestBtn) protoRequestBtn.onclick = async () => {
    await doAction(() => post(`/api/leads/${slug}/prototyp/request`, {}), "Prototyp-Auftrag angelegt");
  };

  const protoApproveBtn = document.getElementById("act-proto-approve-btn");
  if (protoApproveBtn) protoApproveBtn.onclick = async () => {
    await doAction(() => post(`/api/leads/${slug}/prototyp/approve`, {}), "Lokal freigegeben");
  };

  const protoReworkBtn = document.getElementById("act-proto-rework-btn");
  if (protoReworkBtn) protoReworkBtn.onclick = async () => {
    await doAction(() => post(`/api/leads/${slug}/prototyp/rework`, {}), "Zur Überarbeitung markiert");
  };

  const protoPublishBtn = document.getElementById("act-proto-publish-btn");
  if (protoPublishBtn) protoPublishBtn.onclick = async () => {
    if (!confirm("Oeffentlichen Link erstellen? Damit wird die Demo per Git-Push veröffentlicht.")) return;
    await doAction(() => post(`/api/leads/${slug}/prototyp/publish`, {}), "Demo veröffentlicht");
  };

  const protoArchiveBtn = document.getElementById("act-proto-archive-btn");
  if (protoArchiveBtn) protoArchiveBtn.onclick = async () => {
    await doAction(() => post(`/api/leads/${slug}/prototyp/archive`, {}), "Prototyp archiviert");
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
  App.newLeadTags = new Set();
  renderTagPicker(document.getElementById("new-lead-tags"), App.newLeadTags);
  setTimeout(() => form.querySelector("input[name=firma]").focus(), 50);
}
function closeModal() { document.getElementById("modal-scrim").hidden = true; }

// Generischer Schwäche-Tag-Picker: festes Set + bereits gewählte eigene Tags, Klick toggelt.
function renderTagPicker(host, sel) {
  if (!host) return;
  const all = [...SCHWAECHE_TAGS];
  sel.forEach(t => { if (!all.includes(t)) all.push(t); });
  host.innerHTML = all.map(t =>
    `<button type="button" class="tag-chip${sel.has(t) ? " on" : ""}" data-tag="${esc(t)}">${esc(t)}</button>`
  ).join("");
  host.querySelectorAll(".tag-chip").forEach(b => b.addEventListener("click", () => {
    const t = b.dataset.tag;
    if (sel.has(t)) sel.delete(t); else sel.add(t);
    renderTagPicker(host, sel);
  }));
}

// Eigenen Tag aus einem Textfeld ins Set übernehmen und neu rendern.
function addTagFromInput(inputEl, sel, host) {
  const val = (inputEl.value || "").trim();
  if (!val) return;
  sel.add(val);
  inputEl.value = "";
  renderTagPicker(host, sel);
}

async function submitNewLead(e) {
  e.preventDefault();
  const form = e.target;
  const firma = form.firma.value.trim();
  const schwaeche = [...App.newLeadTags].join(", ");
  const notiz = form.notiz.value.trim();
  const errEl = document.getElementById("new-lead-error");
  errEl.hidden = true;
  if (!firma) { errEl.textContent = "Bitte Firma ausfüllen."; errEl.hidden = false; return; }
  if (!App.newLeadTags.size) { errEl.textContent = "Bitte mindestens einen Schwäche-Tag wählen."; errEl.hidden = false; return; }

  if (App.offline) {
    closeModal();
    toast("Offline (Demo-Daten) — Lead nicht gespeichert", "error");
    return;
  }
  try {
    await post("/api/leads", { firma, schwaeche, notiz });
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
  const cf = App.candFilter;
  const kand = run.kandidaten || [];
  // Übernommene Leads (lead_angelegt) leben ab jetzt in der Pipeline → in Discovery ausblenden.
  const abgelehnt = kand.filter(c => c.status === "abgelehnt");
  const uebernommen = kand.filter(c => c.lead_angelegt && c.status !== "abgelehnt");
  const offen = kand.filter(c => c.status !== "abgelehnt" && !c.lead_angelegt);

  const rejectedToggle = abgelehnt.length
    ? `<button class="btn btn-ghost btn-sm" id="toggle-rejected">${
        App.showRejected ? "Abgelehnte ausblenden" : `Abgelehnte zeigen (${abgelehnt.length})`}</button>`
    : "";

  host.innerHTML = `
    <div class="run-detail-head">
      <div>
        <h2>${esc(run.branche)} · ${esc(run.stadtteil)}</h2>
        <div class="rh-sub">${fmtDate(run.erstellt)} · ${offen.length} offen${
          uebernommen.length ? ` · ${uebernommen.length} übernommen` : ""}${
          abgelehnt.length ? ` · ${abgelehnt.length} abgelehnt` : ""}</div>
      </div>
    </div>
    <div class="bulk-bar">
      <button class="btn btn-accent btn-sm" id="bulk-uebernehmen">Alle „keine_website“ übernehmen →</button>
      ${rejectedToggle}
    </div>
    <div class="cand-filter">
      <div class="seg" role="group" aria-label="Kandidaten filtern">
        <button class="seg-btn ${cf.mode === "alle" ? "on" : ""}" data-fmode="alle">Alle</button>
        <button class="seg-btn ${cf.mode === "keine_website" ? "on" : ""}" data-fmode="keine_website">Ohne Website</button>
        <button class="seg-btn ${cf.mode === "mit_website" ? "on" : ""}" data-fmode="mit_website">Mit Website</button>
        <button class="seg-btn ${cf.mode === "veraltet" ? "on" : ""}" data-fmode="veraltet">Veraltete Website</button>
      </div>
      <label class="score-filter">
        <span>Score ≥ <b id="score-val">${cf.minScore}</b></span>
        <input type="range" id="score-range" min="0" max="100" step="5" value="${cf.minScore}" />
      </label>
    </div>
    <div id="cand-list"></div>`;

  const list = document.getElementById("cand-list");
  const basis = App.showRejected ? [...offen, ...abgelehnt] : offen;
  const sichtbar = basis.filter(candMatchesFilter);
  if (!sichtbar.length) {
    list.innerHTML = !kand.length
      ? emptyState("📭", "Keine Kandidaten", "Dieser Lauf enthält keine Einträge.")
      : (offen.length
          ? emptyState("🔍", "Kein Treffer", "Kein Kandidat passt zum Filter. Schwelle senken oder Filter zurücksetzen.")
          : emptyState("✓", "Alle bearbeitet", "Alle Kandidaten dieses Laufs sind übernommen oder abgelehnt."));
  } else {
    sichtbar.forEach(c => list.appendChild(candCard(c, file)));
  }

  document.getElementById("bulk-uebernehmen").onclick = async () => {
    await doDiscoveryAction(
      () => post("/api/discovery/uebernehmen", { file, which: "auto" }),
      res => uebernahmeMsg(res)
    );
  };
  const tgl = document.getElementById("toggle-rejected");
  if (tgl) tgl.onclick = () => { App.showRejected = !App.showRejected; renderRunDetail(); };

  host.querySelectorAll("[data-fmode]").forEach(b => {
    b.onclick = () => { App.candFilter.mode = b.dataset.fmode; renderRunDetail(); };
  });
  const range = document.getElementById("score-range");
  if (range) {
    // Live-Vorschau der Zahl beim Ziehen, Re-Render erst beim Loslassen (kein Flackern).
    range.oninput = () => { document.getElementById("score-val").textContent = range.value; };
    range.onchange = () => { App.candFilter.minScore = Number(range.value); renderRunDetail(); };
  }
}

function candCard(c, file) {
  const rejected = c.status === "abgelehnt";
  const el = document.createElement("div");
  el.className = "cand" + (rejected ? " cand-abgelehnt" : "");

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
  const gmaps = c.google_url || googleMapsLink(c.firma, c.adresse || "");

  let actions;
  if (rejected) {
    actions = `<button class="btn btn-ghost btn-sm" data-restore>↩ Wiederherstellen</button>`;
  } else if (c.lead_angelegt) {
    actions = `<span class="cand-done">✓ als Lead angelegt</span>`;
  } else {
    actions = `<button class="btn btn-accent btn-sm" data-uebernehmen>→ Lead</button>
               <button class="btn btn-ghost btn-sm" data-ablehnen>Ablehnen</button>`;
  }

  // Abgelehnte Karte: reduziert (kein Status-/URL-Editor), nur Wiederherstellen.
  const actionRow = rejected
    ? `<div class="cand-actions">${actions}</div>`
    : `<div class="cand-actions">
      <div class="field"><span>Status</span><select data-status>${statusOpts}</select></div>
      <div class="field url"><span>URL (optional)</span><input type="text" data-url placeholder="https://…" value="${esc(c.gefundene_url || "")}" /></div>
      <button class="btn btn-ghost btn-sm" data-setstatus>Speichern</button>
      ${actions}
    </div>`;

  el.innerHTML = `
    <div class="cand-top">
      <div>
        <div class="cand-firma">${esc(c.firma)}</div>
        <div class="cand-addr">${esc(c.adresse || "")}</div>
        ${gmaps ? `<a class="cand-gmaps" href="${esc(gmaps)}" target="_blank" rel="noopener">Google-Eintrag ↗</a>` : ""}
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
    ${actionRow}`;

  const setBtn = el.querySelector("[data-setstatus]");
  if (setBtn) setBtn.onclick = async () => {
    const status = el.querySelector("[data-status]").value;
    const url = el.querySelector("[data-url]").value.trim();
    await doDiscoveryAction(
      () => post("/api/discovery/setstatus", { file, id: c.id, status, url }),
      () => "Status gespeichert"
    );
  };
  const ueb = el.querySelector("[data-uebernehmen]");
  if (ueb) ueb.onclick = () => openUebernehmeDialog(file, c);
  const abl = el.querySelector("[data-ablehnen]");
  if (abl) abl.onclick = async () => {
    await doDiscoveryAction(
      () => post("/api/discovery/reject", { file, id: c.id }),
      () => `„${c.firma}“ abgelehnt`
    );
  };
  const res = el.querySelector("[data-restore]");
  if (res) res.onclick = async () => {
    await doDiscoveryAction(
      () => post("/api/discovery/restore", { file, id: c.id }),
      () => `„${c.firma}“ wiederhergestellt`
    );
  };
  return el;
}

/* Klartext-Meldung für Übernahme-Ergebnis ({angelegt:[], uebersprungen:[]}). */
function uebernahmeMsg(res) {
  const a = (res && res.angelegt) || [];
  const u = (res && res.uebersprungen) || [];
  if (a.length && !u.length) return a.length === 1 ? `Lead angelegt: ${a[0]}` : `${a.length} Leads angelegt`;
  if (!a.length && u.length) return u.length === 1 ? `Bereits vorhanden: ${u[0]}` : `${u.length} bereits vorhanden`;
  if (a.length && u.length) return `${a.length} angelegt, ${u.length} bereits vorhanden`;
  return "Nichts zu übernehmen";
}

/* Übernahme-Dialog: Website-URL + Notiz erfassen, dann Kandidaten als Lead anlegen. */
function openUebernehmeDialog(file, c) {
  if (App.offline) { toast("Offline (Demo-Daten) — keine echte Aktion", "error"); return; }
  const scrim = document.getElementById("ueber-scrim");
  document.getElementById("ueber-firma").textContent = c.firma;
  const urlEl = document.getElementById("ueber-url");
  const notizEl = document.getElementById("ueber-notiz");
  urlEl.value = c.gefundene_url || c.website || "";   // ggf. in Tier-2 gefundene URL vorbelegen
  notizEl.value = "";
  App.ueberTags = new Set();
  renderTagPicker(document.getElementById("ueber-tags"), App.ueberTags);
  document.getElementById("ueber-tag-custom").value = "";
  scrim.hidden = false;
  setTimeout(() => urlEl.focus(), 50);

  const confirmBtn = document.getElementById("ueber-confirm");
  const closeEls = scrim.querySelectorAll("[data-ueber-close]");
  const close = () => {
    scrim.hidden = true;
    confirmBtn.onclick = null;
    closeEls.forEach(b => (b.onclick = null));
  };
  closeEls.forEach(b => (b.onclick = close));
  confirmBtn.onclick = async () => {
    const website = urlEl.value.trim();
    const notiz = notizEl.value.trim();
    const schwaeche = [...App.ueberTags].join(", ");   // leer → Backend nutzt Auto-Schwäche
    close();
    await doDiscoveryAction(
      () => post("/api/discovery/uebernehmen", { file, which: [c.id], website, notiz, schwaeche }),
      res => uebernahmeMsg(res)
    );
  };
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
   OUTREACH-WIZARD
   ===================================================================== */

/* Gibt den Outreach-Overlay-Container zurück (lazy-create, separate von #modal-scrim). */
function getOutreachScrim() {
  let scrim = document.getElementById("outreach-scrim");
  if (!scrim) {
    scrim = document.createElement("div");
    scrim.id = "outreach-scrim";
    scrim.className = "modal-scrim";
    scrim.hidden = true;
    document.body.appendChild(scrim);
    scrim.addEventListener("click", e => { if (e.target === scrim) { scrim.hidden = true; scrim.innerHTML = ""; } });
  }
  return scrim;
}

/* Outreach-Wizard: Felder vorbefüllt aus dem Lead, sendet Draft-Auftrag ans Backend. */
function openOutreach(slug) {
  const l = App.state.leads.find(x => x.slug === slug);
  if (!l) return;
  const pstate = l.prototyp_state || {};
  // W4.2: Demo-Link nur bei published — draft_ready/approved_local zählt nicht
  const protoUrl = pstate.status === "published" ? (pstate.url || "") : "";
  const linkSel = protoUrl ? " selected" : "";
  const keinerSel = protoUrl ? "" : " selected";
  const host = getOutreachScrim();
  host.innerHTML = `
    <div class="modal modal-wide" role="dialog" aria-modal="true">
      <h2 class="modal-title">Lead anschreiben — ${esc(l.firma)}</h2>
      <form id="outreach-form" class="modal-form">
        <label class="field"><span>Angebot / Leistung</span>
          <input name="angebot" required value="${esc(l.ucp || "")}" placeholder="z.B. Website-Relaunch zum Festpreis" /></label>
        <label class="field"><span>Nutzen (ROI)</span>
          <input name="nutzen" value="${esc(l.roi_these || "")}" placeholder="z.B. mehr Anfragen über mobile Nutzer" /></label>
        <label class="field"><span>Ton</span>
          <select name="ton"><option>Sie, professionell</option><option>Sie, locker</option><option>Du, locker</option></select></label>
        <label class="field"><span>Call-to-Action</span>
          <input name="cta" value="kurzes Telefonat vorschlagen" /></label>
        <label class="field"><span>Prototyp</span>
          <select name="proto_mode"><option value="keiner"${keinerSel}>keiner</option><option value="link"${linkSel}>Link</option><option value="anhang">Anhang</option></select></label>
        <label class="field"><span>Prototyp-Link (falls Link)</span>
          <input name="proto_link" value="${esc(protoUrl)}" placeholder="https://…" /></label>
        <label class="field"><span>Betreff (optional)</span>
          <input name="betreff" placeholder="leer lassen = Claude schlägt vor" /></label>
        <p class="form-error" id="outreach-error" hidden></p>
        <div class="modal-actions">
          <button type="button" class="btn btn-ghost" id="outreach-cancel">Abbrechen</button>
          <button type="submit" class="btn btn-accent">Entwurf erstellen</button>
        </div>
      </form>
    </div>`;
  host.hidden = false;
  document.getElementById("outreach-cancel").onclick = () => { host.hidden = true; host.innerHTML = ""; };
  document.getElementById("outreach-form").onsubmit = (e) => submitOutreach(e, slug);
}

async function submitOutreach(e, slug) {
  e.preventDefault();
  const f = e.target;
  const req = {
    angebot: f.angebot.value.trim(),
    nutzen: f.nutzen.value.trim(),
    ton: f.ton.value,
    cta: f.cta.value.trim(),
    betreff: f.betreff.value.trim(),
    prototyp: { mode: f.proto_mode.value, url: f.proto_link.value.trim() },
  };
  const err = document.getElementById("outreach-error");
  if (!req.angebot) { err.textContent = "Angebot ist Pflicht."; err.hidden = false; return; }
  try {
    await post(`/api/leads/${slug}/outreach/request`, req);
    const host = getOutreachScrim();
    host.hidden = true;
    host.innerHTML = "";
    toast("Auftrag erstellt — Claude Code entwirft…", "ok");
    pollOutreach(slug);
  } catch (e2) { err.textContent = e2.message || "Fehler"; err.hidden = false; }
}

/* =====================================================================
   OUTREACH-VORSCHAU & POLL
   ===================================================================== */

/* Pollt den Outreach-Zustand, bis der Entwurf 'ready' ist, dann Vorschau zeigen. */
async function pollOutreach(slug, tries = 0) {
  if (tries > 60) { toast("Zeitüberschreitung — läuft Claude Code?", "error"); return; }
  let state;
  try { state = await api(`/api/leads/${slug}/outreach`); } catch (e) { toast(e.message, "error"); return; }
  if (state.status === "ready" && state.draft) { showOutreachPreview(slug, state.draft); return; }
  if (state.status === "sent") { toast("bereits gesendet", "ok"); return; }
  setTimeout(() => pollOutreach(slug, tries + 1), 1500);
}

/* Pollt den Prototyp-Zustand bis 'ready', lädt dann State neu und öffnet den Drawer. */
/* Baut aus dem Lead einen fertigen Prompt für Claude Design (Artifact-One-Pager). */
function buildPrototypPrompt(l) {
  const info = [];
  const add = (k, v) => { if (v && String(v).trim()) info.push(`${k}: ${String(v).trim()}`); };
  add("Firma", l.firma);
  add("Branche/Ort", [l.branche, l.ort].filter(Boolean).join(" · "));
  add("Adresse", l.adresse);
  add("Aktuelle Website", l.website || "keine");
  add("Google-Eintrag", l.google_eintrag);
  add("Konkrete Schwäche(n), die die neue Seite besser lösen muss", splitTags(l.schwaeche).join(", "));
  const notizen = (Array.isArray(l.notizen) && l.notizen.length) ? l.notizen.join(" | ") : (l.notiz || "");
  add("Notiz", notizen);
  add("UCP", l.ucp);
  return [
    `Baue mir eine einseitige Website (One-Pager) als Artifact — modern, hochwertig und mit eigenständiger Handschrift — für diesen echten Betrieb aus Hamburg: ${l.firma || l.slug}`,
    "",
    "Betrieb:",
    ...info.map(x => `- ${x}`),
    "",
    "Auftrag:",
    "- Zielgruppe sind lokale Kund*innen dieses Betriebs. Die Seite muss die genannte(n) Schwäche(n) sichtbar besser lösen als der Status quo.",
    "- Design: klare, eigenständige Gestaltung statt generischem Template-Look — zur Branche und zum Ort passend. Durchdachtes Farb- und Typo-System, großzügiges Layout, ein klarer Call-to-Action (Termin/Anruf/Kontakt).",
    "- Sinnvolle Sektionen zur Branche wählen (z. B. Hero, Leistungen, Über uns, Öffnungszeiten/Anfahrt, Kontakt/CTA).",
    "- Mobile-first responsive, kein horizontaler Scroll, funktioniert von 320px bis Desktop.",
    "",
    "Technische Vorgaben (wichtig — sonst lädt das Artifact nicht und lässt sich nicht live schalten):",
    "- Ein einzelnes, komplett self-contained HTML-Dokument, CSS und JS inline.",
    "- Keine externen Ressourcen: keine CDN-Skripte, keine externen Fonts/Stylesheets, keine remote Bilder. System-Font-Stack nutzen.",
    "- Bilder nur als Inline-SVG, CSS-Gradients/-Muster oder data:-URI — keine echten Fotos verlinken.",
    "",
    "Inhaltsregeln:",
    "- Keine erfundenen Fakten über den Betrieb hinaus: keine erfundenen Preise, Bewertungen, Zahlen oder Adressen. Nur die oben gegebenen Angaben verwenden.",
    "- Wo echte Inhalte fehlen, neutrale und klar als Platzhalter erkennbare Texte einsetzen.",
    "",
    "Ergebnis: ein einzelnes HTML-Artifact, das ich direkt live schalten kann."
  ].join("\n");
}

/* Prompt in die Zwischenablage kopieren; Fallback-Dialog, falls die Clipboard-API blockt. */
async function copyPrototypPrompt(slug) {
  const l = App.state.leads.find(x => x.slug === slug);
  if (!l) return;
  const text = buildPrototypPrompt(l);
  try {
    await navigator.clipboard.writeText(text);
    toast("Design-Prompt kopiert — in Claude Design einfügen", "ok");
  } catch (e) {
    showCopyFallback(text);
  }
}

/* Fallback: Text im Dialog anzeigen und markieren, damit manuell (Strg+C) kopiert werden kann. */
function showCopyFallback(text) {
  const host = getOutreachScrim();
  host.innerHTML = `
    <div class="modal modal-wide" role="dialog" aria-modal="true">
      <h2 class="modal-title">Design-Prompt kopieren</h2>
      <p class="wm-hint">Automatisches Kopieren wurde blockiert — Text ist markiert, mit Strg+C kopieren.</p>
      <textarea id="copy-fallback-ta" rows="16" style="width:100%">${esc(text)}</textarea>
      <div class="modal-actions"><button class="btn btn-accent" id="copy-fallback-close">Schließen</button></div>
    </div>`;
  host.hidden = false;
  const ta = document.getElementById("copy-fallback-ta");
  ta.focus(); ta.select();
  document.getElementById("copy-fallback-close").onclick = () => { host.hidden = true; host.innerHTML = ""; };
}

function showOutreachPreview(slug, draft) {
  const l = App.state.leads.find(x => x.slug === slug) || {};
  const to = (l.kontakt && l.kontakt.email) || "";
  // Demo-Link nur wenn published
  const ps = l.prototyp_state || {};
  const demoLink = ps.status === "published" && ps.url ? ps.url : (draft.demo_link || "");
  const host = getOutreachScrim();
  host.innerHTML = `
    <div class="modal modal-wide" role="dialog" aria-modal="true">
      <h2 class="modal-title">Vorschau — ${esc(l.firma || slug)}</h2>
      <div class="mail-preview">
        <div class="mp-row"><span>An</span><b>${esc(to)}</b></div>
        <div class="mp-row"><span>Betreff</span><b>${esc(draft.betreff)}</b></div>
        ${demoLink ? `<div class="mp-row"><span>Demo-Link</span><a href="${esc(demoLink)}" target="_blank" rel="noopener">${esc(demoLink)}</a></div>` : ""}
        <pre class="mp-body">${esc(draft.text)}</pre>
      </div>
      <label class="field" style="margin:10px 0 4px">
        <span>Sendemodus</span>
        <select id="prev-send-mode">
          <option value="draft" selected>Entwurf (.eml ablegen) — Standard</option>
          <option value="direct">Direkt senden (SMTP)</option>
        </select>
      </label>
      <p class="wm-hint" style="margin-bottom:10px">
        Direkt senden nur nach bewusster Auswahl. Standard legt die Mail als .eml-Datei ab.
      </p>
      <p class="form-error" id="outreach-send-error" hidden></p>
      <div class="modal-actions">
        <button type="button" class="btn btn-ghost" id="prev-cancel">Abbrechen</button>
        <button type="button" class="btn btn-accent" id="prev-send">Freigeben &amp; ausführen</button>
      </div>
    </div>`;
  host.hidden = false;
  document.getElementById("prev-cancel").onclick = () => { host.hidden = true; host.innerHTML = ""; };
  document.getElementById("prev-send").onclick = async () => {
    const err = document.getElementById("outreach-send-error");
    const sendMode = document.getElementById("prev-send-mode").value;
    try {
      const res = await post(`/api/leads/${slug}/outreach/send`, { send_mode: sendMode });
      host.hidden = true; host.innerHTML = "";
      toast(res.send_mode === "direct" ? "Mail gesendet (SMTP)" : "Entwurf (.eml) abgelegt", "ok");
      await loadState();
    } catch (e) { err.textContent = e.message || "Sendefehler"; err.hidden = false; }
  };
}

/* =====================================================================
   PRIORITÄT + NÄCHSTE AKTION — Hilfsfunktionen
   ===================================================================== */

/* Baut den Prioritäts-Breakdown-Block für den Drawer. */
function buildPriorityBlock(l) {
  const prio = l.priority;
  const na = l.next_action || "";
  const naLabel = NEXT_ACTION_LABEL[na] || na;
  const naClass = NEXT_ACTION_CLASS[na] || "na-pruefen";

  const naHtml = naLabel
    ? `<div class="prio-action"><span class="na-badge ${naClass}">${esc(naLabel)}</span><span class="prio-action-label">Nächste Aktion</span></div>`
    : "";

  if (!prio || !prio.faktoren) {
    return naHtml ? `<div class="drawer-section">${naHtml}</div>` : "";
  }

  const score = prio.score || 0;
  const faktoren = prio.faktoren;
  const FAKTOR_LABEL = {
    befundstaerke: "Befundstärke",
    segmentpassung: "Segmentpassung",
    datenvollstaendigkeit: "Datenvollständigkeit",
    wiedervorlage_faellig: "Wiedervorlage fällig",
  };
  const rows = Object.entries(faktoren).map(([key, f]) => {
    const dots = "●".repeat(f.wert) + "○".repeat(Math.max(0, 3 - f.wert));
    return `<div class="prio-row">
      <span class="prio-label">${FAKTOR_LABEL[key] || key}</span>
      <span class="prio-dots" aria-label="${f.wert} von 3">${dots}</span>
      <span class="prio-erkl">${esc(f.erklaerung)}</span>
    </div>`;
  }).join("");

  return `
    <div class="drawer-section">
      <h3>Priorität <span class="prio-score-inline">${score}/12</span></h3>
      ${naHtml}
      <div class="prio-breakdown">${rows}</div>
    </div>`;
}

/* =====================================================================
   FOKUS-ANSICHT — Top-Leads nach Priorität
   ===================================================================== */

function renderFokus() {
  const host = document.getElementById("fokus-container");
  if (!host) return;
  const s = App.state;
  if (!s || !s.leads || !s.leads.length) {
    host.innerHTML = emptyState("🌱", "Keine Leads", "Noch keine Leads in der Pipeline.");
    return;
  }

  // Aktive Leads (nicht verloren/inaktiv), nach score absteigend sortieren
  const aktiv = s.leads.filter(l => !["verloren", "inaktiv"].includes(l.status));
  const sorted = [...aktiv].sort((a, b) => {
    const sa = (a.priority && a.priority.score) || 0;
    const sb = (b.priority && b.priority.score) || 0;
    return sb - sa;
  });

  const heute = sorted.filter(l => {
    const wv = l.wiedervorlage || "";
    const naechsteAktion = l.next_action || "";
    if (wv && wv <= s.today) return true;  // Wiedervorlage fällig
    if (naechsteAktion === "nachfassen") return true;
    return false;
  });
  const top = sorted.slice(0, 5);

  // Doppelte ausblenden: in "Heute" liegende auch in Top zeigen, aber als Gruppe
  const heuteSlugs = new Set(heute.map(l => l.slug));
  const topOhneHeute = top.filter(l => !heuteSlugs.has(l.slug));

  const dueSet = new Set((s.report.wiedervorlage_faellig || []).map(r => r.slug));
  const staleSet = new Set((s.report.keine_antwort || []).map(r => r.slug));

  function fokusCard(l) {
    const prio = l.priority || {};
    const score = prio.score != null ? prio.score : "–";
    const na = l.next_action || "";
    const naLabel = NEXT_ACTION_LABEL[na] || "";
    const naClass = NEXT_ACTION_CLASS[na] || "na-pruefen";
    const isDue = dueSet.has(l.slug);
    const isStale = staleSet.has(l.slug);
    const flag = isStale
      ? `<span class="flag-dot danger" title="Keine Antwort > 14 Tage"></span>`
      : (isDue ? `<span class="flag-dot warn" title="Wiedervorlage fällig"></span>` : "");

    // Faktor-Zeilen kompakt
    const FAKTOR_SHORT = {
      befundstaerke: "Befund",
      segmentpassung: "Segment",
      datenvollstaendigkeit: "Daten",
      wiedervorlage_faellig: "Wiedervorlage",
    };
    const faktoren = prio.faktoren || {};
    const faktorHtml = Object.entries(faktoren).map(([key, f]) => {
      const dots = "●".repeat(f.wert) + "○".repeat(Math.max(0, 3 - f.wert));
      return `<div class="fk-row" title="${esc(f.erklaerung)}">
        <span class="fk-name">${FAKTOR_SHORT[key] || key}</span>
        <span class="fk-dots">${dots}</span>
      </div>`;
    }).join("");

    return `<div class="fokus-card reveal" style="cursor:pointer" data-slug="${esc(l.slug)}">
      <div class="fokus-card-head">
        <div>
          <div class="fokus-firma">${esc(l.firma)}</div>
          <span class="badge ${STATUS_CLASS[l.status] || "s-ink"}">${statusLabel(l.status)}</span>
          ${l.warm ? `<span class="warm-badge">warm</span>` : ""}
        </div>
        <div class="fokus-right">
          ${flag}
          <div class="fokus-score" title="Prioritäts-Score">${score}<span>/12</span></div>
        </div>
      </div>
      ${naLabel ? `<div class="fokus-na"><span class="na-badge ${naClass}">${esc(naLabel)}</span></div>` : ""}
      ${l.schwaeche ? `<div class="fokus-schwaeche">${tagBadges(l.schwaeche)}</div>` : ""}
      <div class="fokus-faktoren">${faktorHtml}</div>
    </div>`;
  }

  let html = "";

  if (heute.length) {
    html += `<div class="fokus-section">
      <h2 class="fokus-section-title">Heute / Fällig</h2>
      <p class="fokus-section-sub">Wiedervorlage fällig oder Nachfassen steht an</p>
      <div class="fokus-grid">${heute.map(fokusCard).join("")}</div>
    </div>`;
  }

  if (topOhneHeute.length) {
    html += `<div class="fokus-section">
      <h2 class="fokus-section-title">Diese Woche — Top-Leads</h2>
      <p class="fokus-section-sub">Höchste Priorität nach Befund, Segment, Datenvollständigkeit und Wiedervorlage</p>
      <div class="fokus-grid">${topOhneHeute.map(fokusCard).join("")}</div>
    </div>`;
  }

  if (!heute.length && !topOhneHeute.length) {
    html = emptyState("✓", "Nichts fällig", "Keine Wiedervorlagen fällig, keine dringenden Leads. Schau in die Pipeline für den Überblick.");
  }

  host.innerHTML = html;

  // Klick auf Karte → Drawer
  host.querySelectorAll(".fokus-card[data-slug]").forEach(card => {
    card.addEventListener("click", () => openDrawer(card.dataset.slug));
  });
}

/* =====================================================================
   HELPERS
   ===================================================================== */

/* Liste fehlender Pflichtinfos eines warmen Leads (für den "Was fehlt"-Block). */
function missingInfo(l) {
  // W4.1: Readiness-Pflichtpunkte spiegeln outreach_readiness() im Backend.
  // Informationelle Fehlpunkte (Website, Prototyp) bleiben als Hinweise erhalten.
  const miss = [];
  if (!l.kontakt || !l.kontakt.email) miss.push("E-Mail fehlt");
  if (!l.schwaeche && !l.anlass) miss.push("Anlass fehlt (Schwäche/Befund)");
  if (!l.ucp && !l.angebot) miss.push("Angebot fehlt (UCP)");
  if (!l.roi_these && !l.nutzen) miss.push("Nutzen fehlt (ROI-These)");
  if (!l.cta) miss.push("CTA fehlt");
  return miss;
}

function outreachReadinessOk(l) {
  // Kurzprüfung ob alle Pflichtpunkte erfüllt sind (spiegelt Backend outreach_readiness).
  if (!l.warm && !l.kalt_freigegeben) return false;
  return missingInfo(l).length === 0;
}

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
  document.getElementById("view-fokus").classList.toggle("is-active", view === "fokus");
  document.getElementById("view-discovery").classList.toggle("is-active", view === "discovery");
}

function init() {
  document.querySelectorAll(".tab").forEach(t => t.addEventListener("click", () => switchView(t.dataset.view)));
  const searchInput = document.getElementById("lead-search");
  const searchClear = document.getElementById("lead-search-clear");
  if (searchInput) {
    searchInput.addEventListener("input", () => {
      App.leadSearch = searchInput.value.trim().toLowerCase();
      if (searchClear) searchClear.hidden = !searchInput.value;
      renderBoard();
    });
    searchInput.addEventListener("keydown", e => { if (e.key === "Escape") { searchInput.value = ""; searchInput.dispatchEvent(new Event("input")); } });
  }
  if (searchClear) searchClear.addEventListener("click", () => { searchInput.value = ""; searchInput.dispatchEvent(new Event("input")); searchInput.focus(); });
  document.getElementById("btn-new-lead").addEventListener("click", openModal);
  document.getElementById("modal-cancel").addEventListener("click", closeModal);
  document.getElementById("new-lead-form").addEventListener("submit", submitNewLead);
  const nlTagHost = document.getElementById("new-lead-tags");
  const nlTagInput = document.getElementById("new-lead-tag-custom");
  document.getElementById("new-lead-tag-add").addEventListener("click", () => addTagFromInput(nlTagInput, App.newLeadTags, nlTagHost));
  nlTagInput.addEventListener("keydown", e => {
    if (e.key === "Enter") { e.preventDefault(); addTagFromInput(nlTagInput, App.newLeadTags, nlTagHost); }
  });
  const ubTagHost = document.getElementById("ueber-tags");
  const ubTagInput = document.getElementById("ueber-tag-custom");
  document.getElementById("ueber-tag-add").addEventListener("click", () => addTagFromInput(ubTagInput, App.ueberTags, ubTagHost));
  ubTagInput.addEventListener("keydown", e => {
    if (e.key === "Enter") { e.preventDefault(); addTagFromInput(ubTagInput, App.ueberTags, ubTagHost); }
  });
  document.getElementById("drawer-scrim").addEventListener("click", closeDrawer);
  document.getElementById("modal-scrim").addEventListener("click", e => { if (e.target.id === "modal-scrim") closeModal(); });
  document.addEventListener("keydown", e => {
    if (e.key === "Escape") { closeDrawer(); closeModal(); }
  });
  loadState();
}

document.addEventListener("DOMContentLoaded", init);
