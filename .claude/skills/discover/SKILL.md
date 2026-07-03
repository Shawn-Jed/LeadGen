---
name: discover
description: Use when looking for new leads in Hamburg — Betriebe einer Branche finden + Website-Schwächen prüfen (Tier 1+2). Trigger: "finde Leads", "scan Branche X in Stadtteil Y", "discovery", "neue Kandidaten", "website analysieren", "tier 2".
---

# Lead-Discovery (Hamburg, Tier 1)

Findet Hamburger Betriebe ohne auffindbare Website und legt bestätigte Funde als Leads an
(Subsystem B). Bedienung über `python discover.py …` — **immer aus `backend/` ausführen**
(`cd backend`); die CLI nutzt das aktuelle Verzeichnis als Datenwurzel.
Run-Dateien in `backend/discovery/` nur über die CLI ändern, nicht von Hand.

## Ablauf (Tier 1 + Tier 2)

1. **Scannen:**
   `python discover.py scan "<Branche>" "<Stadtteil>"`
   (Stadtteil optional → ganz Hamburg.) Erzeugt eine Run-Datei und meldet, wie viele Kandidaten
   `website_unklar` sind (kein website-Tag in OSM).

2. **Anzeigen:** `python discover.py show <run-datei>` — Liste mit ids/Status/Score.

