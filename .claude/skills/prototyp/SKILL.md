---
name: prototyp
description: Use when building acquisition demo one-pagers for leads in LeadGen — offene Prototyp-Aufträge aus dem Cockpit abgreifen, eine maßgeschneiderte One-Pager-HTML der verbesserten Website entwerfen, zurückschreiben (Backend deployt nach GitHub Pages). Trigger: "Prototyp-Aufträge", "Demo bauen", "prototyp draften".
---

# Prototyp — Demo-One-Pager (Subsystem C)

Das Cockpit legt bei „Prototyp bauen" einen Auftrag ab. **Du** (Claude Code) baust die
One-Pager-HTML. Das Backend committet sie ins öffentliche `prototyp`-Repo und liefert die
Live-URL (GitHub Pages) zurück ans Cockpit.

## Voraussetzung
Backend läuft (`cd backend && python app.py`). Basis-URL `http://127.0.0.1:8723`.
`PROTOTYP_REPO_PATH` + `PROTOTYP_PAGES_BASE` in `backend/.env` gesetzt.

## Ablauf
1. **Offene Aufträge holen:** `GET /api/prototyp/pending` → Liste mit `slug`.
2. **Lead-Kontext lesen:** aus `GET /api/state` (Feld `leads`, passender `slug`):
   `firma`, `schwaeche`, `branche`, `ort`, `ucp`.
3. **One-Pager-HTML bauen** aus dem Kontext:
   - Adressiert die konkrete `schwaeche` des Betriebs (z.B. kein Mobil-Layout → responsive).
   - Spiegelt Branche/Ort, plausibler Firmenname + Leistungen. Kein erfundener Fakt über den
     Betrieb hinaus (keine erfundenen Preise, Bewertungen, Adressen).
   - **Self-contained**: HTML + CSS inline, KEIN externes CDN/Font/Script (die Seite muss
     ohne Netz-Abhängigkeiten live funktionieren). Modern, responsive, mit klarem CTA.
4. **Zurückschreiben:** `POST /api/leads/<slug>/prototyp/draft` mit `{"html": "<!doctype html>…"}`.
   Das Backend deployt und setzt den Auftrag auf `ready` (mit Live-URL). Das Cockpit zeigt den Link.

## Watch-Modus (nahtlos)
Für sofortige Demos: mit dem `/loop`-Skill diese Anleitung in kurzem Intervall laufen lassen
(offene Aufträge abgreifen → HTML bauen → zurückschreiben). Ohne laufendes Claude Code bleibt
der Auftrag `pending`; das Cockpit zeigt „Demo wird gebaut…".

## Grenzen
- Du deployst nie selbst — der `draft`-Endpunkt committet+pusht (Backend).
- Recht: Die Demo trägt den Firmennamen des Betriebs und wird öffentlich unter Shawns
  Pages-URL sichtbar. Shawn verantwortet den Einsatz pro Lead.
