# Prototyp-Qualitätsschleife — wie die One-Pager immer besser werden

Ziel: nicht „einmal gut" (Glück), sondern **jede Demo besser als die letzte**. Zwei aktive
Schleifen; eine dritte ist bewusst zurückgestellt.

---

## Schleife 1 — Craft pro Demo (hebt jede einzelne)

Fester Ablauf statt „einmal bauen, fertig". Er ersetzt den bisherigen `draft → approve`:

1. **Bauen** mit Pflicht-Sub-Skill `frontend-design` + `impeccable` (Craft-Floor). Self-contained.
2. **Detektor-Hook** (läuft automatisch nach dem Schreiben) — mechanische AI-Tells fixen.
3. **`impeccable critique <datei>`** — bepunktetes UX-Urteil gegen die Rubrik unten.
4. **Gezielter Refine-Pass** (`polish` / `bolder` / `typeset` / `layout`), bis die Rubrik-Schwelle sitzt.
5. **Erst dann `approve`** (Status `approved_local`). Publish bleibt separate Einzelfreigabe.

### Freigabe-Rubrik (jede Demo muss sie treffen)
| Dimension | Mindestanspruch |
|---|---|
| Vertrauen/Seriosität | wirkt für die Branche glaubwürdig, kein Template-Look |
| Lesbarkeit Zielgruppe | Fließtext ≥17 px, WCAG-AA-Kontrast, klare Hierarchie |
| Faktenbindung | nur belegte Fakten; Unbelegtes = markierter Platzhalter |
| Mobil (375 px) | kein Querscroll, tappbare CTA (≥44 px), lesbar |
| Genau eine CTA | eine klare Aktion, farblich reserviert |
| Distinktivität | individuell für den Betrieb, kein generisches AI-Layout |

Gate: **keine Dimension unter „erfüllt"** → sonst zurück zu Schritt 4. Score/Urteil im
Lead-Verlauf notieren.

### Detektor voll scharf (optional, Umgebungssache)
Der impeccable-Detektor läuft aktuell „degraded" (fehlende npm-Parser). Für echte Kontrast-/
Selektor-/Font-Prüfung: `htmlparser2 css-select css-tree domutils` bereitstellen (nicht ins
Python-Repo committen — global oder in einer Node-Umgebung). Ohne das bleibt `critique` (Schritt 3)
das tragende Urteil.

---

## Schleife 2 — Lernen über Demos (hebt das Grundniveau, kompoundiert)

### Portfolio-Flywheel (Store ist gebaut)
Nach jeder `approved_local`/`published`-Demo einen Portfolio-Eintrag anlegen
(`portfolio.add_entry`), Felder u.a. `muster` (das wiederverwendbare Lösungsprinzip) und
`lernnotiz` (was hier funktioniert hat). Der `prototype-art-director` referenziert beim nächsten
Brief ein passendes Muster (W5.4) — **individuelle Fakten, aber bewährtes Prinzip**. Startet ab
2 freigegebenen Demos.

### Hausstil extrahieren → DESIGN.md
Sobald **2–3 starke Demos** existieren: `impeccable extract` / `document` laufen lassen, um die
wiederkehrenden Tokens/Bausteine (Farbwelt, Typo-Skala, Icon-Stil, Karten-/Listen-Muster,
Motion) in eine **`DESIGN.md`** zu gießen. Neue Demos starten dann vom bewährten Fundament statt
bei null — bleiben aber pro Betrieb individuell. Das ist der Hebel, der „besser" automatisch macht.

---

## Schleife 3 — Realität als Maßstab (ZURÜCKGESTELLT, vorgemerkt)

Später: Lead-Ausgang (`kontaktiert → termin_vereinbart → gewonnen`) mit dem Demo-Muster
verknüpfen, damit auf echte Rückrufe optimiert wird, nicht nur auf Optik. CRM-Daten existieren
schon. Siehe Memory `prototyp-verbesserung-outcome-loop`.

---

## Kurzfassung des Kreislaufs
`Brief (Fakten) → bauen (frontend-design+impeccable) → Detektor → critique → refine → Rubrik-Gate
→ approve → Portfolio-Eintrag (muster+lernnotiz) → [ab 2–3 Demos] Hausstil/DESIGN.md → nächster
Brief referenziert Muster & Hausstil.`
Jede Runde startet höher als die letzte.