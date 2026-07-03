# Design: Lead-Tracking-Rückgrat (Subsystem B)

**Datum:** 2026-06-28
**Autor:** Shawn Jedrzejczyk (shje@delta-sport.com)
**Status:** Approved (Brainstorming)

## Kontext & Ziel

Shawn will in Hamburg **Festpreis-Projekte** (keine Stundensätze) akquirieren. Das Gesamtsystem
besteht aus 5 Subsystemen:

| # | Subsystem | Zweck | Hängt ab von |
|---|-----------|-------|--------------|
| A | Lead-Discovery | Hamburger Firmen finden + Website-Schwächen erkennen | — |
| **B** | **Lead-Tracking / CRM** | **Wer, wann, Status, Absprachen** | **A (Datenmodell = Rückgrat)** |
| C | Prototyp-Generator | Aus Schwäche → Mockup/UCP-Prototyp | A |
| D | Outreach | Professionelle Mail mit ROI + Prototyp | B, C |
| E | Portfolio | Wiederverwendbare Prototypen sammeln | C |

**Diese Spec deckt nur Subsystem B ab.** B ist zuerst dran, weil alle anderen Teile sich an das
Lead-Datenmodell hängen. A, C, D, E bekommen jeweils eigene Spec → Plan → Implementierung.

### Rahmenbedingungen
- **Wenig laufende Handarbeit.** Shawn ist parallel ausgelastet (NWS-Ablöse bis 31.12.2026,
  2 IU-Seminararbeiten bis 30.09.2026). Das System muss neben den Hauptprojekten überleben.
- **Claude Code ist der Haupt-Operator.** Claude findet Leads, baut Prototypen, entwirft Mails,
  pflegt Status. Shawn schaut drauf und trifft Entscheidungen. Datenspeicher muss für beide gut
  les-/schreibbar sein.
- **Rechtlicher Showstopper für Subsystem D (hier nur dokumentiert, nicht gebaut):**
  Kaltakquise per E-Mail ist nach **UWG §7** ohne vorherige Einwilligung auch im B2B abmahnbar.
  Outreach wird deshalb **niemals vollautomatisch versenden** — das System bereitet alles
  one-click-fertig vor, der Mensch klickt final auf Senden. B muss dafür nur die Daten halten
  (Kontakt, ucp, roi_these, Prototyp-Verweis, kontaktiert_am).

## Designentscheidungen

1. **Form:** Datei-basiert + Claude-Skill. Kein Hosting, sofort nutzbar, git-versioniert,
   perfekt für Claude-als-Operator. (Verworfen: lokale Web-App / Power Platform / Notion —
   zu viel Bau-Aufwand bzw. kein Coding-Lernwert bzw. Daten außer Haus.)
2. **Format:** Markdown + YAML-Frontmatter, spiegelt Shawns Brain-Muster (sofort vertraut,
   git-diff-bar, per Grep/Frontmatter abfragbar). (Verworfen: SQLite — bei Dutzenden Leads verfrüht.)
3. **Zwei-Ebenen-Speicher:** Eine Sammeldatei für kalte/frühe Leads (eine Zeile/Lead),
   eigene Datei erst für **warme** Leads. Hält die Sache schlank.
4. **Graduierung bei `in_klaerung`:** Sobald eine echte Antwort kommt und der Kontakt weitergeht,
   bekommt der Lead seine eigene Datei. Alles davor bleibt eine Zeile in der Sammeldatei.
5. **14-Tage-Regel abgeleitet, kein Cron:** `keine_antwort` wird aus `kontaktiert_am` berechnet,
   wenn Claude `lead report` läuft. Kein Hintergrundjob nötig.

## Status-Lebenszyklus

```
identifiziert → analysiert → prototyp_erstellt → kontaktiert
   → keine_antwort        (AUTO-Vorschlag: kontaktiert_am > 14 Tage her & keine Antwort)
   → in_klaerung          (Antwort kam, Kontakt geht weiter → GRADUIERUNG zu eigener Datei)
   → termin_vereinbart
   → angebot_raus
   → gewonnen             (+ Absprachen-Pflicht)
   → verloren / zurückgestellt
```

- **Kalte/frühe Status** (leben in `pipeline.md`): `identifiziert, analysiert, prototyp_erstellt,
  kontaktiert, keine_antwort, verloren, zurückgestellt`
- **Warme Status** (leben in eigener Datei `leads/<slug>.md`): `in_klaerung, termin_vereinbart,
  angebot_raus, gewonnen`

## Repo-Struktur

```
Leads/
├── CLAUDE.md              # Repo-Router: erklärt System + Status-Regeln (init-proj-Schema)
├── pipeline.md            # SAMMELDATEI: Tabelle aller kalten/frühen Leads (1 Zeile/Lead)
├── leads/                 # WARME Leads — eine Datei pro Stück (ab in_klaerung)
│   └── <firma-slug>.md
├── templates/
│   └── lead.md            # Vorlage für eine warme Lead-Datei
├── prototypes/            # (Subsystem C, später) — Feld schon reserviert
└── .claude/skills/lead/
    └── SKILL.md           # der Tracking-Skill, den Claude in jeder Session nutzt
```

