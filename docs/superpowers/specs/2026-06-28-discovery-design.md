# Design: Lead-Discovery (Subsystem A)

**Datum:** 2026-06-28
**Autor:** Shawn Jedrzejczyk (shje@delta-sport.com)
**Status:** Approved (Brainstorming)

## Kontext & Ziel

Subsystem A des Festpreis-Akquise-Systems (siehe `2026-06-28-lead-tracking-backbone-design.md`).
Discovery findet **Hamburger Firmen mit Website-Schwächen** und legt vielversprechende Funde
automatisch als Leads in der bestehenden Pipeline (Subsystem B) an.

Discovery zerfällt in drei Schritte:
1. **Kandidaten finden** — Hamburger Betriebe nach Branche + Stadtteil
2. **Website prüfen** — existiert sie? aktuell? mobil? Funktionen? (gestuft Tier 1–3)
3. **Als Lead anlegen** — `leadtool.add_lead(...)` (Subsystem B, bereits fertig)

## Designentscheidungen (aus Brainstorming)

1. **Kandidaten-Quelle:** OpenStreetMap via **Overpass-API** (kostenlos, legal, strukturiert),
   angereichert durch **WebSearch** (um fehlende `website`-Tags gegenzuprüfen). Verworfen:
   Google-Maps-/Verzeichnis-Scraping (ToS-Verstoß), Google Places API (Setup/Kosten).
2. **Schwächen-Tiefe:** Endziel Tier 1–3, aber **stufenweise gebaut** (A1→A2→A3), jede Stufe
   für sich nutzbar und testbar.
3. **Architektur = gleiche Philosophie wie B:** deterministische Mechanik in einem getesteten
   Python-Tool, Urteilsvermögen bei Claude.
4. **Lead-Erzeugung = Schwellwert-Hybrid:** Hochkaräter (z.B. nachweislich keine Website) werden
   automatisch Lead; Grenzfälle landen in einer Fund-Liste zur Ein-Kommando-Freigabe. Kein Müll
   in der Pipeline.

## Architektur

```
discover.py      # CLI-Dispatch (parallel zu lead.py)
discotool.py     # Kern: Overpass-Query, Parsing, Heuristiken, Score, Run-Dateien, Lead-Anlage
.claude/skills/discover/SKILL.md   # orchestriert die Urteils-Schritte (WebSearch, Playwright)
discovery/       # Run-Dateien (transientes Arbeitsmaterial): <datum>-<branche>-<area>.json
```

Discovery **importiert `leadtool`** und ruft `add_lead(...)` — dockt direkt an Subsystem B an.

### Aufgabenteilung

| Deterministisch (Python `discotool.py`, getestet) | Urteil (Claude + MCP, via `discover`-Skill) |
|---|---|
| Branche → OSM-Tags mappen | WebSearch: fehlende Seite gegenprüfen / URL finden |
| Overpass-Query bauen + abfragen + parsen | Tier-3: Design-Qualität, Screenshot-Bewertung (Playwright) |
| HTML laden + Tier1/2-Heuristiken | Befund-Text formulieren |
| Opportunity-Score, Run-Dateien, Lead-Anlage, Dedup | Grenzfall-Entscheidungen |

### Discovery-Ablauf (Vollausbau)

```
discover.py scan "Zahnärzte" "Eimsbüttel"
  → [Python]  Overpass: Betriebe der Branche im Stadtteil → Run-Datei mit Kandidaten
  → [Python]  je Kandidat mit Seite: HTML laden, Tier1/2-Heuristiken, Score (A2)
  → [Claude]  Kandidaten ohne Seite: WebSearch-Gegenprüfung → Status setzen
  → [Claude]  Tier-3-Urteil auf Shortlist: Playwright laden/Screenshot (A3)
  → [Python]  Hybrid: Hochkaräter → add_lead (auto); Grenzfälle → Fund-Liste
discover.py uebernehmen <run> 1,3,5    # Grenzfälle freigeben → werden Leads
```

## Tier-Definitionen

- **Tier 1 — keine Website:** Betrieb existiert, aber keine auffindbare Website. Klarste
  Verkaufsstory. Signal: kein `website`-Tag in OSM **und** per WebSearch keine Seite gefunden.
- **Tier 2 — grobe Mängel** (vorhandene Seite): kein HTTPS, nicht mobil-tauglich (kein
  Viewport-Meta / responsive), veraltet (altes Copyright-Jahr / alte Tech), kein Impressum,
  kein Kontaktformular.
- **Tier 3 — volle Analyse:** Performance (Ladezeit), SEO-Basics, Design-Qualität, Barrierefreiheit
  — Claude-Urteil mit Playwright auf der Shortlist.

## Opportunity-Score

Deterministisch aus den Signalen, je höher desto besser der Lead:
- keine Website (bestätigt) → hoher Basis-Score (Tier 1)
- kein HTTPS / nicht mobil / veraltet / kein Impressum / kein Kontaktformular → Aufschläge (Tier 2)
- schlechte Performance / schlechtes Design-Urteil → Aufschläge (Tier 3)

