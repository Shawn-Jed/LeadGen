# LeadGen

Akquise-Cockpit für Festpreis-Web-Projekte in Hamburg. Findet lokale Betriebe mit
Website-Schwächen (Discovery), trackt sie durch die Sales-Pipeline (CRM) und zeigt
alles in einem lokalen Web-Cockpit.

Selfwork-Projekt von Shawn Jedrzejczyk. **Frontend und Backend sind sauber getrennt.**

## Struktur

```
backend/     Python (stdlib-only Server) — JSON-API + CLIs + Logik + Daten + Tests
frontend/    Vanilla JS/HTML/CSS — kein Build-Step, kein npm-Dependency-Baum
docs/        Specs, Pläne, Screenshots
```

Das Backend hat **keine externen Runtime-Dependencies** außer `PyYAML` und `beautifulsoup4`
(für Discovery-Analyse). Das Frontend ist statisch.

## Schnellstart

### Variante A — alles in einem Prozess (einfachster Weg)
```bash
cd backend
python app.py            # http://127.0.0.1:8723  (API + Frontend)
```
`frontend/config.js` steht per Default auf `http://127.0.0.1:8723` — passt.

### Variante B — entkoppelt (zwei Prozesse)
```bash
# Terminal 1 — reine API mit CORS
cd backend
python app.py --api-only            # optional: --cors-origin http://localhost:3000

# Terminal 2 — statisches Frontend
npx serve frontend                  # oder ein beliebiger Static-Server
```
Trägt das Frontend auf einer anderen Origin/Port, in `frontend/config.js` die Backend-URL setzen.

## Kommandozeile (CRM + Discovery)

Immer aus `backend/` ausführen (die CLIs nutzen das aktuelle Verzeichnis als Datenwurzel):

```bash
cd backend
python lead.py neu "Firma GmbH" --schwaeche "keine Mobil-Ansicht"
python lead.py status <slug> kontaktiert
python lead.py report
python discover.py scan "Zahnarzt" "Eppendorf"
```

## Datenmodell

| Was | Wo | Format |
|-----|-----|--------|
| kalte Leads (Pipeline) | `backend/pipeline.md` | Markdown-Tabelle |
| warme Leads (graduiert) | `backend/leads/<slug>.md` | Markdown + YAML-Frontmatter |
| Discovery-Läufe | `backend/discovery/*.json` | JSON |

Alles datei-basiert und versionierbar — kein Datenbank-Server nötig.

## Tests

```bash
cd backend
python -m pytest -q
```

## Status der Subsysteme

- **A Discovery** — Tier 1 (keine Website), Tier 2 (Website-Mängel), Tier 3 (qualitatives Urteil) ✅
- **B Tracking** — datei-basiertes CRM mit Pipeline + Graduierung + Follow-up-Report ✅
- **Cockpit** — Web-UI über die JSON-API ✅
- **D Outreach** — Lead im Cockpit anschreiben: Wizard → Claude Code entwirft → Vorschau → SMTP-Versand ✅
- **C Prototyp** — Opt-in pro Lead: Claude Code baut eine One-Pager-Demo, Deploy nach GitHub Pages (`prototyp`-Repo), URL speist die Outreach-Mail ✅
- **E Portfolio** — geplant

## Outreach (Lead anschreiben)

Im Lead-Detail eines **warmen** Leads (mit E-Mail): Button **„✉ Lead anschreiben"** → Wizard
(Angebot, Prototyp als Link/Anhang, Ton). Der Auftrag wird abgelegt; **Claude Code** entwirft
die Mail (outreach-Skill, `.claude/skills/outreach/`), das Cockpit zeigt eine **Vorschau** —
nach deiner Freigabe („Ja, senden") sendet das Backend per SMTP.

### Setup
`backend/.env` anlegen (Vorlage: `backend/.env.example`), SMTP-Zugang eintragen.
`OUTREACH_SEND_MODE` steuert den Versand:
- `draft` (Default, sicher) — legt die Mail als `.eml` ab, sendet nicht.
- `direct` — echter SMTP-Versand nach der Freigabe.

### Recht (UWG §7)
Jede Mail wird **einzeln** in der Vorschau freigegeben — kein Stapelversand. Ob ein Betrieb
kalt angemailt werden darf, entscheidest du; das System sendet nur nach deiner Bestätigung.

## Prototyp (Live-Demo pro Lead, Subsystem C)

Im Lead-Detail Button **„🎨 Prototyp bauen"** (kalt oder warm). Der Auftrag wird abgelegt;
**Claude Code** baut die One-Pager-HTML (prototyp-Skill, `.claude/skills/prototyp/`), das
Backend committet sie ins öffentliche **`prototyp`-Repo** und GitHub Pages liefert sie live
unter `<PROTOTYP_PAGES_BASE>/<slug>`. Ist die Demo fertig, füllt der Outreach-Wizard den
Prototyp-Link automatisch vor.

### Setup
Öffentliches GitHub-Repo `prototyp` anlegen, GitHub Pages aktivieren (Branch `main`, Root),
lokal auschecken. In `backend/.env`:
- `PROTOTYP_REPO_PATH` — lokaler Pfad zum ausgecheckten `prototyp`-Repo
- `PROTOTYP_PAGES_BASE` — z.B. `https://shawn-jed.github.io/prototyp`
