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
   - **PFLICHT-SUB-SKILL: `frontend-design` invoken**, bevor du HTML schreibst. Prototypen
     sollen distinctive, production-grade wirken — kein generisches „AI-Slop"-Layout. Wähle
     eine klare, zum Betrieb passende Ästhetik (bei Pflege/Gesundheit i.d.R. warm, seriös,
     vertrauenswürdig, hoher Kontrast, große Schrift statt maximalistischem Chaos).
   - **Qualitätsschleife (Pflicht):** nach dem Bauen `impeccable critique` + gezielter
     `polish`/`bolder`-Pass gegen die Rubrik in
     [`docs/superpowers/prototyp-qualitaetsschleife.md`](../../../docs/superpowers/prototyp-qualitaetsschleife.md).
     Sobald ein Hausstil (`DESIGN.md`) existiert, davon ausgehen statt bei null starten.
   - Adressiert die konkrete `schwaeche` des Betriebs (z.B. kein Mobil-Layout → responsive).
   - Spiegelt Branche/Ort, plausibler Firmenname + Leistungen. Kein erfundener Fakt über den
     Betrieb hinaus (keine erfundenen Preise, Bewertungen, Adressen).
   - **Self-contained (überschreibt widersprüchliche Skill-Hinweise)**: HTML + CSS inline,
     KEIN externes CDN/Font/Script (die Seite muss ohne Netz-Abhängigkeiten live funktionieren).
     Statt Google-Fonts distinctive **web-safe Font-Stacks** (z.B. Georgia/Iowan/Palatino für
     warme Serifen, oder eine per `@font-face` als base64 eingebettete Schrift). Atmosphäre über
     inline-SVG/CSS-Gradients/Noise, nicht über externe Assets. Modern, responsive, klarer CTA.
4. **Zurückschreiben (nur lokaler Entwurf):** `POST /api/leads/<slug>/prototyp/draft` mit
   `{"html": "<!doctype html>…"}`. Das Backend speichert das HTML **lokal** und setzt den
   Status auf **`draft_ready`** — es **deployt NICHT** und veröffentlicht nichts. Das Cockpit
   zeigt „Entwurf bereit, lokal prüfbar".
5. **Direkt veröffentlichen (Standard, Shawn-Vorgabe):** Sobald die Rubrik-Gate der
   Qualitätsschleife sitzt, fährst du den Rest **automatisch** durch — kein manueller Klick:
   - `POST …/prototyp/approve` → `approved_local`.
   - `POST …/prototyp/publish` → deployt nach GitHub Pages **und** legt lokal
     `prototypes/<slug>/` mit `index.html` + `info.md` (inkl. Live-Link) an; setzt `published` + URL.
   - Danach Portfolio-Eintrag (`portfolio.add_entry`) mit `muster` + `lernnotiz` (Flywheel) und
     Zeile in `prototypes/README.md` ergänzen.
   - `POST …/prototyp/rework` bzw. `…/archive` für Korrektur bzw. Aussortieren.
   Kanonische Status bleiben `none → pending → draft_ready → approved_local → published`
   (+ `rework`/`archived`). Die Qualitäts-Rubrik ist die einzige Bremse vor dem Publish, nicht
   ein separater Freigabe-Klick.

## Watch-Modus (nahtlos)
Für sofortige Demos: mit dem `/loop`-Skill diese Anleitung in kurzem Intervall laufen lassen
(offene Aufträge abgreifen → HTML bauen → zurückschreiben). Ohne laufendes Claude Code bleibt
der Auftrag `pending`; das Cockpit zeigt „Demo wird gebaut…".

## Grenzen
- Der `draft`-Endpunkt deployt selbst nicht — veröffentlicht wird über den `publish`-Schritt,
  den du nach bestandener Rubrik automatisch fährst. Standardfluss endet bei **`published`**
  (lokaler Ordner `prototypes/<slug>/` + Live-Pages-URL). `publish` ist die einzige Stelle mit
  echtem Git-Push ins Pages-Repo.
- Recht: Die Demo trägt den Firmennamen des Betriebs und wird öffentlich unter Shawns
  Pages-URL sichtbar. Shawn verantwortet den Einsatz pro Lead.