Schwellwert `AUTO_SCHWELLE`: ≥ Schwelle → Lead wird automatisch angelegt; darunter → Fund-Liste.

## Run-Datei (transientes Arbeitsmaterial)

`discovery/<datum>-<branche>-<area>.json` — Quelle der Wahrheit für einen Scan-Lauf:
Liste von Kandidaten mit `id, firma, adresse, website, status, score, befund, lead_angelegt`.
Status-Werte: `neu, website_unklar, keine_website, hat_website, analysiert`.
Wird **nur über CLI-Kommandos** mutiert (nicht von Hand). `discover.py show <run>` rendert
es menschenlesbar. (JSON statt Markdown, weil Claude Status programmatisch zuverlässig
fortschreibt; die Run-Datei ist Arbeitsmaterial, nicht das permanente CRM.)

## Scope dieser Spec vs. A1-Bau

Diese Spec beschreibt die **ganze Vision** (Tier 1–3, Vollausbau). **Gebaut wird zuerst nur A1**
(eigener Plan). A2/A3 bekommen je einen eigenen Plan.

### A1 (Tier 1) — Lieferumfang

1. **`discotool.py`:**
   - `branche_to_tags(branche)` — deutsches Branchenwort → OSM-Tags (erweiterbares Dict, mit
     Synonymen; unbekannte Branche → klare Fehlermeldung mit Hinweis auf bekannte).
   - `build_overpass_query(tags, area, stadtteil=None)` — Overpass-QL für Hamburg (+ optional
     Stadtteil), Nodes/Ways/Relations mit Tags.
   - `fetch_overpass(query, *, fetch_fn)` — POST an Overpass, JSON → Kandidaten-Dicts.
     **HTTP injizierbar** (`fetch_fn`) für deterministische Tests ohne Netz.
   - `parse_elements(json)` — Overpass-JSON → `[{firma, adresse, website, telefon, osm_id}]`.
   - `score_tier1(cand)` — kein website-Tag → Basis-Score, sonst 0.
   - Run-Datei lesen/schreiben (`load_run`, `save_run`), `new_run(...)`, `set_status(run, id, status, url=None)`.
   - `create_leads(root, run, ids|auto, today)` — ruft `leadtool.add_lead(...)` mit
     `schwaeche="keine auffindbare Website"`; Dedup über `add_lead`-ValueError (skip + zählen).
2. **`discover.py`:** Subcommands `scan <branche> <stadtteil>`, `show <run>`,
   `setstatus <run> <id> <status> [url]`, `uebernehmen <run> <ids|auto>`. `main(argv)->int`,
   UTF-8-stdout (wie lead.py).
3. **`.claude/skills/discover/SKILL.md`:** orchestriert den A1-Loop — scan, dann je
   `website_unklar`-Kandidat WebSearch → `setstatus`, dann `uebernehmen auto`.
4. **Tests:** branche_to_tags, query-Bau, parse_elements (gegen Overpass-Beispiel-JSON-Fixture),
   score_tier1, Run-Datei-Roundtrip, create_leads inkl. Dedup (mit echtem leadtool gegen tmp-Repo).
   Overpass wird über `fetch_fn`-Injektion gemockt — **kein echter Netz-Call im Test**.

### A1 — Nicht enthalten (kommt in A2/A3)
HTML-Fetch + Tier-2-Heuristiken (A2), Playwright/Tier-3-Urteil (A3), Performance/SEO.

## Integration mit Subsystem B
- Discovery ruft `leadtool.add_lead(root, firma, schwaeche=..., today=...)`.
- Dedup ist geschenkt: `add_lead` wirft bei existierendem slug → Discovery überspringt.
- Reservierte Lead-Felder (`ucp`, `roi_these`, `prototyp`) bleiben leer — füllen C/D.

## Out of Scope (ganz Subsystem A)
- Outreach / Mailversand (D), Prototyp-Bau (C), Portfolio (E).
- Bundesweite Suche — bewusst nur Hamburg.
- Personenbezogene Kontaktdaten — Discovery speichert nur Firmen-Geschäftsinfo (Name, Adresse,
  Website). Kontaktpersonen erst in D.

## Recht & ehrliche Grenzen
- **Overpass/OSM:** höflich abfragen (Timeout, aussagekräftiger User-Agent, keine Massen-Loops).
- **Abdeckung schwankt je Branche** — manche Betriebsarten sind in OSM gut gepflegt, andere kaum.
  Keine Vollständigkeit erwarten; Discovery ist ein Trichter, kein Kataster.
- **Nur öffentliche Geschäftsdaten** gespeichert → DSGVO-unkritisch.

## Erfolgskriterien (A1)
- `discover.py scan "<branche>" "<stadtteil>"` liefert eine Run-Datei mit echten Hamburger
  Kandidaten der Branche.
- Kandidaten ohne `website`-Tag werden als `website_unklar` markiert; nach WebSearch-Gegenprüfung
  (Claude) als `keine_website` bestätigte Funde landen per `uebernehmen auto` als Leads in `pipeline.md`.
- Doppelte Firmen erzeugen keine Duplikate (Dedup greift).
- Alle deterministischen Teile sind getestet, **ohne echten Overpass-Call im Test**.