3. **Gegenprüfen (dein Urteil):** Für JEDEN Kandidaten mit Status `website_unklar`:
   per **WebSearch** suchen (Firmenname + Adresse/„Hamburg").
   - Echte offizielle Website gefunden → `python discover.py setstatus <run> <id> hat_website <url>`
   - Keine Website auffindbar → `python discover.py setstatus <run> <id> keine_website`
   Sei ehrlich: Branchenportal-/Facebook-Einträge sind KEINE eigene Website.

4. **Tier-2-Analyse** (für alle `hat_website`-Kandidaten):
   `python discover.py analyse <run-datei>`
   Lädt HTML, prüft: HTTPS, Viewport-Meta, Copyright-Jahr (veraltet?), Impressum, Kontaktformular.
   Speichert `tier2`-Signale + erhöht Score. Status wird `analysiert`.
   Anschließend `show` aufrufen, um Tier-2-Befunde zu sehen.

5. **Übernehmen:** `python discover.py uebernehmen <run> auto`
   Legt für alle als `keine_website` bestätigten Funde automatisch Leads an (Schwäche:
   „keine auffindbare Website"). Tier-2-analysierte Kandidaten mit hohem Score können
   separat mit expliziten IDs übernommen werden: `uebernehmen <run> 1,3,5`.
   Duplikate werden übersprungen.

## Tier-2-Mängel im Befund

Analysierte Kandidaten erhalten im Feld `befund` eine Mängelliste, z.B.:
`Tier-2-Mängel: kein HTTPS, nicht mobil, veraltet (2009), kein Impressum`

Score-Aufschläge: kein HTTPS +15 / nicht mobil +20 / veraltet +15 / kein Impressum +10 / kein Kontaktformular +10.

## Bekannte Branchen
zahnarzt, arzt/hausarzt, friseur, bäckerei, restaurant/gastronomie, sanitär/klempner,
elektriker, anwalt/kanzlei, tischler/schreiner, autowerkstatt/kfz. Weitere → `BRANCHE_TAGS`
in `discotool.py` ergänzen.

## Ehrliche Grenzen
OSM-Abdeckung schwankt je Branche — Discovery ist ein Trichter, kein vollständiges Register.
Höflich abfragen (kein Massen-Loop). Nur öffentliche Firmendaten, keine Kontaktpersonen (DSGVO).
Tier-2-HTML-Fetch: manche Seiten blocken Bots (403/timeout) → Fehler werden protokolliert,
kein Crash. Seite dann ggf. manuell prüfen.

## Integration
Discovery → `leadtool.add_lead`. Danach lebt der Lead im normalen Tracking (`lead`-Skill):
Status setzen, kontaktieren, report. Prototyp (C) / Outreach (D) docken später an.

---

## Tier 3 — Qualitätsurteil per Playwright (A3)

Bewerte die vielversprechendsten analysierten Kandidaten qualitativ. Tier 3 läuft NACH A2
(`analyse`-Subcommand). Playwright wird direkt als MCP-Tool im Skill benutzt —
kein Python-Code für den Browser-Aufruf.

### Ablauf

1. **Shortlist holen:**
   ```
   python discover.py shortlist <run-datei>
   ```
   Gibt die top-10 analysierten Kandidaten sortiert nach Score (desc) aus.
   Optional: `--top 5` für eine engere Auswahl.
   Kandidaten ohne Status `analysiert` tauchen hier nie auf.

2. **Für jeden Kandidaten — Browser-Urteil:**
   Für jede Website auf der Shortlist:
   - `browser_navigate` zur URL des Kandidaten.
   - `browser_take_screenshot` — visueller Ersteindruck.
   - Optional `browser_snapshot` für DOM-Struktur (z.B. bei unklarer Responsiveness).
   Beurteile nach diesen Dimensionen:
   - **Design-Qualität:** Farben, Typografie, Layout — wirkt es professionell oder veraltet?
   - **Mobile / Responsiveness:** Navigiere auf 375 px Breite (`browser_resize`), prüfe ob
     Layout bricht. Fehlt Viewport-Meta (aus A2 bekannt) → wahrscheinlich nicht responsiv.
   - **UX / Klarheit:** Ist das Angebot sofort verständlich? Gibt es CTA/Kontakt-Weg?
   - **Professionalität:** Passt die Seite zur Branche? Wirkt sie vertrauenswürdig?

3. **Urteil eintragen:**
   ```
   python discover.py bewerten <run-datei> <id> <lohnt|lohnt_nicht|unklar> "<kurzes Urteil>"
   ```
   Beispiele:
   ```
   python discover.py bewerten discovery/2026-06-28-zahnaerzte-eimsbuettel.json 3 lohnt \
     "Veraltetes Design, kein Responsive, kein CTA — klare Schwäche"
   python discover.py bewerten discovery/2026-06-28-zahnaerzte-eimsbuettel.json 7 lohnt_nicht \
     "Modernes, responsives Design — kein offensichtlicher Bedarf"
   python discover.py bewerten discovery/2026-06-28-zahnaerzte-eimsbuettel.json 5 unklar \
     "Design veraltet, aber Praxis-Typ unklar — nochmal prüfen"
   ```

4. **Entscheidung:** Nach der Tier-3-Runde:
   - `lohnt`-Kandidaten mit ausreichendem Score → `python discover.py uebernehmen <run> <id,id,...>`
   - `lohnt_nicht`-Kandidaten → nicht übernehmen (bleiben im Run als Archiv).
   - `unklar`-Kandidaten → nochmals kurz recherchieren oder mit niedrigerer Priorität übernehmen.

### Faustregeln fürs Urteilen

- **Fokus auf Geschäftsschaden:** Nicht jede hässliche Seite ist ein Lead. Frag dich:
  würde der Betrieb mit einer besseren Seite mehr Kunden gewinnen?
- **Score als Orientierung, nicht als Wahrheit:** Ein hoher Tier-2-Score (kein HTTPS, kein
  Viewport, kein Impressum) bedeutet strukturell viele Mängel — Tier 3 prüft, ob es sich
  visuell/inhaltlich bestätigt.
- **Sei fair:** Nicht jeder Klempner braucht eine Hochglanz-Site. Urteile branchenrelativ.
- **Branchenportal ≠ eigene Website:** Auch hier gilt: wer nur auf meinestadt.de oder
  gelbeseiten.de zu finden ist, hat keine eigene Website.

### Ehrliche Grenzen

- Playwright ist langsam und manuell — beurteile die **Shortlist**, nicht alle Kandidaten.
  Standardmäßig top-10; bei großen Runs ggf. `--top 5`.
- Screenshots zeigen den aktuellen Stand — einige Seiten laden dynamisch und sehen
  im Screenshot anders aus als im Browser. Im Zweifel: `browser_snapshot` für DOM-Analyse.
- Das Tier-3-Urteil wird **nicht** automatisch in den Opportunity-Score eingerechnet
  (Score bleibt deterministisch aus Tier 1 + Tier 2). Das Urteil ist ein qualitativer
  Hinweis, keine harte Metrik.

### Integration mit `uebernehmen`

Tier 3 ergänzt die Entscheidung für `uebernehmen` — Kandidaten mit `tier3.empfehlung == "lohnt"`
sind gute Übernahmekandidaten, auch wenn ihr Score nicht automatisch hoch genug für
`uebernehmen auto` wäre. Explizit übernehmen mit: `python discover.py uebernehmen <run> <ids>`.