## Komponente 1: Sammeldatei `pipeline.md`

Eine Markdown-Tabelle, schlank, alles auf einen Blick. Spalten:

| slug | Firma | Status | Schwäche | kontaktiert_am | Wiedervorlage | Notiz |
|------|-------|--------|----------|----------------|---------------|-------|
| mueller-sanitaer | Müller Sanitär | kontaktiert | keine Mobil-Ansicht | 2026-06-20 | 2026-07-05 | — |

- Enthält nur kalte/frühe Status.
- `slug` ist der stabile Identifier (kebab-case Firmenname), verbindet später Prototyp-Ordner + warme Datei.
- Datumsfelder als `YYYY-MM-DD`, leer = `—`.

## Komponente 2: Warme Lead-Datei `leads/<slug>.md`

YAML-Frontmatter (strukturiert) + Body (Historie/Absprachen/Notizen):

```yaml
---
firma: Müller Sanitär GmbH
slug: mueller-sanitaer
status: in_klaerung
prioritaet: hoch            # hoch | mittel | niedrig
ort: Hamburg-Altona
branche: Handwerk
website: https://...
schwaeche: ["keine mobile Ansicht", "kein Kontaktformular"]
ucp: "Mobile-Website mit Online-Terminbuchung"
roi_these: "20 verpasste Anfragen/Monat × ..."
prototyp: prototypes/mueller-sanitaer/   # Subsystem C, sonst leer
kontakt: { name: "", rolle: "", email: "", quelle: Impressum }
kontaktiert_am: 2026-06-20
wiedervorlage: 2026-07-05
angelegt: 2026-06-18
---
## Historie
- 2026-06-18 identifiziert (Discovery-Lauf)
- 2026-06-20 Erstmail raus
- 2026-06-25 Antwort: Interesse, will Angebot

## Absprachen
(bei gewonnen Pflicht: Umfang, Festpreis, Deadline, sonstige Zusagen)

## Notizen
```

## Komponente 3: Der `lead`-Skill

Operationen, die Claude in jeder Session konsistent ausführt:

| Operation | Verhalten |
|-----------|-----------|
| `neu <firma>` | Lead-Zeile in `pipeline.md` anlegen (Subsystem A ruft das später auf). slug ableiten, Status `identifiziert`, `angelegt`-Datum setzen. |
| `status <slug> <status>` | Status setzen. **Beim Übergang → `in_klaerung`:** Datei aus `templates/lead.md` anlegen, Werte aus pipeline-Zeile übernehmen, Zeile aus `pipeline.md` entfernen (Graduierung). |
| `report` | Zeigt **fällige Wiedervorlagen** (`wiedervorlage` ≤ heute) **+** Leads mit `kontaktiert_am > 14 Tage` ohne Antwort → schlägt `keine_antwort` vor. Das „nichts-verschlafen"-Cockpit. Rein abgeleitet. |
| `notiz <slug> <text>` | Historie/Notiz mit Datum anhängen (Sammeldatei-Notizspalte oder warme Datei). |
| `gewonnen <slug>` | Setzt Status `gewonnen` und erzwingt Ausfüllen des `## Absprachen`-Abschnitts. |

**Datums-Hinweis:** Claude erfährt das heutige Datum aus dem Session-Kontext (`currentDate`).
Der Skill nutzt dieses Datum für `report`-Berechnungen und neue Einträge.

## Integrationspunkte (reserviert, in B NICHT gebaut)

- **A Discovery** → ruft `lead neu` mit vorbefüllter `schwaeche` + `branche` + `website`.
- **C Prototyp** → schreibt nach `prototypes/<slug>/`, setzt Frontmatter-Feld `prototyp:`.
- **D Outreach** → liest `ucp` + `roi_these` + `prototyp`, entwirft Mail, setzt nach manuellem
  Versand `kontaktiert_am` + Status `kontaktiert`.

## Out of Scope (B)

- Discovery-Automatik (A), Prototyp-Generierung (C), Mail-Versand/-Entwurf (D), Portfolio (E).
- UI / Web-Frontend. (Kann später auf die Dateien aufsetzen.)
- SQLite/DB-Migration. (Erst wenn Lead-Zahl es erzwingt.)

## Erfolgskriterien

- Shawn kann einen Lead anlegen, durch alle Status führen, und der Lead graduiert bei `in_klaerung`
  automatisch korrekt in eine eigene Datei.
- `lead report` zeigt zuverlässig fällige Follow-ups + überfällige (>14 Tage) Kontakte.
- Alles git-versioniert, ohne dass Shawn YAML/Markdown von Hand pflegen muss (Skill macht das).
- Das Datenmodell trägt die reservierten Felder für A/C/D, ohne dass diese gebaut sind.
